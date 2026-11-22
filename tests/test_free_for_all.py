"""Tests for the 5-player game: the host picks 5 seats, everyone plays Round 1
together, the weakest result (fewest right, then slowest) is out, and the other
four go to Round 2. Ties for last place answer the tie-breaker."""

import random

import pytest

import round1 as r1
import tournament as t

T0 = 1_000_000.0
START = T0 + r1.INTRO_SECONDS
NAMES = ["Ana", "Bruno", "Carla", "Dani", "Eva"]
IDS = [f"p{i}" for i in range(5)]
FAST = r1.MEMORY_SHOW_SECONDS + 1


def lobby(size=5):
    tour, _ = t.new_tournament("ABCD", "p0", NAMES[0], size=size)
    return tour


def started(seed=1):
    tour = lobby()
    for i in range(1, 5):
        tour, _ = t.join(tour, f"p{i}", NAMES[i])
    tour, message = t.start(tour, "p0", random.Random(seed), now=T0)
    assert message == "Everyone against everyone. Let the games begin!"
    return tour


def answer(tour, pid, right, think):
    game = r1.current_game(tour, pid)
    p = r1.puzzle(tour, game)
    if right:
        value = {"memory": p.get("missing")}.get(game, p.get("answer"))
    elif game == "number_lock":
        value = "123" if p["answer"] != "123" else "456"
    elif game == "pattern":
        value = next(k for k in p["options"] if k != p["answer"])
    elif game == "memory":
        value = p["missing"][:2] + [next(i for i in p["options"] if i not in p["missing"])]
    else:
        value = next(r for r in _routes(p["map"]) if r != p["answer"])
    now = tour["round1"]["players"][pid]["game_started_at"] + think
    tour, _ = r1.answer(tour, pid, r1.game_number(tour, pid), value, now)
    return tour


def _routes(doors, here="Start", so=()):
    if here not in doors:
        yield list(so)
        return
    for room in doors[here]:
        yield from _routes(doors, room, so + (room,))


def play(tour, plans):
    """plans: {pid: (rights, think)}; everyone plays at the same time, in time order."""
    todo = {pid: (list(rights), think) for pid, (rights, think) in plans.items()}
    while any(r for r, _ in todo.values()):
        pid = min((p for p in todo if todo[p][0]),
                  key=lambda p: tour["round1"]["players"][p]["game_started_at"] + todo[p][1])
        rights, think = todo[pid]
        tour = answer(tour, pid, rights.pop(0), think)
    return tour


# --- table size ------------------------------------------------------------------

def test_the_host_picks_5_or_8_seats():
    assert t.table_size(lobby(5)) == 5 and t.table_size(lobby(8)) == 8
    assert t.new_tournament("ABCD", "p0", "Ana", size=6)[0] is None
    assert t.table_size({"players": []}) == 8                  # older games: 8


def test_a_5_seat_table_is_full_at_5_and_starts_with_exactly_5():
    tour = lobby(5)
    for i in range(1, 4):
        tour, _ = t.join(tour, f"p{i}", NAMES[i])
    assert t.start(tour, "p0", now=T0)[1] == "You need exactly 5 players to start (4 so far)."
    tour, _ = t.join(tour, "p4", NAMES[4])
    assert t.join(tour, "p5", "Zed")[1] == "This tournament is full (5 players)."


def test_5_players_play_round1_as_one_group_with_the_same_order():
    tour = started()
    assert r1.is_free_for_all(tour)
    assert tour["duels"] == [sorted(tour["duels"][0], key=IDS.index)] or set(tour["duels"][0]) == set(IDS)
    assert len(tour["round1"]["orders"]) == 1
    assert t.opponent_of(tour, "p0") is None                   # no single opponent
    assert not r1.is_free_for_all({"duels": [["a", "b"], ["c", "d"]]})


# --- who is out ---------------------------------------------------------------------

def test_fewest_right_answers_is_out_and_four_go_through():
    tour = play(started(), {"p0": ([True] * 4, 8), "p1": ([True, True, True, False], 7),
                            "p2": ([True, True, False, False], 6), "p3": ([True, False, True, True], 9),
                            "p4": ([False, False, True, False], 6)})
    result = tour["round1"]["results"][0]
    assert tour["status"] == "round1_results"
    assert result["loser"] == "p4" and result["decided_by"] == "fewest right answers"
    assert set(r1.advancing(tour)) == {"p0", "p1", "p2", "p3"} and len(r1.advancing(tour)) == 4
    assert r1.advancing(tour)[0] == "p0"                       # best first
    assert tour["eliminated"] == ["p4"]


