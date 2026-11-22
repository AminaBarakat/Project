"""Round 2 rules for the shared Duo Vault Challenge state."""

import copy
import random

# Puzzle and timing constants live here so the team can change them together.
VAULT_CODE = "3583"
CARD_A = "The first digit is 3. The second digit is two more than the first."
CARD_B = "The third digit is the first plus the second. The final digit is the third minus the second."
SAFE_ROUTE = ("Vault", "Gallery", "Rooftop")
ROUTE_CHOICES = {
    "Vault": ("Gallery", "Cellar"),
    "Gallery": ("Rooftop", "Kitchen"),
}
WRONG_DOORS = {"Vault": "Cellar", "Gallery": "Kitchen"}
LOCKOUT_SECONDS = 10
ROUND_SECONDS = 60
INTRO_SECONDS = 5  # Retained for older saved rounds with a timed introduction.


def new_round(player_ids, now, rng=None, show_intro=False):
    """Pair the four Round 1 winners and create their shared vault state."""
    if len(player_ids) != 4 or len(set(player_ids)) != 4:
        raise ValueError("Round 2 needs exactly four different players.")

    rng = rng or random.Random()
    shuffled = list(player_ids)
    rng.shuffle(shuffled)
    players = {}
    duos = {}
    for index in range(2):
        duo_id = f"duo_{index + 1}"
        pair = shuffled[index * 2:index * 2 + 2]
        duos[duo_id] = {
            "players": pair,
            "code_solved_at": None,
            "route_step": 0,
            "alarm_count": 0,
            "locked_until": None,
            "finished_at": None,
        }
        for card, player_id in zip(("A", "B"), pair):
            players[player_id] = {"duo_id": duo_id, "card": card}

    round_state = {
        "started_at": now,
        "players": players,
        "duos": duos,
        "winner": None,
        "resolved_at": None,
        "decided_by": None,
    }
    if show_intro:
        # Keep the matchup page visible until a finalist starts the challenge.
        # The challenge clock begins from that shared server-side action.
        round_state["intro_ends_at"] = None
        round_state["challenge_started_at"] = None
    return round_state


def _challenge_started_at(round_state):
    """Use the post-intro server time for the challenge clock when an intro exists."""
    return round_state.get("challenge_started_at", round_state["started_at"])


def _validate_action(tour, player_id, duo_id, now):
    """Return (Round 2 state, duo state, message) for a valid active player."""
    round_state = tour.get("round2") or {}
    if round_state.get("winner") is not None:
        return None, None, "Another duo has already won."
    if tour.get("status") != "round2":
        return None, None, "Round 2 is not active."
    if player_id in tour.get("eliminated", []):
        return None, None, "You've been eliminated and can't submit."

    if not round_state:
        return None, None, "Round 2 hasn't been set up yet."
    assignment = round_state.get("players", {}).get(player_id)
    if not assignment:
        return None, None, "You're not playing in Round 2."
    if assignment.get("duo_id") != duo_id:
        return None, None, "You're not in that duo."

    duo = round_state.get("duos", {}).get(duo_id)
    if not duo:
        return None, None, "That duo doesn't exist."
    challenge_started_at = _challenge_started_at(round_state)
    if challenge_started_at is None:
        return None, None, "The Round 2 challenge hasn't started yet."
    intro_ends_at = round_state.get("intro_ends_at")
    if intro_ends_at is not None and now < intro_ends_at:
        return None, None, "The Round 2 introduction is still playing."
    if now >= challenge_started_at + ROUND_SECONDS:
        return None, None, "Time is up. The result is being settled."
    if duo.get("finished_at") is not None:
        return None, None, "Your duo has already finished."
    if duo.get("locked_until") is not None and now < duo["locked_until"]:
        left = max(1, int(duo["locked_until"] - now + 0.999))
        return None, None, f"Your duo is locked out for {left} more seconds."
    return round_state, duo, None


