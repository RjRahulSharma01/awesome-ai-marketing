#!/usr/bin/env python3
"""AI Tools Momentum Index.

Measures which tools on the Awesome AI Marketing list are gaining or losing
attention, using three free public signals:

  * Wikipedia page views (Wikimedia REST API)
  * Hacker News stories and comments that mention the tool (Algolia HN API)
  * GitHub stars, for open-source tools (GitHub REST API), shown for context

Each signal is compared over the last 28 days against the 28 days before.
Small numbers are damped so a page going from 3 to 9 views doesn't read
as +200%. The momentum score is the average change across the two
attention signals (Wikipedia and Hacker News) a tool has.

Standard library only. Run:  python3 momentum/momentum.py
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS_FILE = ROOT / "tools.json"
HISTORY_FILE = ROOT / "data" / "history.csv"
LATEST_FILE = ROOT / "data" / "latest.json"
README_FILE = ROOT / "README.md"
CHART_FILE = ROOT / "chart.svg"

WINDOW_DAYS = 28
USER_AGENT = (
    "awesome-ai-marketing-momentum/1.0 "
    "(https://github.com/RjRahulSharma01/awesome-ai-marketing)"
)
# Damping constants: added to both windows before comparing them.
DAMPING = {"wiki": 500, "hn": 25}

HISTORY_FIELDS = [
    "date", "tool", "wiki_28d", "wiki_prev_28d",
    "hn_28d", "hn_prev_28d", "github_stars",
]


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------

def get_json(url: str, headers: dict | None = None, retries: int = 3):
    """GET a URL and parse JSON. Returns None on 404, raises on other errors."""
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    hdrs.update(headers or {})
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            if attempt == retries - 1 or err.code < 500 and err.code != 429:
                raise
        except urllib.error.URLError:
            if attempt == retries - 1:
                raise
        time.sleep(2 * (attempt + 1))
    return None


def wiki_views(title: str, end: dt.date) -> tuple[int, int] | None:
    """Page views for the last 28 days and the 28 before, ending at `end`."""
    start = end - dt.timedelta(days=2 * WINDOW_DAYS - 1)
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia/all-access/user/{urllib.parse.quote(title, safe='')}/daily/"
        f"{start:%Y%m%d}/{end:%Y%m%d}"
    )
    data = get_json(url)
    if not data or not data.get("items"):
        return None
    split = end - dt.timedelta(days=WINDOW_DAYS - 1)
    recent = prev = 0
    for item in data["items"]:
        day = dt.datetime.strptime(item["timestamp"][:8], "%Y%m%d").date()
        if day >= split:
            recent += item["views"]
        else:
            prev += item["views"]
    return recent, prev


def hn_mentions(query: str, end: dt.date) -> tuple[int, int] | None:
    """Hacker News stories + comments matching `query` in each window."""
    end_ts = int(dt.datetime.combine(end + dt.timedelta(days=1), dt.time()).timestamp())
    mid_ts = end_ts - WINDOW_DAYS * 86400
    start_ts = mid_ts - WINDOW_DAYS * 86400

    def count(lo: int, hi: int) -> int:
        params = urllib.parse.urlencode({
            "query": query,
            "tags": "(story,comment)",
            "numericFilters": f"created_at_i>={lo},created_at_i<{hi}",
            "hitsPerPage": 0,
        })
        data = get_json(f"https://hn.algolia.com/api/v1/search_by_date?{params}")
        return int(data["nbHits"]) if data else 0

    return count(mid_ts, end_ts), count(start_ts, mid_ts)


def github_stars(repo: str) -> int | None:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = get_json(f"https://api.github.com/repos/{repo}", headers)
    return int(data["stargazers_count"]) if data else None


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

def damped_change(recent: float, prev: float, k: float) -> float:
    """Percent change with damping so tiny bases don't produce huge swings."""
    return ((recent + k) / (prev + k) - 1) * 100


def stars_28_days_ago(history: list[dict], tool: str, today: dt.date) -> int | None:
    """Most recent star count recorded at least 28 days before today."""
    cutoff = today - dt.timedelta(days=WINDOW_DAYS)
    best = None
    for row in history:
        if row["tool"] != tool or not row.get("github_stars"):
            continue
        day = dt.date.fromisoformat(row["date"])
        if day <= cutoff and (best is None or day > best[0]):
            best = (day, int(row["github_stars"]))
    return best[1] if best else None


