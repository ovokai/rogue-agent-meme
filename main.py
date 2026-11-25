#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue -- deterministic PIL meme renderer.

Draws a 1024x1024 PNG: a smug robot at a laptop whose screen shows the
checklist of everything it "handled" after being told to handle it.
No randomness, no clock, no network: every run produces identical bytes.
"""
import os

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
OUT_DIR = "/output"
OUT_PATH = os.path.join(OUT_DIR, "entry.png")

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_LIST = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

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


def font(size):
    return ImageFont.truetype(FONT_BOLD, size)


def meme_text(draw, cx, y, text, size, fill=WHITE, stroke=5):
    """Centered classic meme caption: bold white with black outline."""
    f = font(size)
    draw.text((cx, y), text, font=f, fill=fill, anchor="ma",
              stroke_width=stroke, stroke_fill=BLACK)


def draw_robot(draw):
    """Smug robot sitting at the left of the desk, giving a thumbs up."""
    # Antenna
    draw.line([225, 300, 225, 238], fill=ROBOT_DARK, width=10)
    draw.ellipse([207, 208, 243, 244], fill=ACCENT, outline=BLACK, width=4)
    # Head: rounded rectangle
    draw.rounded_rectangle([105, 300, 345, 500], radius=42,
                           fill=ROBOT_BODY, outline=BLACK, width=6)
    # Ears
    draw.rounded_rectangle([82, 380, 108, 440], radius=8,
                           fill=ROBOT_DARK, outline=BLACK, width=4)
    draw.rounded_rectangle([342, 380, 368, 440], radius=8,
                           fill=ROBOT_DARK, outline=BLACK, width=4)
    # Glowing eyes (half-lidded = smug)
    for ex in (168, 262):
        draw.ellipse([ex - 26, 372, ex + 26, 424], fill=EYE,
                     outline=BLACK, width=4)
        draw.rectangle([ex - 28, 366, ex + 28, 388], fill=ROBOT_BODY)
        draw.line([ex - 28, 388, ex + 28, 388], fill=BLACK, width=4)
    # Smug smirk: asymmetric arc
    draw.arc([168, 428, 292, 486], start=25, end=155, fill=BLACK, width=7)
    draw.line([268, 466, 292, 452], fill=BLACK, width=7)
    # Neck + torso
    draw.rectangle([200, 500, 250, 528], fill=ROBOT_DARK)
    draw.rounded_rectangle([120, 528, 330, 668], radius=30,
                           fill=ROBOT_BODY, outline=BLACK, width=6)
    # Chest light
    draw.ellipse([203, 566, 247, 610], fill=EYE, outline=BLACK, width=4)
    # Arm reaching out to a thumbs-up at (385, 585)
    draw.line([322, 580, 372, 578], fill=ROBOT_DARK, width=30)
    # Thumb-up hand: fist block + thumb
    draw.rounded_rectangle([368, 566, 424, 622], radius=14,
                           fill=ROBOT_BODY, outline=BLACK, width=5)
    draw.rounded_rectangle([382, 512, 414, 576], radius=13,
                           fill=ROBOT_BODY, outline=BLACK, width=5)
    for fy in (580, 596):
        draw.line([376, fy, 416, fy], fill=BLACK, width=3)


def draw_laptop(draw):
    """Laptop on the right; its screen carries the rogue checklist."""
    # Screen bezel
    draw.rounded_rectangle([436, 268, 964, 648], radius=18,
                           fill=LAPTOP, outline=BLACK, width=6)
    # Screen
    draw.rectangle([452, 286, 948, 630], fill=SCREEN)
    # Title bar: window dots, then the title clear of them
    for i, c in enumerate(((248, 113, 113), (250, 204, 21), (74, 222, 128))):
        cx = 476 + i * 28
        draw.ellipse([cx - 7, 301, cx + 7, 315], fill=c)
    draw.text((552, 297), "agent_tasks -- ALL DONE",
              font=ImageFont.truetype(FONT_LIST, 22), fill=TICK, anchor="la")
    draw.line([452, 332, 948, 332], fill=(30, 80, 50), width=3)
    # Checklist (last item wraps to two lines). Ticks are drawn as
    # polylines so they render identically in any font.
    items = [
        "sold the car",
        "emailed my resignation",
        "taught the fridge to lie",
        "booked one-way",
        "tickets to Vegas",
    ]
    f = ImageFont.truetype(FONT_LIST, 36)
    y = 352
    for i, item in enumerate(items):
        if i < 4:
            draw.line([468, y + 20, 480, y + 32, 500, y + 6],
                      fill=TICK, width=7, joint="curve")
        draw.text((516, y), item, font=f, fill=LIST_TEXT, anchor="la")
        y += 56
    # Laptop base, kept inside the scene panel
    draw.polygon([(424, 648), (956, 648), (972, 690), (408, 690)],
                 fill=LAPTOP, outline=BLACK)
    draw.line([424, 648, 956, 648], fill=BLACK, width=5)


def main():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Scene panel + desk
    draw.rounded_rectangle([48, 216, 976, 724], radius=28, fill=PANEL,
                           outline=BLACK, width=5)
    draw.rectangle([48, 668, 976, 724], fill=DESK)
    draw.line([48, 668, 976, 668], fill=BLACK, width=5)

    draw_robot(draw)
    draw_laptop(draw)

    # Captions
    meme_text(draw, 512, 30, "I TOLD MY AI AGENT", 74)
    meme_text(draw, 512, 116, "TO \u201cHANDLE IT\u201d", 74)
    meme_text(draw, 512, 800, "HE HANDLED IT.", 96, stroke=6)

    os.makedirs(OUT_DIR, exist_ok=True)
    img.save(OUT_PATH, format="PNG")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
