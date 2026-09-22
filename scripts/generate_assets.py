#!/usr/bin/env python3
"""Generate the hand-built animated SVG art for the profile README.

Outputs (written to ./assets/, dark "tokyonight" + light variants):
  hero.svg / hero-light.svg          - header banner: neon grid, glow title, typed tagline
  terminal.svg / terminal-light.svg  - fake shell session that types itself out
  divider.svg / divider-light.svg    - thin neon rule with a travelling pulse
  footer.svg / footer-light.svg      - closing banner with an equaliser

The content is static, so this needs no network access and no GITHUB_TOKEN. It is
generated rather than hand-written only so the dark and light variants cannot drift
apart. Output is deterministic (fixed RNG seeds) so re-running produces no diff.

Animation is SMIL only: GitHub serves these through <img>, which runs SMIL and
CSS inside the SVG but blocks scripts and external resources (so: no web fonts).
"""
import os
import random

W = 1000
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
CW = 0.61  # monospace advance as a fraction of font-size, rounded up so clips never cut glyphs

THEMES = {
    "": {
        "BG0": "#0b0d17", "BG1": "#1a1b27", "PANEL": "#12131f", "BAR": "#1f2135",
        "GRID": "#2b3163", "TITLE": "#c0caf5", "TEXT": "#a9b1d6", "MUTED": "#565f89",
        "CYAN": "#7dcfff", "PURPLE": "#bb9af7", "GREEN": "#9ece6a", "ORANGE": "#ff9e64",
        "RED": "#f7768e", "STROKE": "#2a2e45",
        "GRID_OP": "0.55", "SCAN_OP": "0.07", "HORIZON_OP": "0.30", "TITLE_GLOW": "0.85",
    },
    "-light": {
        "BG0": "#e9eef6", "BG1": "#ffffff", "PANEL": "#ffffff", "BAR": "#eaeef4",
        "GRID": "#c3cde0", "TITLE": "#1f2328", "TEXT": "#3d444d", "MUTED": "#8c959f",
        "CYAN": "#0969da", "PURPLE": "#8250df", "GREEN": "#1a7f37", "ORANGE": "#bc4c00",
        "RED": "#cf222e", "STROKE": "#d1d9e0",
        "GRID_OP": "0.70", "SCAN_OP": "0.03", "HORIZON_OP": "0.14", "TITLE_GLOW": "0.30",
    },
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, defs, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" fill="none" role="img">\n'
        f'  <defs>\n' + "\n".join(defs) + "\n  </defs>\n" + "\n".join(body) + "\n</svg>\n"
    )


def grid_pattern(t, uid, size=44, dur=9):
    """A scrolling line grid. patternTransform animation degrades to a static grid."""
    return (
        f'    <pattern id="{uid}" width="{size}" height="{size}" patternUnits="userSpaceOnUse">'
        f'<path d="M{size} 0H0V{size}" stroke="{t["GRID"]}" stroke-width="1" '
        f'opacity="{t["GRID_OP"]}"/>'
        f'<animateTransform attributeName="patternTransform" type="translate" '
        f'from="0 0" to="{size} {size}" dur="{dur}s" repeatCount="indefinite"/></pattern>'
    )


def scan_pattern(t, uid):
    return (
        f'    <pattern id="{uid}" width="4" height="4" patternUnits="userSpaceOnUse">'
        f'<rect width="4" height="1.3" fill="{t["TITLE"]}" opacity="{t["SCAN_OP"]}"/></pattern>'
    )


def glow_filter(uid, std):
    return (f'    <filter id="{uid}" x="-70%" y="-70%" width="240%" height="240%">'
            f'<feGaussianBlur stdDeviation="{std}"/></filter>')


def keyframes(total, steps):
    """steps: [(time_seconds, value)]. Returns (values, keyTimes) held discretely."""
    times, vals = [], []
    for at, val in steps:
        frac = min(max(at / total, 0.0), 1.0)
        if times and frac <= times[-1]:
            frac = times[-1] + 1e-5
        times.append(min(frac, 1.0))
        vals.append(val)
    if times[-1] < 1.0:
        times.append(1.0)
        vals.append(vals[-1])
    return (";".join(f"{v}" for v in vals),
            ";".join(f"{t:.5f}" for t in times))