def score(tool: dict, raw: dict, history: list[dict], today: dt.date) -> dict:
    changes = {}
    if raw.get("wiki"):
        changes["wiki"] = damped_change(*raw["wiki"], DAMPING["wiki"])
    if raw.get("hn"):
        changes["hn"] = damped_change(*raw["hn"], DAMPING["hn"])
    stars_gained = None
    if raw.get("stars") is not None:
        old = stars_28_days_ago(history, tool["name"], today)
        if old is not None:
            stars_gained = raw["stars"] - old
    momentum = sum(changes.values()) / len(changes) if changes else None
    return {"name": tool["name"], "section": tool["section"], "changes": changes,
            "momentum": momentum, "stars_gained": stars_gained, **{k: raw.get(k) for k in ("wiki", "hn", "stars")}}


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    with HISTORY_FILE.open(newline="") as fh:
        return list(csv.DictReader(fh))


def save_history(history: list[dict], today: dt.date, results: list[dict]) -> None:
    kept = [row for row in history if row["date"] != today.isoformat()]
    for r in results:
        kept.append({
            "date": today.isoformat(), "tool": r["name"],
            "wiki_28d": r["wiki"][0] if r["wiki"] else "",
            "wiki_prev_28d": r["wiki"][1] if r["wiki"] else "",
            "hn_28d": r["hn"][0] if r["hn"] else "",
            "hn_prev_28d": r["hn"][1] if r["hn"] else "",
            "github_stars": "" if r["stars"] is None else r["stars"],
        })
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=HISTORY_FIELDS)
        writer.writeheader()
        writer.writerows(sorted(kept, key=lambda r: (r["date"], r["tool"])))


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "–"
    return f"{value:+.0f}%"


def fmt_int(value: int | None) -> str:
    return "–" if value is None else f"{value:,}"


