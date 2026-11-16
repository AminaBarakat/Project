"""The two-finalist screen for Round 3: Final Mansion Mystery."""

import time

import streamlit as st

import round3 as r3
import storage
import tournament as rules
from screens import common


def show(code, me):
    _live_round(code, me)


@st.fragment(run_every="1s")
def _live_round(code, me):
    now = time.time()
    tour, _ = storage.update(code, r3.settle, now)
    if tour is None:
        st.error("This tournament could not be found.")
        return
    if tour["status"] not in ("round3", "round3_results", "finished"):
        st.rerun(scope="app")

    if tour["status"] == "round3":
        _mystery(tour, code, me, now)
    else:
        _results(tour, me)


def _mystery(tour, code, me, now):
    state = tour["round3"]
    st.title("Round 3: Final Mansion Mystery")
    st.caption("The earlier games were security tests inside the mansion. During the final blackout, someone stole the Star Key.")

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
