"""Round 2's matchup intro uses one shared, server-set start time."""

import copy
import random

import round2 as r2


NOW = 1_000_000.0
PLAYER_IDS = ["p0", "p1", "p2", "p3"]


def active_tournament():
    return {
        "status": "round2",
        "players": [{"id": player_id, "name": player_id, "appearance": None}
                    for player_id in PLAYER_IDS],
        "eliminated": [],
        "round2": r2.new_round(PLAYER_IDS, NOW, random.Random(7)),
    }


def test_first_round2_screen_persists_one_shared_intro_deadline():
    tour = active_tournament()
    original = copy.deepcopy(tour)

    prepared, _ = r2.prepare_round(tour, NOW + 2)
    intro_ends_at = NOW + r2.INTRO_SECONDS

    assert tour == original
    assert prepared["round2"]["intro_ends_at"] == intro_ends_at
    assert prepared["round2"]["challenge_started_at"] == intro_ends_at

    refreshed, _ = r2.prepare_round(prepared, NOW + 4)
    assert refreshed == prepared


def test_code_submission_waits_for_the_intro_to_finish():
    tour, _ = r2.prepare_round(active_tournament(), NOW)
    player_id = PLAYER_IDS[0]
    duo_id = tour["round2"]["players"][player_id]["duo_id"]

    refused, message = r2.submit_code(tour, player_id, duo_id, "3583", NOW + r2.INTRO_SECONDS - 1)
    assert refused == tour
    assert "introduction" in message.lower()

    accepted, message = r2.submit_code(tour, player_id, duo_id, "3583", NOW + r2.INTRO_SECONDS)
    assert accepted["round2"]["duos"][duo_id]["code_solved_at"] == NOW + r2.INTRO_SECONDS
    assert "unlocked" in message.lower()
