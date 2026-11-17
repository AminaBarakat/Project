"""Tests for round1.py: every duel plays all four games one after another, each
with its own 60-second timer; more right answers wins, then faster total time,
then a tie-breaker; results come as soon as everyone is done.

Times are made up (T0 = when the host pressed Start), so the tests can jump ahead
instead of waiting."""

import copy
import random

import round1 as r1
import tournament as t

T0 = 1_000_000.0
START = T0 + r1.INTRO_SECONDS                 # the moment the first game appears
NAMES = ["Ana", "Bruno", "Carla", "Dani", "Eva", "Filipe", "Gui", "Helena"]
THINK = r1.MEMORY_SHOW_SECONDS + 1            # seconds a test player "thinks" per game

RIGHT = {
    "number_lock": "6205",
    "pattern": "C",
    "escape_route": ["Hall", "Library", "Billiard Room", "Study", "Exit"],
    "memory": ["Compass", "Candle", "Hourglass"],
}
WRONG = {
    "number_lock": "1234",
    "pattern": "A",
    "escape_route": ["Kitchen", "Pantry"],
    "memory": ["Compass", "Candle", "Key"],
}


def started(seed=1):
    """A started tournament with 8 players (ids p0..p7)."""
    tour, _ = t.new_tournament("ABCD", "p0", NAMES[0])
    for i in range(1, 8):
        tour, _ = t.join(tour, f"p{i}", NAMES[i])
    tour, _ = t.start(tour, "p0", random.Random(seed), now=T0)
    return tour


def started_at(tour, pid):
    return tour["round1"]["players"][pid]["game_started_at"]


def play_one(tour, pid, right, think=THINK):
    """pid answers their current game after `think` seconds."""
    game = r1.current_game(tour, pid)
    now = started_at(tour, pid) + think
    tour, _ = r1.answer(tour, pid, r1.game_number(tour, pid), (RIGHT if right else WRONG)[game], now)
    return tour


def play_all(tour, pid, rights, think=THINK):
    """pid plays all four games; rights says which ones they get right."""
    for right in rights:
        tour = play_one(tour, pid, right, think)
    return tour


def assert_refused(tour, result):
    after, message = result
    assert after == tour and message


# --- the games themselves ------------------------------------------------------

def test_number_lock_answer_is_the_only_code_that_fits_the_clues():
    from itertools import permutations

    def feedback(guess, code):
        right_place = sum(g == c for g, c in zip(guess, code))
        return right_place, len(set(guess) & set(code)) - right_place

    codes = ["".join(p) for p in permutations("0123456789", 4)]      # 4 different digits
    fits = [c for c in codes
            if all(feedback(g, c) == r1.NUMBER_LOCK_FEEDBACK[g] for g, _ in r1.NUMBER_LOCK_CLUES)]
    assert fits == [r1.NUMBER_LOCK_ANSWER]


def test_number_lock_clue_texts_match_the_feedback():
    words = {(1, 1): "right place; one", (0, 2): "Two digits", (0, 1): "One digit is right but"}
    for guess, text in r1.NUMBER_LOCK_CLUES:
        assert words[r1.NUMBER_LOCK_FEEDBACK[guess]] in text


def test_number_lock_checks():
    assert r1.check("number_lock", " 6205 ") == "right"
    assert r1.check("number_lock", "6250") == "wrong"
    for bad in ["620", "62055", "62a5", "6605", "", None]:
        assert r1.check("number_lock", bad) == "invalid"


def test_pattern_wall_has_exactly_one_tile_that_fits():
    grid = r1.PATTERN_GRID
    row, col = next((i, j) for i in range(4) for j in range(4) if grid[i][j] is None)
    others = [grid[row][k] for k in range(4) if k != col] + [grid[k][col] for k in range(4) if k != row]
    fits = [key for key, (shape, colour) in r1.PATTERN_OPTIONS.items()
            if shape not in {s for s, _ in others} and colour not in {c for _, c in others}]
    assert fits == [r1.PATTERN_ANSWER]


def test_pattern_checks():
    assert r1.check("pattern", "C") == "right"
    assert r1.check("pattern", "A") == "wrong"
    assert r1.check("pattern", "E") == "invalid"


