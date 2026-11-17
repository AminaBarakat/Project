"""Round 1: the duels.

All 4 duels happen at the same time. In every duel both players play ALL FOUR
games, one after another, in the same order. Each duel starts with a different
game, so no two duels look the same. Every game has its own 60-second timer and
one try. As soon as you answer, your next game starts: nobody waits for a timer.

    intro (5 s) → game 1 → game 2 → game 3 → game 4 → [tie-breaker] → results (8 s) → Round 2

Who wins a duel:
    - more right answers                        → wins
    - same number right (at least one)          → faster total time wins
    - both got nothing right                    → tie-breaker question

When every player has finished, the results appear straight away.

Time matters here, so every function takes `now` (seconds, like time.time()). The
app passes the real time; the tests pass made-up times so they can "jump" ahead
instead of waiting.

Nobody's phone is in charge of the clock. Every phone regularly calls `settle()`,
which applies whatever is due: moving a player on when a game's time runs out,
deciding duels, starting tie-breakers, showing results, moving on to Round 2.
Doing it twice changes nothing, so it doesn't matter which phone gets there first.

This module only looks at tournament["duels"], tournament["round1"],
tournament["status"] and tournament["eliminated"]; it never imports tournament.py.
"""

import copy
import random

INTRO_SECONDS = 5
GAME_SECONDS = 60
TIEBREAK_SECONDS = 30
RESULTS_SECONDS = 8
MEMORY_SHOW_SECONDS = 7      # the memory items are shown for the first 7 s of that game

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
    "Never enter a room with food in it.",
    "Never enter a room where something ticks or chimes.",
    "The guard never leaves the piano.",
    "From the room with the fireplace, the Exit is exactly three doors away.",
    "Read every door carefully: the house only tells you once.",
]
ESCAPE_MAP = {
    "Start": ["Hall", "Kitchen", "Conservatory"],
    "Hall": ["Library", "Music Room", "Gallery"],
    "Kitchen": ["Pantry", "Gallery"],
    "Conservatory": ["Chapel", "Library"],
    "Library": ["Billiard Room", "Clock Room", "Chapel"],
    "Music Room": ["Study"],
    "Gallery": ["Study", "Ballroom"],
    "Chapel": ["Study", "Greenhouse"],
    "Billiard Room": ["Study", "Storage Room"],
    "Clock Room": ["Study"],
    "Study": ["Exit", "Wine Cellar"],
    "Ballroom": ["Exit"],
}   # rooms not listed as keys are dead ends
ESCAPE_ROOMS = {   # what you read on each door; the clues are hidden in here
    "Hall": "Tall windows over the garden.",
    "Kitchen": "It smells of fresh bread.",
    "Conservatory": "Breakfast is laid out among the palms.",
    "Library": "A fire crackles in the hearth.",
    "Music Room": "A grand piano… and heavy footsteps.",
    "Gallery": "Old portraits watch you pass.",
    "Pantry": "Shelves full of jam jars.",
    "Chapel": "A bell chimes every quarter hour.",
    "Billiard Room": "Green felt and silence.",
    "Clock Room": "Dozens of clocks on every wall.",
    "Greenhouse": "Glass walls, no other door.",
    "Study": "A desk covered in maps.",
    "Storage Room": "Dusty boxes, no other door.",
    "Ballroom": "A grandfather clock stands in the corner.",
    "Wine Cellar": "Bottles, cheese and a locked gate.",
    "Exit": "Fresh night air!",
}
# What the descriptions above reveal (used by the tests to prove there's one safe route).
ESCAPE_HIDDEN = {
    "food": {"Kitchen", "Conservatory", "Pantry", "Wine Cellar"},
    "ticks": {"Clock Room", "Ballroom", "Chapel"},
    "guard": {"Music Room"},
    "fireplace": {"Library"},
}
ESCAPE_ANSWER = ["Hall", "Library", "Billiard Room", "Study", "Exit"]

MEMORY_ITEMS = ["Key", "Compass", "Rose", "Coin", "Feather",
                "Chess piece", "Candle", "Pocket watch", "Hourglass", "Lantern"]
MEMORY_MISSING = ["Compass", "Candle", "Hourglass"]          # the three that disappear
MEMORY_REMAINING = ["Lantern", "Feather", "Coin", "Pocket watch", "Key", "Chess piece", "Rose"]  # shuffled

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
        # Exactly three different items, picked from the ten.
        count = len(MEMORY_MISSING)
        if not isinstance(value, list) or len(value) != count:
            return "invalid"
        names = {item.casefold(): item for item in MEMORY_ITEMS}
        picked = {names.get(v.strip().casefold()) if isinstance(v, str) else None for v in value}
        if None in picked or len(picked) != count:
            return "invalid"
        return "right" if picked == set(MEMORY_MISSING) else "wrong"

    return "invalid"


# --- setting up --------------------------------------------------------------

