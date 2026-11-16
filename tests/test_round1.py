"""Tests for round1.py: the four challenges, the timer, tie-breakers, results and
moving on to Round 2. Times are made up (T0 = when the host pressed Start), so the
tests can jump ahead instead of waiting."""

import copy
import random

import round1 as r1
import tournament as t

T0 = 1_000_000.0
PLAY = T0 + r1.INTRO_SECONDS + 1          # a moment after the round has begun
END = T0 + r1.INTRO_SECONDS + r1.ROUND_SECONDS
NAMES = ["Ana", "Bruno", "Carla", "Dani", "Eva", "Filipe", "Gui", "Helena"]

ALL_RIGHT = {
    "number_lock": "042",
    "pattern": "square",
    "escape_route": ["Hall", "Library", "Exit"],
    "memory": "Compass",
}
ALL_WRONG = {
    "number_lock": "999",
    "pattern": "circle",
    "escape_route": ["Kitchen"],
    "memory": "Key",
}


def started():
    """A started tournament with 8 players (ids p0..p7)."""
    tour, _ = t.new_tournament("ABCD", "p0", NAMES[0])
    for i in range(1, 8):
        tour, _ = t.join(tour, f"p{i}", NAMES[i])
    tour, _ = t.start(tour, "p0", random.Random(1), now=T0)
    return tour


def play(tour, pid, n_right, now=PLAY):
    """pid answers all four challenges: the first n_right correctly, the rest wrongly."""
    for k, cid in enumerate(r1.CHALLENGES):
        value = ALL_RIGHT[cid] if k < n_right else ALL_WRONG[cid]
        tour, _ = r1.answer(tour, pid, cid, value, now)
    return tour


def first_duel(tour):
    return tour["duels"][0]


def assert_refused(tour, result):
    after, message = result
    assert after == tour and message


# --- the challenges themselves ------------------------------------------------

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


# --- starting the round -------------------------------------------------------

def test_start_sets_up_round1_with_an_intro_then_3_minutes():
    tour = started()
    assert tour["round1"]["starts_at"] == T0 + r1.INTRO_SECONDS
    assert tour["round1"]["ends_at"] == END
    assert len(tour["round1"]["boards"]) == 8
    assert r1.phase(tour, "p0", T0) == "intro"
    assert r1.phase(tour, "p0", PLAY) == "playing"


def test_no_answers_during_the_intro():
    tour = started()
    assert_refused(tour, r1.answer(tour, "p0", "pattern", "square", T0 + 1))


# --- answering ------------------------------------------------------------------

def test_right_and_wrong_answers_score():
    tour = started()
    tour, _ = r1.answer(tour, "p0", "pattern", "square", PLAY)
    tour, _ = r1.answer(tour, "p0", "memory", "Key", PLAY)
    assert r1.score(tour, "p0") == 1


def test_invalid_answer_is_refused_and_does_not_use_the_try():
    tour = started()
    assert_refused(tour, r1.answer(tour, "p0", "number_lock", "42", PLAY))
    tour, _ = r1.answer(tour, "p0", "number_lock", "042", PLAY)
    assert r1.score(tour, "p0") == 1


def test_each_challenge_can_be_answered_once():
    tour = started()
    tour, _ = r1.answer(tour, "p0", "pattern", "circle", PLAY)
    assert_refused(tour, r1.answer(tour, "p0", "pattern", "square", PLAY))


def test_unknown_challenge_and_unknown_player_are_refused():
    tour = started()
    assert_refused(tour, r1.answer(tour, "p0", "riddle", "x", PLAY))
    assert_refused(tour, r1.answer(tour, "stranger", "pattern", "square", PLAY))


def test_answering_does_not_change_the_original():
    tour = started()
    before = copy.deepcopy(tour)
    r1.answer(tour, "p0", "pattern", "square", PLAY)
    assert tour == before


def test_board_is_finished_after_four_answers_and_player_waits():
    tour = play(started(), "p0", 3)
    assert tour["round1"]["boards"]["p0"]["finished_at"] == PLAY
    assert r1.phase(tour, "p0", PLAY) == "waiting"
    assert r1.finished_count(tour) == 1


