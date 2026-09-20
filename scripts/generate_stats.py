#!/usr/bin/env python3
"""Generate local stats SVGs (tokyonight style) for the GitHub profile README.

Outputs (written to ./stats/, dark "tokyonight" + light variants):
  stats.svg / stats-light.svg           - overall stats card
  top-langs.svg / top-langs-light.svg   - languages donut card
  pin-<repo>.svg / pin-<repo>-light.svg - one card per featured repo
  activity.svg / activity-light.svg     - contribution activity area chart
  trophies.svg / trophies-light.svg     - trophy wall (ryo-ma algorithm replica)
    (activity/trophies require GITHUB_TOKEN; skipped with a warning when unavailable)

Environment:
  GITHUB_USER   - GitHub username (default: helloe365)
  GITHUB_TOKEN  - token for higher API rate limits (optional but recommended)
"""
import json
import math
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GITHUB_USER", "helloe365")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"
# (repo, blurb). The blurb overrides the repo's own description so the cards stay
# English regardless of the language the repo is documented in. Keep blurbs <= 66
# chars or trunc() will ellipsize them.
FEATURED_REPOS = [
    ("CrackPDFPassword", "Multi-process CPU + hashcat GPU recovery, fully resumable"),
    ("CupLens", "Forecasting with versioned models and hashed provenance"),
    ("RagAgent", "LangChain RAG: ReAct tools, incremental KB, streaming UI"),
    ("AdaptiveFinancialFraudDetectionSystem",
     "DevNet deviation network + VAE augmentation for fraud detection"),
]

LANG_COLORS = {
    "Python": "#3572A5", "HTML": "#e34c26", "CSS": "#563d7c",
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Shell": "#89e051",
    "C": "#555555", "C++": "#f34b7d", "Java": "#b07219",
    "Jupyter Notebook": "#DA5B0B", "TeX": "#3D6117", "Makefile": "#427819",
    "Dockerfile": "#384d54", "Go": "#00ADD8", "Rust": "#dea584",
    "Vue": "#41b883", "SCSS": "#c6538c", "PowerShell": "#012456",
    "Batchfile": "#C1F12E", "SQL": "#e38c00", "MDX": "#fcb32c",
}

PURPLE = "#bb9af7"
CYAN = "#7dcfff"
GREEN = "#9ece6a"
ORANGE = "#ff9e64"
FONT = "Segoe UI, Ubuntu, Helvetica, Arial, sans-serif"

# filename suffix -> palette. "" = dark (tokyonight), "-light" = GitHub light.
THEMES = {
    "": {
        "BG": "#1a1b27", "FG": "#c0caf5", "MUTED": "#565f89",
        "SUBTLE": "#9aa5ce", "ACCENT": "#7aa2f7", "BORDER": "#1a1b27",
        "RANKS": {
            "SSS": "#ffd700", "SS": "#ff9e64", "S": "#e0af68",
            "AAA": "#bb9af7", "AA": "#7aa2f7", "A": "#7dcfff",
            "B": "#9ece6a", "C": "#9aa5ce", "SECRET": "#f7768e", "?": "#565f89",
        },
    },
    "-light": {
        "BG": "#ffffff", "FG": "#1f2328", "MUTED": "#8c959f",
        "SUBTLE": "#59636e", "ACCENT": "#0969da", "BORDER": "#d1d9e0",
        "RANKS": {
            "SSS": "#b08800", "SS": "#bc4c00", "S": "#9a6700",
            "AAA": "#8250df", "AA": "#0969da", "A": "#0550ae",
            "B": "#1a7f37", "C": "#59636e", "SECRET": "#cf222e", "?": "#8c959f",
        },
    },
}

BG = FG = MUTED = SUBTLE = ACCENT = BORDER = ""
RANKS = {}


def use_theme(palette):
    global BG, FG, MUTED, SUBTLE, ACCENT, BORDER, RANKS
    BG = palette["BG"]
    FG = palette["FG"]
    MUTED = palette["MUTED"]
    SUBTLE = palette["SUBTLE"]
    ACCENT = palette["ACCENT"]
    BORDER = palette["BORDER"]
    RANKS = palette["RANKS"]


