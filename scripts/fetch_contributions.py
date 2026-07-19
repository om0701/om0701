from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


DATA_DIR = Path("data")
DEFAULT_USERNAME = "om0701"
CONTRIBUTION_URL = "https://github.com/users/{username}/contributions"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; profile-readme-bot/1.0)",
    "Accept": "text/html",
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch public GitHub contribution calendar data.")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="GitHub username to inspect.")
    return parser.parse_args()


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def extract_days(soup: BeautifulSoup) -> list[dict[str, object]]:
    days: list[dict[str, object]] = []

    # Primary selector: GitHub uses <rect> elements inside SVG calendar
    rects = soup.select("rect[data-date]")

    if not rects:
        # Fallback: older GitHub markup used <td> elements
        rects = soup.select("td[data-date]")

    for element in rects:
        date_value = element.get("data-date")
        if not date_value:
            continue

        level = element.get("data-level", "0")

        # Try to extract exact count from aria-label or tool-tip
        count = 0
        aria_label = element.get("aria-label", "")
        if aria_label:
            count_match = re.search(r"(\d+)\s+contributions?", aria_label)
            if count_match:
                count = int(count_match.group(1))

        # If no aria-label count, check for a nested <tool-tip> element
        if count == 0:
            tooltip = element.find("tool-tip")
            if tooltip:
                tip_text = tooltip.get_text(strip=True)
                tip_match = re.search(r"(\d+)\s+contributions?", tip_text)
                if tip_match:
                    count = int(tip_match.group(1))

        # If still no count, infer from level
        if count == 0 and int(level) > 0:
            count = int(level)

        days.append(
            {
                "date": date_value,
                "count": count,
                "level": int(level),
            }
        )

    return days


def main() -> int:
    args = parse_arguments()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    url = CONTRIBUTION_URL.format(username=args.username)
    print(f"Fetching contributions from {url} ...")
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    days = extract_days(soup)

    if not days:
        print(
            "WARNING: No contribution data found. "
            "GitHub may have changed their markup, or the profile may be private."
        )

    total = sum(d.get("count", 0) for d in days)
    print(f"Found {len(days)} days, {total} total contributions.")

    payload = {
        "username": args.username,
        "source_url": url,
        "days": days,
    }

    output = DATA_DIR / "contributions.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
