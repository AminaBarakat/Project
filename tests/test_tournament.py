"""Tests for tournament.py: creating, joining, leaving, removing and starting.

Every refused action must leave the tournament exactly as it was."""

import copy
import random

import tournament as t

NAMES = ["Ana", "Bruno", "Carla", "Dani", "Eva", "Filipe", "Gui", "Helena"]


def lobby_with(n):
    """A lobby with the first n NAMES; Ana (id p0) is the host."""
    tour, _ = t.new_tournament("ABCD", "p0", NAMES[0])
    for i in range(1, n):
        tour, _ = t.join(tour, f"p{i}", NAMES[i])
    return tour


def assert_refused(before, result):
    """The action was refused: same tournament back, and the original wasn't touched."""
    after, message = result
    assert after == before
    assert message


# --- creating -------------------------------------------------------------

def test_new_tournament_has_host_as_first_player():
    tour, _ = t.new_tournament("ABCD", "p0", "  Ana  ")
    assert tour["code"] == "ABCD"
    assert tour["status"] == "lobby"
    assert tour["host_id"] == "p0"
    assert tour["players"] == [{"id": "p0", "name": "Ana", "appearance": None}]
    assert tour["duels"] == []


def test_new_tournament_refuses_bad_host_name():
    for bad in ["", "   ", "x" * 21, None]:
        tour, message = t.new_tournament("ABCD", "p0", bad)
        assert tour is None
        assert message


# --- names ----------------------------------------------------------------

def test_names_are_trimmed_and_inner_spaces_squashed():
    assert t.clean_name("  Ana   Maria ") == ("Ana Maria", None)


def test_name_length_limit():
    assert t.clean_name("x" * 20)[0] == "x" * 20
    assert t.clean_name("x" * 21)[0] is None


# --- joining --------------------------------------------------------------

def test_join_adds_player_in_order_with_empty_appearance():
    tour = lobby_with(3)
    assert [p["name"] for p in tour["players"]] == ["Ana", "Bruno", "Carla"]
    assert tour["players"][2] == {"id": "p2", "name": "Carla", "appearance": None}


def test_join_refuses_duplicate_name_ignoring_capitals_and_spaces():
    tour = lobby_with(2)
    before = copy.deepcopy(tour)
    assert_refused(before, t.join(tour, "p9", " bruno "))
    assert tour == before


def test_join_refuses_an_already_claimed_detective_portrait():
    tour, _ = t.new_tournament("ABCD", "p0", "Ana", appearance="girl_emerald")
    before = copy.deepcopy(tour)
    assert_refused(before, t.join(tour, "p1", "Bruno", appearance="girl_emerald"))
    joined, _ = t.join(tour, "p1", "Bruno", appearance="boy_royal")
    assert joined["players"][1]["appearance"] == "boy_royal"


def test_join_refuses_empty_and_too_long_names():
    tour = lobby_with(2)
    before = copy.deepcopy(tour)
    for bad in ["", "   ", "x" * 21]:
        assert_refused(before, t.join(tour, "p9", bad))


def test_join_refuses_same_player_twice():
    tour = lobby_with(2)
    assert_refused(copy.deepcopy(tour), t.join(tour, "p1", "Someone Else"))


def test_join_refuses_ninth_player():
    tour = lobby_with(8)
    assert_refused(copy.deepcopy(tour), t.join(tour, "p8", "Ines"))


def test_join_refused_after_start():
    tour, _ = t.start(lobby_with(8), "p0", random.Random(1))
    assert_refused(copy.deepcopy(tour), t.join(tour, "p9", "Ines"))


def test_join_does_not_change_the_original():
    tour = lobby_with(2)
    before = copy.deepcopy(tour)
    t.join(tour, "p9", "Ines")
    assert tour == before


# --- leaving and removing -------------------------------------------------

def test_player_can_leave_the_lobby():
    tour, _ = t.leave(lobby_with(3), "p1")
    assert [p["name"] for p in tour["players"]] == ["Ana", "Carla"]