def api(path, retries=4, critical=True):
    """GET a GitHub API path with retries. Returns None on failure when not critical."""
    url = API + path
    last_err = None
    for i in range(retries):
        try:
            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": "profile-stats-generator",
            }
            if TOKEN:
                headers["Authorization"] = f"Bearer {TOKEN}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2 * (i + 1))
    if critical:
        raise last_err
    print(f"WARN: request failed: {url} ({last_err})")
    return None


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def trunc(s, n):
    s = s or ""
    return s if len(s) <= n else s[: n - 1] + "…"


def fmt(n):
    return f"{n:,}"


def svg_wrap(w, h, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}">\n'
        f'  <rect width="{w}" height="{h}" rx="10" fill="{BG}" stroke="{BORDER}"/>\n{body}\n</svg>\n'
    )


def text(x, y, content, size=13, fill=SUBTLE, weight="normal", anchor="start"):
    return (
        f'  <text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}">{esc(content)}</text>'
    )


def stats_svg(stars, commits, repos, forks, prs, issues):
    left = [
        ("⭐", "Total Stars", stars, ORANGE),
        ("💬", "Total Commits", commits, CYAN),
        ("📦", "Total Repos", repos, PURPLE),
    ]
    right = [
        ("🍴", "Total Forks", forks, ACCENT),
        ("🔀", "Total PRs", prs, GREEN),
        ("📋", "Total Issues", issues, "#f7768e"),
    ]
    body = [text(25, 38, f"{USER}'s GitHub Stats", 18, FG, "600")]
    body.append(f'  <line x1="0" y1="52" x2="495" y2="52" stroke="{MUTED}" stroke-opacity="0.4"/>')
    for idx, (icon, label, value, color) in enumerate(left):
        y = 88 + idx * 37
        body.append(text(25, y, f"{icon}  {label}", 13, SUBTLE))
        body.append(text(235, y, fmt(value), 15, FG, "600", anchor="end"))
    for idx, (icon, label, value, color) in enumerate(right):
        y = 88 + idx * 37
        body.append(text(265, y, f"{icon}  {label}", 13, SUBTLE))
        body.append(text(470, y, fmt(value), 15, FG, "600", anchor="end"))
    return svg_wrap(495, 195, "\n".join(body))


def langs_svg(lang_items):
    """lang_items: list of (lang, bytes)."""
    total = sum(b for _, b in lang_items) or 1
    top = lang_items[:6]
    other = sum(b for _, b in lang_items[6:])
    if other > 0:
        top.append(("Other", other))

    cx, cy, r, sw = 150, 118, 52, 24
    c = 2 * math.pi * r
    acc = 0.0
    arcs = []
    for lang, b in top:
        seg = b / total * c
        color = LANG_COLORS.get(lang, "#7aa2f7" if lang == "Other" else "#565f89")
        dash = f"{seg:.2f} {c - seg:.2f}"
        arcs.append(
            f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-dasharray="{dash}" stroke-dashoffset="{-acc:.2f}" '
            f'transform="rotate(-90 {cx} {cy})"/>'
        )
        acc += seg

    body = [text(25, 38, "Most Used Languages", 18, FG, "600")]
    body.append(f'  <line x1="0" y1="52" x2="495" y2="52" stroke="{MUTED}" stroke-opacity="0.4"/>')
    body.extend(arcs)
    body.append(text(cx, cy - 2, str(len(top) - (1 if other > 0 else 0)), 26, FG, "700", "middle"))
    body.append(text(cx, cy + 20, "languages", 11, MUTED, "normal", "middle"))
    ly = 78
    for lang, b in top:
        color = LANG_COLORS.get(lang, "#7aa2f7" if lang == "Other" else "#565f89")
        pct = b / total * 100
        body.append(f'  <rect x="255" y="{ly - 11}" width="12" height="12" rx="3" fill="{color}"/>')
        body.append(text(275, ly, lang, 13, FG))
        body.append(text(470, ly, f"{pct:.1f}%", 13, SUBTLE, "normal", "end"))
        ly += 21
    return svg_wrap(495, 195, "\n".join(body))


