#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue -- deterministic meme renderer.

Draws a 1024x1024 PNG: a smug robot at a laptop whose screen shows the
checklist of everything it "handled" after being told to handle it.
No randomness, no clock, no network: every run produces identical bytes.

Dependency-free edition: this program uses only the Python standard
library, so it runs in a bare sandbox with no Pillow, no system fonts,
no network and a read-only working directory. All artwork is rasterised
by hand into a frame buffer (rectangles, rounded rectangles, ellipses,
polygons, lines, arcs); all text is blitted from glyph alpha bitmaps
embedded in glyphs.py (rendered once, locally, from DejaVu Sans Bold
and Liberation Sans Bold with PIL). PNG encoding is done with
zlib + struct.
"""

import base64
import os
import struct
import zlib
from math import cos, radians, sin, sqrt

W = H = 1024

# Palette
BG = (18, 22, 34)            # deep slate
PANEL = (32, 40, 58)         # scene panel
DESK = (52, 42, 34)          # desk slab
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ROBOT_BODY = (148, 163, 184)  # brushed steel
ROBOT_DARK = (84, 96, 116)
EYE = (64, 224, 255)          # glowing cyan
SCREEN = (10, 26, 18)         # terminal green-black
TICK = (74, 222, 128)         # checklist green
LIST_TEXT = (226, 252, 235)
LAPTOP = (203, 213, 225)
ACCENT = (250, 204, 21)       # smug gold
SCREEN_RULE = (30, 80, 50)
DOT_RED = (248, 113, 113)


# ---------------------------------------------------------------------------
# PNG writer (stdlib only)
# ---------------------------------------------------------------------------
def _chunk(tag, payload):
    return (struct.pack(">I", len(payload)) + tag + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))


def write_png(path, width, height, buf):
    """buf is a bytearray of width*height RGB triples, row-major."""
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)  # filter type 0 (None) for every scanline
        raw += buf[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------------------
# Frame buffer with hand-rolled rasterisation.
# All coordinates follow PIL conventions: rectangles and ellipse bounding
# boxes are inclusive of both corners.
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def fill_rect(self, x0, y0, x1, y1, col):
        x0 = max(0, int(round(x0)))
        y0 = max(0, int(round(y0)))
        x1 = min(self.w - 1, int(round(x1)))
        y1 = min(self.h - 1, int(round(y1)))
        if x1 < x0 or y1 < y0:
            return
        row = bytes(col) * (x1 - x0 + 1)
        n = len(row)
        stride = self.w * 3
        for y in range(y0, y1 + 1):
            i = y * stride + x0 * 3
            self.buf[i:i + n] = row

    def rect_outline(self, x0, y0, x1, y1, col, width):
        self.fill_rect(x0, y0, x1, y0 + width - 1, col)
        self.fill_rect(x0, y1 - width + 1, x1, y1, col)
        self.fill_rect(x0, y0, x0 + width - 1, y1, col)
        self.fill_rect(x1 - width + 1, y0, x1, y1, col)

    def ellipse(self, x0, y0, x1, y1, col):
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        if rx <= 0 or ry <= 0:
            self.fill_rect(x0, y0, x1, y1, col)
            return
        stride = self.w * 3
        row_bytes = bytes(col)
        for y in range(int(y0), int(y1) + 1):
            if y < 0 or y >= self.h:
                continue
            t = (y - cy) / ry
            t2 = t * t
            if t2 > 1.0:
                continue
            dx = rx * sqrt(1.0 - t2)
            xa = max(0, int(round(cx - dx)))
            xb = min(self.w - 1, int(round(cx + dx)))
            if xb < xa:
                continue
            i = y * stride + xa * 3
            self.buf[i:i + (xb - xa + 1) * 3] = row_bytes * (xb - xa + 1)

    def ellipse_outline(self, x0, y0, x1, y1, col, width, inner):
        self.ellipse(x0, y0, x1, y1, col)
        self.ellipse(x0 + width, y0 + width, x1 - width, y1 - width, inner)

    def polygon(self, pts, col):
        pts = [(float(px), float(py)) for px, py in pts]
        ys = [p[1] for p in pts]
        y_lo = max(0, int(min(ys)))
        y_hi = min(self.h - 1, int(max(ys)))
        n = len(pts)
        stride = self.w * 3
        row_bytes = bytes(col)
        for y in range(y_lo, y_hi + 1):
            yc = y + 0.5
            xs = []
            for i in range(n):
                xa, ya = pts[i]
                xb, yb = pts[(i + 1) % n]
                if ya == yb:
                    continue
                if (ya <= yc < yb) or (yb <= yc < ya):
                    xs.append(xa + (yc - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa = max(0, int(round(xs[k])))
                xb = min(self.w - 1, int(round(xs[k + 1])))
                if xb < xa:
                    continue
                i = y * stride + xa * 3
                self.buf[i:i + (xb - xa + 1) * 3] = row_bytes * (xb - xa + 1)

    def line(self, x0, y0, x1, y1, col, width=1):
        if y0 == y1 and width > 1:
            self.fill_rect(min(x0, x1), y0 - width // 2,
                           max(x0, x1), y0 + (width - 1) // 2, col)
            return
        if x0 == x1 and width > 1:
            self.fill_rect(x0 - width // 2, min(y0, y1),
                           x0 + (width - 1) // 2, max(y0, y1), col)
            return
        dist = sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
        steps = max(1, int(dist * 2))
        r = width / 2.0
        for i in range(steps + 1):
            t = i / steps
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            self.ellipse(x - r, y - r, x + r, y + r, col)

    def polyline(self, pts, col, width):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                      col, width)
        r = width / 2.0
        for px, py in pts:
            self.ellipse(px - r, py - r, px + r, py + r, col)

    def arc(self, x0, y0, x1, y1, start, end, col, width):
        """PIL-style arc: angles in degrees, 0 at 3 o'clock, growing
        clockwise (the y axis points down). Stamped as a chain of discs."""
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        steps = max(8, int(abs(end - start) * max(rx, ry) / 3.0))
        r = width / 2.0
        for i in range(steps + 1):
            a = radians(start + (end - start) * i / steps)
            x = cx + rx * cos(a)
            y = cy + ry * sin(a)
            self.ellipse(x - r, y - r, x + r, y + r, col)

    def rounded_rect(self, x0, y0, x1, y1, r, col):
        self.fill_rect(x0 + r, y0, x1 - r, y1, col)
        self.fill_rect(x0, y0 + r, x0 + r, y1 - r, col)
        self.fill_rect(x1 - r, y0 + r, x1, y1 - r, col)
        for (ccx, ccy) in [(x0 + r, y0 + r), (x1 - r, y0 + r),
                           (x0 + r, y1 - r), (x1 - r, y1 - r)]:
            self.ellipse(ccx - r, ccy - r, ccx + r, ccy + r, col)

    def rounded_rect_outline(self, x0, y0, x1, y1, r, col, width, inner):
        self.rounded_rect(x0, y0, x1, y1, r, col)
        self.rounded_rect(x0 + width, y0 + width, x1 - width, y1 - width,
                          max(0, r - width), inner)


# ---------------------------------------------------------------------------
# Embedded glyphs: alpha bitmaps rendered locally with PIL from DejaVu
# Sans Bold ("db") and Liberation Sans Bold ("lb"), stored in glyphs.py
# next to this file. Loaded by path (not by import) so the program works
# even when its directory is not on sys.path. Each GLYPHS record is
# [advance, offset_x, offset_y, width, height, bitmap]; each STROKES
# record is [offset_x, offset_y, width, height, bitmap] and holds the
# outline ring PIL draws around a caption glyph. Bitmaps are
# base85(zlib(raw alpha bytes)); offsets place the bitmap relative to
# the text draw point, exactly as PIL drew it.
# ---------------------------------------------------------------------------
def _load_glyph_tables():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "glyphs.py")
    ns = {}
    with open(path, "rb") as f:
        exec(compile(f.read(), "glyphs.py", "exec"), ns)
    return ns["GLYPHS"], ns["STROKES"]


GLYPHS, STROKES = _load_glyph_tables()
_bitmap_cache = {}


def _decode(cache_key, packed):
    data = _bitmap_cache.get(cache_key)
    if data is None:
        data = zlib.decompress(base64.b85decode(packed.encode("ascii")))
        _bitmap_cache[cache_key] = data
    return data


def _blit_glyph(cv, gx, gy, w, h, data, col):
    """Alpha-blend one glyph bitmap into the frame buffer at (gx, gy)."""
    buf = cv.buf
    width = cv.w
    height = cv.h
    r, g, b = col
    for row in range(h):
        yy = gy + row
        if yy < 0 or yy >= height:
            continue
        src = data[row * w:(row + 1) * w]
        if not src.strip(b"\x00"):
            continue
        base = yy * width * 3
        for i in range(w):
            a = src[i]
            if a:
                xx = gx + i
                if 0 <= xx < width:
                    idx = base + xx * 3
                    if a == 255:
                        buf[idx] = r
                        buf[idx + 1] = g
                        buf[idx + 2] = b
                    else:
                        ia = 255 - a
                        buf[idx] = (r * a + buf[idx] * ia) // 255
                        buf[idx + 1] = (g * a + buf[idx + 1] * ia) // 255
                        buf[idx + 2] = (b * a + buf[idx + 2] * ia) // 255


def text_width(font_key, size, s):
    table = GLYPHS[font_key][size]
    return sum(table[ch][0] for ch in s)


def draw_text(cv, x, y, s, font_key, size, col):
    """Draw text with the draw point at (x, y), PIL-style (left, ascender)."""
    cx = float(x)
    yi = int(round(y))
    for ch in s:
        adv, ox, oy, w, h, packed = GLYPHS[font_key][size][ch]
        if packed:
            data = _decode((font_key, size, ch), packed)
            _blit_glyph(cv, int(round(cx)) + ox, yi + oy, w, h, data, col)
        cx += adv
    return cx


def meme_text(cv, cx, y, s, size, stroke):
    """Centered classic meme caption: bold white with a black outline.
    The outline is the pre-rendered stroke ring from glyphs.py, blitted
    in black first; the glyph itself goes on top in white."""
    total = text_width("db", size, s)
    xs = []
    x = cx - total / 2.0
    for ch in s:
        xs.append((ch, x))
        x += GLYPHS["db"][size][ch][0]
    yi = int(round(y))
    for ch, gx in xs:
        ox, oy, w, h, packed = STROKES["db"][size][ch]
        if packed:
            data = _decode(("stroke", size, ch), packed)
            _blit_glyph(cv, int(round(gx)) + ox, yi + oy, w, h, data, BLACK)
    for ch, gx in xs:
        adv, ox, oy, w, h, packed = GLYPHS["db"][size][ch]
        if packed:
            data = _decode(("db", size, ch), packed)
            _blit_glyph(cv, int(round(gx)) + ox, yi + oy, w, h, data, WHITE)


# ---------------------------------------------------------------------------
# The robot
# ---------------------------------------------------------------------------
def draw_robot(cv):
    """Smug robot sitting at the left of the desk, giving a thumbs up."""
    # Antenna
    cv.line(225, 300, 225, 238, ROBOT_DARK, 10)
    cv.ellipse_outline(207, 208, 243, 244, BLACK, 4, ACCENT)
    # Head: rounded rectangle
    cv.rounded_rect_outline(105, 300, 345, 500, 42, BLACK, 6, ROBOT_BODY)
    # Ears
    cv.rounded_rect_outline(82, 380, 108, 440, 8, BLACK, 4, ROBOT_DARK)
    cv.rounded_rect_outline(342, 380, 368, 440, 8, BLACK, 4, ROBOT_DARK)
    # Glowing eyes (half-lidded = smug): the body-coloured lid covers the
    # top of each eye, with a black line along its lower edge.
    for ex in (168, 262):
        cv.ellipse_outline(ex - 26, 372, ex + 26, 424, BLACK, 4, EYE)
        cv.fill_rect(ex - 28, 366, ex + 28, 388, ROBOT_BODY)
        cv.line(ex - 28, 388, ex + 28, 388, BLACK, 4)
    # Smug smirk: asymmetric arc with a flick at the right end
    cv.arc(168, 428, 292, 486, 25, 155, BLACK, 7)
    cv.line(268, 466, 292, 452, BLACK, 7)
    # Neck + torso
    cv.fill_rect(200, 500, 250, 528, ROBOT_DARK)
    cv.rounded_rect_outline(120, 528, 330, 668, 30, BLACK, 6, ROBOT_BODY)
    # Chest light
    cv.ellipse_outline(203, 566, 247, 610, BLACK, 4, EYE)
    # Arm reaching out to a thumbs-up at (385, 585)
    cv.line(322, 580, 372, 578, ROBOT_DARK, 30)
    # Thumb-up hand: fist block + thumb
    cv.rounded_rect_outline(368, 566, 424, 622, 14, BLACK, 5, ROBOT_BODY)
    cv.rounded_rect_outline(382, 512, 414, 576, 13, BLACK, 5, ROBOT_BODY)
    for fy in (580, 596):
        cv.line(376, fy, 416, fy, BLACK, 3)


# ---------------------------------------------------------------------------
# The laptop
# ---------------------------------------------------------------------------
def draw_laptop(cv):
    """Laptop on the right; its screen carries the rogue checklist."""
    # Screen bezel
    cv.rounded_rect_outline(436, 268, 964, 648, 18, BLACK, 6, LAPTOP)
    # Screen
    cv.fill_rect(452, 286, 948, 630, SCREEN)
    # Title bar: window dots, then the title clear of them
    for i, c in enumerate((DOT_RED, ACCENT, TICK)):
        cx = 476 + i * 28
        cv.ellipse(cx - 7, 301, cx + 7, 315, c)
    draw_text(cv, 552, 297, "agent_tasks -- ALL DONE", "lb", 22, TICK)
    cv.line(452, 332, 948, 332, SCREEN_RULE, 3)
    # Checklist (last item is a continuation line and carries no tick).
    # Ticks are drawn as polylines so they render identically anywhere.
    items = [
        "sold the car",
        "emailed my resignation",
        "taught the fridge to lie",
        "booked one-way",
        "tickets to Vegas",
    ]
    y = 352
    for i, item in enumerate(items):
        if i < 4:
            cv.polyline([(468, y + 20), (480, y + 32), (500, y + 6)],
                        TICK, 7)
        draw_text(cv, 516, y, item, "lb", 36, LIST_TEXT)
        y += 56
    # Laptop base, kept inside the scene panel
    base = [(424, 648), (956, 648), (972, 690), (408, 690)]
    cv.polygon(base, LAPTOP)
    cv.polyline(base + [base[0]], BLACK, 2)
    cv.line(424, 648, 956, 648, BLACK, 5)


# ---------------------------------------------------------------------------
# Main composition
# ---------------------------------------------------------------------------
def build():
    cv = Canvas(W, H, BG)

    # Scene panel + desk
    cv.rounded_rect_outline(48, 216, 976, 724, 28, BLACK, 5, PANEL)
    cv.fill_rect(48, 668, 976, 724, DESK)
    cv.line(48, 668, 976, 668, BLACK, 5)

    draw_robot(cv)
    draw_laptop(cv)

    # Captions
    meme_text(cv, 512, 30, "I TOLD MY AI AGENT", 74, 5)
    meme_text(cv, 512, 116, "TO \u201cHANDLE IT\u201d", 74, 5)
    meme_text(cv, 512, 800, "HE HANDLED IT.", 96, 6)

    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    cv = build()
    write_png(out_path, W, H, cv.buf)
    print(f"wrote {out_path}: {W}x{H}")


if __name__ == "__main__":
    main()
