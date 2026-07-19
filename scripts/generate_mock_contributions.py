"""Generate realistic mock GitHub contribution data for the heatmap.

Creates a contributions.json with natural-looking patterns:
- Weekdays are busier than weekends
- Occasional multi-day streaks (simulating focused project work)
- Some fully quiet weeks (vacations / breaks)
- Contribution counts vary from 1-12, with occasional spikes
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUTPUT = Path("data/contributions.json")
USERNAME = "om0701"
WEEKS = 53
DAYS = 7

random.seed(42)  # reproducible output


def generate_mock_days() -> list[dict]:
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=(WEEKS * DAYS) - 1)
    days: list[dict] = []

    # Pre-generate "burst weeks" – weeks with high activity (simulating sprints)
    burst_weeks = set(random.sample(range(WEEKS), k=12))
    # Pre-generate "quiet weeks" – vacation / break (zero contributions)
    quiet_weeks = set(random.sample(range(WEEKS), k=6))
    # Make sure burst and quiet don't overlap
    quiet_weeks -= burst_weeks

    cursor = start
    while cursor <= end:
        week_index = (cursor - start).days // DAYS
        day_of_week = cursor.weekday()  # 0=Mon … 6=Sun
        is_weekend = day_of_week >= 5

        if week_index in quiet_weeks:
            # Quiet week – maybe 1-2 tiny commits at most
            if random.random() < 0.08:
                count = random.randint(1, 2)
            else:
                count = 0
        elif week_index in burst_weeks:
            # Burst / sprint week
            if is_weekend:
                count = random.choice([0, 0, 1, 2, 3, 5])
            else:
                count = random.choice([3, 4, 5, 6, 7, 8, 9, 10, 12])
        else:
            # Normal week
            if is_weekend:
                count = random.choice([0, 0, 0, 0, 1, 2])
            else:
                count = random.choices(
                    population=[0, 1, 2, 3, 4, 5, 6, 7],
                    weights=[25, 20, 18, 14, 10, 6, 4, 3],
                    k=1,
                )[0]

        # Assign GitHub-style level (0-4)
        if count == 0:
            level = 0
        elif count <= 2:
            level = 1
        elif count <= 5:
            level = 2
        elif count <= 8:
            level = 3
        else:
            level = 4

        days.append({"date": cursor.isoformat(), "count": count, "level": level})
        cursor += timedelta(days=1)

    return days


def main() -> int:
    days = generate_mock_days()
    total = sum(d["count"] for d in days)
    print(f"Generated {len(days)} days, {total} total mock contributions.")

    payload = {
        "username": USERNAME,
        "source_url": f"https://github.com/users/{USERNAME}/contributions",
        "days": days,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
