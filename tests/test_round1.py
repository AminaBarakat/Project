"""Tests for round1.py: every duel plays all four games one after another, each
with its own short timer (see r1.GAME_TIMES); more right answers wins, then faster
total time, then a tie-breaker; results come as soon as everyone is done.

Times are made up (T0 = when the host pressed Start), so the tests can jump ahead
instead of waiting."""

import copy
import random
from itertools import permutations

import pytest

import round1 as r1
import tournament as t

T0 = 1_000_000.0
START = T0 + r1.INTRO_SECONDS                 # the moment the first game appears
NAMES = ["Ana", "Bruno", "Carla", "Dani", "Eva", "Filipe", "Gui", "Helena"]
THINK = r1.MEMORY_SHOW_SECONDS + 1            # seconds a test player "thinks" per game

def all_routes(doors, here="Start", so_far=()):
    """Every complete walk through an escape map, from Start to a dead end."""
    if here not in doors:
        yield list(so_far)
        return
    for room in doors[here]:
        yield from all_routes(doors, room, so_far + (room,))


def right_answer(tour, game):
    p = r1.puzzle(tour, game)
    return {"number_lock": p.get("answer"), "pattern": p.get("answer"),
            "escape_route": p.get("answer"), "memory": p.get("missing")}[game]


def wrong_answer(tour, game):
    p = r1.puzzle(tour, game)
    if game == "number_lock":
        return "123" if p["answer"] != "123" else "456"
    if game == "pattern":
        return next(k for k in p["options"] if k != p["answer"])
    if game == "escape_route":
        return next(r for r in all_routes(p["map"]) if r != p["answer"])
    return p["missing"][:2] + [next(i for i in p["options"] if i not in p["missing"])]


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
    value = right_answer(tour, game) if right else wrong_answer(tour, game)
    tour, _ = r1.answer(tour, pid, r1.game_number(tour, pid), value, now)
    return tour


def play_all(tour, pid, rights, think=THINK):
    """pid plays all four games; rights says which ones they get right."""
    for right in rights:
        tour = play_one(tour, pid, right, think)
    return tour


def play_together(tour, plans):
    """Several players play at the same time, like real phones: plans is a list of
    (pid, rights, think). Answers are given in time order, so nobody's clock runs
    out just because the test played someone else first."""
    todo = {pid: (list(rights), think) for pid, rights, think in plans}
    while any(rights for rights, _ in todo.values()):
        pid = min((p for p in todo if todo[p][0]), key=lambda p: started_at(tour, p) + todo[p][1])
        rights, think = todo[pid]
        tour = play_one(tour, pid, rights.pop(0), think)
    return tour


def assert_refused(tour, result):
    after, message = result
    assert after == tour and message


# --- every version of every game has exactly one answer ----------------------------

LOCKS = r1.PUZZLES["number_lock"]
WALLS = r1.PUZZLES["pattern"]
MAPS = r1.PUZZLES["escape_route"]
MEMORIES = r1.PUZZLES["memory"]


def test_each_game_has_five_versions():
    assert all(len(versions) == 5 for versions in r1.PUZZLES.values())


def test_no_two_versions_of_a_game_are_the_same():
    for versions in r1.PUZZLES.values():
        answers = [str(v.get("answer", v.get("missing"))) + str(v.get("grid", "")) for v in versions]
        assert len(set(answers)) == len(answers)


@pytest.mark.parametrize("lock", LOCKS)
def test_number_lock_answer_is_the_only_code_that_fits_the_clues(lock):
    def feedback(guess, code):
        right_place = sum(g == c for g, c in zip(guess, code))
        return right_place, len(set(guess) & set(code)) - right_place

    codes = ["".join(p) for p in permutations("0123456789", 3)]      # 3 different digits
    fits = [c for c in codes if all(feedback(g, c) == f for g, f in lock["feedback"].items())]
    assert fits == [lock["answer"]]


def test_every_lock_clue_has_a_sentence():
    for lock in LOCKS:
        for feedback in lock["feedback"].values():
            assert r1.clue_text(feedback)


