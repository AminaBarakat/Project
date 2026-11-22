"""A small QR code maker, so the host can show a code that people scan to join.

It is written here in plain Python (no extra package to install). It makes the
standard QR codes that every phone camera can read: text stored as bytes,
medium error correction (still readable if about 15% is damaged), sizes 1 to 10
(up to 213 characters, far more than an invite link needs).

    qr.matrix("https://...")  -> rows of True (dark) / False (light) squares
    qr.svg("https://...")     -> the code as a picture for the page
"""

# For each size (version 1-10), with medium error correction:
# (error-correction bytes per block, [(number of blocks, data bytes per block), ...])
_BLOCKS = {
    1: (10, [(1, 16)]), 2: (16, [(1, 28)]), 3: (26, [(1, 44)]), 4: (18, [(2, 32)]),
    5: (24, [(2, 43)]), 6: (16, [(4, 27)]), 7: (18, [(4, 31)]),
    8: (22, [(2, 38), (2, 39)]), 9: (22, [(3, 36), (2, 37)]), 10: (26, [(4, 43), (1, 44)]),
}
# Where the small alignment squares go, for each size.
_ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
          7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}

_MASKS = [
    lambda x, y: (x + y) % 2 == 0,
    lambda x, y: y % 2 == 0,
    lambda x, y: x % 3 == 0,
    lambda x, y: (x + y) % 3 == 0,
    lambda x, y: (x // 3 + y // 2) % 2 == 0,
    lambda x, y: x * y % 2 + x * y % 3 == 0,
    lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
    lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
]


def _data_capacity(version):
    _, groups = _BLOCKS[version]
    return sum(count * size for count, size in groups)


# --- error correction (Reed-Solomon over GF(256)) ---------------------------------

def _gf_mul(x, y):
    result = 0
    for i in range(7, -1, -1):
        result = (result << 1) ^ ((result >> 7) * 0x11D)
        result ^= ((y >> i) & 1) * x
    return result


def _rs_divisor(degree):
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = _gf_mul(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = _gf_mul(root, 0x02)
    return result


def _rs_remainder(data, divisor):
    result = [0] * len(divisor)
    for byte in data:
        factor = byte ^ result.pop(0)
        result.append(0)
        for i, coefficient in enumerate(divisor):
            result[i] ^= _gf_mul(coefficient, factor)
    return result


# --- building the code ------------------------------------------------------------

def _pick_version(length):
    for version in range(1, 11):
        count_bits = 8 if version < 10 else 16
        if 4 + count_bits + 8 * length <= 8 * _data_capacity(version):
            return version
    raise ValueError("Text too long for a QR code of size 1-10 (max 213 characters).")


def _codewords(text):
    data = text.encode("utf-8")
    version = _pick_version(len(data))
    capacity = _data_capacity(version)
    bits = [0, 1, 0, 0]                                            # "bytes" mode
    count_bits = 8 if version < 10 else 16
    bits += [(len(data) >> i) & 1 for i in range(count_bits - 1, -1, -1)]
    for byte in data:
        bits += [(byte >> i) & 1 for i in range(7, -1, -1)]
    bits += [0] * min(4, capacity * 8 - len(bits))                 # end marker
    bits += [0] * (-len(bits) % 8)
    payload = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(payload) < capacity:
        payload.append(pad)
        pad ^= 0xEC ^ 0x11

    ec_len, groups = _BLOCKS[version]
    divisor = _rs_divisor(ec_len)
    blocks, start = [], 0
    for count, size in groups:
        for _ in range(count):
            block = payload[start:start + size]
            start += size
            blocks.append((block, _rs_remainder(block, divisor)))
    result = []
    for i in range(max(len(b) for b, _ in blocks)):              # interleave the blocks
        result += [b[i] for b, _ in blocks if i < len(b)]
    for i in range(ec_len):
        result += [ec[i] for _, ec in blocks]
    return version, result


class _Grid:
    def __init__(self, version):
        self.version = version
        self.size = version * 4 + 17
        self.dark = [[False] * self.size for _ in range(self.size)]
        self.fixed = [[False] * self.size for _ in range(self.size)]

    def put(self, x, y, value):
        self.dark[y][x] = bool(value)
        self.fixed[y][x] = True

    def draw_patterns(self):
        size = self.size
        for i in range(size):                                          # timing lines
            self.put(6, i, i % 2 == 0)
            self.put(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):          # the three big corner squares
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < size and 0 <= y < size:
                        self.put(x, y, max(abs(dx), abs(dy)) not in (2, 4))
        positions = _ALIGN[self.version]
        last = len(positions) - 1
        for i, ax in enumerate(positions):                             # small alignment squares
            for j, ay in enumerate(positions):
                if (i, j) in ((0, 0), (0, last), (last, 0)):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self.put(ax + dx, ay + dy, max(abs(dx), abs(dy)) != 1)
        self.draw_format(0)                                           # reserve; redrawn with the real mask
        if self.version >= 7:
            rem = self.version
            for _ in range(12):
                rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
            bits = self.version << 12 | rem
            for i in range(18):
                bit = (bits >> i) & 1
                a, b = size - 11 + i % 3, i // 3
                self.put(a, b, bit)
                self.put(b, a, bit)

    def draw_format(self, mask):
        data = 0 << 3 | mask                                          # 0 = medium error correction
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412
        bit = lambda i: (bits >> i) & 1
        size = self.size
        for i in range(6):
            self.put(8, i, bit(i))
        self.put(8, 7, bit(6))
        self.put(8, 8, bit(7))
        self.put(7, 8, bit(8))
        for i in range(9, 15):
            self.put(14 - i, 8, bit(i))
        for i in range(8):
            self.put(size - 1 - i, 8, bit(i))
        for i in range(8, 15):
            self.put(8, size - 15 + i, bit(i))
        self.put(8, size - 8, True)

    def draw_data(self, codewords):
        size, i, total = self.size, 0, len(codewords) * 8
        right = size - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(size):
                for j in range(2):
                    x = right - j
                    upward = ((right + 1) & 2) == 0
                    y = size - 1 - vert if upward else vert
                    if not self.fixed[y][x] and i < total:
                        self.dark[y][x] = bool((codewords[i >> 3] >> (7 - (i & 7))) & 1)
                        i += 1
            right -= 2

    def apply_mask(self, mask):
        rule = _MASKS[mask]
        for y in range(self.size):
            for x in range(self.size):
                if not self.fixed[y][x] and rule(x, y):
                    self.dark[y][x] = not self.dark[y][x]


def _penalty(dark):
    """How hard a pattern is for a camera to read (lower is better)."""
    size, score = len(dark), 0
    for lines in (dark, list(zip(*dark))):
        for line in lines:
            run, colour = 0, None
            for cell in line:
                if cell == colour:
                    run += 1
                else:
                    if run >= 5:
                        score += run - 2
                    run, colour = 1, cell
            if run >= 5:
                score += run - 2
            text = "".join("1" if c else "0" for c in line)
            score += 40 * (text.count("10111010000") + text.count("00001011101"))
    for y in range(size - 1):
        for x in range(size - 1):
            if dark[y][x] == dark[y][x + 1] == dark[y + 1][x] == dark[y + 1][x + 1]:
                score += 3
    share = sum(map(sum, dark)) * 100 // (size * size)
    score += abs(share - 50) // 5 * 10
    return score


def matrix(text, mask=None):
    """The QR code for `text` as rows of True (dark) / False (light) squares.
    Picks the easiest-to-read pattern unless a `mask` (0-7) is given."""
    version, codewords = _codewords(text)
    best = None
    for candidate in ([mask] if mask is not None else range(8)):
        grid = _Grid(version)
        grid.draw_patterns()
        grid.draw_data(codewords)
        grid.apply_mask(candidate)
        grid.draw_format(candidate)
        score = _penalty(grid.dark)
        if best is None or score < best[0]:
            best = (score, grid.dark)
    return best[1]


def svg(text, dark="#120b22", light="#ffffff", border=4):
    """The QR code as an SVG picture, with the white margin cameras need around it."""
    rows = matrix(text)
    size = len(rows) + 2 * border
    path = "".join(f"M{x + border},{y + border}h1v1h-1z"
                   for y, row in enumerate(rows) for x, cell in enumerate(row) if cell)
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {size} {size}' "
            f"shape-rendering='crispEdges' role='img' aria-label='QR code'>"
            f"<rect width='{size}' height='{size}' fill='{light}'/>"
            f"<path d='{path}' fill='{dark}'/></svg>")
