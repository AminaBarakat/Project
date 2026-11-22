"""Round 1: the duels.

All 4 duels happen at the same time. In every duel both players play ALL FOUR
games, one after another, in the same order. Each duel starts with a different
game, so no two duels look the same. Every game has its own 60-second timer and
one try. As soon as you answer, your next game starts: nobody waits for a timer.

    intro (5 s) → game 1 → game 2 → game 3 → game 4 → [tie-breaker] → results → everyone ready → Round 2

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
deciding duels, starting tie-breakers, showing results.
Doing it twice changes nothing, so it doesn't matter which phone gets there first.

This module only looks at tournament["duels"], tournament["round1"],
tournament["status"] and tournament["eliminated"]; it never imports tournament.py.
"""

import copy
import random

import round2 as duo_round

INTRO_SECONDS = 8           # long enough for the VS moment and a look at your four games
# Round 1 is about thinking AND reacting fast, so every game has its own short timer.
GAME_TIMES = {
    "pattern": 15,            # one tap
    "memory": 25,             # 5 s to look + 20 s to pick the three missing objects
    "number_lock": 30,        # three digits, three clues
    "escape_route": 30,       # three doors, three house rules
}
GAME_SECONDS = max(GAME_TIMES.values())   # the longest game (kept for older code and tests)
TIEBREAK_SECONDS = 15
RESULTS_SECONDS = 10        # (no longer used to move on: Round 2 starts when everyone is ready)
MEMORY_SHOW_SECONDS = 5      # the memory items are shown for the first 5 s of that game

# --- the four games -------------------------------------------------------------
# Each game has a bank of 5 versions. When the host starts, one version of
# each game is drawn at random, so the puzzles change from tournament to
# tournament (both players in a duel always get the same one). Every version has
# exactly one answer; tests/test_round1.py proves that by trying every possibility.

NUMBER_LOCK_RULE = "The code has 3 digits, all different."

_FEEDBACK_TEXT = {
    (1, 1): "One digit is right and in the right place; one is right but in the wrong place",
    (2, 0): "Two digits are right and in the right place",
    (1, 0): "One digit is right and in the right place",
    (0, 1): "One digit is right but in the wrong place",
    (0, 2): "Two digits are right, but both are in the wrong place",
    (0, 3): "Three digits are right, but all are in the wrong place",
    (0, 0): "No digits are right",
}

ESCAPE_CLUES = [
    "Never enter a room with food in it.",
    "Never enter a room where something ticks or chimes.",
    "Keep away from the guard at the piano.",
]

MEMORY_ITEMS = ["Key", "Compass", "Rose", "Coin", "Feather",
                "Chess piece", "Candle", "Pocket watch", "Hourglass", "Lantern"]
MEMORY_DECOYS = ["Ring", "Teacup", "Spectacles", "Dice", "Umbrella", "Envelope"]   # never shown first