def typed(uid, x, y, s, size, fill, start, total, cps=26, weight="400"):
    """Text revealed character by character by an animated clip.

    Works in Chromium/Firefox/Safari (and therefore GitHub), where <animate> on a
    clipped rect's width runs SMIL. Rasters in highlightjs then linger on the
    revealed state, which is exactly what we want for a screenshot.
    Returns (defs, body)."""
    cw = size * CW
    steps = [(0.0, 0.0), (start, 0.0)]
    for i in range(len(s)):
        steps.append((start + (i + 1) / cps, round(cw * (i + 1), 2)))
    vals, kt = keyframes(total, steps)
    clip = (f'    <clipPath id="{uid}"><rect x="{x:.1f}" y="{y - size:.1f}" '
            f'height="{size * 1.45:.1f}" width="0">'
            f'<animate attributeName="width" values="{vals}" keyTimes="{kt}" '
            f'calcMode="discrete" dur="{total}s" repeatCount="indefinite"/></rect></clipPath>')
    body = (f'  <text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" font-size="{size}" '
            f'fill="{fill}" font-weight="{weight}" clip-path="url(#{uid})" '
            f'xml:space="preserve">{esc(s)}</text>')
    return clip, body


def appear(x, y, s, size, fill, start, total, weight="400", anchor="start", extra=""):
    """Text that pops in whole at `start` and holds for the rest of the loop."""
    vals, kt = keyframes(total, [(0.0, 0), (start, 1)])
    return (f'  <text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" font-size="{size}" '
            f'fill="{fill}" font-weight="{weight}" text-anchor="{anchor}" opacity="0" '
            f'{extra} xml:space="preserve">{esc(s)}'
            f'<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" '
            f'calcMode="discrete" dur="{total}s" repeatCount="indefinite"/></text>')


def caret(x, y, size, fill, start, total, period=1.0):
    """Blinking block cursor that switches on at `start`."""
    vals, kt = keyframes(total, [(0.0, 0), (start, 1)])
    return (f'  <rect x="{x:.1f}" y="{y - size * 0.82:.1f}" width="{size * CW * 0.6:.1f}" '
            f'height="{size:.1f}" fill="{fill}" opacity="0">'
            f'<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" '
            f'calcMode="discrete" dur="{total}s" repeatCount="indefinite"/>'
            f'<animate attributeName="width" values="{size * CW * 0.6:.1f};0" dur="{period}s" '
            f'calcMode="discrete" keyTimes="0;0.5" repeatCount="indefinite"/></rect>')


def centre_x(s, size):
    return W / 2 - len(s) * size * CW / 2


# --------------------------------------------------------------------------- hero

HERO_CMD = "ssh helloe365@github.com"
HERO_TITLE = "hello2world"
HERO_TAG = "Python · AI · LLM · Security"


