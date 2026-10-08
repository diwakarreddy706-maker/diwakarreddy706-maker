#!/usr/bin/env python3
"""
generate.py
Fetches live GitHub contribution data for user diwakarreddy706-maker via GraphQL API (or HTML scraping fallback)
and generates:
1. contrib-heatmap.svg (860px width contribution calendar)
2. stats.svg / info-card.svg (490px width stats card with 6 metric boxes + monthly bar chart)
"""

import datetime
import json
import os
import re
import sys
import urllib.request
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "contributions.json")

HEATMAP_SVG = os.path.join(BASE_DIR, "contrib-heatmap.svg")
STATS_SVG = os.path.join(BASE_DIR, "stats.svg")
INFO_CARD_SVG = os.path.join(BASE_DIR, "info-card.svg")

USERNAME = "diwakarreddy706-maker"

# GitHub dark theme level colors
LEVEL_COLORS = {
    0: "#161b22",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353",
    5: "#69f0a0"
}


def fetch_contributions_graphql(username, token):
    url = "https://api.github.com/graphql"
    query = """
    query($user: String!) {
      user(login: $user) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                color
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"user": username}}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "GitHub-Profile-Generator"
    }
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
            total_contribs = cal["totalContributions"]
            days = []
            for week in cal["weeks"]:
                for day in week["contributionDays"]:
                    count = day["contributionCount"]
                    if count == 0:
                        level = 0
                    elif count <= 2:
                        level = 1
                    elif count <= 5:
                        level = 2
                    elif count <= 10:
                        level = 3
                    elif count <= 20:
                        level = 4
                    else:
                        level = 5
                    days.append({"date": day["date"], "count": count, "level": level})
            return process_contribution_days(username, total_contribs, days)
    except Exception as e:
        print(f"[WARNING] GraphQL API fetch failed: {e}. Falling back to HTML scraping...")
        return None


def fetch_contributions_scraping(username):
    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html",
        "X-Requested-With": "XMLHttpRequest"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode("utf-8")

        soup = BeautifulSoup(html, "html.parser")
        tooltips = {}
        for tt in soup.find_all("tool-tip"):
            for_id = tt.get("for")
            if for_id:
                tooltips[for_id] = tt.get_text(strip=True)

        day_elements = soup.find_all(["td", "rect"], class_=lambda c: c and "ContributionCalendar-day" in c)
        parsed_days = []
        for el in day_elements:
            date_str = el.get("data-date")
            if not date_str:
                continue

            level = int(el.get("data-level", 0))
            el_id = el.get("id")
            text = tooltips.get(el_id, "") or el.get_text(strip=True) or el.get("aria-label", "")
            count = 0
            if text:
                match = re.search(r"(\d+)\s+contribution", text)
                if match:
                    count = int(match.group(1))

            parsed_days.append({"date": date_str, "count": count, "level": level})

        parsed_days.sort(key=lambda x: x["date"])
        total_contribs = sum(d["count"] for d in parsed_days)
        return process_contribution_days(username, total_contribs, parsed_days)
    except Exception as e:
        print(f"[ERROR] Scraping contributions failed: {e}")
        return None


def process_contribution_days(username, total_contribs, days_data):
    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    best_day = {"date": "-", "count": 0}
    monthly_totals = {}

    for day in days_data:
        c = day["count"]
        d_str = day["date"]

        if c > best_day["count"]:
            best_day = {"date": d_str, "count": c}

        try:
            m_dt = datetime.datetime.strptime(d_str, "%Y-%m-%d")
            m_key = m_dt.strftime("%b %Y")
            monthly_totals[m_key] = monthly_totals.get(m_key, 0) + c
        except Exception:
            pass

        if c > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0

    # Current streak calculation ending today/yesterday
    rev_days = sorted(days_data, key=lambda x: x["date"], reverse=True)
    c_streak = 0
    counting = False
    for i, day in enumerate(rev_days):
        if i == 0 and day["count"] == 0 and len(rev_days) > 1 and rev_days[1]["count"] > 0:
            continue
        if day["count"] > 0:
            c_streak += 1
        else:
            if c_streak > 0:
                break
    current_streak = max(c_streak, 1 if days_data and days_data[-1]["count"] > 0 else 0)

    result = {
        "username": username,
        "total_contributions": total_contribs,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": monthly_totals,
        "days": days_data
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def generate_heatmap_svg(data):
    days = data.get("days", [])
    total_contribs = data.get("total_contributions", 127)
    current_streak = data.get("current_streak", 1)
    longest_streak = data.get("longest_streak", 5)

    if days:
        first_date = datetime.datetime.strptime(days[0]["date"], "%Y-%m-%d").date()
    else:
        first_date = datetime.date.today() - datetime.timedelta(days=364)

    first_dow = (first_date.weekday() + 1) % 7
    date_map = {d["date"]: d for d in days}

    svg_width = 860
    svg_height = 215
    start_x = 42
    start_y = 68
    box_size = 11
    box_gap = 3
    step = box_size + box_gap

    weeks_rects = []
    month_labels = []
    last_month = None

    curr_date = first_date - datetime.timedelta(days=first_dow)

    for w in range(53):
        col_x = start_x + (w * step)
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
                "x": col_x, "y": row_y, "color": color, "delay": delay, "title": title_text
            })
            curr_date += datetime.timedelta(days=1)

    filtered_month_labels = []
    prev_x = -100
    for mx, mname in month_labels:
        if mx - prev_x >= 32 and mx <= start_x + (52 * step) - 10:
            filtered_month_labels.append((mx, mname))
            prev_x = mx

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
        .bg { fill: #0d1117; rx: 10px; ry: 10px; stroke: #30363d; stroke-width: 1px; }
        .dot-red { fill: #ff5f56; }
        .dot-yellow { fill: #ffbd2e; }
        .dot-green { fill: #27c93f; }
        .term-title { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; fill: #8b949e; font-weight: 600; }
        .stat-label { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11px; fill: #8b949e; }
        .stat-val { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11px; fill: #3fb950; font-weight: bold; }
        .axis-label { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 10px; fill: #6e7681; }
        .day-box {
            animation: boxFade 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            opacity: 0;
            transform-box: fill-box;
            transform-origin: center;
        }
        .day-box:hover { stroke: #58a6ff; stroke-width: 1px; cursor: pointer; }
        .legend-text { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 10px; fill: #6e7681; }
    ''')
    svg_lines.append('</style>')
    svg_lines.append('</defs>')

    svg_lines.append(f'<rect width="{svg_width}" height="{svg_height}" class="bg" />')

    # Header Bar
    svg_lines.append('<g>')
    svg_lines.append('  <circle cx="24" cy="24" r="5" class="dot-red" />')
    svg_lines.append('  <circle cx="39" cy="24" r="5" class="dot-yellow" />')
    svg_lines.append('  <circle cx="54" cy="24" r="5" class="dot-green" />')
    svg_lines.append('  <text x="70" y="28" class="term-title">diwakar@github:~ $ ./contributions.sh</text>')
    
    stats_x = 440
    svg_lines.append(f'  <text x="{stats_x}" y="28" class="stat-label">Contributions: <tspan class="stat-val">{total_contribs}</tspan></text>')
    svg_lines.append(f'  <text x="{stats_x + 130}" y="28" class="stat-label">Streak: <tspan class="stat-val">{current_streak}d</tspan></text>')
    svg_lines.append(f'  <text x="{stats_x + 220}" y="28" class="stat-label">Max Streak: <tspan class="stat-val">{longest_streak}d</tspan></text>')
    svg_lines.append('</g>')

    svg_lines.append('<line x1="15" y1="42" x2="845" y2="42" stroke="#21262d" stroke-width="1" />')

    for mx, mname in filtered_month_labels:
        svg_lines.append(f'<text x="{mx}" y="58" class="axis-label">{mname}</text>')

    svg_lines.append(f'<text x="18" y="{start_y + (1 * step) + 9}" class="axis-label">Mon</text>')
    svg_lines.append(f'<text x="18" y="{start_y + (3 * step) + 9}" class="axis-label">Wed</text>')
    svg_lines.append(f'<text x="18" y="{start_y + (5 * step) + 9}" class="axis-label">Fri</text>')

    svg_lines.append('<g>')
    for box in weeks_rects:
        svg_lines.append(
            f'  <rect x="{box["x"]}" y="{box["y"]}" width="{box_size}" height="{box_size}" rx="2" ry="2" '
            f'fill="{box["color"]}" class="day-box" style="animation-delay: {box["delay"]}s;">'
            f'<title>{box["title"]}</title></rect>'
        )
    svg_lines.append('</g>')

    leg_y = start_y + (7 * step) + 16
    leg_x = 710

    # Subtitle matching prompt: "N contributions in the last year"
    svg_lines.append(f'<text x="42" y="{leg_y + 9}" style="font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; font-weight: bold; fill: #e6edf3;">{total_contribs} contributions in the last year</text>')

    svg_lines.append(f'<text x="{leg_x}" y="{leg_y + 9}" class="legend-text">Less</text>')
    for idx, lvl in enumerate(range(5)):
        bx = leg_x + 30 + (idx * 14)
        svg_lines.append(f'<rect x="{bx}" y="{leg_y}" width="11" height="11" rx="2" ry="2" fill="{LEVEL_COLORS[lvl]}" />')
    svg_lines.append(f'<text x="{leg_x + 105}" y="{leg_y + 9}" class="legend-text">More</text>')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def generate_stats_svg(data):
    svg_width = 490
    svg_height = 490

    total_contribs = data.get("total_contributions", 127)
    current_streak = data.get("current_streak", 1)
    longest_streak = data.get("longest_streak", 5)
    days = data.get("days", [])

    active_days = sum(1 for d in days if d.get("count", 0) > 0) or 18
    pct_year = round((active_days / 365.0) * 100)
    avg_per_active = round(total_contribs / max(active_days, 1), 1)

    best_day_info = data.get("best_day", {"date": "Sep 28", "count": 45})
    best_count = best_day_info.get("count", 45) if isinstance(best_day_info, dict) else 45
    best_date = best_day_info.get("date", "Sep 28") if isinstance(best_day_info, dict) else "Sep 28"

    monthly_totals = data.get("monthly_totals", {})
    recent_months = list(monthly_totals.items())[-12:] if monthly_totals else []

    peak_month = "-"
    peak_val = -1
    for mname, count in recent_months:
        if count > peak_val:
            peak_val = count
            peak_month = mname.split()[0]

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
        .term-title { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; fill: #8b949e; font-weight: 600; }
        
        .metric-box { fill: #161b22; rx: 6px; ry: 6px; stroke: #21262d; stroke-width: 1px; }
        .metric-lbl { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 10px; fill: #8b949e; }
        .metric-val-green { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 17px; fill: #3fb950; font-weight: bold; }
        .metric-val-white { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 17px; fill: #e6edf3; font-weight: bold; }
        .metric-sub { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 9px; fill: #6e7681; }
        
        .chart-lbl { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11px; fill: #8b949e; }
        .peak-lbl { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 10px; fill: #3fb950; font-weight: bold; }
        .bar-bg { fill: #161b22; rx: 2px; ry: 2px; }
        .bar-fill { fill: #26a641; rx: 2px; ry: 2px; }
        .bar-fill-peak { fill: #39d353; rx: 2px; ry: 2px; }
        .bar-fill:hover { fill: #39d353; }
        .month-lbl { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 9px; fill: #6e7681; text-anchor: middle; }
        
        .anim-group { animation: fadeIn 0.5s ease-out forwards; opacity: 0; }
    ''')
    svg_lines.append('</style>')
    svg_lines.append('</defs>')

    svg_lines.append(f'<rect width="{svg_width}" height="{svg_height}" class="bg" />')

    # Header Bar: diwakar@github: ~/stats.sh
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.1s;">')
    svg_lines.append('  <circle cx="20" cy="20" r="4.5" class="dot-red" />')
    svg_lines.append('  <circle cx="34" cy="20" r="4.5" class="dot-yellow" />')
    svg_lines.append('  <circle cx="48" cy="20" r="4.5" class="dot-green" />')
    svg_lines.append('  <text x="62" y="24" class="term-title">diwakar@github: ~/stats.sh</text>')
    svg_lines.append('</g>')

    svg_lines.append('<line x1="10" y1="36" x2="480" y2="36" stroke="#21262d" stroke-width="1" />')

    box_w = 215
    box_h = 58

    # Row 1: Current Streak & Longest Streak
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.15s;">')
    svg_lines.append(f'  <rect x="20" y="48" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="32" y="64" class="metric-lbl">$ current streak</text>')
    svg_lines.append(f'  <text x="32" y="84" class="metric-val-green">{current_streak} <tspan class="metric-lbl">days</tspan></text>')
    svg_lines.append('  <text x="32" y="97" class="metric-sub">Active GitHub streak</text>')
    svg_lines.append('</g>')

    svg_lines.append('<g class="anim-group" style="animation-delay: 0.2s;">')
    svg_lines.append(f'  <rect x="255" y="48" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="267" y="64" class="metric-lbl">$ longest streak</text>')
    svg_lines.append(f'  <text x="267" y="84" class="metric-val-white">{longest_streak} <tspan class="metric-lbl">days</tspan></text>')
    svg_lines.append('  <text x="267" y="97" class="metric-sub">Max consecutive streak</text>')
    svg_lines.append('</g>')

    # Row 2: Contributions & Active Days
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.25s;">')
    svg_lines.append(f'  <rect x="20" y="114" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="32" y="130" class="metric-lbl">$ contributions</text>')
    svg_lines.append(f'  <text x="32" y="150" class="metric-val-white">{total_contribs}</text>')
    svg_lines.append('  <text x="32" y="163" class="metric-sub">in the last year</text>')
    svg_lines.append('</g>')

    svg_lines.append('<g class="anim-group" style="animation-delay: 0.3s;">')
    svg_lines.append(f'  <rect x="255" y="114" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="267" y="130" class="metric-lbl">$ active days</text>')
    svg_lines.append(f'  <text x="267" y="150" class="metric-val-white">{active_days} <tspan class="metric-sub">/ 365</tspan></text>')
    svg_lines.append(f'  <text x="267" y="163" class="metric-sub">{pct_year}% of the year</text>')
    svg_lines.append('</g>')

    # Row 3: Best Day & Avg / Active Day
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.35s;">')
    svg_lines.append(f'  <rect x="20" y="180" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="32" y="196" class="metric-lbl">$ best day</text>')
    svg_lines.append(f'  <text x="32" y="216" class="metric-val-white">{best_count}</text>')
    svg_lines.append(f'  <text x="32" y="229" class="metric-sub">{best_date}</text>')
    svg_lines.append('</g>')

    svg_lines.append('<g class="anim-group" style="animation-delay: 0.4s;">')
    svg_lines.append(f'  <rect x="255" y="180" width="{box_w}" height="{box_h}" class="metric-box" />')
    svg_lines.append('  <text x="267" y="196" class="metric-lbl">$ avg / active day</text>')
    svg_lines.append(f'  <text x="267" y="216" class="metric-val-white">{avg_per_active}</text>')
    svg_lines.append('  <text x="267" y="229" class="metric-sub">contributions</text>')
    svg_lines.append('</g>')

    # BOTTOM SECTION: MONTHLY CONTRIBUTION BAR CHART WITH PEAK MONTH
    svg_lines.append('<g class="anim-group" style="animation-delay: 0.45s;">')
    svg_lines.append('  <text x="20" y="260" class="chart-lbl">📊 contributions / month</text>')
    svg_lines.append(f'  <text x="340" y="260" class="peak-lbl">Peak: {peak_month} ({peak_val})</text>')
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

        m_short = mname.split()[0][0]
        is_peak = (count == peak_val and count > 0)
        bar_class = "bar-fill-peak" if is_peak else "bar-fill"

        svg_lines.append(f'  <rect x="{bx}" y="{chart_y_base - max_bar_h}" width="{bar_width}" height="{max_bar_h}" class="bar-bg" />')
        svg_lines.append(f'  <rect x="{bx}" y="{by}" width="{bar_width}" height="{fill_h}" class="{bar_class}">'
                         f'<title>{mname}: {count} contributions</title></rect>')
        svg_lines.append(f'  <text x="{bx + (bar_width//2)}" y="{chart_y_base + 16}" class="month-lbl">{m_short}</text>')

    svg_lines.append('</g>')
    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def main():
    token = os.environ.get("GITHUB_TOKEN")
    data = None

    if token:
        print(f"[INFO] Fetching contributions for {USERNAME} via GraphQL API...")
        data = fetch_contributions_graphql(USERNAME, token)

    if not data:
        print(f"[INFO] Fetching contributions for {USERNAME} via Web Scraping...")
        data = fetch_contributions_scraping(USERNAME)

    if not data and os.path.exists(DATA_FILE):
        print("[INFO] Loading cached contributions data...")
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    if not data:
        print("[ERROR] Failed to fetch or load contribution data.")
        sys.exit(1)

    print(f"[SUCCESS] Total Contributions: {data['total_contributions']} | Streak: {data['current_streak']}d | Longest: {data['longest_streak']}d")

    heatmap_content = generate_heatmap_svg(data)
    with open(HEATMAP_SVG, "w", encoding="utf-8") as f:
        f.write(heatmap_content)
    print(f"[SUCCESS] Heatmap SVG written to: {HEATMAP_SVG}")

    stats_content = generate_stats_svg(data)
    with open(STATS_SVG, "w", encoding="utf-8") as f:
        f.write(stats_content)
    with open(INFO_CARD_SVG, "w", encoding="utf-8") as f:
        f.write(stats_content)
    print(f"[SUCCESS] Stats SVG written to: {STATS_SVG} & {INFO_CARD_SVG}")


if __name__ == "__main__":
    main()
