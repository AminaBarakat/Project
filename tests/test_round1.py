"""Tests for round1.py: one random game per duel, 60 seconds, right answer then speed,
tie-breakers, results and moving on to Round 2. Times are made up (T0 = when the
host pressed Start), so the tests can jump ahead instead of waiting."""

import copy
import random

import round1 as r1
import tournament as t

T0 = 1_000_000.0
START = T0 + r1.INTRO_SECONDS                 # the moment the games appear
PLAY = START + r1.MEMORY_SHOW_SECONDS + 1     # a moment after the memory items are hidden
END = START + r1.GAME_SECONDS
NAMES = ["Ana", "Bruno", "Carla", "Dani", "Eva", "Filipe", "Gui", "Helena"]

RIGHT = {
    "number_lock": "042",
    "pattern": "square",
    "escape_route": ["Hall", "Library", "Exit"],
    "memory": "Compass",
}
WRONG = {
    "number_lock": "999",
    "pattern": "circle",
    "escape_route": ["Kitchen"],
    "memory": "Key",
}


def started(seed=1):
    """A started tournament with 8 players (ids p0..p7)."""
    tour, _ = t.new_tournament("ABCD", "p0", NAMES[0])
    for i in range(1, 8):
        tour, _ = t.join(tour, f"p{i}", NAMES[i])
    tour, _ = t.start(tour, "p0", random.Random(seed), now=T0)
    return tour


def answer(tour, pid, right, now=PLAY):
    """pid answers their own game, rightly or wrongly."""
    game = r1.game_of(tour, pid)
    tour, _ = r1.answer(tour, pid, (RIGHT if right else WRONG)[game], now)
    return tour


def assert_refused(tour, result):
    after, message = result
    assert after == tour and message


# --- the games themselves ------------------------------------------------------

def test_number_lock_answer_is_the_only_code_that_fits_the_clues():
    def feedback(guess, code):
        right_place = sum(g == c for g, c in zip(guess, code))
        common = sum(min(guess.count(d), code.count(d)) for d in set(guess))
        return right_place, common - right_place

    expected = {"682": (1, 0), "614": (0, 1), "206": (0, 2), "738": (0, 0), "780": (0, 1)}
    fits = [f"{n:03}" for n in range(1000)
            if all(feedback(g, f"{n:03}") == expected[g] for g, _ in r1.NUMBER_LOCK_CLUES)]
    assert fits == [r1.NUMBER_LOCK_ANSWER]


def test_number_lock_checks():
    assert r1.check("number_lock", " 042 ") == "right"
    assert r1.check("number_lock", "420") == "wrong"
    for bad in ["42", "0420", "4a2", "", None]:
        assert r1.check("number_lock", bad) == "invalid"


def test_pattern_checks():
    assert r1.check("pattern", "square") == "right"
    assert r1.check("pattern", "circle") == "wrong"
    assert r1.check("pattern", "star") == "invalid"


def test_escape_route_checks():
    assert r1.check("escape_route", ["Hall", "Library", "Exit"]) == "right"
    for wrong in (["Kitchen"], ["Hall", "Clock Room"], ["Hall", "Library", "Storage Room"]):
        assert r1.check("escape_route", wrong) == "wrong"
    for bad in (["Hall", "Exit"], ["Hall"], [], "Hall"):
        assert r1.check("escape_route", bad) == "invalid"


def test_memory_checks():
    assert r1.check("memory", "compass") == "right"
    assert r1.check("memory", "Key") == "wrong"
    assert r1.check("memory", "Dragon") == "invalid"


# --- the draw of games --------------------------------------------------------

def test_each_duel_gets_a_different_game():
    tour = started()
    assert sorted(tour["round1"]["games"]) == sorted(r1.GAMES)


def test_both_players_in_a_duel_play_the_same_game():
    tour = started()
    for a, b in tour["duels"]:
        assert r1.game_of(tour, a) == r1.game_of(tour, b)


