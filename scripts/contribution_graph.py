"""Render the public GitHub contribution calendar as local dark/light SVGs."""
import json
import os
import datetime as dt
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = "llakyoll"
QUERY = "query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"
COLORS = {
    "dark": {"bg": "#101d2b", "edge": "#357b80", "text": "#f0f7f8", "muted": "#b4cbd1", "grid": "#314c57", "accent": "#58d6c2", "cells": ["#1c3440", "#24615f", "#318f83", "#47b9a5", "#7de7cf"]},
    "light": {"bg": "#f5faf9", "edge": "#a9d4cd", "text": "#18313b", "muted": "#526d74", "grid": "#c9deda", "accent": "#147c72", "cells": ["#e0eeeb", "#a4ded2", "#6bcab8", "#35ab99", "#147c72"]},
}
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def fetch():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors") or not result.get("data", {}).get("user"):
        raise SystemExit(f"GitHub GraphQL response has no contribution calendar: {result.get('errors')}")
    return result["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(calendar, palette):
    weeks = calendar["weeks"]
    if not 52 <= len(weeks) <= 54:
        raise ValueError("Unexpected contribution calendar length")
    totals = [sum(day["contributionCount"] for day in week["contributionDays"]) for week in weeks]
    peak = max(totals) or 1
    p = palette
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 292" role="img" aria-labelledby="title desc">
<title id="title">Ahmed Akyol's GitHub contributions</title>
<desc id="desc">{calendar['totalContributions']} public contributions over the last year, shown by week and day.</desc>
<rect x="1" y="1" width="898" height="290" rx="14" fill="{p['bg']}" stroke="{p['edge']}"/>
<text x="35" y="43" fill="{p['text']}" font-family="Arial,Helvetica,sans-serif" font-size="23" font-weight="700">Contribution activity</text>
<text x="35" y="66" fill="{p['muted']}" font-family="Arial,Helvetica,sans-serif" font-size="14">{calendar['totalContributions']} public contributions in the last year</text>
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
            color = p["cells"][LEVELS[day["contributionLevel"]]]
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
