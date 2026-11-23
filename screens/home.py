"""The first screen: host a tournament, or join one with a code.

Layout (the same on phone and laptop, just narrower on a phone):
the game's title, a tagline and three chips that sum up the night, then a pill
switch (Host a game | Join with a code) above one glass card with the form.
"""

import streamlit as st

import storage
import tournament as rules
from screens import common

STYLE = """<style>
.mm-steps { display: flex; flex-wrap: wrap; justify-content: center; gap: .45rem; margin: .4rem 0 1.4rem; }
.mm-step { display: flex; align-items: center; gap: .45rem; padding: .32rem .8rem .32rem .38rem; border-radius: 999px;
  background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.13); color: #e4e7ef; font-size: .8rem; }
.mm-step b { display: inline-grid; place-items: center; width: 22px; height: 22px; border-radius: 50%;
  background: #b57bff; color: #10071f; font-size: .72rem; }

/* The pill switch: two buttons side by side in one rounded track. */
.st-key-mm_mode { width: 100%; max-width: 460px; margin: 0 auto .9rem; padding: 4px; border-radius: 999px;
  background: #0c0518; border: 1px solid rgba(255,255,255,.14); }
.st-key-mm_mode [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0 !important; }
.st-key-mm_mode [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
.st-key-mm_mode div.stButton > button { border-radius: 999px !important; min-height: 2.6rem; border: none !important;
  background: transparent !important; box-shadow: none !important; }
.st-key-mm_mode div.stButton > button p { color: #e4e7efaa !important; font-weight: 700 !important; }
.st-key-mm_mode .mm-on div.stButton > button, .st-key-mm_mode_on_host .st-key-mm_mode_host div.stButton > button,
.st-key-mm_mode_on_join .st-key-mm_mode_join div.stButton > button {
  background: linear-gradient(90deg, #8b4fe0, #b57bff) !important; box-shadow: 0 4px 16px rgba(181,123,255,.4) !important; }
.st-key-mm_mode_on_host .st-key-mm_mode_host div.stButton > button p,
.st-key-mm_mode_on_join .st-key-mm_mode_join div.stButton > button p { color: #fff !important; }

/* The 5 | 8 players switch on "Host a game": same pill look, a bit smaller. */
.st-key-mm_size { width: 100%; padding: 3px; border-radius: 999px; background: #0c0518; border: 1px solid rgba(255,255,255,.14); }
.st-key-mm_size [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0 !important; }
.st-key-mm_size [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
.st-key-mm_size div.stButton > button { border-radius: 999px !important; min-height: 2.2rem; border: none !important;
  background: transparent !important; box-shadow: none !important; }
.st-key-mm_size div.stButton > button p { color: #e4e7efaa !important; font-weight: 700 !important; white-space: nowrap; }
.st-key-mm_size_on_5 .st-key-mm_size_5 div.stButton > button, .st-key-mm_size_on_8 .st-key-mm_size_8 div.stButton > button {
  background: linear-gradient(90deg, #8b4fe0, #b57bff) !important; box-shadow: 0 4px 14px rgba(181,123,255,.35) !important; }
.st-key-mm_size_on_5 .st-key-mm_size_5 div.stButton > button p, .st-key-mm_size_on_8 .st-key-mm_size_8 div.stButton > button p {
  color: #fff !important; }

/* The glass card holding the form. */
.st-key-mm_home_card { width: 100%; max-width: 560px; margin: 0 auto; padding: 1.1rem 1.1rem .9rem; border-radius: 20px;
  background: linear-gradient(160deg, rgba(42,20,80,.93), rgba(23,11,47,.93)); border: 1px solid rgba(255,255,255,.12);
  box-shadow: 0 20px 50px rgba(0,0,0,.5); }
.st-key-mm_home_card [data-testid="stWidgetLabel"] p, .mm-label { color: #e4e7efbb !important; font-size: .78rem !important;
  letter-spacing: .08em; text-transform: uppercase; font-weight: 600; }
.mm-label { margin: .1rem 0 .45rem; }
.st-key-mm_home_card div.stButton > button[kind="primary"] { min-height: 3rem; border-radius: 12px !important;
  background: linear-gradient(90deg, #8b4fe0, #b57bff) !important; box-shadow: 0 8px 24px rgba(181,123,255,.35) !important; }
.st-key-mm_home_card div.stButton > button[kind="primary"] p { font-weight: 800 !important; font-size: 1.02rem !important; }
.st-key-mm_mode div.stButton > button p { white-space: nowrap; }
.mm-join-title { text-align: center; font-family: Cinzel, Georgia, serif; font-weight: 800; color: #f8f2ff;
  font-size: 1.15rem; margin: 0 0 .8rem; }
</style>"""

