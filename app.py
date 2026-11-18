"""The Missing Mastermind: start the app with

    uv run streamlit run app.py

Every player opens the app on their own phone. Who you are is kept in the page's
address (the ?code=...&me=... part), so refreshing the page keeps you in the game.

This file only decides WHICH screen to show. The rules live in tournament.py,
the shared saving in storage.py, and the screens in screens/.
"""

import time

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

import fan_vote
import round1
import storage
import tournament as rules
from screens import common, home, lobby
from screens import round1 as round1_screen
from screens import round2 as round2_screen
from screens import round3 as round3_screen

st.set_page_config(page_title=common.TITLE, page_icon="🗝️", layout="centered")
common.apply_theme()

# On a laptop, storage.py uses the local SQLite file.  On Streamlit Community
# Cloud, these two values are added in the app's Secrets settings so every
# visitor uses the same online Supabase database.  Secrets are deliberately
# not stored in this GitHub repository.
def _supabase_secrets():
    """The [supabase] secrets, or None when this computer has no secrets file
    (then we simply use the local SQLite file instead of crashing)."""
    try:
        return st.secrets["supabase"] if "supabase" in st.secrets else None
    except StreamlitSecretNotFoundError:
        return None


supabase = _supabase_secrets()
if supabase:
    if "key" not in supabase:
        st.error("Add key to the [supabase] secrets.")
        st.stop()
    storage.configure_supabase(
        supabase["url"],
        supabase["key"],
    )

code = st.query_params.get("code")
me = st.query_params.get("me")

common.show_flash()

if not code:
    home.show()
    st.stop()

tour = storage.load(code)

if tour is None:
    st.error(f"There's no tournament with the code {storage.normalise_code(code)}.")
    if st.button("Back to the start"):
        common.go_home()
    st.stop()

if not rules.find_player(tour, me):
    # Someone who opened a join link, or a player who left or was removed.
    if me:
        st.warning("You're not in this tournament any more.")
    if tour["status"] == "lobby":
        home.show_join(prefilled_code=tour["code"])
    else:
        st.error("This tournament has already started, so you can't join it.")
        if st.button("Back to the start"):
            common.go_home()
    st.stop()

def _screen_id(tour, me, now):
    """Which screen this player should be looking at (e.g. 'round1:playing:2')."""
    status = tour["status"]
    try:
        if status == "round1":
            settled, _ = round1.settle(tour, now)        # a timer that just ran out counts already
            if settled["status"] != "round1":
                return settled["status"]
            return f"round1:{round1.phase(settled, me, now)}:{round1.game_number(settled, me)}"
        if status == "round3":
            return "round3:" + ("story" if tour["round3"].get("starts_at") is None else "mystery")
        if status in ("round3_results", "finished"):
            return "final:" + ("vote" if fan_vote.is_open(tour, now) else "stage")
    except Exception:
        pass
    return status


# The whole screen lives in one frame. When the player moves to another screen
# (next game, next round, the vote, the final), the frame is wiped first, so
# nothing from the previous screen can stay behind on the page. Taps that stay
# on the same screen don't wipe anything, so there's no flicker while playing.
page = st.empty()
screen = _screen_id(tour, me, time.time())
if st.session_state.get("mm_screen") != screen:
    page.empty()
    st.session_state["mm_screen"] = screen

with page.container():
    if tour["status"] == "lobby":
        lobby.show(tour["code"], me)
    elif tour["status"] in ("round1", "round1_results"):
        round1_screen.show(tour["code"], me)
    elif tour["status"] in ("round2", "final"):
        round2_screen.show(tour["code"], me)
    elif tour["status"] in ("round3", "round3_results", "finished"):
        round3_screen.show(tour["code"], me)
    else:
        st.error("This tournament is in an unknown game phase.")
