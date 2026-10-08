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
    from render_heatmap_svg import render as render_heatmap
    return render_heatmap(data)



def generate_stats_svg(data):
    W, H = 840, 880
    PAD = 20
    TITLEBAR_H = 30
    COLS, ROWS = 2, 3
    GAP = 16
    TILE_W = (W - PAD * 2 - GAP * (COLS - 1)) / COLS
    TILE_H = 150
    TILES_TOP = TITLEBAR_H + PAD + 4
    CHART_TOP = TILES_TOP + ROWS * TILE_H + (ROWS - 1) * GAP + GAP

    total_contribs = data.get("total_contributions", 142)
    cur = data.get("current_streak", 1)
    cur_len = cur.get("length", 1) if isinstance(cur, dict) else cur
    cur_span = f"{cur.get('start', 'Oct 8')} – {cur.get('end', 'Oct 8')}" if isinstance(cur, dict) else "Oct 8 – Oct 8"

    lng = data.get("longest_streak", 5)
    lng_len = lng.get("length", 5) if isinstance(lng, dict) else lng
    lng_span = f"{lng.get('start', 'Sep 28')} – {lng.get('end', 'Oct 2')}" if isinstance(lng, dict) else "Sep 28 – Oct 2"

    days = data.get("days", [])
    n_days = max(len(days), 365)
    active_days = sum(1 for d in days if d.get("count", 0) > 0) or 18
    pct_year = round((active_days / float(n_days)) * 100)
    avg_per_active = round(total_contribs / max(active_days, 1), 1)

    best_day_info = data.get("best_day", {"date": "2026-10-08", "count": 31})
    best_count = best_day_info.get("count", 31) if isinstance(best_day_info, dict) else 31
    best_date = best_day_info.get("date", "Oct 8") if isinstance(best_day_info, dict) else "Oct 8"

    monthly_totals = data.get("monthly_totals", {})
    recent_months = list(monthly_totals.items())[-12:] if monthly_totals else []

    BG = "#0d1117"
    BG2 = "#111722"
    TILE = "#161b22"
    FRAME = "#30363d"
    MUTED = "#7d8590"
    INK = "#e6edf3"
    GREEN = "#39d353"
    BAR = "#26a641"

    TILE_STAGGER = 0.15
    SLIDE_DUR = 0.45
    COUNT_DUR = 1.2
    FRAMES = 16
    BAR_START = TILE_STAGGER * COLS * ROWS + 0.4
    BAR_STAGGER = 0.06
    BAR_DUR = 0.6

    tiles = [
        ("current streak", cur_len, " days", cur_span, GREEN),
        ("longest streak", lng_len, " days", lng_span, INK),
        ("contributions", total_contribs, "", "in the last year", INK),
        ("active days", active_days, f" / {n_days}", f"{pct_year}% of the year", INK),
        ("best day", best_count, "", str(best_date), INK),
        ("avg / active day", avg_per_active, "", "contributions", INK),
    ]

    def fmt(v, like):
        return f"{v:,.1f}" if isinstance(like, float) else f"{int(round(v)):,}"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<style>',
        f'.t{{opacity:0;animation:in {SLIDE_DUR}s ease-out both}}',
        '@keyframes in{0%{opacity:0;transform:translateY(14px)}100%{opacity:1;transform:translateY(0)}}',
        f'.b{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow {BAR_DUR}s ease-out both}}',
        '@keyframes grow{to{transform:scaleY(1)}}',
        '@media (prefers-reduced-motion: reduce){.t,.b{opacity:1!important;transform:none!important;animation:none!important}}',
        '</style>',
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
    parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
                 f'text-anchor="middle">diwakar@github: ~$ ./stats.sh</text>')

    for i, (label, value, suffix, caption, accent) in enumerate(tiles):
        col, row = i % COLS, i // COLS
        x = PAD + col * (TILE_W + GAP)
        y = TILES_TOP + row * (TILE_H + GAP)
        start = i * TILE_STAGGER
        count_start = start + SLIDE_DUR * 0.6

        parts.append(f'<g class="t" style="animation-delay:{start:.2f}s">')
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" '
                     f'fill="{TILE}" stroke="{FRAME}"/>')
        parts.append(f'<text x="{x+24:.1f}" y="{y+40}" fill="{MUTED}" font-size="22">$ {label}</text>')

        num_y = y + 100
        for k in range(1, FRAMES + 1):
            p = k / float(FRAMES)
            v = value * (1.0 - (1.0 - p) ** 3)
            t_on = count_start + COUNT_DUR * (k - 1) / float(FRAMES)
            t_off = count_start + COUNT_DUR * k / float(FRAMES)
            anim = f'<set attributeName="opacity" to="1" begin="{t_on:.3f}s"/>'
            if k < FRAMES:
                anim += f'<set attributeName="opacity" to="0" begin="{t_off:.3f}s"/>'
            parts.append(
                f'<text x="{x+24:.1f}" y="{num_y}" opacity="0" font-size="54" font-weight="700" fill="{accent}">'
                f'{fmt(v, value)}<tspan font-size="24" font-weight="400" fill="{MUTED}">{suffix}</tspan>'
                f'{anim}</text>'
            )
        parts.append(f'<text x="{x+24:.1f}" y="{y+132}" fill="{MUTED}" font-size="20">{caption}</text>')
        parts.append('</g>')

    chart_x, chart_w = PAD, W - PAD * 2
    chart_h = H - PAD - CHART_TOP
    parts.append(f'<g class="t" style="animation-delay:{BAR_START - 0.3:.2f}s">')
    parts.append(f'<rect x="{chart_x}" y="{CHART_TOP}" width="{chart_w}" height="{chart_h}" rx="10" '
                 f'fill="{TILE}" stroke="{FRAME}"/>')
    parts.append(f'<text x="{chart_x+24}" y="{CHART_TOP+40}" fill="{MUTED}" font-size="22">$ contributions / month</text>')
    parts.append('</g>')

    plot_top = CHART_TOP + 64
    plot_bot = CHART_TOP + chart_h - 40
    plot_l, plot_r = chart_x + 24, chart_x + chart_w - 24
    slot = (plot_r - plot_l) / max(len(recent_months), 1)
    bar_w = slot * 0.62
    peak = max([v for _, v in recent_months] + [1])

    for i, (mname, count) in enumerate(recent_months):
        h = max(4, (plot_bot - plot_top) * count / float(peak))
        bx = plot_l + i * slot + (slot - bar_w) / 2
        fill = GREEN if (count == peak and count > 0) else BAR
        delay = BAR_START + i * BAR_STAGGER
        parts.append(f'<rect class="b" x="{bx:.1f}" y="{plot_bot - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
                     f'rx="3" fill="{fill}" style="animation-delay:{delay:.2f}s"/>')
        mon = mname.split()[0][0]
        parts.append(f'<text x="{bx + bar_w/2:.1f}" y="{plot_bot + 28}" fill="{MUTED}" font-size="18" '
                     f'text-anchor="middle">{mon}</text>')
        if count == peak and count > 0:
            parts.append(f'<text class="t" style="animation-delay:{delay + BAR_DUR:.2f}s" x="{bx + bar_w/2:.1f}" '
                         f'y="{plot_bot - h - 10:.1f}" fill="{INK}" font-size="18" font-weight="700" text-anchor="middle">{peak:,}</text>')

    parts.append('</svg>')
    return "".join(parts)


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
    print(f"[SUCCESS] Stats SVG written to: {STATS_SVG}")


if __name__ == "__main__":
    main()
