"""Round 1: the Challenge Board.

All 4 duels happen at the same time. Both players in a duel get the same four
challenges on their own phone and have 3 minutes. One point per right answer.

    intro (5 s) → playing (3 min) → [tie-breaker (30 s)] → results (8 s) → Round 2

Time matters here, so every function takes `now` (seconds, like time.time()). The
app passes the real time; the tests pass made-up times so they can "jump" a few
minutes ahead instead of waiting.

Nobody's phone is in charge of the clock. Every phone regularly calls `settle()`,
which applies whatever is due: closing boards when time runs out, deciding duels,
starting tie-breakers, showing results, moving on to Round 2. Doing it twice
changes nothing, so it doesn't matter which phone gets there first.

This module only looks at tournament["duels"], tournament["round1"],
tournament["status"] and tournament["eliminated"]; it never imports tournament.py.
"""

import copy
import random

INTRO_SECONDS = 5
ROUND_SECONDS = 180
TIEBREAK_SECONDS = 30
RESULTS_SECONDS = 8

# --- the four challenges -----------------------------------------------------

NUMBER_LOCK_CLUES = [
    ("682", "One digit is correct and in the right place"),
    ("614", "One digit is correct but in the wrong place"),
    ("206", "Two digits are correct, but both are in the wrong place"),
    ("738", "No digits are correct"),
    ("780", "One digit is correct but in the wrong place"),
]
NUMBER_LOCK_ANSWER = "042"          # the only code that fits all five clues

PATTERN_GRID = [["▲", "■", "●"], ["■", "●", "▲"], ["●", "▲", "?"]]
PATTERN_OPTIONS = {"triangle": "▲", "square": "■", "circle": "●"}
PATTERN_ANSWER = "square"

ESCAPE_CLUES = [
    "Avoid rooms containing food.",
    "Avoid rooms containing clocks.",
    "The exit is reached through the room with books.",
]
ESCAPE_MAP = {
    "Start": ["Hall", "Kitchen"],
    "Hall": ["Library", "Clock Room"],
    "Library": ["Exit", "Storage Room"],
}   # rooms not listed as keys are dead ends
ESCAPE_ANSWER = ["Hall", "Library", "Exit"]

MEMORY_ITEMS = ["Key", "Compass", "Rose", "Coin", "Feather", "Chess piece"]
MEMORY_ANSWER = "Compass"

CHALLENGES = {
    "number_lock": "🔐 Number Lock",
    "pattern": "🧩 Pattern Wall",
    "escape_route": "🗺️ Escape Route",
    "memory": "🃏 Memory Table",
}

TIEBREAK_QUESTION = ("I am a two-digit number. My digits add up to 9. "
                     "My digits multiply to 20. My first digit is smaller than my second.")
TIEBREAK_ANSWER = "45"


def check(challenge_id, value):
    """Is this answer 'right', 'wrong', or 'invalid' (wrong format: doesn't use the try)?"""
    if challenge_id == "number_lock":
        code = value.strip() if isinstance(value, str) else ""
        if len(code) != 3 or not code.isdigit():
            return "invalid"
        return "right" if code == NUMBER_LOCK_ANSWER else "wrong"

    if challenge_id == "pattern":
        if value not in PATTERN_OPTIONS:
            return "invalid"
        return "right" if value == PATTERN_ANSWER else "wrong"

    if challenge_id == "escape_route":
        if not isinstance(value, list) or not value:
            return "invalid"
        here = "Start"
        for room in value:
            if room not in ESCAPE_MAP.get(here, []):
                return "invalid"            # jumped between rooms that aren't connected
            here = room
        if here in ESCAPE_MAP:
            return "invalid"                # stopped before reaching a dead end
        return "right" if value == ESCAPE_ANSWER else "wrong"

    if challenge_id == "memory":
        if not isinstance(value, str):
            return "invalid"
        names = {item.casefold(): item for item in MEMORY_ITEMS}
        item = names.get(value.strip().casefold())
        if item is None:
            return "invalid"
        return "right" if item == MEMORY_ANSWER else "wrong"

    return "invalid"


# --- setting up --------------------------------------------------------------

def new_round(duels, now):
    """The Round 1 part of the tournament, created when the host starts."""
    starts_at = now + INTRO_SECONDS
    return {
        "starts_at": starts_at,
        "ends_at": starts_at + ROUND_SECONDS,
        "boards": {pid: {"answers": {}, "finished_at": None} for duel in duels for pid in duel},
        "tiebreaks": {},          # duel number (as text) → {"started_at", "answers": {pid: {...}}}
        "results": [None] * len(duels),
        "results_at": None,
    }


# --- what a player can see ---------------------------------------------------

def score(tour, player_id):
    answers = tour["round1"]["boards"][player_id]["answers"]
    return sum(1 for result in answers.values() if result)


def duel_index(tour, player_id):
    for i, duel in enumerate(tour["duels"]):
        if player_id in duel:
            return i
    return None


def phase(tour, player_id, now):
    """What this player should see: 'intro', 'playing', 'waiting', 'tiebreak',
    'results' or 'round2'."""
    if tour["status"] == "round2":
        return "round2"
    if tour["status"] == "round1_results":
        return "results"
    r1 = tour["round1"]
    if now < r1["starts_at"]:
        return "intro"
    i = duel_index(tour, player_id)
    tiebreak = r1["tiebreaks"].get(str(i))
    if tiebreak and r1["results"][i] is None and player_id not in tiebreak["answers"]:
        return "tiebreak"
    if r1["boards"][player_id]["finished_at"] is None:
        return "playing"
    return "waiting"


def seconds_left(tour, now):
    return max(0, int(tour["round1"]["ends_at"] - now + 0.999))