PUZZLES = {
    "number_lock": [
        {"answer": "714",
         "feedback": {"792": (1, 0), "597": (0, 1), "814": (2, 0)}},
        {"answer": "382",
         "feedback": {"508": (0, 1), "532": (1, 1), "728": (0, 2)}},
        {"answer": "905",
         "feedback": {"739": (0, 1), "695": (1, 1), "510": (0, 2)}},
        {"answer": "268",
         "feedback": {"068": (2, 0), "920": (0, 1), "768": (2, 0)}},
        {"answer": "473",
         "feedback": {"257": (0, 1), "467": (1, 1), "735": (0, 2)}},
    ],
    # A 4 × 4 wall: every row and every column has each shape once and each colour once.
    # None is the gap.
    "pattern": [
        {"grid": [
            [("triangle", "purple"), ("square", "royal"), ("circle", "silver"), ("diamond", "ice")],
            [("square", "ice"), ("triangle", "silver"), ("diamond", "royal"), ("circle", "purple")],
            [("circle", "royal"), None, ("triangle", "ice"), ("square", "silver")],
            [("diamond", "silver"), ("circle", "ice"), ("square", "purple"), ("triangle", "royal")]],
         "options": {"A": ("circle", "purple"), "B": ("diamond", "royal"),
                     "C": ("diamond", "purple"), "D": ("square", "purple")},
         "answer": "C"},
        {"grid": [
            [("triangle", "ice"), ("circle", "purple"), ("square", "silver"), ("diamond", "royal")],
            [("square", "royal"), ("diamond", "silver"), ("triangle", "purple"), None],
            [("circle", "silver"), ("triangle", "royal"), ("diamond", "ice"), ("square", "purple")],
            [("diamond", "purple"), ("square", "ice"), ("circle", "royal"), ("triangle", "silver")]],
         "options": {"A": ("square", "silver"), "B": ("circle", "ice"),
                     "C": ("circle", "royal"), "D": ("diamond", "ice")},
         "answer": "B"},
        {"grid": [
            [("triangle", "purple"), ("diamond", "silver"), ("square", "royal"), ("circle", "ice")],
            [("circle", "silver"), ("square", "purple"), ("diamond", "ice"), ("triangle", "royal")],
            [("square", "ice"), ("circle", "royal"), ("triangle", "silver"), ("diamond", "purple")],
            [("diamond", "royal"), ("triangle", "ice"), ("circle", "purple"), None]],
         "options": {"A": ("square", "royal"), "B": ("circle", "silver"),
                     "C": ("diamond", "purple"), "D": ("square", "silver")},
         "answer": "D"},
        {"grid": [
            [("diamond", "royal"), ("square", "ice"), ("triangle", "purple"), ("circle", "silver")],
            [("triangle", "silver"), ("circle", "purple"), ("diamond", "ice"), ("square", "royal")],
            [("square", "purple"), ("diamond", "silver"), ("circle", "royal"), None],
            [("circle", "ice"), ("triangle", "royal"), ("square", "silver"), ("diamond", "purple")]],
         "options": {"A": ("triangle", "ice"), "B": ("triangle", "purple"),
                     "C": ("square", "ice"), "D": ("circle", "silver")},
         "answer": "A"},
        {"grid": [
            [("circle", "silver"), ("triangle", "ice"), ("square", "purple"), ("diamond", "royal")],
            [None, ("circle", "purple"), ("diamond", "ice"), ("square", "silver")],
            [("square", "ice"), ("diamond", "silver"), ("circle", "royal"), ("triangle", "purple")],
            [("diamond", "purple"), ("square", "royal"), ("triangle", "silver"), ("circle", "ice")]],
         "options": {"A": ("triangle", "silver"), "B": ("triangle", "royal"),
                     "C": ("circle", "royal"), "D": ("square", "purple")},
         "answer": "B"},
    ],
    # The same house rules every time, but the doors and what they say change.
    # "hidden" spells out what the descriptions reveal (the tests use it).
    # Short houses: exactly 3 doors from Start to the Exit. "hidden" says which rooms break
    # a house rule; tests/test_round1.py proves exactly one route breaks none.
    "escape_route": [
        {"map": {"Start": ["Gallery", "Hall", "Kitchen"],
                 "Gallery": ["Study", "Music Room"],
                 "Hall": ["Library", "Clock Room"],
                 "Kitchen": ["Pantry", "Library"],
                 "Study": ["Exit", "Storage Room"],
                 "Music Room": ["Exit"],
                 "Library": ["Exit", "Billiard Room"],
                 "Billiard Room": ["Exit"],
                 "Clock Room": ["Exit"]},
         "rooms": {"Gallery": "Portraits glow above a crackling fireplace.",
                   "Hall": "A clock ticks somewhere on the landing.",
                   "Kitchen": "Soup bubbles on the stove.",
                   "Study": "A desk covered in maps.",
                   "Music Room": "A grand piano… and heavy footsteps.",
                   "Library": "Books from floor to ceiling, all quiet.",
                   "Billiard Room": "Green felt and silence.",
                   "Clock Room": "Dozens of clocks on every wall.",
                   "Pantry": "Shelves full of jam jars.",
                   "Storage Room": "Dusty boxes, no other door.",
                   "Exit": "Fresh night air!"},
         "hidden": {"food": set(["Kitchen", "Pantry"]), "ticks": set(["Clock Room", "Hall"]), "guard": set(["Music Room"])},
         "answer": ["Gallery", "Study", "Exit"]},
        {"map": {"Start": ["Hall", "Conservatory", "Chapel"],
                 "Hall": ["Library", "Kitchen"],
                 "Conservatory": ["Billiard Room", "Ballroom"],
                 "Chapel": ["Study", "Greenhouse"],
                 "Library": ["Exit", "Clock Room"],
                 "Kitchen": ["Exit"],
                 "Billiard Room": ["Exit"],
                 "Ballroom": ["Exit"],
                 "Study": ["Exit"],
                 "Clock Room": ["Exit"]},
         "rooms": {"Hall": "Coats on hooks, not a sound.",
                   "Conservatory": "Breakfast is served among the ferns.",
                   "Chapel": "A bell chimes every quarter hour.",
                   "Library": "Books from floor to ceiling, all quiet.",
                   "Kitchen": "Bread is baking in the oven.",
                   "Billiard Room": "Green felt and silence.",
                   "Ballroom": "A banquet is laid out for a party.",
                   "Study": "A desk covered in maps.",
                   "Greenhouse": "Glass walls, no other door.",
                  "Clock Room": "Dozens of clocks on every wall.",
                   "Exit": "Fresh night air!"},
         "hidden": {"food": set(["Ballroom", "Conservatory", "Kitchen"]), "ticks": set(["Chapel", "Clock Room"]), "guard": set([])},
         "answer": ["Hall", "Library", "Exit"]},
        {"map": {"Start": ["Library", "Music Room", "Pantry"],
                 "Library": ["Gallery", "Clock Room"],
                 "Music Room": ["Gallery", "Exit"],
                 "Pantry": ["Exit"],
                 "Gallery": ["Exit", "Greenhouse"],
                 "Clock Room": ["Exit"]},
         "rooms": {"Library": "Books from floor to ceiling, all quiet.",
                   "Music Room": "A grand piano… and heavy footsteps.",
                   "Pantry": "Shelves full of jam jars.",
                   "Gallery": "Portraits glow above a crackling fireplace.",
                   "Clock Room": "Dozens of clocks on every wall.",
                   "Greenhouse": "Glass walls, no other door.",
                   "Exit": "Fresh night air!"},
         "hidden": {"food": set(["Pantry"]), "ticks": set(["Clock Room"]), "guard": set(["Music Room"])},
         "answer": ["Library", "Gallery", "Exit"]},
        {"map": {"Start": ["Conservatory", "Kitchen", "Hall"],
                 "Conservatory": ["Study", "Ballroom"],
                 "Kitchen": ["Study", "Pantry"],
                 "Hall": ["Billiard Room"],
                 "Study": ["Exit", "Chapel"],
                 "Ballroom": ["Exit"],
                 "Billiard Room": ["Exit", "Storage Room"],
                 "Chapel": ["Exit"]},
         "rooms": {"Conservatory": "Ferns and orchids, nothing to eat.",
                   "Kitchen": "Soup bubbles on the stove.",
                   "Hall": "A clock ticks somewhere on the landing.",
                   "Study": "A desk covered in maps.",
                   "Ballroom": "A banquet is laid out for a party.",
                   "Billiard Room": "Green felt and silence.",
                   "Chapel": "A bell chimes every quarter hour.",
                   "Pantry": "Shelves full of jam jars.",
                   "Storage Room": "Dusty boxes, no other door.",
                   "Exit": "Fresh night air!"},
         "hidden": {"food": set(["Ballroom", "Kitchen", "Pantry"]), "ticks": set(["Chapel", "Hall"]), "guard": set([])},
         "answer": ["Conservatory", "Study", "Exit"]},
        {"map": {"Start": ["Study", "Wine Cellar", "Clock Room"],
                 "Study": ["Library", "Music Room"],
                 "Wine Cellar": ["Gallery"],
                 "Clock Room": ["Library"],
                 "Gallery": ["Library", "Kitchen"],
                 "Music Room": ["Exit"],
                 "Library": ["Exit", "Storage Room"],
                 "Kitchen": ["Exit"]},
         "rooms": {"Study": "A desk covered in maps.",
                   "Wine Cellar": "Bottles, cheese and a locked gate.",
                   "Clock Room": "Dozens of clocks on every wall.",
                   "Gallery": "Portraits glow above a crackling fireplace.",
                   "Music Room": "A grand piano… and heavy footsteps.",
                   "Library": "Books from floor to ceiling, all quiet.",
                   "Kitchen": "Bread is baking in the oven.",
                   "Storage Room": "Dusty boxes, no other door.",
                   "Exit": "Fresh night air!"},
         "hidden": {"food": set(["Kitchen", "Wine Cellar"]), "ticks": set(["Clock Room"]), "guard": set(["Music Room"])},
         "answer": ["Study", "Library", "Exit"]},
    ],
    "memory": [
        # "options" are the 10 objects players pick from: the 3 that vanished, 3 that
        # are still on the table, and 4 decoys that were never shown at all.
        {"missing": ["Compass", "Candle", "Hourglass"],
         "remaining": ["Lantern", "Feather", "Coin", "Pocket watch", "Key", "Chess piece", "Rose"],
         "options": ["Ring", "Compass", "Lantern", "Umbrella", "Candle", "Key", "Teacup", "Hourglass", "Coin", "Spectacles"]},
        {"missing": ["Rose", "Key", "Pocket watch"],
         "remaining": ["Hourglass", "Coin", "Candle", "Lantern", "Compass", "Feather", "Chess piece"],
         "options": ["Spectacles", "Ring", "Hourglass", "Coin", "Key", "Pocket watch", "Compass", "Umbrella", "Rose", "Envelope"]},
        {"missing": ["Feather", "Coin", "Lantern"],
         "remaining": ["Pocket watch", "Rose", "Chess piece", "Key", "Hourglass", "Candle", "Compass"],
         "options": ["Hourglass", "Ring", "Feather", "Envelope", "Coin", "Chess piece", "Lantern", "Key", "Umbrella", "Spectacles"]},
        {"missing": ["Chess piece", "Compass", "Rose"],
         "remaining": ["Candle", "Key", "Lantern", "Hourglass", "Feather", "Pocket watch", "Coin"],
         "options": ["Chess piece", "Compass", "Pocket watch", "Envelope", "Rose", "Hourglass", "Lantern", "Dice", "Umbrella", "Ring"]},
        {"missing": ["Hourglass", "Pocket watch", "Feather"],
         "remaining": ["Coin", "Lantern", "Compass", "Rose", "Candle", "Key", "Chess piece"],
         "options": ["Feather", "Chess piece", "Hourglass", "Coin", "Teacup", "Ring", "Candle", "Umbrella", "Pocket watch", "Envelope"]},
    ],
}