def test_games_are_drawn_at_random():
    draws = {tuple(started(seed)["round1"]["games"]) for seed in range(20)}
    assert len(draws) > 1


# --- timing -----------------------------------------------------------------------

def test_intro_then_60_seconds_of_game():
    tour = started()
    assert r1.phase(tour, "p0", T0) == "intro"
    assert r1.phase(tour, "p0", START) == "playing"
    assert r1.seconds_left(tour, START) == r1.GAME_SECONDS
    assert r1.phase(tour, "p0", END) == "waiting"


def test_no_answers_during_the_intro_or_after_time():
    tour = started()
    game = r1.game_of(tour, "p0")
    assert_refused(tour, r1.answer(tour, "p0", RIGHT[game], T0 + 1))
    assert_refused(tour, r1.answer(tour, "p0", RIGHT[game], END))


def test_memory_answer_refused_while_items_are_still_shown():
    tour = started()
    pid = next(p for p in tour["round1"]["answers"] if r1.game_of(tour, p) == "memory")
    assert_refused(tour, r1.answer(tour, pid, "Compass", START + 1))
    tour, _ = r1.answer(tour, pid, "Compass", PLAY)
    assert tour["round1"]["answers"][pid]["correct"] is True


# --- answering --------------------------------------------------------------------

def test_one_try_only():
    tour = answer(started(), "p0", right=False)
    game = r1.game_of(tour, "p0")
    assert_refused(tour, r1.answer(tour, "p0", RIGHT[game], PLAY + 1))


def test_invalid_answer_is_refused_and_does_not_use_the_try():
    tour = started()
    game = r1.game_of(tour, "p0")
    bad = {"number_lock": "42", "pattern": "star", "escape_route": ["Hall"], "memory": "Dragon"}[game]
    assert_refused(tour, r1.answer(tour, "p0", bad, PLAY))
    tour = answer(tour, "p0", right=True)
    assert tour["round1"]["answers"]["p0"]["correct"] is True


def test_unknown_player_is_refused():
    tour = started()
    assert_refused(tour, r1.answer(tour, "stranger", "042", PLAY))


def test_answering_does_not_change_the_original():
    tour = started()
    before = copy.deepcopy(tour)
    answer(tour, "p0", right=True)
    assert tour == before


def test_after_answering_the_player_waits():
    tour = answer(started(), "p0", right=True)
    assert r1.phase(tour, "p0", PLAY) == "waiting"
    assert r1.finished_count(tour, PLAY) == 1
    assert r1.time_taken(tour, "p0") == PLAY - START


# --- deciding duels -------------------------------------------------------------

def first_duel(tour):
    return tour["duels"][0]


def test_only_one_right_wins():
    tour = started()
    a, b = first_duel(tour)
    tour = answer(tour, a, right=False, now=PLAY)
    tour = answer(tour, b, right=True, now=PLAY + 10)
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["loser"] == a
    assert result["decided_by"] == "right answer"


def test_both_right_the_faster_wins():
    tour = started()
    a, b = first_duel(tour)
    tour = answer(tour, a, right=True, now=PLAY + 9)
    tour = answer(tour, b, right=True, now=PLAY + 2)
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["decided_by"] == "faster"


def test_duel_waits_until_both_are_done():
    tour = answer(started(), first_duel(started())[0], right=True)
    assert tour["round1"]["results"][0] is None


def test_right_answer_beats_running_out_of_time():
    tour = started()
    a, b = first_duel(tour)
    tour = answer(tour, a, right=True)
    tour, _ = r1.settle(tour, END)
    assert tour["round1"]["results"][0]["winner"] == a


def test_settle_twice_changes_nothing_more():
    tour = started()
    once, _ = r1.settle(tour, END)
    twice, _ = r1.settle(once, END)
    assert twice == once


# --- tie-breakers --------------------------------------------------------------

