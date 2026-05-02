import socket
import sys
import os
import struct
import json
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import bot

from bot import (
    send_json,
    receive_json,
    handle_message,
    build_subscribe_message,
    BOT_PORT,
    BOT_NAME,
    choose_move,
    get_my_kind,
    get_possible_moves,
    play_move,
    undo_move,
    is_winning_move,
    score_move,
    sort_moves,
    opponent_can_win_next_turn,
    evaluation,
    negamax,
    check_timeout,
    TimeoutException,
    subscribe_to_server
)


@pytest.fixture(autouse=True)
def fast_bot(monkeypatch):
    monkeypatch.setattr(bot, "TIME_LIMIT", 0.08)
    monkeypatch.setattr(bot, "SAFETY_MARGIN", 0.001)
    monkeypatch.setattr(bot, "MAX_ROOT_MOVES", 6)
    monkeypatch.setattr(bot, "MAX_NEGAMAX_MOVES", 5)
    bot._deadline = None
    yield
    bot._deadline = None


def empty_board():
    return [[[None, None] for _ in range(8)] for _ in range(8)]


def make_state(players=None, color=None, board=None, current=0):
    return {
        "players": players or [BOT_NAME, "adversaire"],
        "current": current,
        "color": color,
        "board": board or empty_board()
    }


def test_check_timeout_does_nothing_without_deadline():
    bot._deadline = None
    check_timeout()


def test_check_timeout_raises_when_deadline_is_passed():
    bot._deadline = bot.time.perf_counter() - 1

    with pytest.raises(TimeoutException):
        check_timeout()


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

    socket_1.sendall(struct.pack("I", 10))
    socket_1.close()

    result = receive_json(socket_2)

    socket_2.close()

    assert result is None


def test_build_subscribe_message():
    message = build_subscribe_message()

    assert message["request"] == "subscribe"
    assert message["port"] == BOT_PORT
    assert message["name"] == BOT_NAME
    assert message["matricules"] == ["24371", "23032"]


def test_subscribe_to_server(monkeypatch):
    response = {"response": "ok"}
    response_bytes = json.dumps(response).encode("utf-8")
    incoming = [
        struct.pack("I", len(response_bytes)),
        response_bytes
    ]

    class FakeSocket:
        def __init__(self):
            self.sent = []
            self.connected_to = None
            self.closed = False

        def connect(self, address):
            self.connected_to = address

        def sendall(self, data):
            self.sent.append(data)

        def recv(self, size):
            return incoming.pop(0)

        def close(self):
            self.closed = True

    fake_socket = FakeSocket()

    monkeypatch.setattr(bot.socket, "socket", lambda *args, **kwargs: fake_socket)

    subscribe_to_server()

    assert fake_socket.connected_to == (bot.SERVER_HOST, bot.SERVER_PORT)
    assert fake_socket.closed is True
    assert len(fake_socket.sent) == 2


def test_handle_message_ping():
    socket_1, socket_2 = socket.socketpair()

    send_json(socket_1, {"request": "ping"})
    handle_message(socket_2)

    response = receive_json(socket_1)

    socket_1.close()
    socket_2.close()

    assert response == {"response": "pong"}


def test_handle_message_none_does_not_crash():
    socket_1, socket_2 = socket.socketpair()
    socket_1.close()

    result = handle_message(socket_2)

    socket_2.close()

    assert result is None


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


def test_get_my_kind_returns_none_when_not_my_turn():
    state = make_state(current=1)

    assert get_my_kind(state) is None


def test_get_my_kind_dark_when_bot_is_first_player():
    state = make_state(players=[BOT_NAME, "adversaire"], current=0)

    assert get_my_kind(state) == "dark"


def test_get_my_kind_light_when_bot_is_second_player():
    state = make_state(players=["adversaire", BOT_NAME], current=1)

    assert get_my_kind(state) == "light"


def test_get_my_kind_raises_error_if_bot_name_not_in_players():
    state = make_state(players=["joueur1", "joueur2"])

    with pytest.raises(ValueError):
        get_my_kind(state)


def test_get_possible_moves_returns_empty_when_kind_is_none():
    state = make_state()

    assert get_possible_moves(state, None) == []


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
        players=["adversaire", BOT_NAME],
        current=1,
        color="blue",
        board=board
    )

    moves = get_possible_moves(state, "light")

    assert [[0, 3], [1, 3]] in moves
    assert [[0, 3], [1, 2]] in moves
    assert [[0, 3], [1, 4]] in moves


def test_get_possible_moves_respects_required_color():
    board = empty_board()
    board[7][0][1] = ("blue", "dark")
    board[7][7][1] = ("red", "dark")

    state = make_state(color="red", board=board)

    moves = get_possible_moves(state, "dark")

    assert all(move[0] == [7, 7] for move in moves)


