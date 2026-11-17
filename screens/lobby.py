"""The lobby: everyone waits here until the host starts the tournament.

The player list refreshes itself every 2 seconds (st.fragment with run_every), so
when someone joins on their phone, everyone else sees them appear shortly after."""

import streamlit as st

import storage
import tournament as rules
from screens import common

REFRESH = "2s"


def show(code, me):
    common.show_wordmark()
    st.markdown("Join code")
    st.markdown(f"# `{code}`")
    link = common.join_link(code)
    if link:
        st.caption("Or send this link:")
        st.code(link, language=None)
    st.caption("Share the code or the link above, **not** your own page address: "
               "your address is your seat in the game.")
    st.divider()
    live_players(code, me)


@st.fragment(run_every=REFRESH)
def live_players(code, me):
    common.show_flash()
    tour = storage.load(code)
    # Something changed that needs a different screen: the game started,
    # the tournament vanished, or this player was removed.
    if tour is None or tour["status"] != "lobby" or not rules.find_player(tour, me):
        st.rerun(scope="app")

    host = rules.is_host(tour, me)
    count = len(tour["players"])
    st.subheader(f"Players ({count}/{rules.MAX_PLAYERS})")

    for player in tour["players"]:
        left, right = st.columns([4, 1], vertical_alignment="center")
        label = common.profile_card(player)
        if player["id"] == tour["host_id"]:
            label += "<div style='text-align:center; color:#d6b7eb'>host</div>"
        if player["id"] == me:
            label += "<div style='text-align:center; color:#d6b7eb'>you</div>"
        left.markdown(label, unsafe_allow_html=True)
        if host and player["id"] != me:
            if right.button("Remove", key=f"remove_{player['id']}"):
                _, message = storage.update(code, rules.remove_player, me, player["id"])
                common.flash("info", message)
                st.rerun(scope="fragment")

    for _ in range(rules.MAX_PLAYERS - count):
        st.markdown("<span style='opacity:0.4'>… waiting for a player</span>", unsafe_allow_html=True)

    st.divider()
    if host:
        ready = count == rules.MAX_PLAYERS
        if not ready:
            st.caption(f"The tournament starts when all {rules.MAX_PLAYERS} players have joined.")
        if st.button("Start the tournament", type="primary", disabled=not ready):
            _, message = storage.update(code, rules.start, me)
            common.flash("success", message)
            st.rerun(scope="app")
    else:
        st.info("Waiting for the host to start…")
        if st.button("Leave"):
            _, message = storage.update(code, rules.leave, me)
            common.flash("info", message)
            common.go_home()
