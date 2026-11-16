"""The first screen: create a tournament, or join one with a code."""

import streamlit as st

import storage
import tournament as rules
from screens import common


def show():
    st.title(f"🗝️ {common.TITLE}")
    st.write("Eight guests. One mansion. Only one will solve the last clue.")

    create_tab, join_tab = st.tabs(["Create a tournament", "Join with a code"])
    with create_tab:
        show_create()
    with join_tab:
        show_join()


def show_create():
    with st.form("create"):
        name = st.text_input("Your name", max_chars=rules.MAX_NAME_LENGTH)
        st.caption(f"You'll be the host and one of the {rules.MAX_PLAYERS} players.")
        submitted = st.form_submit_button("Create tournament", type="primary")
    if submitted:
        tour, host_id, message = storage.create(name)
        if tour is None:
            st.error(message)
        else:
            common.flash("success", message)
            common.go_to(tour["code"], host_id)


def show_join(prefilled_code=""):
    if prefilled_code:
        st.subheader(f"Join tournament {prefilled_code}")
    with st.form("join"):
        code = st.text_input("Code", value=prefilled_code, max_chars=storage.CODE_LENGTH,
                             placeholder="e.g. KQZT")
        name = st.text_input("Your name", max_chars=rules.MAX_NAME_LENGTH)
        submitted = st.form_submit_button("Join", type="primary")
    if submitted:
        player_id = storage.new_player_id()
        tour, message = storage.update(code, rules.join, player_id, name)
        if tour is not None and rules.find_player(tour, player_id):
            common.flash("success", message)
            common.go_to(tour["code"], player_id)
        else:
            st.error(message)
