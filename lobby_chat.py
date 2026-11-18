"""Greetings in the lobby: while the table fills up, seated players can send one of
four short greetings. They pop up as a speech bubble next to the sender's seat on
everyone's screen, and the latest ones are listed in a small feed.

Plain Python like the other rule files: no Streamlit, no database. Functions that
change the tournament return (new_tournament, message) and never change the old one.
"""

import copy

# key: (button label, what the bubble says)
GREETINGS = {
    "wave": ("Wave", "Hi everyone!"),
    "good_luck": ("Good luck", "Good luck, detectives!"),
    "watching": ("I'm watching you", "I'm watching you…"),
    "hurry": ("Hurry up!", "Hurry up, we're waiting!"),
}

COOLDOWN = 3          # seconds between two greetings from the same player
BUBBLE_SECONDS = 6    # how long a bubble stays next to the seat
KEEP = 12             # only the latest greetings are stored


def _state(tour):
    return tour.get("lobby_chat") or {"greetings": [], "next_id": 1}


def greet(tour, player_id, kind, now):
    """A seated player sends a greeting (lobby only)."""
    if tour.get("status") != "lobby":
        return tour, "The game has already started."
    if player_id not in {p["id"] for p in tour["players"]}:
        return tour, "You're not at this table."
    if kind not in GREETINGS:
        return tour, "That greeting doesn't exist."
    mine = [g for g in _state(tour)["greetings"] if g["by"] == player_id]
    if mine and now - mine[-1]["at"] < COOLDOWN:
        return tour, "One moment, detective!"
    new = copy.deepcopy(tour)
    state = _state(new)
    state["greetings"] = (state["greetings"] + [{"id": state["next_id"], "by": player_id,
                                                 "kind": kind, "at": now}])[-KEEP:]
    state["next_id"] += 1
    new["lobby_chat"] = state
    return new, GREETINGS[kind][1]


def bubbles(tour, now):
    """Greetings to show as bubbles right now: the latest one per player, with its
    age in seconds (so a redraw carries on instead of restarting the animation)."""
    seated = {p["id"] for p in tour["players"]}
    latest = {}
    for greeting in _state(tour)["greetings"]:
        age = now - greeting["at"]
        if greeting["by"] in seated and 0 <= age < BUBBLE_SECONDS:
            latest[greeting["by"]] = {**greeting, "age": round(age, 2)}
    return latest


def latest_id(tour):
    """The id of the newest greeting (0 if none): the screens redraw when it changes."""
    greetings = _state(tour)["greetings"]
    return greetings[-1]["id"] if greetings else 0


def feed(tour, limit=3):
    """The newest greetings, newest first, as (player id, greeting key)."""
    seated = {p["id"] for p in tour["players"]}
    recent = [g for g in _state(tour)["greetings"] if g["by"] in seated]
    return [(g["by"], g["kind"]) for g in reversed(recent[-limit:])]