def both_wrong():
    tour = started()
    a, b = first_duel(tour)
    tour = answer(tour, a, right=False)
    tour = answer(tour, b, right=False)
    return tour, a, b


def test_both_wrong_starts_a_tie_breaker():
    tour, a, b = both_wrong()
    assert tour["round1"]["results"][0] is None
    assert r1.phase(tour, a, PLAY) == "tiebreak"
    assert r1.phase(tour, b, PLAY) == "tiebreak"


def test_both_out_of_time_starts_a_tie_breaker():
    tour, _ = r1.settle(started(), END)
    a, _ = first_duel(tour)
    assert r1.phase(tour, a, END) == "tiebreak"


def test_only_right_answer_wins_the_tie_breaker():
    tour, a, b = both_wrong()
    tour, _ = r1.answer_tiebreak(tour, a, "54", PLAY + 1)
    tour, _ = r1.answer_tiebreak(tour, b, "45", PLAY + 2)
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["decided_by"] == "tie-breaker"


def test_tie_breaker_both_right_fastest_wins():
    tour, a, b = both_wrong()
    tour, _ = r1.answer_tiebreak(tour, b, "45", PLAY + 1)
    tour, _ = r1.answer_tiebreak(tour, a, "45", PLAY + 3)
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["decided_by"] == "tie-breaker speed"


def test_tie_breaker_answer_must_be_a_number_and_only_once():
    tour, a, _ = both_wrong()
    assert_refused(tour, r1.answer_tiebreak(tour, a, "forty", PLAY + 1))
    tour, _ = r1.answer_tiebreak(tour, a, "45", PLAY + 1)
    assert_refused(tour, r1.answer_tiebreak(tour, a, "45", PLAY + 2))


def test_tie_breaker_time_up_the_one_who_answered_wins():
    tour, a, b = both_wrong()
    tour, _ = r1.answer_tiebreak(tour, a, "12", PLAY + 1)
    tour, _ = r1.settle(tour, PLAY + r1.TIEBREAK_SECONDS + 1)
    assert tour["round1"]["results"][0]["winner"] == a


def test_tie_breaker_nobody_answers_is_a_fair_draw():
    tour, a, b = both_wrong()
    late = PLAY + r1.TIEBREAK_SECONDS + 1
    first, _ = r1.settle(tour, late, random.Random(3))
    again, _ = r1.settle(tour, late, random.Random(3))
    assert first["round1"]["results"][0]["winner"] in (a, b)
    assert first["round1"]["results"][0]["decided_by"] == "draw"
    assert first == again


def test_no_tie_breaker_without_a_tie():
    tour = started()
    a, b = first_duel(tour)
    tour = answer(answer(tour, a, right=True), b, right=False)
    assert_refused(tour, r1.answer_tiebreak(tour, a, "45", PLAY))


# --- results and Round 2 ------------------------------------------------------

def everyone_done():
    """Every duel decided: the first player is right, the second wrong."""
    tour = started()
    for a, b in tour["duels"]:
        tour = answer(answer(tour, a, right=True), b, right=False)
    return tour


def test_all_duels_decided_shows_results_and_eliminates_the_4_losers():
    tour = everyone_done()
    assert tour["status"] == "round1_results"
    losers = [b for _, b in tour["duels"]]
    assert sorted(tour["eliminated"]) == sorted(losers)
    assert r1.phase(tour, losers[0], PLAY) == "results"


def test_results_move_on_to_round2_after_8_seconds():
    tour = everyone_done()
    early, _ = r1.settle(tour, PLAY + r1.RESULTS_SECONDS - 1)
    assert early["status"] == "round1_results"
    later, _ = r1.settle(tour, PLAY + r1.RESULTS_SECONDS)
    assert later["status"] == "round2"
    assert len(later["eliminated"]) == 4          # not eliminated twice


def test_no_answers_once_results_are_shown():
    tour = everyone_done()
    assert_refused(tour, r1.answer(tour, "p0", "042", PLAY))
