#!/usr/bin/env python3
"""
ascii_portrait.py
Converts assets/photo.jpg to a monochrome animated terminal ASCII portrait (ascii-portrait.svg):
- Header: diwakar@github: ~/portrait.sh
- Character Ramp: " .:-=+*#%@"
- Monochromatic / Green terminal shading on dark background (#0d1117)
- Footer line: $ whoami  Diwakar
"""

import os
import sys
from PIL import Image, ImageEnhance, ImageOps

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PHOTO_PATH = os.path.join(ASSETS_DIR, "photo.jpg")
OUTPUT_SVG = os.path.join(BASE_DIR, "ascii-portrait.svg")

# Character density ramp from darkest to brightest
DENSITY_RAMP = " .:-=+*#%@"


def load_and_convert_photo(photo_path, ascii_width=46):
    if not os.path.exists(photo_path):
        # Fall back to root photo
        photo_path = os.path.join(BASE_DIR, "IMG_9746.JPG.jpeg")
        if not os.path.exists(photo_path):
            print(f"[ERROR] Photo not found at {photo_path}")
            return None

    try:
        img = Image.open(photo_path)
        w, h = img.size

        # Crop to headshot focus if needed
        if 0.8 <= (w / float(h)) <= 1.2:
            left = int(w * 0.38)
            top = int(h * 0.25)
            right = int(w * 0.70)
            bottom = int(h * 0.67)
            img = img.crop((left, top, right, bottom))

        # Convert to grayscale and apply contrast boost
        gray = img.convert("L")
        gray = ImageOps.autocontrast(gray, cutoff=2)
        gray_contrast = ImageEnhance.Contrast(gray).enhance(1.8)
        gray_sharp = ImageEnhance.Sharpness(gray_contrast).enhance(1.8)

        # 0.5 Aspect Ratio Correction for Monospace character height
        ascii_height = int((float(gray_sharp.size[1]) / float(gray_sharp.size[0])) * ascii_width * 0.52)

        img_resized = gray_sharp.resize((ascii_width, ascii_height), Image.Resampling.LANCZOS)
        pixels = list(img_resized.tobytes())

        ramp_len = len(DENSITY_RAMP)
        lines = []

        for row in range(ascii_height):
            line_cells = []
            for col in range(ascii_width):
                p = pixels[row * ascii_width + col]
                # Map pixel value 0..255 to index
                char_idx = int((p / 255.0) * (ramp_len - 1))
                char_val = DENSITY_RAMP[char_idx]

                # Monochrome white/grey palette with green accents
                if char_idx >= 7:
                    color = "#e6edf3"  # Bright white/light grey
                elif char_idx >= 4:
                    color = "#8b949e"  # Mid grey
                elif char_idx >= 2:
                    color = "#3fb950"  # Terminal green
                else:
                    color = "#26a641"  # Deep green background accent

                line_cells.append({"char": char_val, "color": color})
            lines.append(line_cells)

        return lines
    except Exception as e:
        print(f"[ERROR] ASCII Conversion Error: {e}")
        return None