def test_escape_route_has_exactly_one_safe_path():
    hidden = r1.ESCAPE_HIDDEN
    forbidden = hidden["food"] | hidden["ticks"] | hidden["guard"]

    def routes(here="Start", so_far=()):
        if here not in r1.ESCAPE_MAP:
            yield list(so_far)
            return
        for room in r1.ESCAPE_MAP[here]:
            yield from routes(room, so_far + (room,))

    def safe(route):
        fires = [i for i, room in enumerate(route) if room in hidden["fireplace"]]
        return (route[-1] == "Exit" and not forbidden & set(route)
                and len(fires) == 1 and len(route) - 1 - fires[0] == 3)

    all_routes = list(routes())
    assert len(all_routes) == 28
    assert [r for r in all_routes if safe(r)] == [r1.ESCAPE_ANSWER]


def test_every_escape_room_has_a_description():
    rooms = {room for doors in r1.ESCAPE_MAP.values() for room in doors}
    assert rooms <= set(r1.ESCAPE_ROOMS)
    assert set().union(*r1.ESCAPE_HIDDEN.values()) <= set(r1.ESCAPE_ROOMS)


def test_escape_route_checks():
    assert r1.check("escape_route", ["Hall", "Library", "Billiard Room", "Study", "Exit"]) == "right"
    for wrong in (["Kitchen", "Pantry"],
                  ["Hall", "Library", "Chapel", "Study", "Exit"],           # the bell chimes
                  ["Hall", "Gallery", "Study", "Exit"],                     # no fireplace
                  ["Conservatory", "Library", "Billiard Room", "Study", "Exit"],   # breakfast
                  ["Hall", "Library", "Billiard Room", "Storage Room"]):
        assert r1.check("escape_route", wrong) == "wrong"
    for bad in (["Hall", "Exit"], ["Hall", "Library"], [], "Hall"):
        assert r1.check("escape_route", bad) == "invalid"


def test_memory_shows_the_others_without_the_missing_two():
    assert sorted(r1.MEMORY_REMAINING + r1.MEMORY_MISSING) == sorted(r1.MEMORY_ITEMS)


def test_memory_checks():
    assert r1.check("memory", ["candle", " Compass", "HOURGLASS"]) == "right"
    assert r1.check("memory", ["Compass", "Candle", "Key"]) == "wrong"
    for bad in (["Compass", "Candle"], ["Compass", "Compass", "Candle"], ["Compass", "Candle", "Dragon"],
                ["Compass", "Candle", "Hourglass", "Key"], "Compass"):
        assert r1.check("memory", bad) == "invalid"


# --- the order of games -------------------------------------------------------

def test_every_duel_plays_all_four_games():
    tour = started()
    for order in tour["round1"]["orders"]:
        assert sorted(order) == sorted(r1.GAMES)


def test_each_duel_starts_with_a_different_game():
    tour = started()
    firsts = [order[0] for order in tour["round1"]["orders"]]
    assert sorted(firsts) == sorted(r1.GAMES)


def test_both_players_in_a_duel_get_the_same_order():
    tour = started()
    for a, b in tour["duels"]:
        assert r1.order_of(tour, a) == r1.order_of(tour, b)


def test_order_of_games_is_random():
    draws = {tuple(started(seed)["round1"]["orders"][0]) for seed in range(20)}
    assert len(draws) > 1


# --- timing -----------------------------------------------------------------------

def test_intro_then_the_first_game_with_its_own_60_seconds():
    tour = started()
    assert r1.phase(tour, "p0", T0) == "intro"
    assert r1.phase(tour, "p0", START) == "playing"
    assert r1.seconds_left(tour, "p0", START) == r1.GAME_SECONDS


def test_no_answers_during_the_intro():
    tour = started()
    game = r1.current_game(tour, "p0")
    assert_refused(tour, r1.answer(tour, "p0", 0, RIGHT[game], T0 + 1))


def test_answering_starts_the_next_game_straight_away_with_a_fresh_timer():
    tour = play_one(started(), "p0", right=True, think=12)
    assert r1.game_number(tour, "p0") == 1
    assert started_at(tour, "p0") == START + 12
    assert r1.seconds_left(tour, "p0", START + 12) == r1.GAME_SECONDS


