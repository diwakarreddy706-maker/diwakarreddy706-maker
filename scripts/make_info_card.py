#!/usr/bin/env python3
"""
make_info_card.py
Renders a neofetch-style stats & developer card (info-card.svg) matching the exact video reference (img2.mp4):
- Header: diwakar@github: ~$ ./stats.sh
- Top Section: 6 Metric Boxes Grid (2x3):
  1. $ current streak
  2. $ longest streak
  3. $ contributions
  4. $ active days
  5. $ best day
  6. $ avg / active day
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
        "total_contributions": 121,
        "current_streak": 1,
        "longest_streak": 5,
        "monthly_totals": {"Jan 2026": 5, "Apr 2026": 2, "Aug 2026": 8, "Sep 2026": 45, "Oct 2026": 61}
    }


def generate_info_card_svg(data):
    svg_width = 490
    svg_height = 490

    total_contribs = data.get("total_contributions", 121)
    current_streak = data.get("current_streak", 1)
    longest_streak = data.get("longest_streak", 5)
    days = data.get("days", [])

    active_days = sum(1 for d in days if d.get("count", 0) > 0) or 18
    pct_year = round((active_days / 365.0) * 100)
    avg_per_active = round(total_contribs / max(active_days, 1), 1)

    best_day_info = data.get("best_day", {"date": "Sep 28", "count": 45})
    best_count = best_day_info.get("count", 45) if isinstance(best_day_info, dict) else 45
    best_date = best_day_info.get("date", "Sep 28") if isinstance(best_day_info, dict) else "Sep 28"

    # Monthly totals for bottom bar chart
    monthly_totals = data.get("monthly_totals", {})
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
        .metric-lbl { font-family: 'Fira Code', Consolas, monospace; font-size: 10px; fill: #8b949e; }
        .metric-val-green { font-family: 'Fira Code', Consolas, monospace; font-size: 17px; fill: #3fb950; font-weight: bold; }
        .metric-val-white { font-family: 'Fira Code', Consolas, monospace; font-size: 17px; fill: #f0f6fc; font-weight: bold; }
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

    # Header Bar matching img2.mp4: avi@github: ~$ ./stats.sh
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.1s;">')
    svg_lines.append('  <circle cx="20" cy="20" r="4.5" class="dot-red" />')
    svg_lines.append('  <circle cx="34" cy="20" r="4.5" class="dot-yellow" />')
    svg_lines.append('  <circle cx="48" cy="20" r="4.5" class="dot-green" />')
    svg_lines.append('  <text x="62" y="24" class="term-title">diwakar@github: ~$ ./stats.sh</text>')
    svg_lines.append('</g>')

    # Window Divider Line
    svg_lines.append('<line x1="10" y1="36" x2="480" y2="36" stroke="#21262d" stroke-width="1" />')

    # TOP SECTION: 6 METRIC CARDS GRID (Exact 2x3 grid matching img2.mp4)
    box_w = 215
    box_h = 58

    # Row 1: Box 1 (Current Streak) & Box 2 (Longest Streak)
    # Box 1: Current Streak
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.15s;">')
    svg_lines.append(f'  <rect x="20" y="48" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="32" y="64" class="metric-lbl">$ current streak</text>')
    svg_lines.append(f'  <text x="32" y="84" class="metric-val-green">{current_streak} <tspan class="metric-lbl">days</tspan></text>')
    svg_lines.append('  <text x="32" y="97" class="metric-sub">Oct 8</text>')
    svg_lines.append('</g>')

    # Box 2: Longest Streak
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.2s;">')
    svg_lines.append(f'  <rect x="255" y="48" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="267" y="64" class="metric-lbl">$ longest streak</text>')
    svg_lines.append(f'  <text x="267" y="84" class="metric-val-white">{longest_streak} <tspan class="metric-lbl">days</tspan></text>')
    svg_lines.append('  <text x="267" y="97" class="metric-sub">Sep 28 - Oct 2</text>')
    svg_lines.append('</g>')

    # Row 2: Box 3 (Contributions) & Box 4 (Active Days)
    # Box 3: Total Contributions
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.25s;">')
    svg_lines.append(f'  <rect x="20" y="114" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="32" y="130" class="metric-lbl">$ contributions</text>')
    svg_lines.append(f'  <text x="32" y="150" class="metric-val-white">{total_contribs}</text>')
    svg_lines.append('  <text x="32" y="163" class="metric-sub">in the last year</text>')
    svg_lines.append('</g>')

    # Box 4: Active Days
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.3s;">')
    svg_lines.append(f'  <rect x="255" y="114" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="267" y="130" class="metric-lbl">$ active days</text>')
    svg_lines.append(f'  <text x="267" y="150" class="metric-val-white">{active_days} <tspan class="metric-sub">/ 365</tspan></text>')
    svg_lines.append(f'  <text x="267" y="163" class="metric-sub">{pct_year}% of the year</text>')
    svg_lines.append('</g>')

    # Row 3: Box 5 (Best Day) & Box 6 (Avg / Active Day)
    # Box 5: Best Day
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.35s;">')
    svg_lines.append(f'  <rect x="20" y="180" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="32" y="196" class="metric-lbl">$ best day</text>')
    svg_lines.append(f'  <text x="32" y="216" class="metric-val-white">{best_count}</text>')
    svg_lines.append(f'  <text x="32" y="229" class="metric-sub">{best_date}</text>')
    svg_lines.append('</g>')

    # Box 6: Avg / Active Day
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.4s;">')
    svg_lines.append(f'  <rect x="255" y="180" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="267" y="196" class="metric-lbl">$ avg / active day</text>')
    svg_lines.append(f'  <text x="267" y="216" class="metric-val-white">{avg_per_active}</text>')
    svg_lines.append('  <text x="267" y="229" class="metric-sub">contributions</text>')
    svg_lines.append('</g>')

    # BOTTOM SECTION: MONTHLY CONTRIBUTION BAR CHART (Matching img2.mp4)
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.45s;">')
    svg_lines.append('  <text x="20" y="260" class="chart-lbl">📊 contributions / month</text>')
    svg_lines.append('  <line x1="20" y1="268" x2="470" y2="268" stroke="#21262d" stroke-width="1" />')

    max_m_val = max([v for _, v in recent_months] + [1])
    chart_y_base = 450
    max_bar_h = 150
    bar_width = 24

    for idx, (mname, count) in enumerate(recent_months):
        bx = 30 + (idx * (bar_width + 12))
        fill_h = int((count / max_m_val) * max_bar_h) if max_m_val > 0 else 4
        fill_h = max(fill_h, 4)
        by = chart_y_base - fill_h
        
        # Month letter/short (e.g. O, N, D, J, F, M, A, M, J, J, A, S, O)
        m_short = mname.split()[0][0]
        
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
