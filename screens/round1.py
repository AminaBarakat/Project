"""Round 1 on a player's phone: intro → four games, one after another →
waiting room / tie-breaker → results.

Keeping it fast with 8 phones: while you play, nothing is redrawn by the server.
The game is drawn once and only redrawn when YOU tap something. The countdown
number and bar are animated by the browser itself (CSS), and a tiny invisible
check redraws the page once when your time runs out or the memory objects must
hide. Screens that wait for other players (waiting
room, tie-breaker) check the database every 2 seconds, and only write to it when
something is actually due, like a timer that has run out.

Things only this phone needs (the dials of the lock, the route clicked so far,
the memory items picked) live in st.session_state, with the game number in the
key so every game starts fresh. Everything shared lives in the database.
The pictures and the "tap the picture" buttons come from screens/art.py.
"""

import time

import streamlit as st

import round1 as r1
import storage
import tournament as rules
from screens import art, common, duels

WAITING_LINES = [
    "Dusting the bookshelves for fingerprints…",
    "Checking who had the key last…",
    "Comparing the witness statements…",
    "Following muddy footprints down the hall…",
    "Counting the portraits in the gallery…",
]


def show(code, me):
    now = time.time()
    tour = _load_settled(code, now)
    if tour is None or tour["status"] not in ("round1", "round1_results"):
        st.rerun()                            # Round 2, or the tournament vanished

    phase = r1.phase(tour, me, now)
    if phase == "intro":
        _intro(tour, me)
        _redraw_at(tour["round1"]["starts_at"], "Starting in {}…")
    elif phase == "playing":
        _game_header(tour, me, now)
        _redraw_when_due(_deadlines(tour, me, now))
        _game(code, me)
    elif phase == "results":
        _results(tour, me)
        _redraw_at(tour["round1"]["results_at"] + r1.RESULTS_SECONDS, "Round 2 begins in {}…")
    else:
        _waiting_or_tiebreak(code, me)


def _load_settled(code, now):
    """Read the tournament; write only if something is due (a timer ran out, a duel can be decided)."""
    tour = storage.load(code)
    if tour is not None and r1.settle(tour, now)[0] != tour:
        tour, _ = storage.update(code, r1.settle, now)
    return tour


@st.fragment(run_every="1s")
def _redraw_at(when, text):
    """A small countdown; redraws the whole page once `when` has passed."""
    left = int(when - time.time() + 0.999)
    if left <= 0:
        st.rerun()
    st.markdown(f"### {text.format(left)}")


def _deadlines(tour, me, now):
    """The moments when this player's screen must change by itself."""
    started = tour["round1"]["players"][me]["game_started_at"]
    moments = [started + r1.GAME_SECONDS]
    if r1.current_game(tour, me) == "memory" and now < started + r1.MEMORY_SHOW_SECONDS:
        moments.append(started + r1.MEMORY_SHOW_SECONDS)
    return moments


@st.fragment(run_every="1s")
def _redraw_when_due(moments):
    """Invisible: draws nothing, and redraws the page once one of the moments has passed."""
    if time.time() >= min(moments):
        st.rerun()


def _game_header(tour, me, now):
    """Game number and a countdown that the BROWSER animates, so the server
    doesn't redraw anything every second (that is what made taps get lost)."""
    number = r1.game_number(tour, me)
    started = tour["round1"]["players"][me]["game_started_at"]
    seconds = max(0, int(started + r1.GAME_SECONDS - now + 0.999))
    dots = "".join("●" if k < number else ("◉" if k == number else "○") for k in range(len(r1.GAMES)))
    _html(art.countdown(f"g{number}_{int(started)}", seconds, r1.GAME_SECONDS,
                        f"Game {number + 1} of {len(r1.GAMES)} &nbsp; {dots}"))


@st.fragment(run_every="2s")
def _waiting_or_tiebreak(code, me):
    now = time.time()
    tour = _load_settled(code, now)
    if tour is None or r1.phase(tour, me, now) not in ("waiting", "tiebreak"):
        st.rerun()                            # results are in, or something changed
    if r1.phase(tour, me, now) == "tiebreak":
        _tiebreak(tour, code, me, now)
    else:
        _waiting(tour, me, now)


def _html(markup):
    """Show our own drawings and styles (screens/art.py). Never pass player-typed text in here."""
    st.markdown(markup, unsafe_allow_html=True)