def pin_svg(repo, blurb=None):
    name = repo["name"]
    desc = trunc(blurb or repo.get("description") or "", 66)
    lang = repo.get("language") or ""
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    color = LANG_COLORS.get(lang, "#7aa2f7")

    body = [text(25, 38, name, 17, ACCENT, "600")]
    body.append(f'  <rect x="{25 + 8.2 * len(name) + 10:.0f}" y="24" width="52" height="18" rx="9" '
                f'fill="none" stroke="{MUTED}"/>')
    body.append(text(25 + 8.2 * len(name) + 36, 37, "Public", 11, MUTED, "normal", "middle"))
    body.append(text(25, 68, desc, 13, SUBTLE))
    if lang:
        body.append(f'  <circle cx="31" cy="102" r="6" fill="{color}"/>')
        body.append(text(43, 106, lang, 12, FG))
    body.append(text(495 - 130, 106, f"⭐ {fmt(stars)}", 12, SUBTLE))
    body.append(text(495 - 60, 106, f"🍴 {fmt(forks)}", 12, SUBTLE))
    return svg_wrap(495, 128, "\n".join(body))


GQL = "https://api.github.com/graphql"
CAL_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def graphql(query, variables, retries=4):
    """POST a GraphQL query. Returns None on failure (never raises)."""
    if not TOKEN:
        print("WARN: GITHUB_TOKEN not set, skipping activity graph")
        return None
    payload = json.dumps({"query": query, "variables": variables}).encode()
    last_err = None
    for i in range(retries):
        try:
            req = urllib.request.Request(
                GQL, data=payload, method="POST",
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "profile-stats-generator",
                    "Content-Type": "application/json",
                })
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
            if data.get("errors"):
                raise RuntimeError(data["errors"])
            return data.get("data")
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2 * (i + 1))
    print(f"WARN: graphql request failed ({last_err})")
    return None


def contribution_weeks():
    """Return (total_contributions, [(week_start_date, weekly_sum), ...])."""
    data = graphql(CAL_QUERY, {"login": USER})
    if not data:
        return 0, []
    cal = (data.get("user") or {}).get("contributionsCollection", {}).get(
        "contributionCalendar", {})
    weeks = []
    for w in cal.get("weeks", []):
        days = w.get("contributionDays", [])
        if days:
            weeks.append((days[0]["date"], sum(d["contributionCount"] for d in days)))
    return cal.get("totalContributions", 0), weeks


