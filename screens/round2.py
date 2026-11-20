"""Round 2 on each phone. Shared progress is re-read from storage every 2 seconds."""

import base64
import functools
import html
import math
import time
from pathlib import Path

import streamlit as st

import round2 as rules
import storage
import tournament
from screens import art, common, spectate

REFRESH = "2s"
ROOM_IMAGES = {
    "Vault": "r2-vault.png",
    "Gallery": "r2-gallery.png",
    "Rooftop": "r2-rooftop.png",
}
ROOM_ICONS = {"Cellar": "Wine Cellar", "Kitchen": "Kitchen"}

def show(code, me):
    # Spectators: crowd bar + reactions at the top, their own buttons at the bottom.
    tour = spectate.start(code, me)
    round2_state = (tour or {}).get("round2") or {}
    intro_ends_at = round2_state.get("intro_ends_at")
    intro_active = bool(
        tour and tour.get("status") == "round2"
        and (intro_ends_at is None or time.time() < intro_ends_at)
    )
    _live_round(code, me)
    if not intro_active:
        spectate.panel(code, tour, me)


@st.fragment(run_every=REFRESH)
def _live_round(code, me):
    now = time.time()                         # server clock; never accept a browser timestamp
    tour, _ = storage.update(code, rules.prepare_round, now)
    if tour is None:
        st.error("This tournament is no longer available.")
        return
    if tour["status"] not in ("round2", "final"):
        st.rerun(scope="app")

    view = rules.player_view(tour, me)
    intro_ends_at = tour["round2"].get("intro_ends_at")
    if tour["status"] == "round2" and intro_ends_at is not None and now < intro_ends_at:
        _round2_intro(tour, me, intro_ends_at, now)
        return
    if tour["status"] == "final":
        _end_screen(code, tour, me, view)
        return
    if view.get("duo_id") is None:
        st.title("Round 2: Duo Vault Challenge")
        st.info("You were eliminated in Round 1. You can watch the challenge here.")
        return

    st.title("Round 2: Duo Vault Challenge")
    st.caption("One minute. Combine your clues, open the vault, then find the safe route.")
    teammate = view.get("teammate")
    if teammate:
        st.markdown(f"Your teammate: {common.player_label(teammate)}")

    seconds = max(0, math.ceil(view["ends_at"] - now))
    st.markdown(f"### ⏱️ {seconds // 60}:{seconds % 60:02d}")
    st.progress(seconds / rules.ROUND_SECONDS)

    feedback = st.session_state.get(_feedback_key(code))
    if feedback:
        kind, message, expires_at = feedback
        if now < expires_at:
            getattr(st, kind)(message)
        else:
            st.session_state.pop(_feedback_key(code), None)

    st.subheader("Your clue card")
    _clue_card(code, me, view["card"])
    st.caption("Read your clue aloud to your teammate. Each phone receives only its player's card.")

    locked_until = view.get("locked_until")
    if locked_until is not None and now < locked_until:
        left = max(1, math.ceil(locked_until - now))
        st.warning(f"Alarm lockout: wait {left} seconds before submitting again.")
        return

    if view["code_solved_at"] is None:
        _code_form(code, me, view["duo_id"])
    else:
        if st.session_state.pop(_locked_in_key(code), False):
            st.markdown(art.stamp("LOCKED IN"), unsafe_allow_html=True)
        st.success("Vault code solved. Your teammate sees this progress too.")
        _map(code, me, view)

    st.info("The other duo is still in the challenge. First to reach the Rooftop advances.")


