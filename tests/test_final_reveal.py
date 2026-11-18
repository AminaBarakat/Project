"""Tests for the final spotlight (screens/round3.py) and the small avatars
(screens/avatars.py). These import screen code, so Streamlit must be installed
(it is, in the project's environment: `uv run pytest`)."""

import pytest

from screens import avatars, common
from screens import round3 as screen


def test_the_spotlight_ends_pointing_straight_down_at_place_one():
    angles, times = screen._spotlight_times()
    assert angles[-1] == 0
    swings = [abs(a) for a in angles[1:-1]]
    assert swings == sorted(swings, reverse=True)       # each sweep smaller than the one before
    assert max(swings) >= 25                            # the first sweeps reach the crowd at the sides
    assert times == sorted(times)


def test_the_champion_is_revealed_first_then_places_two_and_three():
    land, others, end = screen._stage_timeline()
    assert screen.SPOT_ON < land < others < end
    assert 3 < land < 8                                 # dramatic, but not boring


def test_long_after_the_reveal_everything_is_simply_shown():
    css = screen._stage_css(None)
    assert ".r3-cover { display: none; }" in css and "r3-spot-sweep" not in css
    assert "r3-spot-sweep" in screen._stage_css(1.0)


def test_small_avatars_are_much_smaller_than_the_originals():
    for appearance, (_, path) in common.AVATARS.items():
        small = avatars.picture({"appearance": appearance}, 96)
        assert small.startswith("data:image/png;base64,")
        assert len(small) < 80_000, appearance          # a few dozen KB at most, not megabytes


def test_unknown_or_missing_appearance_falls_back_to_the_classic_detective():
    assert avatars.picture({"appearance": "nope"}, 96) == avatars.picture({"appearance": "girl"}, 96)
    assert avatars.picture({}, 96) == avatars.picture({"appearance": "girl"}, 96)
