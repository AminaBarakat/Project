"""The pictures for Round 1, drawn in code as SVG (scalable vector graphics).

Drawing them ourselves means there are no image files to manage, no copyright
questions, and they look the same on every phone. Every picture uses the same
style: a deep purple-black card with silver line-art and a few accent colours,
matching the game's purple-and-silver theme.

Nothing here contains text typed by players, so it is safe to show as HTML.
"""

import base64

BG = "#1d1438"          # dark purple, used for small details drawn on light parts
SILVER = "#e4e7ef"      # line-art and borders
IVORY = "#f4f5f9"       # light fills
PURPLE = "#a78bfa"
RED = "#d9534f"
GREEN = "#5cb85c"
BLUE = "#4a90d9"
YELLOW = "#f0c419"

# The four Pattern Wall colours: silver, purple, royal blue and ice blue.
# Different enough in shade to tell apart, all in the game's theme.
TILE_COLOURS = {"purple": "#b57bff", "silver": "#eef0f5", "royal": "#3b6bff", "ice": "#9be4ff"}


# The card behind every picture: a purple-to-royal-blue gradient with a soft glow
# in the middle and a bright silver edge, so the drawing "pops".
_CARD_PAINT = (
    '<defs>'
    '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#3a2470"/><stop offset="1" stop-color="#1f2a6e"/></linearGradient>'
    '<radialGradient id="glow" cx="0.5" cy="0.45" r="0.55">'
    '<stop offset="0" stop-color="#8f7bff" stop-opacity="0.55"/><stop offset="1" stop-color="#8f7bff" stop-opacity="0"/>'
    '</radialGradient></defs>'
)


def _svg(body, size=100, background=True):
    card = ""
    if background:
        r = size * 0.12
        card = (f'{_CARD_PAINT}'
                f'<rect x="2" y="2" width="{size - 4}" height="{size - 4}" rx="{r}" fill="url(#bg)"/>'
                f'<rect x="2" y="2" width="{size - 4}" height="{size - 4}" rx="{r}" fill="url(#glow)"/>'
                f'<rect x="2" y="2" width="{size - 4}" height="{size - 4}" rx="{r}" fill="none" '
                f'stroke="{SILVER}" stroke-width="{max(2.5, size / 40)}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
            f'{card}{body}</svg>')


def img(svg, width="100%"):
    """HTML that shows an SVG picture (as an image, so the browser draws it safely)."""
    data = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{data}" style="width:{width};max-width:100%;display:block;margin:auto"/>'


def card(svg, caption="", width="100%"):
    """A picture with a small caption under it."""
    text = f'<div style="text-align:center;font-size:0.85rem;margin-top:0.2rem">{caption}</div>' if caption else ""
    return f'<div style="margin-bottom:0.4rem">{img(svg, width)}{text}</div>'


def row(svgs_with_captions, columns):
    """Several cards side by side, wrapping onto new lines (works on narrow phones)."""
    cells = "".join(
        f'<div style="flex:0 0 calc({100 / columns}% - 0.5rem)">{card(svg, caption)}</div>'
        for svg, caption in svgs_with_captions
    )
    return f'<div style="display:flex;flex-wrap:wrap;gap:0.5rem;justify-content:center">{cells}</div>'


# --- Memory Table objects --------------------------------------------------------

_LINE = f'fill="none" stroke="{SILVER}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"'

