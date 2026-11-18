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
STORY_CHARACTERS_PER_SECOND = 22

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
STORY = (
    "Detective, the earlier games were security tests inside the mansion.\n\n"
    "During the final blackout, someone stole the Moonstone Key.\n\n"
    "Find the thief, the hiding place, and the code that opens its vault."
)
FINAL_QUESTION = "…Who took the Moonstone Key?"


def new_round(finalists, now):
    """Create the shared Round 3 state for exactly two finalist ids."""
    return {
        "story_started_at": now,
        "starts_at": None,
        "ends_at": None,
        "finalists": list(finalists),
        "guesses": {pid: [] for pid in finalists},
        "winner": None,
        "decided_by": None,
        "results_at": None,
    }


def is_finalist(tour, player_id):
    return player_id in tour.get("round3", {}).get("finalists", [])


def seconds_left(tour, now):
    ends_at = tour["round3"]["ends_at"]
    return 0 if ends_at is None else max(0, int(ends_at - now + 0.999))


def story_text(tour, now):
    """The portion of the detective's briefing visible at this moment."""
    started = tour["round3"]["story_started_at"]
    characters = int(max(0, now - started) * STORY_CHARACTERS_PER_SECOND)
    return STORY[:characters]


def story_finished(tour, now):
    return len(story_text(tour, now)) >= len(STORY)


def guesses_left(tour, player_id):
    return max(0, MAX_GUESSES - len(tour["round3"]["guesses"].get(player_id, [])))


def start_investigation(tour, player_id, now):
    """A finalist starts the shared countdown after the briefing is complete."""
    if tour.get("status") != "round3":
        return tour, "The final mystery is not open right now."
    if not is_finalist(tour, player_id):
        return tour, "Only a finalist can open the final case."
    if not story_finished(tour, now):
        return tour, "Listen to the detective's briefing first."
    if tour["round3"]["starts_at"] is not None:
        return tour, "The investigation has already begun."

    new = copy.deepcopy(tour)
    new["round3"]["starts_at"] = now
    new["round3"]["ends_at"] = now + ROUND_SECONDS
    return new, "The final investigation has begun!"


def answer(tour, player_id, suspect, room, object_name, now, vault_code=FINAL_CODE):
    """Record one finalist's theory. The correct theory and vault code win."""
    if tour.get("status") != "round3":
        return tour, "The final mystery is not open right now."
    if not is_finalist(tour, player_id):
        return tour, "Only the two finalists can submit a theory."
    # Tournaments already in Round 3 before this story intro was added do not
    # have starts_at; let those older games continue normally.
    if "starts_at" in tour["round3"] and tour["round3"]["starts_at"] is None:
        return tour, "The detective's briefing is still playing."
    if now >= tour["round3"]["ends_at"]:
        return tour, "Time's up!"
    if suspect not in SUSPECTS or room not in ROOMS or object_name not in OBJECTS:
        return tour, "Choose one suspect, room, and object from the lists."
    if guesses_left(tour, player_id) == 0:
        return tour, f"You have used all {MAX_GUESSES} theories."

    new = copy.deepcopy(tour)
    guess = {"suspect": suspect, "room": room, "object": object_name, "at": now}
    new["round3"]["guesses"][player_id].append(guess)

    if _score_guess(guess) == len(SOLUTION) and str(vault_code).strip() == FINAL_CODE:
        _record_winner(new, player_id, "solved the mystery", now)
        return new, "✅ You solved it and opened the Moonstone Vault!"
    if _score_guess(guess) == len(SOLUTION):
        return new, "Not quite. Your theory is right, but the vault code did not open the lock."
    return new, "Not quite. Check the clues and try another theory."


def settle(tour, now, rng=None):
    """Close a timed-out final and later move it to the finished state.

    It is safe for every phone to call this repeatedly.
    """
    if tour.get("status") not in ("round3", "round3_results"):
        return tour, ""

    new = copy.deepcopy(tour)
    state = new["round3"]
    if new["status"] == "round3" and state["ends_at"] is not None and now >= state["ends_at"]:
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