def clue_text(feedback):
    """(1, 1) → 'One digit is right and in the right place; one is right but in the wrong place'."""
    return _FEEDBACK_TEXT[feedback]


GAMES = {          # id → name shown on screen (the screens add a drawn icon)
    "number_lock": "Number Lock",
    "pattern": "Pattern Wall",
    "escape_route": "Escape Route",
    "memory": "Memory Table",
}

TIEBREAK_QUESTION = ("I am a two-digit number. My digits add up to 9. "
                     "My digits multiply to 20. My first digit is smaller than my second.")
TIEBREAK_ANSWER = "45"


def check(game, value, puzzle):
    """Is this answer to this version of the game 'right', 'wrong', or 'invalid'
    (wrong format: doesn't use the try)?"""
    if game == "number_lock":
        code = value.strip() if isinstance(value, str) else ""
        if len(code) != 3 or not code.isdigit() or len(set(code)) != 3:
            return "invalid"
        return "right" if code == puzzle["answer"] else "wrong"

    if game == "pattern":
        if value not in puzzle["options"]:
            return "invalid"
        return "right" if value == puzzle["answer"] else "wrong"

    if game == "escape_route":
        doors = puzzle["map"]
        if not isinstance(value, list) or not value:
            return "invalid"
        here = "Start"
        for room in value:
            if room not in doors.get(here, []):
                return "invalid"            # jumped between rooms that aren't connected
            here = room
        if here in doors:
            return "invalid"                # stopped before reaching a dead end
        return "right" if value == puzzle["answer"] else "wrong"

    if game == "memory":
        # Exactly three different objects, picked from this version's ten options.
        count = len(puzzle["missing"])
        if not isinstance(value, list) or len(value) != count:
            return "invalid"
        names = {item.casefold(): item for item in puzzle["options"]}
        picked = {names.get(v.strip().casefold()) if isinstance(v, str) else None for v in value}
        if None in picked or len(picked) != count:
            return "invalid"
        return "right" if picked == set(puzzle["missing"]) else "wrong"

    return "invalid"


