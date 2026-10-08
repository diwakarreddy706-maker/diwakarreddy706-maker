#!/usr/bin/env python3
"""
render_heatmap_svg.py
Reads data/contributions.json and generates an animated SVG heatmap contrib-heatmap.svg
in the repository root directory.
"""

import datetime
import json
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "contributions.json")
OUTPUT_SVG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "contrib-heatmap.svg")

# GitHub dark theme level colors
LEVEL_COLORS = {
    0: "#161b22",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353"
}

DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_contributions_data(data_path):
    if not os.path.exists(data_path):
        print(f"[WARNING] Data file {data_path} not found. Generating default data structure...")
        today = datetime.date.today()
        days = []
        curr = today - datetime.timedelta(days=364)
        while curr <= today:
            days.append({"date": curr.strftime("%Y-%m-%d"), "count": 0, "level": 0})
            curr += datetime.timedelta(days=1)
        return {
            "username": "diwakarrreddy706-maker",
            "total_contributions": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "best_day": {"date": "-", "count": 0},
            "days": days
        }

    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_svg(data):
    days = data.get("days", [])
    total_contribs = data.get("total_contributions", 0)
    current_streak = data.get("current_streak", 0)
    longest_streak = data.get("longest_streak", 0)
    best_day_info = data.get("best_day", {"date": "-", "count": 0})
    best_count = best_day_info.get("count", 0) if isinstance(best_day_info, dict) else 0

    # Build 53 columns grid
    # Organize days by week (Sunday start or day index)
    if days:
        first_date = datetime.datetime.strptime(days[0]["date"], "%Y-%m-%d").date()
    else:
        first_date = datetime.date.today() - datetime.timedelta(days=364)

    # Offset to first Sunday
    first_dow = (first_date.weekday() + 1) % 7  # 0=Sunday, 1=Monday...
    
    # Map dates to objects
    date_map = {d["date"]: d for d in days}
    
    # SVG layout settings
    svg_width = 860
    svg_height = 215
    start_x = 42
    start_y = 68
    box_size = 11
    box_gap = 3
    step = box_size + box_gap # 14px

    # Calculate grid of 53 weeks x 7 days
    weeks_rects = []
    month_labels = []
    last_month = None

    curr_date = first_date - datetime.timedelta(days=first_dow)
    
    for w in range(53):
        col_x = start_x + (w * step)
        
        # Check month label for this week
        mid_week_date = curr_date + datetime.timedelta(days=3)
        m_name = mid_week_date.strftime("%b")
        if m_name != last_month:
            month_labels.append((col_x, m_name))
            last_month = m_name

        for d in range(7):
            date_str = curr_date.strftime("%Y-%m-%d")
            day_info = date_map.get(date_str, {"count": 0, "level": 0})
            level = day_info.get("level", 0)
            count = day_info.get("count", 0)
            color = LEVEL_COLORS.get(level, LEVEL_COLORS[0])
            
            row_y = start_y + (d * step)
            delay = round((w * 0.015) + (d * 0.035) + 0.15, 3)
            
            title_text = f"{date_str}: {count} contribution{'s' if count != 1 else ''}"
            weeks_rects.append({
                "x": col_x,
                "y": row_y,
                "color": color,
                "delay": delay,
                "title": title_text,
                "date": date_str,
                "count": count
            })
            
            curr_date += datetime.timedelta(days=1)

    # Filter month labels to avoid crowding (minimum spacing 32px)
    filtered_month_labels = []
    prev_x = -100
    for mx, mname in month_labels:
        if mx - prev_x >= 32 and mx <= start_x + (52 * step) - 10:
            filtered_month_labels.append((mx, mname))
            prev_x = mx

    # Generate SVG Content
    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">')
    svg_lines.append('<defs>')
    svg_lines.append('<style>')
    svg_lines.append('''
        @keyframes boxFade {
            0% { opacity: 0; transform: scale(0.2); }
            70% { opacity: 1; transform: scale(1.15); }
            100% { opacity: 1; transform: scale(1); }
        }
        @keyframes headerFade {
            0% { opacity: 0; transform: translateY(-5px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        .bg { fill: #0d1117; rx: 10px; ry: 10px; stroke: #30363d; stroke-width: 1px; }
        .terminal-header { animation: headerFade 0.5s ease-out forwards; }
        .dot-red { fill: #ff5f56; }
        .dot-yellow { fill: #ffbd2e; }
        .dot-green { fill: #27c93f; }
        .term-title { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 13px; fill: #8b949e; font-weight: 600; }
        .stat-label { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 11px; fill: #8b949e; }
        .stat-val { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 11px; fill: #3fb950; font-weight: bold; }
        .axis-label { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 10px; fill: #6e7681; }
        .day-box {
            animation: boxFade 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            opacity: 0;
            transform-box: fill-box;
            transform-origin: center;
        }
        .day-box:hover {
            stroke: #58a6ff;
            stroke-width: 1px;
            cursor: pointer;
        }
        .legend-text { font-family: 'Fira Code', Consolas, 'Courier New', monospace; font-size: 10px; fill: #6e7681; }
    ''')
    svg_lines.append('</style>')
    svg_lines.append('</defs>')

    # Background Card
    svg_lines.append(f'<rect width="{svg_width}" height="{svg_height}" class="bg" />')

    # Terminal Top Bar
    svg_lines.append('<g class="terminal-header">')
    svg_lines.append('  <circle cx="24" cy="24" r="5" class="dot-red" />')
    svg_lines.append('  <circle cx="39" cy="24" r="5" class="dot-yellow" />')
    svg_lines.append('  <circle cx="54" cy="24" r="5" class="dot-green" />')
    svg_lines.append('  <text x="70" y="28" class="term-title">diwakarr@github:~ $ ./contributions.sh</text>')
    
    # Stats Badges on Header Right
    stats_x = 440
    svg_lines.append(f'  <text x="{stats_x}" y="28" class="stat-label">Contributions: <tspan class="stat-val">{total_contribs}</tspan></text>')
    svg_lines.append(f'  <text x="{stats_x + 130}" y="28" class="stat-label">Streak: <tspan class="stat-val">{current_streak}d</tspan></text>')
    svg_lines.append(f'  <text x="{stats_x + 220}" y="28" class="stat-label">Max Streak: <tspan class="stat-val">{longest_streak}d</tspan></text>')
    svg_lines.append(f'  <text x="{stats_x + 330}" y="28" class="stat-label">Best: <tspan class="stat-val">{best_count}</tspan></text>')
    svg_lines.append('</g>')

    # Terminal Divider Line
    svg_lines.append('<line x1="15" y1="42" x2="845" y2="42" stroke="#21262d" stroke-width="1" />')

    # Month Labels
    for mx, mname in filtered_month_labels:
        svg_lines.append(f'<text x="{mx}" y="58" class="axis-label">{mname}</text>')

    # Day Labels (Mon, Wed, Fri)
    svg_lines.append(f'<text x="18" y="{start_y + (1 * step) + 9}" class="axis-label">Mon</text>')
    svg_lines.append(f'<text x="18" y="{start_y + (3 * step) + 9}" class="axis-label">Wed</text>')
    svg_lines.append(f'<text x="18" y="{start_y + (5 * step) + 9}" class="axis-label">Fri</text>')

    # Days Heatmap Boxes
    svg_lines.append('<g>')
    for box in weeks_rects:
        svg_lines.append(
            f'  <rect x="{box["x"]}" y="{box["y"]}" width="{box_size}" height="{box_size}" rx="2" ry="2" '
            f'fill="{box["color"]}" class="day-box" style="animation-delay: {box["delay"]}s;">'
            f'<title>{box["title"]}</title></rect>'
        )
    svg_lines.append('</g>')

    # Legend at Bottom Right
    leg_y = start_y + (7 * step) + 16
    leg_x = 710
    svg_lines.append(f'<text x="{leg_x}" y="{leg_y + 9}" class="legend-text">Less</text>')
    for idx, lvl in enumerate(range(5)):
        bx = leg_x + 30 + (idx * 14)
        svg_lines.append(f'<rect x="{bx}" y="{leg_y}" width="11" height="11" rx="2" ry="2" fill="{LEVEL_COLORS[lvl]}" />')
    svg_lines.append(f'<text x="{leg_x + 105}" y="{leg_y + 9}" class="legend-text">More</text>')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def main():
    data = load_contributions_data(DATA_FILE)
    svg_content = render_svg(data)
    
    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    print(f"[SUCCESS] Heatmap SVG generated successfully at: {OUTPUT_SVG}")


if __name__ == "__main__":
    main()
