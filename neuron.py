# neuron_client — cross-platform (Windows + Linux), Python 3

import base64
import sys, socket, os, hashlib, signal, threading
from Crypto.Cipher import AES

os.system('cls' if os.name == 'nt' else 'clear')
print(r"""
	  ___  ___ __ _________  ___ 
	 / _ \/ -_) // / __/ _ \/ _ \ 
	/_//_/\__/\_,_/_/  \___/_//_/
	    chat 1.0 | yungjaki
""")


def sigint_handler(signum, frame):
    print('\n user interrupt ! shutting down')
    print("[info] shutting down NEURON \n\n")
    os._exit(0)

signal.signal(signal.SIGINT, sigint_handler)


def hasher(key):
    hexd = hashlib.sha512(key.encode('utf-8')).hexdigest()
    return hashlib.md5(hexd.encode('utf-8')).hexdigest()


BLOCK_SIZE = 32
PADDING = '{'


def encrypt(secret, data):
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
    cipher = AES.new(secret.encode('utf-8'), AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(data).encode('utf-8')))


def decrypt(secret, data):
    cipher = AES.new(secret.encode('utf-8'), AES.MODE_ECB)
    decoded = cipher.decrypt(base64.b64decode(data))
    return decoded.rstrip(PADDING.encode('utf-8')).decode('utf-8')


def receiver(s, key):
    """Background thread: read from the server and print incoming messages."""
    while True:
        try:
            data = s.recv(4096)
        except OSError:
            break
        if not data:
            print("\033[91m" + "\nDisconnected from chat server" + "\033[0m")
            os._exit(0)
        try:
            text = decrypt(key, data)
        except Exception:
            continue
        sys.stdout.write("\r" + text + "\n[Me :] ")
        sys.stdout.flush()


def chat_client():
    if len(sys.argv) < 5:
        print('Usage : python neuron.py <hostname> <port> <password> <nick_name>')
        sys.exit()

    host = sys.argv[1]
    port = int(sys.argv[2])
    key = hasher(sys.argv[3])
    uname = sys.argv[4]

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((host, port))
    except Exception:
        print("\033[91m" + 'Unable to connect' + "\033[0m")
        sys.exit()
    s.settimeout(None)  # blocking for the receive thread

    print("Connected to remote host. You can start sending messages")

    # start the background receiver
    t = threading.Thread(target=receiver, args=(s, key), daemon=True)
    t.start()

    # main thread: read keyboard input and send
    while True:
        try:
            line = input("[Me :] ")
        except (EOFError, KeyboardInterrupt):
            break
        if line.strip() == "":
            continue
        msg = '[ ' + uname + ': ] ' + line + '\n'
        try:
            s.send(encrypt(key, msg))
        except OSError:
            print("\033[91m" + "Connection lost" + "\033[0m")
            break


if __name__ == "__main__":
    chat_client()