def hero_svg(t):
    H, total = 280, 14.0
    rnd = random.Random(11)
    defs = [
        f'    <linearGradient id="hbg" x1="0" y1="0" x2="0.35" y2="1">'
        f'<stop offset="0%" stop-color="{t["BG1"]}"/>'
        f'<stop offset="100%" stop-color="{t["BG0"]}"/></linearGradient>',
        grid_pattern(t, "hgrid"),
        scan_pattern(t, "hscan"),
        glow_filter("hglow", 9),
        glow_filter("hsoft", 30),
    ]
    body = [
        f'  <rect width="{W}" height="{H}" rx="14" fill="url(#hbg)"/>',
        f'  <rect width="{W}" height="{H}" rx="14" fill="url(#hgrid)"/>',
        f'  <ellipse cx="500" cy="{H + 16}" rx="430" ry="78" fill="{t["CYAN"]}" '
        f'opacity="{t["HORIZON_OP"]}" filter="url(#hsoft)">'
        f'<animate attributeName="rx" values="430;470;430" dur="7s" '
        f'repeatCount="indefinite"/></ellipse>',
    ]

    for i in range(16):
        px, py = rnd.uniform(40, W - 40), rnd.uniform(50, H - 40)
        r, dur, delay = rnd.uniform(1.0, 2.3), rnd.uniform(5, 11), rnd.uniform(0, 9)
        colour = rnd.choice([t["CYAN"], t["PURPLE"]])
        body.append(
            f'  <circle cx="{px:.0f}" cy="{py:.0f}" r="{r:.1f}" fill="{colour}" opacity="0">'
            f'<animate attributeName="cy" values="{py:.0f};{py - 36:.0f}" dur="{dur:.1f}s" '
            f'begin="-{delay:.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;0.8;0" dur="{dur:.1f}s" '
            f'begin="-{delay:.1f}s" repeatCount="indefinite"/></circle>')

    bracket = 26
    for cx, cy, sx, sy in ((28, 28, 1, 1), (W - 28, 28, -1, 1),
                           (28, H - 28, 1, -1), (W - 28, H - 28, -1, -1)):
        body.append(
            f'  <path d="M{cx} {cy + sy * bracket} V{cy} H{cx + sx * bracket}" '
            f'stroke="{t["PURPLE"]}" stroke-width="2" stroke-linecap="round" opacity="0.55"/>')

    # prompt line
    k_size = 14
    body.append(appear(58, 66, "$", k_size, t["GREEN"], 0.3, total, weight="700"))
    d, b = typed("hcmd", 58 + 2 * k_size * CW, 66, HERO_CMD, k_size, t["TEXT"], 0.45, total, 30)
    defs.append(d)
    body.append(b)

    # title, fading up behind its own glow once the "connection" lands
    tx = centre_x(HERO_TITLE, 54)
    vals, kt = keyframes(total, [(0.0, 0), (2.0, 1)])
    fade = (f'<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" '
            f'calcMode="discrete" dur="{total}s" repeatCount="indefinite"/>')
    body.append(
        f'  <text x="{tx:.1f}" y="166" font-family="{MONO}" font-size="54" font-weight="700" '
        f'fill="{t["CYAN"]}" filter="url(#hglow)" opacity="0">{esc(HERO_TITLE)}{fade}'
        f'<animate attributeName="fill-opacity" values="{t["TITLE_GLOW"]};0.45;'
        f'{t["TITLE_GLOW"]}" dur="4s" repeatCount="indefinite"/></text>')
    body.append(
        f'  <text x="{tx:.1f}" y="166" font-family="{MONO}" font-size="54" font-weight="700" '
        f'fill="{t["TITLE"]}" opacity="0">{esc(HERO_TITLE)}{fade}</text>')

    # typed tagline + caret
    gx = centre_x(HERO_TAG, 19)
    d, b = typed("htag", gx, 212, HERO_TAG, 19, t["PURPLE"], 2.9, total, 22)
    defs.append(d)
    body.append(b)
    body.append(caret(gx + len(HERO_TAG) * 19 * CW + 3, 212, 19, t["CYAN"], 4.4, total))

    body.append(f'  <rect width="{W}" height="{H}" rx="14" fill="url(#hscan)"/>')
    body.append(f'  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" '
                f'stroke="{t["STROKE"]}"/>')
    return svg(W, H, defs, body)


# ----------------------------------------------------------------------- terminal

# (text, colour_key, is_command). Commands type out; output lines land whole.
SESSION = [
    ("whoami", "cmd", True),
    ("hello2world · undergrad @ Hunan University, AI & Robotics", "TEXT", False),
    ("cat ~/focus.md", "cmd", True),
    ("LLM agents · RAG pipelines · data security & privacy", "CYAN", False),
    ("ls ~/ship", "cmd", True),
    ("CrackPDFPassword/   RagAgent/   CupLens/   FraudDetection/", "PURPLE", False),
    ("echo $MOTTO", "cmd", True),
    ('"Stay hungry, Stay foolish."', "ORANGE", False),
]


def terminal_svg(t):
    size, lh, bar = 17, 31, 42
    x0, y0 = 34, 82
    H = y0 + len(SESSION) * lh + 26
    total = 20.0
    defs = [glow_filter("tglow", 6)]
    body = [
        f'  <rect width="{W}" height="{H}" rx="12" fill="{t["PANEL"]}"/>',
        f'  <path d="M0 12a12 12 0 0 1 12-12h{W - 24}a12 12 0 0 1 12 12v{bar - 12}H0z" '
        f'fill="{t["BAR"]}"/>',
    ]
    for i, colour in enumerate((t["RED"], t["ORANGE"], t["GREEN"])):
        body.append(f'  <circle cx="{28 + i * 20}" cy="{bar / 2:.0f}" r="6" fill="{colour}"/>')
    body.append(f'  <text x="{W / 2:.0f}" y="{bar / 2 + 5:.0f}" font-family="{MONO}" '
                f'font-size="13" fill="{t["MUTED"]}" text-anchor="middle">'
                f'helloe365 — zsh — 96×24</text>')

    at = 0.5
    for i, (line, key, is_cmd) in enumerate(SESSION):
        y = y0 + i * lh
        if is_cmd:
            body.append(appear(x0, y, "❯", size, t["GREEN"], at, total, weight="700"))
            d, b = typed(f"tl{i}", x0 + 2 * size * CW, y, line, size, t["TITLE"],
                         at + 0.15, total, 26)
            defs.append(d)
            body.append(b)
            at += 0.35 + len(line) / 26
        else:
            body.append(appear(x0, y, line, size, t[key], at, total))
            at += 0.55
    y = y0 + len(SESSION) * lh
    body.append(appear(x0, y, "❯", size, t["GREEN"], at, total, weight="700"))
    body.append(caret(x0 + 2 * size * CW, y, size, t["CYAN"], at + 0.1, total))

    body.append(f'  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" '
                f'stroke="{t["STROKE"]}"/>')
    return svg(W, H, defs, body)