ROUND1_CHIP = {5: "Round 1 · Everyone vs everyone", 8: "Round 1 · Four duels", None: "Round 1 · Quick puzzles"}
GUESTS = {5: "FIVE GUESTS · ", 8: "EIGHT GUESTS · ", None: ""}


def _hero(size=None):
    """Title, tagline and the three round chips. The host's page shows the version
    for the number of players they pick (5: everyone together in Round 1, 8: duels).
    Someone joining hasn't chosen anything, so they see a neutral version (None);
    the lobby shows the right one once they're in."""
    st.markdown(STYLE, unsafe_allow_html=True)
    common.show_wordmark()
    steps = ("<div class='mm-steps'>"
             f"<span class='mm-step'><b>1</b>{ROUND1_CHIP[size]}</span>"
             "<span class='mm-step'><b>2</b>Round 2 · The vault</span>"
             "<span class='mm-step'><b>3</b>Round 3 · The final mystery</span></div>")
    st.markdown(f"<div class='mm-tagline'>{GUESTS[size]}ONE MANSION · ONE LAST CLUE</div>" + steps,
                unsafe_allow_html=True)


def show():
    mode = st.session_state.setdefault("mm_home_mode", "host")
    if mode == "host":
        _hero(st.session_state.setdefault("mm_table_size", rules.MAX_PLAYERS))   # follows the 5 | 8 switch
    else:
        _hero()                                                                # neutral: the code decides

    # The pill switch. The outer container's key says which half is lit.
    with st.container(key=f"mm_mode_on_{mode}"):
        with st.container(key="mm_mode"):
            host_col, join_col = st.columns(2)
            with host_col:
                if st.button("Host a game", key="mm_mode_host", width="stretch") and mode != "host":
                    st.session_state["mm_home_mode"] = "host"
                    st.rerun()
            with join_col:
                if st.button("Join with a code", key="mm_mode_join", width="stretch") and mode != "join":
                    st.session_state["mm_home_mode"] = "join"
                    st.rerun()
    with st.container(key="mm_home_card"):
        if mode == "host":
            show_create()
        else:
            _join_form()


def _table_size():
    """The host's choice: 8 players (Round 1 in duels) or 5 (everyone together)."""
    size = st.session_state.setdefault("mm_table_size", rules.MAX_PLAYERS)
    st.markdown("<div class='mm-label'>How many players?</div>", unsafe_allow_html=True)
    with st.container(key=f"mm_size_on_{size}"):
        with st.container(key="mm_size"):
            for column, option in zip(st.columns(2), (5, 8)):
                with column:
                    if st.button(f"{option} players", key=f"mm_size_{option}", width="stretch") and size != option:
                        st.session_state["mm_table_size"] = option
                        st.rerun()
    st.caption("5 players: everyone plays Round 1 together and the weakest is out (quicker, great for a demo). "
               if size == 5 else "8 players: Round 1 is four 1-v-1 duels.")
    return size


def show_create():
    size = _table_size()
    appearance = common.avatar_picker("create_avatar")
    name = st.text_input("Your name", key="create_name", max_chars=rules.MAX_NAME_LENGTH, placeholder="e.g. Marta")
    submitted = st.button("Create tournament", type="primary", key="create_tournament", width="stretch")
    st.caption(f"You'll be the host and one of the {size} players.")
    if submitted:
        tour, host_id, message = storage.create(name, appearance=appearance, size=size)
        if tour is None:
            st.error(message)
        else:
            common.flash("success", message)
            common.go_to(tour["code"], host_id)


def show_join(prefilled_code=""):
    """Used by app.py when someone opens a join link: the same look, join form only."""
    _hero()                            # neutral, like the Join tab: the lobby shows the game's version
    with st.container(key="mm_home_card"):
        st.markdown(f"<div class='mm-join-title'>Join tournament {prefilled_code}</div>", unsafe_allow_html=True)
        _join_form(prefilled_code)


def _join_form(prefilled_code=""):
    code = st.text_input("Code", value=prefilled_code, key="join_code", max_chars=storage.CODE_LENGTH,
                         placeholder="e.g. KQZT")
    existing = storage.load(code) if len(code.strip()) == storage.CODE_LENGTH else None
    occupied = [player.get("appearance") for player in existing.get("players", [])] if existing else []
    appearance = common.avatar_picker("join_avatar", occupied)
    name = st.text_input("Your name", key="join_name", max_chars=rules.MAX_NAME_LENGTH, placeholder="e.g. Marta")
    submitted = st.button("Join tournament", type="primary", key="join_tournament", width="stretch")
    if submitted:
        player_id = storage.new_player_id()
        tour, message = storage.update(code, rules.join, player_id, name, appearance)
        if tour is not None and rules.find_player(tour, player_id):
            common.flash("success", message)
            common.go_to(tour["code"], player_id)
        else:
            st.error(message)