def test_running_out_of_time_moves_on_to_the_next_game():
    tour, _ = r1.settle(started(), START + r1.GAME_SECONDS)
    result = tour["round1"]["players"]["p0"]["results"][0]
    assert result == {"correct": False, "seconds": r1.GAME_SECONDS, "timed_out": True}
    assert r1.game_number(tour, "p0") == 1
    assert started_at(tour, "p0") == START + r1.GAME_SECONDS


def test_an_answer_for_a_game_that_already_ran_out_is_refused():
    tour = started()
    game = r1.current_game(tour, "p0")
    assert_refused(tour, r1.answer(tour, "p0", 0, RIGHT[game], START + r1.GAME_SECONDS + 1))


def test_memory_answer_refused_while_items_are_still_shown():
    tour = started()
    pid = "p0"
    while r1.current_game(tour, pid) != "memory":
        tour = play_one(tour, pid, right=True)
    n = r1.game_number(tour, pid)
    assert_refused(tour, r1.answer(tour, pid, n, RIGHT["memory"], started_at(tour, pid) + 1))
    tour = play_one(tour, pid, right=True)
    assert tour["round1"]["players"][pid]["results"][-1]["correct"] is True


# --- answering --------------------------------------------------------------------

def test_one_try_per_game():
    tour = play_one(started(), "p0", right=False)
    first_game = r1.order_of(tour, "p0")[0]
    assert_refused(tour, r1.answer(tour, "p0", 0, RIGHT[first_game], started_at(tour, "p0") + 1))


def test_invalid_answer_is_refused_and_does_not_use_the_try():
    tour = started()
    game = r1.current_game(tour, "p0")
    bad = {"number_lock": "42", "pattern": "Z", "escape_route": ["Hall"], "memory": ["Dragon"]}[game]
    assert_refused(tour, r1.answer(tour, "p0", 0, bad, START + THINK))
    tour = play_one(tour, "p0", right=True)
    assert tour["round1"]["players"]["p0"]["results"][0]["correct"] is True


def test_unknown_player_is_refused():
    tour = started()
    assert_refused(tour, r1.answer(tour, "stranger", 0, "6205", START + THINK))


def test_answering_does_not_change_the_original():
    tour = started()
    before = copy.deepcopy(tour)
    play_one(tour, "p0", right=True)
    assert tour == before


def test_after_four_games_the_player_waits():
    tour = play_all(started(), "p0", [True, True, False, True])
    assert r1.is_done(tour, "p0")
    assert r1.phase(tour, "p0", started_at(tour, "p0")) == "waiting"
    assert r1.points(tour, "p0") == 3
    assert r1.total_seconds(tour, "p0") == 4 * THINK
    assert r1.finished_count(tour) == 1


# --- deciding duels -------------------------------------------------------------

def first_duel(tour):
    return tour["duels"][0]


def test_more_right_answers_wins():
    tour = started()
    a, b = first_duel(tour)
    tour = play_all(tour, a, [True, True, False, False], think=8)
    tour = play_all(tour, b, [True, True, True, False], think=20)       # slower, but more right
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["loser"] == a
    assert result["decided_by"] == "more right answers"
    assert result["points"] == {a: 2, b: 3}


def test_same_points_the_faster_total_time_wins():
    tour = started()
    a, b = first_duel(tour)
    tour = play_all(tour, a, [True, False, True, False], think=12)
    tour = play_all(tour, b, [False, True, False, True], think=9)
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["decided_by"] == "faster"


def test_duel_waits_until_both_have_played_all_four():
    tour = started()
    a, b = first_duel(tour)
    tour = play_all(tour, a, [True] * 4)
    tour = play_all(tour, b, [True] * 3)
    assert tour["round1"]["results"][0] is None


def test_running_out_of_time_on_everything_ends_the_round():
    tour, _ = r1.settle(started(), START + 4 * r1.GAME_SECONDS)
    assert all(r1.is_done(tour, pid) for pid in tour["round1"]["players"])


