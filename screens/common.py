"""Small pieces every screen uses: the title, messages that survive a page reload,
moving between screens, and how a player is shown.

Styling (avatars, colours, animations) will mostly happen here later."""

import base64
import html
from functools import lru_cache
from pathlib import Path

import streamlit as st

TITLE = "The Missing Mastermind"   # working title, change it here only
AVATARS = {
    "girl": ("Ivy · classic", "assets/detective-girl.png"),
    "boy": ("Theo · classic", "assets/detective-boy.png"),
    "girl_violet": ("Ivy · violet", "assets/detective-girl-violet.png"),
    "boy_teal": ("Theo · teal", "assets/detective-boy-teal.png"),
    "girl_emerald": ("Ivy · emerald", "assets/detective-girl-emerald.png"),
    "girl_ruby": ("Ivy · ruby", "assets/detective-girl-ruby.png"),
    "boy_royal": ("Theo · royal", "assets/detective-boy-royal.png"),
    "boy_amber": ("Theo · amber", "assets/detective-boy-amber.png"),
}

# Characters that mean something in Markdown. Player names are typed by players,
# so we escape them; otherwise a name like "**Bob**" or "[click](http://...)" would
# turn into bold text or a link on everyone's screen.
_MARKDOWN_CHARACTERS = "\\`*_{}[]()#+-.!|<>~$"


