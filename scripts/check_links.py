#!/usr/bin/env python3
"""Check every image referenced by README.md renders, not just links.

Remote URLs are fetched and their HTTP status + content-type verified.
For shields.io badges the SVG body is also scanned for error strings
("404: badge not found", "invalid", "rate limit", "Error"), because shields
returns HTTP 200 with an error body when the route is wrong — the same class
of failure as the broken /github/repos/ badge this tool was written to catch.

Local relative paths (./stats/*.svg, ./profile-3d-contrib/*.svg) are checked
against the working tree on disk.

Exit code 0 = all green, 1 = at least one failure (or no images found).
"""
import argparse
import concurrent.futures as cf
import re
import sys
import urllib.request

README = "README.md"
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
ERROR_PATTERNS = (
    "404: badge not found",
    "404",
    "invalid",
    "not found",
    "rate limit",
    "exceeded",
)
LOCAL_PREFIX = "./"


def extract_urls(text):
    """Return [(url, kind, scheme)] where kind is 'markdown', 'html' or 'srcset'."""
    urls = []
    # markdown images: ![alt](url)
    for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text):
        urls.append((m.group(1).strip(), "markdown"))
    # <img ... src="...">
    for m in re.finditer(r'<img\b[^>]*\bsrc="([^"]+)"', text):
        urls.append((m.group(1).strip(), "html"))
    # <source ... srcset="...">
    for m in re.finditer(r'<source\b[^>]*\bsrcset="([^"]+)"', text):
        for src in m.group(1).split(","):
            urls.append((src.strip(), "srcset"))
    return urls


def check_remote(url):
    """Returns (ok, detail) for one remote URL."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "profile-link-checker"},
        )
        with urllib.request.urlopen(req, timeout=25) as r:
            status = r.status
            ctype = (r.headers.get("Content-Type") or "").lower()
            if not ctype.startswith("image/"):
                return False, f"HTTP {status}, content-type {ctype!r} (not an image)"
            body = r.read(65536).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return False, f"request failed: {e}"

    if "shields.io" in url:
        title = (TITLE_RE.search(body) or [""])[1] if TITLE_RE.search(body) else ""
        if any(p.lower() in title.lower() for p in ERROR_PATTERNS):
            return False, f"shields badge renders error body: {title!r}"
    return True, f"HTTP {status}, image/svg+xml"


def check_url(url, kind):
    if url.startswith("http://") or url.startswith("https://"):
        return url, kind, *check_remote(url)
    if url.startswith(LOCAL_PREFIX):
        try:
            with open(url, "rb"):
                return url, kind, True, "local file exists"
        except OSError as e:
            return url, kind, False, f"local file missing: {e}"
    return url, kind, False, f"unsupported scheme: {url[:40]}"


def main():
    ap = argparse.ArgumentParser(description="Health-check images referenced by README.md")
    ap.add_argument("--readme", default=README)
    ap.add_argument("--timeout", type=int, default=25, help="per-URL timeout, seconds")
    args = ap.parse_args()

    try:
        text = open(args.readme, encoding="utf-8").read()
    except OSError as e:
        print(f"cannot read {args.readme}: {e}")
        return 1

    urls = extract_urls(text)
    if not urls:
        print("no images found in README")
        return 1

    results = []
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        for url, kind in urls:
            results.append(pool.submit(check_url, url, kind))

    failures = 0
    for fut in results:
        url, kind, ok, detail = fut.result()
        mark = "OK " if ok else "FAIL"
        failures += 0 if ok else 1
        print(f"[{mark}] ({kind:7s}) {url[:110]}")
        if not ok:
            print(f"        {detail}")

    print(f"\n{len(urls)} image references, {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
