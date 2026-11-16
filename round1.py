"""Round 1: the duels.

All 4 duels happen at the same time. Each duel gets ONE game, drawn at random, and
every duel gets a different one. Both players in a duel play the same game on their
own phone, with one try and 60 seconds.

    intro (5 s) → game (60 s) → [tie-breaker (30 s)] → results (8 s) → Round 2

Who wins a duel:
    - only one player is right                → they win
    - both are right                           → the faster one wins
    - both are wrong (or ran out of time)      → tie-breaker question

Time matters here, so every function takes `now` (seconds, like time.time()). The
app passes the real time; the tests pass made-up times so they can "jump" ahead
instead of waiting.

Nobody's phone is in charge of the clock. Every phone regularly calls `settle()`,
which applies whatever is due: closing games when time runs out, deciding duels,
starting tie-breakers, showing results, moving on to Round 2. Doing it twice
changes nothing, so it doesn't matter which phone gets there first.

This module only looks at tournament["duels"], tournament["round1"],
tournament["status"] and tournament["eliminated"]; it never imports tournament.py.
"""

import copy
import random

INTRO_SECONDS = 5
GAME_SECONDS = 60
TIEBREAK_SECONDS = 30
RESULTS_SECONDS = 8
MEMORY_SHOW_SECONDS = 6      # the memory items are shown for the first 6 s of the game

# --- the four games -------------------------------------------------------------
# Every puzzle below has exactly one answer; tests/test_round1.py checks that by
# trying every possibility.

NUMBER_LOCK_RULE = "The code has 4 digits, all different."
NUMBER_LOCK_CLUES = [
    ("4865", "One digit is right and in the right place; one is right but in the wrong place"),
    ("0423", "Two digits are right, but both are in the wrong place"),
    ("5874", "One digit is right but in the wrong place"),
    ("6753", "One digit is right and in the right place; one is right but in the wrong place"),
    ("2731", "One digit is right but in the wrong place"),
]
NUMBER_LOCK_FEEDBACK = {"4865": (1, 1), "0423": (0, 2), "5874": (0, 1), "6753": (1, 1), "2731": (0, 1)}
NUMBER_LOCK_ANSWER = "6205"

# A 4 × 4 wall: every row and every column has each shape once and each colour once.
PATTERN_GRID = [
    [("triangle", "royal"), ("square", "purple"), ("circle", "silver"), ("diamond", "ice")],
    [("square", "ice"), ("triangle", "silver"), ("diamond", "purple"), ("circle", "royal")],
    [("circle", "purple"), None, ("triangle", "ice"), ("square", "silver")],
    [("diamond", "silver"), ("circle", "ice"), ("square", "royal"), ("triangle", "purple")],
]   # None is the missing tile
PATTERN_OPTIONS = {
    "A": ("circle", "royal"),
    "B": ("diamond", "purple"),
    "C": ("diamond", "royal"),
    "D": ("square", "royal"),
}
PATTERN_ANSWER = "C"

ESCAPE_CLUES = [
    "Avoid any room with food in it.",
    "Avoid any room where something ticks.",
    "A guard patrols the Conservatory.",
    "The portraits in the Gallery hide an alarm.",
    "The Exit is reached through the Study.",
]
ESCAPE_MAP = {
    "Start": ["Hall", "Kitchen", "Conservatory"],
    "Hall": ["Library", "Clock Room", "Gallery"],
    "Kitchen": ["Pantry", "Gallery"],
    "Conservatory": ["Greenhouse", "Library"],
    "Library": ["Study", "Storage Room"],
    "Gallery": ["Study", "Ballroom"],
    "Clock Room": ["Study"],
    "Study": ["Exit", "Wine Cellar"],
    "Ballroom": ["Exit"],
}   # rooms not listed as keys are dead ends
ESCAPE_ROOMS = {   # what you see on each door
    "Hall": "A grand staircase, very quiet.",
    "Kitchen": "It smells of fresh bread.",
    "Conservatory": "Footsteps echo between the palms.",
    "Library": "Books from floor to ceiling.",
    "Clock Room": "Dozens of clocks on every wall.",
    "Gallery": "Old portraits watch you pass.",
    "Pantry": "Shelves full of jam jars.",
    "Greenhouse": "Glass walls, no other door.",
    "Study": "A desk covered in maps.",
    "Storage Room": "Dusty boxes, no other door.",
    "Ballroom": "A grandfather clock stands in the corner.",
    "Wine Cellar": "Bottles, cheese and a locked gate.",
    "Exit": "Fresh night air!",
}
ESCAPE_ANSWER = ["Hall", "Library", "Study", "Exit"]

