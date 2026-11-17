"""Round 1 on a player's phone: intro → four games, one after another →
waiting room / tie-breaker → results.

Keeping it fast with 8 phones: while you play, nothing is redrawn by the server.
The game is drawn once and only redrawn when YOU tap something. The countdown
number and bar are animated by the browser itself (CSS), and a tiny invisible
check redraws the page once when your time runs out or the memory objects must
hide. Screens that wait for other players (waiting
room, tie-breaker) check the database every second, and only write to it when
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
        if rules.is_host(tour, me) and phase == "waiting":
            _host_controls(code, me)


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


@st.fragment(run_every="1s")
def _waiting_or_tiebreak(code, me):
    now = time.time()
    tour = _load_settled(code, now)
    if tour is None or r1.phase(tour, me, now) not in ("waiting", "tiebreak"):
        st.rerun()                            # results are in, or something changed
    if r1.phase(tour, me, now) == "tiebreak":
        _tiebreak(tour, code, me, now)
    else:
        _waiting(tour, code, me, now)


def _html(markup):
    """Show our own drawings and styles (screens/art.py). Never pass player-typed text in here."""
    st.markdown(markup, unsafe_allow_html=True)


def _key(code, name):
    """session_state keys are per tournament, so an old game never leaks into a new one."""
    return f"r1_{code}_{name}"


def _grid(name, count):
    """`count` columns that stay side by side on phones too.

    Normally Streamlit stacks columns on top of each other on narrow screens,
    which turns 4 tiles into a long list you have to scroll. This keeps them
    in one row (they just get smaller)."""
    key = art.css_key(f"grid_{name}")
    _html(art.phone_grid_style(key))
    with st.container(key=key):
        return st.columns(count)


def _picture_button(key, svg, label, height=120, selected=False, bob=False):
    """A drawing you tap directly. Returns True when tapped."""
    key = art.css_key(key)        # e.g. "Clock Room" → "Clock_Room", safe as a CSS class
    _html(art.picture_button_style(key, svg, height, selected, bob))
    return st.button(label, key=key, width="stretch")


# --- intro ------------------------------------------------------------------------

def _intro(tour, me):
    _html(art.heading("duel", "Round 1: the duels", size=44, level=1))
    opponent = rules.opponent_of(tour, me)
    you = rules.find_player(tour, me)
    st.markdown("### Your first suspect is… your opponent.")
    st.markdown(common.duel_card(you, opponent), unsafe_allow_html=True)
    order = r1.order_of(tour, me)
    _html("<p><b>Your four games:</b> " + " &nbsp;→&nbsp; ".join(
        f"{art.icon(g, 22)}{r1.GAMES[g]}" for g in order) + "</p>")
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
    _html(art.heading(game, r1.GAMES[game]))

    puzzle = r1.puzzle(tour, game)          # the version this tournament drew
    if game == "number_lock":
        _number_lock(code, me, number, puzzle)
    elif game == "pattern":
        _pattern(code, me, number, puzzle)
    elif game == "escape_route":
        _escape_route(code, me, number, puzzle)
    elif game == "memory":
        _memory(tour, code, me, number, now, puzzle)


def _submit(code, me, number, value):
    tour, message = storage.update(code, r1.answer, me, number, value, time.time())
    answered = tour is not None and r1.game_number(tour, me) > number
    if answered:
        st.rerun()                            # straight on, without saying right or wrong                            # the next game, with a fresh timer
    else:
        st.error(message)


def _number_lock(code, me, number, puzzle):
    st.caption(r1.NUMBER_LOCK_RULE)
    for guess, feedback in puzzle["feedback"].items():
        st.markdown(f"`{guess}`  {r1.clue_text(feedback)}")

    _html(art.img(art.padlock(["?", "?", "?", "?"]), width="190px"))
    with st.form(_key(code, f"lock_form_{number}"), border=False):
        typed = st.text_input("Type the 4-digit code", max_chars=4, placeholder="e.g. 1234",
                              key=_key(code, f"typed_{number}"))
        if st.form_submit_button("Unlock", type="primary", width="stretch"):
            _submit(code, me, number, typed)


def _pattern(code, me, number, puzzle):
    st.write("Every row and every column has each shape once and each colour once. "
             "**Tap the tile that fills the gap**, then lock in.")
    _html(art.img(art.wall(puzzle["grid"]), width="320px"))

    picked_key = _key(code, f"pattern_{number}")
    picked = st.session_state.get(picked_key)
    columns = _grid(f"pattern_{number}", 4)
    for column, (option, (shape, colour)) in zip(columns, puzzle["options"].items()):
        with column:
            chosen = option == picked
            if _picture_button(f"pattern_{number}_{option}", art.tile(shape, colour),
                               f"✓ {option}" if chosen else option, selected=chosen, bob=not picked):
                st.session_state[picked_key] = None if chosen else option
                st.rerun(scope="fragment")
    if st.button("Lock in", type="primary", width="stretch", disabled=picked is None,
                 key=f"pattern_lock_{number}"):
        _submit(code, me, number, picked)


def _escape_route(code, me, number, puzzle):
    _html(art.panel("rules", "The rules of the house", r1.ESCAPE_CLUES))
    route_key = _key(code, f"route_{number}")
    route = st.session_state.get(route_key, [])
    here = route[-1] if route else "Start"
    st.markdown("**Your path:** " + " → ".join(["Start"] + route))
    st.caption("Tap a door to go through it. There's no going back.")

    doors = puzzle["map"][here]
    columns = _grid(f"doors_{number}_{art.css_key(here)}", len(doors))
    for column, room in zip(columns, doors):
        with column:
            if _picture_button(f"door_{number}_{here}_{room}", art.room(room), room, height=130):
                new_route = route + [room]
                if room in puzzle["map"]:          # not a dead end yet: keep walking
                    st.session_state[route_key] = new_route
                    st.rerun(scope="fragment")
                else:
                    st.session_state[route_key] = []
                    _submit(code, me, number, new_route)
            st.caption(puzzle["rooms"][room])


def _memory(tour, code, me, number, now, puzzle):
    if r1.memory_items_visible(tour, me, now):
        st.write(f"**Remember these!** They hide after {r1.MEMORY_SHOW_SECONDS} seconds.")
        _html(art.row([(art.item(name), name) for name in r1.MEMORY_ITEMS], columns=5))
        return

    st.write("Now only these are left:")
    _html(art.row([(art.item(name), name) for name in puzzle["remaining"]], columns=7))
    need = len(puzzle["missing"])
    st.write(f"**Which {need} vanished? Tap {need} objects**, then lock in.")

    picked_key = _key(code, f"memory_{number}")
    picked = st.session_state.setdefault(picked_key, [])
    rows = [_grid(f"memory_{number}_{r}", 5) for r in range(2)]
    for k, name in enumerate(r1.MEMORY_ITEMS):
        with rows[k // 5][k % 5]:
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
    _html(art.heading("tiebreak", "It's a tie!", size=44, level=1))
    st.markdown(f"Neither you nor {common.player_label(opponent)} got a game right. "
                "One question decides it. If you're both right, the faster one wins.")
    seconds = r1.tiebreak_seconds_left(tour, me, now)
    _html(art.heading("timer", f"{seconds}s"))
    st.progress(seconds / r1.TIEBREAK_SECONDS)
    _html(art.panel("rules", "The question", [r1.TIEBREAK_QUESTION]))
    with st.form(_key(code, "tiebreak_form")):
        value = st.text_input("Your answer", max_chars=4)
        if st.form_submit_button("Lock it in", type="primary"):
            storage.update(code, r1.answer_tiebreak, me, value, time.time())
            st.rerun()


# --- waiting room --------------------------------------------------------------



def _waiting(tour, code, me, now):
    _html(art.heading("solutions", "Case file closed", size=44, level=1))
    st.markdown(f"You finished all four games in **{r1.total_seconds(tour, me)}s**. "
                "The verdict comes when every detective is done…")
    _race_track(tour, code, me, now)
    _html(f"<p style='text-align:center'><em>{WAITING_LINES[int(now / 3) % len(WAITING_LINES)]}</em></p>")
    done = r1.finished_count(tour)
    total = len(tour["round1"]["players"])
    st.caption(f"{done} of {total} detectives have finished")


def _race_track(tour, code, me, now):
    """Everyone on one track, sliding forward as they get through their games.
    Shows how far along each detective is, never whether they were right."""
    last_key = _key(code, "race_last")
    last = st.session_state.get(last_key, {})
    runners, now_positions = [], {}
    for player in tour["players"]:
        pid = player["id"]
        if pid not in tour["round1"]["players"]:
            continue
        position = r1.progress(tour, pid, now)
        now_positions[pid] = position
        name = player["name"] + (" (left)" if r1.has_left(tour, pid) else "")
        runners.append({"name": name, "from": last.get(pid, position), "to": position,
                        "me": pid == me, "done": r1.is_done(tour, pid)})
    st.session_state[last_key] = now_positions
    _html(art.race_track(runners, uid=f"{int(now * 10)}"))


@st.fragment
def _host_controls(code, me):
    """Only the host sees this, once their own games are done. Drawn once and only
    redrawn when the host taps something, so the buttons don't get lost."""
    now = time.time()
    tour = storage.load(code)
    if tour is None or tour["status"] != "round1":
        return
    still_playing = [p for p in tour["players"] if p["id"] in tour["round1"]["players"]
                     and not r1.is_done(tour, p["id"])
                     and tour["round1"]["results"][r1.duel_index(tour, p["id"])] is None]
    confirm_key = _key(code, "host_confirm")
    confirm = st.session_state.get(confirm_key)

    st.divider()
    _html(art.heading("rules", "Host controls", size=28, level=4))
    st.caption("Only you can see this. Use it if someone has left, or to stop waiting for the timers.")

    for player in still_playing:
        left, right = _grid(f"host_{player['id']}", 2)
        left.markdown(f"{common.player_label(player)} is still playing")
        if confirm == ("left", player["id"]):
            if right.button("Yes, they left", key=f"left_yes_{player['id']}", type="primary", width="stretch"):
                storage.update(code, r1.player_left, me, player["id"], time.time())
                st.session_state[confirm_key] = None
                st.rerun()
        elif right.button("Left the game", key=f"left_{player['id']}", width="stretch"):
            st.session_state[confirm_key] = ("left", player["id"])
            st.rerun(scope="fragment")

    if confirm == ("end",):
        st.warning("End Round 1 now? Every unfinished game counts as not answered.")
        yes, no = _grid("host_end_confirm", 2)
        if yes.button("Yes, end it", key="end_yes", type="primary", width="stretch"):
            storage.update(code, r1.end_round_now, me, time.time())
            st.session_state[confirm_key] = None
            st.rerun()
        if no.button("Cancel", key="end_no", width="stretch"):
            st.session_state[confirm_key] = None
            st.rerun(scope="fragment")
    elif st.button("End the round now", key="end_round", width="stretch"):
        st.session_state[confirm_key] = ("end",)
        st.rerun(scope="fragment")


