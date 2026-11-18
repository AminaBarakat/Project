"""Tests for the Final Mansion Mystery rules."""

import copy
import random

import round3 as r3
import tournament as t

T0 = 3_000_000.0
PLAY = T0 + 24
END = T0 + 20 + r3.ROUND_SECONDS


def final_started():
    """A minimal tournament that has arrived at the two-finalist finale."""
    tour, _ = t.new_tournament("ABCD", "p0", "Ana")
    for pid, name in (("p1", "Bruno"), ("p2", "Carla"), ("p3", "Dani")):
        tour, _ = t.join(tour, pid, name)
    tour["status"] = "round2"
    tour["eliminated"] = ["p2", "p3"]
    tour, _ = t.start_round3(tour, "p0", ["p0", "p1"], now=T0)
    tour, _ = r3.start_investigation(tour, "p0", T0 + 20)
    return tour


def assert_refused(tour, result):
    after, message = result
    assert after == tour
    assert message


def test_final_mystery_has_the_expected_solution_and_code():
    assert r3.SOLUTION == {"suspect": "Nova", "room": "Conservatory", "object": "Map"}
    assert r3.FINAL_CODE == "318"


def test_story_comes_before_the_shared_final_timer():
    tour, _ = t.new_tournament("ABCD", "p0", "Ana")
    tour, _ = t.join(tour, "p1", "Bruno")
    tour["status"] = "round2"
    tour, _ = t.start_round3(tour, "p0", ["p0", "p1"], now=T0)
    assert r3.story_text(tour, T0) == ""
    assert tour["round3"]["starts_at"] is None
    assert_refused(tour, r3.answer(tour, "p0", "Nova", "Conservatory", "Map", T0 + 1))
    assert_refused(tour, r3.start_investigation(tour, "p0", T0 + 1))

    started, _ = r3.start_investigation(tour, "p0", T0 + 20)
    assert started["round3"]["starts_at"] == T0 + 20
    assert started["round3"]["ends_at"] == T0 + 20 + r3.ROUND_SECONDS


def test_finalist_can_solve_the_mystery_and_wins_immediately():
    tour = final_started()
    solved, message = r3.answer(tour, "p1", "Nova", "Conservatory", "Map", PLAY)
    assert solved["status"] == "round3_results"
    assert solved["round3"]["winner"] == "p1"
    assert solved["round3"]["decided_by"] == "solved the mystery"
    assert "Moonstone Vault" in message


def test_correct_theory_needs_the_vault_code_when_one_is_supplied():
    tour = final_started()
    after, message = r3.answer(tour, "p1", "Nova", "Conservatory", "Map", PLAY, "999")
    assert after["status"] == "round3"
    assert len(after["round3"]["guesses"]["p1"]) == 1
    assert "vault code" in message


def test_wrong_theory_does_not_reveal_which_part_was_wrong():
    tour = final_started()
    after, message = r3.answer(tour, "p1", "Theo", "Library", "Key", PLAY)
    assert after["status"] == "round3"
    assert len(after["round3"]["guesses"]["p1"]) == 1
    assert "Not quite" in message


def test_only_finalists_with_valid_choices_can_submit_and_there_are_three_tries():
    tour = final_started()
    assert_refused(tour, r3.answer(tour, "p2", "Nova", "Conservatory", "Map", PLAY))
    assert_refused(tour, r3.answer(tour, "p1", "Nobody", "Conservatory", "Map", PLAY))

    for second in range(1, 4):
        tour, _ = r3.answer(tour, "p1", "Theo", "Library", "Key", PLAY + second)
    assert r3.guesses_left(tour, "p1") == 0
    assert_refused(tour, r3.answer(tour, "p1", "Nova", "Conservatory", "Map", PLAY + 5))


def test_timeout_uses_the_best_theory_then_fastest_theory():
    tour = final_started()
    # Both have two matching parts, but p1 gave that better theory first.
    tour, _ = r3.answer(tour, "p0", "Nova", "Conservatory", "Key", PLAY)
    tour, _ = r3.answer(tour, "p1", "Nova", "Conservatory", "Key", PLAY + 2)
    ended, _ = r3.settle(tour, END)
    assert ended["status"] == "round3_results"
    assert ended["round3"]["winner"] == "p0"
    assert ended["round3"]["decided_by"] == "fastest matching theory"


def test_timeout_draw_is_repeatable_with_a_seed_and_settle_is_idempotent():
    tour = final_started()
    first, _ = r3.settle(tour, END, random.Random(4))
    again, _ = r3.settle(first, END, random.Random(4))
    assert first["round3"]["winner"] in ("p0", "p1")
    assert first["round3"]["decided_by"] == "draw"
    assert again == first


def test_answering_does_not_change_the_original_tournament():
    tour = final_started()
    before = copy.deepcopy(tour)
    r3.answer(tour, "p0", "Theo", "Library", "Key", PLAY)
    assert tour == before
