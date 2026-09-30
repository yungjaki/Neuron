#neuron_server  — Python 3 port

import configparser
import base64
import sys, socket, select
from Crypto.Cipher import AES
import hashlib
import os
import signal

os.system("clear")
print(r"""
	  ___  ___ __ _________  ___ 
	 / _ \/ -_) // / __/ _ \/ _ \ 
	/_//_/\__/\_,_/_/  \___/_//_/
	    chat 1.0 | yungjaki
""")


def sigint_handler(signum, frame):
    print('\n user interrupt ! shutting down')
    print("[info] shutting down NEURON \n\n")
    sys.exit()

signal.signal(signal.SIGINT, sigint_handler)


def hasher(key):
    hexd = hashlib.sha512(key.encode('utf-8')).hexdigest()
    return hashlib.md5(hexd.encode('utf-8')).hexdigest()  # 32 chars -> AES-256 key


BLOCK_SIZE = 32
PADDING = '{'


def encrypt(secret, data):
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
    cipher = AES.new(secret.encode('utf-8'), AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(data).encode('utf-8')))  # bytes


def decrypt(secret, data):
    cipher = AES.new(secret.encode('utf-8'), AES.MODE_ECB)
    decoded = cipher.decrypt(base64.b64decode(data))
    return decoded.rstrip(PADDING.encode('utf-8')).decode('utf-8')


config = configparser.RawConfigParser()
config.read(r'neuron.conf')

HOST = config.get('config', 'HOST')
PORT = int(config.get('config', 'PORT'))
PASSWORD = config.get('config', 'PASSWORD')
VIEW = str(config.get('config', 'VIEW'))
key = hasher(PASSWORD)

SOCKET_LIST = []
ADDRESSES = {}          # fd -> (ip, port), so we always report the right client
RECV_BUFFER = 4096


def chat_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    SOCKET_LIST.append(server_socket)
    print("neuron server started on port " + str(PORT))

    while True:
        ready_to_read, _, _ = select.select(SOCKET_LIST, [], [], 0)

        for sock in ready_to_read:

            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
                ADDRESSES[sockfd] = addr
                print("user (%s, %s) connected" % addr)
                broadcast(server_socket, sockfd,
                          encrypt(key, "[%s:%s] entered our chatting room\n" % addr))

            else:
                addr = ADDRESSES.get(sock, ('?', '?'))
                try:
                    data = sock.recv(RECV_BUFFER)
                    if data:
                        text = decrypt(key, data)
                        broadcast(server_socket, sock, encrypt(key, "\r" + text))
                        if VIEW == '1':
                            print(text)
                    else:
                        if sock in SOCKET_LIST:
                            SOCKET_LIST.remove(sock)
                        ADDRESSES.pop(sock, None)
                        broadcast(server_socket, sock,
                                  encrypt(key, "user (%s, %s) is offline\n" % addr))
                except Exception:
                    if sock in SOCKET_LIST:
                        SOCKET_LIST.remove(sock)
                    ADDRESSES.pop(sock, None)
                    broadcast(server_socket, sock,
                              encrypt(key, "user (%s, %s) is offline\n" % addr))
                    continue

    server_socket.close()


def broadcast(server_socket, sock, message):
    for client in list(SOCKET_LIST):
        if client != server_socket and client != sock:
            try:
                client.send(message)
            except Exception:
                client.close()
                if client in SOCKET_LIST:
                    SOCKET_LIST.remove(client)
                ADDRESSES.pop(client, None)


if __name__ == "__main__":
    sys.exit(chat_server())