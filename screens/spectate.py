"""What spectators (eliminated detectives) see and do during Rounds 2 and 3.

* live(): a small part of the page that refreshes by itself every 2 seconds. It
  shows the crowd bar (who the spectators back) and makes reactions pop up at the
  edge of everyone's screen. It has nothing to tap.
* panel(): for spectators only, drawn as part of the main page (so the buttons can
  never go missing): make your call, and the six reaction buttons.
* calls_summary(): who called it, for the results screens.

The rules (who may do what) live in spectators.py. Every drawing here is our own
SVG; player names are escaped before they go into any HTML.
"""

import html
import time

import streamlit as st

import spectators as sp
import storage
import tournament as rules
from screens import art, avatars, common, live as shared

ICE, ALARM, GOLD = art.TILE_COLOURS["ice"], "#ff6b7a", "#f7d84a"


def _html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def _name(tour, pid):
    player = rules.find_player(tour, pid)
    return player["name"] if player else "?"


# --- our drawings for the six reactions -----------------------------------------

def _svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{body}</svg>'


DRAWINGS = {
    # Elementary!: a detective's pipe with smoke rings
    "elementary": _svg(
        '<path d="M8 30 Q20 30 30 36 L34 38" stroke="#5b3a1a" stroke-width="6" fill="none" stroke-linecap="round"/>'
        '<path d="M30 30 L52 30 Q54 50 41 52 Q30 52 30 40 Z" fill="#8a5a2b" stroke="#5b3a1a" stroke-width="2.5"/>'
        '<ellipse cx="41" cy="30" rx="11" ry="3.5" fill="#2a170a"/>'
        f'<path d="M40 24 Q34 18 40 13 Q46 8 40 3" stroke="{art.SILVER}" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
        f'<circle cx="49" cy="17" r="3.5" fill="none" stroke="{art.SILVER}" stroke-width="2"/>'
        f'<circle cx="54" cy="8" r="2.5" fill="none" stroke="{art.SILVER}" stroke-width="1.8"/>'),
    # I knew it!: a light bulb with a spark
    "knew_it": _svg(
        f'<circle cx="32" cy="26" r="15" fill="{GOLD}" stroke="{art.IVORY}" stroke-width="2"/>'
        '<path d="M26 26 Q32 34 38 26" stroke="#b5891f" stroke-width="2.5" fill="none"/>'
        f'<rect x="25" y="40" width="14" height="5" rx="2" fill="{art.SILVER}"/>'
        f'<rect x="26" y="46" width="12" height="4" rx="2" fill="#aeb3c2"/>'
        f'<path d="M32 4 L32 0 M50 10 L54 6 M14 10 L10 6 M56 26 L62 26 M8 26 L2 26" stroke="{ICE}" stroke-width="3" stroke-linecap="round"/>'),
    # Too slow, detective!: an hourglass
    "too_slow": _svg(
        f'<rect x="14" y="6" width="36" height="6" rx="3" fill="{art.PURPLE}"/>'
        f'<rect x="14" y="52" width="36" height="6" rx="3" fill="{art.PURPLE}"/>'
        f'<path d="M18 12 L46 12 L34 32 L46 52 L18 52 L30 32 Z" fill="#ffffff22" stroke="{art.SILVER}" stroke-width="2.5"/>'
        f'<path d="M22 16 L42 16 L33 28 L31 28 Z" fill="{GOLD}"/><path d="M31 33 L33 33 L33 44 L31 44 Z" fill="{GOLD}"/>'
        f'<path d="M22 50 Q32 40 42 50 Z" fill="{GOLD}"/>'),
    # Suspicious…: a magnifying glass
    "magnifier": _svg(
        f'<circle cx="26" cy="26" r="16" fill="{ICE}55" stroke="{art.SILVER}" stroke-width="5"/>'
        '<path d="M18 20 Q22 14 28 14" stroke="#ffffffcc" stroke-width="3" fill="none" stroke-linecap="round"/>'
        f'<path d="M38 38 L56 56" stroke="{art.PURPLE}" stroke-width="8" stroke-linecap="round"/>'),
    # On their trail: two pairs of shoe prints walking up the screen
    "footprints": _svg(
        f'<g transform="translate(18 48) rotate(-12)"><path d="M0 -12 Q7 -12 6 -2 Q5 4 0 4 Q-5 4 -6 -2 Q-7 -12 0 -12 Z" fill="{art.SILVER}"/><ellipse cx="0" cy="10" rx="4.5" ry="4" fill="{art.SILVER}"/></g><g transform="translate(32 38) rotate(10)"><path d="M0 -12 Q7 -12 6 -2 Q5 4 0 4 Q-5 4 -6 -2 Q-7 -12 0 -12 Z" fill="{art.SILVER}"/><ellipse cx="0" cy="10" rx="4.5" ry="4" fill="{art.SILVER}"/></g><g transform="translate(30 22) rotate(-12)"><path d="M0 -12 Q7 -12 6 -2 Q5 4 0 4 Q-5 4 -6 -2 Q-7 -12 0 -12 Z" fill="{art.PURPLE}"/><ellipse cx="0" cy="10" rx="4.5" ry="4" fill="{art.PURPLE}"/></g><g transform="translate(45 13) rotate(10)"><path d="M0 -12 Q7 -12 6 -2 Q5 4 0 4 Q-5 4 -6 -2 Q-7 -12 0 -12 Z" fill="{art.PURPLE}"/><ellipse cx="0" cy="10" rx="4.5" ry="4" fill="{art.PURPLE}"/></g>'),
    # Sound the alarm!: a ringing bell
    "alarm": _svg(
        f'<path d="M18 44 Q18 18 32 16 Q46 18 46 44 L50 48 L14 48 Z" fill="{GOLD}" stroke="{art.IVORY}" stroke-width="2"/>'
        '<circle cx="32" cy="53" r="5" fill="#b5891f"/><rect x="29" y="10" width="6" height="7" rx="2" fill="#b5891f"/>'
        f'<path d="M8 22 Q4 32 8 42 M56 22 Q60 32 56 42 M3 18 Q-2 32 3 46 M61 18 Q66 32 61 46" stroke="{ALARM}" '
        'stroke-width="3" fill="none" stroke-linecap="round"/>'),
}


