"""Round 2 placeholder, with a temporary host bridge into the Round 3 finale."""

import time

import streamlit as st

import storage
import tournament as rules
from screens import common


def show(tour, me):
    st.title("Round 2: the duos")
    if me in tour["eliminated"]:
        st.info("You're out, but you can keep watching.")
    st.subheader("Still in the game")
    active = [player for player in tour["players"] if player["id"] not in tour["eliminated"]]
    st.markdown("<div class='mm-lobby-grid'>" + "".join(
        f"<div class='mm-lobby-card'>{common.profile_card(player)}</div>" for player in active
    ) + "</div>", unsafe_allow_html=True)
    st.divider()
    st.info("The Duo Vault Challenge is coming soon.")

    if not rules.is_host(tour, me):
        st.caption("While Round 2 is being built, the host will choose the two finalists for Round 3.")
        return

    names_to_ids = {player["name"]: player["id"] for player in active}
    st.subheader("Temporary bridge to the finale")
    st.caption("Pick Round 2's two survivors so you can test the Final Mansion Mystery now.")
    chosen_names = st.multiselect("Choose exactly two finalists", list(names_to_ids), max_selections=2)
    if st.button("Start Round 3: Final Mansion Mystery", type="primary", disabled=len(chosen_names) != 2):
        _, message = storage.update(
            tour["code"], rules.start_round3, me,
            [names_to_ids[name] for name in chosen_names], time.time(),
        )
        st.toast(message)
        st.rerun()