def generate_ascii_svg(ascii_lines):
    svg_width = 370
    svg_height = 490
    total_loop_time = 10.0

    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">')
    svg_lines.append('<defs>')

    # Scanline pattern
    svg_lines.append('  <pattern id="scanlines" width="100" height="4" patternUnits="userSpaceOnUse">')
    svg_lines.append('    <line x1="0" y1="0" x2="100" y2="0" stroke="#000000" stroke-width="1" opacity="0.2" />')
    svg_lines.append('  </pattern>')

    # Laser beam gradient
    svg_lines.append('  <linearGradient id="laserGrad" x1="0%" y1="0%" x2="0%" y2="100%">')
    svg_lines.append('    <stop offset="0%" stop-color="#3fb950" stop-opacity="0" />')
    svg_lines.append('    <stop offset="50%" stop-color="#56d364" stop-opacity="0.75" />')
    svg_lines.append('    <stop offset="100%" stop-color="#3fb950" stop-opacity="0" />')
    svg_lines.append('  </linearGradient>')

    svg_lines.append('<style>')
    svg_lines.append(f'''
        @keyframes windowAppear {{
            0% {{ opacity: 0; transform: scale(0.98); }}
            3% {{ opacity: 1; transform: scale(1); }}
            92% {{ opacity: 1; transform: scale(1); }}
            97% {{ opacity: 0; transform: scale(0.99); }}
            100% {{ opacity: 0; }}
        }}
        @keyframes laserSweep {{
            0%, 45% {{ transform: translateY(0px); opacity: 0; }}
            47% {{ opacity: 0.85; }}
            65% {{ transform: translateY(300px); opacity: 0.85; }}
            67% {{ opacity: 0; }}
            100% {{ opacity: 0; }}
        }}
        @keyframes cursorBlink {{
            0%, 49% {{ opacity: 1; }}
            50%, 100% {{ opacity: 0; }}
        }}

        .bg {{ fill: #0d1117; rx: 10px; ry: 10px; stroke: #30363d; stroke-width: 1px; }}
        .dot-red {{ fill: #ff5f56; }}
        .dot-yellow {{ fill: #ffbd2e; }}
        .dot-green {{ fill: #27c93f; }}
        .term-title {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11.5px; fill: #8b949e; font-weight: 600; }}
        
        .prompt-txt {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11px; fill: #58a6ff; font-weight: bold; }}
        .load-txt {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 10px; fill: #8b949e; }}
        
        .ascii-row-txt {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 7.5px;
            font-weight: bold;
            white-space: pre;
            letter-spacing: 0.3px;
            text-anchor: middle;
        }}
        .laser-beam {{ animation: laserSweep {total_loop_time}s ease-in-out infinite; }}
        .footer-txt {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11px; fill: #e6edf3; font-weight: bold; }}
        .footer-whoami {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11px; fill: #3fb950; font-weight: bold; }}
        .blink-cursor {{ animation: cursorBlink 0.8s infinite; fill: #3fb950; }}
    ''')
    svg_lines.append('</style>')
    svg_lines.append('</defs>')

    # Outer Terminal Background
    svg_lines.append(f'<rect width="{svg_width}" height="{svg_height}" class="bg" />')

    # Header Bar: diwakar@github: ~/portrait.sh
    svg_lines.append('<g>')
    svg_lines.append('  <circle cx="20" cy="20" r="4.5" class="dot-red" />')
    svg_lines.append('  <circle cx="34" cy="20" r="4.5" class="dot-yellow" />')
    svg_lines.append('  <circle cx="48" cy="20" r="4.5" class="dot-green" />')
    svg_lines.append('  <text x="62" y="24" class="term-title">diwakar@github: ~/portrait.sh</text>')
    svg_lines.append('</g>')

    # Terminal Header Divider
    svg_lines.append('<line x1="10" y1="36" x2="360" y2="36" stroke="#21262d" stroke-width="1" />')

    # Prompt Command
    svg_lines.append('<g transform="translate(18, 54)">')
    svg_lines.append('  <text class="prompt-txt">$ ./render_portrait.sh</text>')
    svg_lines.append('</g>')

    # ASCII Face Grid (Centered at x=185 with 35px side padding)
    svg_lines.append('<g transform="translate(0, 78)">')

    num_rows = len(ascii_lines)
    step_delay = 2.5 / max(num_rows, 1)

    for i, line_cells in enumerate(ascii_lines):
        y_pos = i * 10.5
        row_delay = round(1.8 + (i * step_delay), 2)
        row_anim_name = f"showRow_{i}"

        row_anim = f'''
            @keyframes {row_anim_name} {{
                0% {{ opacity: 0; transform: translateY(-2px); }}
                {int((row_delay / total_loop_time) * 100)}% {{ opacity: 0; transform: translateY(-2px); }}
                {int(((row_delay + 0.1) / total_loop_time) * 100)}% {{ opacity: 1; transform: translateY(0); }}
                92% {{ opacity: 1; transform: translateY(0); }}
                97% {{ opacity: 0; }}
                100% {{ opacity: 0; }}
            }}
        '''
        svg_lines.insert(len(svg_lines) - 1, f'    <style> .row-{i} {{ animation: {row_anim_name} {total_loop_time}s ease-out infinite; }} </style>')

        svg_lines.append(f'  <text x="185" y="{y_pos}" class="ascii-row-txt row-{i}">')
        for cell in line_cells:
            char_val = cell["char"]
            color_val = cell["color"]
            escaped_char = char_val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace(" ", "&#160;")
            svg_lines.append(f'<tspan fill="{color_val}">{escaped_char}</tspan>')
        svg_lines.append('</text>')

    svg_lines.append('</g>')

    # Laser scanline beam
    svg_lines.append('  <g transform="translate(14, 75)">')
    svg_lines.append('    <rect x="0" y="0" width="342" height="12" fill="url(#laserGrad)" class="laser-beam" />')
    svg_lines.append('  </g>')

    # CRT scanline pattern overlay
    svg_lines.append('  <rect x="12" y="70" width="346" height="360" fill="url(#scanlines)" pointer-events="none" />')

    # Footer Divider Line & Footer Command: $ whoami  Diwakar
    svg_lines.append('  <line x1="10" y1="440" x2="360" y2="440" stroke="#30363d" stroke-width="1" />')
    svg_lines.append('  <g transform="translate(18, 465)">')
    svg_lines.append('    <text x="0" y="0" class="footer-txt">$ whoami  <tspan class="footer-whoami">Diwakar</tspan></text>')
    svg_lines.append('    <rect x="155" y="-9" width="7" height="11" class="blink-cursor" />')
    svg_lines.append('  </g>')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def main():
    print(f"[INFO] Generating ASCII portrait from photo: {PHOTO_PATH}")
    ascii_lines = load_and_convert_photo(PHOTO_PATH, ascii_width=44)
    if not ascii_lines:
        print("[ERROR] Could not load image for ASCII conversion.")
        sys.exit(1)

    svg_content = generate_ascii_svg(ascii_lines)
    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[SUCCESS] ASCII Portrait SVG generated at: {OUTPUT_SVG}")


if __name__ == "__main__":
    main()
