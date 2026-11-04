#!/usr/bin/env python3
"""Check README images, navigation anchors, repository links and contact URLs.

HTTP links must finish with status 200; images must have an image content type.
mailto links are checked for syntax only: this does not verify mail delivery.
--offline checks local files/anchors and explicitly reports remote URLs as skipped.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class References(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img":
            if not attrs.get("alt", "").strip():
                self.errors.append("An <img> is missing meaningful alt text.")
            if attrs.get("src"):
                self.urls.append((attrs["src"], "image"))
        elif tag == "source" and attrs.get("srcset"):
            # URL query commas (skillicons) are not srcset separators.
            for source in re.split(r",\s+", attrs["srcset"]):
                self.urls.append((source.strip().split()[0], "image"))
        elif tag == "a" and attrs.get("href"):
            self.urls.append((attrs["href"], "link"))


def extract_urls(markdown):
    fence = chr(96) * 3
    clean = re.sub(r"<!--.*?-->|" + fence + ".*?" + fence, "", markdown, flags=re.S)
    parser = References()
    parser.feed(clean)
    for match in re.finditer(r"(!?)\[([^\]]*)\]\((<[^>]+>|[^\s)]+)\)", clean):
        image, label, url = match.groups()
        if image and not label.strip():
            parser.errors.append("A Markdown image is missing alt text.")
        parser.urls.append((unescape(url.strip("<>")), "image" if image else "link"))
    return list(dict.fromkeys(parser.urls)), parser.errors


def heading_anchors(markdown):
    anchors, counts = set(), {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", markdown, re.M):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        n = counts.get(slug, 0)
        counts[slug] = n + 1
        anchors.add(slug if not n else f"{slug}-{n}")
    return anchors


def validate_svg(body, url):
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        return False, f"Invalid SVG: {exc}"
    if root.tag.rsplit("}", 1)[-1] != "svg":
        return False, "Not an SVG root element."
    if "shields.io" in url:
        title = root.findtext("{http://www.w3.org/2000/svg}title", default="")
        if re.search(r"\b(404|invalid|not found|rate limit|exceeded)\b", title, re.I):
            return False, f"Badge contains an error: {title}"
        logo = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).get("logo")
        if logo and not any(e.tag.rsplit("}", 1)[-1] == "image" for e in root.iter()):
            return False, f"Badge logo {logo[0]!r} is missing."
    return True, "Valid SVG"


def check_remote(url, kind, timeout):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 profile-link-checker"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = response.status
                content_type = response.headers.get("Content-Type", "").lower()
                if status != 200:
                    return False, f"HTTP {status}, expected 200"
                if kind == "image":
                    if not content_type.startswith("image/"):
                        return False, f"HTTP 200 but not an image: {content_type}"
                    if "svg" in content_type:
                        ok, detail = validate_svg(response.read(), url)
                        if not ok:
                            return False, detail
            return True, f"HTTP 200 ({content_type})"
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                return False, f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            if attempt == 2:
                return False, str(exc)
        time.sleep(attempt + 1)
    return False, "Request failed"


def check_url(url, kind, root, anchors, timeout=20, offline=False):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme in ("https", "http"):
        if offline:
            return "SKIP", "Remote URL (--offline)"
        ok, detail = check_remote(url, kind, timeout)
        return ("OK" if ok else "FAIL"), detail
    if parts.scheme == "mailto":
        ok = bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", urllib.parse.unquote(parts.path)))
        return ("OK" if ok else "FAIL"), "Email syntax only; delivery not tested"
    if parts.scheme:
        return "FAIL", f"Unsupported scheme: {parts.scheme}"
    if not parts.path:
        ok = urllib.parse.unquote(parts.fragment) in anchors
        return ("OK" if ok else "FAIL"), "README heading anchor"
    path = (root / urllib.parse.unquote(parts.path)).resolve()
    if not path.is_file():
        return "FAIL", f"Missing local file: {parts.path}"
    if kind == "image" and path.suffix.lower() == ".svg":
        ok, detail = validate_svg(path.read_bytes(), str(path))
        if not ok:
            return "FAIL", detail
    if parts.fragment and path.suffix.lower() == ".md":
        if urllib.parse.unquote(parts.fragment) not in heading_anchors(path.read_text(encoding="utf-8")):
            return "FAIL", f"Missing heading in {parts.path}"
    return "OK", "Local file exists"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readme", type=Path, default=ROOT / "README.md")
    parser.add_argument("--timeout", type=float, default=20, help="Timeout per HTTP attempt, seconds")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        markdown = args.readme.read_text(encoding="utf-8")
    except OSError as exc:
        print(exc)
        return 1
    urls, errors = extract_urls(markdown)
    if not urls:
        errors.append("No references found in README.")
    anchors = heading_anchors(markdown)

    def check(item):
        return check_url(*item, args.readme.resolve().parent, anchors, args.timeout, args.offline)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, urls))
    for (url, _), (status, detail) in zip(urls, results):
        print(f"[{status}] {url}\n       {detail}")
    for error in errors:
        print(f"[FAIL] {error}")
    failures = sum(status == "FAIL" for status, _ in results) + len(errors)
    skipped = sum(status == "SKIP" for status, _ in results)
    print(f"\n{len(urls)} unique references; {failures} failures; {skipped} skipped.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
