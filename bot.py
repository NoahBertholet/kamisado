#import
import json
import struct
import socket
import threading
import random

#constantes
BOT_PORT = 8888
BOT_NAME = "BERTHOFUSEE"
SERVER_HOST = "localhost"
SERVER_PORT = 3000
funnylines = [
    "Je réfléchis très fort...",
    "Coup calculé à 200 IQ",
    "Ça passe ou ça casse !",
    "Je n'ai aucune idée de ce que je fais",
    "Stratégie secrète activée",
    "Tout est sous contrôle (je crois)",
    "On tente quelque chose...",
    "Pourquoi pas ce coup ?",
    "C'est sûrement une bonne idée",
    "Ça a l'air intelligent",
    "Je joue au hasard mais avec style",
    "Un coup digne d'un maître... ou pas",
    "Faisons semblant que c'est stratégique",
    "Je bluffe complètement",
    "Coup improvisé",
    "On verra bien ce que ça donne",
    "La chance est avec moi",
    "Plan génial en cours",
    "Ça va passer... peut-être",
    "Je sens que ça va marcher",
    "Coup audacieux",
    "C'est le moment de briller",
    "Analyse terminée (plus ou moins)",
    "Je tente un truc",
    "Espérons que ça fonctionne",
    "On croise les doigts",
    "Coup inspiré",
    "Je joue avec confiance",
    "Aucune pression",
    "Tout est calculé... ou presque"
]

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
    message = json.loads(json_string)

    return message

def choose_move(state):
    players = state["players"]
    my_name = BOT_NAME

    my_index = players.index(my_name)

    if my_index == 0:
        my_kind = "dark"
    else:
        my_kind = "light"

    print("Je joue les", my_kind)

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

            print("Pièce jouable :", r, c)

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

def handle_message(sock):
    message = receive_json(sock)
    print("Message recu", message)

    if message is None:
        return

    if message["request"] == "ping":
        print("réponse envoyée: pong")
        send_json(sock, {"response": "pong"})

    elif message["request"] == "play":
        move = choose_move(message["state"])
        print("Erreurs précédentes :", message.get("errors"))

        if move is None:
            send_json(sock, {"response": "giveup"})
        else:
            send_json(sock, {
                "response": "move",
                "move": move,
                "message ": random.choice(funnylines)
            })
        
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

def build_subscribe_message():
    return {
        "request": "subscribe",
        "port": BOT_PORT,
        "name": BOT_NAME,
        "matricules": ["24371", "23032"]
    }

def subscribe_to_server():
    print("Connexion au serveur...")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))

    print("Connexion établie")

    subscribe_message = build_subscribe_message()

    print("Envoi du message subscribe...")
    send_json(client_socket, subscribe_message)

    print("Attente de la réponse du serveur...")
    response = receive_json(client_socket)

    print("Réponse du serveur :", response)

    client_socket.close()
    print("Connexion fermée")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_bot_server)
    bot_thread.start()

    subscribe_to_server()

    bot_thread.join()