def _key(code, name):
    """session_state keys are per tournament, so an old game never leaks into a new one."""
    return f"r1_{code}_{name}"


def _picture_button(key, svg, label, height=120, selected=False, bob=False):
    """A drawing you tap directly. Returns True when tapped."""
    key = art.css_key(key)        # e.g. "Clock Room" → "Clock_Room", safe as a CSS class
    _html(art.picture_button_style(key, svg, height, selected, bob))
    return st.button(label, key=key, width="stretch")


# --- intro ------------------------------------------------------------------------

def _intro(tour, me):
    st.title("Round 1: the duels")
    opponent = rules.opponent_of(tour, me)
    you = rules.find_player(tour, me)
    st.markdown("### Your first suspect is… your opponent.")
    st.markdown(common.duel_card(you, opponent), unsafe_allow_html=True)
    order = r1.order_of(tour, me)
    st.markdown("**Your four games:** " + "  →  ".join(r1.GAMES[g] for g in order))
    st.caption(f"{r1.GAME_SECONDS} seconds and one try per game. Most right answers wins; "
               "on a draw, the faster one wins.")
    st.divider()
    duels.show_bracket(tour, me)


# --- the games --------------------------------------------------------------------

@st.fragment
def _game(code, me):
    """The current game. Drawn once, and redrawn only when this player taps something."""
    now = time.time()
    tour = storage.load(code)
    if tour is None or r1.phase(tour, me, now) != "playing":
        st.rerun()
    number = r1.game_number(tour, me)
    game = r1.current_game(tour, me)
    # The team theme paints every button purple; make switched-off ones look switched off.
    _html("<style>div.stButton > button:disabled { opacity: .35 !important; filter: grayscale(.6) "
          "!important; cursor: not-allowed !important; box-shadow: none !important; }</style>")
    st.subheader(r1.GAMES[game])

    if game == "number_lock":
        _number_lock(code, me, number)
    elif game == "pattern":
        _pattern(code, me, number)
    elif game == "escape_route":
        _escape_route(code, me, number)
    elif game == "memory":
        _memory(tour, code, me, number, now)


def _submit(code, me, number, value):
    tour, message = storage.update(code, r1.answer, me, number, value, time.time())
    answered = tour is not None and r1.game_number(tour, me) > number
    if answered:
        st.toast(message)
        st.rerun()                            # the next game, with a fresh timer
    else:
        st.error(message)


def _number_lock(code, me, number):
    st.caption(r1.NUMBER_LOCK_RULE)
    for guess, clue in r1.NUMBER_LOCK_CLUES:
        st.markdown(f"`{guess}`  {clue}")

    digits = st.session_state.setdefault(_key(code, f"dials_{number}"), ["0", "0", "0", "0"])
    _html(art.img(art.padlock(digits), width="220px"))

    columns = st.columns(4)
    for k, column in enumerate(columns):
        if column.button("▲", key=f"dial_up_{number}_{k}", width="stretch"):
            digits[k] = str((int(digits[k]) + 1) % 10)
            st.rerun(scope="fragment")
        if column.button("▼", key=f"dial_down_{number}_{k}", width="stretch"):
            digits[k] = str((int(digits[k]) - 1) % 10)
            st.rerun(scope="fragment")
    if st.button("🔓 Unlock", type="primary", width="stretch"):
        _submit(code, me, number, "".join(digits))


def _pattern(code, me, number):
    st.write("Every row and every column has each shape once and each colour once. "
             "**Tap the tile that fills the gap**, then lock in.")
    _html(art.img(art.wall(r1.PATTERN_GRID), width="320px"))

    picked_key = _key(code, f"pattern_{number}")
    picked = st.session_state.get(picked_key)
    columns = st.columns(4)
    for column, (option, (shape, colour)) in zip(columns, r1.PATTERN_OPTIONS.items()):
        with column:
            chosen = option == picked
            if _picture_button(f"pattern_{number}_{option}", art.tile(shape, colour),
                               f"✓ {option}" if chosen else option, selected=chosen, bob=not picked):
                st.session_state[picked_key] = None if chosen else option
                st.rerun(scope="fragment")
    if st.button("Lock in", type="primary", width="stretch", disabled=picked is None,
                 key=f"pattern_lock_{number}"):
        _submit(code, me, number, picked)


