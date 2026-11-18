"""The list of Round 1 duels, shown during the intro countdown."""

import streamlit as st

import tournament as rules
from screens import common


def show_bracket(tour, me):
    """Centred detective cards for the Round 1 draw."""
    st.markdown("### Who's got you in their sights?")
    for number, (a, b) in enumerate(tour["duels"], start=1):
        player_a = rules.find_player(tour, a)
        player_b = rules.find_player(tour, b)
        marker = " · YOUR CASE" if me in (a, b) else ""
        st.markdown(f"<div class='mm-result-duel-title'>DUEL {number}{marker}</div>"
                    + common.duel_card(player_a, player_b), unsafe_allow_html=True)
