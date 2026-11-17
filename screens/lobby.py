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

    # Each player owns one small glass card.  The host's remove control lives in
    # that card so it is obvious who will be removed, instead of in a detached row.
    columns = st.columns(4)
    for number, player in enumerate(tour["players"]):
        badges = []
        if player["id"] == tour["host_id"]:
            badges.append("host")
        if player["id"] == me:
            badges.append("you")
        badge_text = " · ".join(badges)
        with columns[number % 4]:
            with st.container(border=True):
                st.markdown(
                    common.profile_card(player) + f"<div class='mm-lobby-badges'>{badge_text}</div>",
                    unsafe_allow_html=True,
                )
                if host and player["id"] != me:
                    key = f"remove_{player['id']}"
                    st.markdown(f"""<style>
                    .st-key-{key} div.stButton > button {{ background:rgba(116,19,42,.72) !important; border:1px solid #ff8592 !important;
                      border-radius:9px !important; box-shadow:none !important; color:#ffd8dd !important; font-family:Cinzel, Georgia, serif !important;
                      font-size:1.1rem !important; line-height:1 !important; min-height:30px !important; padding:.12rem .52rem !important; }}
                    .st-key-{key} div.stButton > button:hover {{ background:#b42f4a !important; color:#fff !important; }}
                    </style>""", unsafe_allow_html=True)
                    remove = st.button("×", key=key, help=f"Remove {player['name']}")
                    if remove:
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
