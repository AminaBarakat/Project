"""The purple, story-led two-finalist screen for Round 3."""

import base64
import html
from pathlib import Path
import time

import streamlit as st

import round1 as r1
import fan_vote
import round3 as r3
import storage
import tournament as rules
from screens import art, avatars, common, spectate

DETECTIVE_IMAGE = Path(__file__).resolve().parents[1] / "assets" / "detective-purple.png"
ASSETS = Path(__file__).resolve().parents[1] / "assets"
CASE_IMAGES = {
    "Nova": ASSETS / "suspect-nova.png",
    "Theo": ASSETS / "suspect-theo.png",
    "Mira": ASSETS / "suspect-mira.png",
    "Library": ASSETS / "room-library.png",
    "Observatory": ASSETS / "room-observatory.png",
    "Conservatory": ASSETS / "room-conservatory.png",
}
EVIDENCE_MARKERS = {
    "Nova": "3", "Theo": "7", "Mira": "5",
    "Library": "4", "Observatory": "6", "Conservatory": "1",
    "Key": "2", "Map": "8", "Flashlight": "9",
}


def _detective_data_url():
    """A local asset as a data URL so it also works after Streamlit deployment."""
    encoded = base64.b64encode(DETECTIVE_IMAGE.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _image_data_url(path):
    """Embed supplied case-file art so Streamlit Cloud can render it too."""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _story_style():
    st.markdown("""
    <style>
    .r3-story { max-width: 1000px; margin: 0 auto; padding: .4rem 0 0; }
    .r3-story-kicker { color: #e3c9ff; font-size: .78rem; font-weight: 700; letter-spacing: .16em; text-align: center; }
    .r3-scene { display: grid; grid-template-columns: minmax(185px, .78fr) minmax(0, 1.55fr); align-items: center;
      gap: clamp(1rem, 5vw, 3.5rem); min-height: 440px; padding: .5rem 1rem 0; }
    .r3-detective { width: min(100%, 290px); margin: 0 auto; position: relative; align-self: end; animation: r3-bob 2.3s ease-in-out infinite; }
    .r3-detective img { width: 100%; display: block; filter: drop-shadow(0 0 20px #b249f7); }
    .r3-mouth { position: absolute; width: 19px; height: 5px; left: 47%; top: 25.1%; background: #57213a;
      border-radius: 0 0 12px 12px; animation: r3-talk .34s ease-in-out infinite alternate; }
    .r3-speech { background: rgba(12, 5, 27, .82); border: 1px solid rgba(220, 190, 255, .72); border-radius: 17px;
      box-shadow: 0 12px 35px rgba(0, 0, 0, .3), inset 0 0 28px rgba(135, 66, 193, .15); color: #f7eeff;
      font-family: Georgia, serif; font-size: clamp(1.08rem, 2.3vw, 1.34rem); line-height: 1.62; min-height: 210px; padding: 1.4rem 1.55rem; }
    .r3-typed-text { display:block; }
    .r3-typed-line { display:block; max-width:100%; overflow:hidden; white-space:nowrap; width:0;
      animation:r3-type-line 1.65s steps(38, end) forwards; animation-delay:var(--delay); }
    .r3-typed-line + .r3-typed-line { margin-top:.38rem; }
    .r3-cursor { color: #e6a7ff; animation: r3-blink .75s step-end infinite; }
    .r3-question { color: #fff; font-family: Georgia, serif; font-size: 1.5rem; font-style: italic; line-height: 1.35;
      padding: 1.2rem .3rem .2rem; text-align: center; }
    .r3-finalists { border-top: 1px solid rgba(223, 190, 255, .38); display: flex; gap: clamp(2rem, 9vw, 6rem);
      justify-content: center; margin-top: .4rem; padding: 1rem 0 1.1rem; }
    .r3-finalist { color: #f7eeff; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 1rem; font-weight:800; letter-spacing: .02em; text-align: center; }
    .r3-avatar-ring { align-items: center; background: linear-gradient(145deg, #ffffff, #aeb4c0 42%, #fbfdff 66%, #777f8b);
      border-radius: 50%; box-shadow: 0 0 0 3px rgba(183, 147, 235, .55), 0 5px 18px rgba(0,0,0,.5); display: flex;
      height: 64px; justify-content: center; margin: 0 auto .45rem; padding: 4px; width: 64px; }
    .r3-avatar-ring img { border-radius:50%; height:100%; object-fit:contain; width:100%; }
    .r3-avatar-face { align-items: center; background: radial-gradient(circle at 38% 28%, #4e596c, #171426 72%); border-radius: 50%;
      color: #e9eef5; display: flex; font-size: 1.55rem; height: 100%; justify-content: center; width: 100%; }
    .r3-finalists-title { color: #d7b8f2; font-size: .72rem; font-weight: 700; letter-spacing: .16em; text-align: center; }
    .r3-case-intro { color:#d9c2ec; font-family:Georgia,serif; font-size:1.08rem; margin:.15rem 0 1rem; }
    .r3-case-section { color:#e3c9ff; font-family:Cinzel, Georgia, serif; font-size:.9rem; font-weight:800; letter-spacing:.08em; margin:1.25rem 0 .55rem; }
    .r3-case-grid { display:grid; gap:.8rem; grid-template-columns:repeat(3, minmax(0, 1fr)); }
    .r3-case-card { background:rgba(19,8,39,.58); border:1px solid rgba(220,190,255,.38); border-radius:16px; overflow:hidden; padding:.45rem; text-align:center; }
    .r3-case-card img { background:#eee8f3; border-radius:11px; display:block; height:136px; mix-blend-mode:normal; object-fit:contain; width:100%; }
    .r3-case-card span { color:#f8f2ff; display:block; font-family:ui-sans-serif, system-ui, sans-serif; font-weight:800; padding:.45rem .15rem .12rem; }
    .r3-evidence-marker { align-items:center; background:linear-gradient(135deg,rgba(112,54,191,.92),rgba(195,132,255,.9)); border:2px solid rgba(245,228,255,.94); border-radius:50%; box-shadow:0 0 13px rgba(193,120,255,.86); color:#fff; display:inline-flex; font-family:Cinzel, Georgia, serif; font-size:.76rem; font-weight:900; height:25px; justify-content:center; margin-left:.38rem; text-shadow:0 0 5px #35105e; vertical-align:middle; width:25px; }
    .r3-object-card { align-items:center; background:rgba(19,8,39,.58); border:1px solid rgba(220,190,255,.38); border-radius:16px; display:flex; gap:.55rem; justify-content:center; min-height:82px; padding:.6rem; }
    .r3-object-card b { color:#f8f2ff; font-family:ui-sans-serif, system-ui, sans-serif; }
    .r3-vault-lock { background:linear-gradient(135deg,rgba(100,52,170,.8),rgba(25,78,142,.62)); border:1px solid rgba(166,235,255,.76); border-radius:17px; box-shadow:0 0 25px rgba(155,85,255,.34),inset 0 0 25px rgba(194,235,255,.12); margin:1rem 0 .65rem; padding:.9rem 1rem; text-align:center; }
    .r3-vault-lock-title { color:#fff; font-family:Cinzel, Georgia, serif; font-size:.9rem; font-weight:900; letter-spacing:.08em; }
    .r3-vault-lock-help { color:#e2d2f6; font-size:.86rem; margin-top:.3rem; }
    .r3-solution-grid { display:grid; gap:.8rem; grid-template-columns:repeat(3, minmax(0, 1fr)); margin:1rem 0 1.35rem; }
    .r3-solution-card { background:rgba(39, 26, 77, .68); border:1px solid rgba(191,225,255,.52); border-radius:16px; overflow:hidden; padding:.5rem; text-align:center; }
    .r3-solution-card img { background:#eee8f3; border-radius:11px; display:block; height:138px; object-fit:contain; width:100%; }
    .r3-solution-kind { color:#d9c2ec; font-size:.72rem; font-weight:800; letter-spacing:.1em; margin-top:.55rem; text-transform:uppercase; }
    .r3-solution-value { color:#fff; font-family:ui-sans-serif, system-ui, sans-serif; font-size:1.08rem; font-weight:850; padding:.15rem 0 .25rem; }
    .r3-solution-icon { align-items:center; background:rgba(238,232,243,.9); border-radius:11px; display:flex; font-size:4.2rem; height:138px; justify-content:center; }
    .r3-choice-label { color:#f8f2ff; font-family:ui-sans-serif, system-ui, sans-serif; font-size:1rem; font-weight:800; margin:.9rem 0 .35rem; }
    .r3-choice-help { color:#d9c2ec; font-size:.88rem; margin-bottom:.55rem; }
    .r3-winner-lineup-title { color:#d7b8f2; font-size:.76rem; font-weight:800; letter-spacing:.16em; margin-top:1rem; text-align:center; }
    .r3-winner-lineup { align-items:end; display:flex; gap:.55rem; justify-content:center; margin:4.8rem auto 1rem; max-width:850px; position:relative; }
    .r3-lineup-player { color:#d8c9e9; flex:1 1 0; font-size:.67rem; font-weight:800; max-width:92px; opacity:.58; overflow-wrap:anywhere; position:relative; text-align:center; }
    .r3-lineup-player img { border:2px solid rgba(220,190,255,.55); border-radius:50%; height:58px; object-fit:contain; width:58px; }
    .r3-lineup-winner { color:#fff; opacity:1; text-shadow:0 0 12px #dba4ff; }
    .r3-hanging-light { animation:r3-light-slide 2.1s cubic-bezier(.2,.8,.2,1) forwards; height:82px; left:var(--target); opacity:0; position:absolute; top:-90px; transform:translateX(-50%); width:80px; z-index:2; }
    .r3-hanging-light::before { background:linear-gradient(#dfffff,#94e8ff); box-shadow:0 0 9px #baf5ff; content:''; height:63px; left:39px; position:absolute; top:0; width:2px; }
    .r3-hanging-light::after { background:radial-gradient(circle,#fff 0 16%,#9deeff 27%,#9e5aff 56%,transparent 70%); border-radius:50%; box-shadow:0 0 24px 10px rgba(160,224,255,.72); color:#fff; content:'✦'; font-size:21px; height:36px; left:22px; line-height:36px; position:absolute; text-align:center; top:56px; width:36px; }
    .r3-podium { align-items:end; animation:r3-podium-rise .9s 2.15s cubic-bezier(.2,.8,.2,1) both; display:flex; gap:clamp(.55rem, 3vw, 1.4rem); justify-content:center; margin:1.1rem 0 1.2rem; min-height:240px; }
    .r3-place { background:linear-gradient(145deg, rgba(109, 75, 164, .7), rgba(29, 55, 107, .65)); border:1px solid rgba(202, 229, 255, .48); border-radius:18px 18px 5px 5px; box-shadow:inset 0 1px 18px rgba(246, 235, 255, .14), 0 12px 24px rgba(0,0,0,.24); display:flex; flex-direction:column; justify-content:flex-end; padding:.75rem .55rem; text-align:center; width:min(29vw, 190px); }
    .r3-place-one { background:linear-gradient(145deg, rgba(157, 91, 224, .88), rgba(39, 91, 180, .83)); box-shadow:0 0 34px rgba(213, 170, 255, .8), inset 0 1px 25px rgba(255,255,255,.25); min-height:235px; position:relative; }
    .r3-place-two { min-height:180px; } .r3-place-three { min-height:145px; }
    .r3-place-number { color:#fff; font-family:Cinzel, Georgia, serif; font-size:1.55rem; font-weight:900; text-shadow:0 0 10px #a86bff; }
    .r3-place-one .r3-place-number { font-size:2.1rem; } .r3-place-name { color:#fff; font-family:ui-sans-serif, system-ui, sans-serif; font-size:.94rem; font-weight:850; margin-top:.38rem; overflow-wrap:anywhere; }
    .r3-place-note { color:#e4d8f2; font-size:.7rem; line-height:1.25; margin-top:.18rem; } .r3-place img { height:76px; margin:0 auto; object-fit:contain; width:76px; }
    .r3-place-one img { filter:drop-shadow(0 0 10px #fff3a2); height:104px; width:104px; }
    .r3-confetti { height:0; position:relative; z-index:3; } .r3-confetti i { animation:r3-confetti 2.8s linear infinite; background:var(--c); display:block; height:10px; left:var(--x); position:absolute; top:-10px; transform:rotate(20deg); width:6px; }
    @keyframes r3-confetti { 0% { opacity:0; transform:translateY(-20px) rotate(0deg) } 12% { opacity:1 } 100% { opacity:0; transform:translateY(260px) rotate(520deg) } }
    @keyframes r3-light-slide { 0% { left:4%; opacity:0; transform:translate(-50%,-58px); } 12% { opacity:1; } 78% { opacity:1; transform:translate(-50%,0); } 100% { left:var(--target); opacity:1; transform:translate(-50%,0); } }
    @keyframes r3-podium-rise { from { opacity:0; transform:translateY(90px); } to { opacity:1; transform:translateY(0); } }
    @media (max-width: 620px) { .r3-case-grid, .r3-solution-grid { grid-template-columns:1fr; } .r3-case-card img { height:175px; } .r3-typed-line { animation:none; overflow:visible; white-space:normal; width:auto; } .r3-winner-lineup { flex-wrap:wrap; margin-top:2rem; } .r3-lineup-player { flex:0 0 20%; } .r3-hanging-light { display:none; } }
    @media (max-width: 520px) { .r3-podium { gap:.35rem; } .r3-place { width:31vw; padding:.55rem .25rem; } .r3-place img { height:58px; width:58px; } .r3-place-one img { height:76px; width:76px; } .r3-place-name { font-size:.78rem; } }
    @media (max-width: 620px) { .r3-scene { grid-template-columns: 1fr; gap: 0; padding: .2rem 1rem 0; }
      .r3-detective { width: 180px; margin-bottom: -1rem; } .r3-speech { min-height: 170px; } }
    @keyframes r3-bob { 0%,100% { transform: translateY(0) } 50% { transform: translateY(-7px) } }
    @keyframes r3-talk { from { transform: scaleY(.55) } to { transform: scaleY(1.6) } }
    @keyframes r3-type-line { to { width:100%; } }
    @keyframes r3-blink { 50% { opacity: 0 } }
    </style>
    """, unsafe_allow_html=True)


def show(code, me):
    # Spectators: crowd bar + reactions at the top, their own buttons at the bottom.
    tour = spectate.start(code, me)
    _show_round(code, me)
    spectate.panel(code, tour, me)


def _show_round(code, me):
    # Keep the briefing in one browser render: the character animation can then
    # progress smoothly instead of restarting in the live timer fragment.
    tour = storage.load(code)
    now = time.time()
    if tour and tour["status"] == "round3" and tour["round3"].get("starts_at") is None:
        _story_style()
        _story(tour, code, me, time.time())
        return
    # Results must stay in one render. Otherwise the half-second live fragment
    # restarts their CSS animation and leaves the podium permanently dim.
    if tour and tour["status"] in ("round3_results", "finished"):
        _story_style()
        _results(tour, me)
        return
    if tour is None:
        st.error("This tournament could not be found.")
        return
    if tour["status"] != "round3":
        st.rerun(scope="app")

    _story_style()
    state = tour["round3"]
    if state.get("starts_at") is None:
        _story(tour, code, me, now)
    else:
        _mystery(tour, code, me, now)
    _round3_watch(code, tour["status"], state.get("starts_at"), state.get("ends_at"))


@st.fragment(run_every="1s")
def _round3_watch(code, shown_status, shown_starts_at, shown_ends_at):
    """Watch state changes without redrawing the case-file controls."""
    now = time.time()
    tour = storage.load(code)
    if tour is None:
        return
    state = tour.get("round3", {})
    if tour.get("status") == "round3" and state.get("ends_at") is not None and now >= state["ends_at"]:
        tour, _ = storage.update(code, r3.settle, now)
        state = tour.get("round3", {}) if tour else {}
    if (tour is None or tour.get("status") != shown_status
            or state.get("starts_at") != shown_starts_at
            or state.get("ends_at") != shown_ends_at):
        st.rerun(scope="app")


def _story(tour, code, me, now):
    text = _typed_story()
    profiles = _finalist_profiles(tour)
    st.markdown(f"""
    <div class="r3-story">
      <div class="r3-story-kicker">FINAL MANSION MYSTERY · CASE FILE 03</div>
      <div class="r3-scene">
        <div class="r3-detective"><img src="{_detective_data_url()}" alt="The detective briefing the finalists"><span class="r3-mouth"></span></div>
        <div class="r3-speech">{text}<span class="r3-cursor">▍</span></div>
      </div>
      <div class="r3-finalists-title">THE FINALISTS</div>
      <div class="r3-finalists">{profiles}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='r3-question'>{r3.FINAL_QUESTION}</div>", unsafe_allow_html=True)
    if r3.is_finalist(tour, me):
        if st.button("Open the final case", type="primary", width="stretch"):
            _, message = storage.update(code, r3.start_investigation, me, time.time())
            if "briefing is still" in message:
                st.info(message)
            else:
                st.toast(message)
                st.rerun()
    else:
        st.info("The finalists will open the final case when they are ready.")


def _typed_story():
    """Reveal whole lines reliably; per-character animations dropped letters."""
    lines = "".join(
        f"<span class='r3-typed-line' style='--delay:{number * 1.75:.2f}s'>{html.escape(line)}</span>"
        for number, line in enumerate(r3.STORY.splitlines())
    )
    return f"<span class='r3-typed-text'>{lines}</span>"


def _finalist_profiles(tour):
    """Silver-framed placeholders until the game later supports photo uploads."""
    profiles = []
    for player_id in tour["round3"]["finalists"]:
        player = rules.find_player(tour, player_id)
        name = html.escape(player["name"])
        _, path = common.AVATARS.get(player.get("appearance"), common.AVATARS["girl"])
        profiles.append(
            f"<div class='r3-finalist'><div class='r3-avatar-ring'><img src='{common.avatar_data_url(path)}' alt=''></div>{name}</div>"
        )
    return "".join(profiles)


def _mystery(tour, code, me, now):
    state = tour["round3"]
    st.title("Round 3: Final Mansion Mystery")

    left = r3.seconds_left(tour, now)
    st.markdown(f"### ⏱️ {left // 60}:{left % 60:02d}")
    st.progress(left / r3.ROUND_SECONDS)

    st.subheader("Case file")
    st.markdown("<div class='r3-case-intro'>Study the people, rooms, and clues. The three markers on your final theory form the Moonstone Vault code.</div>", unsafe_allow_html=True)
    suspects = "".join(
        f"<div class='r3-case-card'><img src='{_image_data_url(CASE_IMAGES[name])}' alt='{name}'><span>{name}<b class='r3-evidence-marker' title='Evidence marker'>{EVIDENCE_MARKERS[name]}</b></span></div>"
        for name in r3.SUSPECTS
    )
    rooms = "".join(
        f"<div class='r3-case-card'><img src='{_image_data_url(CASE_IMAGES[name])}' alt='{name}'><span>{name}<b class='r3-evidence-marker' title='Evidence marker'>{EVIDENCE_MARKERS[name]}</b></span></div>"
        for name in r3.ROOMS
    )
    objects = "".join(
        f"<div class='r3-object-card'><span>{icon}</span><b>{name}<span class='r3-evidence-marker' title='Evidence marker'>{EVIDENCE_MARKERS[name]}</span></b></div>"
        for name, icon in (("Key", "🗝️"), ("Map", "🗺️"), ("Flashlight", "🔦"))
    )
    st.markdown("<div class='r3-case-section'>Suspects</div><div class='r3-case-grid'>" + suspects + "</div>", unsafe_allow_html=True)
    st.markdown("<div class='r3-case-section'>Rooms</div><div class='r3-case-grid'>" + rooms + "</div>", unsafe_allow_html=True)
    st.markdown("<div class='r3-case-section'>Objects</div><div class='r3-case-grid'>" + objects + "</div>", unsafe_allow_html=True)
    for number, clue in enumerate(r3.CLUES, start=1):
        st.markdown(f"{number}. {clue}")

    finalists = [rules.find_player(tour, pid) for pid in state["finalists"]]
    st.caption("Finalists: " + " vs ".join(common.player_label(player) for player in finalists))

    if not r3.is_finalist(tour, me):
        st.info("The finalists are solving the mystery. You can watch the result here.")
        return

    st.divider()
    st.subheader("Present your theory")
    remaining = r3.guesses_left(tour, me)
    st.caption(f"You have {remaining} {'theory' if remaining == 1 else 'theories'} left. A fully correct theory wins immediately.")
    if remaining == 0:
        st.warning("You have used your theories. Watch the other finalist or wait for the clock.")
        return

    suspect = _theory_choice_cards(code, "suspect", "Who stole the Moonstone Key?", r3.SUSPECTS)
    room = _theory_choice_cards(code, "room", "Where did they hide it?", r3.ROOMS)
    object_name = _theory_choice_cards(code, "object", "What object did they carry?", r3.OBJECTS)
    st.markdown("<div class='r3-vault-lock'><div class='r3-vault-lock-title'>✦ Moonstone Vault Lock</div><div class='r3-vault-lock-help'>Enter the three evidence markers from your chosen thief, place, and object.</div></div>", unsafe_allow_html=True)
    lock_key = art.css_key(f"r3_vault_{code}")
    st.markdown(art.lock_style(lock_key, digits=3), unsafe_allow_html=True)
    st.markdown(f"""<style>
    .st-key-{lock_key} div.stFormSubmitButton {{ display: flex; justify-content: center; }}
    .st-key-{lock_key} div.stFormSubmitButton > button {{ width: auto !important; }}
    </style>""", unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;margin-top:.3rem">' + art.img(art.shackle(), width="130px").replace("margin:auto", "margin:0 auto -4px") + "</div>", unsafe_allow_html=True)
    with st.container(key=lock_key):
        with st.form(f"r3_{code}_vault_form", border=False):
            vault_code = st.text_input("Enter the vault code", max_chars=3, placeholder="···", key=f"r3_{code}_vault_code")
            with st.container(horizontal=True, horizontal_alignment="center"):
                submitted = st.form_submit_button("Unlock and submit theory", type="primary")
    if submitted:
        after, message = storage.update(code, r3.answer, me, suspect, room, object_name, time.time(), vault_code)
        if after is not None and after["status"] == "round3_results":
            st.rerun(scope="app")
        st.error(message) if message.startswith("Not quite") else st.toast(message)
        st.rerun()


def _theory_choice_cards(code, group, question, options):
    """Three glass choices, using session state only until the theory is submitted."""
    state_key = f"r3_{code}_{group}_choice"
    if state_key not in st.session_state:
        st.session_state[state_key] = options[0]
    st.markdown(f"<div class='r3-choice-label'>{question}</div><div class='r3-choice-help'>Choose one case-file card.</div>", unsafe_allow_html=True)
    columns = st.columns(3)
    for column, option in zip(columns, options):
        widget_key = f"r3_{code}_{group}_{option.casefold()}"
        selected = st.session_state[state_key] == option
        selector = f".st-key-{widget_key} div.stButton > button"
        selected_style = "border-color:#bcecff !important; box-shadow:0 0 22px rgba(136,218,255,.62), inset 0 0 22px rgba(178,109,255,.26) !important; transform:translateY(-3px);" if selected else ""
        st.markdown(f"""<style>
          {selector} {{ background:rgba(55, 26, 92, .6) !important; border:1px solid rgba(220,190,255,.44) !important; border-radius:15px !important; min-height:74px !important; padding:.6rem .35rem !important; {selected_style} }}
          {selector} p {{ color:#f8f2ff !important; font-family:ui-sans-serif, system-ui, sans-serif !important; font-weight:800 !important; }}
        </style>""", unsafe_allow_html=True)
        with column:
            if st.button(("✓ " if selected else "") + option, key=widget_key, width="stretch"):
                st.session_state[state_key] = option
                # The click itself reruns the script. Starting another whole-page
                # rerun here made consecutive phone taps needlessly sluggish.
    return st.session_state[state_key]


def _results(tour, me):
    """First a 10-second fan-favourite vote, then the stage: the yellow spotlight
    sweeps over the podium and the crowd and stops on the champion."""
    state = tour["round3"]
    now = time.time()
    if fan_vote.is_open(tour, now):
        _fan_vote_screen(tour, me, now)
        return
    _final_stage(tour, me, now)
    st.markdown(spectate.calls_summary(tour, "round3"), unsafe_allow_html=True)

    st.subheader("Solution")
    st.markdown(_solution_cards(), unsafe_allow_html=True)
    st.info("Nova marker: **3** · Conservatory marker: **1** · Map marker: **8**  \n### Moonstone Vault code: `318`")
    st.caption(f"Winner decided by: {state['decided_by']}.")


# --- the fan-favourite vote (10 seconds, everyone) -------------------------------------

@st.fragment(run_every="1s")
def _vote_watch(code, closes):
    """Shows how many have voted; redraws the page when the vote closes."""
    tour = storage.load(code)
    if tour is None:
        return
    now = time.time()
    if now >= fan_vote.closes_at(tour) or fan_vote.closes_at(tour) != closes:
        st.rerun()
    voted = len((tour.get("fan_vote") or {}).get("votes", {}))
    st.caption(f"{voted} of {len(tour['players'])} detectives have voted")


def _fan_vote_screen(tour, me, now):
    code = tour["code"]
    closes = fan_vote.closes_at(tour)
    st.title("The verdict is in…")
    st.markdown(art.heading("finish", "Vote for the fan favourite", size=34, level=2), unsafe_allow_html=True)
    st.caption("Who made this game more fun? Your votes decide podium place 3. "
               "You can't vote for yourself or for the two finalists.")
    seconds = max(1, int(closes - now + 0.999))
    st.markdown(art.countdown(f"fan_{int(closes)}", seconds, fan_vote.VOTE_SECONDS, "Vote closes in", urgent=3),
                unsafe_allow_html=True)
    _vote_watch(code, closes)

    mine = fan_vote.my_vote(tour, me)
    if mine is not None:
        name = html.escape(rules.find_player(tour, mine)["name"])
        st.markdown(art.banner("through", f"Vote counted for {name}! The podium is coming…"), unsafe_allow_html=True)
        return
    choices = fan_vote.candidates(tour, me)
    per_row = 3
    for start in range(0, len(choices), per_row):
        row = choices[start:start + per_row]
        key = art.css_key(f"grid_fan_{start}")
        st.markdown(art.phone_grid_style(key), unsafe_allow_html=True)
        with st.container(key=key):
            columns = st.columns(per_row)
        for column, pid in zip(columns, row):
            player = rules.find_player(tour, pid)
            button_key = art.css_key(f"fan_{pid}")
            with column:
                st.markdown(spectate._choice_style(button_key, [avatars.picture(player, 200)]), unsafe_allow_html=True)
                if st.button(common.player_label(player), key=button_key, width="stretch"):
                    _, message = storage.update(code, fan_vote.vote, me, pid, time.time())
                    st.toast(message)
                    st.rerun()


# --- the final stage: one yellow spotlight sweep, then the podium is revealed ------------

SPOT_ON = 0.9                                   # the podium has risen; the spotlight switches on
SWEEP = [(-32, .55), (30, .6), (-26, .62), (22, .65), (-15, .7), (10, .72), (-4, .7), (1.5, .6), (0, .5)]
REVEAL_OTHERS = 0.8                             # places 2 and 3 appear this long after the champion


def _spotlight_times():
    """(angles, arrival times) of the spotlight: wide sweeps over the stage and the
    crowd, each one smaller and slower, until it points straight down at place 1."""
    angles, times, t = [0], [SPOT_ON], SPOT_ON
    for angle, duration in SWEEP:
        t += duration
        angles.append(angle)
        times.append(t)
    return angles, times


def _stage_timeline():
    _, times = _spotlight_times()
    land = times[-1]                            # the light stops on place 1: the champion is revealed
    return land, land + REVEAL_OTHERS, land + REVEAL_OTHERS + 1.2


def _stage_offset(tour, end):
    """Seconds since the stage started for EVERYONE (it starts when the vote closes,
    which every phone knows), or None once it is long over. Redraws carry on."""
    elapsed = time.time() - fan_vote.closes_at(tour)
    return elapsed if elapsed < end + 3 else None


def _stage_css(offset):
    land, others, end = _stage_timeline()
    angles, times = _spotlight_times()
    total = times[-1]
    base = f"""
.r3-champion-title {{ position: relative; text-align: center; margin: .2rem 0 .6rem; min-height: 3.2rem;
    font-family: Cinzel, Georgia, serif; font-weight: 900; font-size: clamp(1.35rem, 5.4vw, 2.3rem); line-height: 1.15; color: #fff; }}
.r3-ct-wait, .r3-ct-done {{ display: block; }}
.r3-ct-done {{ background: linear-gradient(90deg, #ffe9a6, #fff, #ffe9a6); -webkit-background-clip: text; background-clip: text;
    color: transparent; filter: drop-shadow(0 0 14px #ffd76a); }}
.r3-stage {{ position: relative; max-width: 640px; margin: 0 auto 1rem; padding-top: 70px; overflow: hidden; border-radius: 22px;
    background: radial-gradient(ellipse 70% 30% at 50% 100%, #3a1e66, transparent 70%); }}
.r3-stage .r3-podium {{ position: relative; z-index: 2; margin: 0 0 0; }}
.r3-stage .r3-place {{ position: relative; overflow: hidden; }}
.r3-cover {{ position: absolute; inset: 0; z-index: 3; display: flex; align-items: center; justify-content: center;
    background: linear-gradient(160deg, #2a1550, #140a2a); border-radius: inherit;
    font-family: Cinzel, Georgia, serif; font-size: 2.6rem; font-weight: 900; color: #b48cff66; }}
.r3-floor {{ position: absolute; left: 4%; right: 4%; bottom: 10px; height: 90px; z-index: 0; border-radius: 50%;
    background: radial-gradient(ellipse at center, #5b2c9a 0, #2a1550 60%, transparent 72%); }}
.r3-crowd {{ position: relative; z-index: 4; display: flex; flex-wrap: wrap; justify-content: center; gap: 0 .2rem;
    margin: .5rem auto .4rem; max-width: 560px; padding-bottom: .6rem; }}
.r3-fan {{ width: 84px; text-align: center; animation: r3-idle 2.4s ease-in-out infinite; animation-delay: calc(var(--i) * -.37s); }}
.r3-fan:nth-child(even) {{ margin-top: 14px; }}
.r3-fan img {{ height: 86px; max-width: 100%; object-fit: contain; filter: drop-shadow(0 6px 8px #000a); }}
.r3-fan span {{ display: block; margin-top: -4px; color: #fff; font-size: .7rem; font-weight: 800; text-shadow: 0 1px 4px #000;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
@keyframes r3-idle {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-4px); }} }}
@keyframes r3-cheer {{ 0%,100% {{ transform: translateY(0) scale(1); }} 40% {{ transform: translateY(-16px) scale(1.05); }} }}
.r3-lamp {{ position: absolute; top: 4px; left: 50%; width: 34px; height: 22px; margin-left: -17px; z-index: 6;
    border-radius: 10px 10px 6px 6px; background: linear-gradient(#3b3550, #1b1726); box-shadow: 0 0 18px #ffd76a, inset 0 -5px 0 #ffd76a; }}
.r3-spot {{ position: absolute; top: 18px; left: 50%; width: 0; height: 350px; z-index: 5; transform-origin: 50% 0;
    pointer-events: none; }}
.r3-spot::before {{ content: ''; position: absolute; top: 0; left: -105px; width: 210px; height: 100%;
    clip-path: polygon(44% 0, 56% 0, 100% 100%, 0 100%); mix-blend-mode: screen; filter: blur(1.5px);
    background: linear-gradient(to bottom, rgba(255,240,170,.95), rgba(255,215,90,.45) 55%, rgba(255,210,80,.18)); }}
.r3-spot::after {{ content: ''; position: absolute; bottom: -18px; left: -110px; width: 220px; height: 44px; border-radius: 50%;
    background: radial-gradient(ellipse, rgba(255,226,120,.6), transparent 70%); mix-blend-mode: screen; }}
.r3-dim {{ position: absolute; inset: 0; z-index: 4; pointer-events: none; background: rgba(8,3,20,.55); opacity: 0; }}
@media (max-width: 560px) {{
  .r3-fan {{ width: 62px; }} .r3-fan img {{ height: 64px; }} .r3-fan span {{ font-size: .58rem; }}
  .r3-spot {{ height: 300px; }} .r3-spot::before {{ left: -80px; width: 160px; }} .r3-spot::after {{ left: -85px; width: 170px; }} }}
"""
    if offset is None:              # long over: everything simply in place, the light resting on the champion
        return base + """
.r3-stage .r3-podium { animation: none !important; } .r3-cover { display: none; } .r3-ct-wait { display: none; }
.r3-spot { transform: rotate(0deg); } .r3-place-one { box-shadow: 0 0 40px #ffd76a, inset 0 1px 25px rgba(255,255,255,.25) !important; }"""
    o = offset
    frames = " ".join(f"{100 * t / total:.2f}% {{ transform: rotate({a}deg); opacity: {0 if t < SPOT_ON else 1}; }}"
                      for a, t in zip([angles[0]] + angles, [0] + times))
    frames = frames.replace(f"{100 * SPOT_ON / total:.2f}% {{ transform: rotate(0deg); opacity: 0; }}",
                            f"{100 * SPOT_ON / total:.2f}% {{ transform: rotate(0deg); opacity: 1; }}")
    return base + f"""
@keyframes r3-spot-sweep {{ {frames} }}
@keyframes r3-flicker {{ 0% {{ opacity: 0; }} 20% {{ opacity: 1; }} 30% {{ opacity: .2; }} 45% {{ opacity: 1; }} 55% {{ opacity: .5; }} 70%,100% {{ opacity: 1; }} }}
@keyframes r3-gone {{ to {{ opacity: 0; visibility: hidden; }} }}
@keyframes r3-dim-in-out {{ 0% {{ opacity: 0; }} 15% {{ opacity: 1; }} 85% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}
@keyframes r3-show {{ from {{ opacity: 0; visibility: hidden; }} to {{ opacity: 1; visibility: visible; }} }}
@keyframes r3-champ-pop {{ 0% {{ transform: scale(1); }} 45% {{ transform: scale(1.08); box-shadow: 0 0 60px #ffd76a; }}
                           100% {{ transform: scale(1); box-shadow: 0 0 40px #ffd76a, inset 0 1px 25px rgba(255,255,255,.25); }} }}
.r3-stage .r3-podium {{ animation: r3-podium-rise .9s cubic-bezier(.2,.8,.2,1) {-o:.2f}s both !important; }}
.r3-spot {{ animation: r3-spot-sweep {total:.2f}s ease-in-out {-o:.2f}s both; }}
.r3-lamp {{ animation: r3-flicker .5s linear {SPOT_ON - .3 - o:.2f}s both; }}
.r3-dim {{ animation: r3-dim-in-out {land + .6:.2f}s linear {-o:.2f}s both; }}
.r3-place-one .r3-cover {{ animation: r3-gone .35s ease-out {land - o:.2f}s both; }}
.r3-place-two .r3-cover, .r3-place-three .r3-cover {{ animation: r3-gone .35s ease-out {others - o:.2f}s both; }}
.r3-place-one {{ animation: r3-champ-pop .7s ease-out {land - o:.2f}s both; }}
.r3-ct-wait {{ animation: r3-gone .01s {land - o:.2f}s both; position: absolute; left: 0; right: 0; }}
.r3-ct-done {{ animation: r3-show .5s ease-out {land - o:.2f}s both; }}
.r3-stage .r3-confetti, .mm-calls {{ animation: r3-show .4s {others - o:.2f}s both; }}
.r3-fan {{ animation: r3-idle 2.4s ease-in-out calc(var(--i) * -.37s) infinite, r3-cheer .45s ease-out {land + .1 - o:.2f}s 4; }}
"""


def _final_stage(tour, me, now):
    state = tour["round3"]
    winner = rules.find_player(tour, state["winner"])
    land, others, end = _stage_timeline()
    offset = _stage_offset(tour, end)

    # Title first (the most important line), hidden behind "…" until the light lands.
    champion = ("You are the Mastermind champion!" if me == state["winner"]
                else f"{html.escape(winner['name'])} is the Mastermind champion!")
    st.markdown(f"<style>{_stage_css(offset)}</style>"
                f"<div class='r3-champion-title'><span class='r3-ct-wait'>And the Mastermind champion is…</span>"
                f"<span class='r3-ct-done'>{champion}</span></div>", unsafe_allow_html=True)

    # The podium: 1 champion, 2 the other finalist, 3 the fan favourite.
    finalists = [rules.find_player(tour, pid) for pid in state["finalists"]]
    runner_up = next((p for p in finalists if p and p["id"] != winner["id"]), None)
    third = fan_vote.favourite(tour)
    fan = rules.find_player(tour, third[0]) if third else None
    places = []
    if runner_up:
        places.append(_podium_place(runner_up, 2, "Finalist", "r3-place-two"))
    places.append(_podium_place(winner, 1, "Mastermind champion", "r3-place-one"))
    if fan:
        note = f"Fan favourite · {third[1]} vote{'s' if third[1] != 1 else ''}" if third[1] else third[2]
        places.append(_podium_place(fan, 3, note, "r3-place-three"))

    # Everyone else stands in the crowd in front of the podium.
    on_podium = {p["id"] for p in (winner, runner_up, fan) if p}
    crowd = "".join(
        f"<div class='r3-fan' style='--i:{k}'><img src='{avatars.picture(p, 200)}' alt=''><span>{html.escape(p['name'])}</span></div>"
        for k, p in enumerate(p for p in tour["players"] if p["id"] not in on_podium))
    confetti = "".join(f"<i style='--x:{x}%;--c:{colour};animation-delay:{delay}s'></i>" for x, colour, delay in
                       ((8, '#f7d84a', 0), (19, '#f07bda', .4), (31, '#89e4ff', .8), (45, '#fff', .2),
                        (58, '#f7d84a', 1), (71, '#b990ff', .55), (86, '#6ff0c1', .95)))
    st.markdown("<div class='r3-stage'><div class='r3-floor'></div><div class='r3-lamp'></div><div class='r3-spot'></div>"
                f"<div class='r3-confetti'>{confetti}</div><div class='r3-podium'>{''.join(places)}</div>"
                f"<div class='r3-dim'></div><div class='r3-crowd'>{crowd}</div></div>", unsafe_allow_html=True)


def _podium_place(player, place, note, css_class):
    """One podium block (the team's design), with a cover that hides who stands on it
    until the spotlight reveals it."""
    return (f"<div class='r3-place {css_class}'><div class='r3-cover'>?</div><img src='{avatars.picture(player, 240)}' alt=''>"
            f"<div class='r3-place-number'>{place}</div><div class='r3-place-name'>{html.escape(player['name'])}</div>"
            f"<div class='r3-place-note'>{html.escape(note)}</div></div>")


def _solution_cards():
    """A visual recap makes the final reveal match the case-file style."""
    items = (("Thief", "Nova", CASE_IMAGES["Nova"], ""),
             ("Hiding place", "Conservatory", CASE_IMAGES["Conservatory"], ""),
             ("Object", "Map", None, "🗺️"))
    cards = []
    for kind, value, path, icon in items:
        visual = (f"<img src='{_image_data_url(path)}' alt='{value}'>" if path else
                  f"<div class='r3-solution-icon' aria-label='{value}'>{icon}</div>")
        cards.append(f"<div class='r3-solution-card'>{visual}<div class='r3-solution-kind'>{kind}</div><div class='r3-solution-value'>{value}</div></div>")
    return "<div class='r3-solution-grid'>" + "".join(cards) + "</div>"
