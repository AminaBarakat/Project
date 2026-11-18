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
    # Decoys: objects that are never on the table, only among the answers to pick from.
    "Ring": f'''
        <circle cx="50" cy="58" r="22" fill="none" stroke="{YELLOW}" stroke-width="8"/>
        <path d="M40 34 L50 18 L60 34 Z" fill="{TILE_COLOURS['ice']}" stroke="{SILVER}" stroke-width="2"/>''',
    "Teacup": f'''
        <path d="M24 40 H70 V58 C 70 72, 58 78, 47 78 C 36 78, 24 72, 24 58 Z" fill="{IVORY}"/>
        <path d="M70 46 C 84 46, 84 64, 70 64" fill="none" stroke="{IVORY}" stroke-width="5"/>
        <ellipse cx="47" cy="84" rx="30" ry="5" fill="{SILVER}"/>
        <path d="M38 32 C 34 26, 42 22, 38 16 M54 32 C 50 26, 58 22, 54 16" fill="none" stroke="{IVORY}" stroke-width="2.5" stroke-linecap="round"/>''',
    "Spectacles": f'''
        <circle cx="32" cy="54" r="15" fill="{TILE_COLOURS['ice']}" fill-opacity=".25" stroke="{SILVER}" stroke-width="5"/>
        <circle cx="68" cy="54" r="15" fill="{TILE_COLOURS['ice']}" fill-opacity=".25" stroke="{SILVER}" stroke-width="5"/>
        <path d="M47 52 C 50 48, 50 48, 53 52 M17 50 L10 40 M83 50 L90 40" fill="none" stroke="{SILVER}" stroke-width="5" stroke-linecap="round"/>''',
    "Dice": f'''
        <rect x="24" y="24" width="52" height="52" rx="10" fill="{IVORY}" transform="rotate(-8 50 50)"/>
        <g fill="{BG}" transform="rotate(-8 50 50)"><circle cx="37" cy="37" r="5"/><circle cx="50" cy="50" r="5"/>
        <circle cx="63" cy="63" r="5"/><circle cx="63" cy="37" r="5"/><circle cx="37" cy="63" r="5"/></g>''',
    "Umbrella": f'''
        <path d="M14 50 C 14 26, 86 26, 86 50 C 80 44, 74 44, 68 50 C 62 44, 56 44, 50 50 C 44 44, 38 44, 32 50 C 26 44, 20 44, 14 50 Z" fill="{RED}"/>
        <path d="M50 26 V20 M50 50 V78 C 50 86, 40 86, 40 78" fill="none" stroke="{SILVER}" stroke-width="5" stroke-linecap="round"/>''',
    "Envelope": f'''
        <rect x="18" y="30" width="64" height="44" rx="4" fill="{IVORY}"/>
        <path d="M18 32 L50 56 L82 32" fill="none" stroke="{SILVER}" stroke-width="4" stroke-linejoin="round"/>
        <circle cx="50" cy="58" r="7" fill="{RED}"/>''',
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

# Each colour also has its own texture, so the tiles can be told apart without
# relying on colour alone (colour-blind players): dots on purple, stripes on royal
# blue, fine lines on ice blue; silver stays plain.
TEXTURES = (
    '<defs>'
    '<pattern id="tx-purple" width="9" height="9" patternUnits="userSpaceOnUse">'
    '<circle cx="4.5" cy="4.5" r="1.9" fill="#1d1438" opacity=".55"/></pattern>'
    '<pattern id="tx-royal" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
    '<rect width="3.2" height="9" fill="#ffffff" opacity=".38"/></pattern>'
    '<pattern id="tx-ice" width="9" height="6" patternUnits="userSpaceOnUse">'
    '<rect width="9" height="1.8" fill="#1d1438" opacity=".5"/></pattern>'
    '</defs>'
)
_TEXTURED = {"purple", "royal", "ice"}


def _shape_outline(shape, cx, cy, r, fill):
    if shape == "circle":
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'
    if shape == "square":
        return f'<rect x="{cx - r * 0.85}" y="{cy - r * 0.85}" width="{r * 1.7}" height="{r * 1.7}" rx="2" fill="{fill}"/>'
    if shape == "triangle":
        return f'<path d="M{cx} {cy - r} L{cx + r} {cy + r * 0.8} L{cx - r} {cy + r * 0.8} Z" fill="{fill}"/>'
    if shape == "diamond":
        return f'<path d="M{cx} {cy - r} L{cx + r} {cy} L{cx} {cy + r} L{cx - r} {cy} Z" fill="{fill}"/>'
    raise ValueError(shape)