def _drawing_url(kind):
    import base64
    return "data:image/svg+xml;base64," + base64.b64encode(DRAWINGS[kind].encode()).decode()


# --- the part that refreshes by itself -----------------------------------------------

STYLE = f"""<style>
@keyframes mm-rx-bubble {{ 0% {{ transform: translateX(-130%); opacity: 0; }} 8% {{ transform: translateX(6%); opacity: 1; }}
                           12% {{ transform: none; }} 86% {{ transform: none; opacity: 1; }}
                           100% {{ transform: translateX(-130%); opacity: 0; }} }}
@keyframes mm-rx-fly {{ 0% {{ transform: translateX(-35vw); opacity: 0; }} 6% {{ opacity: 1; }} 94% {{ opacity: 1; }}
                        100% {{ transform: translateX(110vw); opacity: 0; }} }}
@keyframes mm-rx-wobble {{ 0%,100% {{ transform: rotate(-12deg) translateY(0); }} 50% {{ transform: rotate(12deg) translateY(-8px); }} }}
.mm-rx {{ position: fixed; z-index: 998; pointer-events: none; animation-fill-mode: both; }}
.mm-rx-bubble {{ left: 10px; display: flex; align-items: flex-end; gap: .35rem; max-width: 72vw;
                animation: mm-rx-bubble {sp.REACTION_SECONDS}s ease-out both; }}
.mm-rx-bubble img.mm-rx-face {{ width: 46px; height: 46px; border-radius: 50%; object-fit: contain; flex: none;
                               background: #291345; border: 2px solid {art.PURPLE}; box-shadow: 0 0 12px {art.PURPLE}; }}
.mm-rx-say {{ position: relative; background: {art.IVORY}; color: {art.BG}; border-radius: 14px 14px 14px 4px;
             padding: .3rem .65rem .35rem; font-weight: 900; font-size: .92rem; line-height: 1.15;
             box-shadow: 0 6px 18px #0008; display: flex; align-items: center; gap: .4rem; }}
.mm-rx-say img {{ width: 26px; height: 26px; }}
.mm-rx-who {{ display: block; font-size: .62rem; font-weight: 800; letter-spacing: .05em; color: #5d4a86; }}
.mm-rx-sticker {{ left: 0; display: flex; align-items: center; gap: .3rem;
                 animation: mm-rx-fly {sp.REACTION_SECONDS}s linear both; }}
.mm-rx-sticker img {{ width: 54px; height: 54px; filter: drop-shadow(0 4px 10px #000a);
                     animation: mm-rx-wobble .6s ease-in-out infinite; }}
.mm-rx-tag {{ background: #10071fdd; border: 2px solid {ICE}; color: {art.IVORY}; border-radius: 999px;
             padding: .15rem .6rem; font-weight: 900; font-size: .8rem; white-space: nowrap; box-shadow: 0 0 12px {ICE}66; }}
.mm-rx-tag b {{ color: {ICE}; }}
.mm-crowd {{ background: rgba(29,20,56,.85); border: 1px solid {art.SILVER}33; border-radius: 14px;
            padding: .5rem .8rem .6rem; margin: 0 0 .9rem; }}
.mm-crowd-title {{ text-align: center; color: {art.SILVER}; font-size: .7rem; font-weight: 900; letter-spacing: .14em; margin-bottom: .35rem; }}
.mm-crowd-row {{ display: flex; align-items: center; gap: .55rem; }}
.mm-crowd-side {{ flex: 0 0 auto; display: flex; flex-direction: column; align-items: center; width: 96px; min-width: 0; }}
.mm-crowd-faces {{ display: flex; justify-content: center; }}
.mm-crowd-faces img {{ width: 34px; height: 34px; border-radius: 50%; object-fit: contain; background: #291345;
                      border: 2px solid {art.SILVER}88; margin: 0 -5px; }}
.mm-crowd-name {{ color: {art.IVORY}; font-weight: 800; font-size: .7rem; max-width: 96px; text-align: center;
                 white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: .15rem; }}
.mm-crowd-bar {{ flex: 1 1 auto; display: flex; height: 22px; border-radius: 11px; overflow: hidden; background: #ffffff18; }}
.mm-crowd-bar div {{ display: flex; align-items: center; justify-content: center; color: {art.BG}; font-weight: 900;
                    font-size: .78rem; transition: width .8s ease; min-width: 0; }}
.mm-crowd-left {{ background: linear-gradient(90deg, {art.PURPLE}, #c9a6ff); }}
.mm-crowd-right {{ background: linear-gradient(90deg, #bdefff, {ICE}); }}
.mm-crowd-none {{ flex: 1 1 auto; text-align: center; color: {art.SILVER}99; font-size: .78rem; font-style: italic; }}
.mm-crowd-r2 {{ padding: .55rem clamp(.6rem,2.5vw,1.8rem) .65rem; border-radius: 18px; }}
.mm-crowd-r2 .mm-crowd-title {{ font-size: clamp(.76rem,1.2vw,.9rem); margin-bottom: .3rem; }}
.mm-crowd-r2-votes {{ max-width: 1000px; margin: .2rem auto 0; text-align: center;
                      color: {art.SILVER}; font-size: .8rem; font-weight: 800; }}
.mm-crowd-r2-vote-counts {{ display: flex; justify-content: space-between; margin-bottom: .25rem; }}
.mm-crowd-r2-vote-track {{ display: flex; height: 12px; overflow: hidden; border-radius: 8px; background: #ffffff18; }}
.mm-crowd-r2-vote-track div {{ min-width: 0; transition: width .8s ease; }}
.mm-crowd-r2-vote-left {{ background: linear-gradient(90deg, {art.PURPLE}, #c9a6ff); }}
.mm-crowd-r2-vote-right {{ background: linear-gradient(90deg, #bdefff, {ICE}); }}
@media (max-width: 560px) {{
  .mm-crowd-r2 {{ padding: .45rem .35rem .55rem; }}
  .mm-crowd-r2-votes {{ font-size: .68rem; }}
}}
@media (max-width: 560px) {{ .mm-crowd-side {{ width: 70px; }} .mm-crowd-name {{ max-width: 70px; font-size: .62rem; }}
  .mm-rx-say {{ font-size: .8rem; }} .mm-rx-sticker img {{ width: 44px; height: 44px; }} .mm-rx-tag {{ font-size: .7rem; }} }}
</style>"""


