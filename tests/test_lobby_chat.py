"""Tests for lobby_chat.py: greetings while the table fills up."""

import lobby_chat as chat

NOW = 1_000_000.0


def lobby(*ids):
    return {"code": "ABCD", "status": "lobby", "host_id": ids[0],
            "players": [{"id": pid, "name": pid.upper(), "appearance": None} for pid in ids]}


def test_a_seated_player_can_greet_and_everyone_sees_a_bubble():
    tour, message = chat.greet(lobby("p0", "p1"), "p1", "wave", NOW)
    assert message == "Hi everyone!"
    assert chat.bubbles(tour, NOW + 2) == {"p1": {"id": 1, "by": "p1", "kind": "wave", "at": NOW, "age": 2.0}}
    assert chat.bubbles(tour, NOW + chat.BUBBLE_SECONDS) == {}


def test_only_players_at_the_table_and_only_known_greetings():
    tour = lobby("p0")
    assert chat.greet(tour, "zz", "wave", NOW)[1] == "You're not at this table."
    assert chat.greet(tour, "p0", "<b>", NOW)[1] == "That greeting doesn't exist."


def test_no_greetings_once_the_game_has_started():
    tour = lobby("p0")
    tour["status"] = "round1"
    assert chat.greet(tour, "p0", "wave", NOW)[1] == "The game has already started."


def test_a_short_wait_between_greetings():
    tour, _ = chat.greet(lobby("p0", "p1"), "p0", "wave", NOW)
    assert chat.greet(tour, "p0", "hurry", NOW + 1)[1] == "One moment, detective!"
    tour, message = chat.greet(tour, "p0", "hurry", NOW + chat.COOLDOWN)
    assert message == "Hurry up, we're waiting!"


def test_one_bubble_per_player_the_newest_one():
    tour = lobby("p0", "p1")
    tour, _ = chat.greet(tour, "p0", "wave", NOW)
    tour, _ = chat.greet(tour, "p0", "good_luck", NOW + 3)
    assert chat.bubbles(tour, NOW + 4)["p0"]["kind"] == "good_luck"


def test_feed_is_newest_first_and_skips_players_who_left():
    tour = lobby("p0", "p1", "p2")
    for k, (pid, kind) in enumerate((("p0", "wave"), ("p1", "watching"), ("p2", "hurry"))):
        tour, _ = chat.greet(tour, pid, kind, NOW + k)
    assert chat.feed(tour) == [("p2", "hurry"), ("p1", "watching"), ("p0", "wave")]
    tour["players"] = [p for p in tour["players"] if p["id"] != "p1"]       # p1 left
    assert chat.feed(tour) == [("p2", "hurry"), ("p0", "wave")]
    assert "p1" not in chat.bubbles(tour, NOW + 2)
    assert chat.latest_id(tour) == 3


def test_only_the_latest_greetings_are_kept_and_the_original_is_untouched():
    start = lobby("p0")
    tour = start
    for k in range(chat.KEEP + 4):
        tour, _ = chat.greet(tour, "p0", "wave", NOW + k * chat.COOLDOWN)
    assert len(tour["lobby_chat"]["greetings"]) == chat.KEEP
    assert "lobby_chat" not in start