def submit_code(tour, player_id, duo_id, code, now):
    """Submit the shared code. Wrong four-digit guesses trigger a lockout."""
    _, duo, problem = _validate_action(tour, player_id, duo_id, now)
    if problem:
        return tour, problem
    if duo["code_solved_at"] is not None:
        return tour, "Your vault is already open. Choose a route on the map."
    if not isinstance(code, str) or len(code) != 4 or not code.isdigit():
        return tour, "Enter exactly four digits."
    if code != VAULT_CODE:
        new = copy.deepcopy(tour)
        new["round2"]["duos"][duo_id]["locked_until"] = now + LOCKOUT_SECONDS
        return new, f"Wrong code. Your duo is locked out for {LOCKOUT_SECONDS} seconds."

    new = copy.deepcopy(tour)
    changed_duo = new["round2"]["duos"][duo_id]
    changed_duo["code_solved_at"] = now
    changed_duo["locked_until"] = None
    return new, "Vault unlocked! Your duo can now choose a route."


def choose_door(tour, player_id, duo_id, destination, now, rng=None):
    """Take one map step. A wrong door adds an alarm and leaves the route in place."""
    _, duo, problem = _validate_action(tour, player_id, duo_id, now)
    if problem:
        return tour, problem
    if duo["code_solved_at"] is None:
        return tour, "Solve the vault code before choosing a route."

    route_step = duo["route_step"]
    if route_step >= len(SAFE_ROUTE) - 1:
        return tour, "Your duo has already completed the route."
    here = SAFE_ROUTE[route_step]
    if destination not in ROUTE_CHOICES[here]:
        return tour, "That door isn't available from here."

    new = copy.deepcopy(tour)
    changed_duo = new["round2"]["duos"][duo_id]
    if destination == WRONG_DOORS[here]:
        changed_duo["alarm_count"] += 1
        changed_duo["locked_until"] = now + LOCKOUT_SECONDS
        return new, f"Alarm! Your route stays at {here}; locked out for {LOCKOUT_SECONDS} seconds."

    changed_duo["route_step"] += 1
    changed_duo["locked_until"] = None
    if changed_duo["route_step"] == len(SAFE_ROUTE) - 1:
        changed_duo["finished_at"] = now
        _finish(new, duo_id, now, "route")
        return new, "Rooftop reached! Your duo advances to the final."
    return new, f"Safe choice. You reached {destination}."


def share_clue(tour, player_id, now):
    """The clue holder sends their clue to their teammate's phone. Only the holder
    can do this (their own card), once, while Round 2 is being played."""
    round_state = tour.get("round2") or {}
    if tour.get("status") != "round2" or round_state.get("winner") is not None:
        return tour, "Round 2 is not active."
    assignment = round_state.get("players", {}).get(player_id)
    if not assignment:
        return tour, "You're not playing in Round 2."
    if _challenge_started_at(round_state) is None:
        return tour, "The Round 2 challenge hasn't started yet."
    if assignment.get("shared_at") is not None:
        return tour, "You've already sent your clue."
    new = copy.deepcopy(tour)
    new["round2"]["players"][player_id]["shared_at"] = now
    return new, "Clue sent to your teammate!"


def prepare_round(tour, now, rng=None):
    """Migrate older Round 2 states and settle any expired challenge."""
    round_state = tour.get("round2")
    if (tour.get("status") == "round2" and round_state
            and "challenge_started_at" not in round_state):
        new = copy.deepcopy(tour)
        intro_ends_at = round_state.get("intro_ends_at")
        if intro_ends_at is None:
            intro_ends_at = round_state.get("started_at", now) + INTRO_SECONDS
        new["round2"]["intro_ends_at"] = intro_ends_at
        new["round2"]["challenge_started_at"] = intro_ends_at
        tour = new
    return settle(tour, now, rng)