def test_settle_twice_changes_nothing_more():
    tour = started()
    once, _ = r1.settle(tour, START + 100)
    twice, _ = r1.settle(once, START + 100)
    assert twice == once


# --- tie-breakers --------------------------------------------------------------

def nothing_right():
    tour = started()
    a, b = first_duel(tour)
    tour = play_all(tour, a, [False] * 4)
    tour = play_all(tour, b, [False] * 4)
    return tour, a, b, started_at(tour, b)


def test_nothing_right_for_both_starts_a_tie_breaker():
    tour, a, b, now = nothing_right()
    assert tour["round1"]["results"][0] is None
    assert r1.phase(tour, a, now) == "tiebreak"
    assert r1.phase(tour, b, now) == "tiebreak"


def test_only_right_answer_wins_the_tie_breaker():
    tour, a, b, now = nothing_right()
    tour, _ = r1.answer_tiebreak(tour, a, "54", now + 1)
    tour, _ = r1.answer_tiebreak(tour, b, "45", now + 2)
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["decided_by"] == "tie-breaker"


def test_tie_breaker_both_right_fastest_wins():
    tour, a, b, now = nothing_right()
    tour, _ = r1.answer_tiebreak(tour, b, "45", now + 1)
    tour, _ = r1.answer_tiebreak(tour, a, "45", now + 3)
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["decided_by"] == "tie-breaker speed"


def test_tie_breaker_answer_must_be_a_number_and_only_once():
    tour, a, _, now = nothing_right()
    assert_refused(tour, r1.answer_tiebreak(tour, a, "forty", now + 1))
    tour, _ = r1.answer_tiebreak(tour, a, "45", now + 1)
    assert_refused(tour, r1.answer_tiebreak(tour, a, "45", now + 2))


def test_tie_breaker_time_up_the_one_who_answered_wins():
    tour, a, b, now = nothing_right()
    tour, _ = r1.answer_tiebreak(tour, a, "12", now + 1)
    tour, _ = r1.settle(tour, now + r1.TIEBREAK_SECONDS + 1)
    assert tour["round1"]["results"][0]["winner"] == a


def test_tie_breaker_nobody_answers_is_a_fair_draw():
    tour, a, b, now = nothing_right()
    late = now + r1.TIEBREAK_SECONDS + 1
    first, _ = r1.settle(tour, late, random.Random(3))
    again, _ = r1.settle(tour, late, random.Random(3))
    assert first["round1"]["results"][0]["winner"] in (a, b)
    assert first["round1"]["results"][0]["decided_by"] == "draw"
    assert first == again


def test_no_tie_breaker_without_a_tie():
    tour = started()
    a, b = first_duel(tour)
    tour = play_all(play_all(tour, a, [True] * 4), b, [False] * 4)
    assert_refused(tour, r1.answer_tiebreak(tour, a, "45", started_at(tour, b)))


# --- results and Round 2 ------------------------------------------------------

def everyone_done():
    """Every duel decided: the first player gets all four right, the second none... except
    one right, so no tie-breakers are needed."""
    tour = started()
    for a, b in tour["duels"]:
        tour = play_all(tour, a, [True] * 4)
        tour = play_all(tour, b, [True, False, False, False])
    return tour


def test_results_come_as_soon_as_everyone_is_done_without_waiting_for_timers():
    tour = everyone_done()
    assert tour["status"] == "round1_results"
    assert tour["round1"]["results_at"] < START + r1.GAME_SECONDS     # long before any timer
    losers = [b for _, b in tour["duels"]]
    assert sorted(tour["eliminated"]) == sorted(losers)


def test_results_move_on_to_round2_after_the_results_time():
    tour = everyone_done()
    at = tour["round1"]["results_at"]
    early, _ = r1.settle(tour, at + r1.RESULTS_SECONDS - 1)
    assert early["status"] == "round1_results"
    later, _ = r1.settle(tour, at + r1.RESULTS_SECONDS)
    assert later["status"] == "round2"
    assert len(later["eliminated"]) == 4          # not eliminated twice


def test_no_answers_once_results_are_shown():
    tour = everyone_done()
    assert_refused(tour, r1.answer(tour, "p0", 0, "6205", START + THINK))
