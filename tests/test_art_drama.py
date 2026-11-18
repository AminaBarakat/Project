"""Tests for the Round 1 'drama' drawings in screens/art.py: the VS moment, the
duel race strip, the stamps, the last-10-seconds pressure and the results reveal.

The most important thing to check is safety: player names are typed by players,
so they must always be escaped before going into our HTML."""

import re

from screens import art

PIC = "data:image/png;base64,AAAA"
SNEAKY = '<img src=x onerror="alert(1)">'


def visible_text(page):
    """Only the words a player would see: no styles, no tags."""
    return re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", " ", page, flags=re.S))


def racer(name, progress=1.5, status="playing"):
    return {"name": name, "picture": PIC, "progress": progress, "status": status}


def test_vs_intro_escapes_both_names():
    page = art.vs_intro((SNEAKY, PIC), ("<b>Bob</b>", PIC))
    assert SNEAKY not in page and "<b>Bob</b>" not in page
    assert "&lt;b&gt;Bob&lt;/b&gt;" in page
    assert "YOU" in page and "OPPONENT" in page and ">VS<" in page


def test_duel_race_escapes_the_opponent_and_says_nothing_about_answers():
    page = art.duel_race(racer("Marta"), racer(SNEAKY))
    assert SNEAKY not in page
    assert "game 2 of 4" in page
    for word in ("right", "wrong", "correct"):
        assert word not in visible_text(page).lower()


def test_duel_race_shows_when_the_opponent_finished_or_left():
    assert "finished all 4!" in art.duel_race(racer("Marta"), racer("Coucou", 4, "finished"))
    assert "left the game" in art.duel_race(racer("Marta"), racer("Coucou", 2, "left"))


def test_duel_race_bar_never_goes_past_the_end():
    page = art.duel_race(racer("Marta", 9), racer("Coucou", 0))
    assert "width:100.0%" in page and "width:0.0%" in page


def test_stamps():
    assert "LOCKED IN" in art.stamp("LOCKED IN")
    assert "pointer-events: none" in art.stamp("TIME'S UP", good=False)   # taps go through it


def test_countdown_pressure_starts_ten_seconds_before_the_end():
    # 45 s left: the red timer, red edges and trembling lock start in 35 s.
    page = art.countdown("g1", 45, 60)
    assert "mm-go-red-text .3s 35s" in page and "mm-tremble .35s linear 35s" in page
    # Only 6 s left: the pressure is on straight away.
    assert "mm-go-red-text .3s 0s" in art.countdown("g2", 6, 60)


def test_reveal_card_uses_our_detective_terms_and_escapes_names():
    page = art.reveal_card(1, (SNEAKY, PIC), ("Coucou", PIC), "right", mine=True, delay=1.0)
    assert SNEAKY not in page
    assert "ON THE CASE" in page and "OFF THE CASE" in page
    assert "ESCAPE" not in page.upper().replace("ESCAPE ROUTE", "") and "CAUGHT" not in page.upper()
    assert "YOUR CASE" in page and "--d:1.00s" in page


def test_reveal_card_puts_the_winner_where_they_were_drawn():
    page = art.reveal_card(2, ("Ana", PIC), ("Bruno", PIC), "right", mine=False, delay=None)
    ana, bruno = page.index("Ana"), page.index("Bruno")
    assert page.rfind("mm-rv-lose", 0, ana) > page.rfind("mm-rv-win", 0, ana)     # Ana lost
    assert page.rfind("mm-rv-win", 0, bruno) > page.rfind("mm-rv-lose", 0, bruno)  # Bruno won
    assert "mm-rv-static" in page and "--d:" not in page                           # no animation


def test_reveal_timing_and_the_after_reveal_container():
    assert art.reveal_seconds(4) > 4 * art.REVEAL_STEP
    assert art.after_reveal_style("box", 0) == ""                     # reveal over: just show it
    assert "mm-after .6s ease-out 2.50s" in art.after_reveal_style("box", 2.5)
