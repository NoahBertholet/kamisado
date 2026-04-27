import socket
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bot import send_json, receive_json


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