"""Tests for fan_vote.py: everyone votes for podium place 3 after the final."""

import fan_vote as fv

NOW = 1_000_000.0
IDS = [f"p{i}" for i in range(8)]
FINALISTS = ["p0", "p1"]


def decided(round1=None):
    """A tournament whose final was decided at NOW (the vote opens then)."""
    tour = {
        "code": "ABCD",
        "status": "round3_results",
        "players": [{"id": pid, "name": pid.upper(), "appearance": None} for pid in IDS],
        "eliminated": IDS[2:],
        "round3": {"finalists": list(FINALISTS), "winner": "p0", "results_at": NOW},
    }
    if round1:
        tour["round1"] = round1
    return tour


def test_the_vote_opens_when_the_final_is_decided_and_lasts_ten_seconds():
    tour = decided()
    assert fv.VOTE_SECONDS == 10
    assert fv.is_open(tour, NOW) and fv.is_open(tour, NOW + 9.9)
    assert not fv.is_open(tour, NOW + 10)
    still_playing = decided()
    still_playing["round3"]["results_at"] = None
    assert not fv.is_open(still_playing, NOW)


def test_you_cannot_vote_for_yourself_or_a_finalist():
    tour = decided()
    assert fv.vote(tour, "p3", "p3", NOW)[1] == "You can't vote for yourself!"
    assert fv.vote(tour, "p3", "p0", NOW)[1] == "You can't vote for that player."
    assert fv.vote(tour, "p3", "nobody", NOW)[1] == "You can't vote for that player."
    assert fv.candidates(tour, "p3") == ["p2", "p4", "p5", "p6", "p7"]


def test_finalists_vote_too_and_one_vote_each():
    tour, message = fv.vote(decided(), "p0", "p5", NOW + 1)
    assert message == "Vote counted!" and fv.my_vote(tour, "p0") == "p5"
    assert fv.vote(tour, "p0", "p6", NOW + 2)[1] == "You've already voted."


def test_late_votes_and_strangers_are_refused():
    assert fv.vote(decided(), "p3", "p4", NOW + 10)[1] == "The vote is closed."
    assert fv.vote(decided(), "zz", "p4", NOW)[1] == "You're not in this game."


def test_the_vote_closes_early_once_everyone_has_voted():
    tour = decided()
    for k, voter in enumerate(IDS):
        tour, _ = fv.vote(tour, voter, "p2" if voter != "p2" else "p3", NOW + k * 0.5)
    assert fv.closes_at(tour) == NOW + 3.5
    assert not fv.is_open(tour, NOW + 4)


def test_most_votes_wins():
    tour = decided()
    for voter, choice in (("p0", "p5"), ("p1", "p5"), ("p2", "p6"), ("p3", "p5")):
        tour, _ = fv.vote(tour, voter, choice, NOW)
    assert fv.counts(tour)["p5"] == 3
    assert fv.favourite(tour) == ("p5", 3, "Fan favourite")


def test_a_tie_goes_to_the_better_round1_score():
    # p6 got more games right than p5; p7 as many as p6 but slower.
    def player(rights, seconds):
        return {"game_started_at": 0, "results": [{"correct": k < rights, "seconds": seconds, "timed_out": False}
                                                  for k in range(4)]}
    round1 = {"players": {"p5": player(1, 10), "p6": player(3, 20), "p7": player(3, 25)}}
    tour = decided(round1)
    for voter, choice in (("p0", "p5"), ("p1", "p6"), ("p2", "p7")):
        tour, _ = fv.vote(tour, voter, choice, NOW)
    assert fv.favourite(tour) == ("p6", 1, "Fan favourite")


def test_with_no_votes_the_best_round1_player_gets_the_place():
    def player(rights):
        return {"game_started_at": 0, "results": [{"correct": k < rights, "seconds": 5, "timed_out": False}
                                                  for k in range(4)]}
    tour = decided({"players": {"p3": player(2), "p4": player(4)}})
    assert fv.favourite(tour) == ("p4", 0, "Round 1 ace")


def test_voting_does_not_change_the_original_tournament():
    tour = decided()
    fv.vote(tour, "p3", "p4", NOW)
    assert "fan_vote" not in tour
