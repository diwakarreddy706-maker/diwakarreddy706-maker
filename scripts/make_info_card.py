#!/usr/bin/env python3
"""
make_info_card.py
Renders a neofetch-style stats & developer card (info-card.svg) matching the exact video reference:
- Top 4 Metric Boxes: Current streak, Longest streak, Total contributions, Active days & Avg/active day
- Bottom Section: Contributions / month green bar chart
- Dark terminal card aesthetic (#0d1117)
"""

import json
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "contributions.json")
OUTPUT_SVG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "info-card.svg")


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "total_contributions": 116,
        "current_streak": 1,
        "longest_streak": 5,
        "monthly_totals": {"Jan 2026": 5, "Apr 2026": 2, "Aug 2026": 8, "Sep 2026": 45, "Oct 2026": 56}
    }


def generate_info_card_svg(data):
    svg_width = 490
    svg_height = 450

    total_contribs = data.get("total_contributions", 116)
    current_streak = data.get("current_streak", 1)
    longest_streak = data.get("longest_streak", 5)
    days = data.get("days", [])

    active_days = sum(1 for d in days if d.get("count", 0) > 0) or 18
    avg_per_active = round(total_contribs / max(active_days, 1), 1)

    # Monthly totals for bottom bar chart
    monthly_totals = data.get("monthly_totals", {})
    # Take last 12 months or recent months
    recent_months = list(monthly_totals.items())[-12:] if monthly_totals else []

    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">')
    svg_lines.append('<defs>')
    svg_lines.append('<style>')
    svg_lines.append('''
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(6px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        .bg { fill: #0d1117; rx: 10px; ry: 10px; stroke: #30363d; stroke-width: 1px; }
        .dot-red { fill: #ff5f56; }
        .dot-yellow { fill: #ffbd2e; }
        .dot-green { fill: #27c93f; }
        .term-title { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 12px; fill: #8b949e; font-weight: 600; }
        
        .metric-box { fill: #161b22; rx: 6px; ry: 6px; stroke: #21262d; stroke-width: 1px; }
        .metric-icon { font-family: 'Fira Code', Consolas, monospace; font-size: 11px; fill: #3fb950; }
        .metric-lbl { font-family: 'Fira Code', Consolas, monospace; font-size: 10px; fill: #8b949e; }
        .metric-val { font-family: 'Fira Code', Consolas, monospace; font-size: 18px; fill: #f0f6fc; font-weight: bold; }
        .metric-sub { font-family: 'Fira Code', Consolas, monospace; font-size: 9px; fill: #6e7681; }
        
        .chart-lbl { font-family: 'Fira Code', Consolas, monospace; font-size: 11px; fill: #8b949e; }
        .bar-bg { fill: #161b22; rx: 2px; ry: 2px; }
        .bar-fill { fill: #26a641; rx: 2px; ry: 2px; }
        .bar-fill:hover { fill: #39d353; }
        .month-lbl { font-family: 'Fira Code', Consolas, monospace; font-size: 9px; fill: #6e7681; text-anchor: middle; }
        
        .anim-group { animation: fadeIn 0.5s ease-out forwards; opacity: 0; }
    ''')
    svg_lines.append('</style>')
    svg_lines.append('</defs>')

    # Card Background
    svg_lines.append(f'<rect width="{svg_width}" height="{svg_height}" class="bg" />')

    # Header Bar
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.1s;">')
    svg_lines.append('  <circle cx="20" cy="20" r="4.5" class="dot-red" />')
    svg_lines.append('  <circle cx="34" cy="20" r="4.5" class="dot-yellow" />')
    svg_lines.append('  <circle cx="48" cy="20" r="4.5" class="dot-green" />')
    svg_lines.append('  <text x="62" y="24" class="term-title">diwakar@github: ~/stats.asc</text>')
    svg_lines.append('</g>')

    # Window Divider Line
    svg_lines.append('<line x1="10" y1="36" x2="480" y2="36" stroke="#21262d" stroke-width="1" />')

    # TOP SECTION: 4 METRIC CARDS (Exact match to video stats.svg)
    box_w = 215
    box_h = 75

    # Box 1: Current Streak
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.15s;">')
    svg_lines.append(f'  <rect x="20" y="52" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="35" y="70" class="metric-icon">⚡ <tspan class="metric-lbl">Current streak</tspan></text>')
    svg_lines.append(f'  <text x="35" y="98" class="metric-val">{current_streak} <tspan class="metric-lbl">day</tspan></text>')
    svg_lines.append('  <text x="35" y="114" class="metric-sub">Active GitHub streak</text>')
    svg_lines.append('</g>')

    # Box 2: Longest Streak
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.2s;">')
    svg_lines.append(f'  <rect x="255" y="52" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="270" y="70" class="metric-icon">🔥 <tspan class="metric-lbl">Longest streak</tspan></text>')
    svg_lines.append(f'  <text x="270" y="98" class="metric-val">{longest_streak} <tspan class="metric-lbl">days</tspan></text>')
    svg_lines.append('  <text x="270" y="114" class="metric-sub">Max consecutive activity</text>')
    svg_lines.append('</g>')

    # Box 3: Total Contributions
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.25s;">')
    svg_lines.append(f'  <rect x="20" y="140" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="35" y="158" class="metric-icon">📊 <tspan class="metric-lbl">Contributions</tspan></text>')
    svg_lines.append(f'  <text x="35" y="186" class="metric-val">{total_contribs}</tspan></text>')
    svg_lines.append('  <text x="35" y="202" class="metric-sub">Total contributions in year</text>')
    svg_lines.append('</g>')

    # Box 4: Active Days & Avg/Active Day
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.3s;">')
    svg_lines.append(f'  <rect x="255" y="140" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="270" y="158" class="metric-icon">📈 <tspan class="metric-lbl">1 active day / avg</tspan></text>')
    svg_lines.append(f'  <text x="270" y="186" class="metric-val">{active_days} <tspan class="metric-sub">/ {avg_per_active} daily</tspan></text>')
    svg_lines.append('  <text x="270" y="202" class="metric-sub">Active coding breakdown</text>')
    svg_lines.append('</g>')

    # BOTTOM SECTION: MONTHLY CONTRIBUTION BAR CHART (Matching video)
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.35s;">')
    svg_lines.append('  <text x="20" y="245" class="chart-lbl">📊 contributions / month</text>')
    svg_lines.append('  <line x1="20" y1="255" x2="470" y2="255" stroke="#21262d" stroke-width="1" />')

    max_m_val = max([v for _, v in recent_months] + [1])
    chart_y_base = 410
    max_bar_h = 130
    bar_width = 24
    spacing = (450 - (len(recent_months) * bar_width)) / max(len(recent_months) + 1, 1)

    for idx, (mname, count) in enumerate(recent_months):
        bx = 30 + (idx * (bar_width + 12))
        fill_h = int((count / max_m_val) * max_bar_h) if max_m_val > 0 else 4
        fill_h = max(fill_h, 4)
        by = chart_y_base - fill_h
        
        # Short month display (e.g. Jan, Feb)
        m_short = mname.split()[0]
        
        svg_lines.append(f'  <rect x="{bx}" y="{chart_y_base - max_bar_h}" width="{bar_width}" height="{max_bar_h}" class="bar-bg" />')
        svg_lines.append(f'  <rect x="{bx}" y="{by}" width="{bar_width}" height="{fill_h}" class="bar-fill">'
                         f'<title>{mname}: {count} contributions</title></rect>')
        svg_lines.append(f'  <text x="{bx + (bar_width//2)}" y="{chart_y_base + 16}" class="month-lbl">{m_short}</text>')
        
    svg_lines.append('</g>')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def main():
    data = load_data()
    svg_content = generate_info_card_svg(data)
    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[SUCCESS] Info Card SVG generated at: {OUTPUT_SVG}")


if __name__ == "__main__":
    main()
