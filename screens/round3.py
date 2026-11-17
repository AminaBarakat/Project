"""The purple, story-led two-finalist screen for Round 3."""

import base64
import html
from pathlib import Path
import time

import streamlit as st

import round1 as r1
import round3 as r3
import storage
import tournament as rules
from screens import common

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
    .r3-case-card img { background:transparent; border-radius:11px; display:block; height:136px; mix-blend-mode:multiply; object-fit:contain; width:100%; }
    .r3-case-card span { color:#f8f2ff; display:block; font-family:ui-sans-serif, system-ui, sans-serif; font-weight:800; padding:.45rem .15rem .12rem; }
    .r3-object-card { align-items:center; background:rgba(19,8,39,.58); border:1px solid rgba(220,190,255,.38); border-radius:16px; display:flex; gap:.55rem; justify-content:center; min-height:82px; padding:.6rem; }
    .r3-object-card b { color:#f8f2ff; font-family:ui-sans-serif, system-ui, sans-serif; }
    .r3-choice-label { color:#f8f2ff; font-family:ui-sans-serif, system-ui, sans-serif; font-size:1rem; font-weight:800; margin:.9rem 0 .35rem; }
    .r3-choice-help { color:#d9c2ec; font-size:.88rem; margin-bottom:.55rem; }
    .r3-podium { align-items:end; display:flex; gap:clamp(.55rem, 3vw, 1.4rem); justify-content:center; margin:1.7rem 0 2rem; min-height:300px; }
    .r3-place { background:linear-gradient(145deg, rgba(109, 75, 164, .7), rgba(29, 55, 107, .65)); border:1px solid rgba(202, 229, 255, .48); border-radius:18px 18px 5px 5px; box-shadow:inset 0 1px 18px rgba(246, 235, 255, .14), 0 12px 24px rgba(0,0,0,.24); display:flex; flex-direction:column; justify-content:flex-end; padding:.75rem .55rem; text-align:center; width:min(29vw, 190px); }
    .r3-place-one { background:linear-gradient(145deg, rgba(157, 91, 224, .88), rgba(39, 91, 180, .83)); box-shadow:0 0 34px rgba(213, 170, 255, .8), inset 0 1px 25px rgba(255,255,255,.25); min-height:235px; position:relative; }
    .r3-place-two { min-height:180px; } .r3-place-three { min-height:145px; }
    .r3-place-number { color:#fff; font-family:Cinzel, Georgia, serif; font-size:1.55rem; font-weight:900; text-shadow:0 0 10px #a86bff; }
    .r3-place-one .r3-place-number { font-size:2.1rem; } .r3-place-name { color:#fff; font-family:ui-sans-serif, system-ui, sans-serif; font-size:.94rem; font-weight:850; margin-top:.38rem; overflow-wrap:anywhere; }
    .r3-place-note { color:#e4d8f2; font-size:.7rem; line-height:1.25; margin-top:.18rem; } .r3-place img { height:76px; margin:0 auto; object-fit:contain; width:76px; }
    .r3-place-one img { filter:drop-shadow(0 0 10px #fff3a2); height:104px; width:104px; }
    .r3-confetti { height:0; position:relative; z-index:3; } .r3-confetti i { animation:r3-confetti 2.8s linear infinite; background:var(--c); display:block; height:10px; left:var(--x); position:absolute; top:-10px; transform:rotate(20deg); width:6px; }
    @keyframes r3-confetti { 0% { opacity:0; transform:translateY(-20px) rotate(0deg) } 12% { opacity:1 } 100% { opacity:0; transform:translateY(260px) rotate(520deg) } }
    @media (max-width: 620px) { .r3-case-grid { grid-template-columns:1fr; } .r3-case-card img { height:175px; } }
    @media (max-width: 520px) { .r3-podium { gap:.35rem; } .r3-place { width:31vw; padding:.55rem .25rem; } .r3-place img { height:58px; width:58px; } .r3-place-one img { height:76px; width:76px; } .r3-place-name { font-size:.78rem; } }
    @media (max-width: 620px) { .r3-scene { grid-template-columns: 1fr; gap: 0; padding: .2rem 1rem 0; }
      .r3-detective { width: 180px; margin-bottom: -1rem; } .r3-speech { min-height: 170px; } }
    @keyframes r3-bob { 0%,100% { transform: translateY(0) } 50% { transform: translateY(-7px) } }
    @keyframes r3-talk { from { transform: scaleY(.55) } to { transform: scaleY(1.6) } }
    @keyframes r3-blink { 50% { opacity: 0 } }
    </style>
    """, unsafe_allow_html=True)


def show(code, me):
    _live_round(code, me)


@st.fragment(run_every="0.5s")
def _live_round(code, me):
    now = time.time()
    tour, _ = storage.update(code, r3.settle, now)
    if tour is None:
        st.error("This tournament could not be found.")
        return
    if tour["status"] not in ("round3", "round3_results", "finished"):
        st.rerun(scope="app")

    _story_style()
    if tour["status"] == "round3" and "starts_at" in tour["round3"] and tour["round3"]["starts_at"] is None:
        _story(tour, code, me, now)
    elif tour["status"] == "round3":
        _mystery(tour, code, me, now)
    else:
        _results(tour, me)


def _story(tour, code, me, now):
    text = html.escape(r3.story_text(tour, now)).replace("\n", "<br>")
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

    if not r3.story_finished(tour, now):
        st.caption("The detective is briefing the finalists…")
        return

    st.markdown(f"<div class='r3-question'>{r3.FINAL_QUESTION}</div>", unsafe_allow_html=True)
    if r3.is_finalist(tour, me):
        if st.button("Open the final case", type="primary", width="stretch"):
            _, message = storage.update(code, r3.start_investigation, me, time.time())
            st.toast(message)
            st.rerun(scope="app")
    else:
        st.info("The finalists will open the final case when they are ready.")


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
    st.markdown("<div class='r3-case-intro'>Study the people, the rooms, and the clues before you present your theory.</div>", unsafe_allow_html=True)
    suspects = "".join(
        f"<div class='r3-case-card'><img src='{_image_data_url(CASE_IMAGES[name])}' alt='{name}'><span>{name}</span></div>"
        for name in r3.SUSPECTS
    )
    rooms = "".join(
        f"<div class='r3-case-card'><img src='{_image_data_url(CASE_IMAGES[name])}' alt='{name}'><span>{name}</span></div>"
        for name in r3.ROOMS
    )
    objects = "".join(
        f"<div class='r3-object-card'><span>{icon}</span><b>{name}</b></div>"
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

    suspect = _theory_choice_cards(code, "suspect", "Who stole the Star Key?", r3.SUSPECTS)
    room = _theory_choice_cards(code, "room", "Where did they hide it?", r3.ROOMS)
    object_name = _theory_choice_cards(code, "object", "What object did they carry?", r3.OBJECTS)
    if st.button("Submit theory", type="primary"):
        after, message = storage.update(code, r3.answer, me, suspect, room, object_name, time.time())
        if after is not None and after["status"] == "round3_results":
            st.rerun(scope="app")
        st.error(message) if message.startswith("Not quite") else st.toast(message)
        st.rerun(scope="fragment")


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
                st.rerun()
    return st.session_state[state_key]


def _results(tour, me):
    state = tour["round3"]
    winner = rules.find_player(tour, state["winner"])
    st.title("The Star Key is found")
    _podium(tour, winner)
    if me == state["winner"]:
        st.success("🏆 You are the Mastermind champion!")
    else:
        st.success(f"🏆 {common.player_label(winner)} is the Mastermind champion!")

    st.subheader("Solution")
    st.markdown("- **Thief:** Nova\n- **Hiding place:** Conservatory\n- **Object:** Map")
    st.info("Portrait number for Nova: **3** · Conservatory room: **1** · Map clue: **8**  \n### Final vault code: `318`")
    st.caption(f"Winner decided by: {state['decided_by']}.")


def _podium(tour, winner):
    """Celebrate the champion and two real, non-invented honours."""
    finalists = [rules.find_player(tour, player_id) for player_id in tour["round3"]["finalists"]]
    runner_up = next((player for player in finalists if player and player["id"] != winner["id"]), None)
    excluded = {winner["id"]} | ({runner_up["id"]} if runner_up else set())
    candidates = [player for player in tour["players"] if player["id"] not in excluded]
    if tour.get("round1") and candidates:
        honourable = min(candidates, key=lambda player: (-r1.points(tour, player["id"]), r1.total_seconds(tour, player["id"]), player["name"].casefold()))
    else:
        honourable = candidates[0] if candidates else None

    confetti = "".join(f"<i style='--x:{x}%;--c:{colour};animation-delay:{delay}s'></i>" for x, colour, delay in ((8, '#f7d84a', 0), (19, '#f07bda', .4), (31, '#89e4ff', .8), (45, '#fff', .2), (58, '#f7d84a', 1), (71, '#b990ff', .55), (86, '#6ff0c1', .95)))
    places = []
    if runner_up:
        places.append(_podium_place(runner_up, 2, "Finalist", "r3-place-two"))
    places.append(_podium_place(winner, 1, "Mastermind champion", "r3-place-one"))
    if honourable:
        places.append(_podium_place(honourable, 3, "Round 1 ace", "r3-place-three"))
    st.markdown(f"<div class='r3-confetti'>{confetti}</div><div class='r3-podium'>{''.join(places)}</div>", unsafe_allow_html=True)


def _podium_place(player, place, note, css_class):
    _, path = common.AVATARS.get(player.get("appearance"), common.AVATARS["girl"])
    return (f"<div class='r3-place {css_class}'><img src='{common.avatar_data_url(path)}' alt=''>"
            f"<div class='r3-place-number'>{place}</div><div class='r3-place-name'>{html.escape(player['name'])}</div>"
            f"<div class='r3-place-note'>{note}</div></div>")