ITEMS = {
    "Key": f'''
        <circle cx="32" cy="50" r="14" {_LINE}/>
        <circle cx="32" cy="50" r="5" {_LINE}/>
        <path d="M46 50 H82 M70 50 V62 M80 50 V60" {_LINE}/>''',
    "Compass": f'''
        <circle cx="50" cy="52" r="30" {_LINE}/>
        <path d="M50 30 L57 52 L50 74 L43 52 Z" fill="{IVORY}"/>
        <path d="M50 30 L57 52 L43 52 Z" fill="{RED}"/>
        <circle cx="50" cy="52" r="3" fill="{BG}"/>
        <text x="50" y="19" font-size="11" text-anchor="middle" fill="{SILVER}" font-family="Georgia,serif">N</text>''',
    "Rose": f'''
        <path d="M50 52 V86" stroke="{GREEN}" stroke-width="4" stroke-linecap="round"/>
        <path d="M50 70 C 62 62, 70 66, 72 60 C 64 58, 56 62, 50 70" fill="{GREEN}"/>
        <circle cx="50" cy="38" r="18" fill="{RED}"/>
        <path d="M40 36 C 44 26, 58 26, 60 36 C 56 32, 46 32, 44 40 C 48 44, 56 42, 56 36" fill="none" stroke="#8e2b28" stroke-width="2.5"/>''',
    "Coin": f'''
        <circle cx="50" cy="50" r="30" fill="{YELLOW}" stroke="{SILVER}" stroke-width="3"/>
        <circle cx="50" cy="50" r="22" fill="none" stroke="#b8860b" stroke-width="2"/>
        <path d="M50 34 L54 46 L66 46 L56 53 L60 65 L50 58 L40 65 L44 53 L34 46 L46 46 Z" fill="#b8860b"/>''',
    "Feather": f'''
        <path d="M28 82 C 40 60, 58 34, 78 18 C 76 40, 62 62, 34 78" fill="{IVORY}" stroke="{SILVER}" stroke-width="2"/>
        <path d="M24 88 L66 34" stroke="{SILVER}" stroke-width="3" stroke-linecap="round"/>
        <path d="M44 62 L56 60 M50 52 L62 50 M56 44 L68 40" stroke="{SILVER}" stroke-width="1.5"/>''',
    "Chess piece": f'''
        <circle cx="50" cy="30" r="10" fill="{IVORY}"/>
        <path d="M42 42 H58 L56 48 C 56 60, 62 66, 64 72 H36 C 38 66, 44 60, 44 48 Z" fill="{IVORY}"/>
        <rect x="30" y="72" width="40" height="9" rx="3" fill="{IVORY}"/>''',
    "Candle": f'''
        <path d="M50 16 C 58 26, 56 34, 50 38 C 44 34, 42 26, 50 16 Z" fill="{YELLOW}"/>
        <path d="M50 24 C 53 29, 52 33, 50 35 C 48 33, 47 29, 50 24 Z" fill="{RED}"/>
        <rect x="40" y="40" width="20" height="38" rx="3" fill="{IVORY}"/>
        <rect x="32" y="78" width="36" height="6" rx="3" fill="{SILVER}"/>''',
    "Pocket watch": f'''
        <path d="M44 16 H56 V24 H44 Z" fill="{SILVER}"/>
        <circle cx="50" cy="56" r="28" fill="{IVORY}" stroke="{SILVER}" stroke-width="5"/>
        <path d="M50 56 V38 M50 56 L62 62" stroke="{BG}" stroke-width="3.5" stroke-linecap="round"/>
        <circle cx="50" cy="56" r="3" fill="{BG}"/>''',
    "Hourglass": f'''
        <rect x="28" y="16" width="44" height="7" rx="3" fill="{SILVER}"/>
        <rect x="28" y="77" width="44" height="7" rx="3" fill="{SILVER}"/>
        <path d="M34 23 H66 C 66 40, 52 44, 52 50 C 52 56, 66 60, 66 77 H34 C 34 60, 48 56, 48 50 C 48 44, 34 40, 34 23 Z" fill="none" stroke="{SILVER}" stroke-width="3"/>
        <path d="M40 30 H60 C 58 40, 52 42, 50 47 C 48 42, 42 40, 40 30 Z" fill="{YELLOW}"/>
        <path d="M38 75 C 40 66, 46 62, 50 60 C 54 62, 60 66, 62 75 Z" fill="{YELLOW}"/>''',
    "Lantern": f'''
        <path d="M42 18 C 42 10, 58 10, 58 18" fill="none" stroke="{SILVER}" stroke-width="3"/>
        <path d="M34 24 H66 L62 30 H38 Z" fill="{SILVER}"/>
        <rect x="38" y="30" width="24" height="40" rx="3" fill="{YELLOW}" opacity="0.85"/>
        <path d="M50 38 C 56 46, 54 54, 50 58 C 46 54, 44 46, 50 38 Z" fill="{RED}"/>
        <path d="M38 30 V70 M62 30 V70" stroke="{SILVER}" stroke-width="3"/>
        <path d="M34 70 H66 L62 80 H38 Z" fill="{SILVER}"/>''',
}


