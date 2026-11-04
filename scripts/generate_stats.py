#!/usr/bin/env python3
"""Fetch GitHub evidence once, then render all local stats from the same snapshot.

Live: GITHUB_TOKEN=... python scripts/generate_stats.py
Offline replay: python scripts/generate_stats.py --snapshot stats/data.json
Only the Python standard library is required. A failed API request aborts before
writing any outputs; missing data is never turned into a zero or a stale card.
"""
import argparse
import json
import math
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from generate_assets import ROOT, THEMES, svg, text

API = "https://api.github.com"
FEATURED_REPOS = {
    "CrackPDFPassword": {
        "title": ["CrackPDFPassword"],
        "description": "恢复自有或授权 PDF 的遗忘密码",
        "highlight": "中断后可从检查点继续",
        "stack": [("code", "Python"), ("chip", "hashcat")],
    },
    "CupLens": {
        "title": ["CupLens"],
        "description": "为赛事预测保留可追溯依据",
        "highlight": "保存模型版本、来源与快照哈希",
        "stack": [("code", "Python"), ("api", "FastAPI"), ("layers", "React")],
    },
    "RagAgent": {
        "title": ["RagAgent"],
        "description": "让本地知识库支持检索问答",
        "highlight": "内容未变的文件不重复入库",
        "stack": [("code", "Python"), ("layers", "LangChain"), ("data", "SQLite")],
    },
    "AdaptiveFinancialFraudDetectionSystem": {
        "title": ["AdaptiveFinancial", "FraudDetectionSystem"],
        "description": "识别不平衡交易数据中的欺诈",
        "highlight": "VAE 增强少数类，DevNet 检测",
        "stack": [("code", "Python"), ("layers", "PyTorch"), ("data", "VAE")],
    },
}
CAL_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def request_json(path, token, payload=None):
    url = API + path
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "helloe365-profile",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    if body:
        headers["Content-Type"] = "application/json"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.load(response)
            if isinstance(data, dict) and data.get("errors"):
                raise RuntimeError(f"GitHub GraphQL error: {data['errors']}")
            return data
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f"GitHub HTTP {exc.code}: {path}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise
        time.sleep(attempt + 1)
    raise RuntimeError(f"GitHub request failed: {path}")


def collect_snapshot(user, token):
    if not token:
        raise ValueError("Set GITHUB_TOKEN for live data, or use --snapshot stats/data.json.")
    repos = []
    page = 1
    while True:
        batch = request_json(
            f"/users/{user}/repos?type=owner&sort=full_name&per_page=100&page={page}", token
        )
        repos.extend(r for r in batch if not r["fork"] and not r["private"])
        if len(batch) < 100:
            break
        page += 1

    def with_languages(repo):
        return {
            key: repo[key] for key in (
                "name", "full_name", "html_url", "description", "language",
                "stargazers_count", "forks_count",
            )
        } | {"languages": request_json(f"/repos/{repo['full_name']}/languages", token)}

    with ThreadPoolExecutor(max_workers=4) as pool:
        repositories = list(pool.map(with_languages, repos))
    response = request_json("/graphql", token, {"query": CAL_QUERY, "variables": {"login": user}})
    owner = response["data"]["user"]
    if not owner:
        raise ValueError(f"GitHub user not found: {user}")
    result = {
        "schema": 1,
        "user": user,
        "sources": {
            "repositories": f"{API}/users/{user}/repos",
            "contributions": f"https://github.com/{user}?tab=overview",
            "graphql": f"{API}/graphql",
        },
        "repositories": sorted(repositories, key=lambda r: r["name"]),
        "contributions": owner["contributionsCollection"],
    }
    validate_snapshot(result)
    return result


def validate_snapshot(data):
    if data["schema"] != 1 or not data["user"]:
        raise ValueError("Unsupported or missing snapshot schema/user.")
    repos = data["repositories"]
    missing = set(FEATURED_REPOS) - {r["name"] for r in repos}
    if missing:
        raise ValueError(f"Missing featured repositories: {', '.join(sorted(missing))}")
    cc = data["contributions"]
    counts = [cc[k] for k in (
        "totalCommitContributions", "totalPullRequestContributions",
        "totalIssueContributions", "totalPullRequestReviewContributions",
    )]
    for repo in repos:
        counts.extend((repo["stargazers_count"], repo["forks_count"]))
        counts.extend(repo["languages"].values())
    cal = cc["contributionCalendar"]
    days = [d for week in cal["weeks"] for d in week["contributionDays"]]
    if not days:
        raise ValueError("Contribution calendar is empty; refusing to overwrite cards.")
    dates = [d["date"] for d in days]
    if dates != sorted(set(dates)):
        raise ValueError("Calendar dates must be unique and chronological.")
    counts.extend(d["contributionCount"] for d in days)
    counts.append(cal["totalContributions"])
    if any(type(n) is not int or n < 0 for n in counts):
        raise ValueError("Every API metric must be a nonnegative integer.")
    if sum(d["contributionCount"] for d in days) != cal["totalContributions"]:
        raise ValueError("Contribution calendar total does not match its daily counts.")