def test_same_right_answers_the_slowest_is_out():
    plans = {pid: ([True, True, False, False], 6 + k) for k, pid in enumerate(IDS)}   # p4 slowest
    tour = play(started(), plans)
    result = tour["round1"]["results"][0]
    assert result["loser"] == "p4" and result["decided_by"] == "slowest"


def tied_for_last():
    """p3 and p4: same right answers, same time: a tie-breaker between just those two."""
    plans = {"p0": ([True] * 4, 6), "p1": ([True] * 4, 7), "p2": ([True] * 4, 8),
             "p3": ([False] * 4, 6), "p4": ([False] * 4, 6)}
    return play(started(), plans)


def test_a_tie_for_last_place_opens_a_tie_breaker_only_for_the_tied_players():
    tour = tied_for_last()
    now = tour["round1"]["tiebreaks"]["0"]["started_at"]       # when the tie-breaker opened
    assert tour["round1"]["results"][0] is None
    assert r1.phase(tour, "p3", now) == "tiebreak" and r1.phase(tour, "p4", now) == "tiebreak"
    assert r1.phase(tour, "p0", now) == "waiting"
    assert r1.answer_tiebreak(tour, "p0", "45", now + 1)[1] == "There's no tie-breaker for you."


def test_tie_breaker_wrong_answer_goes_out():
    tour = tied_for_last()
    now = tour["round1"]["tiebreaks"]["0"]["started_at"]       # when the tie-breaker opened
    tour, _ = r1.answer_tiebreak(tour, "p3", "54", now + 1)        # wrong, but first
    tour, _ = r1.answer_tiebreak(tour, "p4", "45", now + 3)        # right
    assert tour["round1"]["results"][0]["loser"] == "p3"
    assert tour["round1"]["results"][0]["decided_by"] == "tie-breaker"


def test_tie_breaker_both_right_the_slower_goes_out():
    tour = tied_for_last()
    now = tour["round1"]["tiebreaks"]["0"]["started_at"]       # when the tie-breaker opened
    tour, _ = r1.answer_tiebreak(tour, "p4", "45", now + 1)
    tour, _ = r1.answer_tiebreak(tour, "p3", "45", now + 2)
    assert tour["round1"]["results"][0]["loser"] == "p3"


def test_tie_breaker_no_answer_goes_out_when_time_is_up():
    tour = tied_for_last()
    now = tour["round1"]["tiebreaks"]["0"]["started_at"]       # when the tie-breaker opened
    tour, _ = r1.answer_tiebreak(tour, "p4", "54", now + 1)        # wrong, but answered
    tour, _ = r1.settle(tour, now + r1.TIEBREAK_SECONDS + 1)
    assert tour["round1"]["results"][0]["loser"] == "p3"


def test_a_player_who_left_is_the_one_out():
    tour = started()
    tour, message = r1.player_left(tour, "p0", "p2", START + 3)
    assert message == "Marked as gone; they're out of the game."
    tour = play(tour, {pid: ([True] * 4, FAST) for pid in IDS if pid != "p2"})
    assert tour["round1"]["results"][0]["loser"] == "p2"
    assert tour["round1"]["results"][0]["decided_by"] == "left the game"


def test_host_can_end_round1_early_in_the_5_player_game():
    tour = play(started(), {"p0": ([True, True], FAST), "p1": ([True], FAST)})
    tour, _ = r1.end_round_now(tour, "p0", START + 20, random.Random(1))
    assert tour["status"] == "round1_results"
    assert len(r1.advancing(tour)) == 4


def test_round2_starts_with_the_four_who_went_through():
    tour = play(started(), {pid: ([True] * (4 - k) + [False] * k, FAST) for k, pid in enumerate(IDS)})
    going = r1.advancing(tour)
    for pid in going:
        tour, _ = r1.mark_ready(tour, pid, START + 200, random.Random(2))
    assert tour["status"] == "round2"
    assert set(tour["round2"]["players"]) == set(going)


@pytest.mark.parametrize("seed", range(5))
def test_everyone_runs_out_of_time_still_ends_with_four_going_through(seed):
    tour, _ = r1.settle(started(seed), START + sum(r1.GAME_TIMES.values()))
    tour, _ = r1.end_round_now(tour, "p0", START + 200, random.Random(seed))
    assert tour["status"] == "round1_results" and len(r1.advancing(tour)) == 4
