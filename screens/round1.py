"""Round 1 on a player's phone: intro → board (3 min) → waiting room / tie-breaker → results.

The whole screen is a fragment that reruns every second. Each time, it asks
storage to `settle` the round (apply anything that's due, like time running out)
and then draws whatever this player should see right now.

Things only this phone needs to remember (which challenge is open, the route
clicked so far, when the memory items were shown) live in st.session_state.
Everything shared lives in the database.
"""

import time

import streamlit as st

import round1 as r1
import storage
import tournament as rules
from screens import common, duels

MEMORY_SHOW_SECONDS = 5

WAITING_LINES = [
    "Dusting the bookshelves for fingerprints…",
    "Checking who had the key last…",
    "Comparing the witness statements…",
    "Following muddy footprints down the hall…",
    "Counting the portraits in the gallery…",
]


def show(code, me):
    _live_round(code, me)


@st.fragment(run_every="1s")
def _live_round(code, me):
    now = time.time()
    tour, _ = storage.update(code, r1.settle, now)
    if tour is None or tour["status"] not in ("round1", "round1_results"):
        st.rerun(scope="app")                 # Round 2, or the tournament vanished

    phase = r1.phase(tour, me, now)
    if phase == "intro":
        _intro(tour, me, now)
    elif phase == "playing":
        _board(tour, code, me, now)
    elif phase == "tiebreak":
        _tiebreak(tour, code, me, now)
    elif phase == "waiting":
        _waiting(tour, me, now)
    else:
        _results(tour, me, now)


# --- intro ------------------------------------------------------------------------

def _intro(tour, me, now):
    st.title("Round 1: The Challenge Board")
    opponent = rules.opponent_of(tour, me)
    you = rules.find_player(tour, me)
    st.markdown("### Your first suspect is… your opponent.")
    st.markdown(common.duel_card(you, opponent), unsafe_allow_html=True)
    left = max(0, int(tour["round1"]["starts_at"] - now + 0.999))
    st.markdown(f"### Starting in {left}…")
    st.caption("Four challenges, three minutes, one point each. Highest score goes through.")
    st.divider()
    duels.show_bracket(tour, me)


# --- the board -------------------------------------------------------------------

def _key(code, name):
    """session_state keys are per tournament, so an old game never leaks into a new one."""
    return f"r1_{code}_{name}"


def _board(tour, code, me, now):
    seconds = r1.seconds_left(tour, now)
    answers = tour["round1"]["boards"][me]["answers"]

    top_left, top_right = st.columns([3, 1])
    top_left.markdown(f"### ⏱️ {seconds // 60}:{seconds % 60:02d}")
    top_right.markdown(f"### {len(answers)}/4")
    st.progress(seconds / r1.ROUND_SECONDS)

    open_key = _key(code, "open")
    opened = st.session_state.get(open_key)
    if opened in answers:
        opened = None

    if opened is None:
        st.write("Pick a challenge:")
        tiles = list(r1.CHALLENGES.items())
        for row in (tiles[:2], tiles[2:]):
            columns = st.columns(2)
            for column, (cid, title) in zip(columns, row):
                if cid in answers:
                    column.button(f"{title}  {'✅' if answers[cid] else '❌'}",
                                  key=f"tile_{cid}", disabled=True, width="stretch")
                elif column.button(title, key=f"tile_{cid}", width="stretch"):
                    st.session_state[open_key] = cid
                    st.rerun(scope="fragment")
        return

    st.subheader(r1.CHALLENGES[opened])
    if opened == "number_lock":
        _number_lock(code, me)
    elif opened == "pattern":
        _pattern(code, me)
    elif opened == "escape_route":
        _escape_route(code, me)
    elif opened == "memory":
        _memory(code, me, now)

    if opened != "memory" and st.button("← Back to the board"):
        st.session_state[open_key] = None
        st.rerun(scope="fragment")


def _submit(code, me, challenge_id, value):
    tour, message = storage.update(code, r1.answer, me, challenge_id, value, time.time())
    answered = tour is not None and challenge_id in tour["round1"]["boards"][me]["answers"]
    if answered:
        st.session_state[_key(code, "open")] = None
        st.toast(message)
        st.rerun(scope="fragment")
    else:
        st.error(message)


def _number_lock(code, me):
    for guess, clue in r1.NUMBER_LOCK_CLUES:
        st.markdown(f"`{guess}`  {clue}")
    with st.form(_key(code, "lock_form"), clear_on_submit=False):
        value = st.text_input("The 3-digit code", max_chars=3, placeholder="e.g. 123")
        if st.form_submit_button("🔓 Unlock", type="primary"):
            _submit(code, me, "number_lock", value)


def _pattern(code, me):
    grid = "\n".join("  ".join(row) for row in r1.PATTERN_GRID)
    st.code(grid, language=None)
    st.write("Which symbol goes in the empty space?")
    columns = st.columns(3)
    for column, (option, symbol) in zip(columns, r1.PATTERN_OPTIONS.items()):
        if column.button(symbol, key=f"pattern_{option}", width="stretch"):
            _submit(code, me, "pattern", option)


def _escape_route(code, me):
    for clue in r1.ESCAPE_CLUES:
        st.markdown(f"- {clue}")
    route_key = _key(code, "route")
    route = st.session_state.get(route_key, [])
    here = route[-1] if route else "Start"
    st.markdown(f"**You are in:** {here}" + (f"  ({' → '.join(['Start'] + route)})" if route else ""))
    st.caption("Choose carefully, there's no going back.")
    columns = st.columns(2)
    for column, room in zip(columns, r1.ESCAPE_MAP[here]):
        if column.button(f"🚪 {room}", key=f"room_{here}_{room}", width="stretch"):
            new_route = route + [room]
            if room in r1.ESCAPE_MAP:          # not a dead end yet: keep walking
                st.session_state[route_key] = new_route
                st.rerun(scope="fragment")
            else:
                st.session_state[route_key] = []
                _submit(code, me, "escape_route", new_route)