def item(name):
    return _svg(ITEMS[name])


# --- Escape Route rooms ----------------------------------------------------------

ROOMS = {
    "Hall": f'''
        <path d="M22 80 H38 V68 H50 V56 H62 V44 H74 V32 H82" {_LINE}/>
        <path d="M18 84 H86" {_LINE}/>''',
    "Kitchen": f'''
        <path d="M26 46 H74 V70 C 74 78, 68 82, 62 82 H38 C 32 82, 26 78, 26 70 Z" fill="{IVORY}"/>
        <path d="M20 50 H26 M74 50 H80" {_LINE}/>
        <path d="M40 38 C 36 32, 44 28, 40 22 M52 38 C 48 32, 56 28, 52 22 M64 38 C 60 32, 68 28, 64 22" fill="none" stroke="{IVORY}" stroke-width="2.5" stroke-linecap="round"/>''',
    "Conservatory": f'''
        <path d="M50 84 V44" stroke="#8b6b3e" stroke-width="5" stroke-linecap="round"/>
        <path d="M50 44 C 36 30, 22 36, 18 44 C 30 40, 40 42, 50 46 C 60 42, 70 40, 82 44 C 78 36, 64 30, 50 44 Z M50 44 C 46 30, 50 20, 58 16 C 56 28, 54 36, 50 44" fill="{GREEN}"/>
        <ellipse cx="72" cy="80" rx="14" ry="4" fill="{IVORY}"/>
        <path d="M64 66 H80 V74 C 80 78, 64 78, 64 74 Z" fill="{IVORY}"/>
        <path d="M80 68 C 86 68, 86 74, 80 74" fill="none" stroke="{IVORY}" stroke-width="2"/>
        <path d="M70 62 C 68 58, 72 56, 70 52" fill="none" stroke="{IVORY}" stroke-width="1.5"/>''',
    "Library": f'''
        <rect x="20" y="30" width="10" height="50" fill="{RED}"/><rect x="32" y="24" width="10" height="56" fill="{BLUE}"/>
        <rect x="44" y="34" width="10" height="46" fill="{GREEN}"/><rect x="56" y="26" width="10" height="54" fill="{YELLOW}"/>
        <rect x="68" y="30" width="12" height="50" fill="{IVORY}" transform="rotate(10 74 55)"/>
        <path d="M14 82 H86" {_LINE}/>''',
    "Clock Room": f'''
        <circle cx="34" cy="38" r="14" fill="{IVORY}"/><path d="M34 38 V30 M34 38 L40 41" stroke="{BG}" stroke-width="2.5"/>
        <circle cx="68" cy="34" r="11" fill="{IVORY}"/><path d="M68 34 V27 M68 34 L73 36" stroke="{BG}" stroke-width="2.5"/>
        <circle cx="52" cy="68" r="16" fill="{IVORY}"/><path d="M52 68 V58 M52 68 L60 72" stroke="{BG}" stroke-width="2.5"/>''',
    "Gallery": f'''
        <rect x="24" y="22" width="52" height="58" rx="2" fill="none" stroke="{SILVER}" stroke-width="6"/>
        <circle cx="50" cy="44" r="10" fill="{IVORY}"/>
        <path d="M34 74 C 36 60, 64 60, 66 74 Z" fill="{IVORY}"/>
        <circle cx="46" cy="43" r="1.8" fill="{BG}"/><circle cx="54" cy="43" r="1.8" fill="{BG}"/>''',
    "Pantry": f'''
        <rect x="30" y="36" width="40" height="44" rx="8" fill="{RED}" opacity="0.85"/>
        <rect x="28" y="26" width="44" height="12" rx="3" fill="{IVORY}"/>
        <rect x="38" y="50" width="24" height="16" rx="2" fill="{IVORY}"/>''',
    "Greenhouse": f'''
        <path d="M20 80 V46 L50 22 L80 46 V80 Z" fill="none" stroke="{IVORY}" stroke-width="3"/>
        <path d="M50 22 V80 M20 60 H80" stroke="{IVORY}" stroke-width="2" opacity="0.6"/>
        <path d="M36 80 C 34 70, 40 66, 36 58 M64 80 C 66 70, 60 66, 64 58" stroke="{GREEN}" stroke-width="4" fill="none" stroke-linecap="round"/>''',
    "Study": f'''
        <rect x="18" y="54" width="64" height="8" rx="2" fill="#8b6b3e"/>
        <path d="M24 62 V84 M76 62 V84" stroke="#8b6b3e" stroke-width="5"/>
        <path d="M28 30 L46 26 L58 32 L74 28 V50 L58 54 L46 48 L28 52 Z" fill="{IVORY}"/>
        <path d="M46 26 V48 M58 32 V54" stroke="{SILVER}" stroke-width="1.5"/>
        <path d="M34 40 L40 36 L52 42" fill="none" stroke="{RED}" stroke-width="2" stroke-dasharray="3 2"/>''',
    "Storage Room": f'''
        <rect x="18" y="48" width="34" height="32" fill="#8b6b3e"/><rect x="52" y="56" width="30" height="24" fill="#a07d4b"/>
        <rect x="30" y="22" width="30" height="26" fill="#a07d4b"/>
        <path d="M18 64 H52 M30 35 H60 M52 68 H82" stroke="{BG}" stroke-width="2"/>''',
    "Ballroom": f'''
        <rect x="38" y="14" width="24" height="72" rx="4" fill="#8b6b3e"/>
        <circle cx="50" cy="32" r="9" fill="{IVORY}"/><path d="M50 32 V26 M50 32 L54 34" stroke="{BG}" stroke-width="2"/>
        <path d="M50 46 V66" stroke="{SILVER}" stroke-width="2"/><circle cx="50" cy="70" r="5" fill="{SILVER}"/>''',
    "Wine Cellar": f'''
        <path d="M40 24 H48 V36 C 56 40, 58 46, 58 54 V82 H30 V54 C 30 46, 32 40, 40 36 Z" fill="#6b2737"/>
        <rect x="34" y="56" width="20" height="14" fill="{IVORY}"/>
        <path d="M62 66 L80 66 L74 80 H66 Z" fill="{YELLOW}"/>''',
    "Exit": f'''
        <rect x="30" y="20" width="40" height="62" rx="3" fill="none" stroke="{SILVER}" stroke-width="4"/>
        <path d="M30 20 L54 28 V88 L30 82 Z" fill="{IVORY}"/>
        <circle cx="48" cy="56" r="2.5" fill="{BG}"/>
        <path d="M60 52 H84 M76 44 L84 52 L76 60" {_LINE}/>''',
    "Music Room": f'''
        <path d="M18 46 C 18 34, 40 30, 60 34 C 74 36, 82 44, 82 52 V58 H18 Z" fill="{IVORY}"/>
        <rect x="18" y="58" width="64" height="8" fill="{BG}"/>
        <path d="M22 58 V66 M30 58 V66 M38 58 V66 M46 58 V66 M54 58 V66 M62 58 V66 M70 58 V66 M78 58 V66" stroke="{IVORY}" stroke-width="1.5"/>
        <path d="M26 66 V84 M74 66 V84" stroke="{SILVER}" stroke-width="4"/>
        <ellipse cx="34" cy="88" rx="5" ry="2.5" fill="{RED}"/><ellipse cx="46" cy="90" rx="5" ry="2.5" fill="{RED}"/>''',
    "Chapel": f'''
        <path d="M50 14 V24 M45 19 H55" stroke="{SILVER}" stroke-width="3"/>
        <path d="M30 50 L50 26 L70 50 V84 H30 Z" fill="none" stroke="{SILVER}" stroke-width="3"/>
        <path d="M42 54 C 42 46, 58 46, 58 54 L60 66 H40 Z" fill="{YELLOW}"/>
        <circle cx="50" cy="69" r="3" fill="{YELLOW}"/>
        <path d="M22 50 C 18 46, 18 40, 22 36 M78 50 C 82 46, 82 40, 78 36" fill="none" stroke="{IVORY}" stroke-width="2"/>''',
    "Billiard Room": f'''
        <rect x="14" y="34" width="72" height="40" rx="6" fill="#2e7d4f" stroke="#8b6b3e" stroke-width="5"/>
        <circle cx="38" cy="52" r="6" fill="{IVORY}"/><circle cx="58" cy="48" r="6" fill="{RED}"/>
        <circle cx="66" cy="60" r="6" fill="{YELLOW}"/>
        <path d="M20 84 L58 54" stroke="{SILVER}" stroke-width="3" stroke-linecap="round"/>''',
}


