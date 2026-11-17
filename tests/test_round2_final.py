"""Round 2 finalists enter Round 3 as the exact winning duo."""

import random

import round2
import tournament as rules


def completed_round2():
    tour, _ = rules.new_tournament("ABCD", "p0", "Player 0")
    for pid in range(1, 4):
        tour, _ = rules.join(tour, f"p{pid}", f"Player {pid}")
    tour["status"] = "round2"
    tour["round2"] = round2.new_round(("p0", "p1", "p2", "p3"), 100, random.Random(1))
    winner, loser = list(tour["round2"]["duos"])
    tour["round2"]["winner"] = winner
    tour["round2"]["duos"][winner]["finished_at"] = 110
    tour["status"] = "final"
    tour["eliminated"] = tour["round2"]["duos"][loser]["players"][:]
    return tour, winner, loser


def test_winning_duo_starts_round3_with_exactly_its_two_players():
    tour, winner, _ = completed_round2()
    finalists = tour["round2"]["duos"][winner]["players"]
    after, message = rules.start_round3(tour, finalists[0], finalists, now=120)
    assert after["status"] == "round3"
    assert after["round3"]["finalists"] == finalists
    assert after["round3"]["story_started_at"] == 120
    assert message


def test_losing_duo_cannot_start_round3_or_replace_the_finalists():
    tour, winner, loser = completed_round2()
    finalists = tour["round2"]["duos"][winner]["players"]
    losing_player = tour["round2"]["duos"][loser]["players"][0]
    refused, message = rules.start_round3(tour, losing_player, finalists, now=120)
    assert refused == tour and "winning duo" in message.lower()

    refused, message = rules.start_round3(tour, finalists[0], [finalists[0], losing_player], now=120)
    assert refused == tour and "both players" in message.lower()