def _round2_intro(tour, me, intro_ends_at, now):
    st.markdown(art.heading("duel", "Round 2: Duo Vault Challenge", size=44, level=1),
                unsafe_allow_html=True)
    st.markdown("### Two duos. One vault. Who reaches the rooftop first?")

    teams = []
    for duo_id, duo in tour["round2"]["duos"].items():
        players = [tournament.find_player(tour, player_id) for player_id in duo["players"]]
        teams.append((duo_id, players))

    cards = []
    for index, (duo_id, players) in enumerate(teams, start=1):
        portraits = "".join(common.profile_card(player) for player in players if player is not None)
        yours = me in tour["round2"]["duos"][duo_id]["players"]
        label = f"DUO {index}" + (" · YOUR TEAM" if yours else "")
        cards.append(
            f"<section class='r2-intro-team' aria-label='{label}'>"
            f"<div class='r2-intro-team-title'>{label}</div>"
            f"<div class='r2-intro-players'>{portraits}</div></section>"
        )

    st.markdown("""
    <style>
    .r2-intro-matchup { align-items:center; display:grid; gap:clamp(.5rem,2vw,1.4rem);
      grid-template-columns:minmax(0,1fr) auto minmax(0,1fr); margin:1.25rem auto; max-width:980px; }
    .r2-intro-team { background:linear-gradient(145deg,rgba(99,50,150,.58),rgba(30,15,60,.76));
      border:1px solid rgba(180,194,255,.55); border-radius:18px; box-shadow:0 0 20px rgba(143,105,255,.22);
      min-width:0; padding:1rem .5rem .8rem; }
    .r2-intro-team-title { color:#e7d2ff; font-family:Cinzel,Georgia,serif; font-size:.95rem;
      font-weight:800; letter-spacing:.1em; margin-bottom:.8rem; text-align:center; }
    .r2-intro-players { align-items:flex-start; display:flex; gap:.15rem; justify-content:center; }
    .r2-intro-players .mm-profile { flex:1 1 0; min-width:0; }
    .r2-intro-players .mm-profile-photo { height:clamp(66px,10vw,112px); width:clamp(66px,10vw,112px); }
    .r2-intro-players .mm-profile-name { font-size:clamp(.72rem,1.6vw,.95rem); }
    .r2-intro-vs { color:#f5edff; font-family:Cinzel,Georgia,serif; font-size:clamp(2.4rem,6vw,4.4rem);
      font-weight:900; letter-spacing:.05em; text-shadow:0 0 8px #c4a0ff,0 0 22px #8c49df; }
    .r2-intro-start { color:#d5c0e8; margin:.7rem 0 0; text-align:center; }
    @media(max-width:620px) {
      .r2-intro-matchup { gap:.3rem; grid-template-columns:minmax(0,1fr) auto minmax(0,1fr); }
      .r2-intro-team { padding:.8rem .25rem .6rem; }
      .r2-intro-team-title { font-size:.76rem; letter-spacing:.04em; }
      .r2-intro-players .mm-profile-photo { height:64px; width:64px; }
      .r2-intro-vs { font-size:1.8rem; }
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown(
        f"<div class='r2-intro-matchup'>{cards[0]}<div class='r2-intro-vs'>VS</div>{cards[1]}</div>",
        unsafe_allow_html=True,
    )
    st.caption("Round 1's four winners have been paired into two teams. Combine your clues to open the vault.")
    seconds = max(1, math.ceil(intro_ends_at - now))
    st.markdown(f"<p class='r2-intro-start'>The challenge begins in {seconds}…</p>", unsafe_allow_html=True)


def _feedback_key(code):
    return f"r2_{code}_feedback"


def _locked_in_key(code):
    return f"r2_{code}_locked_in"


def _clue_card(code, me, clue):
    button_key = art.css_key(f"r2_{code}_{me}_clue_card")
    revealed_key = f"{button_key}_revealed"
    st.markdown(f"""
    <style>
    .st-key-{button_key} {{ max-width: 520px; margin: .75rem auto 1rem; }}
    .st-key-{button_key} div.stButton > button {{
      min-height: 320px; border: 3px solid #9d55ff !important; border-radius: 18px !important;
      color: #fff !important; font-size: 1.25rem !important; font-weight: 900 !important;
      letter-spacing: .14em; text-shadow: 0 2px 8px #10071f;
      background:
        radial-gradient(ellipse 42% 46% at 50% 50%, #34366f 0 80%, transparent 82%),
        linear-gradient(135deg, #32164e, #302b69 57%, #172e5b) !important;
      box-shadow: 0 0 18px rgba(159,85,255,.48), inset 0 0 22px rgba(186,142,255,.2);
      transition: transform .18s ease, box-shadow .18s ease;
    }}
    .st-key-{button_key} div.stButton > button:hover {{
      border-color: #c9a6ff !important; transform: translateY(-3px);
      box-shadow: 0 0 28px rgba(159,85,255,.72), inset 0 0 24px rgba(186,142,255,.27);
    }}
    .st-key-{button_key} div.stButton > button p {{ color: #fff !important; }}
    .r2-card-scene {{ height: 320px; max-width: 520px; margin: .75rem auto 1rem; perspective: 1100px; }}
    .r2-clue-card {{ height: 100%; position: relative; transform-style: preserve-3d;
      animation: r2-card-flip .78s cubic-bezier(.2,.8,.25,1) both; }}
    @keyframes r2-card-flip {{ from {{ transform: rotateY(0deg); }} to {{ transform: rotateY(180deg); }} }}
    .r2-card-face {{ position: absolute; inset: 0; display: flex; flex-direction: column;
      align-items: center; justify-content: center; padding: 1.4rem; text-align: center;
      border: 3px solid #9d55ff; border-radius: 18px; backface-visibility: hidden;
      -webkit-backface-visibility: hidden; box-shadow: 0 0 22px rgba(159,85,255,.48),
      inset 0 0 24px rgba(186,142,255,.18); }}
    .r2-card-back {{ color: #fff; font-size: 1.25rem; font-weight: 900; letter-spacing: .14em;
      background: radial-gradient(ellipse 42% 46% at 50% 50%, #34366f 0 80%, transparent 82%),
      linear-gradient(135deg, #32164e, #302b69 57%, #172e5b); }}
    .r2-card-front {{ transform: rotateY(180deg); color: #fbf7ff;
      background: linear-gradient(145deg, #432274 0%, #34265f 52%, #173c70 100%); }}
    .r2-card-front-label {{ color: #d8bdff; font-size: .78rem; font-weight: 900;
      letter-spacing: .18em; margin-bottom: .8rem; text-transform: uppercase; }}
    .r2-card-front-clue {{ font-size: clamp(1rem,2.5vw,1.3rem); font-weight: 700;
      line-height: 1.55; margin: 0; white-space: pre-line; }}
    @media(max-width:560px) {{
      .st-key-{button_key} div.stButton > button {{ min-height: 270px; }}
      .r2-card-scene {{ height: 270px; }}
      .r2-card-face {{ padding: 1rem; }}
    }}
    @media(prefers-reduced-motion:reduce) {{ .r2-clue-card {{ animation-duration: .01ms; }} }}
    </style>
    """, unsafe_allow_html=True)

    if not st.session_state.get(revealed_key, False):
        if st.button("Tap here", key=button_key, width="stretch"):
            st.session_state[revealed_key] = True
            st.rerun(scope="fragment")
        return

    st.markdown(
        "<div class='r2-card-scene' role='group' aria-label='Your revealed clue'>"
        "<div class='r2-clue-card'>"
        "<div class='r2-card-face r2-card-back'>Tap here</div>"
        "<div class='r2-card-face r2-card-front'>"
        "<div class='r2-card-front-label'>Your clue</div>"
        f"<p class='r2-card-front-clue'>{html.escape(clue)}</p>"
        "</div></div></div>",
        unsafe_allow_html=True,
    )


def _show_feedback(code, message):
    if message.startswith(("Vault unlocked", "Safe choice", "Rooftop reached")):
        if message.startswith("Vault unlocked"):
            # A local, one-shot stamp for the player who submitted the solved code.
            # art.stamp fades out after 1.4 seconds, like Round 1.
            st.session_state[_locked_in_key(code)] = True
            st.session_state.pop(_feedback_key(code), None)
            st.rerun(scope="fragment")
        kind = "success"
    elif message.startswith(("Wrong code", "Alarm")):
        kind = "error"
    else:
        kind = "info"
    st.session_state[_feedback_key(code)] = (kind, message, time.time() + 8)
    st.rerun(scope="fragment")


def _code_form(code, me, duo_id):
    input_class = art.css_key(f"r2_{code}_vault_code")
    input_key = f"r2_{code}_vault_code"
    typed = str(st.session_state.get(input_key, ""))[:4]
    digits = [character if character in "0123456789" else "?" for character in typed]
    digits.extend(["?"] * (4 - len(digits)))
    st.markdown(f"""
    <style>
    .r2-vault-entry {{ margin: .7rem auto .35rem; text-align: center; }}
    .r2-vault-entry-title {{ color: #f3e6ff; font-family: Cinzel, Georgia, serif;
      font-size: 1.15rem; font-weight: 800; letter-spacing: .08em;
      margin-bottom: -.35rem; text-shadow: 0 0 10px rgba(186,115,255,.7); }}
    .st-key-{input_class} {{ max-width: 440px; margin: 0 auto .8rem; }}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(
        "<div class='r2-vault-entry'><div class='r2-vault-entry-title'>Type the code</div>"
        + art.img(art.padlock(digits), width="220px")
        + "</div>",
        unsafe_allow_html=True,
    )
    value = st.text_input(
        "Enter the four-digit vault code", max_chars=4, type="password", placeholder="Enter 4 digits",
        label_visibility="collapsed", key=input_key,
    )
    if st.button("Unlock", type="primary", key=f"r2_{code}_vault_unlock"):
        _, message = storage.update(code, rules.submit_code, me, duo_id, value, time.time())
        _show_feedback(code, message)


@functools.lru_cache(maxsize=5)
def _room_image_uri(room):
    if room in ROOM_IMAGES:
        image_path = Path(__file__).resolve().parent.parent / "assets" / ROOM_IMAGES[room]
        image_data = image_path.read_bytes()
        return "data:image/png;base64," + base64.b64encode(image_data).decode("ascii")

    svg = art.room(ROOM_ICONS[room])
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def _route_progress(route_step):
    route = rules.SAFE_ROUTE
    current_step = min(max(int(route_step), 0), len(route) - 1)
    progress = round(current_step / (len(route) - 1) * 100) if len(route) > 1 else 100
    stops = []
    for index, room in enumerate(route):
        state = "visited" if index < current_step else "current" if index == current_step else "upcoming"
        marker = (
            "<span class='r2-route-marker'>You're here"
            "<span aria-hidden='true'>&#8595;</span></span>"
            if index == current_step else ""
        )
        stops.append(
            f"<div class='r2-route-stop r2-route-{state}'>{marker}"
            f"<div class='r2-route-node'><img src='{_room_image_uri(room)}' alt=''/></div>"
            f"<span class='r2-route-label'>{html.escape(room)}</span></div>"
        )
    return f"""
    <style>
    .r2-route-progress {{ position:relative; display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
      align-items:start; max-width:940px; margin:1.1rem auto 1.25rem; padding-top:2.4rem; }}
    .r2-route-line {{ position:absolute; z-index:0; left:16.666%; top:92px; width:66.668%; height:5px;
      border-radius:99px; background:rgba(207,190,255,.2); box-shadow:0 0 10px rgba(151,112,255,.28); }}
    .r2-route-line > span {{ display:block; height:100%; border-radius:inherit;
      background:linear-gradient(90deg,#a56aff,#bd91ff 55%,#87e8ff);
      box-shadow:0 0 12px rgba(180,119,255,.9); transition:width .35s ease; }}
    .r2-route-stop {{ position:relative; z-index:1; display:flex; min-width:0; flex-direction:column;
      align-items:center; opacity:.58; transition:opacity .25s ease; }}
    .r2-route-node {{ display:grid; width:108px; height:108px; place-items:center; overflow:hidden;
      border:2px solid rgba(218,211,255,.78); border-radius:50%;
      background:radial-gradient(circle at 50% 42%,rgba(106,86,192,.68),rgba(35,22,63,.98) 74%);
      box-shadow:0 0 13px rgba(157,116,255,.4),inset 0 0 15px rgba(201,174,255,.18); }}
    .r2-route-node img {{ width:82%; height:82%; object-fit:contain;
      filter:drop-shadow(0 0 8px rgba(198,159,255,.78)); }}
    .r2-route-label {{ margin-top:.55rem; color:#eee7ff; font-size:.95rem; font-weight:900;
      text-shadow:0 0 8px rgba(187,143,255,.54); }}
    .r2-route-visited {{ opacity:.9; }}
    .r2-route-visited .r2-route-node {{ border-color:#bfa0ff;
      box-shadow:0 0 17px rgba(166,112,255,.72),inset 0 0 15px rgba(201,174,255,.2); }}
    .r2-route-current {{ opacity:1; }}
    .r2-route-current .r2-route-node {{ border-color:#a4edff;
      box-shadow:0 0 9px #9aeaff,0 0 24px rgba(166,112,255,.95),inset 0 0 18px rgba(201,174,255,.25); }}
    .r2-route-current .r2-route-label {{ color:#fff; text-shadow:0 0 10px #a879ff; }}
    .r2-route-marker {{ position:absolute; top:-2.25rem; display:flex; flex-direction:column; align-items:center;
      color:#fff; font-size:.83rem; font-weight:900; white-space:nowrap;
      text-shadow:0 0 9px #bc8aff,0 0 18px rgba(164,115,255,.9); }}
    .r2-route-marker > span {{ color:#a9ecff; font-size:1.65rem; line-height:.9;
      text-shadow:0 0 10px #a9ecff; }}
    @media(max-width:560px) {{
      .r2-route-progress {{ padding-top:2rem; margin:.9rem auto 1rem; }}
      .r2-route-line {{ top:66px; height:4px; }}
      .r2-route-node {{ width:64px; height:64px; }}
      .r2-route-label {{ margin-top:.4rem; font-size:.76rem; }}
      .r2-route-marker {{ top:-1.75rem; font-size:.67rem; }}
      .r2-route-marker > span {{ font-size:1.35rem; }}
    }}
    </style>
    <div class='r2-route-progress' aria-label='Vault to Gallery to Rooftop route'>
      <div class='r2-route-line' aria-hidden='true'><span style='width:{progress}%'></span></div>
      {''.join(stops)}
    </div>
    """


def _room_choice_style(key, image_uri):
    selector = f".st-key-{art.css_key(key)} div.stButton > button"
    return f"""
    <style>
    {selector} {{
      background-image:url("{image_uri}"),linear-gradient(145deg,#42216c,#25275b 65%,#173967) !important;
      background-repeat:no-repeat,no-repeat !important; background-position:center 12px,center !important;
      background-size:min(calc(100% - 26px),180px) 150px,100% 100% !important;
      border:2px solid {art.PURPLE} !important; border-radius:16px !important;
      box-shadow:0 0 18px rgba(157,85,255,.4),inset 0 0 16px rgba(190,166,255,.12) !important;
      color:{art.IVORY} !important; min-height:232px; padding:164px .5rem .45rem !important;
      transition:transform .15s ease,box-shadow .15s ease,border-color .15s ease;
    }}
    {selector}:hover {{ border-color:{art.TILE_COLOURS['ice']} !important; filter:drop-shadow(0 0 12px {art.TILE_COLOURS['ice']});
      transform:translateY(-4px); }}
    {selector} p {{ color:{art.IVORY} !important; font-size:1rem !important; font-weight:900 !important;
      line-height:1.15 !important; margin:0 !important; text-align:center; }}
    @media(max-width:640px) {{
      {selector} {{ background-size:min(calc(100% - 18px),138px) 116px,100% 100% !important;
        min-height:194px; padding:128px .25rem .4rem !important; }}
      {selector} p {{ font-size:.78rem !important; }}
    }}
    </style>
    """


def _map(code, me, view):
    route_step = view["route_step"]
    st.subheader("Choose a safe route")
    st.markdown(_route_progress(route_step), unsafe_allow_html=True)
    st.caption(f"Alarms: {view['alarm_count']}")

    locked_until = view.get("locked_until")
    now = time.time()
    if locked_until is not None and now < locked_until:
        left = max(1, math.ceil(locked_until - now))
        st.warning(f"Alarm lockout: wait {left} seconds before choosing again.")
        return

    if route_step >= len(rules.SAFE_ROUTE) - 1:
        st.success("Your duo reached the Rooftop.")
        return

    here = rules.SAFE_ROUTE[route_step]
    columns = st.columns(2)
    for column, door in zip(columns, rules.ROUTE_CHOICES[here]):
        key = f"r2_{code}_{here}_{door}"
        with column:
            st.markdown(_room_choice_style(key, _room_image_uri(door)), unsafe_allow_html=True)
            if st.button(door, key=key, width="stretch"):
                _, message = storage.update(code, rules.choose_door, me, view["duo_id"], door, time.time())
                _show_feedback(code, message)


def _end_screen(code, tour, me, view):
    st.title("Which duo made it out?")
    finalists = tour["round2"]["duos"][tour["round2"]["winner"]]["players"]
    winner_players = [tournament.find_player(tour, player_id) for player_id in finalists]

    if view.get("duo_id") is None:
        st.markdown(art.banner("eliminated", "You were eliminated in Round 1. Stay and watch the rest of the game!", good=False),
                    unsafe_allow_html=True)
    elif view.get("advanced"):
        st.markdown(art.banner("through", "Your duo made it through to the final!"), unsafe_allow_html=True)
    else:
        st.markdown(art.banner("eliminated", "Your duo was eliminated. Stay and watch the final!", good=False),
                    unsafe_allow_html=True)

    st.markdown(spectate.calls_summary(tour, "round2"), unsafe_allow_html=True)
    winners_html = "".join(common.profile_card(player, "passed") for player in winner_players)
    st.markdown(
        "<style>"
        ".mm-r2-winners .mm-result-duel{padding:1.2rem .9rem}"
        ".mm-r2-winners .mm-result-duel-title{font-size:1.05rem;margin-bottom:1rem}"
        ".mm-r2-winners .mm-result-pair{gap:clamp(1rem,5vw,3rem)}"
        ".mm-r2-winners .mm-result-pair .mm-profile-photo{width:132px;height:132px}"
        ".mm-r2-winners .mm-profile-name{font-size:1.08rem;margin-top:.3rem}"
        ".mm-r2-winners .mm-profile-status{font-size:.92rem;margin-top:.35rem}"
        "@media(max-width:560px){.mm-r2-winners .mm-result-pair .mm-profile-photo{width:104px;height:104px}}"
        "</style>"
        "<div class='mm-r2-winners'><div class='mm-results-grid' "
        "style='grid-template-columns:minmax(340px, 600px);justify-content:center'>"
        "<div class='mm-result-duel'><div class='mm-result-duel-title'>The winning duo</div>"
        f"<div class='mm-result-pair'>{winners_html}</div></div></div></div>",
        unsafe_allow_html=True,
    )

    if view.get("advanced"):
        if view.get("decided_by") == "timeout":
            st.caption("The timer ended; the code, alarms, and tie-break draw decided the result.")
        if me in finalists and st.button("Start Round 3: Final Mansion Mystery", type="primary"):
            after, message = storage.update(
                code, tournament.start_round3, me, finalists, time.time()
            )
            if after is not None and after["status"] == "round3":
                st.rerun(scope="app")
            st.error(message)
    if view.get("decided_by") == "timeout":
        st.caption("The round ended at its server-set one-minute limit.")