def _shape(shape, colour, cx, cy, r):
    """A coloured shape, with its colour's texture on top. The SVG it goes into
    must include TEXTURES."""
    drawn = _shape_outline(shape, cx, cy, r, TILE_COLOURS[colour])
    if colour in _TEXTURED:
        drawn += _shape_outline(shape, cx, cy, r, f"url(#tx-{colour})")
    return drawn


def tile(shape, colour):
    return _svg(TEXTURES + _shape(shape, colour, 50, 50, 28))


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
    return _svg(TEXTURES + "".join(parts), size=size)


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


def picture_button_style(key, svg, height=120, selected=False, bob=False, appear=None):
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
    if appear is not None:      # slide up into place, `appear` seconds after the screen is drawn
        float_ = f"animation:mm-appear .55s ease-out {appear:.2f}s both;"
    return f"""<style>
@keyframes mm-bob {{ 0%,100% {{ transform: translateY(0) }} 50% {{ transform: translateY(-5px) }} }}
@keyframes mm-appear {{ from {{ opacity: 0; transform: translateY(22px) scale(.92) }} to {{ opacity: 1; transform: none }} }}
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


# --- The race track in the waiting room ------------------------------------------------

def race_track(runners, uid, games=4):
    """One animated track with every player as a token.

    runners: list of dicts {"name", "from", "to", "me", "done"}, where "from"/"to"
    are positions between 0 and `games` (the token slides from one to the other).
    Players at (almost) the same spot are grouped: their tokens sit side by side and
    share one label, so names never pile up. Names are HTML-escaped here."""
    import html as _html

    def x(pos):                       # 0 … games  →  5% … 88% across the track
        return round(5 + 83 * max(0.0, min(games, pos)) / games, 2)

    # Group runners whose positions are close together.
    ordered = sorted(runners, key=lambda r: r["to"])
    groups = []
    for r in ordered:
        if groups and abs(r["to"] - groups[-1][-1]["to"]) < 0.22:
            groups[-1].append(r)
        else:
            groups.append([r])

    styles, tokens = [], []
    for g, group in enumerate(groups):
        above = g % 2 == 0
        names = ["You" if r["me"] else _html.escape(r["name"][:10]) for r in group]
        label = ", ".join(names[:3]) + (f" +{len(names) - 3}" if len(names) > 3 else "")
        has_me = any(r["me"] for r in group)
        anchor = sum(r["to"] for r in group) / len(group)
        start = sum(r["from"] for r in group) / len(group)
        anim = f"mm-run-{uid}-{g}"
        styles.append(f"@keyframes {anim} {{ from {{ left: {x(start)}%; }} to {{ left: {x(anchor)}%; }} }}")
        circles = ""
        for r in group:
            ring = TILE_COLOURS["ice"] if r["me"] else SILVER
            fill = TILE_COLOURS["silver"] if r["done"] else PURPLE
            glow = f"box-shadow:0 0 12px {TILE_COLOURS['ice']};" if r["me"] else ""
            initial = _html.escape((r["name"][:1] or "?").upper())
            circles += (f'<div style="width:24px;height:24px;border-radius:50%;background:{fill};'
                        f'border:2.5px solid {ring};{glow}display:flex;align-items:center;justify-content:center;'
                        f'color:{BG};font-weight:800;font-size:.75rem;margin-left:-6px">{initial}</div>')
        label_html = (f'<div style="font-size:.7rem;color:{IVORY};white-space:nowrap;'
                      f'font-weight:{700 if has_me else 400};margin:2px 0">{label}</div>')
        tokens.append(
            f'<div style="position:absolute;top:{12 if above else 50}px;left:{x(anchor)}%;'
            f'transform:translateX(-50%);animation:{anim} .9s ease-out;text-align:center;'
            f'z-index:{20 if has_me else 10}">'
            + (label_html if above else "")
            + f'<div style="display:flex;justify-content:center;padding-left:6px">{circles}</div>'
            + ("" if above else label_html)
            + "</div>")

    # small dividers between the games, a START label and the finish flag past the end
    checkpoints = "".join(
        f'<div style="position:absolute;top:43px;left:{x(g)}%;width:2px;height:18px;'
        f'background:{SILVER};opacity:.55"></div>' for g in range(1, games))
    checkpoints += (f'<div style="position:absolute;top:40px;left:0;font-size:.6rem;letter-spacing:.08em;'
                    f'color:{SILVER};opacity:.8">START</div>')
    flag = f'<div style="position:absolute;top:26px;left:92%">{icon("finish", 34)}</div>'
    return f"""<style>
{chr(10).join(styles)}
@keyframes mm-shimmer-{uid} {{ from {{ background-position: 0 0; }} to {{ background-position: 200px 0; }} }}
</style>
<div style="position:relative;height:110px;margin:1rem 0 .4rem">
  <div style="position:absolute;top:47px;left:5%;right:10%;height:10px;border-radius:5px;
       background:repeating-linear-gradient(90deg,{TILE_COLOURS['purple']}55 0 20px,{TILE_COLOURS['ice']}55 20px 40px);
       animation:mm-shimmer-{uid} 3s linear infinite;border:1px solid {SILVER}66"></div>
  {checkpoints}{flag}{"".join(tokens)}