def _reactions(tour, now):
    """The reactions on screen right now. Each one starts its animation `age`
    seconds in, so a refresh carries on where it was instead of restarting."""
    parts = []
    for reaction in sp.recent_reactions(tour, now):
        kind, info = reaction["kind"], sp.REACTIONS[reaction["kind"]]
        who = html.escape(_name(tour, reaction["by"]))
        slot = reaction["id"] % 3
        delay = f"animation-delay:-{reaction['age']:.2f}s"
        if info["style"] == "bubble":
            face = avatars.picture(rules.find_player(tour, reaction["by"]), 96)
            parts.append(
                f'<div class="mm-rx mm-rx-bubble" style="bottom:{14 + slot * 70}px;{delay}">'
                f'<img class="mm-rx-face" src="{face}" alt=""/>'
                f'<div class="mm-rx-say"><img src="{_drawing_url(kind)}" alt=""/>'
                f'<span><span class="mm-rx-who">{who}</span>{info["text"]}</span></div></div>')
        else:
            parts.append(
                f'<div class="mm-rx mm-rx-sticker" style="top:{70 + slot * 62}px;{delay}">'
                f'<img src="{_drawing_url(kind)}" alt=""/>'
                f'<span class="mm-rx-tag"><b>{who}</b> · {info["text"]}</span></div>')
    return "".join(parts)


