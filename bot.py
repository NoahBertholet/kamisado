# import
import json
import struct
import socket
import threading
import random
import time

# constantes
BOT_PORT = 8888
BOT_NAME = "BERTHOFUSEE"
SERVER_HOST = "LOCALHOST"
SERVER_PORT = 3000
TIME_LIMIT = 2.8
MAX_ROOT_MOVES = 10
MAX_NEGAMAX_MOVES = 8
SAFETY_MARGIN = 0.05
_deadline = None

DIRECTIONS = {
    "dark": [(-1, 0), (-1, -1), (-1, 1)],
    "light": [(1, 0), (1, -1), (1, 1)]
}

CENTER_BONUS = [0, 5, 10, 15, 15, 10, 5, 0]

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

class TimeoutException(Exception):
    pass

def check_timeout():
    if _deadline is not None and time.perf_counter() >= _deadline:
        raise TimeoutException()
    
def send_json(sock, message):
    json_string = json.dumps(message)
    json_bytes = json_string.encode("utf-8")
    size_bytes = struct.pack("I", len(json_bytes))

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

    return json.loads(json_bytes.decode("utf-8"))

def get_my_kind(state):
    players = state["players"]
    my_index = players.index(BOT_NAME)

    if state["current"] != my_index:
        return None

    if my_index == 0:
        return "dark"
    return "light"

def get_possible_moves(state, kind):
    if kind is None:
        return []

    board = state["board"]
    required_color = state["color"]
    directions = DIRECTIONS[kind]

    moves = []

    for r in range(8):
        row = board[r]

        for c in range(8):
            piece = row[c][1]

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

def play_move(state, move):
    board = state["board"]

    start, end = move
    start_r, start_c = start
    end_r, end_c = end

    old_color = state["color"]
    piece = board[start_r][start_c][1]

    board[start_r][start_c][1] = None
    board[end_r][end_c][1] = piece

    state["color"] = board[end_r][end_c][0]

    return old_color, piece

def undo_move(state, move, old_color, piece):
    board = state["board"]

    start, end = move
    start_r, start_c = start
    end_r, end_c = end

    board[end_r][end_c][1] = None
    board[start_r][start_c][1] = piece

    state["color"] = old_color

def is_winning_move(move, kind):
    end_r = move[1][0]

    if kind == "dark":
        return end_r == 0

    if kind == "light":
        return end_r == 7

    return False

def score_move(move, my_kind):
    start, end = move

    start_r, start_c = start
    end_r, end_c = end

    if is_winning_move(move, my_kind):
        return 10000

    if my_kind == "dark":
        avance = start_r - end_r
        progression = 7 - end_r
    else:
        avance = end_r - start_r
        progression = end_r

    distance_move = abs(end_r - start_r) + abs(end_c - start_c)

    score = 0
    score += avance * 12
    score += progression * 7
    score += CENTER_BONUS[end_c]
    score += distance_move

    return score

def sort_moves(moves, kind):
    return sorted(moves, key=lambda move: score_move(move, kind), reverse=True)

def opponent_can_win_next_turn(state, opponent_kind):
    opponent_moves = get_possible_moves(state, opponent_kind)

    for opponent_move in opponent_moves:
        if is_winning_move(opponent_move, opponent_kind):
            return True

    return False