</div>"""


ICONS["finish"] = f'''<path d="M26 90 V14" stroke="{SILVER}" stroke-width="5" stroke-linecap="round"/>
    <path d="M28 16 H80 L70 32 L80 48 H28 Z" fill="{SILVER}"/>
    <path d="M28 16 H41 V32 H28 Z M54 16 H67 V32 H54 Z M41 32 H54 V48 H41 Z M67 32 H76 L80 48 H67 Z" fill="{BG}"/>'''


# --- The scoreboard after Round 1 ----------------------------------------------------

ICONS["mark_right"] = f'''<circle cx="50" cy="50" r="38" fill="{TILE_COLOURS['ice']}"/>
    <path d="M32 52 L45 65 L70 38" fill="none" stroke="{BG}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>'''
ICONS["mark_wrong"] = f'''<circle cx="50" cy="50" r="36" fill="none" stroke="{PURPLE}" stroke-width="7"/>
    <path d="M36 36 L64 64 M64 36 L36 64" stroke="{PURPLE}" stroke-width="9" stroke-linecap="round"/>'''
ICONS["mark_time"] = f'''<circle cx="50" cy="50" r="36" fill="none" stroke="{SILVER}" stroke-width="7" opacity=".7"/>
    <path d="M50 50 V30 M50 50 L64 58" stroke="{SILVER}" stroke-width="8" stroke-linecap="round" opacity=".7"/>'''


def scoreboard(rows, game_ids):
    """How everyone did in Round 1: a mark per game, the score and the total time.
    It never shows the answers themselves.

    rows: list of dicts {"name", "marks": {game_id: "right"/"wrong"/"time"},
          "points", "seconds", "me", "out"}. Names are escaped here."""
    import html as _html
    head = "".join(f'<th style="padding:.3rem .1rem">{icon(g, 22)}</th>' for g in game_ids)
    body = []
    for r in rows:
        name = _html.escape(r["name"])
        marks = "".join(f'<td style="text-align:center;padding:.3rem .1rem">{icon("mark_" + r["marks"][g], 20)}</td>'
                        for g in game_ids)
        style = (f"background:rgba(155,228,255,.10);outline:2px solid {TILE_COLOURS['ice']};" if r["me"] else "")
        style += "opacity:.55;" if r["out"] else ""
        tag = (f' <span style="font-size:.7rem;color:#e0449b;font-weight:700">OUT</span>' if r["out"] else "")
        you = ' <span style="font-size:.7rem;color:#9be4ff;font-weight:700">YOU</span>' if r["me"] else ""
        body.append(
            f'<tr style="{style}">'
            f'<td style="padding:.3rem .4rem;white-space:nowrap;max-width:7.5rem;overflow:hidden;text-overflow:ellipsis">{name}{you}{tag}</td>'
            f'{marks}'
            f'<td style="text-align:center;font-weight:800;padding:.3rem .2rem">{r["points"]}/4</td>'
            f'<td style="text-align:right;padding:.3rem .4rem;color:{SILVER};white-space:nowrap">{r["seconds"]}s</td></tr>')
    return (f'<div style="overflow-x:auto;border:1.5px solid {SILVER}88;border-radius:14px;'
            f'background:rgba(29,20,56,.85);margin:.4rem 0 1rem">'
            f'<table style="width:100%;border-collapse:collapse;color:{IVORY};font-size:.85rem">'
            f'<thead><tr style="border-bottom:1px solid {SILVER}55"><th style="text-align:left;padding:.4rem .5rem">Detective</th>'
            f'{head}<th>Score</th><th style="text-align:right;padding:.4rem .5rem">Time</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


# --- The searching detective (waiting room) -----------------------------------------------

ICONS["footprint"] = f'''<path d="M38 20 C 26 22, 24 44, 30 58 C 34 66, 46 66, 48 56 C 50 44, 50 18, 38 20 Z" fill="{SILVER}"/>
    <ellipse cx="40" cy="78" rx="9" ry="11" fill="{SILVER}"/>
    <path d="M66 30 C 56 32, 54 52, 60 64 C 64 72, 76 70, 77 60 C 78 48, 78 28, 66 30 Z" fill="{SILVER}" opacity=".75"/>
    <ellipse cx="70" cy="84" rx="8" ry="9" fill="{SILVER}" opacity=".75"/>'''


def searching_scene():
    """A magnifying glass sweeping back and forth over a trail of footprints that
    fade in and out. Pure CSS animation; no player text in here."""
    prints = "".join(
        f'<span style="display:inline-block;animation:mm-fade 2.4s {k * 0.4:.1f}s infinite;'
        f'transform:rotate({-8 if k % 2 else 8}deg) translateY({-6 if k % 2 else 6}px)">{icon("footprint", 30)}</span>'
        for k in range(6))
    return f"""<style>
