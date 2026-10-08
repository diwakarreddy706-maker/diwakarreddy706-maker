#!/usr/bin/env python3
"""
make_ascii_svg.py
Converts a preprocessed photo (or fallback image) into a monochrome animated SVG ASCII portrait.
If no photo is found, generates a clearly marked developer avatar ASCII placeholder SVG.
Output: ascii-portrait.svg in the repository root.
"""

import os
import sys
from PIL import Image

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PREPROCESSED_PHOTO = os.path.join(DATA_DIR, "preprocessed_photo.png")
OUTPUT_SVG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ascii-portrait.svg")

# Density ramp specified in requirements
DENSITY_RAMP = " .`:-=+*cs#%@"

# Default placeholder ASCII portrait lines when no photo is provided
PLACEHOLDER_ASCII = [
    "   ===================================   ",
    "   |    [ DEVELOPER ASCII PORTRAIT ] |   ",
    "   ===================================   ",
    "                                         ",
    "               .----------------.        ",
    "              /   .-----------.  \\       ",
    "             /   /   (o) (o)   \\  \\      ",
    "            |   |       ^       |  |     ",
    "            |   |    \\_____/    |  |     ",
    "             \\   \\             /  /      ",
    "              \\   '-----------'  /       ",
    "               '----------------'        ",
    "                  /|   ||   |\\           ",
    "                 / |   ||   | \\          ",
    "                /  |===||===|  \\         ",
    "               (   |   ||   |   )        ",
    "                |  |___||___|  |         ",
    "                |  |        |  |         ",
    "               /____\\      /____\\        ",
    "                                         ",
    "   -----------------------------------   ",
    "   | [PLACEHOLDER] Add photo.jpg and |   ",
    "   | run python scripts/prep_photo.py|   ",
    "   -----------------------------------   "
]


def image_to_ascii_lines(image_path, width=46):
    """Converts a photo to a list of ASCII strings using the density ramp."""
    if not os.path.exists(image_path):
        return None

    try:
        img = Image.open(image_path).convert("L")
        # Aspect ratio compensation for character cell height (~0.5)
        w_percent = width / float(img.size[0])
        h_size = int((float(img.size[1]) * float(w_percent)) * 0.5)
        
        img_resized = img.resize((width, h_size), Image.Resampling.LANCZOS)
        
        pixels = list(img_resized.tobytes())
        ramp_len = len(DENSITY_RAMP)
        
        ascii_lines = []
        for row in range(h_size):
            line_chars = []
            for col in range(width):
                pixel_val = pixels[row * width + col]
                # Map 0..255 to index 0..ramp_len-1
                char_idx = int((pixel_val / 255.0) * (ramp_len - 1))
                line_chars.append(DENSITY_RAMP[char_idx])
            ascii_lines.append("".join(line_chars))
            
        return ascii_lines
    except Exception as e:
        print(f"[WARNING] Error reading photo for ASCII conversion: {e}")
        return None


def generate_ascii_svg(ascii_lines, is_placeholder=False):
    svg_width = 370
    svg_height = 450
    start_y = 62
    line_height = 14
    
    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">')
    svg_lines.append('<defs>')
    svg_lines.append('<style>')
    svg_lines.append('''
        @keyframes printRow {
            0% { opacity: 0; transform: translateY(-4px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        .bg { fill: #0d1117; rx: 10px; ry: 10px; stroke: #30363d; stroke-width: 1px; }
        .dot-red { fill: #ff5f56; }
        .dot-yellow { fill: #ffbd2e; }
        .dot-green { fill: #27c93f; }
        .term-title { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 12px; fill: #8b949e; font-weight: 600; }
        .ascii-text {
            font-family: 'Fira Code', Consolas, 'Courier New', monospace;
            font-size: 10px;
            fill: #3fb950;
            white-space: pre;
        }
        .ascii-row {
            animation: printRow 0.15s ease-out forwards;
            opacity: 0;
        }
    ''')
    svg_lines.append('</style>')
    svg_lines.append('</defs>')

    # Background Card
    svg_lines.append(f'<rect width="{svg_width}" height="{svg_height}" class="bg" />')

    # Terminal Top Bar
    svg_lines.append('<g>')
    svg_lines.append('  <circle cx="20" cy="22" r="5" class="dot-red" />')
    svg_lines.append('  <circle cx="35" cy="22" r="5" class="dot-yellow" />')
    svg_lines.append('  <circle cx="50" cy="22" r="5" class="dot-green" />')
    title_text = "diwakarr@github: ~/portrait.asc" if not is_placeholder else "diwakarr@github: ~/placeholder.asc"
    svg_lines.append(f'  <text x="65" y="26" class="term-title">{title_text}</text>')
    svg_lines.append('</g>')

    # Terminal Divider Line
    svg_lines.append('<line x1="12" y1="38" x2="358" y2="38" stroke="#21262d" stroke-width="1" />')

    # ASCII Text Rows
    svg_lines.append('<g class="ascii-text">')
    for i, line in enumerate(ascii_lines):
        y_pos = start_y + (i * line_height)
        if y_pos > svg_height - 15:
            break
        delay = round(0.1 + (i * 0.035), 3)
        # Escape XML characters inside ASCII string
        escaped_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace(" ", "&#160;")
        svg_lines.append(f'  <text x="18" y="{y_pos}" class="ascii-row" style="animation-delay: {delay}s;">{escaped_line}</text>')
    svg_lines.append('</g>')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def main():
    ascii_lines = None
    is_placeholder = False

    # Check for preprocessed photo or potential original photo
    if os.path.exists(PREPROCESSED_PHOTO):
        print(f"[INFO] Found preprocessed photo at: {PREPROCESSED_PHOTO}")
        ascii_lines = image_to_ascii_lines(PREPROCESSED_PHOTO, width=42)

    if not ascii_lines:
        # Check raw photo candidates in data/ or root directory
        raw_candidates = [
            os.path.join(DATA_DIR, "photo.jpg"),
            os.path.join(DATA_DIR, "photo.png"),
            "d.1.jpeg",
            "IMG_9746.JPG.jpeg",
            "photo.jpg",
            "photo.png",
            "profile.jpg",
            "profile.png"
        ]
        for cand in raw_candidates:
            if os.path.exists(cand):
                print(f"[INFO] Found raw photo candidate at: {cand}")
                ascii_lines = image_to_ascii_lines(cand, width=42)
                if ascii_lines:
                    break

    if not ascii_lines:
        print("[NOTICE] No valid photo found. Generating placeholder ASCII portrait SVG...")
        ascii_lines = PLACEHOLDER_ASCII
        is_placeholder = True

    svg_content = generate_ascii_svg(ascii_lines, is_placeholder=is_placeholder)

    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"[SUCCESS] ASCII portrait SVG saved to: {OUTPUT_SVG}")
    if is_placeholder:
        print("[INFO] To replace placeholder with your own photo later:")
        print("       1. Place your photo file at data/photo.jpg")
        print("       2. Run: python scripts/prep_photo.py data/photo.jpg")
        print("       3. Run: python scripts/make_ascii_svg.py")


if __name__ == "__main__":
    main()