def room(name):
    return _svg(ROOMS[name])


# --- Pattern Wall tiles ----------------------------------------------------------

def _shape(shape, colour, cx, cy, r):
    fill = TILE_COLOURS[colour]
    if shape == "circle":
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'
    if shape == "square":
        return f'<rect x="{cx - r * 0.85}" y="{cy - r * 0.85}" width="{r * 1.7}" height="{r * 1.7}" rx="2" fill="{fill}"/>'
    if shape == "triangle":
        return f'<path d="M{cx} {cy - r} L{cx + r} {cy + r * 0.8} L{cx - r} {cy + r * 0.8} Z" fill="{fill}"/>'
    if shape == "diamond":
        return f'<path d="M{cx} {cy - r} L{cx + r} {cy} L{cx} {cy + r} L{cx - r} {cy} Z" fill="{fill}"/>'
    raise ValueError(shape)


def tile(shape, colour):
    return _svg(_shape(shape, colour, 50, 50, 28))


def wall(grid):
    """The whole 4 × 4 wall in one picture; None is drawn as a glowing '?'."""
    size, cell = 420, 100
    parts = []
    for i, line in enumerate(grid):
        for j, value in enumerate(line):
            x, y = 10 + j * cell, 10 + i * cell
            parts.append(f'<rect x="{x + 4}" y="{y + 4}" width="{cell - 8}" height="{cell - 8}" rx="10" '
                         f'fill="#2c2160" fill-opacity="0.75" stroke="{PURPLE if value is None else "#6a5bb0"}" stroke-width="{4 if value is None else 2}"/>')
            if value is None:
                parts.append(f'<text x="{x + 50}" y="{y + 66}" font-size="46" text-anchor="middle" '
                             f'fill="{PURPLE}" font-family="Georgia,serif">?'
                             f'<animate attributeName="opacity" values="1;0.35;1" dur="1.6s" '
                             f'repeatCount="indefinite"/></text>')
            else:
                parts.append(_shape(value[0], value[1], x + 50, y + 50, 26))
    return _svg("".join(parts), size=size)


