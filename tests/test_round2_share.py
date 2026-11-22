"""Tests for sharing clues in Round 2: each player opens their own card and then
decides when to send it to their teammate's phone."""

import random

import round2 as r2

NOW = 1_000.0
PLAYERS = ["a", "b", "c", "d"]


def playing():
    tour = {"status": "round2", "players": [{"id": pid, "name": pid.upper()} for pid in PLAYERS],
            "eliminated": [], "round2": r2.new_round(PLAYERS, NOW, random.Random(1))}
    return tour


def duo_of(tour, pid):
    duo_id = tour["round2"]["players"][pid]["duo_id"]
    mate = next(p for p in tour["round2"]["duos"][duo_id]["players"] if p != pid)
    return duo_id, mate


def test_your_teammate_sees_nothing_until_you_send_your_clue():
    tour = playing()
    _, mate = duo_of(tour, "a")
    assert r2.player_view(tour, mate)["teammate_card"] is None
    assert r2.player_view(tour, "a")["card_shared"] is False


def test_sending_your_clue_shows_it_on_your_teammates_phone_only():
    tour = playing()
    _, mate = duo_of(tour, "a")
    tour, message = r2.share_clue(tour, "a", NOW + 5)
    assert message == "Clue sent to your teammate!"
    assert r2.player_view(tour, mate)["teammate_card"] == r2.player_view(tour, "a")["card"]
    assert r2.player_view(tour, "a")["card_shared"] is True
    others = [p for p in PLAYERS if p not in ("a", mate)]
    assert all(r2.player_view(tour, p)["teammate_card"] is None for p in others)   # the other duo sees nothing


def test_both_teammates_can_send_and_then_each_has_both_clues():
    tour = playing()
    _, mate = duo_of(tour, "a")
    tour, _ = r2.share_clue(tour, "a", NOW + 1)
    tour, _ = r2.share_clue(tour, mate, NOW + 2)
    mine, theirs = r2.player_view(tour, "a"), r2.player_view(tour, mate)
    assert {mine["card"], mine["teammate_card"]} == {r2.CARD_A, r2.CARD_B}
    assert {theirs["card"], theirs["teammate_card"]} == {r2.CARD_A, r2.CARD_B}


def test_only_once_and_only_for_players_in_round2():
    tour, _ = r2.share_clue(playing(), "a", NOW + 1)
    assert r2.share_clue(tour, "a", NOW + 2)[1] == "You've already sent your clue."
    assert r2.share_clue(tour, "zz", NOW + 2)[1] == "You're not playing in Round 2."


def test_not_before_the_challenge_starts_or_after_it_is_decided():
    waiting = playing()
    waiting["round2"] = r2.new_round(PLAYERS, NOW, random.Random(1), show_intro=True)
    assert r2.share_clue(waiting, "a", NOW)[1] == "The Round 2 challenge hasn't started yet."
    done = playing()
    done["round2"]["winner"] = "duo_1"
    assert r2.share_clue(done, "a", NOW)[1] == "Round 2 is not active."


def test_sharing_does_not_change_the_original_game():
    tour = playing()
    r2.share_clue(tour, "a", NOW)
    assert "shared_at" not in tour["round2"]["players"]["a"]