# --- results ---------------------------------------------------------------------

def _results(tour, me):
    st.title("Which detectives made it out?")
    if me in tour["eliminated"]:
        _html(art.banner("eliminated", "You've been eliminated. Stay and watch the rest of the game!", good=False))
    else:
        _html(art.banner("through", "You're through to Round 2!"))

    cards = []
    for number, result in enumerate(tour["round1"]["results"], start=1):
        w, l = result["winner"], result["loser"]
        winner = rules.find_player(tour, w)
        loser = rules.find_player(tour, l)
        cards.append(common.result_duel_card(number, winner, loser))
    st.markdown("<div class='mm-results-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)

    st.divider()
    _solutions(tour)


def _solutions(tour):
    """Round 1 is over, so everyone gets to see what the answers were."""
    lock, wall = r1.puzzle(tour, "number_lock"), r1.puzzle(tour, "pattern")
    route, memory = r1.puzzle(tour, "escape_route"), r1.puzzle(tour, "memory")
    shape, colour = wall["options"][wall["answer"]]
    colour_name = {"royal": "royal blue", "ice": "ice blue"}.get(colour, colour)
    _html(art.heading("solutions", "The solutions"))
    _html(f"<p>{art.icon('number_lock', 24)}<b>Number Lock:</b> the code was <b>{lock['answer']}</b>.</p>")
    _html(f"<p style='display:flex;align-items:center;gap:.4rem'>{art.icon('pattern', 24)}"
          f"<span><b>Pattern Wall:</b> tile <b>{wall['answer']}</b>, the {colour_name} {shape}.</span>"
          f"{art.img(art.tile(shape, colour), width='48px')}</p>")
    _html(f"<p>{art.icon('escape_route', 24)}<b>Escape Route:</b> "
          + " → ".join(["Start"] + route["answer"])
          + ". Food, ticking or chiming, the guard at the piano and the fireplace rule ruled out every other way.</p>")
    _html(f"<p>{art.icon('memory', 24)}<b>Memory Table:</b> these vanished:</p>")
    _html(art.row([(art.item(name), name) for name in memory["missing"]], columns=5))