def nice_max(v):
    """Smallest candidate >= v; all candidates divisible by 3 for clean gridlines."""
    for m in (6, 9, 12, 15, 18, 24, 30, 45, 60, 90, 120, 150, 300, 600, 900, 1200):
        if v <= m:
            return m
    return ((v // 600) + 1) * 600


def activity_svg(total, weeks):
    W, H = 850, 240
    x0, x1, y0, y1 = 48, W - 20, 68, 190
    vals = [v for _, v in weeks]
    top = nice_max(max(vals) if vals else 0)
    n = len(weeks)

    def px(i):
        return x0 + (x1 - x0) * (i / (n - 1) if n > 1 else 0.5)

    def py(v):
        return y1 - (y1 - y0) * (v / top)

    pts = [(px(i), py(v)) for i, v in enumerate(vals)]
    line = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{line} L {pts[-1][0]:.1f},{y1} L {pts[0][0]:.1f},{y1} Z"

    body = [
        f'  <defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.35"/>'
        f'<stop offset="100%" stop-color="{ACCENT}" stop-opacity="0.02"/>'
        f'</linearGradient></defs>',
        text(25, 38, "Contribution Activity", 18, FG, "600"),
        text(W - 20, 38, f"{fmt(total)} contributions in the last year",
             13, SUBTLE, "normal", "end"),
        f'  <line x1="0" y1="52" x2="{W}" y2="52" stroke="{MUTED}" stroke-opacity="0.4"/>',
    ]
    for frac in (0, 1 / 3, 2 / 3, 1):
        gy = y1 - (y1 - y0) * frac
        body.append(f'  <line x1="{x0}" y1="{gy:.1f}" x2="{x1}" y2="{gy:.1f}" '
                    f'stroke="{MUTED}" stroke-opacity="0.25"/>')
        body.append(text(x0 - 8, gy + 4, f"{top * frac:g}", 11, MUTED,
                         "normal", "end"))
    body.append(f'  <path d="{area}" fill="url(#fade)"/>')
    body.append(f'  <path d="{line}" fill="none" stroke="{ACCENT}" '
                f'stroke-width="2" stroke-linejoin="round"/>')
    prev_month = None
    for i, (date, _) in enumerate(weeks):
        month = int(date[5:7])
        if month != prev_month:
            anchor = "start" if i == 0 else "middle"
            body.append(text(px(i), H - 12, MONTHS[month - 1], 11, MUTED,
                             "normal", anchor))
            prev_month = month
    return svg_wrap(W, H, "\n".join(body))


TROPHY_QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    organizations { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestReviewContributions
    }
    openIssues: issues(states: OPEN) { totalCount }
    closedIssues: issues(states: CLOSED) { totalCount }
    pullRequests { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        createdAt
        languages(first: 10) { nodes { name } }
      }
    }
  }
}"""

# Rank thresholds replicated from ryo-ma/github-profile-trophy (src/trophy.ts).
RANK_ORDER = ["SECRET", "SSS", "SS", "S", "AAA", "AA", "A", "B", "C", "?"]
COND_STAR = [("SSS", "Super Stargazer", 2000), ("SS", "High Stargazer", 700),
             ("S", "Stargazer", 200), ("AAA", "Super Star", 100),
             ("AA", "High Star", 50), ("A", "You are a Star", 30),
             ("B", "Middle Star", 10), ("C", "First Star", 1)]
COND_COMMIT = [("SSS", "God Committer", 4000), ("SS", "Deep Committer", 2000),
               ("S", "Super Committer", 1000), ("AAA", "Ultra Committer", 500),
               ("AA", "Hyper Committer", 200), ("A", "High Committer", 100),
               ("B", "Middle Committer", 10), ("C", "First Commit", 1)]
COND_FOLLOWER = [("SSS", "Super Celebrity", 1000), ("SS", "Ultra Celebrity", 400),
                 ("S", "Hyper Celebrity", 200), ("AAA", "Famous User", 100),
                 ("AA", "Active User", 50), ("A", "Dynamic User", 20),
                 ("B", "Many Friends", 10), ("C", "First Friend", 1)]
COND_ISSUE = [("SSS", "God Issuer", 1000), ("SS", "Deep Issuer", 500),
              ("S", "Super Issuer", 200), ("AAA", "Ultra Issuer", 100),
              ("AA", "Hyper Issuer", 50), ("A", "High Issuer", 20),
              ("B", "Middle Issuer", 10), ("C", "First Issue", 1)]
COND_PR = [("SSS", "God Puller", 1000), ("SS", "Deep Puller", 500),
           ("S", "Super Puller", 200), ("AAA", "Ultra Puller", 100),
           ("AA", "Hyper Puller", 50), ("A", "High Puller", 20),
           ("B", "Middle Puller", 10), ("C", "First Pull", 1)]
COND_REPO = [("SSS", "God Repo Creator", 50), ("SS", "Deep Repo Creator", 45),
             ("S", "Super Repo Creator", 40), ("AAA", "Ultra Repo Creator", 35),
             ("AA", "Hyper Repo Creator", 30), ("A", "High Repo Creator", 20),
             ("B", "Middle Repo Creator", 10), ("C", "First Repository", 1)]
COND_REVIEW = [("SSS", "God Reviewer", 70), ("SS", "Deep Reviewer", 57),
               ("S", "Super Reviewer", 45), ("AAA", "Ultra Reviewer", 30),
               ("AA", "Hyper Reviewer", 20), ("A", "Active Reviewer", 8),
               ("B", "Intermediate Reviewer", 3), ("C", "New Reviewer", 1)]
COND_DURATION = [("SSS", "Seasoned Veteran", 70), ("SS", "Grandmaster", 55),
                 ("S", "Master Dev", 40), ("AAA", "Expert Dev", 28),
                 ("AA", "Experienced Dev", 18), ("A", "Intermediate Dev", 11),
                 ("B", "Junior Dev", 6), ("C", "Newbie", 2)]


def trophy_info():
    """Fetch all trophy inputs in one GraphQL query. Returns None on failure."""
    data = graphql(TROPHY_QUERY, {"login": USER})
    if not data:
        return None
    u = data.get("user") or {}
    repos = u.get("repositories", {}) or {}
    nodes = repos.get("nodes") or []
    cc = u.get("contributionsCollection", {}) or {}

    earliest = u.get("createdAt")
    langs, stars = set(), 0
    for n in nodes:
        stars += n.get("stargazerCount", 0)
        if earliest is None or n.get("createdAt", "") < earliest:
            earliest = n.get("createdAt") or earliest
        for l in (n.get("languages") or {}).get("nodes") or []:
            langs.add(l.get("name"))

    days, joined_year = 0, None
    if earliest:
        dt = datetime.fromisoformat(earliest.replace("Z", "+00:00"))
        days = max(0, (datetime.now(timezone.utc) - dt).days)
        joined_year = dt.year

    return {
        "stars": stars,
        "commits": cc.get("totalCommitContributions", 0)
        + cc.get("restrictedContributionsCount", 0),
        "followers": (u.get("followers") or {}).get("totalCount", 0),
        "issues": (u.get("openIssues") or {}).get("totalCount", 0)
        + (u.get("closedIssues") or {}).get("totalCount", 0),
        "prs": (u.get("pullRequests") or {}).get("totalCount", 0),
        "repos": repos.get("totalCount", len(nodes)),
        "reviews": cc.get("totalPullRequestReviewContributions", 0),
        "langs": len(langs),
        "orgs": (u.get("organizations") or {}).get("totalCount", 0),
        "duration_year": days // 365,
        "duration_score": days // 100,
        "joined_year": joined_year,
    }


def rank_for(score, conditions):
    """Highest-priority rank whose threshold is met (RANK_ORDER = priority)."""
    for rank, msg, threshold in sorted(
            conditions, key=lambda c: RANK_ORDER.index(c[0])):
        if score >= threshold:
            return rank, msg
    return "?", "Unknown"


def abridge(score):
    if abs(score) < 1:
        return "0pt"
    if abs(score) > 999:
        return f"{score / 1000:.1f}kpt"
    return f"{score}pt"


def trophy_panels(info):
    """Return [(rank, title, message, bottom_text), ...] to display."""
    base = [
        ("Stars", info["stars"], COND_STAR),
        ("Commits", info["commits"], COND_COMMIT),
        ("Followers", info["followers"], COND_FOLLOWER),
        ("Issues", info["issues"], COND_ISSUE),
        ("PullRequest", info["prs"], COND_PR),
        ("Repositories", info["repos"], COND_REPO),
        ("Reviews", info["reviews"], COND_REVIEW),
    ]
    panels, base_ranks = [], []
    for title, score, cond in base:
        rank, msg = rank_for(score, cond)
        base_ranks.append(rank)
        panels.append((rank, title, msg, abridge(score)))

    # Secret trophies — only shown when earned (same as upstream filterByHidden)
    jy = info["joined_year"]
    if all(r.startswith("S") for r in base_ranks):
        panels.append(("SECRET", "All S", "S Rank Hacker", ""))
    if info["langs"] >= 10:
        panels.append(("SECRET", "Languages", "Rainbow Lang User",
                       abridge(info["langs"])))
    if info["duration_year"] >= 10:
        panels.append(("SECRET", "Veteran", "Village Elder",
                       abridge(info["duration_year"])))
    if jy is not None and jy <= 2008:
        panels.append(("SECRET", "OG", "OG User", "Joined 2008"))
    if jy is not None and jy <= 2010:
        panels.append(("SECRET", "Ancient", "Ancient User", "Joined 2010"))
    if jy == 2020:
        panels.append(("SECRET", "2020", "Everything started...", "Joined 2020"))
    if info["orgs"] >= 3:
        panels.append(("SECRET", "Orgs", "Jack of all Trades",
                       abridge(info["orgs"])))
    rank, msg = rank_for(info["duration_score"], COND_DURATION)
    if rank != "?":
        panels.append((rank, "Experience", msg, ""))
    return panels


def _panel(x, y, rank, title, message, bottom):
    color = RANKS.get(rank, MUTED)
    rank_size = 13 if len(rank) <= 3 else 8.5  # "SECRET" needs a smaller font
    parts = [
        f'  <circle cx="{x + 55:.0f}" cy="{y + 34}" r="22" fill="none" '
        f'stroke="{color}" stroke-width="2.5"/>',
        text(x + 55, y + 40, rank, rank_size, color, "700", "middle"),
        text(x + 55, y + 74, title, 12, FG, "600", "middle"),
        text(x + 55, y + 90, message, 8.5, SUBTLE, "normal", "middle"),
    ]
    if bottom:
        parts.append(text(x + 55, y + 105, bottom, 9, MUTED, "normal", "middle"))
    return parts


def trophies_svg(info):
    panels = trophy_panels(info)
    per_row = 7  # 7 * 118px = 826px, fits the 850px canvas
    rows = [panels[i:i + per_row] for i in range(0, len(panels), per_row)]
    W = 850
    H = 64 + len(rows) * 118 + 12
    body = [
        text(25, 38, f"{USER}'s Trophies", 18, FG, "600"),
        text(W - 20, 38, f"{len(panels)} trophies unlocked", 13, SUBTLE,
             "normal", "end"),
        f'  <line x1="0" y1="52" x2="{W}" y2="52" stroke="{MUTED}" stroke-opacity="0.4"/>',
    ]
    for r, row in enumerate(rows):
        x_start = (W - len(row) * 118) / 2
        for c, (rank, title, msg, bottom) in enumerate(row):
            body.extend(_panel(x_start + c * 118, 64 + r * 118,
                               rank, title, msg, bottom))
    return svg_wrap(W, H, "\n".join(body))


def main():
    os.makedirs("stats", exist_ok=True)

    user = api(f"/users/{USER}")
    repos = []
    page = 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    owned = [r for r in repos if not r.get("fork")]

    lang_bytes = {}
    for r in owned:
        langs = api(f"/repos/{r['full_name']}/languages", critical=False) or {}
        for lang, b in langs.items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + b
    lang_items = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)

    def search_total(kind):
        q = urllib.parse.quote(f"author:{USER} type:{kind}")
        data = api(f"/search/issues?q={q}", critical=False) or {}
        return data.get("total_count", 0)

    commits_data = api(
        "/search/commits?q=" + urllib.parse.quote(f"author:{USER}"), critical=False
    ) or {}

    stars = sum(r.get("stargazers_count", 0) for r in owned)
    commits = commits_data.get("total_count", 0)
    prs = search_total("pr")
    issues = search_total("issue")

    total_contribs, weeks = contribution_weeks()
    tinfo = trophy_info()

    repo_map = {r["name"]: r for r in owned}
    outputs = {}
    for suffix, palette in THEMES.items():
        use_theme(palette)
        outputs[f"stats/stats{suffix}.svg"] = stats_svg(
            stars, commits, user.get("public_repos", len(owned)),
            sum(r.get("forks_count", 0) for r in owned), prs, issues,
        )
        outputs[f"stats/top-langs{suffix}.svg"] = langs_svg(lang_items)
        if weeks:
            outputs[f"stats/activity{suffix}.svg"] = activity_svg(
                total_contribs, weeks)
        if tinfo:
            outputs[f"stats/trophies{suffix}.svg"] = trophies_svg(tinfo)
        for name, blurb in FEATURED_REPOS:
            if name in repo_map:
                outputs[f"stats/pin-{name}{suffix}.svg"] = pin_svg(repo_map[name], blurb)
            elif not suffix:
                print(f"WARN: featured repo not found: {name}")

    for path, svg in outputs.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