@keyframes mm-search {{ 0%,100% {{ transform: translateX(-90px) rotate(-14deg); }}
                       50% {{ transform: translateX(90px) rotate(14deg); }} }}
@keyframes mm-fade {{ 0%,100% {{ opacity: .12 }} 50% {{ opacity: 1 }} }}
</style>
<div style="text-align:center;padding:.6rem 0 0">
  <div style="display:inline-block;animation:mm-search 3s ease-in-out infinite">{icon("solutions", 84)}</div>
  <div style="margin-top:-.4rem;letter-spacing:.6rem">{prints}</div>
</div>"""


# --- The padlock you type into ------------------------------------------------------------

def shackle():
    """The top of the padlock (the metal loop), drawn above the typing area."""
    body = (f'<path d="M70 118 V70 C 70 22, 170 22, 170 70 V118" fill="none" stroke="#8e93a3" stroke-width="18" stroke-linecap="round"/>'
            f'<path d="M70 118 V70 C 70 22, 170 22, 170 70 V118" fill="none" stroke="{SILVER}" stroke-width="6" opacity=".6"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 120" width="240" height="120">{body}</svg>'


def lock_style(key):
    """CSS that turns the container with this key into the padlock's body, with one
    dark display window for the code (like a digital lock). The digits are typed
    straight into that window. Streamlit's own hints ("Press Enter to submit form"
    and the 0/4 counter) are hidden so they can't show through the digits."""
    k = css_key(key)
    c = f".st-key-{k}"
    return f"""<style>
{c} {{ background: linear-gradient(160deg, {SILVER}, #aeb3c2) !important; border: 4px solid {PURPLE} !important;
      border-radius: 22px !important; padding: 1.1rem 1rem .9rem !important; max-width: 300px; margin: -6px auto 0 !important;
      box-shadow: 0 0 22px {PURPLE}55; }}
{c} [data-testid="InputInstructions"] {{ display: none !important; }}
{c} [data-baseweb="input"] {{
      background: {BG} !important; border: 3px solid #6b7080 !important; border-radius: 12px !important;
      box-shadow: inset 0 3px 8px #000a !important; }}
{c} [data-baseweb="input"] > div, {c} [data-baseweb="base-input"] {{
      background: transparent !important; border: none !important; box-shadow: none !important; }}
{c} input {{
      font-family: "Courier New", Courier, monospace !important; font-size: 2.2rem !important; font-weight: 700 !important;
      letter-spacing: .45em !important; text-indent: .45em; text-align: center !important;
      color: {TILE_COLOURS['ice']} !important; -webkit-text-fill-color: {TILE_COLOURS['ice']} !important;
      caret-color: {PURPLE} !important; background: transparent !important; padding: .2em 0 !important; }}
{c} input::placeholder {{ color: #5d5480 !important; -webkit-text-fill-color: #5d5480 !important; opacity: 1 !important; }}
{c} div.stFormSubmitButton > button {{ width: 100%; margin-top: .6rem; }}
{c} [data-testid="stWidgetLabel"] {{ justify-content: center; }}
{c} [data-testid="stWidgetLabel"] p, {c} label {{ color: {BG} !important; font-weight: 700 !important; }}
</style>"""


# --- Escape Route: the trail so far and the room you just walked into ----------------------

