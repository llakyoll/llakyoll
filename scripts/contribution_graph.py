"""Render the visible GitHub profile contribution calendar as dark/light SVGs."""
import datetime as dt
import re
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = "llakyoll"
COLORS = {
    "dark": {"bg": "#101d2b", "edge": "#357b80", "text": "#f0f7f8", "muted": "#b4cbd1", "grid": "#314c57", "accent": "#58d6c2", "cells": ["#1c3440", "#24615f", "#318f83", "#47b9a5", "#7de7cf"]},
    "light": {"bg": "#f5faf9", "edge": "#a9d4cd", "text": "#18313b", "muted": "#526d74", "grid": "#c9deda", "accent": "#147c72", "cells": ["#e0eeeb", "#a4ded2", "#6bcab8", "#35ab99", "#147c72"]},
}
def fetch():
    request = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "profile-contribution-graph"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8")
    cells = re.findall(
        r'<td\b[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*id="([^"]+)"[^>]*data-level="([0-4])"[^>]*></td>\s*<tool-tip[^>]*for="\2"[^>]*>(.*?)</tool-tip>',
        page, re.S,
    )
    if not 365 <= len(cells) <= 371:
        raise ValueError(f"Expected a full year of GitHub contribution cells, got {len(cells)}")
    days = {}
    for date, _, level, tooltip in cells:
        count = re.search(r"(\d+) contributions?", tooltip)
        days[date] = {"date": date, "contributionCount": int(count.group(1)) if count else 0, "level": int(level)}
    if len(days) != len(cells):
        raise ValueError("Duplicate dates in GitHub contribution calendar")
    first = min(dt.date.fromisoformat(date) for date in days)
    weeks = [[] for _ in range((max(dt.date.fromisoformat(date) for date in days) - first).days // 7 + 1)]
    for day in days.values():
        index = (dt.date.fromisoformat(day["date"]) - first).days // 7
        weeks[index].append(day)
    total = sum(day["contributionCount"] for day in days.values())
    return {"totalContributions": total, "weeks": [{"contributionDays": sorted(week, key=lambda d: d["date"])} for week in weeks]}


def render(calendar, palette):
    weeks = calendar["weeks"]
    if not 52 <= len(weeks) <= 54:
        raise ValueError("Unexpected contribution calendar length")
    totals = [sum(day["contributionCount"] for day in week["contributionDays"]) for week in weeks]
    peak = max(totals) or 1
    p = palette
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 292" role="img" aria-labelledby="title desc">
<title id="title">Ahmed Akyol's GitHub contributions</title>
<desc id="desc">{calendar['totalContributions']} contributions over the last year, shown by week and day.</desc>
<rect x="1" y="1" width="898" height="290" rx="14" fill="{p['bg']}" stroke="{p['edge']}"/>
<text x="35" y="43" fill="{p['text']}" font-family="Arial,Helvetica,sans-serif" font-size="23" font-weight="700">Contribution activity</text>
<text x="35" y="66" fill="{p['muted']}" font-family="Arial,Helvetica,sans-serif" font-size="14">{calendar['totalContributions']} contributions in the last year</text>
<path d="M35 151H857" stroke="{p['grid']}" stroke-dasharray="3 5"/>
''']
    points = []
    for i, total in enumerate(totals):
        x = 43 + i * 15.6
        y = 148 - total / peak * 58
        points.append(f"{x:.1f},{y:.1f}")
    parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{p["accent"]}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
    for i, week in enumerate(weeks):
        for day in week["contributionDays"]:
            row = (dt.date.fromisoformat(day["date"]).weekday() + 1) % 7
            x, y = 43 + i * 15.6, 169 + row * 14
            color = p["cells"][day["level"]]
            parts.append(f'<rect x="{x:.1f}" y="{y}" width="10" height="10" rx="2" fill="{color}"><title>{day["date"]}: {day["contributionCount"]} contributions</title></rect>')
    parts.append(f'<text x="43" y="280" fill="{p["muted"]}" font-family="Arial,Helvetica,sans-serif" font-size="12">{weeks[0]["contributionDays"][0]["date"]} → {weeks[-1]["contributionDays"][-1]["date"]}</text>')
    parts.append(f'<text x="857" y="280" text-anchor="end" fill="{p["muted"]}" font-family="Arial,Helvetica,sans-serif" font-size="12">Weekly trend · daily contributions</text></svg>')
    return "\n".join(parts) + "\n"


def main():
    calendar = fetch()
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    for name, palette in COLORS.items():
        (out / f"contributions-{name}.svg").write_text(render(calendar, palette), encoding="utf-8")
    print(f"Generated two SVGs: {calendar['totalContributions']} contributions, {len(calendar['weeks'])} weeks")


if __name__ == "__main__":
    main()
