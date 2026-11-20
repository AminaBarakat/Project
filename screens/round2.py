"""Round 2 on each phone. Shared progress is re-read from storage every 2 seconds."""

import html
import math
import time

import streamlit as st

import round2 as rules
import storage
import tournament
from screens import art, common, spectate

REFRESH = "2s"

def show(code, me):
    # Spectators: crowd bar + reactions at the top, their own buttons at the bottom.
    tour = spectate.start(code, me)
    _live_round(code, me)
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
    st.markdown("""
    <style>
    .r2-clue-paper {
      position: relative; margin: .8rem 0 1rem; padding: 1.45rem 1.35rem;
      border: 2px solid #9a5c2a; border-radius: 22px 15px 20px 14px;
      color: #432a17;
      background:
        radial-gradient(ellipse at 7% 12%, rgba(108,57,20,.2), transparent 23%),
        radial-gradient(ellipse at 90% 86%, rgba(108,57,20,.18), transparent 21%),
        repeating-linear-gradient(0deg, transparent 0 31px, rgba(105,67,33,.055) 32px 33px),
        linear-gradient(100deg, #d7b274 0%, #f2dfb8 11%, #f7eacb 48%, #edd6a7 88%, #cf9f61 100%);
      box-shadow: 0 9px 22px rgba(0,0,0,.28), inset 0 0 23px rgba(116,68,26,.28);
    }
    .r2-clue-paper::before, .r2-clue-paper::after {
      content: ""; position: absolute; left: 1rem; right: 1rem; height: 9px;
      border-radius: 50%; pointer-events: none;
    }
    .r2-clue-paper::before {
      top: -7px; border-top: 3px solid rgba(115,65,27,.72);
      box-shadow: 0 3px 5px rgba(74,42,18,.24);
    }
    .r2-clue-paper::after {
      bottom: -7px; border-bottom: 3px solid rgba(115,65,27,.58);
    }
    .r2-clue-paper-text {
      font-family: Georgia, 'Times New Roman', serif; font-size: 1.08rem;
      font-weight: 700; line-height: 1.65; white-space: pre-line;
      text-shadow: 0 1px rgba(255,248,225,.35);
    }
    @media(max-width:560px) {
      .r2-clue-paper { padding: 1.1rem .95rem; }
      .r2-clue-paper-text { font-size: 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown(
        f"<div class='r2-clue-paper' role='note'><div class='r2-clue-paper-text'>{html.escape(view['card'])}</div></div>",
        unsafe_allow_html=True,
    )
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
    st.markdown(f"""
    <style>
    .r2-vault-entry {{ margin: .7rem auto .35rem; text-align: center; }}
    .r2-vault-entry-title {{ color: #f3e6ff; font-family: Cinzel, Georgia, serif;
      font-size: 1.15rem; font-weight: 800; letter-spacing: .08em;
      margin-bottom: -.35rem; text-shadow: 0 0 10px rgba(186,115,255,.7); }}
    .st-key-{input_class} {{ max-width: 440px; margin: 0 auto .8rem; }}
    </style>
    """, unsafe_allow_html=True)
    with st.form(f"r2_{code}_vault_form", clear_on_submit=False):
        st.markdown(
            "<div class='r2-vault-entry'><div class='r2-vault-entry-title'>Type the code</div>"
            + art.img(art.padlock(["?", "?", "?", "?"]), width="220px")
            + "</div>",
            unsafe_allow_html=True,
        )
        value = st.text_input(
            "Type the code", max_chars=4, type="password", placeholder="Enter 4 digits",
            label_visibility="collapsed", key=f"r2_{code}_vault_code",
        )
        submitted = st.form_submit_button("Unlock", type="primary")
    if submitted:
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

