"""The purple, story-led two-finalist screen for Round 3."""

import base64
import html
from pathlib import Path
import time

import streamlit as st

import round3 as r3
import storage
import tournament as rules
from screens import common

DETECTIVE_IMAGE = Path(__file__).resolve().parents[1] / "assets" / "detective-purple.png"


def _detective_data_url():
    """A local asset as a data URL so it also works after Streamlit deployment."""
    encoded = base64.b64encode(DETECTIVE_IMAGE.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _story_style():
    st.markdown("""
    <style>
    .r3-story { background: radial-gradient(circle at 50% 25%, #44216b 0%, #160b2d 47%, #090515 100%);
      border: 1px solid #8856cb; border-radius: 24px; min-height: 590px; overflow: hidden; padding: 1.2rem 1.2rem 0; }
    .r3-story-kicker { color: #d8b9ff; font-size: .78rem; font-weight: 700; letter-spacing: .16em; text-align: center; }
    .r3-detective { width: 230px; margin: .3rem auto -2.3rem; position: relative; animation: r3-bob 2.3s ease-in-out infinite; }
    .r3-detective img { width: 100%; display: block; filter: drop-shadow(0 0 20px #b249f7); }
    .r3-mouth { position: absolute; width: 19px; height: 5px; left: 47%; top: 25.1%; background: #57213a;
      border-radius: 0 0 12px 12px; animation: r3-talk .34s ease-in-out infinite alternate; }
    .r3-speech { background: rgba(9, 5, 21, .86); border: 1px solid rgba(214, 169, 255, .55); border-radius: 17px;
      color: #f7eeff; font-family: Georgia, serif; font-size: 1.14rem; line-height: 1.55; min-height: 168px; padding: 1.15rem 1.25rem; }
    .r3-cursor { color: #e6a7ff; animation: r3-blink .75s step-end infinite; }
    .r3-question { color: #fff; font-family: Georgia, serif; font-size: 1.5rem; font-style: italic; line-height: 1.35;
      padding: 1.2rem .3rem .2rem; text-align: center; }
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
    st.markdown(f"""
    <div class="r3-story">
      <div class="r3-story-kicker">FINAL MANSION MYSTERY · CASE FILE 03</div>
      <div class="r3-detective"><img src="{_detective_data_url()}" alt="The detective briefing the finalists"><span class="r3-mouth"></span></div>
      <div class="r3-speech">{text}<span class="r3-cursor">▍</span></div>
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


def _mystery(tour, code, me, now):
    state = tour["round3"]
    st.title("Round 3: Final Mansion Mystery")

    left = r3.seconds_left(tour, now)
    st.markdown(f"### ⏱️ {left // 60}:{left % 60:02d}")
    st.progress(left / r3.ROUND_SECONDS)

    st.subheader("Case file")
    st.markdown("**Suspects:** Nova · Theo · Mira  \n**Rooms:** Library · Observatory · Conservatory  \n**Objects:** Key · Map · Flashlight")
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

    suspect = st.selectbox("Who stole the Star Key?", r3.SUSPECTS, key=f"r3_{code}_suspect")
    room = st.selectbox("Where did they hide it?", r3.ROOMS, key=f"r3_{code}_room")
    object_name = st.selectbox("What object did they carry?", r3.OBJECTS, key=f"r3_{code}_object")
    if st.button("Submit theory", type="primary"):
        after, message = storage.update(code, r3.answer, me, suspect, room, object_name, time.time())
        if after is not None and after["status"] == "round3_results":
            st.rerun(scope="app")
        st.error(message) if message.startswith("Not quite") else st.toast(message)
        st.rerun(scope="fragment")


def _results(tour, me):
    state = tour["round3"]
    winner = rules.find_player(tour, state["winner"])
    st.title("The Star Key is found")
    if me == state["winner"]:
        st.success("🏆 You are the Mastermind champion!")
    else:
        st.success(f"🏆 {common.player_label(winner)} is the Mastermind champion!")

    st.subheader("Solution")
    st.markdown("- **Thief:** Nova\n- **Hiding place:** Conservatory\n- **Object:** Map")
    st.info("Portrait number for Nova: **3** · Conservatory room: **1** · Map clue: **8**  \n### Final vault code: `318`")
    st.caption(f"Winner decided by: {state['decided_by']}.")
