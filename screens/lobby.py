"""The lobby: everyone sits at a round table until the host starts the tournament.

What's on the page (phone and laptop):
* the game's title, the join code and the invite link (with a copy button);
* the round table with 8 seats: players appear in their seat as they join, empty
  seats pulse, the host wears a crown, your own seat glows;
* greetings (Wave, Good luck, …) that pop up as a bubble next to the sender's seat,
  with a small feed; a warm-up riddle; "how the night goes" for first-timers;
* the host's Start button (and a small menu to remove someone), and a switch that
  shows a QR code people can scan to join;

The page itself is drawn as one normal Streamlit run, so taps can't get lost. A tiny
invisible watcher (_watch) checks every 2 seconds, using the shared copy in
screens/live.py, and redraws the page only when something changed: the game
started, someone joined, left or sent a greeting, or the riddle changed.
"""

import base64
import html
import math
import time

import streamlit as st

import lobby_chat as chat
import qr
import storage
import tournament as rules
from screens import art, avatars, common, live

WATCH_EVERY = "2s"
RIDDLE_SECONDS = 45

# Classic riddles (traditional, free to use).
RIDDLES = [
    ("The more of me you take, the more you leave behind. What am I?", "Footsteps"),
    ("What has keys but can't open a single lock?", "A piano"),
    ("I have cities but no houses, forests but no trees, and water but no fish. What am I?", "A map"),
    ("What has hands but can't clap?", "A clock"),
    ("What can travel around the world while staying in a corner?", "A stamp"),
    ("What gets wetter the more it dries?", "A towel"),
    ("What has a head and a tail but no body?", "A coin"),
    ("What can you catch but not throw?", "A cold"),
]

STEPS = [("1", "Round 1", "Four quick puzzles, against one rival (or, with 5 players, everyone)"),
         ("2", "Round 2", "Two duos race to open the vault"),
         ("3", "Round 3", "The final two solve the mystery")]


# --- our own small drawings for the greeting buttons ------------------------------------

def _svg(body):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">{body}</svg>'
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


ICE, GOLD = art.TILE_COLOURS["ice"], "#f7d84a"
GREETING_ICONS = {
    "wave": _svg(f'<path d="M10 28 Q5 22 6 15 L6 10 Q6 8 8 8 Q10 8 10 10 L10 14 L10 6 Q10 4 12 4 Q14 4 14 6 L14 13 '
                 f'L14 5 Q14 3 16 3 Q18 3 18 5 L18 13 L18 7 Q18 5 20 5 Q22 5 22 7 L22 19 Q22 26 16 28 Z" '
                 f'fill="{GOLD}" stroke="#b5891f" stroke-width="1.2"/>'
                 f'<path d="M25 6 Q28 9 27 13 M27 3 Q31 8 30 14" stroke="{ICE}" stroke-width="1.8" fill="none" stroke-linecap="round"/>'),
    "good_luck": _svg(f'<rect x="9" y="5" width="14" height="15" rx="2" fill="#2b2140" stroke="{art.SILVER}" stroke-width="1.4"/>'
                      f'<rect x="9" y="15" width="14" height="3" fill="{art.PURPLE}"/>'
                      f'<ellipse cx="16" cy="21" rx="13" ry="3.5" fill="#2b2140" stroke="{art.SILVER}" stroke-width="1.4"/>'
                      f'<path d="M25 4 L26 7 L29 8 L26 9 L25 12 L24 9 L21 8 L24 7 Z" fill="{GOLD}"/>'),
    "watching": _svg(f'<path d="M2 16 Q16 3 30 16 Q16 29 2 16 Z" fill="#ffffff" stroke="{art.SILVER}" stroke-width="1.4"/>'
                     f'<circle cx="16" cy="16" r="6" fill="{art.PURPLE}"/><circle cx="16" cy="16" r="2.8" fill="#10071f"/>'
                     '<circle cx="18" cy="14" r="1.3" fill="#fff"/>'),
    "hurry": _svg(f'<rect x="7" y="3" width="18" height="3" rx="1.5" fill="{art.PURPLE}"/><rect x="7" y="26" width="18" height="3" rx="1.5" fill="{art.PURPLE}"/>'
                  f'<path d="M9 6 L23 6 L17 16 L23 26 L9 26 L15 16 Z" fill="#ffffff22" stroke="{art.SILVER}" stroke-width="1.4"/>'
                  f'<path d="M11 8 L21 8 L16.5 14 L15.5 14 Z" fill="{GOLD}"/><path d="M11 25 Q16 19 21 25 Z" fill="{GOLD}"/>'),
}

