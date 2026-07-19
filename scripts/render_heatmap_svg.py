from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


INPUT = Path("data/contributions.json")
OUTPUT = Path("contrib-heatmap.svg")
WEEKS = 53
DAYS = 7

# GitHub dark-theme palette
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def load_days() -> list[dict[str, object]]:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    return payload.get("days", [])


def build_grid(days: list[dict[str, object]]) -> list[list[int]]:
    counts: dict[str, int] = defaultdict(int)
    for entry in days:
        date_str = str(entry.get("date", ""))
        if not date_str:
            continue
        counts[date_str] = int(entry.get("count", 0))

    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=(WEEKS * DAYS) - 1)
    grid: list[list[int]] = [[0 for _ in range(DAYS)] for _ in range(WEEKS)]

    cursor = start
    while cursor <= end:
        week_index = (cursor - start).days // DAYS
        day_index = (cursor - start).days % DAYS
        grid[week_index][day_index] = counts.get(cursor.isoformat(), 0)
        cursor += timedelta(days=1)

    return grid


def compute_thresholds(grid: list[list[int]]) -> list[int]:
    """Compute quartile thresholds from non-zero contribution counts."""
    non_zero = sorted(
        count for week in grid for count in week if count > 0
    )
    if not non_zero:
        return [1, 2, 3, 4]

    n = len(non_zero)
    return [
        non_zero[0],                              # level 1: any activity
        non_zero[min(n - 1, n // 4)],             # level 2: 25th percentile
        non_zero[min(n - 1, n // 2)],             # level 3: 50th percentile
        non_zero[min(n - 1, (3 * n) // 4)],       # level 4: 75th percentile
    ]


def color_for(count: int, thresholds: list[int]) -> str:
    """Map a contribution count to a palette color using quartile thresholds."""
    if count == 0:
        return PALETTE[0]
    if count >= thresholds[3]:
        return PALETTE[4]
    if count >= thresholds[2]:
        return PALETTE[3]
    if count >= thresholds[1]:
        return PALETTE[2]
    return PALETTE[1]


def build_svg(grid: list[list[int]], total: int) -> str:
    cols = len(grid)
    rows = len(grid[0])
    cell = 14
    gap = 2
    margin_x = 46
    margin_top = 60
    width = margin_x * 2 + cols * (cell + gap)
    height = margin_top + rows * (cell + gap) + 70

    thresholds = compute_thresholds(grid)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="#0d1117" rx="6"/>',
        f'<text x="40" y="32" font-family="\'Segoe UI\', Arial, Helvetica, sans-serif" font-size="18" fill="#e6edf3">GitHub Contribution Heatmap</text>',
        f'<text x="40" y="50" font-family="\'Segoe UI\', Arial, Helvetica, sans-serif" font-size="13" fill="#7d8590">Yearly total: {total}</text>',
    ]

    square_idx = 0
    for week in range(cols):
        for day in range(rows):
            count = grid[week][day]
            x = margin_x + week * (cell + gap)
            y = margin_top + day * (cell + gap)
            delay = round(square_idx * 0.015, 4)
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{color_for(count, thresholds)}" opacity="0" transform="translate(-8 -8) scale(0.78)">'
                f'<animate attributeName="opacity" values="0;1" dur="0.2s" begin="{delay}s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" values="-8 -8;0 0" dur="0.2s" begin="{delay}s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="scale" values="0.78 0.78;1 1" dur="0.2s" begin="{delay}s" fill="freeze" additive="sum"/>'
                '</rect>'
            )
            square_idx += 1

    legend_x = 40
    legend_y = height - 28
    parts.append(f'<text x="{legend_x}" y="{legend_y - 6}" font-family="\'Segoe UI\', Arial, Helvetica, sans-serif" font-size="12" fill="#7d8590">Less</text>')
    for idx, color in enumerate(PALETTE):
        lx = legend_x + 44 + idx * 24
        parts.append(
            f'<rect x="{lx}" y="{legend_y - 16}" width="16" height="16" rx="2" fill="{color}"/>'
        )
    parts.append(f'<text x="{legend_x + 44 + len(PALETTE) * 24}" y="{legend_y - 6}" font-family="\'Segoe UI\', Arial, Helvetica, sans-serif" font-size="12" fill="#7d8590">More</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> int:
    if not INPUT.exists():
        print(f"Missing contribution data: {INPUT}")
        return 1

    days = load_days()
    grid = build_grid(days)
    total = sum(item.get("count", 0) for item in days)
    OUTPUT.write_text(build_svg(grid, total), encoding="utf-8")
    print(f"Saved {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
