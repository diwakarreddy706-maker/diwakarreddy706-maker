#!/usr/bin/env python3
"""
make_ascii_svg.py
Converts preprocessed portrait into clean monochrome ASCII-art SVG (840x880)
matching the exact video reference (img2.mp4):
- 160-column high-definition grid
- Left-to-right clip wipe per row plus a small block cursor riding the wipe edge
- Staggered top -> bottom so the whole portrait types once and holds frozen
- Status bar with blinking terminal prompt: diwakar@github:~$ whoami Diwakar Reddy █
"""

import html
import os
import sys
from PIL import Image, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(HERE)
DATA_DIR = os.path.join(BASE_DIR, "data")
SCRATCH_DIR = os.path.join(BASE_DIR, "scratch")
OUT = os.path.join(BASE_DIR, "ascii-portrait.svg")


def get_source_image():
    candidates = [
        os.path.join(DATA_DIR, "preprocessed_photo.png"),
        os.path.join(SCRATCH_DIR, "head_nobg.png"),
        os.path.join(SCRATCH_DIR, "head_crop.jpg"),
        os.path.join(BASE_DIR, "assets", "photo.jpg"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


SRC = get_source_image()

# Grid parameters matching exact video reference
COLS = int(os.environ.get("COLS", 160))
ART_W_TARGET = 800
CELL_W = ART_W_TARGET / COLS
CELL_H = CELL_W * 15 / 8
ROWS = round(COLS * 8 / 15)
RAMP = " .`:-=+*cs#%@"

# Contrast & brightness tuning
CONTRAST = 1.35
BRIGHTNESS = 1.05
GAMMA = 1.15
WHITE_FLOOR = 0.82

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = 840
CANVAS_H = 880

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"       # Andrew6rant / Avi silver monochrome
CURSOR = "#c9d1d9"

ROW_DUR = 4.8 / ROWS   # Entire portrait prints in ~4.8s
STAGGER = ROW_DUR      # Single cursor sweeping across each row sequentially

if not SRC:
    print("[ERROR] No source photo found.")
    sys.exit(1)

print(f"[INFO] Sampling photo for ASCII grid from: {SRC}")
im = Image.open(SRC)

# If full photo, auto-crop head/face
w, h = im.size
if w == h and w > 2000:
    im = im.crop((int(w * 0.38), int(h * 0.27), int(w * 0.57), int(h * 0.53)))

has_alpha = (im.mode == "RGBA")
alpha_px = None
if has_alpha:
    alpha = im.split()[-1].resize((COLS, ROWS), Image.Resampling.NEAREST)
    alpha_px = alpha.load()

im_gray = im.convert("L")
im_gray = ImageEnhance.Brightness(im_gray).enhance(BRIGHTNESS)
im_gray = ImageEnhance.Contrast(im_gray).enhance(CONTRAST)
im_gray = im_gray.resize((COLS, ROWS), Image.Resampling.LANCZOS)
px = im_gray.load()

STATIC = bool(os.environ.get("STATIC"))

rows_txt = []
for y in range(ROWS):
    chars = []
    for x in range(COLS):
        if alpha_px and alpha_px[x, y] < 80:
            chars.append(" ")
            continue

        lum = px[x, y] / 255.0
        lum = pow(lum, GAMMA)

        if not alpha_px and lum > WHITE_FLOOR:
            chars.append(" ")
            continue

        idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
        idx = max(0, min(len(RAMP) - 1, idx))
        chars.append(RAMP[idx])
    rows_txt.append("".join(chars))

art_top = TITLEBAR_H + PAD * 0.35

# Assemble exact SVG matching video reference
parts = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, '
    f'Menlo, Consolas, monospace">'
)
parts.append('<defs>'
             f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
             f'</linearGradient></defs>')

parts.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>')
parts.append(f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" '
             f'fill="none" stroke="{FRAME}" stroke-width="1"/>')

parts.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
             f'text-anchor="middle">diwakar@github: ~$ ./portrait.sh</text>')

font_size = CELL_H * 0.86
for ry, line in enumerate(rows_txt):
    y = art_top + ry * CELL_H + CELL_H * 0.74
    row_y = art_top + ry * CELL_H
    delay = ry * STAGGER
    safe = html.escape(line)
    text = (f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
            f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">{safe}</text>')

    if STATIC:
        parts.append(text)
        continue

    # Wipe clip-path per row
    parts.append(
        f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
        f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
    )
    parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
    # Block cursor riding the reveal edge
    parts.append(
        f'<rect y="{row_y+1:.1f}" width="{CELL_W}" height="{CELL_H-2}" fill="{CURSOR}" opacity="0">'
        f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
    )

# Status bar with blinking terminal cursor
status_line_y = TITLEBAR_H + ART_H + PAD * 0.35
status_y = status_line_y + 19
parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="13">'
             f'diwakar@github:~$ whoami <tspan fill="{INK}">Diwakar Reddy</tspan></text>')
status_chars = len("diwakar@github:~$ whoami Diwakar Reddy ")
parts.append(f'<rect x="{PAD + status_chars * 13 * 0.6:.1f}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" repeatCount="indefinite"/></rect>')

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"[SUCCESS] Wrote {OUT}: {CANVAS_W} x {CANVAS_H}, {len(svg)//1024} KB")
