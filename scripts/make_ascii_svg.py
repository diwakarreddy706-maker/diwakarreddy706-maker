#!/usr/bin/env python3
"""
make_ascii_svg.py
Redesigns ascii-portrait.svg into a large, highly recognizable animated terminal portrait:
- Generates ASCII directly from IMG_9746.JPG.jpeg using tight face & headshot crop
- Uses controlled density ramp: " .:-=+*#%@"
- Character multi-color shading (dark: #26a641, mid: #3fb950, bright: #7ee787)
- Large portrait filling ~75-80% of usable terminal width & height
- 6-Phase Terminal Animation Loop (10s continuous cycle):
  Phase 1: Startup & Command Typing ($ ./render_portrait.sh)
  Phase 2: Loading Sequence & Progress Bar ([████████████████] 100%)
  Phase 3: Top-to-Bottom Line-by-Line ASCII Render
  Phase 4: Subtle Top-to-Bottom Scanline Beam Pass
  Phase 5: Finished State (PORTRAIT_RENDERED ✓ + Blinking Cursor █)
  Phase 6: Smooth Loop Restart Cycle
"""

import os
import sys
from PIL import Image, ImageEnhance

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PREPROCESSED_PHOTO = os.path.join(DATA_DIR, "preprocessed_photo.png")
OUTPUT_SVG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ascii-portrait.svg")

# Exact character ramp specified in prompt
DENSITY_RAMP = " .:-=+*#%@"