def test_number_lock_checks():
    lock = LOCKS[0]
    assert r1.check("number_lock", " 714 ", lock) == "right"
    assert r1.check("number_lock", "741", lock) == "wrong"
    for bad in ["71", "7140", "7a4", "774", "", None]:
        assert r1.check("number_lock", bad, lock) == "invalid"


@pytest.mark.parametrize("wall", WALLS)
def test_pattern_wall_is_a_proper_wall_with_exactly_one_tile_that_fits(wall):
    grid = wall["grid"]
    tiles = [grid[i][j] for i in range(4) for j in range(4) if grid[i][j]]
    for i in range(4):          # rows and columns never repeat a shape or a colour
        for line in ([grid[i][j] for j in range(4)], [grid[j][i] for j in range(4)]):
            present = [t for t in line if t]
            assert len({s for s, _ in present}) == len(present)
            assert len({c for _, c in present}) == len(present)
    assert len(tiles) == 15
    row, col = next((i, j) for i in range(4) for j in range(4) if grid[i][j] is None)
    others = [grid[row][k] for k in range(4) if k != col] + [grid[k][col] for k in range(4) if k != row]
    fits = [key for key, (shape, colour) in wall["options"].items()
            if shape not in {s for s, _ in others} and colour not in {c for _, c in others}]
    assert fits == [wall["answer"]]


def test_pattern_answers_are_not_always_in_the_same_place():
    assert {wall["answer"] for wall in WALLS} == {"A", "B", "C", "D"}


def test_pattern_checks():
    wall = WALLS[0]
    assert r1.check("pattern", "C", wall) == "right"
    assert r1.check("pattern", "A", wall) == "wrong"
    assert r1.check("pattern", "E", wall) == "invalid"


@pytest.mark.parametrize("house", MAPS)
def test_escape_route_has_exactly_one_safe_path(house):
    hidden = house["hidden"]
    forbidden = hidden["food"] | hidden["ticks"] | hidden["guard"]     # the three house rules

    def safe(route):
        return route[-1] == "Exit" and not forbidden & set(route)

    routes = list(all_routes(house["map"]))
    assert len(routes) >= 7                       # enough wrong turns to make you think
    assert [r for r in routes if safe(r)] == [house["answer"]]


@pytest.mark.parametrize("house", MAPS)
def test_escape_route_is_short(house):
    assert 3 <= len(house["answer"]) <= 4         # 3 or 4 doors, the Exit included


def test_there_are_three_house_rules():
    assert len(r1.ESCAPE_CLUES) == 3


@pytest.mark.parametrize("house", MAPS)
def test_every_door_has_a_description_and_a_picture(house):
    from screens import art
    rooms = {room for doors in house["map"].values() for room in doors}
    assert rooms <= set(house["rooms"])
    assert rooms <= set(art.ROOMS)


def test_escape_route_checks():
    house = MAPS[0]
    assert r1.check("escape_route", ["Gallery", "Study", "Exit"], house) == "right"
    for wrong in (["Kitchen", "Pantry"],                                    # soup
                  ["Hall", "Library", "Exit"],                              # the clock ticks
                  ["Gallery", "Music Room", "Exit"],                        # the guard
                  ["Gallery", "Study", "Storage Room"]):                    # a dead end
        assert r1.check("escape_route", wrong, house) == "wrong"
    for bad in (["Gallery", "Exit"], ["Gallery", "Study"], [], "Gallery"):
        assert r1.check("escape_route", bad, house) == "invalid"


@pytest.mark.parametrize("memory", MEMORIES)
def test_memory_shows_the_others_without_the_missing_three(memory):
    assert len(memory["missing"]) == 3
    assert sorted(memory["remaining"] + memory["missing"]) == sorted(r1.MEMORY_ITEMS)


@pytest.mark.parametrize("memory", MEMORIES)
def test_memory_offers_ten_options_with_decoys(memory):
    options = memory["options"]
    assert len(options) == 10 and len(set(options)) == 10
    assert set(memory["missing"]) <= set(options)                      # the answer is there
    assert len(set(options) & set(memory["remaining"])) == 3           # 3 still on the table
    assert len(set(options) & set(r1.MEMORY_DECOYS)) == 4              # 4 never shown
    assert options[:3] != memory["missing"]                            # not handed over in order


