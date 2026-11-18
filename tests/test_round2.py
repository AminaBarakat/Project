"""Tests for Round 2's server-side Duo Vault Challenge rules."""

import copy
import random

import round2 as r2
import round1

NOW = 1_000_000.0
PLAYER_IDS = ["p0", "p1", "p2", "p3"]


def started():
    tour = {
        "code": "ABCD",
        "status": "round2",
        "players": [{"id": pid, "name": pid, "appearance": None} for pid in PLAYER_IDS + ["p4"]],
        "eliminated": ["p4"],
        "round2": r2.new_round(PLAYER_IDS, NOW, random.Random(7)),
    }
    return tour


def duo_of(tour, player_id):
    return tour["round2"]["players"][player_id]["duo_id"]


def players_in(tour, duo_id):
    return tour["round2"]["duos"][duo_id]["players"]


def unlock(tour, duo_id, player=None, at=NOW + 1):
    player = player or players_in(tour, duo_id)[0]
    return r2.submit_code(tour, player, duo_id, "3583", at)


def finish_route(tour, duo_id, now=NOW + 5):
    player = players_in(tour, duo_id)[0]
    tour, _ = r2.choose_door(tour, player, duo_id, "Gallery", now)
    return r2.choose_door(tour, player, duo_id, "Rooftop", now + 1)


def test_round2_pairs_only_the_four_active_players_with_one_card_each():
    tour = started()
    assignments = tour["round2"]["players"]
    assert set(assignments) == set(PLAYER_IDS)
    assert all({assignments[pid]["card"] for pid in duo["players"]} == {"A", "B"}
               for duo in tour["round2"]["duos"].values())
    assert tour["round2"]["started_at"] == NOW


def test_round1_results_transition_starts_round2_with_the_four_winners():
    winners = ["p0", "p1", "p2", "p3"]
    losers = ["p4", "p5", "p6", "p7"]
    tour = {
        "status": "round1_results",
        "eliminated": losers[:],
        "round1": {
            "results_at": NOW,
            "results": [{"winner": winner, "loser": loser}
                        for winner, loser in zip(winners, losers)],
        },
    }
    # Round 2 starts once all four winners have tapped "I'm ready" (not after a countdown).
    waited, _ = round1.settle(tour, NOW + 60, random.Random(4))
    assert waited["status"] == "round1_results"
    after = tour
    for k, winner in enumerate(winners):
        after, _ = round1.mark_ready(after, winner, NOW + 1 + k, random.Random(4))
    assert after["status"] == "round2"
    assert set(after["round2"]["players"]) == set(winners)
    assert after["round2"]["started_at"] == NOW + 4


def test_3583_is_accepted_and_both_teammates_see_progress():
    tour = started()
    pid = PLAYER_IDS[0]
    duo_id = duo_of(tour, pid)
    after, message = unlock(tour, duo_id, pid)
    assert "unlocked" in message.lower()
    assert after["round2"]["duos"][duo_id]["code_solved_at"] == NOW + 1
    teammate = next(other for other in players_in(after, duo_id) if other != pid)
    assert r2.player_view(after, teammate)["code_solved_at"] == NOW + 1


def test_3538_is_wrong_code_and_358_and_35833_are_rejected_for_format():
    for code in ("3538", "358", "35833"):
        tour = started()
        pid = PLAYER_IDS[0]
        duo_id = duo_of(tour, pid)
        after, message = r2.submit_code(tour, pid, duo_id, code, NOW + 1)
        if code == "3538":
            assert after != tour
        else:
            assert after == tour
        assert message
    tour = started()
    pid = PLAYER_IDS[0]
    wrong = r2.submit_code(tour, pid, duo_of(tour, pid), "3538", NOW + 1)
    assert "wrong code" in wrong[1].lower()
    tour = started()
    pid = PLAYER_IDS[0]
    duo_id = duo_of(tour, pid)
    locked, _ = r2.submit_code(tour, pid, duo_id, "3538", NOW + 1)
    assert locked["round2"]["duos"][duo_id]["locked_until"] == NOW + 1 + r2.LOCKOUT_SECONDS
    refused, message = r2.submit_code(locked, pid, duo_id, "3583", NOW + 2)
    assert refused == locked and "locked out" in message.lower()


def test_route_is_rejected_before_the_code_is_solved():
    tour = started()
    pid = PLAYER_IDS[0]
    duo_id = duo_of(tour, pid)
    after, message = r2.choose_door(tour, pid, duo_id, "Gallery", NOW + 1)
    assert after == tour
    assert "solve" in message.lower()


def test_safe_route_vault_gallery_rooftop_completes_round():
    tour = started()
    pid = PLAYER_IDS[0]
    duo_id = duo_of(tour, pid)
    tour, _ = unlock(tour, duo_id, pid)
    tour, message = r2.choose_door(tour, pid, duo_id, "Gallery", NOW + 2)
    assert tour["round2"]["duos"][duo_id]["route_step"] == 1
    assert tour["status"] == "round2"
    tour, message = r2.choose_door(tour, pid, duo_id, "Rooftop", NOW + 3)
    assert "advances" in message.lower()
    assert tour["round2"]["duos"][duo_id]["finished_at"] == NOW + 3
    assert tour["round2"]["winner"] == duo_id
    assert tour["status"] == "final"