def _escape_route(code, me, number):
    with st.expander("📜 The rules of the house", expanded=True):
        for clue in r1.ESCAPE_CLUES:
            st.markdown(f"- {clue}")
    route_key = _key(code, f"route_{number}")
    route = st.session_state.get(route_key, [])
    here = route[-1] if route else "Start"
    st.markdown("**Your path:** " + " → ".join(["Start"] + route))
    st.caption("Tap a door to go through it. There's no going back.")

    doors = r1.ESCAPE_MAP[here]
    columns = st.columns(len(doors))
    for column, room in zip(columns, doors):
        with column:
            if _picture_button(f"door_{number}_{here}_{room}", art.room(room), room, height=130):
                new_route = route + [room]
                if room in r1.ESCAPE_MAP:          # not a dead end yet: keep walking
                    st.session_state[route_key] = new_route
                    st.rerun(scope="fragment")
                else:
                    st.session_state[route_key] = []
                    _submit(code, me, number, new_route)
            st.caption(r1.ESCAPE_ROOMS[room])


def _memory(tour, code, me, number, now):
    if r1.memory_items_visible(tour, me, now):
        st.write(f"**Remember these!** They hide after {r1.MEMORY_SHOW_SECONDS} seconds.")
        _html(art.row([(art.item(name), name) for name in r1.MEMORY_ITEMS], columns=5))
        return

    st.write("Now only these are left:")
    _html(art.row([(art.item(name), name) for name in r1.MEMORY_REMAINING], columns=7))
    need = len(r1.MEMORY_MISSING)
    st.write(f"**Which {need} vanished? Tap {need} objects**, then lock in.")

    picked_key = _key(code, f"memory_{number}")
    picked = st.session_state.setdefault(picked_key, [])
    columns = st.columns(5)
    for k, name in enumerate(r1.MEMORY_ITEMS):
        with columns[k % 5]:
            chosen = name in picked
            if _picture_button(f"memory_{number}_{k}", art.item(name),
                               f"✓ {name}" if chosen else name, height=110, selected=chosen):
                if chosen:
                    picked.remove(name)
                elif len(picked) < need:
                    picked.append(name)
                st.rerun(scope="fragment")
    if st.button("Lock in", type="primary", width="stretch", disabled=len(picked) != need,
                 key=f"memory_lock_{number}"):
        _submit(code, me, number, list(picked))


# --- tie-breaker -----------------------------------------------------------------

def _tiebreak(tour, code, me, now):
    opponent = rules.opponent_of(tour, me)
    st.title("⚖️ It's a tie!")
    st.markdown(f"Neither you nor {common.player_label(opponent)} got a game right. "
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
            st.rerun()


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
    st.markdown(f"You got **{r1.points(tour, me)}/4** right in **{r1.total_seconds(tour, me)}s**. "
                "Now we wait for the others…")
    for game, result in zip(r1.order_of(tour, me), tour["round1"]["players"][me]["results"]):
        mark = "⏰" if result["timed_out"] else ("✅" if result["correct"] else "❌")
        st.caption(f"{mark} {r1.GAMES[game]} · {result['seconds']}s")
    # Static HTML only: no player names in here, so nothing typed by a player gets in.
    _html(_WAITING_ANIMATION)
    _html(f"<p style='text-align:center'><em>{WAITING_LINES[int(now / 3) % len(WAITING_LINES)]}</em></p>")

    done = r1.finished_count(tour)
    total = len(tour["round1"]["players"])
    st.progress(done / total, text=f"{done} of {total} detectives have finished")


# --- results ---------------------------------------------------------------------

_HOW = {"more right answers": "more right answers", "faster": "faster",
        "tie-breaker": "won the tie-breaker", "tie-breaker speed": "faster on the tie-breaker",
        "draw": "decided by a draw"}


def _results(tour, me):
    st.title("Which detectives made it out?")
    if me in tour["eliminated"]:
        st.error("💀 You've been eliminated. Stay and watch the rest of the game!")
    else:
        st.success("🎉 You're through to Round 2!")

    cards = []
    for number, result in enumerate(tour["round1"]["results"], start=1):
        w, l = result["winner"], result["loser"]
        winner = rules.find_player(tour, w)
        loser = rules.find_player(tour, l)
        detail = (f" · {result['points'][w]}/4 in {result['seconds'][w]}s · "
                  f"{_HOW[result['decided_by']]}")
        cards.append(common.result_duel_card(number, winner, loser, detail))
    st.markdown("<div class='mm-results-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)

    st.divider()