def route_trail(rooms):
    """Your path so far as a row of little room pictures joined by a 'marching'
    dotted line; the room you're in now glows. Room names are our own text."""
    start = icon("escape_route", 34)
    stops = [("Start", start)] + [(room, img(room_svg(room), "40px")) for room in rooms]
    parts = []
    for k, (name, picture) in enumerate(stops):
        here = k == len(stops) - 1
        glow = (f"filter:drop-shadow(0 0 10px {TILE_COLOURS['ice']});animation:mm-pulse 1.6s ease-in-out infinite;"
                if here else "opacity:.8;")
        parts.append(f'<div style="text-align:center;min-width:46px;{glow}">{picture}'
                     f'<div style="font-size:.62rem;color:{IVORY};margin-top:2px;white-space:nowrap">{name}</div></div>')
        if not here:
            parts.append('<div class="mm-march" style="flex:1 1 18px;min-width:14px;height:4px;margin-bottom:16px"></div>')
    return f"""<style>
@keyframes mm-march {{ from {{ background-position: 0 0 }} to {{ background-position: 24px 0 }} }}
@keyframes mm-pulse {{ 0%,100% {{ transform: scale(1) }} 50% {{ transform: scale(1.08) }} }}
.mm-march {{ background: repeating-linear-gradient(90deg, {PURPLE} 0 8px, transparent 8px 12px);
            animation: mm-march .8s linear infinite; border-radius: 2px; }}
</style>
<div style="display:flex;align-items:center;gap:4px;overflow-x:auto;padding:.4rem .2rem .2rem;margin-bottom:.4rem">
{"".join(parts)}</div>"""


def room_svg(name):
    return room(name)


def room_entrance(name, text):
    """The room you just entered swings open like a door. `name` and `text` are
    our own room names and descriptions, never player input."""
    return f"""<style>
@keyframes mm-swing {{ 0% {{ transform: perspective(500px) rotateY(-85deg); opacity: .2 }}
                       70% {{ transform: perspective(500px) rotateY(8deg); opacity: 1 }}
                       100% {{ transform: perspective(500px) rotateY(0) }} }}
</style>
<div style="display:flex;align-items:center;gap:.8rem;background:rgba(29,20,56,.85);border:1.5px solid {SILVER}88;
     border-radius:14px;padding:.6rem .8rem;margin:.2rem 0 .8rem">
  <div style="width:74px;transform-origin:left center;animation:mm-swing .9s ease-out both">{img(room(name), "74px")}</div>
  <div style="color:{IVORY}"><div style="font-size:.75rem;color:{SILVER};letter-spacing:.06em">YOU ARE IN</div>
       <div style="font-weight:800;font-size:1.1rem">{name}</div>
       <div style="font-size:.85rem;font-style:italic;opacity:.9">{text}</div></div>
</div>"""


# --- Ready check before Round 2 ----------------------------------------------------------

def ready_lineup_style():
    """Styles for the ready check before Round 2, drawn like a game lobby: the four
    detectives going through stand side by side, each with a status bar under the
    portrait. You get ready by tapping your own card (see ready_tap_style)."""
    ice = TILE_COLOURS["ice"]
    return f"""<style>
@keyframes mm-dot {{ 0%,100% {{ opacity:.2 }} 50% {{ opacity:1 }} }}
.mm-dots i {{ font-style:normal;font-weight:900;animation:mm-dot 1.2s infinite }}
.mm-dots i:nth-child(2) {{ animation-delay:.2s }} .mm-dots i:nth-child(3) {{ animation-delay:.4s }}
.mm-rl-title {{ font-size:.8rem;color:{SILVER};letter-spacing:.08em;margin:.4rem 0 .5rem;text-align:center }}
.mm-rl-card {{ position:relative;box-sizing:border-box;height:214px;border-radius:14px;overflow:hidden;background:rgba(29,20,56,.85);
      border:2px solid {SILVER}44;display:flex;flex-direction:column }}
.mm-rl-me {{ border-color:{PURPLE} }}
.mm-rl-ready {{ border-color:{ice};box-shadow:0 0 18px {ice}66 }}
.mm-rl-you {{ position:absolute;top:6px;left:50%;transform:translateX(-50%);z-index:2;background:{PURPLE};color:{BG};
      font-size:.62rem;font-weight:900;letter-spacing:.1em;padding:1px 8px;border-radius:999px }}
.mm-rl-stage {{ position:relative;flex:1 1 auto;min-height:0;
      background:radial-gradient(ellipse 60% 16% at 50% 92%, {PURPLE}88, transparent 70%),
                 radial-gradient(circle at 50% 30%, #4b2a86, #1d1438 75%) }}
.mm-rl-stage img {{ position:absolute;bottom:3%;left:50%;transform:translateX(-50%);height:92%;max-width:100%;object-fit:contain }}
.mm-rl-wait .mm-rl-stage img {{ filter:saturate(.55) brightness(.8) }}
.mm-rl-name {{ text-align:center;color:{IVORY};font-weight:800;font-size:.85rem;padding:.35rem .3rem .3rem;
      white-space:nowrap;overflow:hidden;text-overflow:ellipsis }}
.mm-rl-bar {{ display:flex;align-items:center;justify-content:center;gap:.25rem;padding:.4rem .2rem;
      font-size:.72rem;font-weight:900;letter-spacing:.08em;white-space:nowrap }}
.mm-rl-wait .mm-rl-bar {{ background:#2c2346;color:{SILVER}aa }}
.mm-rl-ready .mm-rl-bar {{ background:{ice};color:{BG} }}
@media (max-width:560px) {{
  .mm-rl-card {{ height:150px }} .mm-rl-name {{ font-size:.7rem }}
  .mm-rl-bar {{ font-size:.56rem;letter-spacing:.03em;padding:.3rem .1rem }} }}
</style>"""