def evaluation(state, joueur, adversaire):
    board = state["board"]
    score = 0

    for r in range(8):
        for c in range(8):
            piece = board[r][c][1]

            if piece is None:
                continue

            piece_color, piece_kind = piece

            if piece_kind == joueur:
                signe = 1
                kind = joueur
            elif piece_kind == adversaire:
                signe = -1
                kind = adversaire
            else:
                continue

            if kind == "dark":
                progression = 7 - r
                distance_victoire = r
                direction = -1
            else:
                progression = r
                distance_victoire = 7 - r
                direction = 1

            piece_score = 0
            piece_score += progression * 18
            piece_score += CENTER_BONUS[c]

            if distance_victoire == 1:
                piece_score += 80
            elif distance_victoire == 2:
                piece_score += 35

            free_forward = 0
            nr = r + direction

            while 0 <= nr < 8:
                if board[nr][c][1] is not None:
                    break

                free_forward += 1
                nr += direction

            piece_score += free_forward * 4

            for dc in [-1, 1]:
                nr = r + direction
                nc = c + dc

                if 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr][nc][1] is None:
                        piece_score += 6

            score += signe * piece_score

    joueur_moves = len(get_possible_moves(state, joueur))
    adversaire_moves = len(get_possible_moves(state, adversaire))

    score += (joueur_moves - adversaire_moves) * 5

    return score

def negamax(state, depth, alpha, beta, joueur, adversaire):
    check_timeout()

    if depth == 0:
        return evaluation(state, joueur, adversaire)

    moves = get_possible_moves(state, joueur)

    if not moves:
        return -1000

    moves = sort_moves(moves, joueur)
    moves = moves[:MAX_NEGAMAX_MOVES]

    meilleur_score = -float("inf")

    for move in moves:
        check_timeout()

        if is_winning_move(move, joueur):
            score = 100000 + depth
        else:
            old_color, piece = play_move(state, move)

            try:
                score = -negamax(
                    state,
                    depth - 1,
                    -beta,
                    -alpha,
                    adversaire,
                    joueur
                )
            finally:
                undo_move(state, move, old_color, piece)

        if score > meilleur_score:
            meilleur_score = score

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    return meilleur_score

def choose_move(state):
    global _deadline

    start_time = time.perf_counter()
    _deadline = start_time + TIME_LIMIT - SAFETY_MARGIN

    my_kind = get_my_kind(state)

    if my_kind is None:
        _deadline = None
        return None

    opponent_kind = "light" if my_kind == "dark" else "dark"

    moves = get_possible_moves(state, my_kind)

    if not moves:
        _deadline = None
        return None

    moves = sort_moves(moves, my_kind)

    for move in moves:
        if is_winning_move(move, my_kind):
            _deadline = None
            return move

    safe_moves = []
    studied_moves = []

    try:
        for move in moves:
            check_timeout()

            old_color, piece = play_move(state, move)

            try:
                if not opponent_can_win_next_turn(state, opponent_kind):
                    safe_moves.append(move)
            finally:
                undo_move(state, move, old_color, piece)

            studied_moves.append(move)

    except TimeoutException:
        if safe_moves:
            _deadline = None
            return sort_moves(safe_moves, my_kind)[0]

        if studied_moves:
            _deadline = None
            return sort_moves(studied_moves, my_kind)[0]

        _deadline = None
        return random.choice(moves)

    if safe_moves:
        moves = safe_moves

    moves = sort_moves(moves, my_kind)
    moves = moves[:MAX_ROOT_MOVES]

    best_move = None
    depth = 1

    while True:
        current_best_move = None
        current_best_score = -float("inf")
        completed_depth = True

        try:
            for move in moves:
                check_timeout()

                old_color, piece = play_move(state, move)

                try:
                    score = -negamax(
                        state,
                        depth,
                        -float("inf"),
                        float("inf"),
                        opponent_kind,
                        my_kind
                    )
                finally:
                    undo_move(state, move, old_color, piece)

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = move

        except TimeoutException:
            completed_depth = False

        if completed_depth and current_best_move is not None:
            best_move = current_best_move
            depth += 1
        else:
            break

    _deadline = None

    print("profondeur atteinte :", depth - 1)

    if best_move is not None:
        return best_move

    return moves[0]

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
        "matricules": ["17866", "66178"]
    }

def subscribe_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))

    subscribe_message = build_subscribe_message()

    send_json(client_socket, subscribe_message)

    response = receive_json(client_socket)

    client_socket.close()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_bot_server)
    bot_thread.start()

    subscribe_to_server()

    bot_thread.join()