def test_no_answers_after_time_is_up():
    tour = started()
    assert_refused(tour, r1.answer(tour, "p0", "pattern", "square", END + 1))


# --- deciding duels -------------------------------------------------------------

def test_higher_score_wins_the_duel_as_soon_as_both_are_done():
    tour = started()
    a, b = first_duel(tour)
    tour = play(tour, a, 3)
    tour = play(tour, b, 1)
    result = tour["round1"]["results"][0]
    assert result["winner"] == a and result["loser"] == b
    assert result["decided_by"] == "score"
    assert tour["status"] == "round1"        # the other duels are still playing


def test_time_up_closes_unfinished_boards_and_counts_what_was_answered():
    tour = started()
    a, b = first_duel(tour)
    tour, _ = r1.answer(tour, a, "pattern", "square", PLAY)      # a: 1 point, never finishes
    tour, _ = r1.settle(tour, END)
    assert tour["round1"]["boards"][a]["finished_at"] == END
    assert tour["round1"]["results"][0]["winner"] == a           # b answered nothing


def test_settle_twice_changes_nothing_more():
    tour = started()
    once, _ = r1.settle(tour, END)
    twice, _ = r1.settle(once, END)
    assert twice == once


# --- tie-breakers --------------------------------------------------------------

def tied():
    tour = started()
    a, b = first_duel(tour)
    tour = play(tour, a, 2)
    tour = play(tour, b, 2)
    return tour, a, b


def test_equal_scores_start_a_tie_breaker():
    tour, a, b = tied()
    assert tour["round1"]["results"][0] is None
    assert r1.phase(tour, a, PLAY) == "tiebreak"
    assert r1.phase(tour, b, PLAY) == "tiebreak"


def test_only_right_answer_wins_the_tie_breaker():
    tour, a, b = tied()
    tour, _ = r1.answer_tiebreak(tour, a, "54", PLAY + 1)
    tour, _ = r1.answer_tiebreak(tour, b, "45", PLAY + 2)
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["decided_by"] == "tie-breaker"


def test_both_right_fastest_wins():
    tour, a, b = tied()
    tour, _ = r1.answer_tiebreak(tour, b, "45", PLAY + 1)
    tour, _ = r1.answer_tiebreak(tour, a, "45", PLAY + 3)
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["decided_by"] == "fastest answer"


def test_tie_breaker_answer_must_be_a_number_and_only_once():
    tour, a, _ = tied()
    assert_refused(tour, r1.answer_tiebreak(tour, a, "forty", PLAY + 1))
    tour, _ = r1.answer_tiebreak(tour, a, "45", PLAY + 1)
    assert_refused(tour, r1.answer_tiebreak(tour, a, "45", PLAY + 2))


def test_tie_breaker_time_up_the_one_who_answered_wins():
    tour, a, b = tied()
    tour, _ = r1.answer_tiebreak(tour, a, "12", PLAY + 1)            # wrong, but answered
    tour, _ = r1.settle(tour, PLAY + r1.TIEBREAK_SECONDS + 1)
    assert tour["round1"]["results"][0]["winner"] == a


def test_tie_breaker_nobody_answers_is_a_fair_draw():
    tour, a, b = tied()
    late = PLAY + r1.TIEBREAK_SECONDS + 1
    first, _ = r1.settle(tour, late, random.Random(3))
    again, _ = r1.settle(tour, late, random.Random(3))
    assert first["round1"]["results"][0]["winner"] in (a, b)
    assert first["round1"]["results"][0]["decided_by"] == "draw"
    assert first == again


def test_no_tie_breaker_without_a_tie():
    tour = started()
    a, b = first_duel(tour)
    tour = play(play(tour, a, 3), b, 1)
    assert_refused(tour, r1.answer_tiebreak(tour, a, "45", PLAY))


# --- results and Round 2 ------------------------------------------------------

def everyone_done():
    """Every duel decided: in each duel, the first player gets 4 and the second 0."""
    tour = started()
    for a, b in tour["duels"]:
        tour = play(play(tour, a, 4), b, 0)
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
    assert_refused(tour, r1.answer(tour, "p0", "pattern", "square", PLAY))