def tiebreak_seconds_left(tour, player_id, now):
    tiebreak = tour["round1"]["tiebreaks"].get(str(duel_index(tour, player_id)))
    if not tiebreak:
        return 0
    return max(0, int(tiebreak["started_at"] + TIEBREAK_SECONDS - now + 0.999))


def results_seconds_left(tour, now):
    at = tour["round1"]["results_at"]
    return 0 if at is None else max(0, int(at + RESULTS_SECONDS - now + 0.999))


def finished_count(tour):
    return sum(1 for b in tour["round1"]["boards"].values() if b["finished_at"] is not None)


# --- actions ------------------------------------------------------------------

def answer(tour, player_id, challenge_id, value, now):
    """A player answers one challenge on their board."""
    if tour["status"] != "round1" or player_id not in tour["round1"]["boards"]:
        return tour, "You can't answer right now."
    r1 = tour["round1"]
    board = r1["boards"][player_id]
    if now < r1["starts_at"]:
        return tour, "Wait, the round hasn't started yet!"
    if board["finished_at"] is not None or now >= r1["ends_at"]:
        return tour, "Your board is closed."
    if challenge_id not in CHALLENGES:
        return tour, "That challenge doesn't exist."
    if challenge_id in board["answers"]:
        return tour, "You've already answered that one."
    result = check(challenge_id, value)
    if result == "invalid":
        return tour, _format_hint(challenge_id)

    new = copy.deepcopy(tour)
    new_board = new["round1"]["boards"][player_id]
    new_board["answers"][challenge_id] = result == "right"
    if len(new_board["answers"]) == len(CHALLENGES):
        new_board["finished_at"] = now
    new, _ = settle(new, now)
    return new, "✅ Correct!" if result == "right" else "❌ Not quite."


def _format_hint(challenge_id):
    return {
        "number_lock": "The code is exactly 3 digits.",
        "pattern": "Pick one of the three symbols.",
        "escape_route": "Keep going until you reach the end of a path.",
        "memory": "Pick one of the items.",
    }.get(challenge_id, "That answer isn't valid.")


def answer_tiebreak(tour, player_id, value, now, rng=None):
    """A player answers the tie-breaker question (one try)."""
    if tour["status"] != "round1" or player_id not in tour["round1"]["boards"]:
        return tour, "There's no tie-breaker right now."
    i = duel_index(tour, player_id)
    tiebreak = tour["round1"]["tiebreaks"].get(str(i))
    if not tiebreak or tour["round1"]["results"][i] is not None:
        return tour, "There's no tie-breaker for you."
    if player_id in tiebreak["answers"]:
        return tour, "You've already answered."
    if now >= tiebreak["started_at"] + TIEBREAK_SECONDS:
        return tour, "Time's up!"
    text = value.strip() if isinstance(value, str) else ""
    if not text.isdigit():
        return tour, "Type a number."

    new = copy.deepcopy(tour)
    new["round1"]["tiebreaks"][str(i)]["answers"][player_id] = {
        "correct": text == TIEBREAK_ANSWER, "at": now,
    }
    new, _ = settle(new, now, rng)
    return new, "Answer locked in!"


def settle(tour, now, rng=None):
    """Applies everything that is due at time `now`. Safe to call as often as you like."""
    if tour["status"] not in ("round1", "round1_results"):
        return tour, ""
    new = copy.deepcopy(tour)
    r1 = new["round1"]

    if new["status"] == "round1":
        # 1. Time's up: close every unfinished board (unanswered challenges count as 0).
        if now >= r1["ends_at"]:
            for board in r1["boards"].values():
                if board["finished_at"] is None:
                    board["finished_at"] = r1["ends_at"]

        # 2. Decide every duel that can be decided.
        for i, (a, b) in enumerate(new["duels"]):
            if r1["results"][i] is None:
                _decide_duel(new, i, a, b, now, rng)

        # 3. All duels decided: show the results.
        if all(r1["results"]):
            new["status"] = "round1_results"
            r1["results_at"] = now
            new["eliminated"] = new.get("eliminated", []) + [r["loser"] for r in r1["results"]]

    elif now >= r1["results_at"] + RESULTS_SECONDS:
        new["status"] = "round2"

    if new == tour:
        return tour, ""
    return new, "Updated."


def _decide_duel(tour, i, a, b, now, rng):
    r1 = tour["round1"]
    board_a, board_b = r1["boards"][a], r1["boards"][b]
    if board_a["finished_at"] is None or board_b["finished_at"] is None:
        return                                        # someone is still playing

    points = {a: score(tour, a), b: score(tour, b)}
    if points[a] != points[b]:
        winner = a if points[a] > points[b] else b
        _record(tour, i, winner, b if winner == a else a, points, "score")
        return

    # Same score: tie-breaker.
    tiebreak = r1["tiebreaks"].get(str(i))
    if tiebreak is None:
        r1["tiebreaks"][str(i)] = {"started_at": now, "answers": {}}
        return
    answers = tiebreak["answers"]
    timed_out = now >= tiebreak["started_at"] + TIEBREAK_SECONDS
    if len(answers) < 2 and not timed_out:
        return                                        # still waiting for answers

    right = [pid for pid in (a, b) if answers.get(pid, {}).get("correct")]
    if len(right) == 1:
        winner, how = right[0], "tie-breaker"
    elif answers:
        # Both right or both wrong (or only one answered in time): fastest answer wins.
        winner, how = min(answers, key=lambda pid: answers[pid]["at"]), "fastest answer"
    else:
        winner, how = (rng or random.Random()).choice([a, b]), "draw"
    _record(tour, i, winner, b if winner == a else a, points, how)


def _record(tour, i, winner, loser, points, how):
    tour["round1"]["results"][i] = {"winner": winner, "loser": loser, "points": points, "decided_by": how}