# ------------------------------------------------------------------ divider/footer

def divider_svg(t):
    H = 18
    defs = [
        f'    <linearGradient id="dl" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{t["CYAN"]}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{t["PURPLE"]}" stop-opacity="0.9"/>'
        f'<stop offset="100%" stop-color="{t["CYAN"]}" stop-opacity="0"/></linearGradient>',
        glow_filter("dg", 4),
    ]
    body = [
        f'  <rect y="{H / 2 - 0.75:.1f}" width="{W}" height="1.5" fill="url(#dl)"/>',
        f'  <circle cy="{H / 2:.0f}" r="4" fill="{t["CYAN"]}" filter="url(#dg)">'
        f'<animate attributeName="cx" values="60;{W - 60};60" dur="7s" '
        f'repeatCount="indefinite"/></circle>',
    ]
    return svg(W, H, defs, body)


def footer_svg(t):
    H = 150
    rnd = random.Random(23)
    defs = [
        f'    <linearGradient id="fbg" x1="0" y1="0" x2="0.3" y2="1">'
        f'<stop offset="0%" stop-color="{t["BG0"]}"/>'
        f'<stop offset="100%" stop-color="{t["BG1"]}"/></linearGradient>',
        grid_pattern(t, "fgrid", 36, 11),
        glow_filter("fglow", 8),
    ]
    body = [
        f'  <rect width="{W}" height="{H}" rx="14" fill="url(#fbg)"/>',
        f'  <rect width="{W}" height="{H}" rx="14" fill="url(#fgrid)"/>',
    ]
    title = "Thanks for visiting!"
    tx = centre_x(title, 26)
    body.append(f'  <text x="{tx:.1f}" y="66" font-family="{MONO}" font-size="26" '
                f'font-weight="700" fill="{t["CYAN"]}" filter="url(#fglow)" '
                f'opacity="{t["TITLE_GLOW"]}">{esc(title)}</text>')
    body.append(f'  <text x="{tx:.1f}" y="66" font-family="{MONO}" font-size="26" '
                f'font-weight="700" fill="{t["TITLE"]}">{esc(title)}</text>')
    body.append(f'  <text x="{W / 2:.0f}" y="94" font-family="{MONO}" font-size="13" '
                f'fill="{t["MUTED"]}" text-anchor="middle">'
                f'a ⭐ on this repo means a lot</text>')

    bottom, bars = H - 16, 46
    for i in range(bars):
        bx = (W - bars * 14) / 2 + i * 14
        peak = rnd.uniform(8, 30)
        dur = rnd.uniform(1.1, 2.3)
        delay = rnd.uniform(0, 2)
        colour = t["PURPLE"] if i % 3 else t["CYAN"]
        hs = f"4;{peak:.0f};10;{peak * 0.6:.0f};4"
        ys = ";".join(f"{bottom - v:.0f}" for v in
                      (4, peak, 10, peak * 0.6, 4))
        body.append(
            f'  <rect x="{bx:.0f}" y="{bottom - 4}" width="6" height="4" rx="2" '
            f'fill="{colour}" opacity="0.7">'
            f'<animate attributeName="height" values="{hs}" dur="{dur:.1f}s" '
            f'begin="-{delay:.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{ys}" dur="{dur:.1f}s" '
            f'begin="-{delay:.1f}s" repeatCount="indefinite"/></rect>')

    body.append(f'  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" '
                f'stroke="{t["STROKE"]}"/>')
    return svg(W, H, defs, body)


BUILDERS = {"hero": hero_svg, "terminal": terminal_svg,
            "divider": divider_svg, "footer": footer_svg}


def main():
    os.makedirs("assets", exist_ok=True)
    for suffix, theme in THEMES.items():
        for name, build in BUILDERS.items():
            path = f"assets/{name}{suffix}.svg"
            markup = build(theme)
            with open(path, "w", encoding="utf-8") as f:
                f.write(markup)
            print(f"wrote {path} ({len(markup)} bytes)")


if __name__ == "__main__":
    main()
