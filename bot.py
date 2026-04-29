# import
import json
import struct
import socket
import threading
import random
import copy
import time

# constantes
BOT_PORT = 2222
BOT_NAME = "Rafael"
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

def get_my_kind(state):
    players = state["players"]
    my_index = players.index(BOT_NAME)

    if state["current"] != my_index:
        return None

    if my_index == 0:
        return "dark"
    else:
        return "light"

def get_possible_moves(state, kind):
    if kind is None:
        return []

    board = state["board"]
    required_color = state["color"]

    moves = []

    if kind == "dark":
        directions = [(-1, 0), (-1, -1), (-1, 1)]
    elif kind == "light":
        directions = [(1, 0), (1, -1), (1, 1)]
    else:
        return []

    for r in range(8):
        for c in range(8):
            piece = board[r][c][1]

            if piece is None:
                continue

            piece_color, piece_kind = piece

            if piece_kind != kind:
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

    return moves

def apply_move_to_copy(state, move):
    new_state = copy.deepcopy(state)
    board = new_state["board"]

    start, end = move
    start_r, start_c = start
    end_r, end_c = end

    piece = board[start_r][start_c][1]

    board[start_r][start_c][1] = None
    board[end_r][end_c][1] = piece

    new_state["color"] = board[end_r][end_c][0]

    return new_state

def is_winning_move(move, kind):
    end_r = move[1][0]

    if kind == "dark" and end_r == 0:
        return True

    if kind == "light" and end_r == 7:
        return True

    return False

def score_move(move, my_kind):
    start, end = move

    start_r, start_c = start
    end_r, end_c = end

    score = 0

    if is_winning_move(move, my_kind):
        score += 10000

    if my_kind == "dark":
        avance = start_r - end_r
        distance_victoire = end_r
    else:
        avance = end_r - start_r
        distance_victoire = 7 - end_r

    score += avance * 12

    score += (7 - distance_victoire) * 7

    distance_from_center = abs(end_c - 3.5)
    score += (3.5 - distance_from_center) * 5

    distance_move = abs(end_r - start_r) + abs(end_c - start_c)
    score += distance_move

    return score

def opponent_can_win_next_turn(state, opponent_kind):
    opponent_moves = get_possible_moves(state, opponent_kind)

    for opponent_move in opponent_moves:
        if is_winning_move(opponent_move, opponent_kind):
            return True

    return False

def score_opponent_danger(opponent_moves, opponent_kind):
    if not opponent_moves:
        return 0

    best_danger = 0

    for move in opponent_moves:
        danger = 0

        if is_winning_move(move, opponent_kind):
            danger += 10000

        end_r = move[1][0]
        end_c = move[1][1]

        if opponent_kind == "dark":
            danger += (7 - end_r) * 10
        else:
            danger += end_r * 10

        distance_from_center = abs(end_c - 3.5)
        danger += (3.5 - distance_from_center) * 3

        if danger > best_danger:
            best_danger = danger

    return best_danger

def choose_move(state):
    start_time = time.time()
    time_limit = 2.8

    my_kind = get_my_kind(state)

    if my_kind is None:
        return None

    opponent_kind = "light" if my_kind == "dark" else "dark"

    moves = get_possible_moves(state, my_kind)

    if not moves:
        return None

    winning_moves = []

    for move in moves:
        if is_winning_move(move, my_kind):
            winning_moves.append(move)

    if winning_moves:
        return random.choice(winning_moves)

    safe_moves = []
    studied_moves = []

    for move in moves:
        if time.time() - start_time >= time_limit:

            if safe_moves:
                return random.choice(safe_moves)

            if studied_moves:
                return random.choice(studied_moves)

            return random.choice(moves)

        future_state = apply_move_to_copy(state, move)

        if not opponent_can_win_next_turn(future_state, opponent_kind):
            safe_moves.append(move)
            
        studied_moves.append(move)

    if safe_moves:
        moves = safe_moves

        meilleur_score = -float("inf")
        meilleurs_coups = []

    for move in moves:
        if time.time() - start_time >= time_limit:
            break

        nouvel_etat = apply_move_to_copy(state, move)

        score = anticipation(nouvel_etat, 2, False, my_kind, opponent_kind, start_time, time_limit)

        if score > meilleur_score:
            meilleur_score = score
            meilleurs_coups = [move]
        elif score == meilleur_score:
            meilleurs_coups.append(move)

    if meilleurs_coups:
        return random.choice(meilleurs_coups)

    return random.choice(moves)

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
                "move": move,
                "message": random.choice(funnylines)
            })

def start_bot_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind(("", BOT_PORT))
    server_socket.listen()

    while True:
        client_socket, address = server_socket.accept()

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

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))

    subscribe_message = build_subscribe_message()

    send_json(client_socket, subscribe_message)

    response = receive_json(client_socket)

    client_socket.close()

def anticipation(etat, preshot, Notre_Coup, mon_shot, shot_adverse, start_time, time_limit):
    if time.time() - start_time >= time_limit:
        return score_opponent_danger(get_possible_moves(etat, shot_adverse), shot_adverse) * -1

    if preshot == 0:
        my_moves = get_possible_moves(etat, mon_shot)
        opponent_moves = get_possible_moves(etat, shot_adverse)

        my_score = 0
        opponent_danger = score_opponent_danger(opponent_moves, shot_adverse)

        for move in my_moves:
            my_score = max(my_score, score_move(move, mon_shot))

        return my_score - opponent_danger

    if Notre_Coup:
        meilleur_shot = -float("inf")
        coups = get_possible_moves(etat, mon_shot)

        if not coups:
            return -1000

        for coup in coups:
            if time.time() - start_time >= time_limit:
                return meilleur_shot

            test_shot = apply_move_to_copy(etat, coup)
            score = anticipation(test_shot, preshot - 1, False, mon_shot, shot_adverse, start_time, time_limit)
            meilleur_shot = max(meilleur_shot, score)

        return meilleur_shot

    else:
        meilleur_shot = float("inf")
        coups = get_possible_moves(etat, shot_adverse)

        if not coups:
            return 1000

        for coup in coups:
            if time.time() - start_time >= time_limit:
                return meilleur_shot

            test_shot = apply_move_to_copy(etat, coup)
            score = anticipation(test_shot, preshot - 1, True, mon_shot, shot_adverse, start_time, time_limit)
            meilleur_shot = min(meilleur_shot, score)

        return meilleur_shot
if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_bot_server)
    bot_thread.start()

    subscribe_to_server()

    bot_thread.join()