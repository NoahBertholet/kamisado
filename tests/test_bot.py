import socket
import sys
import os
import struct

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bot import send_json, receive_json, handle_message, build_subscribe_message, BOT_PORT


def test_send_and_receive_json():

    socket_1, socket_2 = socket.socketpair()

    message = {
        "request": "ping"
    }

    send_json(socket_1, message)
    received = receive_json(socket_2)

    socket_1.close()
    socket_2.close()

    assert received == message

def test_handle_message_ping():
    socket_1, socket_2 = socket.socketpair()

    send_json(socket_1, {"request": "ping"})

    handle_message(socket_2)

    response = receive_json(socket_1)

    socket_1.close()
    socket_2.close()

    assert response == {"response": "pong"}

def test_handle_message_giveup():
    socket_1, socket_2 = socket.socketpair()

    send_json(socket_1, {"request": "play"})

    handle_message(socket_2)

    response = receive_json(socket_1)

    socket_1.close()
    socket_2.close()

    assert response == {"response": "giveup"}
    
def test_build_subscribe_message():
    message = build_subscribe_message()

    assert message["request"] == "subscribe"
    assert message["port"] == BOT_PORT
    assert message["name"] == "BERTHOFUSEE"
    assert message["matricules"] == ["24371", "23032"]

def test_receive_json_no_data():
    socket_1, socket_2 = socket.socketpair()

    socket_1.close()

    result = receive_json(socket_2)

    socket_2.close()

    assert result is None

def test_receive_json_incomplete_data():
    socket_1, socket_2 = socket.socketpair()

    
    size_bytes = struct.pack("I", 10)
    socket_1.sendall(size_bytes)

    # fermer avant d'envoyer le JSON
    socket_1.close()

    result = receive_json(socket_2)

    socket_2.close()

    assert result is None

def test_choose_move_returns_none_when_no_piece_can_move():
    state = {
        "players": ["BERTHOFUSEE", "adversaire"],
        "color": "blue",
        "board": [
            [[None, None] for _ in range(8)]
            for _ in range(8)
        ]
    }

    move = choose_move(state)

    assert move is None