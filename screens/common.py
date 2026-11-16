"""Small pieces every screen uses: the title, messages that survive a page reload,
moving between screens, and how a player is shown.

Styling (avatars, colours, animations) will mostly happen here later."""

import streamlit as st

TITLE = "The Missing Mastermind"   # working title, change it here only

# Characters that mean something in Markdown. Player names are typed by players,
# so we escape them; otherwise a name like "**Bob**" or "[click](http://...)" would
# turn into bold text or a link on everyone's screen.
_MARKDOWN_CHARACTERS = "\\`*_{}[]()#+-.!|<>~$"


def apply_theme():
    """The shared purple-and-silver mystery look used by every game screen."""
    st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
      background: radial-gradient(circle at 50% -15%, #633296 0%, #261044 43%, #10071f 100%) !important;
      color: #f8f2ff;
    }
    [data-testid="stHeader"] { background: rgba(16, 7, 31, .72) !important; }
    [data-testid="stToolbar"] { right: 1rem; }
    .block-container { max-width: 1040px; padding-top: 2.8rem; }
    h1, h2, h3, p, li, label, [data-testid="stMarkdownContainer"] { color: #f8f2ff; }
    h1 { color: #e4c5ff !important; font-family: Georgia, 'Times New Roman', serif !important;
      letter-spacing: .035em; text-shadow: 0 0 18px rgba(193, 116, 255, .44); }
    h2, h3 { color: #dbbaff !important; }
    [data-testid="stCaptionContainer"], small { color: #d0bedf !important; }
    /* Forms stay pale so typed answers and names are always easy to read. */
    [data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-baseweb="base-input"] {
      background: #f8f4fc !important; border-color: #d6b7eb !important; color: #1d102a !important;
    }
    input, textarea, [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
      color: #1d102a !important; -webkit-text-fill-color: #1d102a !important; caret-color: #551f78 !important;
    }
    input::placeholder, textarea::placeholder { color: #786881 !important; opacity: 1 !important; }
    input:-webkit-autofill, textarea:-webkit-autofill {
      -webkit-text-fill-color: #1d102a !important;
      -webkit-box-shadow: 0 0 0 1000px #f8f4fc inset !important;
      transition: background-color 9999s ease-in-out 0s;
    }
    div.stButton > button, div.stFormSubmitButton > button {
      background: linear-gradient(135deg, #7c3db1, #b561e8) !important; border: 1px solid #e2b7ff !important;
      color: white !important; box-shadow: 0 4px 18px rgba(90, 30, 139, .35); }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover { filter: brightness(1.15); }
    [data-baseweb="tab-list"] { gap: .4rem; }
    [data-baseweb="tab"] { color: #dac9e8 !important; background: rgba(19, 8, 39, .42); border-radius: 10px 10px 0 0; }
    [data-baseweb="tab"][aria-selected="true"] { color: #fff !important; background: rgba(128, 68, 177, .55); }
    hr { border-color: rgba(220, 184, 255, .32) !important; }
    .mm-wordmark-wrap { margin: .2rem 0 .45rem; text-align: center; }
    .mm-wordmark-kicker { color: #e7e9f1 !important; font-family: Georgia, 'Times New Roman', serif;
      font-size: clamp(.75rem, 2vw, 1.1rem); font-weight: 700; letter-spacing: .28em; line-height: 1;
      text-shadow: 0 1px 0 #535867, 0 3px 8px #08030f; }
    .mm-wordmark { margin-top: .05rem; font-family: Copperplate, 'Copperplate Gothic Light', 'Old English Text MT', Georgia, serif;
      font-size: clamp(2.2rem, 8vw, 4.3rem); font-weight: 900; letter-spacing: .055em; line-height: .95;
      text-align: center; text-transform: uppercase; background: linear-gradient(180deg, #ffffff 4%, #cbd0da 25%, #777c89 48%, #f4f5fc 66%, #878c99 100%);
      -webkit-background-clip: text; background-clip: text; color: transparent;
      -webkit-text-stroke: .35px #eef0f7; text-shadow: 1px 1px 0 #454958, 2px 3px 0 #1b1229, 0 6px 18px rgba(2, 0, 8, .92); }
    .mm-tagline { color: #d7b9ee !important; font-family: Georgia, serif; font-size: 1.1rem; letter-spacing: .08em; text-align: center; }
    </style>
    """, unsafe_allow_html=True)


def show_wordmark():
    """An original metallic mystery title treatment."""
    st.markdown(
        f"<div class='mm-wordmark-wrap'><div class='mm-wordmark-kicker'>THE</div>"
        f"<div class='mm-wordmark'>{TITLE}</div></div>",
        unsafe_allow_html=True,
    )


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