def test_every_memory_object_and_decoy_has_a_drawing():
    from screens import art
    assert set(r1.MEMORY_ITEMS + r1.MEMORY_DECOYS) <= set(art.ITEMS)


def test_memory_checks():
    memory = MEMORIES[0]
    assert r1.check("memory", ["candle", " Compass", "HOURGLASS"], memory) == "right"
    assert r1.check("memory", ["Compass", "Candle", "Key"], memory) == "wrong"        # Key is still there
    assert r1.check("memory", ["Compass", "Candle", "Teacup"], memory) == "wrong"     # a decoy
    for bad in (["Compass", "Candle"], ["Compass", "Compass", "Candle"], ["Compass", "Candle", "Dragon"],
                ["Compass", "Candle", "Feather"],                                     # not among the options
                ["Compass", "Candle", "Hourglass", "Key"], "Compass"):
        assert r1.check("memory", bad, memory) == "invalid"


# --- the draw of versions ---------------------------------------------------------

def test_one_version_of_each_game_is_drawn_per_tournament():
    tour = started()
    assert set(tour["round1"]["puzzles"]) == set(r1.GAMES)
    for game, number in tour["round1"]["puzzles"].items():
        assert 0 <= number < len(r1.PUZZLES[game])


def test_different_tournaments_get_different_puzzles():
    draws = {tuple(sorted(started(seed)["round1"]["puzzles"].items())) for seed in range(20)}
    assert len(draws) > 3


def test_both_players_in_a_duel_answer_the_same_version():
    tour = started()
    a, b = tour["duels"][0]
    for game in r1.GAMES:
        assert right_answer(tour, game) == right_answer(tour, game)     # one draw per tournament
    tour = play_together(tour, [(a, [True] * 4, THINK), (b, [True] * 4, THINK)])
    assert r1.points(tour, a) == r1.points(tour, b) == 4


def test_older_saved_games_without_a_draw_use_the_first_version():
    tour = started()
    del tour["round1"]["puzzles"]
    assert r1.puzzle(tour, "number_lock") is LOCKS[0]


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

def first_limit(tour, pid="p0"):
    return r1.time_limit(r1.current_game(tour, pid))


def test_every_game_has_its_own_short_timer():
    assert r1.GAME_TIMES == {"pattern": 15, "memory": 25, "number_lock": 30, "escape_route": 40}
    assert r1.MEMORY_SHOW_SECONDS == 5 and r1.TIEBREAK_SECONDS == 15
    assert sum(r1.GAME_TIMES.values()) <= 110     # the whole of Round 1 fits in about 2 minutes


def test_intro_then_the_first_game_with_its_own_timer():
    tour = started()
    assert r1.phase(tour, "p0", T0) == "intro"
    assert r1.phase(tour, "p0", START) == "playing"
    assert r1.seconds_left(tour, "p0", START) == first_limit(tour)


def test_no_answers_during_the_intro():
    tour = started()
    game = r1.current_game(tour, "p0")
    assert_refused(tour, r1.answer(tour, "p0", 0, right_answer(tour, game), T0 + 1))


def test_answering_starts_the_next_game_straight_away_with_a_fresh_timer():
    tour = play_one(started(), "p0", right=True, think=12)
    assert r1.game_number(tour, "p0") == 1
    assert started_at(tour, "p0") == START + 12
    assert r1.seconds_left(tour, "p0", START + 12) == first_limit(tour)


def test_running_out_of_time_moves_on_to_the_next_game():
    limit = first_limit(started())
    tour, _ = r1.settle(started(), START + limit)
    result = tour["round1"]["players"]["p0"]["results"][0]
    assert result == {"correct": False, "seconds": limit, "timed_out": True}
    assert r1.game_number(tour, "p0") == 1
    assert started_at(tour, "p0") == START + limit


def test_an_answer_for_a_game_that_already_ran_out_is_refused():
    tour = started()
    game = r1.current_game(tour, "p0")
    assert_refused(tour, r1.answer(tour, "p0", 0, right_answer(tour, game), START + first_limit(tour) + 1))