MEMORY_ITEMS = ["Key", "Compass", "Rose", "Coin", "Feather", "Chess piece", "Candle", "Pocket watch"]
MEMORY_MISSING = ["Compass", "Candle"]          # the two that disappear
MEMORY_REMAINING = ["Feather", "Coin", "Pocket watch", "Key", "Chess piece", "Rose"]   # shuffled order

GAMES = {
    "number_lock": "🔐 Number Lock",
    "pattern": "🧩 Pattern Wall",
    "escape_route": "🗺️ Escape Route",
    "memory": "🃏 Memory Table",
}

TIEBREAK_QUESTION = ("I am a two-digit number. My digits add up to 9. "
                     "My digits multiply to 20. My first digit is smaller than my second.")
TIEBREAK_ANSWER = "45"


def check(game, value):
    """Is this answer 'right', 'wrong', or 'invalid' (wrong format: doesn't use the try)?"""
    if game == "number_lock":
        code = value.strip() if isinstance(value, str) else ""
        if len(code) != 4 or not code.isdigit() or len(set(code)) != 4:
            return "invalid"
        return "right" if code == NUMBER_LOCK_ANSWER else "wrong"

    if game == "pattern":
        if value not in PATTERN_OPTIONS:
            return "invalid"
        return "right" if value == PATTERN_ANSWER else "wrong"

    if game == "escape_route":
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

    if game == "memory":
        # Exactly two different items, picked from the eight.
        if not isinstance(value, list) or len(value) != 2:
            return "invalid"
        names = {item.casefold(): item for item in MEMORY_ITEMS}
        picked = {names.get(v.strip().casefold()) if isinstance(v, str) else None for v in value}
        if None in picked or len(picked) != 2:
            return "invalid"
        return "right" if picked == set(MEMORY_MISSING) else "wrong"

    return "invalid"


# --- setting up --------------------------------------------------------------

def new_round(duels, now, rng=None):
    """The Round 1 part of the tournament, created when the host starts.
    Each duel gets a different game, in random order."""
    games = list(GAMES)
    (rng or random.Random()).shuffle(games)
    starts_at = now + INTRO_SECONDS
    return {
        "starts_at": starts_at,
        "ends_at": starts_at + GAME_SECONDS,
        "games": games[:len(duels)],          # games[i] is the game of duel i
        "answers": {pid: None for duel in duels for pid in duel},
        # an answer is {"correct": True/False, "at": time}; None = not answered yet
        "tiebreaks": {},          # duel number (as text) → {"started_at", "answers": {pid: {...}}}
        "results": [None] * len(duels),
        "results_at": None,
    }


# --- what a player can see ---------------------------------------------------

def duel_index(tour, player_id):
    for i, duel in enumerate(tour["duels"]):
        if player_id in duel:
            return i
    return None


def game_of(tour, player_id):
    """The game id this player plays, e.g. 'escape_route'."""
    return tour["round1"]["games"][duel_index(tour, player_id)]


def is_done(tour, player_id, now):
    """Answered, or out of time."""
    return tour["round1"]["answers"][player_id] is not None or now >= tour["round1"]["ends_at"]


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
    if not is_done(tour, player_id, now):
        return "playing"
    return "waiting"


