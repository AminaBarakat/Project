"""Tests for spectators.py: calls (predictions) and reactions from eliminated players."""

import random

import pytest

import round2 as r2
import round3 as r3
import spectators as sp
import tournament

NOW = 1_000_000.0
ACTIVE = ["p0", "p1", "p2", "p3"]
OUT = ["p4", "p5", "p6", "p7"]          # eliminated in Round 1: the spectators


def round2_started():
    return {
        "code": "ABCD",
        "status": "round2",
        "host_id": "p0",
        "players": [{"id": pid, "name": pid.upper(), "appearance": None} for pid in ACTIVE + OUT],
        "eliminated": list(OUT),
        "round2": r2.new_round(ACTIVE, NOW, random.Random(7)),
    }


def finish_round2(tour, duo_id="duo_1"):
    player = tour["round2"]["duos"][duo_id]["players"][0]
    tour, _ = r2.submit_code(tour, player, duo_id, "3583", NOW + 1)
    tour, _ = r2.choose_door(tour, player, duo_id, "Gallery", NOW + 2)
    tour, _ = r2.choose_door(tour, player, duo_id, "Rooftop", NOW + 3)
    assert tour["status"] == "final"
    return tour


def start_round3(tour):
    finalists = tour["round2"]["duos"][tour["round2"]["winner"]]["players"]
    tour, message = tournament.start_round3(tour, finalists[0], list(finalists), NOW + 10)
    assert tour["status"] == "round3", message
    return tour


# --- calls ---------------------------------------------------------------------

def test_only_spectators_can_make_a_call_and_only_for_a_real_choice():
    tour = round2_started()
    assert sp.make_call(tour, "p0", "round2", "duo_1")[1] == "Only spectators can make a call."
    assert sp.make_call(tour, "p4", "round2", "duo_9")[1] == "That's not one of the choices."
    assert sp.make_call(tour, "p4", "round3", "p0")[1] == "Calls are closed for this round."
    new, message = sp.make_call(tour, "p4", "round2", "duo_1")
    assert message == "Call locked in!"
    assert sp.my_call(new, "p4", "round2") == "duo_1"
    assert "spectators" not in tour                     # the original is untouched


def test_a_call_cannot_be_changed():
    tour, _ = sp.make_call(round2_started(), "p4", "round2", "duo_1")
    again, message = sp.make_call(tour, "p4", "round2", "duo_2")
    assert message == "You've already made your call." and sp.my_call(again, "p4", "round2") == "duo_1"


def test_crowd_counts_every_choice_even_with_no_backers():
    tour = round2_started()
    assert sp.crowd(tour, "round2") == {"duo_1": 0, "duo_2": 0}
    for pid, duo in (("p4", "duo_1"), ("p5", "duo_1"), ("p6", "duo_2")):
        tour, _ = sp.make_call(tour, pid, "round2", duo)
    assert sp.crowd(tour, "round2") == {"duo_1": 2, "duo_2": 1}


def test_round2_calls_close_when_the_vault_is_opened_and_we_know_who_called_it():
    tour = round2_started()
    tour, _ = sp.make_call(tour, "p4", "round2", "duo_1")
    tour, _ = sp.make_call(tour, "p5", "round2", "duo_2")
    tour = finish_round2(tour, "duo_1")
    assert sp.make_call(tour, "p6", "round2", "duo_1")[1] == "Calls are closed for this round."
    assert sp.who_called_it(tour, "round2") == ["p4"]
    assert sp.crowd(tour, "round2") == {"duo_1": 1, "duo_2": 1}     # still shown on the results


def test_round3_calls_open_after_round2_and_the_losing_duo_can_call_too():
    tour = finish_round2(round2_started(), "duo_1")
    assert sp.open_call(tour) == "round3"
    finalists = tour["round2"]["duos"]["duo_1"]["players"]
    loser = tour["round2"]["duos"]["duo_2"]["players"][0]           # now eliminated → spectator
    tour, message = sp.make_call(tour, loser, "round3", finalists[1])
    assert message == "Call locked in!"
    tour = start_round3(tour)
    tour, _ = sp.make_call(tour, "p4", "round3", finalists[0])      # still open during the story/mystery
    assert sp.crowd(tour, "round3") == {finalists[0]: 1, finalists[1]: 1}


def test_round3_calls_close_once_there_is_a_champion():
    tour = start_round3(finish_round2(round2_started(), "duo_1"))
    finalists = tour["round3"]["finalists"]
    tour, _ = sp.make_call(tour, "p4", "round3", finalists[0])
    tour, _ = r3.start_investigation(tour, finalists[0], NOW + 60)
    solution = r3.SOLUTION
    tour, _ = r3.answer(tour, finalists[0], solution["suspect"], solution["room"], solution["object"],
                        NOW + 61, r3.FINAL_CODE)
    assert tour["round3"]["winner"] == finalists[0]
    assert sp.open_call(tour) is None
    assert sp.make_call(tour, "p5", "round3", finalists[0])[1] == "Calls are closed for this round."
    assert sp.who_called_it(tour, "round3") == ["p4"]


def test_nobody_has_called_it_while_the_round_is_still_on():
    tour, _ = sp.make_call(round2_started(), "p4", "round2", "duo_1")
    assert sp.who_called_it(tour, "round2") == []


# --- reactions -----------------------------------------------------------------

def test_spectators_send_reactions_that_everyone_sees_for_a_few_seconds():
    tour = round2_started()
    tour, message = sp.react(tour, "p4", "elementary", NOW)
    assert message == "Elementary!"
    on_screen = sp.recent_reactions(tour, NOW + 2)
    assert [(r["by"], r["kind"], r["age"]) for r in on_screen] == [("p4", "elementary", 2.0)]
    assert sp.recent_reactions(tour, NOW + sp.REACTION_SECONDS + 0.1) == []


def test_players_still_in_the_game_cannot_react_and_unknown_reactions_are_refused():
    tour = round2_started()
    assert sp.react(tour, "p0", "elementary", NOW)[1] == "Only spectators can send reactions."
    assert sp.react(tour, "p4", "<script>", NOW)[1] == "That reaction doesn't exist."


def test_reactions_only_from_round2_on():
    tour = round2_started()
    tour["status"] = "round1_results"
    assert sp.react(tour, "p4", "alarm", NOW)[1] == "Reactions open in Round 2."


def test_a_spectator_must_wait_between_reactions_but_others_need_not():
    tour, _ = sp.react(round2_started(), "p4", "alarm", NOW)
    assert sp.react(tour, "p4", "footprints", NOW + 1)[1].startswith("Easy, detective!")
    tour, _ = sp.react(tour, "p5", "footprints", NOW + 1)
    tour, message = sp.react(tour, "p4", "footprints", NOW + sp.REACTION_COOLDOWN)
    assert message == "On their trail"
    assert [r["id"] for r in tour["spectators"]["reactions"]] == [1, 2, 3]


def test_only_the_latest_reactions_are_kept():
    tour = round2_started()
    for k in range(sp.KEEP_REACTIONS + 5):
        tour, _ = sp.react(tour, OUT[k % 4], "magnifier", NOW + k * sp.REACTION_COOLDOWN)
    assert len(tour["spectators"]["reactions"]) == sp.KEEP_REACTIONS


@pytest.mark.parametrize("kind", sorted(sp.REACTIONS))
def test_every_reaction_has_a_style_and_text(kind):
    assert sp.REACTIONS[kind]["style"] in ("bubble", "sticker") and sp.REACTIONS[kind]["text"]
