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
        _results(code, tour, me)
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


def _picture_button(key, svg, label, height=120, selected=False, bob=False, appear=None):
    """A drawing you tap directly. Returns True when tapped."""
    key = art.css_key(key)        # e.g. "Clock Room" → "Clock_Room", safe as a CSS class
    _html(art.picture_button_style(key, svg, height, selected, bob, appear))
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
    draw = {"number_lock": lambda: _number_lock(code, me, number, puzzle),
            "pattern": lambda: _pattern(code, me, number, puzzle),
            "escape_route": lambda: _escape_route(code, me, number, puzzle),
            "memory": lambda: _memory(tour, code, me, number, now, puzzle)}[game]
    try:
        draw()
    except Exception as error:          # never leave a player looking at an empty screen
        if _is_streamlit_control(error):
            raise                       # st.rerun() works by raising; let it through
        st.error("This game couldn't be shown. Please take a screenshot and tell the host.")
        st.exception(error)


def _is_streamlit_control(error):
    """st.rerun() and st.stop() work by raising special exceptions; those must not be caught."""
    names = {cls.__name__ for cls in type(error).__mro__}
    return bool(names & {"RerunException", "StopException", "ScriptControlException"})


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

    # The padlock: the loop on top is a drawing, the body is a styled container, and
    # the text box inside it is styled as one dark display window (screens/art.py).
    lock_key = art.css_key(f"lock_{number}")
    _html(art.lock_style(lock_key))
    _html('<div style="text-align:center;margin-top:.6rem">'
          + art.img(art.shackle(), width="150px").replace("margin:auto", "margin:0 auto -4px") + "</div>")
    with st.container(key=lock_key):
        with st.form(_key(code, f"lock_form_{number}"), border=False):
            typed = st.text_input("Type the code", max_chars=4, placeholder="····",
                                  key=_key(code, f"typed_{number}"))
            unlock = st.form_submit_button("Unlock", type="primary")
    if unlock:
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

    # Your path so far, and the room you've just stepped into.
    _html(art.route_trail(route))
    if route:
        _html(art.room_entrance(here, puzzle["rooms"][here]))
    st.caption("Tap a door to go through it. There's no going back.")

    doors = puzzle["map"][here]
    columns = _grid(f"doors_{number}_{art.css_key(here)}", len(doors))
    for k, (column, room) in enumerate(zip(columns, doors)):
        with column:
            if _picture_button(f"door_{number}_{here}_{room}", art.room(room), room, height=130,
                               appear=0.15 + 0.18 * k):
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
    for k, name in enumerate(puzzle["options"]):       # 3 vanished, 3 still here, 4 never shown
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
    _html(art.searching_scene())
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

def _results(code, tour, me):
    st.title("Which detectives made it out?")
    if me in tour["eliminated"]:
        _html(art.banner("eliminated", "You've been eliminated. Stay and watch the rest of the game!", good=False))
    else:
        _html(art.banner("through", "You're through to Round 2!"))

    # Round 2 starts when the four detectives going through are all ready.
    # You get ready by tapping your own card in the lineup.
    _ready_watch(code, tuple(sorted(r1.ready_players(tour))))
    _ready_lineup(code, me)
    _ready_host(code, me)

    cards = []
    for number, result in enumerate(tour["round1"]["results"], start=1):
        w, l = result["winner"], result["loser"]
        winner = rules.find_player(tour, w)
        loser = rules.find_player(tour, l)
        cards.append(common.result_duel_card(number, winner, loser))
    st.markdown("<div class='mm-results-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)

    st.divider()
    _scoreboard(tour, me)


@st.fragment(run_every="1s")
def _ready_watch(code, seen):
    """Invisible: checks every second and redraws the page when someone new is
    ready or Round 2 has begun. Draws nothing, so taps can't get lost in it."""
    tour = storage.load(code)
    if tour is None or tour["status"] != "round1_results" or tuple(sorted(r1.ready_players(tour))) != seen:
        st.rerun()


@st.fragment
def _ready_lineup(code, me):
    """The four detectives going through, side by side. Your own card is a button:
    tap it and you're ready. Everyone else's card shows READY / NOT READY."""
    tour = storage.load(code)
    if tour is None or tour["status"] != "round1_results":
        return
    going = r1.advancing(tour)
    ready = set(r1.ready_players(tour))
    _html(art.ready_lineup_style())
    _html('<div class="mm-rl-title">READY FOR ROUND 2</div>')
    for column, pid in zip(_grid("ready_lineup", len(going)), going):
        player = rules.find_player(tour, pid)
        _, path = common.AVATARS.get(player.get("appearance") or "girl", common.AVATARS["girl"])
        picture = common.avatar_data_url(path)
        with column:
            if pid == me and pid not in ready:
                _html(art.ready_tap_style("ready_tap", picture))
                if st.button(common.safe(player["name"]), key="ready_tap", width="stretch"):
                    storage.update(code, r1.mark_ready, me, time.time())
                    st.rerun()
            else:
                _html(art.ready_card(player["name"], picture, pid in ready, pid == me))
    if me in going and me not in ready:
        st.caption("Tap your detective when you're ready for Round 2.")
    elif me in going:
        st.caption("You're ready. Waiting for the other detectives…")
    else:
        st.caption("The four detectives going through are getting ready for Round 2…")


@st.fragment
def _ready_host(code, me):
    """The host's override: start Round 2 without waiting for everyone."""
    tour = storage.load(code)
    if tour is None or tour["status"] != "round1_results":
        return
    if rules.is_host(tour, me):
        confirm_key = _key(code, "host_start_r2")
        if st.session_state.get(confirm_key):
            st.warning("Start Round 2 now, without waiting for everyone to be ready?")
            yes, no = _grid("host_r2_confirm", 2)
            if yes.button("Yes, start", key="r2_yes", type="primary", width="stretch"):
                storage.update(code, r1.start_round2_now, me, time.time())
                st.session_state[confirm_key] = False
                st.rerun()
            if no.button("Cancel", key="r2_no", width="stretch"):
                st.session_state[confirm_key] = False
                st.rerun(scope="fragment")
        elif st.button("Host: start Round 2 now", key="r2_force", width="stretch"):
            st.session_state[confirm_key] = True
            st.rerun(scope="fragment")


def _scoreboard(tour, me):
    """How every detective did in the four games (never the answers themselves),
    best first: most right answers, then fastest."""
    rows = []
    for player in tour["players"]:
        pid = player["id"]
        if pid not in tour["round1"]["players"]:
            continue
        marks = {}
        for game, result in zip(r1.order_of(tour, pid), tour["round1"]["players"][pid]["results"]):
            marks[game] = "time" if result["timed_out"] else ("right" if result["correct"] else "wrong")
        rows.append({"name": player["name"] + (" (left)" if r1.has_left(tour, pid) else ""),
                     "marks": marks, "points": r1.points(tour, pid),
                     "seconds": r1.total_seconds(tour, pid), "me": pid == me,
                     "out": pid in tour["eliminated"]})
    rows.sort(key=lambda r: (-r["points"], r["seconds"]))
    _html(art.heading("solutions", "How everyone did"))
    _html(art.scoreboard(rows, list(r1.GAMES)))
