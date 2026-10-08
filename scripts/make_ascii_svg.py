#!/usr/bin/env python3
"""
make_ascii_svg.py
Redesigns ascii-portrait.svg with primary focus on face recognizability:
- 100% Focused Headshot Crop of Diwakar's face, hair, smile, beard & shoulders
- 30-column ASCII resolution filling ~75% of usable terminal width
- Centered alignment (x=185, text-anchor="middle") with bold monospace font
- Multi-stage terminal boot animation:
  Stage 1: Terminal window fade-in
  Stage 2: Command typing ($ ./render_portrait.sh)
  Stage 3: Image loading progress bar ([████████████████████] 100%)
  Stage 4: Line-by-line ASCII portrait reveal
  Stage 5: Vertical CRT laser scanline sweep
  Stage 6: Status bar & blinking cursor
  Stage 7: Smooth loop restart cycle
"""

import os
import sys
from PIL import Image, ImageEnhance

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PREPROCESSED_PHOTO = os.path.join(DATA_DIR, "preprocessed_photo.png")
OUTPUT_SVG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ascii-portrait.svg")

# Density ramp requested by spec
DENSITY_RAMP = " .:-=+*#%@"


def generate_ascii_grid_from_photo(photo_path, ascii_width=30):
    if not os.path.exists(photo_path):
        return None

    try:
        img = Image.open(photo_path)
        w, h = img.size

        # Tight Face & Headshot Crop Focus (Diwakar's face & hair)
        if 0.8 <= (w / float(h)) <= 1.2:
            left = int(w * 0.36)
            top = int(h * 0.23)
            right = int(w * 0.64)
            bottom = int(h * 0.58)
            img = img.crop((left, top, right, bottom))

        # Convert to grayscale & optimize contrast for high face definition
        gray = img.convert("L")
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(2.5)

        # Aspect ratio compensation for monospace character height (~0.52 ratio)
        w_percent = ascii_width / float(enhanced.size[0])
        ascii_height = int((float(enhanced.size[1]) * float(w_percent)) * 0.52)

        img_resized = enhanced.resize((ascii_width, ascii_height), Image.Resampling.LANCZOS)
        pixels = list(img_resized.tobytes())

        ramp_len = len(DENSITY_RAMP)
        lines = []

        for row in range(ascii_height):
            line_chars = []
            for col in range(ascii_width):
                p = pixels[row * ascii_width + col]
                # Map 0..255 to index 0..ramp_len-1
                char_idx = int((p / 255.0) * (ramp_len - 1))
                line_chars.append(DENSITY_RAMP[char_idx])
            lines.append("".join(line_chars))

        return lines
    except Exception as e:
        print(f"[ERROR] Failed to convert image to ASCII: {e}")
        return None


