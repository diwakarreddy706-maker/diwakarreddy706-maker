#!/usr/bin/env python3
"""
fetch_contributions.py
Retrieves public GitHub contribution calendar data for a specified user
and saves structured information into data/contributions.json.
"""

import argparse
import datetime
import json
import os
import re
import sys
import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "diwakarrreddy706-maker"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "contributions.json")


def generate_empty_or_fixture_calendar(fixture=False):
    """Generates a 365-day calendar. If fixture=True, populates realistic sample data."""
    today = datetime.date.today()
    days = []
    
    # 52 weeks * 7 days + current week offset (~365 days)
    start_date = today - datetime.timedelta(days=364)
    curr = start_date
    
    total_count = 0
    best_day = {"date": None, "count": 0}
    monthly_totals = {}
    
    while curr <= today:
        date_str = curr.strftime("%Y-%m-%d")
        month_str = curr.strftime("%b %Y")
        
        if fixture:
            # Generate sample pattern for testing renderer
            day_num = curr.timetuple().tm_yday
            if (day_num * 7 + curr.weekday()) % 5 in (0, 1):
                count = (day_num % 9) + 1
            elif (day_num % 11) == 0:
                count = 15
            else:
                count = 0
        else:
            count = 0
            
        level = 0
        if count > 0:
            if count <= 2:
                level = 1
            elif count <= 5:
                level = 2
            elif count <= 9:
                level = 3
            else:
                level = 4
                
        days.append({
            "date": date_str,
            "count": count,
            "level": level
        })
        
        total_count += count
        if count > best_day["count"]:
            best_day = {"date": date_str, "count": count}
            
        monthly_totals[month_str] = monthly_totals.get(month_str, 0) + count
        curr += datetime.timedelta(days=1)

    streaks = calculate_streaks(days)
    
    return {
        "username": DEFAULT_USERNAME,
        "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",
        "is_fixture": fixture,
        "total_contributions": total_count,
        "current_streak": streaks["current_streak"],
        "longest_streak": streaks["longest_streak"],
        "best_day": best_day if best_day["date"] else {"date": "-", "count": 0},
        "monthly_totals": monthly_totals,
        "days": days
    }


def calculate_streaks(days):
    """Calculates current streak and longest streak from ordered days list."""
    longest = 0
    current_run = 0
    
    for day in days:
        if day["count"] > 0:
            current_run += 1
            if current_run > longest:
                longest = current_run
        else:
            current_run = 0
            
    # Current streak calculation: scan backwards from today/latest
    curr_streak = 0
    # Check if latest day or yesterday was active
    if days:
        i = len(days) - 1
        # Allow yesterday to maintain current streak if today has no contributions yet
        if days[i]["count"] == 0 and i > 0 and days[i-1]["count"] > 0:
            i -= 1
        
        while i >= 0 and days[i]["count"] > 0:
            curr_streak += 1
            i -= 1

    return {
        "current_streak": curr_streak,
        "longest_streak": longest
    }


def fetch_github_contributions(username, fixture_mode=False):
    """Fetches and parses public GitHub contribution calendar."""
    if fixture_mode:
        print(f"[INFO] Fixture mode enabled. Generating test dataset for {username}...")
        return generate_empty_or_fixture_calendar(fixture=True)

    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "X-Requested-With": "XMLHttpRequest"
    }

    print(f"[INFO] Requesting contribution calendar from: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"[INFO] HTTP Response Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[WARNING] GitHub returned HTTP {response.status_code} for user '{username}'.")
            print("[INFO] Fallback to standard 0-contribution structure (user may be new or account private).")
            return generate_empty_or_fixture_calendar(fixture=False)
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Build map of tooltips by element ID for exact contribution counts
        tooltips = {}
        for tt in soup.find_all("tool-tip"):
            for_id = tt.get("for")
            if for_id:
                tooltips[for_id] = tt.get_text(strip=True)
                
        day_elements = soup.find_all(["td", "rect"], class_=lambda c: c and "ContributionCalendar-day" in c)
        
        if not day_elements:
            print("[WARNING] Could not parse contribution calendar elements from HTML response.")
            print("[INFO] Fallback to standard 0-contribution structure.")
            return generate_empty_or_fixture_calendar(fixture=False)

        parsed_days = []
        for el in day_elements:
            date_str = el.get("data-date")
            if not date_str:
                continue
                
            level = int(el.get("data-level", 0))
            el_id = el.get("id")
            
            # Extract count from tooltip or text
            text = tooltips.get(el_id, "") or el.get_text(strip=True) or el.get("aria-label", "")
            count = 0
            if text:
                match = re.search(r"(\d+)\s+contribution", text)
                if match:
                    count = int(match.group(1))
                elif "No contribution" in text or "no contribution" in text:
                    count = 0
                else:
                    # Fallback check for raw number inside data-count
                    if el.get("data-count"):
                        try:
                            count = int(el.get("data-count"))
                        except ValueError:
                            count = 0
            else:
                if el.get("data-count"):
                    try:
                        count = int(el.get("data-count"))
                    except ValueError:
                        count = 0

            parsed_days.append({
                "date": date_str,
                "count": count,
                "level": level
            })

        # Sort by date ascending
        parsed_days.sort(key=lambda x: x["date"])
        
        # Calculate totals & stats
        total_count = sum(d["count"] for d in parsed_days)
        best_day = {"date": "-", "count": 0}
        monthly_totals = {}
        
        for d in parsed_days:
            cnt = d["count"]
            if cnt > best_day["count"]:
                best_day = {"date": d["date"], "count": cnt}
                
            dt = datetime.datetime.strptime(d["date"], "%Y-%m-%d")
            m_str = dt.strftime("%b %Y")
            monthly_totals[m_str] = monthly_totals.get(m_str, 0) + cnt
            
        streaks = calculate_streaks(parsed_days)
        
        return {
            "username": username,
            "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",
            "is_fixture": False,
            "total_contributions": total_count,
            "current_streak": streaks["current_streak"],
            "longest_streak": streaks["longest_streak"],
            "best_day": best_day,
            "monthly_totals": monthly_totals,
            "days": parsed_days
        }

    except Exception as e:
        print(f"[ERROR] Exception during contribution fetch: {e}")
        print("[INFO] Fallback to standard 0-contribution structure.")
        return generate_empty_or_fixture_calendar(fixture=False)


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub contribution calendar data.")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="GitHub username")
    parser.add_argument("--output", default=OUTPUT_FILE, help="Path to save output JSON")
    parser.add_argument("--fixture", action="store_true", help="Generate fixture sample data for testing")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    data = fetch_github_contributions(args.username, fixture_mode=args.fixture)
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    print(f"[SUCCESS] Contributions data saved to: {args.output}")
    print(f" Total contributions: {data['total_contributions']}")
    print(f" Current streak: {data['current_streak']} days")
    print(f" Longest streak: {data['longest_streak']} days")


if __name__ == "__main__":
    main()
