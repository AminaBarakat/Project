"""Round 3: the Final Mansion Mystery.

The two finalists see the same six clues and each gets up to three theories.
The first complete correct theory wins immediately.  If nobody solves the
mystery before the clock runs out, the best theory wins; an exact tie is a
random draw.  Like Round 1, this module is plain Python: it has no Streamlit
or database code, which keeps the game rules easy to test.
"""

import copy
import random

ROUND_SECONDS = 180
RESULTS_SECONDS = 15
MAX_GUESSES = 3

SUSPECTS = ("Nova", "Theo", "Mira")
ROOMS = ("Library", "Observatory", "Conservatory")
OBJECTS = ("Key", "Map", "Flashlight")

CLUES = (
    "Theo was in the Library.",
    "The person in the Conservatory carried the Map.",
    "Nova was not in the Library and did not carry the Flashlight.",
    "The Flashlight was not in the Library.",
    "Mira did not carry the Key.",
    "The thief entered the Conservatory.",
)

SOLUTION = {"suspect": "Nova", "room": "Conservatory", "object": "Map"}
FINAL_CODE = "318"


def new_round(finalists, now):
    """Create the shared Round 3 state for exactly two finalist ids."""
    return {
        "started_at": now,
        "ends_at": now + ROUND_SECONDS,
        "finalists": list(finalists),
        "guesses": {pid: [] for pid in finalists},
        "winner": None,
        "decided_by": None,
        "results_at": None,
    }


def is_finalist(tour, player_id):
    return player_id in tour.get("round3", {}).get("finalists", [])


def seconds_left(tour, now):
    return max(0, int(tour["round3"]["ends_at"] - now + 0.999))


def guesses_left(tour, player_id):
    return max(0, MAX_GUESSES - len(tour["round3"]["guesses"].get(player_id, [])))


def answer(tour, player_id, suspect, room, object_name, now):
    """Record one finalist's theory. A complete correct theory wins at once."""
    if tour.get("status") != "round3":
        return tour, "The final mystery is not open right now."
    if not is_finalist(tour, player_id):
        return tour, "Only the two finalists can submit a theory."
    if now >= tour["round3"]["ends_at"]:
        return tour, "Time's up!"
    if suspect not in SUSPECTS or room not in ROOMS or object_name not in OBJECTS:
        return tour, "Choose one suspect, room, and object from the lists."
    if guesses_left(tour, player_id) == 0:
        return tour, f"You have used all {MAX_GUESSES} theories."

    new = copy.deepcopy(tour)
    guess = {"suspect": suspect, "room": room, "object": object_name, "at": now}
    new["round3"]["guesses"][player_id].append(guess)

    if _score_guess(guess) == len(SOLUTION):
        _record_winner(new, player_id, "solved the mystery", now)
        return new, f"✅ You solved it! The final code is {FINAL_CODE}."
    return new, "Not quite. Check the clues and try another theory."


def settle(tour, now, rng=None):
    """Close a timed-out final and later move it to the finished state.

    It is safe for every phone to call this repeatedly.
    """
    if tour.get("status") not in ("round3", "round3_results"):
        return tour, ""

    new = copy.deepcopy(tour)
    state = new["round3"]
    if new["status"] == "round3" and now >= state["ends_at"]:
        winner, how = _winner_at_timeout(state, rng)
        _record_winner(new, winner, how, state["ends_at"])
    elif new["status"] == "round3_results" and now >= state["results_at"] + RESULTS_SECONDS:
        new["status"] = "finished"

    if new == tour:
        return tour, ""
    return new, "Updated."


def _score_guess(guess):
    return sum(guess.get(part) == answer for part, answer in SOLUTION.items())


def _winner_at_timeout(state, rng):
    """Choose the closest theory, then the fastest matching theory, then a draw."""
    best_score = -1
    contenders = []
    for pid in state["finalists"]:
        guesses = state["guesses"].get(pid, [])
        score = max((_score_guess(guess) for guess in guesses), default=0)
        if score > best_score:
            best_score, contenders = score, [pid]
        elif score == best_score:
            contenders.append(pid)

    if len(contenders) == 1:
        return contenders[0], "best theory when time ran out"

    fastest = []
    earliest = None
    for pid in contenders:
        times = [guess["at"] for guess in state["guesses"].get(pid, [])
                 if _score_guess(guess) == best_score]
        if not times:
            continue
        at = min(times)
        if earliest is None or at < earliest:
            earliest, fastest = at, [pid]
        elif at == earliest:
            fastest.append(pid)
    if len(fastest) == 1:
        return fastest[0], "fastest matching theory"
    return (rng or random.Random()).choice(fastest or contenders), "draw"


def _record_winner(tour, player_id, how, now):
    state = tour["round3"]
    state["winner"] = player_id
    state["decided_by"] = how
    state["results_at"] = now
    tour["status"] = "round3_results"