def _side(tour, pids):
    faces = "".join(f'<img src="{avatars.picture(rules.find_player(tour, pid), 96)}" alt=""/>' for pid in pids)
    name = html.escape(" & ".join(_name(tour, pid) for pid in pids))
    return f'<div class="mm-crowd-side"><div class="mm-crowd-faces">{faces}</div><div class="mm-crowd-name">{name}</div></div>'


def _round2_crowd_bar(title, left, right, counts, total):
    left_count, right_count = counts[left], counts[right]
    if total:
        share = round(100 * left_count / total)
        votes = (
            '<div class="mm-crowd-r2-votes"><div class="mm-crowd-r2-vote-counts">'
            f'<span>Duo 1: {left_count} call{"s" if left_count != 1 else ""}</span>'
            f'<span>Duo 2: {right_count} call{"s" if right_count != 1 else ""}</span></div>'
            '<div class="mm-crowd-r2-vote-track">'
            f'<div class="mm-crowd-r2-vote-left" style="width:{share}%"></div>'
            f'<div class="mm-crowd-r2-vote-right" style="width:{100 - share}%"></div>'
            '</div></div>'
        )
    else:
        votes = '<div class="mm-crowd-r2-votes">No calls yet…</div>'
    return (f'<div class="mm-crowd mm-crowd-r2"><div class="mm-crowd-title">{title}</div>'
            f'{votes}</div>')


def crowd_bar(tour, round_name):
    """Who the spectators back, live: the two choices with a split bar between them."""
    options = sp.call_options(tour, round_name) or sp._decided_options(tour, round_name)
    if len(options) != 2:
        return ""
    (left, left_pids), (right, right_pids) = list(options.items())
    counts = sp.crowd(tour, round_name)
    total = counts[left] + counts[right]
    title = "THE CROWD'S CALL · WHICH DUO OPENS THE VAULT?" if round_name == "round2" else "THE CROWD'S CALL · WHO WINS THE CASE?"
    if round_name == "round2":
        return _round2_crowd_bar(title, left, right, counts, total)
    if total == 0:
        middle = '<div class="mm-crowd-none">No calls yet…</div>'
    else:
        share = round(100 * counts[left] / total)
        middle = (f'<div class="mm-crowd-bar"><div class="mm-crowd-left" style="width:{share}%">{counts[left] or ""}</div>'
                  f'<div class="mm-crowd-right" style="width:{100 - share}%">{counts[right] or ""}</div></div>')
    return (f'<div class="mm-crowd"><div class="mm-crowd-title">{title}</div>'
            f'<div class="mm-crowd-row">{_side(tour, left_pids)}{middle}{_side(tour, right_pids)}</div></div>')


def _moment(tour):
    """What the main page was drawn for: if this changes, the page must be redrawn
    (e.g. calls just opened or closed, or the Round 2 intro ends)."""
    round2_state = tour.get("round2") or {}
    intro_ends_at = round2_state.get("intro_ends_at")
    intro_active = (
        tour.get("status") == "round2"
        and (intro_ends_at is None or time.time() < intro_ends_at)
    )
    return (tour.get("status"), sp.open_call(tour), intro_active)


@st.fragment(run_every="2s")
def live(code, me, drawn_for):
    """Crowd bar + reactions popping up at the edge, refreshed every 2 seconds.
    Nothing to tap here. Redraws the whole page when calls open or close."""
    tour = shared.peek(code)
    if tour is None:
        return
    if _moment(tour) != drawn_for:
        st.rerun()
    round_name = sp.open_call(tour)
    bar = crowd_bar(tour, round_name) if round_name else ""
    _html(STYLE + bar + _reactions(tour, time.time()))


# --- the spectator's own controls (main page) ----------------------------------------

