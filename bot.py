import json
import struct
import socket

BOT_PORT = 8888
SERVER_HOST = "localhost"
SERVER_PORT = 3000

def send_json(sock, message):
    json_string = json.dumps(message)
    json_bytes = json_string.encode("utf-8")

    message_size = len(json_bytes)

    size_bytes = struct.pack("!I", message_size)

    sock.sendall(size_bytes)
    sock.sendall(json_bytes)


def receive_json(sock):
    
    size_bytes = sock.recv(4)

    if not size_bytes:
        return None

    message_size = struct.unpack("!I", size_bytes)[0]

    json_bytes = b""

    while len(json_bytes) < message_size:
        chunk = sock.recv(message_size - len(json_bytes))

        if not chunk:
            return None

        json_bytes += chunk

    json_string = json_bytes.decode("utf-8")
    message = json.loads(json_string)

    return message
def handle_message(sock):
    message = receive_json(sock)
    print("Message recu", message)
    if message["request"]=="ping":
        send_json(sock,{"response":"pong"})
    elif message["request"]=="play":
        send_json(sock,{"response" :"giveup"})

def start_bot_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind(("", BOT_PORT))
    server_socket.listen()

    print(f"Bot en écoute sur le port {BOT_PORT}")

    while True:
        client_socket, address = server_socket.accept()
        print("Connexion reçue de :", address)

        handle_message(client_socket)

        client_socket.close()
def subscribe_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.connect((SERVER_HOST, SERVER_PORT))

    subscribe_message = {
        "request": "subscribe",
        "port": BOT_PORT,
        "name": "BERTHOFUSEE",
        "matricules": ["24371"]
    }

    send_json(client_socket, subscribe_message)

    response = receive_json(client_socket)
    print("Réponse du serveur :", response)

    client_socket.close()
