import socket
import sys
import os
import struct
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot import (
    send_json,
    receive_json,
    handle_message,
    build_subscribe_message,
    BOT_PORT,
    choose_move
)


def empty_board():
    return [[[None, None] for _ in range(8)] for _ in range(8)]

def make_state(players=None, color=None, board=None):
    return {
        "players": players or ["BERTHOFUSEE", "adversaire"],
        "color": color,
        "board": board or empty_board()
    }

def test_send_and_receive_json():
    socket_1, socket_2 = socket.socketpair()

    message = {"request": "ping"}

    send_json(socket_1, message)
    received = receive_json(socket_2)

    socket_1.close()
    socket_2.close()

    assert received == message

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

    socket_1.close()

    result = receive_json(socket_2)

    socket_2.close()

    assert result is None

def test_build_subscribe_message():
    message = build_subscribe_message()

    assert message["request"] == "subscribe"
    assert message["port"] == BOT_PORT
    assert message["name"] == "BERTHOFUSEE"
    assert message["matricules"] == ["24371", "23032"]

def test_handle_message_ping():
    socket_1, socket_2 = socket.socketpair()

    send_json(socket_1, {"request": "ping"})
    handle_message(socket_2)

    response = receive_json(socket_1)

    socket_1.close()
    socket_2.close()

    assert response == {"response": "pong"}

def test_handle_message_play_giveup_when_no_move():
    socket_1, socket_2 = socket.socketpair()

    state = make_state()

    send_json(socket_1, {
        "request": "play",
        "state": state,
        "errors": []
    })

    handle_message(socket_2)

    response = receive_json(socket_1)

    socket_1.close()
    socket_2.close()

    assert response == {"response": "giveup"}

def test_choose_move_returns_none_when_no_piece_can_move():
    state = make_state(color="blue")

    move = choose_move(state)

    assert move is None

def test_choose_move_dark_player_returns_a_move():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")

    state = make_state(
        players=["BERTHOFUSEE", "adversaire"],
        color="blue",
        board=board
    )

    move = choose_move(state)

    assert move is not None
    assert move[0] == [7, 7]


def test_choose_move_light_player_returns_a_move():
    board = empty_board()
    board[0][0][1] = ("red", "light")

    state = make_state(
        players=["adversaire", "BERTHOFUSEE"],
        color="red",
        board=board
    )

    move = choose_move(state)

    assert move is not None
    assert move[0] == [0, 0]

def test_choose_move_respects_required_color():
    board = empty_board()
    board[7][0][1] = ("blue", "dark")
    board[7][7][1] = ("red", "dark")

    state = make_state(
        players=["BERTHOFUSEE", "adversaire"],
        color="red",
        board=board
    )

    move = choose_move(state)

    assert move is not None
    assert move[0] == [7, 7]

def test_choose_move_ignores_wrong_color():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")

    state = make_state(
        players=["BERTHOFUSEE", "adversaire"],
        color="red",
        board=board
    )

    move = choose_move(state)

    assert move is None


def test_choose_move_ignores_opponent_piece():
    board = empty_board()
    board[7][7][1] = ("blue", "light")

    state = make_state(
        players=["BERTHOFUSEE", "adversaire"],
        color="blue",
        board=board
    )

    move = choose_move(state)

    assert move is None

def test_choose_move_does_not_go_outside_board():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    move = choose_move(state)

    assert move is not None

    start, end = move
    assert 0 <= start[0] < 8
    assert 0 <= start[1] < 8
    assert 0 <= end[0] < 8
    assert 0 <= end[1] < 8

def test_choose_move_does_not_move_on_occupied_square():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")
    board[6][7][1] = ("red", "light")

    state = make_state(color="blue", board=board)

    move = choose_move(state)

    assert move is not None
    assert move[1] != [6, 7]

def test_choose_move_returns_none_when_piece_is_blocked():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")
    board[6][7][1] = ("red", "light")
    board[6][6][1] = ("red", "light")

    state = make_state(color="blue", board=board)

    move = choose_move(state)

    assert move is None

def test_choose_move_without_required_color_can_play_any_own_piece():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")

    state = make_state(color=None, board=board)

    move = choose_move(state)

    assert move is not None
    assert move[0] == [7, 7]

def test_choose_move_raises_error_if_bot_name_not_in_players():
    state = make_state(players=["joueur1", "joueur2"])

    with pytest.raises(ValueError):
        choose_move(state)

def test_handle_message_none_does_not_crash():
    socket_1, socket_2 = socket.socketpair()

    socket_1.close()

    result = handle_message(socket_2)

    socket_2.close()

    assert result is None
