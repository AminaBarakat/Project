"""The tournament rules: who is in the lobby, who is the host, and who duels whom.

Nothing here knows about Streamlit or the database. Every action takes a tournament
(a plain dict) and returns (new_tournament, message). A refused action returns the
tournament unchanged plus a message saying why, so the screens can show it and the
tests can check it.

A tournament looks like this:

    {
        "code": "KQZT",                 # the join code players type in
        "status": "lobby",              # "lobby" → "round1" → "round1_results" → "round2"
        "host_id": "p_3f9a...",         # the player who created it; only they can start
        "players": [                    # in the order they joined; the host is first
            {"id": "p_3f9a...", "name": "Ana", "appearance": None},
        ],
        "duels": [],                    # filled in at start: [[id, id], [id, id], ...]
        "eliminated": [],               # ids, in the order they were knocked out
        "round1": None,                 # Round 1's own state, see round1.py
    }

"appearance" is empty for now. It's the slot for avatars/colours when we do styling.
"""

import copy
import random
import time

import round1
import round3

MAX_PLAYERS = 8
MAX_NAME_LENGTH = 20


def clean_name(name):
    """Returns (cleaned_name, None) if the name is acceptable, or (None, reason) if not."""
    if not isinstance(name, str):
        return None, "Please type a name."
    name = " ".join(name.split())          # trim, and squash double spaces inside
    if not name:
        return None, "Please type a name."
    if len(name) > MAX_NAME_LENGTH:
        return None, f"Names can be at most {MAX_NAME_LENGTH} characters."
    return name, None


def new_tournament(code, host_id, host_name, appearance=None):
    """Creates a lobby with the host as its first player. Returns (tournament, message);
    the tournament is None if the host's name is refused."""
    name, problem = clean_name(host_name)
    if problem:
        return None, problem
    tournament = {
        "code": code,
        "status": "lobby",
        "host_id": host_id,
        "players": [{"id": host_id, "name": name, "appearance": appearance}],
        "duels": [],
        "eliminated": [],
        "round1": None,
        "round3": None,
    }
    return tournament, f"Tournament {code} created. Share the code with your friends!"


def find_player(tournament, player_id):
    """The player dict with this id, or None."""
    for player in tournament["players"]:
        if player["id"] == player_id:
            return player
    return None


def is_host(tournament, player_id):
    return player_id is not None and player_id == tournament["host_id"]


def join(tournament, player_id, name, appearance=None):
    """A new player joins the lobby."""
    if tournament["status"] != "lobby":
        return tournament, "This tournament has already started."
    if find_player(tournament, player_id):
        return tournament, "You're already in this tournament."
    if len(tournament["players"]) >= MAX_PLAYERS:
        return tournament, f"This tournament is full ({MAX_PLAYERS} players)."
    name, problem = clean_name(name)
    if problem:
        return tournament, problem
    taken = {p["name"].casefold() for p in tournament["players"]}
    if name.casefold() in taken:
        return tournament, f"Someone is already called {name}. Pick another name."

    new = copy.deepcopy(tournament)
    new["players"].append({"id": player_id, "name": name, "appearance": appearance})
    return new, f"Welcome, {name}!"


def leave(tournament, player_id):
    """A player leaves the lobby by themselves. The host can't leave their own lobby."""
    if tournament["status"] != "lobby":
        return tournament, "The tournament has started, so you can't leave now."
    if not find_player(tournament, player_id):
        return tournament, "You're not in this tournament."
    if is_host(tournament, player_id):
        return tournament, "You're the host, so you can't leave your own tournament."
    new = copy.deepcopy(tournament)
    new["players"] = [p for p in new["players"] if p["id"] != player_id]
    return new, "You left the tournament."


def remove_player(tournament, by_id, player_id):
    """The host removes someone from the lobby."""
    if not is_host(tournament, by_id):
        return tournament, "Only the host can remove players."
    if tournament["status"] != "lobby":
        return tournament, "The tournament has started, so players can't be removed."
    if player_id == by_id:
        return tournament, "You can't remove yourself."
    player = find_player(tournament, player_id)
    if not player:
        return tournament, "That player isn't in the tournament."
    new = copy.deepcopy(tournament)
    new["players"] = [p for p in new["players"] if p["id"] != player_id]
    return new, f"{player['name']} was removed."


def start(tournament, by_id, rng=None, now=None):
    """The host starts the tournament: players are shuffled into random 1 v 1 duels.

    rng is a random.Random. The tests pass one with a fixed seed so the draw is
    predictable; the app leaves it out and gets a truly random draw.
    now is the current time (time.time()); Round 1 begins a few seconds later."""
    if not is_host(tournament, by_id):
        return tournament, "Only the host can start the tournament."
    if tournament["status"] != "lobby":
        return tournament, "The tournament has already started."
    count = len(tournament["players"])
    if count != MAX_PLAYERS:
        return tournament, f"You need exactly {MAX_PLAYERS} players to start ({count} so far)."

    rng = rng or random.Random()
    ids = [p["id"] for p in tournament["players"]]
    rng.shuffle(ids)

    new = copy.deepcopy(tournament)
    new["duels"] = [[ids[i], ids[i + 1]] for i in range(0, len(ids), 2)]
    new["status"] = "round1"
    new["round1"] = round1.new_round(new["duels"], time.time() if now is None else now, rng)
    return new, "The duels are set. Let the games begin!"


def duel_of(tournament, player_id):
    """The duel (a pair of ids) this player is in, or None."""
    for duel in tournament["duels"]:
        if player_id in duel:
            return duel
    return None


def opponent_of(tournament, player_id):
    """The player dict this player faces in Round 1, or None."""
    duel = duel_of(tournament, player_id)
    if not duel:
        return None
    other = duel[1] if duel[0] == player_id else duel[0]
    return find_player(tournament, other)


def start_round3(tournament, by_id, finalist_ids, now=None):
    """The host picks Round 2's two survivors and begins the final mystery.

    Round 2 is currently a presentation placeholder, so this is a temporary
    bridge until its Duo Vault rules decide the finalists automatically.
    """
    if not is_host(tournament, by_id):
        return tournament, "Only the host can start the final mystery."
    if tournament["status"] != "round2":
        return tournament, "Round 3 can only start after Round 2."
    if not isinstance(finalist_ids, list) or len(finalist_ids) != 2 or len(set(finalist_ids)) != 2:
        return tournament, "Choose exactly two different finalists."
    active_ids = {player["id"] for player in tournament["players"]
                  if player["id"] not in tournament.get("eliminated", [])}
    if not set(finalist_ids).issubset(active_ids):
        return tournament, "Both finalists must still be in the game."

    new = copy.deepcopy(tournament)
    new["status"] = "round3"
    new["round3"] = round3.new_round(finalist_ids, time.time() if now is None else now)
    return new, "The final mansion mystery has begun!"