def test_memory_answer_refused_while_items_are_still_shown():
    tour = started()
    pid = "p0"
    while r1.current_game(tour, pid) != "memory":
        tour = play_one(tour, pid, right=True)
    n = r1.game_number(tour, pid)
    assert_refused(tour, r1.answer(tour, pid, n, right_answer(tour, "memory"), started_at(tour, pid) + 1))
    tour = play_one(tour, pid, right=True)
    assert tour["round1"]["players"][pid]["results"][-1]["correct"] is True


# --- answering --------------------------------------------------------------------

def test_one_try_per_game():
    tour = play_one(started(), "p0", right=False)
    first_game = r1.order_of(tour, "p0")[0]
    assert_refused(tour, r1.answer(tour, "p0", 0, right_answer(tour, first_game), started_at(tour, "p0") + 1))


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
    tour = play_together(tour, [(a, [True, True, False, False], 8),
                                (b, [True, True, True, False], 13)])     # slower, but more right
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["loser"] == a
    assert result["decided_by"] == "more right answers"
    assert result["points"] == {a: 2, b: 3}


def test_same_points_the_faster_total_time_wins():
    tour = started()
    a, b = first_duel(tour)
    tour = play_together(tour, [(a, [True, False, True, False], 12), (b, [False, True, False, True], 9)])
    result = tour["round1"]["results"][0]
    assert result["winner"] == b and result["decided_by"] == "faster"


def test_duel_waits_until_both_have_played_all_four():
    tour = started()
    a, b = first_duel(tour)
    tour = play_together(tour, [(a, [True] * 4, THINK), (b, [True] * 3, THINK)])
    assert tour["round1"]["results"][0] is None


def test_running_out_of_time_on_everything_ends_the_round():
    tour, _ = r1.settle(started(), START + sum(r1.GAME_TIMES.values()))
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
    tour = play_together(tour, [(a, [False] * 4, THINK), (b, [False] * 4, THINK)])
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
    tour = play_together(tour, [(a, [True] * 4, THINK), (b, [False] * 4, THINK)])
    assert_refused(tour, r1.answer_tiebreak(tour, a, "45", started_at(tour, b)))


# --- results and Round 2 ------------------------------------------------------

def everyone_done():
    """Every duel decided: the first player gets all four right, the second none... except
    one right, so no tie-breakers are needed."""
    tour = started()
    plans = []
    for a, b in tour["duels"]:
        plans += [(a, [True] * 4, THINK), (b, [True, False, False, False], THINK)]
    return play_together(tour, plans)


def test_results_come_as_soon_as_everyone_is_done_without_waiting_for_timers():
    tour = everyone_done()
    assert tour["status"] == "round1_results"
    assert tour["round1"]["results_at"] < START + r1.GAME_SECONDS     # long before any timer
    losers = [b for _, b in tour["duels"]]
    assert sorted(tour["eliminated"]) == sorted(losers)


def test_results_wait_for_everyone_to_be_ready_instead_of_a_timer():
    tour = everyone_done()
    later, _ = r1.settle(tour, tour["round1"]["results_at"] + 600)
    assert later["status"] == "round1_results"


def test_no_answers_once_results_are_shown():
    tour = everyone_done()
    assert_refused(tour, r1.answer(tour, "p0", 0, "6205", START + THINK))


# --- host controls ------------------------------------------------------------------

def test_host_can_mark_a_player_who_left_and_the_opponent_goes_through():
    tour = started()
    a, b = next(duel for duel in tour["duels"] if "p0" not in duel)
    tour, _ = r1.player_left(tour, "p0", a, START + 20)
    result = tour["round1"]["results"][r1.duel_index(tour, a)]
    assert result["winner"] == b and result["loser"] == a
    assert result["decided_by"] == "opponent left"
    assert r1.is_done(tour, a)


def test_only_the_host_can_mark_someone_as_gone():
    tour = started()
    a, _ = next(duel for duel in tour["duels"] if "p0" not in duel)
    other = next(pid for pid in tour["round1"]["players"] if pid not in ("p0", a))
    assert_refused(tour, r1.player_left(tour, other, a, START + 20))