# --- Number Lock padlock ---------------------------------------------------------

def padlock(digits):
    """A padlock with 4 dials showing `digits` (a list of 4 single-character strings)."""
    dials = "".join(
        f'<rect x="{34 + k * 45}" y="128" width="37" height="56" rx="6" fill="{IVORY}"/>'
        f'<text x="{52.5 + k * 45}" y="169" font-size="32" text-anchor="middle" fill="{BG}" '
        f'font-family="Courier New,monospace" font-weight="bold">{d}</text>'
        for k, d in enumerate(digits)
    )
    body = (f'<path d="M80 100 V70 C 80 30, 160 30, 160 70 V100" fill="none" stroke="#8e93a3" stroke-width="16"/>'
            f'<rect x="22" y="96" width="196" height="118" rx="18" fill="{SILVER}" stroke="{PURPLE}" stroke-width="4"/>'
            f'{dials}')
    return _svg(body, size=240, background=False)


# --- Pictures you can tap ------------------------------------------------------------

def css_key(key):
    """Streamlit gives a widget with key "x" the CSS class "st-key-x"."""
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in key)


def picture_button_style(key, svg, height=120, selected=False, bob=False):
    """CSS that turns the st.button with this key into the picture itself.

    Hovering lifts it and makes it glow; a selected picture glows ice-blue with a
    silver ring. bob=True makes it float gently up and down to draw the eye.

    The selectors are more specific than the team theme's button style
    (screens/common.py) and use !important, so pictures win and all other
    buttons keep the theme."""
    data = base64.b64encode(svg.encode()).decode()
    k = css_key(key)
    b = f".st-key-{k} div.stButton > button"
    ring = (f"outline:3px solid {TILE_COLOURS['ice']} !important;outline-offset:2px;"
            f"filter:drop-shadow(0 0 14px {TILE_COLOURS['ice']}) !important;") if selected else ""
    float_ = "animation:mm-bob 2.6s ease-in-out infinite;" if bob else ""
    return f"""<style>
@keyframes mm-bob {{ 0%,100% {{ transform: translateY(0) }} 50% {{ transform: translateY(-5px) }} }}
{b} {{
  background: url("data:image/svg+xml;base64,{data}") center 4px / min(calc(100% - 6px), {height - 30}px) auto no-repeat transparent !important;
  border: none !important; border-radius: 14px !important; box-shadow: none !important;
  min-height: {height}px; padding-top: {height - 34}px !important; width: 100%;
  transition: transform .15s ease, filter .15s ease; {ring}{float_}
}}
{b}:hover {{
  transform: translateY(-5px) scale(1.05); animation: none;
  filter: drop-shadow(0 0 12px {PURPLE}) !important;
}}
{b}:active {{ transform: scale(0.96); }}
{b} p {{ font-weight: 600; color: {SILVER} !important; }}
@media (max-width: 640px) {{
  {b} {{ min-height: {int(height * 0.8)}px; padding-top: {int(height * 0.8) - 24}px !important;
        padding-left: 2px !important; padding-right: 2px !important;
        background-size: min(calc(100% - 6px), {int(height * 0.8) - 30}px) auto !important; }}
  {b} p {{ font-size: .7rem !important; line-height: 1.1; }}
}}
</style>"""


