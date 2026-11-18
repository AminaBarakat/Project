"""The fan favourite: podium place 3, chosen by everyone.

As soon as the final (Round 3) is decided, every player gets a short vote before
the podium is shown. You can't vote for yourself or for the two finalists (they
already have places 1 and 2). The vote closes after VOTE_SECONDS, or as soon as
everyone has voted.

The player with the most votes becomes the fan favourite. A tie goes to the
better Round 1 score (most games right, then fastest), so it is always decided.
If nobody votes at all, the best Round 1 player gets the place ("Round 1 ace").

Plain Python like the other rule files: no Streamlit, no database.
"""

import copy

import round1 as r1

VOTE_SECONDS = 10


def _round3(tour):
    return tour.get("round3") or {}


def _votes(tour):
    return (tour.get("fan_vote") or {}).get("votes", {})


def opens_at(tour):
    """When the vote opened (the moment the final was decided), or None."""
    return _round3(tour).get("results_at")


def closes_at(tour):
    """When the vote closes: VOTE_SECONDS after it opened, or earlier if everyone
    has already voted. None while the final is still being played."""
    start = opens_at(tour)
    if start is None:
        return None
    everyone_at = (tour.get("fan_vote") or {}).get("everyone_voted_at")
    deadline = start + VOTE_SECONDS
    return min(deadline, everyone_at) if everyone_at is not None else deadline


def is_open(tour, now):
    end = closes_at(tour)
    return end is not None and now < end


def candidates(tour, voter_id=None):
    """Who can be voted for: everyone except the two finalists (and yourself)."""
    finalists = set(_round3(tour).get("finalists", []))
    return [p["id"] for p in tour["players"] if p["id"] not in finalists and p["id"] != voter_id]


def my_vote(tour, voter_id):
    return _votes(tour).get(voter_id)


def vote(tour, voter_id, candidate_id, now):
    """One player votes for a fan favourite. One vote each, no changing it."""
    if voter_id not in {p["id"] for p in tour["players"]}:
        return tour, "You're not in this game."
    if not is_open(tour, now):
        return tour, "The vote is closed."
    if my_vote(tour, voter_id) is not None:
        return tour, "You've already voted."
    if candidate_id == voter_id:
        return tour, "You can't vote for yourself!"
    if candidate_id not in candidates(tour, voter_id):
        return tour, "You can't vote for that player."
    new = copy.deepcopy(tour)
    state = new.setdefault("fan_vote", {"votes": {}})
    state.setdefault("votes", {})[voter_id] = candidate_id
    if len(state["votes"]) == len(new["players"]):
        state["everyone_voted_at"] = now           # no need to wait for the clock
    return new, "Vote counted!"


def counts(tour):
    """{candidate: number of votes}, every candidate listed."""
    out = {pid: 0 for pid in candidates(tour)}
    for choice in _votes(tour).values():
        if choice in out:
            out[choice] += 1
    return out


def _round1_rank(tour, pid):
    """Better Round 1 = more games right, then less time. Name last, so it is always decided."""
    player = next(p for p in tour["players"] if p["id"] == pid)
    if tour.get("round1") and pid in tour["round1"].get("players", {}):
        return (-r1.points(tour, pid), r1.total_seconds(tour, pid), player["name"].casefold())
    return (0, 0, player["name"].casefold())


def favourite(tour):
    """(player id, votes, note) for podium place 3, or None if nobody can get it."""
    tally = counts(tour)
    if not tally:
        return None
    best = max(tally.values())
    if best == 0:
        winner = min(tally, key=lambda pid: _round1_rank(tour, pid))
        return winner, 0, "Round 1 ace"
    tied = [pid for pid, n in tally.items() if n == best]
    winner = min(tied, key=lambda pid: _round1_rank(tour, pid))
    return winner, best, "Fan favourite"
