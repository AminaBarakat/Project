"""After the host starts: the random Round 1 duels. The rounds themselves come later."""

import streamlit as st

import tournament as rules
from screens import common


def show(tour, me):
    st.title("Round 1: the duels")

    opponent = rules.opponent_of(tour, me)
    if opponent:
        me_player = rules.find_player(tour, me)
        st.markdown(f"### {common.player_label(me_player)}  ⚔️  {common.player_label(opponent)}")
        st.caption("This is your duel.")

    st.divider()
    for number, (a, b) in enumerate(tour["duels"], start=1):
        player_a = rules.find_player(tour, a)
        player_b = rules.find_player(tour, b)
        marker = "  ← you" if me in (a, b) else ""
        st.markdown(f"**Duel {number}:** {common.player_label(player_a)}  vs  "
                    f"{common.player_label(player_b)}{marker}")

    st.divider()
    st.info("The Round 1 challenges are coming soon.")