def fmt(number):
    return f"{number:,}"


def stats_svg(data, t):
    repos = data["repositories"]
    cc = data["contributions"]
    columns = [
        [("Stars", sum(r["stargazers_count"] for r in repos)),
         ("Commits / yr", cc["totalCommitContributions"]),
         ("Repos", len(repos))],
        [("Forks", sum(r["forks_count"] for r in repos)),
         ("PRs / yr", cc["totalPullRequestContributions"]),
         ("Issues / yr", cc["totalIssueContributions"])],
    ]
    body = [text(20, 34, "GitHub overview", 20, t["CYAN"], 600)]
    for col, rows in enumerate(columns):
        x = 20 + col * 196
        for row, (label, value) in enumerate(rows):
            y = 72 + row * 36
            body.extend([
                text(x, y, label, 16, t["MUTED"]),
                text(x + 164, y, fmt(value), 20, t["GREEN"], 600, "end"),
            ])
    return svg(400, 165, body, t, f"{data['user']}: GitHub overview",
               "Stars, forks and repositories: public, owned, non-fork repositories. "
               "Commits, pull requests and issues: GitHub's visible contributions in the last year.")


def langs_svg(data, t):
    totals = {}
    for repo in data["repositories"]:
        for lang, size in repo["languages"].items():
            totals[lang] = totals.get(lang, 0) + size
    items = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    total = sum(totals.values())
    rows = items[:3]
    if len(items) > 3:
        rows.append(("Other", sum(n for _, n in items[3:])))
    body = [text(20, 34, "Languages by bytes", 20, t["CYAN"], 600)]
    if not total:
        body.append(text(20, 88, "No language bytes reported", 16, t["MUTED"]))
    for i, (name, count) in enumerate(rows):
        y = 66 + i * 28
        label = "Notebook" if name == "Jupyter Notebook" else name
        body.extend([
            text(20, y, label, 16, t["TEXT"]),
            f'<rect x="184" y="{y - 10}" width="112" height="8" rx="4" fill="{t["BORDER"]}"/>',
            f'<rect x="184" y="{y - 10}" width="{112 * count / total:.2f}" '
            f'height="8" rx="4" fill="{t["PURPLE"]}"/>',
            text(380, y, f"{100 * count / total:.1f}%", 16, t["MUTED"], anchor="end"),
        ])
    return svg(400, 165, body, t, "Languages by repository bytes",
               "GitHub Languages API; owned public non-fork repositories, "
               "top three languages and all remaining languages grouped as Other. "
               "Notebook means Jupyter Notebook; percentages are not proficiency scores.")


ICON_PATHS = {
    "code": "m5 3-4 5 4 5m6-10 4 5-4 5M9 1 7 15",
    "chip": "M3 3h10v10H3zM6 0v3m4-3v3M6 13v3m4-3v3M0 6h3m-3 4h3m10-4h3m-3 4h3",
    "api": "m9 1-6 8h5l-1 6 6-8H8z",
    "layers": "m8 1 7 4-7 4-7-4zM1 8l7 4 7-4M1 11l7 4 7-4",
    "data": "M2 4c0-4 12-4 12 0s-12 4-12 0v8c0 4 12 4 12 0V4M2 8c0 4 12 4 12 0",
}


def pin_svg(repo, spec, t):
    body = [text(20, 36 + i * 28, line, 20, t["TEXT"], 600)
            for i, line in enumerate(spec["title"])]
    body.extend([
        text(20, 96, spec["description"], 16, t["TEXT"]),
        text(20, 124, spec["highlight"], 16, t["MUTED"]),
    ])
    for i, (icon, label) in enumerate(spec["stack"]):
        x = 20 + i * 124
        body.extend([
            f'<path d="{ICON_PATHS[icon]}" transform="translate({x} 148)" '
            f'stroke="{t["PURPLE"]}" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>',
            text(x + 24, 162, label, 16, t["PURPLE"]),
        ])
    body.extend([
        f'<path d="M20 180h360" stroke="{t["BORDER"]}" stroke-width="1"/>',
        text(20, 208, f'{fmt(repo["stargazers_count"])} '
             f'{"star" if repo["stargazers_count"] == 1 else "stars"}', 16, t["GREEN"], 600),
        text(380, 208, f'{fmt(repo["forks_count"])} '
             f'{"fork" if repo["forks_count"] == 1 else "forks"}', 16, t["MUTED"], anchor="end"),
    ])
    return svg(400, 228, body, t, repo["name"],
               f'{spec["description"]}；{spec["highlight"]}。'
               f'{repo["stargazers_count"]} stars, {repo["forks_count"]} forks. '
               f'Source: {repo["html_url"]}')