def test_get_possible_moves_without_required_color_can_play_any_piece():
    board = empty_board()
    board[7][0][1] = ("blue", "dark")
    board[7][7][1] = ("red", "dark")

    state = make_state(color=None, board=board)

    moves = get_possible_moves(state, "dark")

    assert any(move[0] == [7, 0] for move in moves)
    assert any(move[0] == [7, 7] for move in moves)


def test_get_possible_moves_ignores_opponent_piece():
    board = empty_board()
    board[7][7][1] = ("blue", "light")

    state = make_state(color="blue", board=board)

    moves = get_possible_moves(state, "dark")

    assert moves == []


def test_get_possible_moves_stops_before_occupied_square():
    board = empty_board()
    board[7][3][1] = ("blue", "dark")
    board[5][3][1] = ("red", "light")

    state = make_state(color="blue", board=board)

    moves = get_possible_moves(state, "dark")

    assert [[7, 3], [6, 3]] in moves
    assert [[7, 3], [5, 3]] not in moves
    assert [[7, 3], [4, 3]] not in moves


def test_get_possible_moves_blocked_piece_has_no_moves():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")
    board[6][7][1] = ("red", "light")
    board[6][6][1] = ("red", "light")

    state = make_state(color="blue", board=board)

    assert get_possible_moves(state, "dark") == []


def test_play_move_moves_piece_and_changes_color():
    board = empty_board()
    board[7][3][1] = ("red", "dark")
    board[5][3][0] = "yellow"

    state = make_state(color="red", board=board)
    move = [[7, 3], [5, 3]]

    old_color, piece = play_move(state, move)

    assert old_color == "red"
    assert piece == ("red", "dark")
    assert state["board"][7][3][1] is None
    assert state["board"][5][3][1] == ("red", "dark")
    assert state["color"] == "yellow"


def test_undo_move_restores_state():
    board = empty_board()
    board[7][3][1] = ("red", "dark")
    board[5][3][0] = "yellow"

    state = make_state(color="red", board=board)
    move = [[7, 3], [5, 3]]

    old_color, piece = play_move(state, move)
    undo_move(state, move, old_color, piece)

    assert state["board"][7][3][1] == ("red", "dark")
    assert state["board"][5][3][1] is None
    assert state["color"] == "red"


def test_is_winning_move_dark():
    assert is_winning_move([[2, 3], [0, 3]], "dark") is True


def test_is_winning_move_light():
    assert is_winning_move([[5, 3], [7, 3]], "light") is True


def test_is_winning_move_false_when_not_on_final_row():
    assert is_winning_move([[7, 3], [6, 3]], "dark") is False


def test_is_winning_move_false_with_unknown_kind():
    assert is_winning_move([[7, 3], [6, 3]], "unknown") is False


def test_score_move_winning_move_has_big_score():
    winning_move = [[1, 3], [0, 3]]
    normal_move = [[7, 3], [6, 3]]

    assert score_move(winning_move, "dark") > score_move(normal_move, "dark")


def test_score_move_light_progression():
    move = [[0, 3], [4, 3]]

    assert score_move(move, "light") > 0


def test_sort_moves_puts_best_move_first():
    moves = [
        [[7, 3], [6, 3]],
        [[1, 3], [0, 3]],
        [[7, 0], [6, 0]]
    ]

    sorted_moves = sort_moves(moves, "dark")

    assert sorted_moves[0] == [[1, 3], [0, 3]]


