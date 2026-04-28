#import
import json
import struct
import socket
import threading
import random
import sys

# constantes
BOT_PORT = 8889
BOT_NAME = "RANDOM_BOT"

SERVER_HOST = "localhost"
SERVER_PORT = 3000


# ======================
# COMMUNICATION
# ======================

def send_json(sock, message):
    json_string = json.dumps(message)
    json_bytes = json_string.encode("utf-8")

    message_size = len(json_bytes)
    size_bytes = struct.pack("I", message_size)

    sock.sendall(size_bytes)
    sock.sendall(json_bytes)


def receive_json(sock):
    size_bytes = sock.recv(4)

    if not size_bytes:
        return None

    message_size = struct.unpack("I", size_bytes)[0]

    json_bytes = b""

    while len(json_bytes) < message_size:
        chunk = sock.recv(message_size - len(json_bytes))

        if not chunk:
            return None

        json_bytes += chunk

    json_string = json_bytes.decode("utf-8")
    return json.loads(json_string)


# ======================
# LOGIQUE RANDOM
# ======================

def choose_move(state):
    players = state["players"]
    my_index = players.index(BOT_NAME)

    if my_index == 0:
        my_kind = "dark"
    else:
        my_kind = "light"

    board = state["board"]
    required_color = state["color"]

    moves = []

    if my_kind == "dark":
        directions = [(-1, 0), (-1, -1), (-1, 1)]
    else:
        directions = [(1, 0), (1, -1), (1, 1)]

    for r in range(8):
        for c in range(8):
            piece = board[r][c][1]

            if piece is None:
                continue

            piece_color, piece_kind = piece

            if piece_kind != my_kind:
                continue

            if required_color is not None and piece_color != required_color:
                continue

            for dr, dc in directions:
                new_r = r + dr
                new_c = c + dc

                while 0 <= new_r < 8 and 0 <= new_c < 8:
                    if board[new_r][new_c][1] is not None:
                        break

                    moves.append([[r, c], [new_r, new_c]])

                    new_r += dr
                    new_c += dc

    if not moves:
        return None

    return random.choice(moves)


# ======================
# GESTION DES MESSAGES
# ======================

def handle_message(sock):
    message = receive_json(sock)

    if message is None:
        return

    if message["request"] == "ping":
        send_json(sock, {"response": "pong"})

    elif message["request"] == "play":
        move = choose_move(message["state"])

        if move is None:
            send_json(sock, {"response": "giveup"})
        else:
            send_json(sock, {
                "response": "move",
                "move": move
            })


# ======================
# SERVEUR BOT
# ======================

def start_bot_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind(("", BOT_PORT))
    server_socket.listen()

    print(f"{BOT_NAME} en écoute sur le port {BOT_PORT}")

    while True:
        client_socket, address = server_socket.accept()
        handle_message(client_socket)
        client_socket.close()


# ======================
# SUBSCRIBE
# ======================

def build_subscribe_message():
    return {
        "request": "subscribe",
        "port": BOT_PORT,
        "name": BOT_NAME,
        "matricules": ["66178", "17866"]
    }


def subscribe_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))

    send_json(client_socket, build_subscribe_message())

    response = receive_json(client_socket)
    print("Réponse serveur :", response)

    client_socket.close()


# ======================
# MAIN
# ======================

if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_bot_server)
    bot_thread.start()

    subscribe_to_server()

    bot_thread.join()