def apply_theme():
    """The shared purple-and-silver mystery look used by every game screen."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800;900&display=swap');
    html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
      background: radial-gradient(circle at 50% -15%, #633296 0%, #261044 43%, #10071f 100%) !important;
      color: #f8f2ff;
    }
    [data-testid="stHeader"] { background: rgba(16, 7, 31, .72) !important; }
    [data-testid="stToolbar"] { right: 1rem; }
    .block-container { max-width: 1040px; padding-top: 2.8rem; }
    h1, h2, h3, p, li, label, [data-testid="stMarkdownContainer"] { color: #f8f2ff; }
    h1 { color: #d9dce5 !important; font-family: Cinzel, Georgia, 'Times New Roman', serif !important;
      letter-spacing: .035em; text-shadow: 0 1px 0 #ffffff66, 0 0 18px rgba(193, 116, 255, .44); }
    h2, h3 { color: #dbbaff !important; }
    [data-testid="stCaptionContainer"], small { color: #d0bedf !important; }
    /* Dark glass fields keep every typed answer bright and readable. */
    [data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-baseweb="base-input"], [data-baseweb="textarea"] {
      background: rgba(40, 17, 79, .92) !important; border-color: #b982e4 !important; color: #f8f2ff !important;
    }
    input, textarea, [data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
    [data-baseweb="select"] input, [data-baseweb="select"] div, [data-baseweb="select"] span {
      color: #f8f2ff !important; -webkit-text-fill-color: #f8f2ff !important; caret-color: #ffffff !important;
    }
    input::placeholder, textarea::placeholder { color: #d8c6e8 !important; opacity: 1 !important; }
    input:-webkit-autofill, textarea:-webkit-autofill {
      -webkit-text-fill-color: #f8f2ff !important;
      -webkit-box-shadow: 0 0 0 1000px #28114f inset !important;
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
    /* Shared announcements use a luminous glass panel rather than Streamlit gray. */
    [data-testid="stAlert"] { background: linear-gradient(105deg, rgba(104, 48, 173, .82), rgba(31, 92, 166, .74)) !important;
      border: 1px solid rgba(177, 234, 255, .72) !important; border-radius: 15px !important;
      box-shadow: 0 0 24px rgba(172, 92, 255, .30), inset 0 0 28px rgba(170, 224, 255, .10) !important; }
    [data-testid="stAlert"] * { color: #fcf8ff !important; }
    .mm-wordmark-wrap { margin: .2rem 0 .45rem; text-align: center; overflow: visible; }
    .mm-wordmark { margin-top: .05rem; font-family: Cinzel, Georgia, serif;
      font-size: clamp(1.7rem, 5.6vw, 4.15rem); font-weight: 900; letter-spacing: .045em; line-height: 1.06;
      text-align: center; text-transform: uppercase; white-space: nowrap; background: linear-gradient(180deg, #ffffff 2%, #e4bcff 26%, #87f1ff 56%, #dca7ff 82%, #ffffff 100%);
      -webkit-background-clip: text; background-clip: text; color: transparent;
      -webkit-text-stroke: .35px #f7eaff; text-shadow: 0 0 5px rgba(255,255,255,.95), 0 0 18px rgba(205,116,255,.95), 0 0 38px rgba(89,220,255,.68), 2px 3px 0 #271247; }
    .mm-tagline { color: #d7b9ee !important; font-family: Georgia, serif; font-size: 1.1rem; letter-spacing: .08em; text-align: center; }
    .mm-avatar-help { color: #d9c2ec !important; margin: .15rem 0 .65rem; }
    .mm-profile { text-align: center; min-width: 120px; }
    .mm-profile-photo { position: relative; display: grid; place-items: center; margin: 0 auto .35rem; width: 112px; height: 112px; border-radius: 50%;
      background: linear-gradient(145deg, #ffffff, #aeb4c0 42%, #fbfdff 66%, #777f8b); overflow:hidden; padding: 4px; box-shadow: 0 4px 16px rgba(0,0,0,.4); }
    .mm-profile-photo img { width: 100%; height: 100%; object-fit: contain; object-position: center center; border-radius: 50%; background: #291345; }
    .mm-profile-name { font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-weight: 750; color: #f8f2ff !important; font-size: .95rem; overflow-wrap: anywhere; }
    .mm-profile-status { display:flex; align-items:center; justify-content:center; gap:.25rem; margin-top: .15rem; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-weight: 800; letter-spacing: .02em; font-size: .78rem; }
    .mm-passed { color: #83e6ad !important; text-shadow: 0 1px 0 #1a5c39, 0 0 9px rgba(89, 221, 137, .45); }
    .mm-eliminated { color: #ff7780 !important; text-shadow: 0 1px 0 #81212b, 0 0 9px rgba(244, 77, 88, .45); }
    .mm-cross, .mm-check { align-items:center; border-radius:50%; display:flex; height:100%; justify-content:center; left:0; position:absolute; top:0; width:100%; }
    .mm-cross { color: #ff6672; font-size: 5rem; line-height: 1; font-family: Arial, sans-serif; font-weight: 300; text-shadow: 0 0 12px #6e1420; transform: rotate(-7deg); }
    .mm-check { color:#82efaf; font-family:Arial, sans-serif; font-size:4rem; font-weight:800; text-shadow:0 0 12px #195c36; }
    .mm-duel { display: flex; justify-content: center; align-items: center; gap: clamp(.7rem, 4vw, 2rem); margin: 1.4rem auto 1rem; padding: .9rem; max-width: 560px; overflow:hidden;
      border: 1px solid rgba(194,199,212,.24); border-radius: 18px; background: rgba(38,16,68,.42); }
    .mm-duel-vs { color: #c2c7d4; font-family: Cinzel, Georgia, serif; font-weight: 900; font-size: 1.2rem; }
    .mm-results-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.1rem; margin: 1.25rem 0; }
    .mm-result-duel { border: 1px solid rgba(194,199,212,.22); border-radius: 16px; padding: .8rem .4rem; background: rgba(38,16,68,.38); }
    .mm-result-duel-title { color: #f8f2ff !important; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: .85rem; font-weight: 800; letter-spacing:.02em; text-align:center; margin-bottom:.6rem; }
    .mm-result-pair { display:flex; justify-content:center; align-items:flex-start; gap:.45rem; }
    .mm-result-pair .mm-profile { flex: 1 1 0; min-width: 0; }
    .mm-result-pair .mm-profile-photo { width:76px; height:76px; }
    .mm-result-pair .mm-cross { font-size:3.7rem; }
    .mm-result-pair .mm-check { font-size:2.85rem; }
    .mm-result-vs { align-self:center; color:#c2c7d4; font-weight:900; }
    .mm-lobby-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:1rem; align-items:stretch; margin:1rem 0; }
    .mm-lobby-card { background:rgba(38,16,68,.44); border:1px solid rgba(194,199,212,.24); border-radius:16px; min-height:180px; padding:.85rem .45rem .6rem; }
    .mm-lobby-badges { color:#d6b7eb; font-size:.78rem; margin-top:.35rem; text-align:center; }
    .mm-remove-button button { background:rgba(116, 19, 42, .72) !important; border:1px solid #ff8592 !important; border-radius:9px !important;
      box-shadow:none !important; color:#ffd8dd !important; font-family:Cinzel, Georgia, serif !important; font-size:1.1rem !important;
      line-height:1 !important; min-height:30px !important; padding:.12rem .52rem !important; }
    .mm-remove-button button:hover { background:#b42f4a !important; color:#fff !important; }
    @media (max-width: 560px) { .mm-duel { gap:.45rem; padding:.7rem .35rem; } .mm-profile-photo { width:94px; height:94px; } .mm-results-grid { grid-template-columns:1fr 1fr; gap:.65rem; } }
    </style>
    """, unsafe_allow_html=True)