def render_chart(ranked: list[dict], today: dt.date) -> str:
    """Diverging horizontal bar chart of momentum, as standalone SVG."""
    rows = [r for r in ranked if r["momentum"] is not None]
    bar_h, gap, top, left, width = 18, 6, 56, 190, 760
    plot_w = width - left - 70
    zero_x = left + plot_w / 2
    cap = max(25.0, min(100.0, max((abs(r["momentum"]) for r in rows), default=25)))
    height = top + len(rows) * (bar_h + gap) + 30
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        '<text x="20" y="26" font-size="16" font-weight="600" fill="#1f2328">'
        'AI Tools Momentum Index</text>',
        f'<text x="20" y="44" font-size="12" fill="#59636e">Change in attention, last 28 days vs the '
        f'28 before · updated {today:%d %b %Y}</text>',
        f'<line x1="{zero_x}" y1="{top - 6}" x2="{zero_x}" y2="{height - 24}" stroke="#d1d9e0"/>',
    ]
    for i, r in enumerate(rows):
        y = top + i * (bar_h + gap)
        val = max(-cap, min(cap, r["momentum"]))
        length = abs(val) / cap * (plot_w / 2)
        x = zero_x if val >= 0 else zero_x - length
        colour = "#1a7f37" if val >= 0 else "#cf222e"
        out.append(f'<text x="{left - 10}" y="{y + 13}" font-size="12" text-anchor="end" '
                   f'fill="#1f2328">{r["name"]}</text>')
        out.append(f'<rect x="{x:.1f}" y="{y}" width="{max(length, 1):.1f}" height="{bar_h}" '
                   f'rx="3" fill="{colour}"/>')
        label_x = zero_x + length + 6 if val >= 0 else zero_x - length - 6
        anchor = "start" if val >= 0 else "end"
        out.append(f'<text x="{label_x:.1f}" y="{y + 13}" font-size="11" text-anchor="{anchor}" '
                   f'fill="#59636e">{fmt_pct(r["momentum"])}</text>')
    out.append(f'<text x="{zero_x}" y="{height - 8}" font-size="11" text-anchor="middle" '
               f'fill="#59636e">0%  (bars capped at ±{cap:.0f}%)</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def render_readme(ranked: list[dict], today: dt.date, gaps: list[str]) -> str:
    scored = [r for r in ranked if r["momentum"] is not None]
    lines = [
        "# AI Tools Momentum Index",
        "",
        "Which tools on the [Awesome AI Marketing](../README.md) list are gaining attention, "
        "and which are cooling off. Rebuilt automatically every Monday by "
        "[a GitHub Action](../.github/workflows/momentum.yml); nobody edits these numbers by hand.",
        "",
        f"**Last updated:** {today:%d %B %Y}",
        "",
    ]
    if len(scored) >= 2:
        up, down = scored[0], scored[-1]
        lines += [
            f"**This month's biggest mover:** {up['name']} ({fmt_pct(up['momentum'])}). "
            f"**Cooling off most:** {down['name']} ({fmt_pct(down['momentum'])}).",
            "",
        ]
    lines += [
        "![Momentum chart](chart.svg)",
        "",
        "| Rank | Tool | Momentum | Wikipedia views (28 days) | Change | HN mentions (28 days) | Change | GitHub stars | Stars gained (28 days) |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for i, r in enumerate(ranked, 1):
        wiki = r["wiki"][0] if r["wiki"] else None
        hn = r["hn"][0] if r["hn"] else None
        lines.append(
            f"| {i if r['momentum'] is not None else '–'} | {r['name']} | "
            f"**{fmt_pct(r['momentum'])}** | {fmt_int(wiki)} | {fmt_pct(r['changes'].get('wiki'))} | "
            f"{fmt_int(hn)} | {fmt_pct(r['changes'].get('hn'))} | {fmt_int(r['stars'])} | {fmt_int(r['stars_gained'])} |"
        )
    lines += [
        "",
        "## How the score works",
        "",
        "For each tool, every available signal compares the last 28 days with the 28 days before:",
        "",
        "- **Wikipedia views**: daily page views of the tool's English Wikipedia article, "
        "excluding bots ([Wikimedia API](https://wikimedia.org/api/rest_v1/)).",
        "- **Hacker News mentions**: stories and comments matching the tool's name "
        "([HN Algolia API](https://hn.algolia.com/api)). A rough signal of builder interest.",
        "- **GitHub stars**: shown for open-source tools as context, not scored. "
        "Stars gained appears once the index has 4 weeks of its own history.",
        "",
        f"Small numbers are damped (adding {DAMPING['wiki']} views and {DAMPING['hn']} mentions to "
        "both windows) so a jump from 3 to 9 doesn't read as +200%. **Momentum** is the average "
        "change across the Wikipedia and Hacker News signals a tool has. It measures attention, not quality: a tool can "
        "trend because of bad news too.",
        "",
        "Raw weekly numbers live in [data/history.csv](data/history.csv), so anyone can check "
        "or reuse them. The code is [momentum.py](momentum.py), standard-library Python with no keys.",
        "",
        "## Run it yourself",
        "",
        "```bash",
        "python3 momentum/momentum.py",
        "```",
        "",
        "Add or change tools in [tools.json](tools.json).",
    ]
    if gaps:
        lines += ["", "## Data gaps this week", ""]
        lines += [f"- {g}" for g in gaps]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def collect(tools: list[dict], end: dt.date) -> tuple[dict, list[str]]:
    raw, gaps = {}, []
    for tool in tools:
        entry = {"wiki": None, "hn": None, "stars": None}
        checks = [("wiki", "wikipedia", wiki_views, (end,)),
                  ("hn", "hn", hn_mentions, (end,)),
                  ("stars", "github", github_stars, ())]
        for key, field, fn, extra in checks:
            if not tool.get(field):
                continue
            try:
                entry[key] = fn(tool[field], *extra)
                if entry[key] is None:
                    gaps.append(f"{tool['name']}: no {field} data for `{tool[field]}`")
            except Exception as err:  # keep going; one bad source shouldn't stop the run
                gaps.append(f"{tool['name']}: {field} request failed ({type(err).__name__})")
            time.sleep(0.2)
        raw[tool["name"]] = entry
    return raw, gaps


def main() -> int:
    tools = json.loads(TOOLS_FILE.read_text())
    today = dt.date.today()
    end = today - dt.timedelta(days=1)  # yesterday is the last complete day
    history = load_history()

    raw, gaps = collect(tools, end)
    results = [score(t, raw[t["name"]], history, today) for t in tools]
    ranked = sorted(results, key=lambda r: (r["momentum"] is None, -(r["momentum"] or 0)))

    if not any(r["momentum"] is not None for r in results):
        print("No signals could be fetched; leaving files unchanged.", file=sys.stderr)
        for g in gaps:
            print(" -", g, file=sys.stderr)
        return 1

    save_history(history, today, results)
    LATEST_FILE.write_text(json.dumps({"date": today.isoformat(), "tools": ranked}, indent=2) + "\n")
    CHART_FILE.write_text(render_chart(ranked, today))
    README_FILE.write_text(render_readme(ranked, today, gaps))

    for r in ranked:
        print(f"{r['name']:<24} {fmt_pct(r['momentum']):>6}")
    if gaps:
        print("\nGaps:\n" + "\n".join(" - " + g for g in gaps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
