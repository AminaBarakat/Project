"""One shared, very recent copy of each tournament for the parts of the screen that
refresh themselves every second or two (race strip, ready check, waiting room,
crowd bar, reactions).

Why: those parts used to ask the database on every phone, every second. While a
phone waits for the database, Streamlit is busy, and a tap that lands in that
moment can get lost or arrive late. Now all phones in a game share one reading
that is at most a second old, so those refreshes are instant almost every time.

Only for showing things. Anything that changes the game (an answer, a vote, a
timer running out) still reads and writes the database directly, through
storage.update. A full page draw calls forget(), so the next refresh starts from
data at least as new as what the page itself showed.
"""

import streamlit as st

import storage


@st.cache_data(ttl=1.0, show_spinner=False, max_entries=64)
def _peek(code):
    return storage.load(code)


def peek(code):
    """The tournament as it was at most a second ago (shared by all phones)."""
    return _peek(storage.normalise_code(code))


def forget():
    """Drop the shared copy, so the next peek reads the database again."""
    _peek.clear()