def test_host_cannot_leave():
    tour = lobby_with(3)
    assert_refused(copy.deepcopy(tour), t.leave(tour, "p0"))


def test_leaving_frees_the_name_and_the_seat():
    tour, _ = t.leave(lobby_with(8), "p1")
    tour, _ = t.join(tour, "p9", "Bruno")
    assert len(tour["players"]) == 8


def test_host_can_remove_a_player():
    tour, _ = t.remove_player(lobby_with(3), "p0", "p2")
    assert [p["name"] for p in tour["players"]] == ["Ana", "Bruno"]


def test_only_host_can_remove():
    tour = lobby_with(3)
    assert_refused(copy.deepcopy(tour), t.remove_player(tour, "p1", "p2"))


def test_host_cannot_remove_themselves_or_unknown_players():
    tour = lobby_with(3)
    before = copy.deepcopy(tour)
    assert_refused(before, t.remove_player(tour, "p0", "p0"))
    assert_refused(before, t.remove_player(tour, "p0", "nobody"))


def test_no_leaving_or_removing_after_start():
    tour, _ = t.start(lobby_with(8), "p0", random.Random(1))
    before = copy.deepcopy(tour)
    assert_refused(before, t.leave(tour, "p3"))
    assert_refused(before, t.remove_player(tour, "p0", "p3"))


# --- starting -------------------------------------------------------------

def test_only_host_can_start():
    tour = lobby_with(8)
    assert_refused(copy.deepcopy(tour), t.start(tour, "p1"))


def test_cannot_start_without_exactly_8_players():
    tour = lobby_with(7)
    assert_refused(copy.deepcopy(tour), t.start(tour, "p0"))


def test_start_makes_4_duels_with_every_player_exactly_once():
    tour, _ = t.start(lobby_with(8), "p0", random.Random(1))
    assert tour["status"] == "round1"
    assert len(tour["duels"]) == 4
    everyone = [pid for duel in tour["duels"] for pid in duel]
    assert sorted(everyone) == sorted(f"p{i}" for i in range(8))


def test_draw_is_random_but_repeatable_with_a_seed():
    lobby = lobby_with(8)
    first, _ = t.start(lobby, "p0", random.Random(7))
    again, _ = t.start(lobby, "p0", random.Random(7))
    assert first["duels"] == again["duels"]
    draws = {str(t.start(lobby, "p0", random.Random(seed))[0]["duels"]) for seed in range(20)}
    assert len(draws) > 1          # not always the same pairs


def test_cannot_start_twice():
    tour, _ = t.start(lobby_with(8), "p0", random.Random(1))
    assert_refused(copy.deepcopy(tour), t.start(tour, "p0"))


def test_only_host_can_choose_two_active_finalists_for_round3():
    tour = lobby_with(4)
    tour["status"] = "round2"
    tour["eliminated"] = ["p2", "p3"]
    before = copy.deepcopy(tour)
    assert_refused(before, t.start_round3(tour, "p1", ["p0", "p1"], now=100))
    assert_refused(before, t.start_round3(tour, "p0", ["p0", "p2"], now=100))
    assert_refused(before, t.start_round3(tour, "p0", ["p0"], now=100))

    final, _ = t.start_round3(tour, "p0", ["p0", "p1"], now=100)
    assert final["status"] == "round3"
    assert final["round3"]["finalists"] == ["p0", "p1"]
    assert final["round3"]["story_started_at"] == 100
    assert final["round3"]["starts_at"] is None
    assert final["round3"]["ends_at"] is None


def test_opponent_of_is_symmetric():
    tour, _ = t.start(lobby_with(8), "p0", random.Random(1))
    for i in range(8):
        opponent = t.opponent_of(tour, f"p{i}")
        assert opponent["id"] != f"p{i}"
        assert t.opponent_of(tour, opponent["id"])["id"] == f"p{i}"


def test_opponent_of_before_start_is_none():
    assert t.opponent_of(lobby_with(8), "p1") is None
