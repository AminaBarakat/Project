"""Small copies of the detective avatars for screens that refresh often.

The avatar pictures in assets/ are big (up to 2 MB each). Screens that are redrawn
every second or two (the Round 1 race strip, spectator reactions, the crowd bar)
would otherwise send several megabytes to every phone, every time. Here each
picture is shrunk once, kept in memory, and reused: a 160-pixel copy is a few
kilobytes.

Pillow (PIL) comes with Streamlit. If it is missing for some reason, we fall back
to the full-size picture, so the game still works, just with heavier screens.
"""

import base64
import functools
import io

from screens import common


@functools.lru_cache(maxsize=128)
def thumbnail(path, size=160):
    """The picture at `path`, at most `size` pixels wide and high, as a data URL."""
    try:
        from PIL import Image

        with Image.open(path) as image:
            image = image.convert("RGBA")
            image.thumbnail((size, size), Image.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    except Exception:
        return common.avatar_data_url(path)


def picture(player, size=160):
    """A player's avatar as a small data URL, ready for our own HTML."""
    appearance = (player or {}).get("appearance") or "girl"
    _, path = common.AVATARS.get(appearance, common.AVATARS["girl"])
    return thumbnail(path, size)