def show_wordmark():
    """An original metallic mystery title treatment."""
    st.markdown(
        f"<div class='mm-wordmark-wrap'><div class='mm-wordmark'>{TITLE}</div></div>",
        unsafe_allow_html=True,
    )


def avatar_picker(key, unavailable=()):
    """Clickable glass portrait cards; occupied portraits are shown as unavailable."""
    choice_key = f"{key}_choice"
    unavailable = set(unavailable)
    if choice_key not in st.session_state or st.session_state[choice_key] in unavailable:
        st.session_state[choice_key] = next((option for option in AVATARS if option not in unavailable), "girl")
    st.markdown("<div class='mm-avatar-help'>Choose your detective — each portrait can be claimed by one player only.</div>", unsafe_allow_html=True)
    options = list(AVATARS)
    for start in range(0, len(options), 2):
        columns = st.columns(2)
        for column, option in zip(columns, options[start:start + 2]):
            _, path = AVATARS[option]
            widget_key = f"{key}_{option}"
            selected = st.session_state[choice_key] == option
            taken = option in unavailable
            selector = f".st-key-{widget_key} div.stButton > button"
            selected_style = "outline:3px solid #9be4ff !important; outline-offset:2px; box-shadow:0 0 24px rgba(155,228,255,.58) !important;" if selected else ""
            st.markdown(f"""<style>
            {selector} {{ background: linear-gradient(rgba(30,14,58,.12), rgba(30,14,58,.55)), url('{avatar_data_url(path)}') center / auto 158px no-repeat, rgba(255,255,255,.08) !important;
              border:1px solid rgba(226,183,255,.72) !important; border-radius:18px !important; min-height:190px; padding:158px .3rem .4rem !important;
              transition:transform .15s ease, box-shadow .15s ease; {selected_style} {'opacity:.28 !important; filter:grayscale(1);' if taken else ''} }}
            {selector}:hover {{ transform:translateY(-4px); box-shadow:0 0 22px rgba(203,151,255,.55) !important; }}
            {selector} p {{ color:transparent !important; font-size:0 !important; }}
            {selector}::after {{ content:'✓'; color:#fff; font-size:1.55rem; opacity:{'1' if selected else '0'}; position:absolute; right:.65rem; top:.4rem; text-shadow:0 0 8px #62d4ff; }}
            </style>""", unsafe_allow_html=True)
            with column:
                if st.button(" ", key=widget_key, width="stretch", disabled=taken):
                    st.session_state[choice_key] = option
                    st.rerun()
    return st.session_state[choice_key]


@lru_cache(maxsize=None)
def avatar_data_url(path):
    """A local avatar image embedded safely in the small HTML profile cards."""
    raw = Path(path).read_bytes()
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def profile_card(player, status=None):
    """A player portrait for a duel or a result; names are HTML-escaped."""
    appearance = player.get("appearance") or "girl"
    _, path = AVATARS.get(appearance, AVATARS["girl"])
    name = html.escape(player["name"])
    overlay = "<span class='mm-cross'>×</span>" if status == "eliminated" else "<span class='mm-check'>✓</span>" if status == "passed" else ""
    label = "Passed" if status == "passed" else "Eliminated" if status == "eliminated" else ""
    status_html = f"<div class='mm-profile-status mm-{status}'>{label}</div>" if status else ""
    return (f"<div class='mm-profile'><div class='mm-profile-photo'><img src='{avatar_data_url(path)}' alt='' />{overlay}</div>"
            f"<div class='mm-profile-name'>{name}</div>{status_html}</div>")


def duel_card(left, right):
    """Two centred character cards for the 'who is your opponent?' moment."""
    return f"<div class='mm-duel'>{profile_card(left)}<div class='mm-duel-vs'>VS</div>{profile_card(right)}</div>"


def result_duel_card(number, winner, loser, how=""):
    """Compact pair of outcome portraits for the results wall."""
    return (f"<div class='mm-result-duel'><div class='mm-result-duel-title'>Winner: {html.escape(winner['name'])}</div>"
            f"<div class='mm-result-pair'>{profile_card(winner, 'passed')}<div class='mm-result-vs'>VS</div>"
            f"{profile_card(loser, 'eliminated')}</div></div>")


def safe(text):
    """Text typed by a player, made safe to put inside st.markdown."""
    return "".join("\\" + ch if ch in _MARKDOWN_CHARACTERS else ch for ch in text)


def player_label(player):
    """A player's name, with no avatar-choice code leaking into game text."""
    return safe(player["name"])


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
