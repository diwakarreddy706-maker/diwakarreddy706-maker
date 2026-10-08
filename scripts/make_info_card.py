#!/usr/bin/env python3
"""
make_info_card.py
Generates a modern neofetch-style terminal developer info card as an SVG (info-card.svg).
Supports STATIC=1 environment variable or --static flag to generate a non-animated version.
"""

import argparse
import os
import sys

OUTPUT_SVG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "info-card.svg")


def xml_escape(text):
    if not isinstance(text, str):
        return text
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# Easily editable developer profile information
PROFILE_INFO = {
    "username": "diwakarrreddy706-maker",
    "role": "Frontend Developer / UI/UX Developer",
    "focus": "Frontend Development, UI/UX and Web Projects",
    "technologies": ["HTML", "CSS", "JavaScript", "Java", "SQL", "Figma"],
    "projects": ["EduNova", "SentinelJob AI", "CRS Online Services"],
    "os_info": "GitHub Profile / Web Stack v2.4",
    "uptime": "Active & Ready for Collaborations",
    "shell": "zsh 5.9 (x86_64-apple-darwin22.0)"
}


def generate_info_card_svg(info, is_static=False):
    svg_width = 490
    svg_height = 450

    # Key-value rows to render in terminal card
    rows = [
        ("OS", info["os_info"], "#79c0ff"),
        ("Host", info["username"], "#7ee787"),
        ("Role", info["role"], "#ffa657"),
        ("Focus", info["focus"], "#d2a8ff"),
        ("Tech Stack", ", ".join(info["technologies"]), "#ff7b72"),
        ("Projects", ", ".join(info["projects"]), "#a5d6ff"),
        ("Status", info["uptime"], "#56d364")
    ]

    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">')
    svg_lines.append('<defs>')
    svg_lines.append('<style>')

    if not is_static:
        svg_lines.append('''
            @keyframes rowSlide {
                0% { opacity: 0; transform: translateX(-10px); }
                100% { opacity: 1; transform: translateX(0); }
            }
            @keyframes headerSlide {
                0% { opacity: 0; transform: translateY(-6px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            .anim-header { animation: headerSlide 0.4s ease-out forwards; opacity: 0; }
            .anim-row { animation: rowSlide 0.35s ease-out forwards; opacity: 0; }
        ''')
    else:
        svg_lines.append('''
            .anim-header { opacity: 1; }
            .anim-row { opacity: 1; }
        ''')

    svg_lines.append('''
        .bg { fill: #0d1117; rx: 10px; ry: 10px; stroke: #30363d; stroke-width: 1px; }
        .dot-red { fill: #ff5f56; }
        .dot-yellow { fill: #ffbd2e; }
        .dot-green { fill: #27c93f; }
        .term-title { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 12px; fill: #8b949e; font-weight: 600; }
        .prompt-user { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 14px; fill: #58a6ff; font-weight: bold; }
        .prompt-at { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 14px; fill: #8b949e; }
        .prompt-host { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 14px; fill: #3fb950; font-weight: bold; }
        .divider { stroke: #30363d; stroke-width: 1px; stroke-dasharray: 4; }
        .key-label { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 12px; fill: #8b949e; font-weight: 600; }
        .key-bullet { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 12px; fill: #58a6ff; font-weight: bold; }
        .val-text { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 12px; font-weight: 500; }
    ''')
    svg_lines.append('</style>')
    svg_lines.append('</defs>')

    # Card background
    svg_lines.append(f'<rect width="{svg_width}" height="{svg_height}" class="bg" />')

    # Top Window Control Bar
    svg_lines.append('<g class="anim-header" style="animation-delay: 0.05s;">')
    svg_lines.append('  <circle cx="20" cy="22" r="5" class="dot-red" />')
    svg_lines.append('  <circle cx="35" cy="22" r="5" class="dot-yellow" />')
    svg_lines.append('  <circle cx="50" cy="22" r="5" class="dot-green" />')
    svg_lines.append('  <text x="65" y="26" class="term-title">diwakarr@github: ~/neofetch</text>')
    svg_lines.append('</g>')

    # Window Divider Line
    svg_lines.append('<line x1="12" y1="38" x2="478" y2="38" stroke="#21262d" stroke-width="1" />')

    # User Header Prompt
    svg_lines.append('<g class="anim-header" style="animation-delay: 0.1s;">')
    svg_lines.append(f'  <text x="24" y="66">')
    svg_lines.append(f'    <tspan class="prompt-user">{info["username"]}</tspan>')
    svg_lines.append(f'    <tspan class="prompt-at">@</tspan>')
    svg_lines.append(f'    <tspan class="prompt-host">github</tspan>')
    svg_lines.append(f'  </text>')
    svg_lines.append('  <line x1="24" y1="78" x2="466" y2="78" class="divider" />')
    svg_lines.append('</g>')

    # Key / Value Rows
    start_y = 108
    row_gap = 36
    
    for idx, (label, val, color) in enumerate(rows):
        y_pos = start_y + (idx * row_gap)
        delay = round(0.15 + (idx * 0.06), 3)
        style_attr = f'style="animation-delay: {delay}s;"' if not is_static else ''
        
        escaped_label = xml_escape(label)
        escaped_val = xml_escape(val)

        # Word wrap check if text is long
        svg_lines.append(f'<g class="anim-row" {style_attr}>')
        svg_lines.append(f'  <text x="24" y="{y_pos}">')
        svg_lines.append(f'    <tspan class="key-bullet">❯ </tspan>')
        svg_lines.append(f'    <tspan class="key-label">{escaped_label:<10}</tspan>')
        svg_lines.append(f'    <tspan class="prompt-at">: </tspan>')
        
        # If value is long (e.g. Focus or Tech), break into multiline if needed
        if len(val) > 34:
            words = val.split(" ")
            line1, line2 = "", ""
            for w in words:
                if len(line1 + " " + w) <= 32:
                    line1 += (" " if line1 else "") + w
                else:
                    line2 += (" " if line2 else "") + w
            svg_lines.append(f'    <tspan class="val-text" fill="{color}">{xml_escape(line1)}</tspan>')
            svg_lines.append(f'  </text>')
            if line2:
                svg_lines.append(f'  <text x="145" y="{y_pos + 16}">')
                svg_lines.append(f'    <tspan class="val-text" fill="{color}">{xml_escape(line2)}</tspan>')
                svg_lines.append(f'  </text>')
        else:
            svg_lines.append(f'    <tspan class="val-text" fill="{color}">{escaped_val}</tspan>')
            svg_lines.append(f'  </text>')
            
        svg_lines.append('</g>')

    # Color Palette Blocks at Card Bottom (Classic Neofetch block display)
    palette_y = 398
    palette_delay = round(0.15 + (len(rows) * 0.06), 3)
    style_attr = f'style="animation-delay: {palette_delay}s;"' if not is_static else ''
    
    colors_list = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4"]
    
    svg_lines.append(f'<g class="anim-row" {style_attr}>')
    svg_lines.append(f'  <line x1="24" y1="{palette_y - 20}" x2="466" y2="{palette_y - 20}" class="divider" />')
    for c_idx, hex_color in enumerate(colors_list):
        bx = 24 + (c_idx * 26)
        svg_lines.append(f'  <rect x="{bx}" y="{palette_y}" width="20" height="12" rx="3" fill="{hex_color}" />')
    for c_idx, hex_color in enumerate(colors_list):
        bx = 24 + (c_idx * 26)
        svg_lines.append(f'  <rect x="{bx}" y="{palette_y + 16}" width="20" height="12" rx="3" fill="{hex_color}" opacity="0.6" />')
    svg_lines.append('</g>')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def main():
    parser = argparse.ArgumentParser(description="Generate neofetch developer info card SVG.")
    parser.add_argument("--static", action="store_true", help="Generate static SVG without animations")
    args = parser.parse_args()

    # Also check STATIC environment variable
    is_static = args.static or (os.environ.get("STATIC", "").strip() == "1")

    svg_content = generate_info_card_svg(PROFILE_INFO, is_static=is_static)

    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)

    mode_text = "STATIC (non-animated)" if is_static else "ANIMATED"
    print(f"[SUCCESS] Developer Info Card SVG ({mode_text}) generated at: {OUTPUT_SVG}")


if __name__ == "__main__":
    main()