STYLE = f"""<style>
.mm-lobby-tag {{ text-align: center; color: #d7b9ee; font-family: Georgia, serif; letter-spacing: .2em; font-size: .75rem; margin-top: -.2rem; }}

/* join code + invite link, side by side on every screen */
.st-key-mm_lobby_top [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: .7rem !important; align-items: flex-end; }}
.st-key-mm_lobby_top [data-testid="stColumn"] {{ min-width: 0 !important; width: auto !important; }}
.st-key-mm_lobby_top [data-testid="stColumn"]:first-child {{ flex: 0 0 auto !important; }}
.st-key-mm_lobby_top [data-testid="stColumn"]:last-child {{ flex: 1 1 0 !important; }}
.mm-code {{ background: #0c0518; border: 1px solid {art.PURPLE}88; border-radius: 14px; padding: .4rem .9rem .5rem;
  box-shadow: 0 0 18px {art.PURPLE}44; white-space: nowrap; }}
/* host's QR invite: white card so every phone camera can read it */
.st-key-mm_qr_toggle {{ display: flex; justify-content: center; margin: .2rem 0 .1rem; }}
.mm-qr {{ width: min(300px, 82vw); margin: .3rem auto 1rem; padding: .9rem .9rem .8rem; text-align: center;
  background: #0c0518; border: 1px solid {art.PURPLE}88; border-radius: 18px;
  box-shadow: 0 0 26px {art.PURPLE}55; animation: mm-qr-in .3s ease-out both; }}
.mm-qr-label {{ font-size: .66rem; letter-spacing: .2em; font-weight: 800; color: #e4e7efcc; margin-bottom: .55rem; }}
.mm-qr-code {{ background: #fff; border-radius: 12px; padding: 6px; line-height: 0; }}
.mm-qr-code svg {{ width: 100%; height: auto; display: block; }}
.mm-qr-foot {{ margin-top: .6rem; font-size: .74rem; color: #e4e7ef99; }}
.mm-qr-foot b {{ font-family: 'Courier New', monospace; color: #fff; letter-spacing: .15em; }}
@keyframes mm-qr-in {{ from {{ opacity: 0; transform: scale(.94); }} to {{ opacity: 1; transform: none; }} }}
.mm-code small {{ display: block; font-size: .6rem; letter-spacing: .16em; color: #e4e7ef99; font-weight: 700; }}
.mm-code b {{ font-family: 'Courier New', monospace; font-size: 1.75rem; letter-spacing: .25em; color: #fff; }}
.mm-invite {{ font-size: .62rem; letter-spacing: .16em; color: #e4e7ef99; font-weight: 700; margin-bottom: .25rem; }}
.st-key-mm_lobby_top [data-testid="stCode"] pre, .st-key-mm_lobby_top .stCode pre {{ white-space: nowrap !important; overflow: hidden;
  text-overflow: ellipsis; font-size: .8rem; }}

/* the round table */
.mm-tablewrap {{ position: relative; width: min(100%, 470px); aspect-ratio: 1; margin: .4rem auto 0; }}
.mm-table {{ position: absolute; inset: 22%; border-radius: 50%; display: grid; place-items: center; text-align: center;
  background: radial-gradient(circle at 50% 40%, #5a2fa0, #2a1450 60%, #170b2f); border: 3px solid #c9b3ff55;
  box-shadow: 0 0 50px {art.PURPLE}55, inset 0 0 30px #0009; }}
.mm-table b {{ display: block; font-family: Cinzel, Georgia, serif; font-size: 2.3rem; color: #fff; line-height: 1; }}
.mm-table small {{ color: #e4e7efaa; font-size: .66rem; letter-spacing: .14em; }}
.mm-candle {{ position: absolute; width: 10px; height: 10px; border-radius: 50%; background: {GOLD};
  box-shadow: 0 0 14px 6px #ffd76a88; animation: mm-flicker 1.7s ease-in-out infinite; }}
@keyframes mm-flicker {{ 50% {{ opacity: .55; transform: scale(.82); }} }}
.mm-seat {{ position: absolute; width: 92px; transform: translate(-50%, -50%); text-align: center; }}
.mm-seat .mm-face {{ width: 66px; height: 66px; margin: 0 auto; border-radius: 50%; overflow: hidden; display: grid; place-items: center;
  background: #291345; border: 2px solid #e4e7ef77; color: #e4e7ef55; font-family: Cinzel, serif; font-size: 1.4rem; }}
.mm-seat .mm-face img {{ width: 100%; height: 100%; object-fit: cover; object-position: top; }}
.mm-seat span {{ display: block; margin-top: .2rem; font-size: .74rem; font-weight: 800; color: #fff;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.mm-seat.mm-joined {{ animation: mm-sit .5s ease-out both; animation-delay: var(--d); }}
@keyframes mm-sit {{ from {{ opacity: 0; transform: translate(-50%, -30%) scale(.7); }} }}
.mm-seat.mm-me .mm-face {{ border-color: {ICE}; box-shadow: 0 0 14px {ICE}; }}
.mm-seat.mm-empty .mm-face {{ border-style: dashed; animation: mm-pulse 1.6s ease-in-out infinite; }}
.mm-seat.mm-empty span {{ color: #e4e7ef66; font-weight: 600; }}
@keyframes mm-pulse {{ 50% {{ border-color: {art.PURPLE}; box-shadow: 0 0 12px {art.PURPLE}88; }} }}
.mm-crown {{ position: absolute; top: -15px; left: 50%; transform: translateX(-50%); color: {GOLD}; font-size: 1.1rem;
  text-shadow: 0 0 8px {GOLD}; font-style: normal; }}
.mm-bubble {{ position: absolute; bottom: 100%; left: 50%; z-index: 3; margin-bottom: 4px; max-width: 150px; width: max-content;
  background: #f8f2ff; color: #10071f; border-radius: 12px 12px 12px 3px; padding: .25rem .55rem; font-size: .72rem; font-weight: 800;
  box-shadow: 0 6px 16px #0008; animation: mm-say {chat.BUBBLE_SECONDS}s ease-out both; }}
@keyframes mm-say {{ 0% {{ opacity: 0; transform: translate(var(--bx), 8px) scale(.7); }} 8% {{ opacity: 1; transform: translate(var(--bx), 0) scale(1); }}
  85% {{ opacity: 1; transform: translate(var(--bx), 0); }} 100% {{ opacity: 0; transform: translate(var(--bx), -6px); }} }}
.mm-bubble {{ --bx: -30%; }} .mm-bubble.mm-to-left {{ --bx: -85%; border-radius: 12px 12px 3px 12px; }}

/* the boxes under the table */
.mm-box {{ background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.12); border-radius: 16px; padding: .8rem .9rem; }}
.mm-box h4 {{ margin: 0 0 .45rem !important; padding: 0 !important; font-size: .72rem !important; letter-spacing: .14em; color: #c79bff !important;
  font-family: inherit !important; }}
.mm-riddle {{ font-size: .95rem; line-height: 1.35; color: #f8f2ff; }}
.mm-box details summary {{ display: inline-block; margin-top: .55rem; cursor: pointer; list-style: none; font-size: .78rem; color: {ICE};
  border: 1px solid {ICE}66; border-radius: 999px; padding: .2rem .65rem; }}
.mm-box details summary::-webkit-details-marker {{ display: none; }}
.mm-box details[open] summary {{ display: none; }}
.mm-box details b {{ display: inline-block; margin-top: .5rem; color: {ICE}; font-size: 1rem; }}
.mm-feed {{ font-size: .78rem; color: #e4e7efaa; line-height: 1.55; margin-top: .3rem; }}
.mm-feed b {{ color: #fff; }}
.mm-steps-list {{ display: grid; gap: .4rem; }}
.mm-steps-list div {{ display: flex; align-items: center; gap: .55rem; font-size: .84rem; color: #e4e7efcc; }}
.mm-steps-list i {{ font-style: normal; display: inline-grid; place-items: center; flex: none; width: 22px; height: 22px; border-radius: 50%;
  background: #b57bff; color: #10071f; font-size: .72rem; font-weight: 800; }}
.mm-steps-list b {{ color: #fff; }}
.mm-hello-title {{ font-size: .72rem; letter-spacing: .14em; color: #c79bff; font-weight: 700; margin-bottom: -.3rem; }}

/* greeting buttons: small pills with our drawn icons, 2 x 2 */
.st-key-mm_hello {{ gap: .45rem !important; }}
.st-key-mm_hello [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: .45rem !important; }}
.st-key-mm_hello [data-testid="stColumn"] {{ min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }}
.st-key-mm_hello div.stButton > button {{ border-radius: 999px !important; min-height: 2.3rem; padding: .2rem .7rem .2rem 2.1rem !important;
  background-color: rgba(255,255,255,.06) !important; background-repeat: no-repeat !important; background-position: .65rem center !important;
  background-size: 20px 20px !important; border: 1px solid rgba(255,255,255,.2) !important; box-shadow: none !important; }}
.st-key-mm_hello div.stButton > button p {{ font-size: .8rem !important; white-space: nowrap; }}
.st-key-mm_hello div.stButton > button:hover {{ border-color: {art.PURPLE} !important; background-color: rgba(181,123,255,.18) !important; }}
{"".join(f'.st-key-mm_hello_{kind} div.stButton > button {{ background-image: url("{icon}") !important; }}' for kind, icon in GREETING_ICONS.items())}

/* start / waiting */
.st-key-mm_start div.stButton > button {{ min-height: 3.1rem; border-radius: 14px !important; }}
.st-key-mm_start div.stButton > button p {{ font-weight: 800 !important; font-size: 1.05rem !important; }}
.st-key-mm_start div.stButton > button:disabled {{ background: rgba(255,255,255,.07) !important; border: 1px dashed rgba(255,255,255,.3) !important;
  box-shadow: none !important; }}
.st-key-mm_start div.stButton > button:disabled p {{ color: #e4e7ef88 !important; }}
.st-key-mm_leave div.stButton > button {{ background: transparent !important; border: 1px solid rgba(255,255,255,.25) !important;
  box-shadow: none !important; min-height: 2rem; }}
.st-key-mm_leave div.stButton > button p {{ color: #e4e7efaa !important; font-size: .85rem !important; }}
.mm-waiting-host {{ text-align: center; padding: .85rem; border-radius: 14px; border: 1px dashed rgba(255,255,255,.3);
  color: #e4e7efcc; font-weight: 700; }}

@media (max-width: 560px) {{
  .mm-seat {{ width: 72px; }} .mm-seat .mm-face {{ width: 48px; height: 48px; font-size: 1.1rem; }}
  .mm-seat span {{ font-size: .62rem; }} .mm-table b {{ font-size: 1.7rem; }} .mm-table small {{ font-size: .55rem; }}
  .mm-code b {{ font-size: 1.35rem; }} .mm-lobby-tag {{ letter-spacing: .08em; font-size: .66rem; }} .mm-bubble {{ max-width: 120px; font-size: .64rem; }}
  /* On a phone Streamlit stacks these columns. Give each lobby section room
     to breathe rather than making the riddle, greetings, and guide touch. */
  .st-key-mm_riddle_section, .st-key-mm_hello_section {{ margin-bottom: 1.15rem; }}
  .mm-box {{ margin-bottom: 1.15rem; }}
  .st-key-mm_hello {{ margin-top: .35rem; }}
  .mm-feed {{ margin-top: .7rem; line-height: 1.7; }}
}}
</style>"""