def _choice_style(key, pictures):
    """Turns the button with this key into a card showing the detectives you'd back."""
    k = art.css_key(key)
    b = f".st-key-{k} div.stButton > button"
    if len(pictures) == 2:
        bg = (f'url("{pictures[0]}") 22% 14px / auto 92px no-repeat, url("{pictures[1]}") 78% 14px / auto 92px no-repeat, ')
    else:
        bg = f'url("{pictures[0]}") center 10px / auto 100px no-repeat, '
    return f"""<style>
{b} {{ background: {bg} radial-gradient(circle at 50% 35%, #4b2a86, #1d1438 75%) !important;
      border: 2px solid {art.PURPLE} !important; border-radius: 16px !important; min-height: 160px;
      padding-top: 118px !important; box-shadow: 0 0 16px {art.PURPLE}55; transition: transform .15s; }}
{b}:hover {{ transform: translateY(-4px); box-shadow: 0 0 26px {ICE}88; border-color: {ICE} !important; }}
{b} p {{ color: {art.IVORY} !important; font-weight: 900 !important; }}
</style>"""


def _grid(name, count):
    key = art.css_key(f"grid_{name}")
    _html(art.phone_grid_style(key))
    with st.container(key=key):
        return st.columns(count)


def _call_section(code, tour, me, round_name):
    options = sp.call_options(tour, round_name)
    question = ("Which duo opens the vault first?" if round_name == "round2"
                else "Who becomes the Mastermind champion?")
    _html(art.heading("solutions", "Make your call", size=30, level=3))
    st.caption(f"{question} One call, no changing your mind. Everyone sees the crowd bar.")
    mine = sp.my_call(tour, me, round_name)
    if mine is not None:
        names = " & ".join(_name(tour, pid) for pid in options.get(mine, []))
        _html(art.banner("through", f"Your call is locked in: {html.escape(names)}"))
        return
    for column, (choice, pids) in zip(_grid(f"call_{round_name}", len(options)), options.items()):
        key = f"call_{round_name}_{choice}"
        with column:
            _html(_choice_style(key, [avatars.picture(rules.find_player(tour, pid), 200) for pid in pids]))
            label = " & ".join(_name(tour, pid) for pid in pids)
            if st.button(common.safe(label), key=art.css_key(key), width="stretch"):
                _, message = storage.update(code, sp.make_call, me, round_name, choice, time.time())
                st.toast(message)
                st.rerun()


def _reaction_pad(code, tour, me):
    _html(art.heading("finish", "Send a reaction", size=30, level=3))
    st.caption("It pops up at the edge of everyone's screen for a few seconds.")
    kinds = list(sp.REACTIONS)
    for row in range(2):
        for column, kind in zip(_grid(f"reactions_{row}", 3), kinds[row * 3:row * 3 + 3]):
            key = art.css_key(f"react_{kind}")
            with column:
                _html(art.picture_button_style(key, DRAWINGS[kind], height=104))
                if st.button(sp.REACTIONS[kind]["text"], key=key, width="stretch"):
                    _, message = storage.update(code, sp.react, me, kind, time.time())
                    st.toast("Sent!" if message == sp.REACTIONS[kind]["text"] else message)


def panel(code, tour, me):
    """Make your call + the reaction buttons. Only spectators see this."""
    if tour is None or not sp.is_spectator(tour, me):
        return
    st.divider()
    _html('<div style="text-align:center;color:#d7b8f2;font-size:.78rem;font-weight:900;'
          'letter-spacing:.16em;margin-bottom:.4rem">YOU ARE WATCHING AS A SPECTATOR</div>')
    round_name = sp.open_call(tour)
    if round_name:
        _call_section(code, tour, me, round_name)
    if tour.get("status") in sp.REACTION_STATUSES:
        _reaction_pad(code, tour, me)


def start(code, me):
    """Call this at the top of a Round 2 / Round 3 screen: draws the live part and
    returns the tournament as it was when the page was drawn."""
    shared.forget()
    tour = storage.load(code)
    if tour is not None:
        live(code, me, _moment(tour))
    return tour


# --- results ---------------------------------------------------------------------------

def calls_summary(tour, round_name):
    """'Who called it' for a decided round, as HTML (empty if nobody made a call)."""
    calls = sp._state(tour)["calls"].get(round_name, {})
    if not calls or sp.correct_choice(tour, round_name) is None:
        return ""
    right = sp.who_called_it(tour, round_name)
    if right:
        names = ", ".join(html.escape(_name(tour, pid)) for pid in right)
        text = f"{names} called it! ({len(right)} of {len(calls)} spectator{'s' if len(calls) != 1 else ''})"
    elif len(calls) == 1:
        text = "Nobody saw that coming: the only call was wrong."
    else:
        text = f"Nobody saw that coming: all {len(calls)} spectators called it wrong."
    return STYLE + f'<div class="mm-calls">{crowd_bar(tour, round_name)}{art.banner("solutions", text)}</div>'