def memory_items_visible(tour, now):
    """During the first few seconds of the game, the memory items are on screen."""
    return now < tour["round1"]["starts_at"] + MEMORY_SHOW_SECONDS


def _ceil(x):
    return max(0, int(x + 0.999))


def seconds_left(tour, now):
    return _ceil(tour["round1"]["ends_at"] - now)


def intro_seconds_left(tour, now):
    return _ceil(tour["round1"]["starts_at"] - now)


def tiebreak_seconds_left(tour, player_id, now):
    tiebreak = tour["round1"]["tiebreaks"].get(str(duel_index(tour, player_id)))
    return _ceil(tiebreak["started_at"] + TIEBREAK_SECONDS - now) if tiebreak else 0


def results_seconds_left(tour, now):
    at = tour["round1"]["results_at"]
    return 0 if at is None else _ceil(at + RESULTS_SECONDS - now)


def finished_count(tour, now):
    return sum(1 for pid in tour["round1"]["answers"] if is_done(tour, pid, now))


def time_taken(tour, player_id):
    """Seconds from the start of the game to this player's answer, or None."""
    answer = tour["round1"]["answers"][player_id]
    return None if answer is None else round(answer["at"] - tour["round1"]["starts_at"], 1)


# --- actions ------------------------------------------------------------------

def answer(tour, player_id, value, now):
    """A player answers their duel's game. One try."""
    if tour["status"] != "round1" or player_id not in tour["round1"]["answers"]:
        return tour, "You can't answer right now."
    r1 = tour["round1"]
    if now < r1["starts_at"]:
        return tour, "Wait, the game hasn't started yet!"
    if r1["answers"][player_id] is not None:
        return tour, "You've already answered."
    if now >= r1["ends_at"]:
        return tour, "Time's up!"
    game = game_of(tour, player_id)
    if game == "memory" and memory_items_visible(tour, now):
        return tour, "Wait until the items are hidden."
    result = check(game, value)
    if result == "invalid":
        return tour, _format_hint(game)

    new = copy.deepcopy(tour)
    new["round1"]["answers"][player_id] = {"correct": result == "right", "at": now}
    new, _ = settle(new, now)
    return new, "✅ Correct!" if result == "right" else "❌ Not quite."


def _format_hint(game):
    return {
        "number_lock": "The code is 4 different digits.",
        "pattern": "Pick one of the four tiles.",
        "escape_route": "Keep going until you reach the end of a path.",
        "memory": "Pick exactly two items.",
    }.get(game, "That answer isn't valid.")


def answer_tiebreak(tour, player_id, value, now, rng=None):
    """A player answers the tie-breaker question (one try)."""
    if tour["status"] != "round1" or player_id not in tour["round1"]["answers"]:
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
        for i, (a, b) in enumerate(new["duels"]):
            if r1["results"][i] is None:
                _decide_duel(new, i, a, b, now, rng)

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
    if not (is_done(tour, a, now) and is_done(tour, b, now)):
        return                                        # someone is still playing

    right = [pid for pid in (a, b) if (r1["answers"][pid] or {}).get("correct")]
    if len(right) == 1:
        _record(tour, i, right[0], a, b, "right answer")
        return
    if len(right) == 2:
        faster = min(right, key=lambda pid: r1["answers"][pid]["at"])
        _record(tour, i, faster, a, b, "faster")
        return

    # Both wrong (or out of time): tie-breaker.
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
        winner, how = min(answers, key=lambda pid: answers[pid]["at"]), "tie-breaker speed"
    else:
        winner, how = (rng or random.Random()).choice([a, b]), "draw"
    _record(tour, i, winner, a, b, how)


def _record(tour, i, winner, a, b, how):
    loser = b if winner == a else a
    tour["round1"]["results"][i] = {"winner": winner, "loser": loser, "decided_by": how}