# --- setting up --------------------------------------------------------------

def new_round(duels, now, rng=None):
    """The Round 1 part of the tournament, created when the host starts.

    The four games are shuffled once; duel 1 plays them in that order, duel 2
    starts one further along, and so on. So every duel plays all four games, but
    each duel starts with a different one. One version of each puzzle is drawn
    for the whole tournament."""
    rng = rng or random.Random()
    games = list(GAMES)
    rng.shuffle(games)
    starts_at = now + INTRO_SECONDS
    return {
        "starts_at": starts_at,
        # Which version of each game this tournament uses, e.g. {"number_lock": 2, ...}
        "puzzles": {game: rng.randrange(len(PUZZLES[game])) for game in GAMES},
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

def time_limit(game):
    """Seconds a player gets for this game."""
    return GAME_TIMES[game]


def _limit_of(tour, player_id, index):
    """Time limit of this player's game number `index` (0-3)."""
    return GAME_TIMES[order_of(tour, player_id)[index]]


def is_free_for_all(tour):
    """True in the 5-player game: everyone plays Round 1 together (one group, not
    duels), and only the weakest result is out."""
    return any(len(group) > 2 for group in tour.get("duels", []))

def duel_index(tour, player_id):
    for i, duel in enumerate(tour["duels"]):
        if player_id in duel:
            return i
    return None


def puzzle(tour, game):
    """The version of `game` this tournament plays (a dict from PUZZLES)."""
    number = tour["round1"].get("puzzles", {}).get(game, 0)     # 0 for older saved games
    return PUZZLES[game][number]


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
    if (tiebreak and r1["results"][i] is None and player_id in _tiebreak_players(tour, i)
            and player_id not in tiebreak["answers"]):
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
    if is_done(tour, player_id):
        return 0
    started = tour["round1"]["players"][player_id]["game_started_at"]
    return _ceil(started + _limit_of(tour, player_id, game_number(tour, player_id)) - now)


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


def progress(tour, player_id, now):
    """How far along this player is, from 0 (just started) to 4 (all four games done).

    Between answers it creeps forward with the clock, so the race track moves
    smoothly. It says nothing about right or wrong."""
    done = game_number(tour, player_id)
    if done >= len(GAMES):
        return float(len(GAMES))
    started = tour["round1"]["players"][player_id]["game_started_at"]
    into_game = max(0.0, min(0.95, (now - started) / _limit_of(tour, player_id, done)))
    return done + into_game


def has_left(tour, player_id):
    return player_id in tour["round1"].get("left", [])


def points(tour, player_id):
    """How many games this player got right."""
    return sum(1 for r in tour["round1"]["players"][player_id]["results"] if r["correct"])


def total_seconds(tour, player_id):
    """Time spent on all finished games (a game that ran out counts as its full time)."""
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
    result = check(game, value, puzzle(settled, game))
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
    # No "right/wrong" here on purpose: players only find out on the results screen.
    return new, "Answer locked in."


def _format_hint(game):
    return {
        "number_lock": "The code is 3 different digits.",
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
    if (not tiebreak or tour["round1"]["results"][i] is not None
            or player_id not in _tiebreak_players(tour, i)):
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


def _close_remaining_games(player, now, order):
    """Count every game this player hasn't answered as not answered, ending now."""
    while len(player["results"]) < len(GAMES):
        limit = GAME_TIMES[order[len(player["results"])]]
        seconds = round(max(0.0, min(limit, now - player["game_started_at"])), 1)
        player["results"].append({"correct": False, "seconds": seconds, "timed_out": True})
        player["game_started_at"] = now


def player_left(tour, by_id, player_id, now, rng=None):
    """The host marks a player who has left the game (closed their phone, lost signal…).
    They are out, and their opponent goes through."""
    if tour.get("host_id") != by_id:
        return tour, "Only the host can do that."
    if tour["status"] != "round1":
        return tour, "That's only possible during Round 1."
    if player_id not in tour["round1"]["players"]:
        return tour, "That player isn't in this round."
    if player_id == by_id:
        return tour, "You can't mark yourself as gone."
    if has_left(tour, player_id):
        return tour, "That player is already marked as gone."
    i = duel_index(tour, player_id)
    if tour["round1"]["results"][i] is not None:
        return tour, "That round is already decided." if is_free_for_all(tour) else "That duel is already decided."

    new = copy.deepcopy(tour)
    new["round1"].setdefault("left", []).append(player_id)
    _close_remaining_games(new["round1"]["players"][player_id], now, order_of(new, player_id))
    new, _ = settle(new, now, rng)
    if is_free_for_all(tour):
        return new, "Marked as gone; they're out of the game."
    return new, "Marked as gone; their opponent goes through."


def end_round_now(tour, by_id, now, rng=None):
    """The host ends Round 1 early: every unfinished game is closed as not answered."""
    if tour.get("host_id") != by_id:
        return tour, "Only the host can do that."
    if tour["status"] != "round1":
        return tour, "Round 1 isn't being played right now."
    if now < tour["round1"]["starts_at"]:
        return tour, "Round 1 hasn't started yet."

    new = copy.deepcopy(tour)
    for pid, player in new["round1"]["players"].items():
        _close_remaining_games(player, now, order_of(new, pid))
    new, _ = settle(new, now, rng)            # this may open tie-breakers for drawn duels…
    if new["status"] == "round1":
        # …so close every open tie-breaker straight away: whoever answered counts,
        # otherwise it's a draw. Nobody waits.
        new = copy.deepcopy(new)
        for tiebreak in new["round1"]["tiebreaks"].values():
            tiebreak["started_at"] = min(tiebreak["started_at"], now - TIEBREAK_SECONDS)
        new, _ = settle(new, now, rng)
    return new, "Round 1 ended."


def settle(tour, now, rng=None):
    """Applies everything that is due at time `now`. Safe to call as often as you like."""
    if tour["status"] not in ("round1", "round1_results"):
        return tour, ""
    new = copy.deepcopy(tour)
    r1 = new["round1"]

    if new["status"] == "round1":
        # 1. A game whose time ran out counts as not answered; the next one starts then.
        for pid, player in r1["players"].items():
            order = order_of(new, pid)
            while len(player["results"]) < len(GAMES):
                limit = GAME_TIMES[order[len(player["results"])]]
                if now < player["game_started_at"] + limit:
                    break
                player["results"].append({"correct": False, "seconds": limit, "timed_out": True})
                player["game_started_at"] += limit

        # 2. Decide every duel (or, with 5 players, the one group) where everyone is done.
        for i, group in enumerate(new["duels"]):
            if r1["results"][i] is None:
                if len(group) == 2:
                    _decide_duel(new, i, group[0], group[1], now, rng)
                else:
                    _decide_group(new, i, group, now, rng)

        # 3. All duels decided: show the results straight away.
        if all(r1["results"]):
            new["status"] = "round1_results"
            r1["results_at"] = now
            new["eliminated"] = new.get("eliminated", []) + [r["loser"] for r in r1["results"]]

    # (Round 2 no longer starts by itself: see mark_ready and start_round2_now.)

    if new == tour:
        return tour, ""
    return new, "Updated."


# --- getting ready for Round 2 ---------------------------------------------------------

def advancing(tour):
    """The four players going through to Round 2: the duel winners in duel order,
    or (5 players) everyone except the one who is out, best first."""
    going = []
    for result in tour["round1"]["results"]:
        if result:
            going.extend(result["advancing"] if "advancing" in result else [result["winner"]])
    return going


def ready_players(tour):
    return list(tour["round1"].get("ready", []))


def _begin_round2(tour, now, rng):
    tour["status"] = "round2"
    tour["round2"] = duo_round.new_round(advancing(tour), now, rng)


def mark_ready(tour, player_id, now, rng=None):
    """A player going through taps "I'm ready". When all four are ready, Round 2 starts."""
    if tour["status"] != "round1_results":
        return tour, "Round 2 isn't waiting for players right now."
    if player_id not in advancing(tour):
        return tour, "Only the detectives going through to Round 2 need to get ready."
    if player_id in ready_players(tour):
        return tour, "You're already ready."
    new = copy.deepcopy(tour)
    new["round1"].setdefault("ready", []).append(player_id)
    if set(new["round1"]["ready"]) >= set(advancing(new)):
        _begin_round2(new, now, rng)
        return new, "Everyone is ready. Round 2 begins!"
    return new, "Ready!"


def start_round2_now(tour, by_id, now, rng=None):
    """The host starts Round 2 without waiting for everyone to tap "I'm ready"."""
    if tour.get("host_id") != by_id:
        return tour, "Only the host can do that."
    if tour["status"] != "round1_results":
        return tour, "Round 2 can only start from the Round 1 results."
    new = copy.deepcopy(tour)
    _begin_round2(new, now, rng)
    return new, "Round 2 begins!"


def _decide_duel(tour, i, a, b, now, rng):
    r1 = tour["round1"]
    gone = [pid for pid in (a, b) if has_left(tour, pid)]
    if gone:                                          # someone left: the other goes through
        score = {pid: points(tour, pid) for pid in (a, b)}
        time = {pid: total_seconds(tour, pid) for pid in (a, b)}
        if len(gone) == 1:
            winner = b if gone[0] == a else a
        else:
            winner = (rng or random.Random()).choice([a, b])
        _record(tour, i, winner, a, b, "opponent left", score, time)
        return
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


# --- 5 players: everyone together, the weakest result is out -------------------------

def _tiebreak_players(tour, i):
    """Who answers the tie-breaker of duel/group i (a duel: both; a group: the tied ones)."""
    tiebreak = tour["round1"]["tiebreaks"].get(str(i)) or {}
    return tiebreak.get("players", tour["duels"][i])


def _rank_key(score, time):
    """Better results sort first: more right answers, then less time."""
    return lambda pid: (-score[pid], time[pid])


def _decide_group(tour, i, group, now, rng):
    """Free-for-all (5 players): once everyone is done, the player with the fewest
    right answers (then the slowest) is out and the other four go through. If
    several are tied for last, they answer the tie-breaker; a wrong (or missing)
    answer goes out first, then the slowest answer."""
    r1 = tour["round1"]
    if not all(is_done(tour, pid) for pid in group):
        return                                        # someone is still playing
    score = {pid: points(tour, pid) for pid in group}
    time = {pid: total_seconds(tour, pid) for pid in group}
    ranking = sorted(group, key=_rank_key(score, time))

    gone = [pid for pid in ranking if has_left(tour, pid)]
    if gone:                                          # someone left: they are the one out
        _record_group(tour, i, ranking, gone[-1], "left the game", score, time)
        return

    last = _rank_key(score, time)(ranking[-1])
    tied = [pid for pid in ranking if _rank_key(score, time)(pid) == last]
    if len(tied) == 1:
        how = "fewest right answers" if score[ranking[-1]] < score[ranking[-2]] else "slowest"
        _record_group(tour, i, ranking, ranking[-1], how, score, time)
        return

    tiebreak = r1["tiebreaks"].get(str(i))
    if tiebreak is None:
        r1["tiebreaks"][str(i)] = {"started_at": now, "answers": {}, "players": tied}
        return
    tied = tiebreak["players"]
    answers = tiebreak["answers"]
    timed_out = now >= tiebreak["started_at"] + TIEBREAK_SECONDS
    if len(answers) < len(tied) and not timed_out:
        return                                        # still waiting for answers
    if not answers:
        out, how = (rng or random.Random()).choice(tied), "draw"
    else:
        # Worst first: no answer, then a wrong answer, then the slowest right answer.
        def badness(pid):
            given = answers.get(pid)
            if given is None:
                return (2, 0)
            return (0 if given["correct"] else 1, given["at"])
        out, how = max(tied, key=badness), "tie-breaker"
    _record_group(tour, i, ranking, out, how, score, time)


def _record_group(tour, i, ranking, out, how, score, time):
    order = [pid for pid in ranking if pid != out] + [out]
    tour["round1"]["results"][i] = {"winner": None, "loser": out, "advancing": order[:-1], "ranking": order,
                                    "decided_by": how, "points": score, "seconds": time}