def new_round(duels, now, rng=None):
    """The Round 1 part of the tournament, created when the host starts.

    The four games are shuffled once; duel 1 plays them in that order, duel 2
    starts one further along, and so on. So every duel plays all four games, but
    each duel starts with a different one."""
    games = list(GAMES)
    (rng or random.Random()).shuffle(games)
    starts_at = now + INTRO_SECONDS
    return {
        "starts_at": starts_at,
        "orders": [games[i % len(games):] + games[:i % len(games)] for i in range(len(duels))],
        # For each player: when their current game started, and how each finished game went.
        # A result is {"correct": True/False, "seconds": time taken, "timed_out": True/False}.
        "players": {pid: {"game_started_at": starts_at, "results": []}
                    for duel in duels for pid in duel},
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


def order_of(tour, player_id):
    """The four game ids this player plays, in order."""
    return tour["round1"]["orders"][duel_index(tour, player_id)]


def game_number(tour, player_id):
    """0, 1, 2 or 3 for the game being played; 4 when all four are done."""
    return len(tour["round1"]["players"][player_id]["results"])


def current_game(tour, player_id):
    """The game id this player is on now, or None when they've finished all four."""
    n = game_number(tour, player_id)
    order = order_of(tour, player_id)
    return order[n] if n < len(order) else None


def is_done(tour, player_id):
    return game_number(tour, player_id) == len(GAMES)


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
    if not is_done(tour, player_id):
        return "playing"
    return "waiting"


def memory_items_visible(tour, player_id, now):
    """During the first seconds of the memory game, the items are on screen."""
    started = tour["round1"]["players"][player_id]["game_started_at"]
    return now < started + MEMORY_SHOW_SECONDS


def _ceil(x):
    return max(0, int(x + 0.999))


def seconds_left(tour, player_id, now):
    """Seconds left on this player's current game."""
    started = tour["round1"]["players"][player_id]["game_started_at"]
    return _ceil(started + GAME_SECONDS - now)


def intro_seconds_left(tour, now):
    return _ceil(tour["round1"]["starts_at"] - now)


def tiebreak_seconds_left(tour, player_id, now):
    tiebreak = tour["round1"]["tiebreaks"].get(str(duel_index(tour, player_id)))
    return _ceil(tiebreak["started_at"] + TIEBREAK_SECONDS - now) if tiebreak else 0


def results_seconds_left(tour, now):
    at = tour["round1"]["results_at"]
    return 0 if at is None else _ceil(at + RESULTS_SECONDS - now)


def finished_count(tour):
    return sum(1 for pid in tour["round1"]["players"] if is_done(tour, pid))


def points(tour, player_id):
    """How many games this player got right."""
    return sum(1 for r in tour["round1"]["players"][player_id]["results"] if r["correct"])


def total_seconds(tour, player_id):
    """Time spent on all finished games (a game that ran out counts as the full 60 s)."""
    return round(sum(r["seconds"] for r in tour["round1"]["players"][player_id]["results"]), 1)


# --- actions ------------------------------------------------------------------

def answer(tour, player_id, number, value, now):
    """A player answers game `number` (0–3) of their duel. One try per game.

    `number` says which game the screen was showing, so an answer that arrives
    just after that game's time ran out is refused instead of being counted
    for the next game."""
    if tour["status"] != "round1" or player_id not in tour["round1"]["players"]:
        return tour, "You can't answer right now."
    r1 = tour["round1"]
    if now < r1["starts_at"]:
        return tour, "Wait, the game hasn't started yet!"
    settled, _ = settle(tour, now)                 # apply any timer that just ran out
    if is_done(settled, player_id):
        return tour, "You've finished all four games."
    if number != game_number(settled, player_id):
        return tour, "Time ran out on that one!"
    game = current_game(settled, player_id)
    if game == "memory" and memory_items_visible(settled, player_id, now):
        return tour, "Wait until the items are hidden."
    result = check(game, value)
    if result == "invalid":
        return tour, _format_hint(game)

    new = copy.deepcopy(settled)
    player = new["round1"]["players"][player_id]
    player["results"].append({
        "correct": result == "right",
        "seconds": round(now - player["game_started_at"], 1),
        "timed_out": False,
    })
    player["game_started_at"] = now               # the next game starts straight away
    new, _ = settle(new, now)
    return new, "✅ Correct!" if result == "right" else "❌ Not quite."


def _format_hint(game):
    return {
        "number_lock": "The code is 4 different digits.",
        "pattern": "Pick one of the four tiles.",
        "escape_route": "Keep going until you reach the end of a path.",
        "memory": "Pick exactly three items.",
    }.get(game, "That answer isn't valid.")


def answer_tiebreak(tour, player_id, value, now, rng=None):
    """A player answers the tie-breaker question (one try)."""
    if tour["status"] != "round1" or player_id not in tour["round1"]["players"]:
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
        # 1. A game whose 60 s ran out counts as not answered; the next one starts then.
        for pid, player in r1["players"].items():
            while len(player["results"]) < len(GAMES) and now >= player["game_started_at"] + GAME_SECONDS:
                player["results"].append({"correct": False, "seconds": GAME_SECONDS, "timed_out": True})
                player["game_started_at"] += GAME_SECONDS

        # 2. Decide every duel where both players are done.
        for i, (a, b) in enumerate(new["duels"]):
            if r1["results"][i] is None:
                _decide_duel(new, i, a, b, now, rng)

        # 3. All duels decided: show the results straight away.
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
    if not (is_done(tour, a) and is_done(tour, b)):
        return                                        # someone is still playing

    score = {pid: points(tour, pid) for pid in (a, b)}
    time = {pid: total_seconds(tour, pid) for pid in (a, b)}
    if score[a] != score[b]:
        _record(tour, i, a if score[a] > score[b] else b, a, b, "more right answers", score, time)
        return
    if score[a] > 0 and time[a] != time[b]:
        _record(tour, i, a if time[a] < time[b] else b, a, b, "faster", score, time)
        return

    # Nothing right for either of them (or a perfect draw): tie-breaker.
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
    _record(tour, i, winner, a, b, how, score, time)


def _record(tour, i, winner, a, b, how, score, time):
    loser = b if winner == a else a
    tour["round1"]["results"][i] = {"winner": winner, "loser": loser, "decided_by": how,
                                    "points": score, "seconds": time}
