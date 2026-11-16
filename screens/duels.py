"""The list of Round 1 duels, shown during the intro countdown."""

import streamlit as st

import tournament as rules
from screens import common


def show_bracket(tour, me):
    """One line per duel, with the player's own duel marked."""
    for number, (a, b) in enumerate(tour["duels"], start=1):
        player_a = rules.find_player(tour, a)
        player_b = rules.find_player(tour, b)
        marker = "  ← you" if me in (a, b) else ""
        st.markdown(f"**Duel {number}:** {common.player_label(player_a)}  vs  "
                    f"{common.player_label(player_b)}{marker}")