# --- A countdown the browser animates by itself ---------------------------------------

def countdown(uid, seconds, total, label=""):
    """A number counting down to 0 and a shrinking bar, animated purely with CSS.

    The server draws this once; the browser does the ticking. `uid` must be
    unique per game so a new game starts a fresh animation."""
    width = round(100 * seconds / total, 1)
    return f"""<style>
@property --mm-n {{ syntax: '<integer>'; inherits: false; initial-value: 0; }}
@keyframes mm-tick-{uid} {{ from {{ --mm-n: {seconds}; }} to {{ --mm-n: 0; }} }}
@keyframes mm-bar-{uid} {{ from {{ width: {width}%; }} to {{ width: 0%; }} }}
.mm-n-{uid} {{ --mm-n: {seconds}; animation: mm-tick-{uid} {seconds}s linear forwards;
              counter-reset: mm-n var(--mm-n); }}
.mm-n-{uid}::after {{ content: counter(mm-n) "s"; }}
.mm-bar-{uid} {{ height: 10px; border-radius: 5px; width: {width}%;
                background: linear-gradient(90deg, {TILE_COLOURS['ice']}, {TILE_COLOURS['purple']});
                animation: mm-bar-{uid} {seconds}s linear forwards; }}
</style>
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.3rem">
  <span style="color:{SILVER};font-size:.9rem">{label}</span>
  <span style="font-size:1.7rem;font-weight:700;color:{IVORY};display:flex;align-items:center">{icon("timer", 30)}<span class="mm-n-{uid}"></span></span>
</div>
<div style="background:rgba(255,255,255,.12);border-radius:5px;margin-bottom:.8rem">
  <div class="mm-bar-{uid}"></div>
</div>"""