def _seats(tour):
    """Who is at the table, in order (what the page shows)."""
    return tuple(player["id"] for player in tour["players"])


def _riddle_index(now):
    return int(now // RIDDLE_SECONDS) % len(RIDDLES)


def _signature(tour, now):
    """Everything the page shows that can change while waiting."""
    return (_seats(tour), chat.latest_id(tour), _riddle_index(now))


@st.fragment(run_every=WATCH_EVERY)
def _watch(code, me, signature):
    """Invisible: redraw the page when the game starts, someone joins, leaves or
    greets, or the riddle changes."""
    tour = live.peek(code)
    if (tour is None or tour["status"] != "lobby" or not rules.find_player(tour, me)
            or _signature(tour, time.time()) != signature):
        st.rerun(scope="app")


def show(code, me):
    live.forget()                      # the watcher starts from data at least this new
    tour = storage.load(code)
    # Something changed that needs a different screen: the game started,
    # the tournament vanished, or this player was removed.
    if tour is None or tour["status"] != "lobby" or not rules.find_player(tour, me):
        st.rerun(scope="app")
    now = time.time()
    _watch(code, me, _signature(tour, now))

    st.markdown(STYLE, unsafe_allow_html=True)
    common.show_wordmark()
    guests = "FIVE" if rules.table_size(tour) == 5 else "EIGHT"
    st.markdown(f"<div class='mm-lobby-tag'>{guests} GUESTS · ONE MANSION · ONE LAST CLUE</div>", unsafe_allow_html=True)
    common.show_flash()
    _code_and_link(code, tour, me)
    st.markdown(_table(tour, me, now), unsafe_allow_html=True)
    if rules.is_host(tour, me) and len(tour["players"]) > 1:
        _manage_seats(code, tour, me)

    riddle_col, hello_col = st.columns(2)
    with riddle_col:
        with st.container(key="mm_riddle_section", border=False):
            index = _riddle_index(now)
            question, answer = RIDDLES[index]
            # Every new riddle must start with its answer hidden. A browser keeps an opened
            # "Tap to reveal" box open if the page only swaps the text inside it, so each
            # riddle gets its own box (own key) and neighbouring riddles use a different
            # outer element (section / article): the browser then builds a new, closed box.
            tag = "section" if index % 2 else "article"
            with st.container(key=f"mm_riddle_{index}"):
                st.markdown(f"<{tag} class='mm-box'><h4>WARM-UP RIDDLE</h4><div class='mm-riddle'>{question}</div>"
                            f"<details><summary>Tap to reveal</summary><b>{answer}</b></details></{tag}>",
                            unsafe_allow_html=True)
    with hello_col:
        with st.container(key="mm_hello_section", border=False):
            _say_hello(code, tour, me)
    steps = "".join(f"<div><i>{n}</i><span><b>{name}</b> · {what}</span></div>" for n, name, what in STEPS)
    st.markdown(f"<div class='mm-box'><h4>HOW THE NIGHT GOES</h4><div class='mm-steps-list'>{steps}</div>"
                "<div class='mm-feed' style='margin-top:.55rem'>Knocked out? You stay as a spectator: make calls "
                "on who wins and send reactions.</div></div>", unsafe_allow_html=True)
    _start_or_wait(code, tour, me)


def _code_and_link(code, tour, me):
    with st.container(key="mm_lobby_top"):
        code_col, link_col = st.columns([1, 3])
        with code_col:
            st.markdown(f"<div class='mm-code'><small>JOIN CODE</small><b>{code}</b></div>", unsafe_allow_html=True)
        with link_col:
            link = common.join_link(code)
            if link:
                st.markdown("<div class='mm-invite'>INVITE LINK · TAP ⧉ TO COPY</div>", unsafe_allow_html=True)
                st.code(link, language=None)
    st.caption("Share the code or this link, not your own page address: your address is your seat in the game.")
    _qr_invite(code)


def _qr_invite(code):
    """Any seated detective can show the join QR code to invite another player."""
    link = common.join_link(code)
    if not link:
        return
    with st.container(key="mm_qr_toggle"):
        shown = st.toggle("Show a QR code to invite players", key=f"mm_qr_{code}")
    if not shown:
        return
    st.markdown(
        "<div class='mm-qr'>"
        "<div class='mm-qr-label'>SCAN TO JOIN</div>"
        f"<div class='mm-qr-code'>{qr.svg(link)}</div>"
        f"<div class='mm-qr-foot'>Point your phone camera at the code · or type <b>{html.escape(code)}</b></div>"
        "</div>",
        unsafe_allow_html=True,
    )


def _table(tour, me, now):
    players = tour["players"]
    bubbles = chat.bubbles(tour, now)
    seats = []
    size = rules.table_size(tour)              # 5 or 8 seats, as the host chose
    for index in range(size):
        angle = math.radians(-90 + index * 360 / size)
        x, y = 50 + 41 * math.cos(angle), 50 + 41 * math.sin(angle)
        where = f"left:{x:.1f}%;top:{y:.1f}%"
        if index < len(players):
            player = players[index]
            classes = "mm-seat mm-joined" + (" mm-me" if player["id"] == me else "")
            crown = "<i class='mm-crown'>♛</i>" if player["id"] == tour["host_id"] else ""
            bubble = ""
            if player["id"] in bubbles:
                said = bubbles[player["id"]]
                side = " mm-to-left" if x > 55 else ""        # seats on the right: bubble opens to the left
                bubble = (f"<div class='mm-bubble{side}' style='animation-delay:-{said['age']:.2f}s'>"
                          f"{chat.GREETINGS[said['kind']][1]}</div>")
            seats.append(f"<div class='{classes}' style='{where};--d:{index * .08:.2f}s'>{bubble}{crown}"
                         f"<div class='mm-face'><img src='{avatars.picture(player, 160)}' alt=''></div>"
                         f"<span>{html.escape(player['name'])}</span></div>")
        else:
            seats.append(f"<div class='mm-seat mm-empty' style='{where}'><div class='mm-face'>?</div><span>waiting…</span></div>")
    seated = len(players)
    middle = (f"<b>{seated}/{size}</b><small>DETECTIVES SEATED</small>" if seated < size
              else f"<b>{size}/{size}</b><small>THE TABLE IS FULL</small>")
    return (f"<div class='mm-tablewrap'><div class='mm-table'><div>{middle}</div></div>"
            "<div class='mm-candle' style='left:38%;top:37%'></div><div class='mm-candle' style='left:60%;top:61%;animation-delay:.6s'></div>"
            + "".join(seats) + "</div>")


def _manage_seats(code, tour, me):
    with st.popover("Manage seats (host)"):
        st.caption("Remove someone who joined by mistake or left.")
        for player in tour["players"]:
            if player["id"] == me:
                continue
            if st.button(f"Remove {common.player_label(player)}", key=f"remove_{player['id']}", width="stretch"):
                _, message = storage.update(code, rules.remove_player, me, player["id"])
                common.flash("info", message)
                st.rerun()


def _say_hello(code, tour, me):
    st.markdown("<div class='mm-hello-title'>SAY HELLO</div>", unsafe_allow_html=True)
    kinds = list(chat.GREETINGS)
    with st.container(key="mm_hello"):
        for start in (0, 2):
            columns = st.columns(2)
            for column, kind in zip(columns, kinds[start:start + 2]):
                with column:
                    if st.button(chat.GREETINGS[kind][0], key=f"mm_hello_{kind}", width="stretch"):
                        _, message = storage.update(code, chat.greet, me, kind, time.time())
                        # A successful greeting is visible in the shared bubble/feed.
                        # Do not create a toast immediately before rerunning: on some
                        # phones that can interrupt the page redraw.
                        if message != chat.GREETINGS[kind][1]:
                            st.toast(message)
                        st.rerun()
    lines = []
    newest = tour["players"][-1] if len(tour["players"]) > 1 else None
    for pid, kind in chat.feed(tour):
        who = rules.find_player(tour, pid)
        lines.append(f"<b>{html.escape(who['name'])}</b>: {chat.GREETINGS[kind][1]}")
    if newest:
        lines.append(f"<b>{html.escape(newest['name'])}</b> just took a seat")
    if lines:
        st.markdown("<div class='mm-feed'>" + "<br>".join(lines[:4]) + "</div>", unsafe_allow_html=True)


def _start_or_wait(code, tour, me):
    count = len(tour["players"])
    if rules.is_host(tour, me):
        missing = rules.table_size(tour) - count
        label = "Start the tournament" if missing == 0 else (
            f"Start · waiting for {missing} more player{'s' if missing != 1 else ''}")
        with st.container(key="mm_start"):
            if st.button(label, type="primary", disabled=missing > 0, width="stretch"):
                _, message = storage.update(code, rules.start, me)
                common.flash("success", message)
                st.rerun(scope="app")
    else:
        st.markdown("<div class='mm-waiting-host'>Waiting for the host to start…</div>", unsafe_allow_html=True)
        if st.button("Leave the table", key="mm_leave"):
            _, message = storage.update(code, rules.leave, me)
            common.flash("info", message)
            common.go_home()
