"""Round 2 placeholder: shows who is still in. The duo round comes later."""

import streamlit as st

import tournament as rules
from screens import common


def show(tour, me):
    st.title("Round 2: the duos")
    if me in tour["eliminated"]:
        st.info("You're out, but you can keep watching.")
    st.subheader("Still in the game")
    for player in tour["players"]:
        if player["id"] not in tour["eliminated"]:
            st.markdown(common.player_label(player))
    st.divider()
    st.info("Round 2 is coming soon.")