def phone_grid_style(key):
    """Keep the columns inside the container with this key side by side on
    narrow screens, instead of Streamlit's default of stacking them."""
    k = css_key(key)
    return f"""<style>
.st-key-{k} [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: .4rem !important; }}
.st-key-{k} [data-testid="stColumn"] {{ min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }}
</style>"""


# --- Icons (instead of emojis) ---------------------------------------------------------
# Small silver line drawings with a purple accent, in the same style as the cards.

_ICON = f'fill="none" stroke="{SILVER}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"'

ICONS = {
    "number_lock": f'''<path d="M32 44 V32 C 32 18, 68 18, 68 32 V44" {_ICON}/>
        <rect x="22" y="44" width="56" height="42" rx="8" fill="{PURPLE}" stroke="{SILVER}" stroke-width="4"/>
        <circle cx="50" cy="61" r="6" fill="{BG}"/><path d="M50 65 V75" stroke="{BG}" stroke-width="5" stroke-linecap="round"/>''',
    "pattern": f'''<rect x="16" y="16" width="30" height="30" rx="5" fill="{TILE_COLOURS['purple']}"/>
        <rect x="54" y="16" width="30" height="30" rx="5" {_ICON}/>
        <rect x="16" y="54" width="30" height="30" rx="5" {_ICON}/>
        <rect x="54" y="54" width="30" height="30" rx="5" fill="{TILE_COLOURS['ice']}"/>
        <text x="69" y="40" font-size="22" text-anchor="middle" fill="{SILVER}" font-family="Georgia,serif">?</text>''',
    "escape_route": f'''<path d="M18 24 L38 16 L62 24 L82 16 V76 L62 84 L38 76 L18 84 Z" fill="{BG}" stroke="{SILVER}" stroke-width="4" stroke-linejoin="round"/>
        <path d="M38 16 V76 M62 24 V84" stroke="{SILVER}" stroke-width="2" opacity=".6"/>
        <path d="M26 66 C 36 56, 44 64, 52 50 S 66 38, 74 32" fill="none" stroke="{PURPLE}" stroke-width="4" stroke-dasharray="6 5" stroke-linecap="round"/>
        <path d="M70 26 L78 34 M78 26 L70 34" stroke="{TILE_COLOURS['ice']}" stroke-width="4" stroke-linecap="round"/>''',
    "memory": f'''<rect x="22" y="22" width="40" height="56" rx="6" fill="{BG}" stroke="{SILVER}" stroke-width="4" transform="rotate(-12 42 50)"/>
        <rect x="40" y="20" width="40" height="56" rx="6" fill="{PURPLE}" stroke="{SILVER}" stroke-width="4" transform="rotate(10 60 48)"/>
        <circle cx="60" cy="48" r="8" fill="none" stroke="{SILVER}" stroke-width="3"/>''',
    "rules": f'''<path d="M26 18 H70 C 76 18, 80 22, 80 28 V78 C 80 84, 76 86, 72 86 H30" {_ICON}/>
        <path d="M30 86 C 22 86, 20 80, 20 76 H62 C 62 80, 64 86, 72 86" {_ICON}/>
        <path d="M26 18 C 20 18, 18 24, 20 28 H32" {_ICON}/>
        <path d="M38 36 H70 M38 48 H70 M38 60 H60" stroke="{PURPLE}" stroke-width="4" stroke-linecap="round"/>''',
    "timer": f'''<circle cx="50" cy="56" r="30" {_ICON}/>
        <path d="M42 16 H58 M50 16 V26 M74 30 L80 24" {_ICON}/>
        <path d="M50 56 V38 M50 56 L62 64" stroke="{PURPLE}" stroke-width="5" stroke-linecap="round"/>''',
    "through": f'''<path d="M30 20 H70 V40 C 70 54, 60 62, 50 62 C 40 62, 30 54, 30 40 Z" fill="{PURPLE}" stroke="{SILVER}" stroke-width="4"/>
        <path d="M30 26 H18 C 18 40, 24 46, 32 46 M70 26 H82 C 82 40, 76 46, 68 46" {_ICON}/>
        <path d="M50 62 V74 M36 84 H64 M40 74 H60" {_ICON}/>''',
    "eliminated": f'''<rect x="28" y="16" width="44" height="70" rx="3" {_ICON}/>
        <path d="M28 16 L54 24 V92 L28 86 Z" fill="{BG}" stroke="{SILVER}" stroke-width="4" stroke-linejoin="round"/>
        <path d="M62 44 L78 60 M78 44 L62 60" stroke="{PURPLE}" stroke-width="5" stroke-linecap="round"/>''',
    "solutions": f'''<circle cx="42" cy="42" r="22" {_ICON}/>
        <path d="M58 58 L82 82" stroke="{SILVER}" stroke-width="8" stroke-linecap="round"/>
        <path d="M32 42 L40 50 L54 34" stroke="{PURPLE}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>''',
    "tiebreak": f'''<path d="M50 16 V82 M30 84 H70 M18 30 H82" {_ICON}/>
        <path d="M18 30 L8 56 H28 Z M82 30 L72 56 H92 Z" fill="{PURPLE}" stroke="{SILVER}" stroke-width="3" stroke-linejoin="round"/>''',
    "duel": f'''<path d="M20 80 L66 24 M66 24 L76 18 L72 30 Z M28 62 L38 72" {_ICON}/>
        <path d="M80 80 L34 24 M34 24 L24 18 L28 30 Z M72 62 L62 72" stroke="{PURPLE}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>''',
}