def ready_card(name, picture, is_ready, is_me):
    """One detective's card in the ready lineup (not tappable). picture is one of
    our own avatar images as a data URL. The name is escaped."""
    import html as _html
    state = "mm-rl-ready" if is_ready else "mm-rl-wait"
    you = '<div class="mm-rl-you">YOU</div>' if is_me else ""
    if is_ready:
        bar = f'{icon("mark_right", 16)}<span>READY</span>'
    else:
        bar = '<span>NOT READY</span><span class="mm-dots"><i>.</i><i>.</i><i>.</i></span>'
    return (f'<div class="mm-rl-card {state}{" mm-rl-me" if is_me else ""}">{you}'
            f'<div class="mm-rl-stage"><img src="{picture}" alt="" /></div>'
            f'<div class="mm-rl-name">{_html.escape(name)}</div>'
            f'<div class="mm-rl-bar">{bar}</div></div>')


def ready_tap_style(key, picture):
    """Turns the button with this key into YOUR card in the lineup: same size and
    look as the others, glowing, with a 'TAP WHEN READY' bar. Tapping it = ready."""
    k = css_key(key)
    b = f".st-key-{k} div.stButton > button"
    return f"""<style>
@keyframes mm-tap-glow {{ 0%,100% {{ box-shadow:0 0 8px {PURPLE}66 }} 50% {{ box-shadow:0 0 24px {PURPLE} }} }}
{b} {{ position:relative;box-sizing:border-box;height:214px;width:100%;padding:0 0 1.95rem !important;overflow:hidden;
      border:2px solid {PURPLE} !important;border-radius:14px !important;display:flex;align-items:flex-end;justify-content:center;
      background:url('{picture}') center 14px / auto 140px no-repeat,
                 radial-gradient(ellipse 60% 12% at 50% 76%, {PURPLE}88, transparent 70%),
                 radial-gradient(circle at 50% 30%, #4b2a86, #1d1438 75%) !important;
      animation:mm-tap-glow 1.6s ease-in-out infinite;transition:transform .1s }}
{b}:active {{ transform:scale(.96) }}
{b} p {{ color:{IVORY} !important;font-weight:800 !important;font-size:.85rem !important;margin:0 0 .3rem !important;
      max-width:100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:0 .3rem }}
{b}::before {{ content:"YOU";position:absolute;top:6px;left:50%;transform:translateX(-50%);background:{PURPLE};color:{BG};
      font-size:.62rem;font-weight:900;letter-spacing:.1em;padding:1px 8px;border-radius:999px }}
{b}::after {{ content:"TAP WHEN READY";position:absolute;left:0;right:0;bottom:0;padding:.4rem .2rem;background:{PURPLE};
      color:{BG};font-size:.72rem;font-weight:900;letter-spacing:.08em;white-space:nowrap }}
@media (max-width:560px) {{
  {b} {{ height:150px;padding-bottom:1.5rem !important;background-size:auto 92px, auto, auto !important;
        background-position:center 16px, center, center !important }}
  {b} p {{ font-size:.7rem !important }}
  {b}::after {{ content:"TAP ME";font-size:.6rem;padding:.3rem .1rem }} }}
</style>"""