def start_challenge(tour, player_id, now):
    """Let a Round 2 finalist start the shared challenge and its server timer."""
    round_state = tour.get("round2") or {}
    if tour.get("status") != "round2":
        return tour, "Round 2 is not active."
    if player_id in tour.get("eliminated", []):
        return tour, "You were eliminated and can't start Round 2."
    if player_id not in round_state.get("players", {}):
        return tour, "You're not playing in Round 2."
    if _challenge_started_at(round_state) is not None:
        return tour, "The Round 2 challenge has already started."

    new = copy.deepcopy(tour)
    new["round2"]["intro_ends_at"] = now
    new["round2"]["challenge_started_at"] = now
    return new, "Round 2 challenge started."


def settle(tour, now, rng=None):
    """Resolve the timeout once. Storage serializes this with every other action."""
    round_state = tour.get("round2")
    if tour.get("status") != "round2" or not round_state:
        return tour, ""
    challenge_started_at = _challenge_started_at(round_state)
    if challenge_started_at is None or now < challenge_started_at + ROUND_SECONDS:
        return tour, ""

    solved = [duo_id for duo_id, duo in round_state["duos"].items()
              if duo["code_solved_at"] is not None]
    contenders = solved if solved else list(round_state["duos"])
    fewest_alarms = min(round_state["duos"][duo_id]["alarm_count"] for duo_id in contenders)
    contenders = [duo_id for duo_id in contenders
                  if round_state["duos"][duo_id]["alarm_count"] == fewest_alarms]
    winner = (rng or random.Random()).choice(contenders)

    new = copy.deepcopy(tour)
    _finish(new, winner, now, "timeout")
    return new, f"Time is up. {winner.replace('_', ' ').title()} wins the vault challenge."


def _finish(tour, winner, now, decided_by):
    """Record one winner and eliminate the other duo in the same state update."""
    round_state = tour["round2"]
    if round_state["winner"] is not None:
        return False
    round_state["winner"] = winner
    round_state["resolved_at"] = now
    round_state["decided_by"] = decided_by
    round_state["duos"][winner]["finished_at"] = (
        round_state["duos"][winner]["finished_at"] or now
    )
    losers = [duo_id for duo_id in round_state["duos"] if duo_id != winner]
    losing_players = [player_id for duo_id in losers
                      for player_id in round_state["duos"][duo_id]["players"]]
    already_eliminated = set(tour.get("eliminated", []))
    tour["eliminated"] = list(tour.get("eliminated", [])) + [
        player_id for player_id in losing_players if player_id not in already_eliminated
    ]
    tour["status"] = "final"
    return True


def player_view(tour, player_id):
    """Return only this player's card and own duo progress for their screen."""
    view = {"status": tour.get("status"), "resolved_at": None,
            "decided_by": None, "advanced": False}
    round_state = tour.get("round2") or {}
    view["resolved_at"] = round_state.get("resolved_at")
    view["decided_by"] = round_state.get("decided_by")
    if tour.get("status") not in ("round2", "final"):
        return view

    assignment = round_state.get("players", {}).get(player_id)
    if assignment is None:
        return view
    duo_id = assignment["duo_id"]
    duo = round_state["duos"][duo_id]
    teammate_id = next(pid for pid in duo["players"] if pid != player_id)
    teammate = next((p for p in tour.get("players", []) if p["id"] == teammate_id), None)
    teammate_assignment = round_state["players"].get(teammate_id, {})
    challenge_started_at = _challenge_started_at(round_state)
    view.update({
        "duo_id": duo_id,
        "card": CARD_A if assignment["card"] == "A" else CARD_B,
        "card_shared": assignment.get("shared_at") is not None,
        # The teammate's clue, but only once the teammate chose to send it.
        "teammate_card": ((CARD_A if teammate_assignment.get("card") == "A" else CARD_B)
                          if teammate_assignment.get("shared_at") is not None else None),
        "teammate": copy.deepcopy(teammate),
        "code_solved_at": duo["code_solved_at"],
        "route_step": duo["route_step"],
        "alarm_count": duo["alarm_count"],
        "locked_until": duo["locked_until"],
        "finished_at": duo["finished_at"],
        "started_at": challenge_started_at,
        "ends_at": (challenge_started_at + ROUND_SECONDS
                    if challenge_started_at is not None else None),
        "advanced": round_state["winner"] == duo_id,
    })
    return view
