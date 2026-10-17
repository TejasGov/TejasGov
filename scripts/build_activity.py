#!/usr/bin/env python3
"""Builds activity.svg: the last year of contributions as an isometric skyline,
with streaks and top languages. Runs daily in .github/workflows/profile.yml and
is published to the `output` branch.

    pip install fonttools uharfbuzz
    GITHUB_TOKEN=... python3 scripts/build_activity.py --out dist
"""

import argparse
import datetime as dt
import json
import math
import os
import subprocess
import urllib.request

from kit import (
    DIM, FAINT, INK_DEEP, LINE, MARIGOLD, MUTED, REDUCED_MOTION, SAFFRON, SOFT, TEXT, document, font, num,
    panel, text, write,
)

USER = "TejasGov"
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      nodes {
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
  }
}
"""
LANG_COLORS = [SAFFRON, "#FF6B4A", "#F2668B", "#9B7BFF", "#5B7CFF", "#3DD9B4"]


def token():
    if os.environ.get("GITHUB_TOKEN"):
        return os.environ["GITHUB_TOKEN"]
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()


def query():
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {token()}", "User-Agent": "build_activity"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


# ── numbers ─────────────────────────────────────────────────────────────────
def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    current = 0
    tail = days[:-1] if days and not days[-1]["contributionCount"] else days   # today may still be empty
    for d in reversed(tail):
        if not d["contributionCount"]:
            break
        current += 1
    return current, longest


def languages(repos, top=6):
    """Weighted like github-readme-stats: sqrt(bytes) × sqrt(repos using it)."""
    size, count = {}, {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            size[name] = size.get(name, 0) + edge["size"]
            count[name] = count.get(name, 0) + 1
    score = {k: math.sqrt(size[k]) * math.sqrt(count[k]) for k in size}
    best = sorted(score.items(), key=lambda kv: -kv[1])[:top]
    total = sum(v for _, v in best) or 1
    shares = [(k, round(100 * v / total)) for k, v in best]
    shares[0] = (shares[0][0], shares[0][1] + 100 - sum(v for _, v in shares))
    return shares


# ── drawing ─────────────────────────────────────────────────────────────────
def shade(hex_color, k):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{max(0, min(255, round(c * k))):02X}" for c in (r, g, b))


LEVELS = ["#1B1F3C", "#56324F", "#B0502F", "#F28A3C", "#FFD08F"]


def level(count, peak):
    if not count:
        return 0
    return min(4, 1 + int(3.999 * math.sqrt(count / peak)))


def axes(s):
    """Weeks run gently up and to the right, weekdays down and to the right."""
    a, b = math.radians(19), math.radians(38)
    return (s * math.cos(a), -s * math.sin(a)), (s * 0.72 * math.cos(b), s * 0.72 * math.sin(b))


def skyline(weeks, ox, oy, s, max_h):
    (ux, uy), (vx, vy) = axes(s)
    peak = max(d["contributionCount"] for w in weeks for d in w["contributionDays"]) or 1
    cells = []
    for wi, week in enumerate(weeks):
        for d in week["contributionDays"]:
            cells.append((wi, d["weekday"], d["contributionCount"], d["date"]))
    cells.sort(key=lambda c: (c[1] - c[0], c[0]))
    shapes, sweep = [], []
    gap = 0.14
    for wi, di, count, date in cells:
        lvl = level(count, peak)
        h = 2.5 if not count else 4 + max_h * math.sqrt(count / peak)
        x0 = ox + wi * ux + di * vx
        y0 = oy + wi * uy + di * vy
        A = (x0 + gap * (ux + vx), y0 + gap * (uy + vy))
        B = (A[0] + ux * (1 - 2 * gap), A[1] + uy * (1 - 2 * gap))
        D = (A[0] + vx * (1 - 2 * gap), A[1] + vy * (1 - 2 * gap))
        C = (B[0] + D[0] - A[0], B[1] + D[1] - A[1])
        lift = lambda p: (p[0], p[1] - h)
        pts = lambda *ps: " ".join(f"{num(x)},{num(y)}" for x, y in ps)
        top = LEVELS[lvl]
        shapes.append(
            f'<polygon points="{pts(A, D, lift(D), lift(A))}" fill="{shade(top, 0.42)}"/>'
            f'<polygon points="{pts(D, C, lift(C), lift(D))}" fill="{shade(top, 0.66)}"/>'
            f'<polygon points="{pts(lift(A), lift(B), lift(C), lift(D))}" fill="{top}"/>'
        )
        if count:
            sweep.append(f'<polygon class="sw" style="animation-delay:{wi * 0.07:.2f}s" '
                         f'points="{pts(lift(A), lift(B), lift(C), lift(D))}" fill="#FFF3DF"/>')
    return "".join(shapes), "".join(sweep)


def build(user, out):
    calendar = user["contributionsCollection"]["contributionCalendar"]
    weeks = calendar["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    total = calendar["totalContributions"]
    current, longest = streaks(days)
    busiest = max(days, key=lambda d: d["contributionCount"])
    by_weekday = [0] * 7
    for d in days:
        by_weekday[d["weekday"]] += d["contributionCount"]
    weekday = ["Sundays", "Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays"][by_weekday.index(max(by_weekday))]
    langs = languages(user["repositories"]["nodes"])
    today = dt.date.fromisoformat(days[-1]["date"])

    serif, sans, mono, mono_m = font("serif"), font("sans", 400), font("mono", 400), font("mono", 500)
    W, H = 1200, 640
    pad = 48
    ox, oy, s = 432, 462, 13
    (ux, uy), (vx, vy) = axes(s)

    city, sweep = skyline(weeks, ox, oy, s, 150)
    busy_date = dt.date.fromisoformat(busiest["date"]).strftime("%b %-d")
    stats = [
        ("CURRENT STREAK", f"{current} day{'s' if current != 1 else ''}"),
        ("LONGEST STREAK", f"{longest} days"),
        ("BUSIEST DAY", f"{busy_date} · {busiest['contributionCount']}"),
        ("MOST ACTIVE ON", weekday),
    ]
    left = [
        text(mono, "LAST 12 MONTHS", 12, pad, 66, DIM, track=1.8),
        text(serif, f"{total:,}", 104, pad - 4, 170, TEXT, track=-2),
        text(sans, "contributions", 19, pad, 204, MUTED),
    ]
    for i, (label, value) in enumerate(stats):
        y = 268 + i * 64
        left.append(f'<rect x="{pad}" y="{y - 26}" width="300" height="1" fill="{LINE}"/>')
        left.append(text(mono, label, 11, pad, y, DIM, track=1.6))
        left.append(text(sans, value, 21, pad, y + 26, TEXT, track=-0.2))

    # month ticks under the skyline
    ticks, seen = [], set()
    for wi, week in enumerate(weeks):
        first = dt.date.fromisoformat(week["contributionDays"][0]["date"])
        key = (first.year, first.month)
        if key in seen or wi == 0:
            seen.add(key)
            continue
        seen.add(key)
        x = ox + wi * ux + 7 * vx + 4
        y = oy + wi * uy + 7 * vy + 18
        ticks.append(text(mono, first.strftime("%b").upper(), 10, x, y, FAINT, track=1.2))

    # languages
    bar_x, bar_y, bar_w = pad, H - 64, W - 2 * pad
    segments, legend, x = [], [], bar_x
    for (name, share), color in zip(langs, LANG_COLORS):
        w = bar_w * share / 100
        segments.append(f'<rect x="{num(x)}" y="{bar_y}" width="{num(max(w - 3, 1))}" height="6" fill="{color}"/>')
        x += w
    lx = pad
    for (name, share), color in zip(langs, LANG_COLORS):
        legend.append(f'<rect x="{num(lx)}" y="{H - 38}" width="7" height="7" fill="{color}"/>')
        label = f"{name.upper()} {share}%"
        legend.append(text(mono, label, 11, lx + 15, H - 31, MUTED, track=1.2))
        lx += mono.width(label, 11, 1.2) + 40
    lang_title = text(mono, "LANGUAGES BY CODE SHARE", 11, pad, bar_y - 14, DIM, track=1.6)

    updated = text(mono, f"UPDATED {today.strftime('%-d %b %Y').upper()}", 11, W - pad, 66, FAINT, anchor="end", track=1.6)
    defs, open_, close = panel(W, H, 22)
    body = (
        "<defs>" + defs
        + f'<clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="6" rx="3"/></clipPath>'
        + f'<radialGradient id="warm" cx="880" cy="300" r="520" gradientUnits="userSpaceOnUse">'
          f'<stop offset="0" stop-color="#FF8A3D" stop-opacity=".09"/><stop offset="1" stop-color="#FF8A3D" stop-opacity="0"/></radialGradient>'
        + "</defs>" + open_
        + f'<rect width="{W}" height="{H}" fill="url(#warm)"/>'
        + city + f"<g>{sweep}</g>" + "".join(ticks)
        + "".join(left) + updated
        + lang_title + f'<g clip-path="url(#bar)">{"".join(segments)}</g>' + "".join(legend)
        + close
    )
    css = (".sw{opacity:0;animation:sw 9s ease-in-out infinite}"
           "@keyframes sw{0%{opacity:0}3%{opacity:.5}10%{opacity:0}100%{opacity:0}}" + REDUCED_MOTION)
    title = (f"{total:,} contributions in the last 12 months. Current streak {current} days, longest {longest} days. "
             "Top languages: " + ", ".join(f"{n} {v}%" for n, v in langs))
    write("activity.svg", document(W, H, title, body, css), root=out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="dist")
    args = parser.parse_args()
    build(query(), args.out)
