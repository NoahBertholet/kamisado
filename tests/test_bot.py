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
    choose_move,
    get_my_kind,
    get_possible_moves,
    apply_move_to_copy,
    is_winning_move,
    score_move,
    opponent_can_win_next_turn,
    score_opponent_danger
)

def empty_board():
    return [[[None, None] for _ in range(8)] for _ in range(8)]

def make_state(players=None, color=None, board=None, current=0):
    return {
        "players": players or ["BERTHOFUSEE", "adversaire"],
        "current": current,
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
        current=1,
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

def test_get_my_kind_returns_none_when_not_my_turn():
    state = make_state(current=1)

    result = get_my_kind(state)

    assert result is None

def test_get_my_kind_dark_when_bot_is_first_player():
    state = make_state(players=["BERTHOFUSEE", "adversaire"], current=0)

    result = get_my_kind(state)

    assert result == "dark"

def test_get_my_kind_light_when_bot_is_second_player():
    state = make_state(players=["adversaire", "BERTHOFUSEE"], current=1)

    result = get_my_kind(state)

    assert result == "light"

def test_get_possible_moves_returns_empty_when_kind_is_none():
    state = make_state()

    moves = get_possible_moves(state, None)

    assert moves == []

def test_get_possible_moves_dark_can_move_forward_and_diagonal():
    board = empty_board()
    board[7][3][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    moves = get_possible_moves(state, "dark")

    assert [[7, 3], [6, 3]] in moves
    assert [[7, 3], [6, 2]] in moves
    assert [[7, 3], [6, 4]] in moves

def test_get_possible_moves_light_can_move_forward_and_diagonal():
    board = empty_board()
    board[0][3][1] = ("blue", "light")

    state = make_state(
        players=["adversaire", "BERTHOFUSEE"],
        current=1,
        color="blue",
        board=board
    )

    moves = get_possible_moves(state, "light")

    assert [[0, 3], [1, 3]] in moves
    assert [[0, 3], [1, 2]] in moves
    assert [[0, 3], [1, 4]] in moves

def test_get_possible_moves_stops_before_occupied_square():
    board = empty_board()
    board[7][3][1] = ("blue", "dark")
    board[5][3][1] = ("red", "light")

    state = make_state(color="blue", board=board)

    moves = get_possible_moves(state, "dark")

    assert [[7, 3], [6, 3]] in moves
    assert [[7, 3], [5, 3]] not in moves
    assert [[7, 3], [4, 3]] not in moves

def test_apply_move_to_copy_moves_piece_without_changing_original_state():
    board = empty_board()
    board[7][3][0] = "blue"
    board[7][3][1] = ("red", "dark")
    board[5][3][0] = "yellow"

    state = make_state(color="red", board=board)
    move = [[7, 3], [5, 3]]

    new_state = apply_move_to_copy(state, move)

    assert state["board"][7][3][1] == ("red", "dark")
    assert state["board"][5][3][1] is None

    assert new_state["board"][7][3][1] is None
    assert new_state["board"][5][3][1] == ("red", "dark")
    assert new_state["color"] == "yellow"

def test_is_winning_move_dark():
    move = [[2, 3], [0, 3]]

    assert is_winning_move(move, "dark") is True

def test_is_winning_move_light():
    move = [[5, 3], [7, 3]]

    assert is_winning_move(move, "light") is True

def test_is_winning_move_false_when_not_on_final_row():
    move = [[7, 3], [6, 3]]

    assert is_winning_move(move, "dark") is False

def test_score_move_winning_move_has_big_score():
    winning_move = [[1, 3], [0, 3]]
    normal_move = [[7, 3], [6, 3]]

    assert score_move(winning_move, "dark") > score_move(normal_move, "dark")

def test_opponent_can_win_next_turn_true():
    board = empty_board()
    board[1][3][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    result = opponent_can_win_next_turn(state, "dark")

    assert result is True

def test_opponent_can_win_next_turn_false():
    board = empty_board()
    board[7][3][1] = ("blue", "dark")
    board[6][3][1] = ("red", "light")
    board[6][2][1] = ("red", "light")
    board[6][4][1] = ("red", "light")

    state = make_state(color="blue", board=board)

    result = opponent_can_win_next_turn(state, "dark")

    assert result is False

def test_score_opponent_danger_returns_zero_when_no_moves():
    danger = score_opponent_danger([], "dark")

    assert danger == 0

def test_score_opponent_danger_detects_winning_move_as_dangerous():
    moves = [
        [[3, 3], [2, 3]],
        [[1, 3], [0, 3]]
    ]

    danger = score_opponent_danger(moves, "dark")

    assert danger >= 10000

def test_choose_move_prefers_immediate_winning_move_dark():
    board = empty_board()
    board[1][3][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    move = choose_move(state)

    assert is_winning_move(move, "dark")

def test_choose_move_prefers_immediate_winning_move_light():
    board = empty_board()
    board[6][3][1] = ("blue", "light")

    state = make_state(
        players=["adversaire", "BERTHOFUSEE"],
        current=1,
        color="blue",
        board=board
    )

    move = choose_move(state)

    assert is_winning_move(move, "light")

def test_handle_message_play_returns_move_response_when_move_exists():
    socket_1, socket_2 = socket.socketpair()

    board = empty_board()
    board[7][7][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    send_json(socket_1, {
        "request": "play",
        "state": state,
        "errors": []
    })

    handle_message(socket_2)

    response = receive_json(socket_1)

    socket_1.close()
    socket_2.close()

    assert response["response"] == "move"
    assert response["move"] is not None
    assert "message" in response