"""The pictures for Round 1, drawn in code as SVG (scalable vector graphics).

Drawing them ourselves means there are no image files to manage, no copyright
questions, and they look the same on every phone. Every picture uses the same
style: a deep purple-black card with silver line-art and a few accent colours,
matching the game's purple-and-silver theme.

Nothing here contains text typed by players, so it is safe to show as HTML.
"""

import base64

BG = "#17112a"          # deep purple-black card
SILVER = "#c9ccd6"      # line-art and borders
IVORY = "#eceef3"       # light fills
PURPLE = "#8b5cf6"
RED = "#d9534f"
GREEN = "#5cb85c"
BLUE = "#4a90d9"
YELLOW = "#f0c419"

# The four Pattern Wall colours: silver, purple, royal blue and ice blue.
# Different enough in shade to tell apart, all in the game's theme.
TILE_COLOURS = {"purple": "#9b5de5", "silver": "#d5d8e0", "royal": "#2f55d4", "ice": "#8fd3ff"}


def _svg(body, size=100, background=True):
    card = f'<rect x="2" y="2" width="{size - 4}" height="{size - 4}" rx="12" fill="{BG}" stroke="{SILVER}" stroke-width="2"/>' if background else ""
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
        <ellipse cx="26" cy="80" rx="5" ry="3" fill="{SILVER}"/><ellipse cx="34" cy="74" rx="5" ry="3" fill="{SILVER}"/>
        <ellipse cx="70" cy="80" rx="5" ry="3" fill="{SILVER}"/><ellipse cx="76" cy="72" rx="5" ry="3" fill="{SILVER}"/>''',
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
                         f'fill="#241a3a" stroke="{PURPLE if value is None else "#3a2d57"}" stroke-width="3"/>')
            if value is None:
                parts.append(f'<text x="{x + 50}" y="{y + 66}" font-size="46" text-anchor="middle" '
                             f'fill="{PURPLE}" font-family="Georgia,serif">?</text>')
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