def test_wrong_door_adds_alarm_and_lockout_without_restarting_route():
    tour = started()
    pid = PLAYER_IDS[0]
    duo_id = duo_of(tour, pid)
    tour, _ = unlock(tour, duo_id, pid)
    tour, message = r2.choose_door(tour, pid, duo_id, "Cellar", NOW + 2)
    assert "alarm" in message.lower()
    duo = tour["round2"]["duos"][duo_id]
    assert duo["alarm_count"] == 1
    assert duo["route_step"] == 0
    assert duo["locked_until"] == NOW + 2 + r2.LOCKOUT_SECONDS
    refused, message = r2.choose_door(tour, pid, duo_id, "Gallery", NOW + 3)
    assert refused == tour
    assert "locked out" in message.lower()
    accepted, _ = r2.choose_door(tour, pid, duo_id, "Gallery", NOW + 13)
    assert accepted["round2"]["duos"][duo_id]["route_step"] == 1


def test_card_view_contains_only_the_players_own_clue():
    tour = started()
    for pid in PLAYER_IDS:
        view = r2.player_view(tour, pid)
        card_id = tour["round2"]["players"][pid]["card"]
        other_card = r2.CARD_B if card_id == "A" else r2.CARD_A
        assert view["card"] == (r2.CARD_A if card_id == "A" else r2.CARD_B)
        assert other_card not in repr(view)
        assert "players" not in view and "duos" not in view


def test_first_duo_to_finish_wins_and_second_completion_is_rejected():
    tour = started()
    duo_a, duo_b = list(tour["round2"]["duos"])
    for duo_id in (duo_a, duo_b):
        tour, _ = unlock(tour, duo_id)
        player = players_in(tour, duo_id)[0]
        tour, _ = r2.choose_door(tour, player, duo_id, "Gallery", NOW + 2)
    tour, _ = r2.choose_door(tour, players_in(tour, duo_a)[0], duo_a, "Rooftop", NOW + 3)
    before = copy.deepcopy(tour)
    refused, message = r2.choose_door(tour, players_in(tour, duo_b)[0], duo_b, "Rooftop", NOW + 3)
    assert refused == before
    assert "already won" in message.lower()
    assert tour["round2"]["winner"] == duo_a


def test_timeout_prefers_the_duo_that_solved_the_code():
    tour = started()
    solved, unsolved = list(tour["round2"]["duos"])
    tour, _ = unlock(tour, solved, at=NOW + 10)
    tour["round2"]["duos"][solved]["alarm_count"] = 4
    tour["round2"]["duos"][unsolved]["alarm_count"] = 0
    after, _ = r2.settle(tour, NOW + r2.ROUND_SECONDS, random.Random(1))
    assert after["round2"]["winner"] == solved
    assert after["round2"]["decided_by"] == "timeout"


def test_timeout_uses_fewer_alarms_when_both_solved_and_random_when_still_tied():
    tour = started()
    duos = list(tour["round2"]["duos"])
    for duo_id in duos:
        tour, _ = unlock(tour, duo_id)
    tour["round2"]["duos"][duos[0]]["alarm_count"] = 2
    tour["round2"]["duos"][duos[1]]["alarm_count"] = 1
    after, _ = r2.settle(tour, NOW + r2.ROUND_SECONDS, random.Random(2))
    assert after["round2"]["winner"] == duos[1]

    tied = started()
    for duo_id in duos:
        tied, _ = unlock(tied, duo_id)
    winner, _ = r2.settle(tied, NOW + r2.ROUND_SECONDS, random.Random(2))
    again, _ = r2.settle(tied, NOW + r2.ROUND_SECONDS, random.Random(2))
    assert winner["round2"]["winner"] in duos
    assert winner == again

    unsolved = started()
    fewer_alarms = list(unsolved["round2"]["duos"])[1]
    other = next(duo_id for duo_id in unsolved["round2"]["duos"] if duo_id != fewer_alarms)
    unsolved["round2"]["duos"][other]["alarm_count"] = 1
    after, _ = r2.settle(unsolved, NOW + r2.ROUND_SECONDS, random.Random(1))
    assert after["round2"]["winner"] == fewer_alarms


def test_eliminated_player_and_member_of_another_duo_cannot_submit():
    tour = started()
    pid = PLAYER_IDS[0]
    own_duo = duo_of(tour, pid)
    other_duo = next(did for did in tour["round2"]["duos"] if did != own_duo)
    before = copy.deepcopy(tour)
    after, message = r2.submit_code(tour, "p4", own_duo, "3583", NOW + 1)
    assert after == before and "eliminated" in message.lower()
    after, message = r2.submit_code(tour, pid, other_duo, "3583", NOW + 1)
    assert after == before and "not in that duo" in message.lower()


def test_submissions_after_timeout_and_outside_round2_are_rejected():
    tour = started()
    pid = PLAYER_IDS[0]
    duo_id = duo_of(tour, pid)
    before = copy.deepcopy(tour)
    after, message = r2.submit_code(tour, pid, duo_id, "3583", NOW + r2.ROUND_SECONDS)
    assert after == before and "time is up" in message.lower()
    tour["status"] = "final"
    before = copy.deepcopy(tour)
    after, message = r2.submit_code(tour, pid, duo_id, "3583", NOW + 1)
    assert after == before and "not active" in message.lower()


def test_winner_moves_game_to_final_and_eliminates_losing_duo():
    tour = started()
    winner, loser = list(tour["round2"]["duos"])
    tour, _ = finish_route(unlock(tour, winner)[0], winner)
    winning_players = set(players_in(tour, winner))
    losing_players = set(players_in(tour, loser))
    assert tour["status"] == "final"
    assert set(tour["eliminated"]) == {"p4"} | losing_players
    assert set(PLAYER_IDS) - set(tour["eliminated"]) == winning_players
    for pid in winning_players:
        assert r2.player_view(tour, pid)["advanced"] is True
    for pid in losing_players:
        assert r2.player_view(tour, pid)["advanced"] is False