def _memory(code, me, now):
    shown_key = _key(code, "memory_shown_at")
    shown_at = st.session_state.get(shown_key)
    if shown_at is None:
        st.write(f"You'll see six objects for {MEMORY_SHOW_SECONDS} seconds. Remember them!")
        if st.button("Show me", type="primary"):
            st.session_state[shown_key] = now
            st.rerun(scope="fragment")
        if st.button("← Back to the board"):
            st.session_state[_key(code, "open")] = None
            st.rerun(scope="fragment")
        return

    left = int(shown_at + MEMORY_SHOW_SECONDS - now + 0.999)
    if left > 0:
        st.markdown("## " + " · ".join(r1.MEMORY_ITEMS))
        st.caption(f"Hiding in {left}…")
        return

    remaining = [item for item in r1.MEMORY_ITEMS if item != r1.MEMORY_ANSWER]
    st.markdown("Now there are only these:  \n**" + " · ".join(remaining) + "**")
    st.write("Which one is missing?")
    columns = st.columns(3)
    for k, item in enumerate(r1.MEMORY_ITEMS):
        if columns[k % 3].button(item, key=f"memory_{item}", width="stretch"):
            _submit(code, me, "memory", item)


# --- tie-breaker -----------------------------------------------------------------

def _tiebreak(tour, code, me, now):
    opponent = rules.opponent_of(tour, me)
    points = r1.score(tour, me)
    st.title("⚖️ It's a tie!")
    st.markdown(f"You and {common.player_label(opponent)} both scored **{points}/4**. "
                "One question decides it. If you're both right, the faster one wins.")
    seconds = r1.tiebreak_seconds_left(tour, me, now)
    st.markdown(f"### ⏱️ {seconds}s")
    st.progress(seconds / r1.TIEBREAK_SECONDS)
    st.info(r1.TIEBREAK_QUESTION)
    with st.form(_key(code, "tiebreak_form")):
        value = st.text_input("Your answer", max_chars=4)
        if st.form_submit_button("Lock it in", type="primary"):
            _, message = storage.update(code, r1.answer_tiebreak, me, value, time.time())
            st.toast(message)
            st.rerun(scope="fragment")


# --- waiting room --------------------------------------------------------------

_WAITING_ANIMATION = """
<style>
.mm-wait { text-align:center; padding: 1.5rem 0 0.5rem; }
.mm-glass { display:inline-block; font-size:4.5rem; animation: mm-search 2.4s ease-in-out infinite; }
.mm-prints { font-size:1.4rem; letter-spacing:0.8rem; opacity:0.6; }
.mm-prints span { animation: mm-fade 2.4s infinite; }
.mm-prints span:nth-child(2) { animation-delay: .4s } .mm-prints span:nth-child(3) { animation-delay: .8s }
.mm-prints span:nth-child(4) { animation-delay: 1.2s } .mm-prints span:nth-child(5) { animation-delay: 1.6s }
@keyframes mm-search { 0%,100% { transform: translateX(-70px) rotate(-12deg); }
                       50% { transform: translateX(70px) rotate(12deg); } }
@keyframes mm-fade { 0%,100% { opacity: .15 } 50% { opacity: 1 } }
</style>
<div class="mm-wait">
  <div class="mm-glass">🔍</div>
  <div class="mm-prints"><span>👣</span><span>👣</span><span>👣</span><span>👣</span><span>👣</span></div>
</div>
"""


def _waiting(tour, me, now):
    st.title("Case file closed")
    st.markdown(f"You solved **{r1.score(tour, me)}/4**. Now we wait for the others…")
    # Static HTML only: no player names in here, so nothing typed by a player gets in.
    st.markdown(_WAITING_ANIMATION, unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center'><em>{WAITING_LINES[int(now / 3) % len(WAITING_LINES)]}</em></p>",
                unsafe_allow_html=True)

    done = r1.finished_count(tour)
    total = len(tour["round1"]["boards"])
    st.progress(done / total, text=f"{done} of {total} detectives have finished")
    seconds = r1.seconds_left(tour, now)
    st.caption(f"The round closes in {seconds // 60}:{seconds % 60:02d} at the latest.")


# --- results ---------------------------------------------------------------------

_HOW = {"score": "", "tie-breaker": " · won the tie-breaker",
        "fastest answer": " · faster on the tie-breaker", "draw": " · decided by a draw"}


def _results(tour, me, now):
    st.title("Which detectives made it out?")
    if me in tour["eliminated"]:
        st.error("💀 You've been eliminated. Stay and watch the rest of the game!")
    else:
        st.success("🎉 You're through to Round 2!")

    cards = []
    for number, result in enumerate(tour["round1"]["results"], start=1):
        winner = rules.find_player(tour, result["winner"])
        loser = rules.find_player(tour, result["loser"])
        points = result["points"]
        how = f" · {points[result['winner']]}–{points[result['loser']]}{_HOW[result['decided_by']]}"
        cards.append(common.result_duel_card(number, winner, loser, how))
    st.markdown("<div class='mm-results-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)

    left = r1.results_seconds_left(tour, now)
    st.divider()
    st.markdown(f"### Round 2 begins in {left}…")