def generate_ascii_grid_from_photo(photo_path, ascii_width=30):
    if not os.path.exists(photo_path):
        return None

    try:
        img = Image.open(photo_path)
        w, h = img.size

        # Tight Face, Hair, Beard & Shoulder Crop Focus from IMG_9746.JPG.jpeg
        if 0.8 <= (w / float(h)) <= 1.2:
            left = int(w * 0.35)
            top = int(h * 0.22)
            right = int(w * 0.65)
            bottom = int(h * 0.60)
            img = img.crop((left, top, right, bottom))

        # Convert to grayscale & optimize contrast for crisp facial features
        gray = img.convert("L")
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(2.3)

        # Aspect ratio compensation for monospace character height (~0.52 ratio)
        w_percent = ascii_width / float(enhanced.size[0])
        ascii_height = int((float(enhanced.size[1]) * float(w_percent)) * 0.52)

        img_resized = enhanced.resize((ascii_width, ascii_height), Image.Resampling.LANCZOS)
        pixels = list(img_resized.tobytes())

        ramp_len = len(DENSITY_RAMP)
        lines = []

        for row in range(ascii_height):
            line_cells = []
            for col in range(ascii_width):
                p = pixels[row * ascii_width + col]
                # Map 0..255 to index 0..ramp_len-1
                char_idx = int((p / 255.0) * (ramp_len - 1))
                char_val = DENSITY_RAMP[char_idx]
                
                # Determine color tier based on character density for visual depth
                if char_idx <= 2:
                    color = "#26a641"  # Dark / shadow tier
                elif char_idx <= 6:
                    color = "#3fb950"  # Midtone tier
                else:
                    color = "#7ee787"  # Highlight tier (smile, forehead, collar)
                    
                line_cells.append({"char": char_val, "color": color})
            lines.append(line_cells)

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
    svg_lines.append('    <stop offset="50%" stop-color="#56d364" stop-opacity="0.75" />')
    svg_lines.append('    <stop offset="100%" stop-color="#3fb950" stop-opacity="0" />')
    svg_lines.append('  </linearGradient>')

    svg_lines.append('<style>')
    svg_lines.append(f'''
        /* Overall 10s Timeline */
        @keyframes windowAppear {{
            0% {{ opacity: 0; transform: scale(0.97); }}
            3% {{ opacity: 1; transform: scale(1); }}
            92% {{ opacity: 1; transform: scale(1); }}
            97% {{ opacity: 0; transform: scale(0.98); }}
            100% {{ opacity: 0; }}
        }}
        @keyframes typeCmd {{
            0% {{ width: 0ch; opacity: 1; }}
            10% {{ width: 23ch; opacity: 1; }}
            92% {{ width: 23ch; opacity: 1; }}
            97% {{ width: 0ch; opacity: 0; }}
            100% {{ width: 0ch; opacity: 0; }}
        }}
        @keyframes showLoadingText {{
            0%, 9% {{ opacity: 0; }}
            11% {{ opacity: 1; }}
            92% {{ opacity: 1; }}
            97% {{ opacity: 0; }}
            100% {{ opacity: 0; }}
        }}
        @keyframes progressStep {{
            0%, 11% {{ width: 0px; }}
            13% {{ width: 35px; }}  /* 25% */
            15% {{ width: 70px; }}  /* 50% */
            17% {{ width: 105px; }} /* 75% */
            19% {{ width: 140px; }} /* 100% */
            92% {{ width: 140px; }}
            97% {{ width: 0px; }}
            100% {{ width: 0px; }}
        }}
        @keyframes laserSweep {{
            0%, 46% {{ transform: translateY(0px); opacity: 0; }}
            48% {{ opacity: 0.85; }}
            65% {{ transform: translateY(300px); opacity: 0.85; }}
            67% {{ opacity: 0; }}
            100% {{ opacity: 0; }}
        }}
        @keyframes showFooter {{
            0%, 45% {{ opacity: 0; }}
            48% {{ opacity: 1; }}
            92% {{ opacity: 1; }}
            97% {{ opacity: 0; }}
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
        .loading-box {{ animation: showLoadingText {total_loop_time}s infinite; }}
        .load-txt {{ font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 10px; fill: #8b949e; }}
        .progress-bg {{ fill: #161b22; rx: 3px; ry: 3px; }}
        .progress-bar {{ fill: #3fb950; rx: 3px; ry: 3px; animation: progressStep {total_loop_time}s ease-out infinite; }}
        
        /* Centered Large ASCII Face Grid (occupies ~75-80% usable terminal space) */
        .ascii-row-txt {{
            font-family: 'Fira Code', Consolas, 'Courier New', monospace;
            font-size: 12.5px;
            font-weight: bold;
            white-space: pre;
            letter-spacing: 1.4px;
            text-anchor: middle;
        }}
        .laser-beam {{
            animation: laserSweep {total_loop_time}s ease-in-out infinite;
        }}
        .footer-group {{ animation: showFooter {total_loop_time}s infinite; }}
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

    # PHASE 1: Terminal Header
    svg_lines.append('  <g>')
    svg_lines.append('    <circle cx="20" cy="20" r="4.5" class="dot-red" />')
    svg_lines.append('    <circle cx="34" cy="20" r="4.5" class="dot-yellow" />')
    svg_lines.append('    <circle cx="48" cy="20" r="4.5" class="dot-green" />')
    svg_lines.append('    <text x="62" y="24" class="term-title">diwakar@github: ~/portrait.asc</text>')
    svg_lines.append('  </g>')

    # Terminal Header Divider
    svg_lines.append('  <line x1="10" y1="36" x2="360" y2="36" stroke="#21262d" stroke-width="1" />')

    # PHASE 1: Command Prompt Typing ($ ./render_portrait.sh)
    svg_lines.append('  <g transform="translate(18, 54)">')
    svg_lines.append('    <text class="prompt-txt">$ ./render_portrait.sh</text>')
    svg_lines.append('  </g>')

    # PHASE 2: Loading Sequence & Progress Bar
    svg_lines.append('  <g class="loading-box" transform="translate(18, 70)">')
    svg_lines.append('    <text x="0" y="0" class="load-txt">Loading IMG_9746.JPG.jpeg ...</text>')
    svg_lines.append('    <rect x="0" y="8" width="140" height="6" class="progress-bg" />')
    svg_lines.append('    <rect x="0" y="8" width="0" height="6" class="progress-bar" />')
    svg_lines.append('  </g>')

    # PHASE 3: Large Centered Line-by-Line ASCII Portrait Reveal
    svg_lines.append('  <g transform="translate(0, 108)">')
    
    num_rows = len(ascii_lines)
    # Line reveal between 2.0s and 4.2s (2.2s total reveal time across rows)
    step_delay = 2.2 / max(num_rows, 1)

    for i, line_cells in enumerate(ascii_lines):
        y_pos = i * 15.0
        row_delay = round(2.0 + (i * step_delay), 2)
        
        # Row visibility animation
        row_anim = f'''
            @keyframes showRow_{i} {{
                0% {{ opacity: 0; transform: translateY(-2px); }}
                {int((row_delay / total_loop_time) * 100)}% {{ opacity: 0; transform: translateY(-2px); }}
                {int(((row_delay + 0.12) / total_loop_time) * 100)}% {{ opacity: 1; transform: translateY(0); }}
                92% {{ opacity: 1; transform: translateY(0); }}
                97% {{ opacity: 0; }}
                100% {{ opacity: 0; }}
            }}
        '''
        svg_lines.insert(len(svg_lines) - 1, f'    <style> .row-{i} {{ animation: showRow_{i} {total_loop_time}s ease-out infinite; }} </style>')
        
        # Render row text with multi-color character tspans
        svg_lines.append(f'    <text x="185" y="{y_pos}" class="ascii-row-txt row-{i}">')
        for cell in line_cells:
            char_val = cell["char"]
            color_val = cell["color"]
            escaped_char = char_val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace(" ", "&#160;")
            svg_lines.append(f'<tspan fill="{color_val}">{escaped_char}</tspan>')
        svg_lines.append('</text>')
        
    svg_lines.append('  </g>')

    # PHASE 4: Vertical CRT Laser Scanning Line Beam
    svg_lines.append('  <g transform="translate(14, 95)">')
    svg_lines.append('    <rect x="0" y="0" width="342" height="12" fill="url(#laserGrad)" class="laser-beam" />')
    svg_lines.append('  </g>')

    # CRT Scanline Pattern Overlay
    svg_lines.append('  <rect x="12" y="90" width="346" height="318" fill="url(#scanlines)" pointer-events="none" />')

    # PHASE 5: Finished State Status Bar & Blinking Cursor
    svg_lines.append('  <line x1="10" y1="412" x2="360" y2="412" stroke="#21262d" stroke-width="1" />')
    svg_lines.append('  <g class="footer-group" transform="translate(18, 430)">')
    svg_lines.append('    <text x="0" y="0" class="footer-txt">PORTRAIT_RENDERED <tspan class="status-online">✓</tspan></text>')
    svg_lines.append('    <text x="170" y="0" class="footer-txt">100% COMPLETE</text>')
    svg_lines.append('    <rect x="275" y="-9" width="7" height="11" class="blink-cursor" />')
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

    print(f"[INFO] Generating redesigned large ASCII portrait from: {raw_photo}")
    ascii_lines = generate_ascii_grid_from_photo(raw_photo, ascii_width=30)

    if not ascii_lines:
        print("[ERROR] ASCII conversion failed.")
        sys.exit(1)

    svg_content = generate_redesigned_animated_svg(ascii_lines)

    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"[SUCCESS] Redesigned ASCII portrait SVG generated at: {OUTPUT_SVG}")


if __name__ == "__main__":
    main()
