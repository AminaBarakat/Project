"""The Missing Mastermind: start the app with

    uv run streamlit run app.py

Every player opens the app on their own phone. Who you are is kept in the page's
address (the ?code=...&me=... part), so refreshing the page keeps you in the game.

This file only decides WHICH screen to show. The rules live in tournament.py,
the shared saving in storage.py, and the screens in screens/.
"""

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

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
    storage.configure_supabase(supabase["url"], supabase["key"])

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

if tour["status"] == "lobby":
    lobby.show(tour["code"], me)
elif tour["status"] in ("round1", "round1_results"):
    round1_screen.show(tour["code"], me)
elif tour["status"] in ("round3", "round3_results", "finished"):
    round3_screen.show(tour["code"], me)
else:
    round2_screen.show(tour, me)
