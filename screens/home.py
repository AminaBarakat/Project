"""The first screen: create a tournament, or join one with a code."""

import streamlit as st

import storage
import tournament as rules
from screens import common


def show():
    common.show_wordmark()
    st.markdown("<div class='mm-tagline'>EIGHT GUESTS · ONE MANSION · ONE LAST CLUE</div>", unsafe_allow_html=True)
    st.divider()

    create_tab, join_tab = st.tabs(["Create a tournament", "Join with a code"])
    with create_tab:
        show_create()
    with join_tab:
        show_join()


def show_create():
    appearance = common.avatar_picker("create_avatar")
    name = st.text_input("Your name", key="create_name", max_chars=rules.MAX_NAME_LENGTH)
    st.caption(f"You'll be the host and one of the {rules.MAX_PLAYERS} players.")
    submitted = st.button("Create tournament", type="primary", key="create_tournament")
    if submitted:
        tour, host_id, message = storage.create(name, appearance=appearance)
        if tour is None:
            st.error(message)
        else:
            common.flash("success", message)
            common.go_to(tour["code"], host_id)


def show_join(prefilled_code=""):
    if prefilled_code:
        st.subheader(f"Join tournament {prefilled_code}")
    code = st.text_input("Code", value=prefilled_code, key="join_code", max_chars=storage.CODE_LENGTH,
                         placeholder="e.g. KQZT")
    existing = storage.load(code) if len(code.strip()) == storage.CODE_LENGTH else None
    occupied = [player.get("appearance") for player in existing.get("players", [])] if existing else []
    appearance = common.avatar_picker("join_avatar", occupied)
    name = st.text_input("Your name", key="join_name", max_chars=rules.MAX_NAME_LENGTH)
    submitted = st.button("Join tournament", type="primary", key="join_tournament")
    if submitted:
        player_id = storage.new_player_id()
        tour, message = storage.update(code, rules.join, player_id, name, appearance)
        if tour is not None and rules.find_player(tour, player_id):
            common.flash("success", message)
            common.go_to(tour["code"], player_id)
        else:
            st.error(message)
