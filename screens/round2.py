"""Round 2 on each phone. Shared progress is re-read from storage every 2 seconds."""

import math
import time

import streamlit as st

import round2 as rules
import storage
import tournament
from screens import art, common

REFRESH = "2s"

def show(code, me):
    _live_round(code, me)


@st.fragment(run_every=REFRESH)
def _live_round(code, me):
    now = time.time()                         # server clock; never accept a browser timestamp
    tour, _ = storage.update(code, rules.settle, now)
    if tour is None:
        st.error("This tournament is no longer available.")
        return
    if tour["status"] not in ("round2", "final"):
        st.rerun(scope="app")

    view = rules.player_view(tour, me)
    if tour["status"] == "final":
        _end_screen(code, tour, me, view)
        return
    if view.get("duo_id") is None:
        st.title("Round 2: Duo Vault Challenge")
        st.info("You were eliminated in Round 1. You can watch the challenge here.")
        return

    st.title("Round 2: Duo Vault Challenge")
    st.caption("Three minutes. Combine your clues, open the vault, then find the safe route.")
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
    st.info(view["card"])
    st.caption("Read your clue aloud to your teammate. Each phone receives only its player's card.")

    locked_until = view.get("locked_until")
    if locked_until is not None and now < locked_until:
        left = max(1, math.ceil(locked_until - now))
        st.warning(f"Alarm lockout: wait {left} seconds before submitting again.")
        return

    if view["code_solved_at"] is None:
        _code_form(code, me, view["duo_id"])
    else:
        st.success("Vault code solved. Your teammate sees this progress too.")
        _map(code, me, view)

    st.info("The other duo is still in the challenge. First to reach the Rooftop advances.")


def _feedback_key(code):
    return f"r2_{code}_feedback"


def _show_feedback(code, message):
    if message.startswith(("Vault unlocked", "Safe choice", "Rooftop reached")):
        kind = "success"
    elif message.startswith(("Wrong code", "Alarm")):
        kind = "error"
    else:
        kind = "info"
    st.session_state[_feedback_key(code)] = (kind, message, time.time() + 8)
    st.rerun(scope="fragment")


def _code_form(code, me, duo_id):
    with st.form(f"r2_{code}_vault_form", clear_on_submit=False):
        number = st.number_input("Vault code (exactly 4 digits)", min_value=0, max_value=99999,
                                 value=None, step=1, format="%d", placeholder="Enter the digits")
        submitted = st.form_submit_button("Unlock the vault", type="primary")
    if submitted:
        value = "" if number is None else str(number)
        _, message = storage.update(code, rules.submit_code, me, duo_id, value, time.time())
        _show_feedback(code, message)


def _map(code, me, view):
    route_step = view["route_step"]
    route = rules.SAFE_ROUTE[:route_step + 1]
    st.subheader("Choose a safe route")
    st.markdown(" → ".join(f"**{place}**" for place in route))
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
        if column.button(f"🚪 {door}", key=f"r2_{code}_{here}_{door}", width="stretch"):
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
        st.caption("The round ended at its server-set three-minute limit.")