def test_host_cannot_mark_themselves_or_twice_or_after_the_duel_is_decided():
    tour = started()
    assert_refused(tour, r1.player_left(tour, "p0", "p0", START + 20))
    a, b = next(duel for duel in tour["duels"] if "p0" not in duel)
    tour, _ = r1.player_left(tour, "p0", a, START + 20)
    assert_refused(tour, r1.player_left(tour, "p0", a, START + 21))
    assert_refused(tour, r1.player_left(tour, "p0", b, START + 21))     # already decided


def test_the_opponent_of_a_player_who_left_can_still_finish_their_games():
    tour = started()
    a, b = next(duel for duel in tour["duels"] if "p0" not in duel)
    tour, _ = r1.player_left(tour, "p0", a, START + 5)
    assert r1.phase(tour, b, START + 6) == "playing"
    tour = play_all(tour, b, [True] * 4)
    assert r1.is_done(tour, b)


def test_host_can_end_the_round_now():
    tour = started()
    a, b = tour["duels"][0]
    tour = play_together(tour, [(a, [True] * 4, THINK), (b, [False] * 4, THINK)])
    tour, _ = r1.end_round_now(tour, "p0", START + 30, random.Random(1))
    assert all(r1.is_done(tour, pid) for pid in tour["round1"]["players"])
    assert tour["status"] == "round1_results"            # nobody waits for any timer
    assert len(tour["eliminated"]) == 4


def test_only_the_host_can_end_the_round_and_not_during_the_intro():
    tour = started()
    assert_refused(tour, r1.end_round_now(tour, "p1", START + 30))
    assert_refused(tour, r1.end_round_now(tour, "p0", T0 + 1))


def test_ending_the_round_closes_open_tie_breakers_too():
    tour = started()
    a, b = tour["duels"][0]
    tour = play_together(tour, [(a, [False] * 4, THINK), (b, [False] * 4, THINK)])
    now = started_at(tour, b)
    tour, _ = r1.answer_tiebreak(tour, a, "45", now + 1)
    tour, _ = r1.end_round_now(tour, "p0", now + 2, random.Random(1))
    assert tour["round1"]["results"][0]["winner"] == a


# --- progress on the race track -----------------------------------------------------

def test_progress_moves_with_games_and_time_but_never_reaches_the_next_game_early():
    tour = started()
    limit = first_limit(tour)
    assert r1.progress(tour, "p0", START) == 0
    assert r1.progress(tour, "p0", START + limit / 2) == 0.5
    assert r1.progress(tour, "p0", START + limit - 0.1) == 0.95
    tour = play_one(tour, "p0", right=False, think=10)
    assert r1.progress(tour, "p0", started_at(tour, "p0")) == 1
    tour = play_all(tour, "p0", [True] * 3)
    assert r1.progress(tour, "p0", started_at(tour, "p0") + 100) == 4


# --- getting ready for Round 2 ------------------------------------------------------

def test_round2_starts_when_all_four_players_going_through_are_ready():
    tour = everyone_done()
    going = r1.advancing(tour)
    assert len(going) == 4
    for pid in going[:3]:
        tour, _ = r1.mark_ready(tour, pid, START + 100)
        assert tour["status"] == "round1_results"
    tour, _ = r1.mark_ready(tour, going[3], START + 101, random.Random(1))
    assert tour["status"] == "round2"
    assert set(tour["round2"]["players"]) == set(going)


def test_eliminated_players_do_not_need_to_get_ready():
    tour = everyone_done()
    out = tour["eliminated"][0]
    assert_refused(tour, r1.mark_ready(tour, out, START + 100))


def test_ready_twice_or_outside_the_results_is_refused():
    tour = everyone_done()
    pid = r1.advancing(tour)[0]
    tour, _ = r1.mark_ready(tour, pid, START + 100)
    assert_refused(tour, r1.mark_ready(tour, pid, START + 101))
    assert_refused(started(), r1.mark_ready(started(), "p0", START + 1))


def test_host_can_start_round2_without_waiting_for_everyone():
    tour = everyone_done()
    assert_refused(tour, r1.start_round2_now(tour, "p1", START + 100))
    tour, _ = r1.start_round2_now(tour, "p0", START + 100, random.Random(2))
    assert tour["status"] == "round2"
    assert set(tour["round2"]["players"]) == set(r1.advancing(tour))