def generate_redesigned_animated_svg(ascii_lines):
    svg_width = 370
    svg_height = 450
    total_loop_time = 10.0  # seconds

    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">')
    svg_lines.append('<defs>')
    
    # CRT Scanline Pattern
    svg_lines.append('  <pattern id="scanlines" width="100" height="4" patternUnits="userSpaceOnUse">')
    svg_lines.append('    <line x1="0" y1="0" x2="100" y2="0" stroke="#000000" stroke-width="1" opacity="0.25" />')
    svg_lines.append('  </pattern>')

    # Vertical Scanline Laser Gradient
    svg_lines.append('  <linearGradient id="laserGrad" x1="0%" y1="0%" x2="0%" y2="100%">')
    svg_lines.append('    <stop offset="0%" stop-color="#3fb950" stop-opacity="0" />')
    svg_lines.append('    <stop offset="50%" stop-color="#56d364" stop-opacity="0.85" />')
    svg_lines.append('    <stop offset="100%" stop-color="#3fb950" stop-opacity="0" />')
    svg_lines.append('  </linearGradient>')

    svg_lines.append('<style>')
    svg_lines.append(f'''
        /* Overall Loop Timeline ({total_loop_time}s) */
        @keyframes windowAppear {{
            0% {{ opacity: 0; transform: scale(0.96); }}
            4% {{ opacity: 1; transform: scale(1); }}
            92% {{ opacity: 1; transform: scale(1); }}
            98% {{ opacity: 0; transform: scale(0.98); }}
            100% {{ opacity: 0; }}
        }}
        @keyframes typeCmd {{
            0% {{ width: 0ch; opacity: 1; }}
            12% {{ width: 23ch; opacity: 1; }}
            92% {{ width: 23ch; opacity: 1; }}
            98% {{ width: 0ch; opacity: 0; }}
            100% {{ width: 0ch; opacity: 0; }}
        }}
        @keyframes showLoading {{
            0% {{ opacity: 0; }}
            14% {{ opacity: 0; }}
            16% {{ opacity: 1; }}
            92% {{ opacity: 1; }}
            98% {{ opacity: 0; }}
            100% {{ opacity: 0; }}
        }}
        @keyframes progressFill {{
            0% {{ width: 0px; }}
            16% {{ width: 0px; }}
            25% {{ width: 140px; }}
            92% {{ width: 140px; }}
            98% {{ width: 0px; }}
            100% {{ width: 0px; }}
        }}
        @keyframes laserSweep {{
            0% {{ transform: translateY(0px); opacity: 0; }}
            58% {{ transform: translateY(0px); opacity: 0; }}
            60% {{ opacity: 0.9; }}
            78% {{ transform: translateY(300px); opacity: 0.9; }}
            80% {{ opacity: 0; }}
            100% {{ opacity: 0; }}
        }}
        @keyframes cursorBlink {{
            0%, 49% {{ opacity: 1; }}
            50%, 100% {{ opacity: 0; }}
        }}

        .term-card {{
            animation: windowAppear {total_loop_time}s ease-in-out infinite;
            transform-origin: center;
        }}
        .bg {{ fill: #0d1117; rx: 10px; ry: 10px; stroke: #30363d; stroke-width: 1px; }}
        .dot-red {{ fill: #ff5f56; }}
        .dot-yellow {{ fill: #ffbd2e; }}
        .dot-green {{ fill: #27c93f; }}
        .term-title {{ font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 11.5px; fill: #8b949e; font-weight: 600; }}
        
        .prompt-txt {{
            font-family: 'Fira Code', Consolas, 'Courier New', monospace;
            font-size: 11px;
            fill: #58a6ff;
            font-weight: bold;
            white-space: nowrap;
            overflow: hidden;
            display: inline-block;
            animation: typeCmd {total_loop_time}s steps(23) infinite;
        }}
        .loading-box {{ animation: showLoading {total_loop_time}s infinite; }}
        .load-txt {{ font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 10px; fill: #8b949e; }}
        .progress-bg {{ fill: #161b22; rx: 3px; ry: 3px; }}
        .progress-bar {{ fill: #3fb950; rx: 3px; ry: 3px; animation: progressFill {total_loop_time}s ease-out infinite; }}
        
        /* Centered bold ASCII Face Grid (75% usable terminal width) */
        .ascii-text {{
            font-family: 'Fira Code', Consolas, 'Courier New', monospace;
            font-size: 11.5px;
            font-weight: bold;
            fill: #3fb950;
            white-space: pre;
            letter-spacing: 1.2px;
            text-anchor: middle;
        }}
        .laser-beam {{
            animation: laserSweep {total_loop_time}s ease-in-out infinite;
        }}
        .footer-txt {{ font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 10px; fill: #8b949e; }}
        .status-online {{ fill: #3fb950; font-weight: bold; }}
        .blink-cursor {{ animation: cursorBlink 0.8s infinite; fill: #3fb950; }}
    ''')
    svg_lines.append('</style>')
    svg_lines.append('</defs>')

    # Outer Terminal Group
    svg_lines.append('<g class="term-card">')

    # Background Card
    svg_lines.append(f'  <rect width="{svg_width}" height="{svg_height}" class="bg" />')

    # Terminal Top Bar
    svg_lines.append('  <g>')
    svg_lines.append('    <circle cx="20" cy="20" r="4.5" class="dot-red" />')
    svg_lines.append('    <circle cx="34" cy="20" r="4.5" class="dot-yellow" />')
    svg_lines.append('    <circle cx="48" cy="20" r="4.5" class="dot-green" />')
    svg_lines.append('    <text x="62" y="24" class="term-title">diwakar@github: ~/portrait.asc</text>')
    svg_lines.append('  </g>')

    # Terminal Top Divider
    svg_lines.append('  <line x1="10" y1="36" x2="360" y2="36" stroke="#21262d" stroke-width="1" />')

    # STAGE 2: Command Prompt Typing
    svg_lines.append('  <g transform="translate(18, 54)">')
    svg_lines.append('    <text class="prompt-txt">$ ./render_portrait.sh</text>')
    svg_lines.append('  </g>')

    # STAGE 3: Loading Progress Indicator
    svg_lines.append('  <g class="loading-box" transform="translate(18, 70)">')
    svg_lines.append('    <text x="0" y="0" class="load-txt">Loading face: IMG_9746.JPG ...</text>')
    svg_lines.append('    <rect x="0" y="8" width="140" height="6" class="progress-bg" />')
    svg_lines.append('    <rect x="0" y="8" width="0" height="6" class="progress-bar" />')
    svg_lines.append('  </g>')

    # STAGE 4: Centered Bold ASCII Face Reveal
    svg_lines.append('  <g class="ascii-text" transform="translate(0, 108)">')
    
    num_rows = len(ascii_lines)
    # Reveal rows between 2.6s and 5.6s (3.0s total reveal time across rows)
    step_delay = 3.0 / max(num_rows, 1)

    for i, line in enumerate(ascii_lines):
        y_pos = i * 14.5
        row_delay = round(2.6 + (i * step_delay), 2)
        escaped_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace(" ", "&#160;")
        
        # Row visibility animation using keyframes
        row_anim = f'''
            @keyframes showRow_{i} {{
                0% {{ opacity: 0; transform: translateY(-2px); }}
                {int((row_delay / total_loop_time) * 100)}% {{ opacity: 0; transform: translateY(-2px); }}
                {int(((row_delay + 0.15) / total_loop_time) * 100)}% {{ opacity: 1; transform: translateY(0); }}
                92% {{ opacity: 1; transform: translateY(0); }}
                98% {{ opacity: 0; }}
                100% {{ opacity: 0; }}
            }}
        '''
        # Embed row animation style rule
        svg_lines.insert(len(svg_lines) - 1, f'    <style> .row-{i} {{ animation: showRow_{i} {total_loop_time}s ease-out infinite; }} </style>')
        svg_lines.append(f'    <text x="185" y="{y_pos}" class="row-{i}">{escaped_line}</text>')
        
    svg_lines.append('  </g>')

    # STAGE 5: Vertical CRT Laser Scanline Beam
    svg_lines.append('  <g transform="translate(14, 95)">')
    svg_lines.append('    <rect x="0" y="0" width="342" height="12" fill="url(#laserGrad)" class="laser-beam" />')
    svg_lines.append('  </g>')

    # CRT Scanline Pattern Overlay over portrait area
    svg_lines.append('  <rect x="12" y="90" width="346" height="315" fill="url(#scanlines)" pointer-events="none" />')

    # STAGE 6: Terminal Footer & Status Bar
    svg_lines.append('  <line x1="10" y1="412" x2="360" y2="412" stroke="#21262d" stroke-width="1" />')
    svg_lines.append('  <g transform="translate(18, 430)">')
    svg_lines.append('    <text x="0" y="0" class="footer-txt">STATUS: <tspan class="status-online">ONLINE</tspan></text>')
    svg_lines.append('    <text x="140" y="0" class="footer-txt">FACE FOCUS: 100%</text>')
    svg_lines.append('    <rect x="250" y="-9" width="7" height="11" class="blink-cursor" />')
    svg_lines.append('  </g>')

    svg_lines.append('</g>')
    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def main():
    raw_photo = None
    for cand in ["IMG_9746.JPG.jpeg", os.path.join(DATA_DIR, "photo.jpg"), "photo.jpg", PREPROCESSED_PHOTO]:
        if os.path.exists(cand):
            raw_photo = cand
            break

    if not raw_photo:
        print("[ERROR] Could not find source photo (IMG_9746.JPG.jpeg).")
        sys.exit(1)

    print(f"[INFO] Generating centered face-focused ASCII portrait from: {raw_photo}")
    ascii_lines = generate_ascii_grid_from_photo(raw_photo, ascii_width=30)

    if not ascii_lines:
        print("[ERROR] ASCII conversion failed.")
        sys.exit(1)

    svg_content = generate_redesigned_animated_svg(ascii_lines)

    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"[SUCCESS] Centered face-focused ASCII portrait SVG generated at: {OUTPUT_SVG}")


if __name__ == "__main__":
    main()
