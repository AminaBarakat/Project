"""Small pieces every screen uses: the title, messages that survive a page reload,
moving between screens, and how a player is shown.

Styling (avatars, colours, animations) will mostly happen here later."""

import streamlit as st

TITLE = "The Missing Mastermind"   # working title, change it here only

# Characters that mean something in Markdown. Player names are typed by players,
# so we escape them; otherwise a name like "**Bob**" or "[click](http://...)" would
# turn into bold text or a link on everyone's screen.
_MARKDOWN_CHARACTERS = "\\`*_{}[]()#+-.!|<>~$"


def safe(text):
    """Text typed by a player, made safe to put inside st.markdown."""
    return "".join("\\" + ch if ch in _MARKDOWN_CHARACTERS else ch for ch in text)


def avatar(player):
    """What represents the player next to their name.

    For now everyone gets the same placeholder. When we do styling, the player's
    "appearance" (chosen at join time) decides what is shown here."""
    return player.get("appearance") or "🕵️"


def player_label(player):
    """'🕵️ Ana' ready for st.markdown."""
    return f"{avatar(player)} {safe(player['name'])}"


def flash(kind, message):
    """Shows `message` at the top of the next screen. kind: 'success', 'info', 'error'."""
    st.session_state["flash"] = (kind, message)


def show_flash():
    if "flash" in st.session_state:
        kind, message = st.session_state.pop("flash")
        getattr(st, kind)(message)


def go_to(code, me):
    """Remember who this phone is (in the page address) and show their screen."""
    st.query_params.clear()
    st.query_params.update({"code": code, "me": me})
    st.rerun()


def go_home():
    st.query_params.clear()
    st.rerun()


def join_link(code):
    """A link that opens the app with the code already filled in, or None if
    Streamlit can't tell us the app's address."""
    url = getattr(st.context, "url", None)
    if not url:
        return None
    base = url.split("?")[0]
    return f"{base}?code={code}"