def test_opponent_can_win_next_turn_true():
    board = empty_board()
    board[1][3][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    assert opponent_can_win_next_turn(state, "dark") is True


def test_opponent_can_win_next_turn_false_when_blocked():
    board = empty_board()
    board[7][3][1] = ("blue", "dark")
    board[6][3][1] = ("red", "light")
    board[6][2][1] = ("red", "light")
    board[6][4][1] = ("red", "light")

    state = make_state(color="blue", board=board)

    assert opponent_can_win_next_turn(state, "dark") is False


def test_evaluation_positive_when_my_piece_is_advanced():
    board = empty_board()
    board[2][3][1] = ("blue", "dark")
    board[7][7][1] = ("red", "light")

    state = make_state(color="blue", board=board)

    assert evaluation(state, "dark", "light") > 0


def test_evaluation_negative_when_opponent_piece_is_advanced():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")
    board[6][3][1] = ("red", "light")

    state = make_state(color="blue", board=board)

    assert evaluation(state, "dark", "light") < 0


def test_evaluation_ignores_empty_board():
    state = make_state()

    assert evaluation(state, "dark", "light") == 0


def test_evaluation_rewards_free_forward_path():
    board_free = empty_board()
    board_blocked = empty_board()

    board_free[4][3][1] = ("blue", "dark")

    board_blocked[4][3][1] = ("blue", "dark")
    board_blocked[3][3][1] = ("red", "light")

    state_free = make_state(color="blue", board=board_free)
    state_blocked = make_state(color="blue", board=board_blocked)

    assert evaluation(state_free, "dark", "light") > evaluation(state_blocked, "dark", "light")


def test_evaluation_rewards_diagonal_options():
    board = empty_board()
    board[4][3][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    score_with_diagonals = evaluation(state, "dark", "light")

    board[3][2][1] = ("red", "light")
    board[3][4][1] = ("red", "light")

    score_without_diagonals = evaluation(state, "dark", "light")

    assert score_with_diagonals > score_without_diagonals


def test_negamax_returns_evaluation_at_depth_zero():
    board = empty_board()
    board[7][3][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    score = negamax(
        state,
        depth=0,
        alpha=-float("inf"),
        beta=float("inf"),
        joueur="dark",
        adversaire="light"
    )

    assert score == evaluation(state, "dark", "light")


def test_negamax_returns_negative_when_no_moves():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")
    board[6][7][1] = ("red", "light")
    board[6][6][1] = ("red", "light")

    state = make_state(color="blue", board=board)

    score = negamax(
        state,
        depth=1,
        alpha=-float("inf"),
        beta=float("inf"),
        joueur="dark",
        adversaire="light"
    )

    assert score == -1000


def test_negamax_detects_winning_move():
    board = empty_board()
    board[1][3][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    score = negamax(
        state,
        depth=1,
        alpha=-float("inf"),
        beta=float("inf"),
        joueur="dark",
        adversaire="light"
    )

    assert score >= 100000


def test_negamax_raises_timeout_when_deadline_is_passed():
    board = empty_board()
    board[7][3][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    bot._deadline = bot.time.perf_counter() - 1

    with pytest.raises(TimeoutException):
        negamax(
            state,
            depth=3,
            alpha=-float("inf"),
            beta=float("inf"),
            joueur="dark",
            adversaire="light"
        )


def test_negamax_uses_alpha_beta_cutoff():
    board = empty_board()
    board[7][0][1] = ("blue", "dark")
    board[7][7][1] = ("red", "dark")

    state = make_state(color=None, board=board)

    score = negamax(
        state,
        depth=2,
        alpha=99999,
        beta=100000,
        joueur="dark",
        adversaire="light"
    )

    assert isinstance(score, (int, float))


def test_choose_move_returns_none_when_no_piece_can_move():
    state = make_state(color="blue")

    assert choose_move(state) is None


def test_choose_move_dark_player_returns_a_move():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    move = choose_move(state)

    assert move is not None
    assert move[0] == [7, 7]


def test_choose_move_light_player_returns_a_move():
    board = empty_board()
    board[0][0][1] = ("red", "light")

    state = make_state(
        players=["adversaire", BOT_NAME],
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

    state = make_state(color="red", board=board)

    move = choose_move(state)

    assert move is not None
    assert move[0] == [7, 7]


def test_choose_move_ignores_wrong_color():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")

    state = make_state(color="red", board=board)

    assert choose_move(state) is None


def test_choose_move_ignores_opponent_piece():
    board = empty_board()
    board[7][7][1] = ("blue", "light")

    state = make_state(color="blue", board=board)

    assert choose_move(state) is None


def test_choose_move_does_not_go_outside_board():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    start, end = choose_move(state)

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

    assert choose_move(state) is None


def test_choose_move_without_required_color_can_play_any_own_piece():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")

    state = make_state(color=None, board=board)

    move = choose_move(state)

    assert move is not None
    assert move[0] == [7, 7]


def test_choose_move_returns_none_when_not_my_turn():
    board = empty_board()
    board[7][7][1] = ("blue", "dark")

    state = make_state(color="blue", board=board, current=1)

    assert choose_move(state) is None


def test_choose_move_raises_error_if_bot_name_not_in_players():
    state = make_state(players=["joueur1", "joueur2"])

    with pytest.raises(ValueError):
        choose_move(state)


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
        players=["adversaire", BOT_NAME],
        current=1,
        color="blue",
        board=board
    )

    move = choose_move(state)

    assert is_winning_move(move, "light")


def test_choose_move_fallback_when_time_limit_is_tiny(monkeypatch):
    monkeypatch.setattr(bot, "TIME_LIMIT", 0.000001)
    monkeypatch.setattr(bot, "SAFETY_MARGIN", 0)
    monkeypatch.setattr(bot.random, "choice", lambda moves: moves[0])

    board = empty_board()
    board[7][3][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    move = choose_move(state)

    assert move is not None


def test_choose_move_resets_deadline_after_success():
    board = empty_board()
    board[7][3][1] = ("blue", "dark")

    state = make_state(color="blue", board=board)

    choose_move(state)

    assert bot._deadline is None


def test_choose_move_resets_deadline_after_no_move():
    state = make_state(color="blue")

    choose_move(state)

    assert bot._deadline is None