def icon_svg(name):
    return _svg(ICONS[name], background=False)


def icon(name, size=28):
    """An inline icon, sitting on the text line like an emoji would."""
    data = base64.b64encode(icon_svg(name).encode()).decode()
    return (f'<img src="data:image/svg+xml;base64,{data}" '
            f'style="width:{size}px;height:{size}px;vertical-align:middle;margin-right:.35rem"/>')


def heading(name, text, size=34, level=3):
    """A heading with an icon in front, in the theme's heading colour.
    `text` must be our own text, never something a player typed."""
    return (f'<h{level} style="display:flex;align-items:center;gap:.2rem;margin:.2rem 0 .6rem">'
            f'{icon(name, size)}<span>{text}</span></h{level}>')


def panel(icon_name, title, lines):
    """A themed box (dark purple, silver edge) with an icon and a list of lines.
    Replaces Streamlit's expander, which turns white on phones in light mode."""
    items = "".join(f"<li>{line}</li>" for line in lines)
    return (f'<div style="background:rgba(29,20,56,.85);border:1.5px solid {SILVER};border-radius:14px;'
            f'padding:.8rem 1rem .4rem;margin-bottom:.8rem;color:{IVORY}">'
            f'<div style="display:flex;align-items:center;font-weight:700;margin-bottom:.3rem">'
            f'{icon(icon_name, 26)}{title}</div><ul style="margin:0 0 .4rem 1.1rem;padding:0">{items}</ul></div>')


def banner(icon_name, text, good=True):
    """A big themed message (e.g. 'You're through to Round 2!').
    `text` must be our own text, never something a player typed."""
    edge = TILE_COLOURS["ice"] if good else "#e0449b"
    return (f'<div style="display:flex;align-items:center;gap:.6rem;background:rgba(29,20,56,.85);'
            f'border:2px solid {edge};border-radius:14px;padding:.7rem 1rem;margin:.4rem 0 1rem;'
            f'color:{IVORY};font-size:1.15rem;font-weight:700;box-shadow:0 0 18px {edge}55">'
            f'{icon(icon_name, 40)}<span>{text}</span></div>')
