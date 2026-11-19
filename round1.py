"""Round 1: the duels.

All 4 duels happen at the same time. In every duel both players play ALL FOUR
games, one after another, in the same order. Each duel starts with a different
game, so no two duels look the same. Every game has its own 60-second timer and
one try. As soon as you answer, your next game starts: nobody waits for a timer.

    intro (5 s) → game 1 → game 2 → game 3 → game 4 → [tie-breaker] → results (10 s) → Round 2

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

import round2 as duo_round

INTRO_SECONDS = 5
GAME_SECONDS = 60
TIEBREAK_SECONDS = 30
RESULTS_SECONDS = 10        # time to read the results and the solutions
MEMORY_SHOW_SECONDS = 7      # the memory items are shown for the first 7 s of that game

# --- the four games -------------------------------------------------------------
# Each game has a bank of 5 versions. When the host starts, one version of
# each game is drawn at random, so the puzzles change from tournament to
# tournament (both players in a duel always get the same one). Every version has
# exactly one answer; tests/test_round1.py proves that by trying every possibility.

NUMBER_LOCK_RULE = "The code has 4 digits, all different."

_FEEDBACK_TEXT = {
    (1, 1): "One digit is right and in the right place; one is right but in the wrong place",
    (1, 0): "One digit is right and in the right place",
    (0, 1): "One digit is right but in the wrong place",
    (0, 2): "Two digits are right, but both are in the wrong place",
    (0, 3): "Three digits are right, but all are in the wrong place",
    (0, 0): "No digits are right",
}

ESCAPE_CLUES = [
    "Never enter a room with food in it.",
    "Never enter a room where something ticks or chimes.",
    "The guard never leaves the piano.",
    "From the room with the fireplace, the Exit is exactly three doors away.",
    "Read every door carefully: the house only tells you once.",
]

MEMORY_ITEMS = ["Key", "Compass", "Rose", "Coin", "Feather",
                "Chess piece", "Candle", "Pocket watch", "Hourglass", "Lantern"]

PUZZLES = {
    "number_lock": [
        {"answer": "6205",
         "feedback": {"4865": (1, 1), "0423": (0, 2), "5874": (0, 1), "6753": (1, 1), "2731": (0, 1)}},
        {"answer": "7489",
         "feedback": {"5278": (0, 2), "7145": (1, 1), "9536": (0, 1), "3167": (0, 1), "8394": (0, 3)}},
        {"answer": "3519",
         "feedback": {"3475": (1, 1), "0862": (0, 0), "7580": (1, 0), "6093": (0, 2), "6410": (1, 0)}},
        {"answer": "3974",
         "feedback": {"2691": (0, 1), "7459": (0, 3), "6150": (0, 0), "4359": (0, 3), "9047": (0, 3)}},
        {"answer": "6473",
         "feedback": {"4315": (0, 2), "1075": (1, 0), "3489": (1, 1), "9186": (0, 1), "5103": (1, 0)}},
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
    "escape_route": [
        {"map": {
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
            "Ballroom": ["Exit"]},
         "rooms": {
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
            "Exit": "Fresh night air!"},
         "hidden": {"food": {"Kitchen", "Conservatory", "Pantry", "Wine Cellar"},
                    "ticks": {"Clock Room", "Ballroom", "Chapel"},
                    "guard": {"Music Room"}, "fireplace": {"Library"}},
         "answer": ["Hall", "Library", "Billiard Room", "Study", "Exit"]},
        {"map": {
            "Start": ["Gallery", "Hall", "Kitchen"],
            "Gallery": ["Study", "Chapel", "Music Room"],
            "Hall": ["Library", "Pantry"],
            "Kitchen": ["Library", "Storage Room"],
            "Study": ["Billiard Room", "Clock Room"],
            "Chapel": ["Billiard Room", "Greenhouse"],
            "Music Room": ["Ballroom"],
            "Library": ["Ballroom", "Study"],
            "Billiard Room": ["Exit", "Wine Cellar"],
            "Clock Room": ["Exit"],
            "Ballroom": ["Exit"]},
         "rooms": {
            "Gallery": "Portraits glow above a crackling fireplace.",
            "Hall": "A clock ticks somewhere on the landing.",
            "Kitchen": "Soup bubbles on the stove.",
            "Study": "A desk covered in maps.",
            "Chapel": "A bell chimes every quarter hour.",
            "Music Room": "A grand piano… and heavy footsteps.",
            "Library": "Books from floor to ceiling, all quiet.",
            "Pantry": "Shelves full of jam jars.",
            "Storage Room": "Dusty boxes, no other door.",
            "Billiard Room": "Green felt and silence.",
            "Clock Room": "Dozens of clocks on every wall.",
            "Greenhouse": "Glass walls, no other door.",
            "Ballroom": "A banquet is laid out for a party.",
            "Wine Cellar": "Bottles, cheese and a locked gate.",
            "Exit": "Fresh night air!"},
         "hidden": {"food": {"Kitchen", "Pantry", "Wine Cellar", "Ballroom"},
                    "ticks": {"Clock Room", "Chapel", "Hall"},
                    "guard": {"Music Room"}, "fireplace": {"Gallery"}},
         "answer": ["Gallery", "Study", "Billiard Room", "Exit"]},
        {"map": {
            "Start": ["Conservatory", "Library", "Hall"],
            "Conservatory": ["Greenhouse", "Gallery"],
            "Library": ["Gallery", "Clock Room", "Kitchen"],
            "Hall": ["Music Room", "Chapel"],
            "Gallery": ["Billiard Room", "Pantry"],
            "Clock Room": ["Billiard Room"],
            "Kitchen": ["Study"],
            "Music Room": ["Study"],
            "Chapel": ["Study", "Storage Room"],
            "Billiard Room": ["Study", "Wine Cellar"],
            "Study": ["Exit", "Ballroom"],
            "Ballroom": ["Exit"]},
         "rooms": {
            "Conservatory": "Palm trees under the glass, perfectly still.",
            "Library": "A clock ticks above the shelves.",
            "Hall": "Tall windows over the garden.",
            "Greenhouse": "Glass walls, no other door.",
            "Gallery": "Portraits glow above a crackling fireplace.",
            "Clock Room": "Dozens of clocks on every wall.",
            "Kitchen": "It smells of fresh bread.",
            "Music Room": "A grand piano… and heavy footsteps.",
            "Chapel": "A bell chimes every quarter hour.",
            "Pantry": "Shelves full of jam jars.",
            "Billiard Room": "Green felt and silence.",
            "Storage Room": "Dusty boxes, no other door.",
            "Study": "A desk covered in maps.",
            "Wine Cellar": "Bottles, cheese and a locked gate.",
            "Ballroom": "A grandfather clock stands in the corner.",
            "Exit": "Fresh night air!"},
         "hidden": {"food": {"Kitchen", "Pantry", "Wine Cellar"},
                    "ticks": {"Clock Room", "Library", "Ballroom", "Chapel"},
                    "guard": {"Music Room"}, "fireplace": {"Gallery"}},
         "answer": ["Conservatory", "Gallery", "Billiard Room", "Study", "Exit"]},
        {"map": {
            "Start": ["Kitchen", "Library", "Gallery"],
            "Kitchen": ["Pantry", "Hall"],
            "Library": ["Hall", "Study", "Chapel"],
            "Gallery": ["Music Room", "Conservatory"],
            "Hall": ["Billiard Room", "Clock Room"],
            "Study": ["Billiard Room", "Storage Room"],
            "Chapel": ["Greenhouse", "Exit"],
            "Music Room": ["Ballroom"],
            "Conservatory": ["Study", "Greenhouse"],
            "Billiard Room": ["Exit", "Wine Cellar"],
            "Clock Room": ["Exit"],
            "Ballroom": ["Exit"]},
         "rooms": {
            "Kitchen": "Soup bubbles on the stove.",
            "Library": "A fire crackles in the hearth.",
            "Gallery": "Old portraits watch you pass.",
            "Pantry": "Shelves full of jam jars.",
            "Hall": "A clock ticks somewhere on the landing.",
            "Study": "A desk covered in maps.",
            "Chapel": "A bell chimes every quarter hour.",
            "Music Room": "A grand piano… and heavy footsteps.",
            "Conservatory": "Breakfast is laid out among the palms.",
            "Billiard Room": "Green felt and silence.",
            "Clock Room": "Dozens of clocks on every wall.",
            "Storage Room": "Dusty boxes, no other door.",
            "Greenhouse": "Glass walls, no other door.",
            "Ballroom": "A grandfather clock stands in the corner.",
            "Wine Cellar": "Bottles, cheese and a locked gate.",
            "Exit": "Fresh night air!"},
         "hidden": {"food": {"Kitchen", "Pantry", "Wine Cellar", "Conservatory"},
                    "ticks": {"Clock Room", "Chapel", "Ballroom", "Hall"},
                    "guard": {"Music Room"}, "fireplace": {"Library"}},
         "answer": ["Library", "Study", "Billiard Room", "Exit"]},
        {"map": {
            "Start": ["Conservatory", "Hall", "Music Room"],
            "Conservatory": ["Gallery", "Greenhouse"],
            "Hall": ["Gallery", "Kitchen", "Study"],
            "Music Room": ["Library"],
            "Gallery": ["Library", "Clock Room"],
            "Kitchen": ["Pantry"],
            "Study": ["Chapel", "Billiard Room"],
            "Library": ["Billiard Room", "Ballroom"],
            "Clock Room": ["Billiard Room"],
            "Chapel": ["Exit"],
            "Billiard Room": ["Exit", "Storage Room"],
            "Ballroom": ["Exit"]},
         "rooms": {
            "Conservatory": "Palm trees under the glass, perfectly still.",
            "Hall": "Afternoon tea and cakes are served here.",
            "Music Room": "A grand piano… and heavy footsteps.",
            "Gallery": "Portraits glow above a crackling fireplace.",
            "Greenhouse": "Glass walls, no other door.",
            "Kitchen": "It smells of fresh bread.",
            "Study": "A desk covered in maps.",
            "Library": "Books from floor to ceiling, all quiet.",
            "Clock Room": "Dozens of clocks on every wall.",
            "Pantry": "Shelves full of jam jars.",
            "Chapel": "A bell chimes every quarter hour.",
            "Billiard Room": "Green felt and silence.",
            "Ballroom": "A banquet is laid out for a party.",
            "Storage Room": "Dusty boxes, no other door.",
            "Exit": "Fresh night air!"},
         "hidden": {"food": {"Kitchen", "Pantry", "Ballroom", "Hall"},
                    "ticks": {"Clock Room", "Chapel"},
                    "guard": {"Music Room"}, "fireplace": {"Gallery"}},
         "answer": ["Conservatory", "Gallery", "Library", "Billiard Room", "Exit"]},
    ],
    "memory": [
        {"missing": ["Compass", "Candle", "Hourglass"],
         "remaining": ["Lantern", "Feather", "Coin", "Pocket watch", "Key", "Chess piece", "Rose"]},
        {"missing": ["Rose", "Key", "Pocket watch"],
         "remaining": ["Hourglass", "Coin", "Candle", "Lantern", "Compass", "Feather", "Chess piece"]},
        {"missing": ["Feather", "Coin", "Lantern"],
         "remaining": ["Pocket watch", "Rose", "Chess piece", "Key", "Hourglass", "Candle", "Compass"]},
        {"missing": ["Chess piece", "Compass", "Rose"],
         "remaining": ["Candle", "Key", "Lantern", "Hourglass", "Feather", "Pocket watch", "Coin"]},
        {"missing": ["Hourglass", "Pocket watch", "Feather"],
         "remaining": ["Coin", "Lantern", "Compass", "Rose", "Candle", "Key", "Chess piece"]},
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
        if len(code) != 4 or not code.isdigit() or len(set(code)) != 4:
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
        # Exactly three different items, picked from the ten.
        count = len(puzzle["missing"])
        if not isinstance(value, list) or len(value) != count:
            return "invalid"
        names = {item.casefold(): item for item in MEMORY_ITEMS}
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


def progress(tour, player_id, now):
    """How far along this player is, from 0 (just started) to 4 (all four games done).

    Between answers it creeps forward with the clock, so the race track moves
    smoothly. It says nothing about right or wrong."""
    done = game_number(tour, player_id)
    if done >= len(GAMES):
        return float(len(GAMES))
    started = tour["round1"]["players"][player_id]["game_started_at"]
    into_game = max(0.0, min(0.95, (now - started) / GAME_SECONDS))
    return done + into_game


def has_left(tour, player_id):
    return player_id in tour["round1"].get("left", [])


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


def _close_remaining_games(player, now):
    """Count every game this player hasn't answered as not answered, ending now."""
    while len(player["results"]) < len(GAMES):
        seconds = round(max(0.0, min(GAME_SECONDS, now - player["game_started_at"])), 1)
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
        return tour, "That duel is already decided."

    new = copy.deepcopy(tour)
    new["round1"].setdefault("left", []).append(player_id)
    _close_remaining_games(new["round1"]["players"][player_id], now)
    new, _ = settle(new, now, rng)
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
    for player in new["round1"]["players"].values():
        _close_remaining_games(player, now)
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
        finalists = [result["winner"] for result in r1["results"]]
        new["round2"] = duo_round.new_round(finalists, now, rng, show_intro=True)

    if new == tour:
        return tour, ""
    return new, "Updated."


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
