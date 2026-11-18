"""Spectators: what eliminated detectives can do while the others play on.

* Make a call: before Round 2 is decided, back the duo you think opens the vault;
  before Round 3 is decided, back the finalist you think becomes champion.
  One call per round, and it can't be changed once made.
* Send reactions: six detective-themed reactions that pop up briefly at the edge
  of everyone's screen. One reaction every few seconds per spectator, so nobody
  can flood the room.

Like the round files, this module is plain Python: no Streamlit and no database.
Every function that changes the tournament returns (new_tournament, message) and
leaves the old one untouched, so it can be passed to storage.update.
"""

import copy

# The six reactions. "bubble": the sender's detective pops up with a speech bubble.
# "sticker": one of our drawings flies along the bottom of the screen.
REACTIONS = {
    "elementary": {"style": "bubble", "text": "Elementary!"},
    "knew_it": {"style": "bubble", "text": "I knew it!"},
    "too_slow": {"style": "bubble", "text": "Too slow, detective!"},
    "magnifier": {"style": "sticker", "text": "Suspicious…"},
    "footprints": {"style": "sticker", "text": "On their trail"},
    "alarm": {"style": "sticker", "text": "Sound the alarm!"},
}

REACTION_COOLDOWN = 4      # seconds between two reactions from the same spectator
REACTION_SECONDS = 5       # how long a reaction stays on screen
KEEP_REACTIONS = 15        # only the most recent reactions are stored

# Where reactions can be sent: from the start of Round 2 to the very end.
REACTION_STATUSES = ("round2", "final", "round3", "round3_results", "finished")


def _state(tour):
    """The spectators' part of the tournament (empty if nobody has done anything yet)."""
    return tour.get("spectators") or {"calls": {"round2": {}, "round3": {}}, "reactions": [], "next_id": 1}


def is_spectator(tour, player_id):
    """Eliminated players are spectators."""
    return player_id in tour.get("eliminated", [])


# --- calls (predictions) -------------------------------------------------------

def call_options(tour, round_name):
    """What a spectator can back in this round, as {choice: [player ids]}.
    Round 2: the two duos. Round 3: the two finalists. Empty when the call is
    not open (the round hasn't started yet, or it has already been decided)."""
    status = tour.get("status")
    if round_name == "round2":
        r2 = tour.get("round2") or {}
        if status != "round2" or r2.get("winner") is not None:
            return {}
        return {duo_id: list(duo["players"]) for duo_id, duo in r2.get("duos", {}).items()}
    if round_name == "round3":
        if status == "final":
            r2 = tour.get("round2") or {}
            winner = r2.get("winner")
            finalists = r2.get("duos", {}).get(winner, {}).get("players", []) if winner else []
        elif status == "round3" and (tour.get("round3") or {}).get("winner") is None:
            finalists = tour["round3"]["finalists"]
        else:
            return {}
        return {pid: [pid] for pid in finalists}
    return {}


def open_call(tour):
    """The round a spectator can make a call for right now, or None."""
    for round_name in ("round2", "round3"):
        if call_options(tour, round_name):
            return round_name
    return None


def my_call(tour, player_id, round_name):
    return _state(tour)["calls"].get(round_name, {}).get(player_id)


def make_call(tour, player_id, round_name, choice, now=None):
    """A spectator backs a duo (Round 2) or a finalist (Round 3)."""
    if not is_spectator(tour, player_id):
        return tour, "Only spectators can make a call."
    options = call_options(tour, round_name)
    if not options:
        return tour, "Calls are closed for this round."
    if choice not in options:
        return tour, "That's not one of the choices."
    if player_id in options[choice]:
        return tour, "You can't back yourself."
    if my_call(tour, player_id, round_name) is not None:
        return tour, "You've already made your call."
    new = copy.deepcopy(tour)
    state = _state(new)
    state["calls"].setdefault(round_name, {})[player_id] = choice
    new["spectators"] = state
    return new, "Call locked in!"


def crowd(tour, round_name):
    """How many spectators back each choice: {choice: count}, every choice listed."""
    options = call_options(tour, round_name) or _decided_options(tour, round_name)
    counts = {choice: 0 for choice in options}
    for choice in _state(tour)["calls"].get(round_name, {}).values():
        if choice in counts:
            counts[choice] += 1
    return counts


def _decided_options(tour, round_name):
    """The choices of a round that has already been decided (for the results)."""
    if round_name == "round2" and tour.get("round2"):
        return {duo_id: list(duo["players"]) for duo_id, duo in tour["round2"]["duos"].items()}
    if round_name == "round3" and tour.get("round3"):
        return {pid: [pid] for pid in tour["round3"]["finalists"]}
    return {}


def correct_choice(tour, round_name):
    """The choice that turned out right, or None while the round is still on."""
    if round_name == "round2":
        return (tour.get("round2") or {}).get("winner")
    if round_name == "round3":
        return (tour.get("round3") or {}).get("winner")
    return None


def who_called_it(tour, round_name):
    """The spectators who backed the winner of this round (ids, in call order)."""
    right = correct_choice(tour, round_name)
    if right is None:
        return []
    return [pid for pid, choice in _state(tour)["calls"].get(round_name, {}).items() if choice == right]


# --- reactions -----------------------------------------------------------------

def react(tour, player_id, kind, now):
    """A spectator sends one of the six reactions."""
    if not is_spectator(tour, player_id):
        return tour, "Only spectators can send reactions."
    if tour.get("status") not in REACTION_STATUSES:
        return tour, "Reactions open in Round 2."
    if kind not in REACTIONS:
        return tour, "That reaction doesn't exist."
    state = _state(tour)
    mine = [r for r in state["reactions"] if r["by"] == player_id]
    if mine and now - mine[-1]["at"] < REACTION_COOLDOWN:
        return tour, "Easy, detective! Wait a moment before the next one."
    new = copy.deepcopy(tour)
    state = _state(new)
    state["reactions"] = (state["reactions"] + [{"id": state["next_id"], "by": player_id,
                                                 "kind": kind, "at": now}])[-KEEP_REACTIONS:]
    state["next_id"] += 1
    new["spectators"] = state
    return new, REACTIONS[kind]["text"]


def recent_reactions(tour, now):
    """The reactions that should be on screen right now, oldest first, each with
    its age in seconds (screens use the age so a redraw doesn't restart them)."""
    out = []
    for reaction in _state(tour)["reactions"]:
        age = now - reaction["at"]
        if 0 <= age < REACTION_SECONDS:
            out.append({**reaction, "age": round(age, 2)})
    return out