def contribution_weeks(data):
    return [
        (w["contributionDays"][0]["date"], sum(d["contributionCount"] for d in w["contributionDays"]))
        for w in data["contributions"]["contributionCalendar"]["weeks"]
        if w["contributionDays"]
    ]


def nice_max(value):
    return max(4, math.ceil(value / 4) * 4)


def activity_svg(data, t):
    weeks = contribution_weeks(data)
    total = data["contributions"]["contributionCalendar"]["totalContributions"]
    x0, x1, y0, y1 = 48, 688, 76, 184
    ceiling = nice_max(max((n for _, n in weeks), default=0))
    points = [(x0 + (x1 - x0) * (i / (len(weeks) - 1) if len(weeks) > 1 else 0.5),
               y1 - n / ceiling * (y1 - y0)) for i, (_, n) in enumerate(weeks)]
    body = [
        text(24, 36, "Weekly contributions", 20, t["CYAN"], 600),
        text(688, 36, f"{fmt(total)} / year", 20, t["GREEN"], 600, "end"),
    ]
    for i in range(3):
        y = y1 - (y1 - y0) * i / 2
        body.extend([
            f'<path d="M{x0} {y}H{x1}" stroke="{t["BORDER"]}" stroke-width="1"/>',
            text(x0 - 12, y + 6, str(int(ceiling * i / 2)), 16, t["MUTED"], anchor="end"),
        ])
    if points:
        coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        body.append(f'<polyline points="{coords}" stroke="{t["GREEN"]}" '
                    'stroke-width="1" stroke-linejoin="round"/>')
        if len(points) == 1:
            body.append(f'<circle cx="{points[0][0]:.2f}" cy="{points[0][1]:.2f}" '
                        f'r="3" fill="{t["GREEN"]}"/>')
        for i in sorted({0, len(weeks) // 2, len(weeks) - 1}):
            anchor = "start" if i == 0 else "end" if i == len(weeks) - 1 else "middle"
            body.append(text(points[i][0], 216, weeks[i][0], 16, t["MUTED"], anchor=anchor))
    return svg(720, 240, body, t, "Weekly contribution activity",
               "Sum of contributionCalendar daily counts by GitHub calendar week; "
               "first and last weeks may be partial. Contributions include more than commits.")


def milestone(value):
    reached = [n for n in (1, 10, 100, 1000, 10000) if value >= n]
    return f"{fmt(reached[-1])}+" if reached else "—"


def trophies_svg(data, t):
    repos = data["repositories"]
    cal = data["contributions"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    entries = [
        ("Stars received", sum(r["stargazers_count"] for r in repos)),
        ("Public projects", len(repos)),
        ("PRs / year", data["contributions"]["totalPullRequestContributions"]),
        ("Active days / year", sum(d["contributionCount"] > 0 for d in days)),
    ]
    body = [text(24, 36, "Open-source milestones", 28, t["CYAN"], 600)]
    for i, (label, value) in enumerate(entries):
        x = 24 + i * 172
        body.extend([
            text(x, 84, milestone(value), 28, t["GREEN"], 600),
            text(x, 116, f"{fmt(value)} recorded", 16, t["TEXT"]),
            text(x, 144, label, 16, t["MUTED"]),
        ])
    return svg(720, 172, body, t, "Open-source milestones",
               "Local thresholds: 1, 10, 100, 1000, 10000. These are not official "
               "GitHub achievements, rankings, or measures of engineering ability.")


def render(data):
    validate_snapshot(data)
    repos = {r["name"]: r for r in data["repositories"]}
    outputs = {}
    for suffix, theme in THEMES.items():
        for name, build in (("stats", stats_svg), ("top-langs", langs_svg),
                            ("activity", activity_svg), ("trophies", trophies_svg)):
            outputs[f"{name}{suffix}.svg"] = build(data, theme).encode("utf-8")
        for name, spec in FEATURED_REPOS.items():
            outputs[f"pin-{name}{suffix}.svg"] = pin_svg(repos[name], spec, theme).encode("utf-8")
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, help="Replay an existing JSON snapshot without network access.")
    args = parser.parse_args()
    if args.snapshot:
        data = json.loads(args.snapshot.read_text(encoding="utf-8"))
    else:
        data = collect_snapshot(os.environ.get("GITHUB_USER", "helloe365"), os.environ.get("GITHUB_TOKEN", ""))
    outputs = render(data)  # Validate and render every card before writing anything.
    output = ROOT / "stats"
    output.mkdir(exist_ok=True)
    for name, markup in outputs.items():
        (output / name).write_bytes(markup)
    (output / "data.json").write_bytes(
        (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    print(f"Wrote {len(outputs)} SVGs and stats/data.json for {data['user']}.")


if __name__ == "__main__":
    main()
