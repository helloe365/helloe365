#!/usr/bin/env python3
"""Generate profile illustrations, offline and byte-for-byte reproducibly."""
import argparse
from html import escape
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FONT = '-apple-system, "Segoe UI", Roboto, sans-serif'
W = 720
RADIUS = 12

# Shared with generate_stats.py: cyan = links, purple = skills, green = results.
# Light accents are darker than #2f9bc4 so small text also passes 4.5:1.
THEMES = {
    "": {
        "BG": "#0b0d17", "CARD": "#1a1b27", "BORDER": "#2a2e45",
        "TEXT": "#c0caf5", "MUTED": "#a9b1d6", "CYAN": "#7dcfff",
        "PURPLE": "#bb9af7", "GREEN": "#9ece6a",
    },
    "-light": {
        "BG": "#f7f9fc", "CARD": "#ffffff", "BORDER": "#e3e8f0",
        "TEXT": "#1a2233", "MUTED": "#5c6b84", "CYAN": "#217594",
        "PURPLE": "#7256a8", "GREEN": "#48752c",
    },
}


def text(x, y, content, size, fill, weight=400, anchor="start", label=False):
    tracking = ' letter-spacing="0.08em"' if label else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{tracking}>'
            f'{escape(str(content))}</text>')


def svg(w, h, body, theme, title, description="", surface="CARD"):
    """No external resources, CSS, IDs, scripts, or delayed essential text."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" fill="none" role="img" '
        f'font-family="{escape(FONT, quote=True)}">\n'
        f'<title>{escape(title)}</title>\n<desc>{escape(description)}</desc>\n'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" '
        f'rx="{RADIUS}" fill="{theme[surface]}" '
        f'stroke="{theme["BORDER"]}" stroke-width="1"/>\n'
        + "\n".join(body) + "\n</svg>\n"
    )


def hero_svg(t):
    body = [
        # Layered translucent shapes give the circuit a glow without filters/IDs.
        f'<circle cx="620" cy="116" r="100" fill="{t["CYAN"]}" opacity="0.025"/>',
        f'<circle cx="620" cy="116" r="76" fill="{t["CYAN"]}" opacity="0.035"/>',
        f'<circle cx="660" cy="168" r="48" fill="{t["PURPLE"]}" opacity="0.045"/>',
        f'<path d="M16 44V16h28m632 0h28v28M16 184v28h28m632 0h28v-28" '
        f'stroke="{t["CYAN"]}" stroke-width="1" opacity="0.55"/>',
        text(32, 40, "HELLOE365 / GRADUATE STUDENT", 16, t["PURPLE"], label=True),
        text(32, 100, "hello2world", 44, t["TEXT"], 700),
        f'<path d="M32 116h96m8 0h40m8 0h16" '
        f'stroke="{t["CYAN"]}" stroke-width="1"/>',
        text(32, 148, "构建可追溯的 AI 工具", 16, t["CYAN"], 600),
        text(32, 184, "湖南大学 · 硕士研究生在读", 16, t["TEXT"], 600),
        text(32, 208, "人工智能与机器人方向 · 长沙", 16, t["MUTED"]),
    ]
    # Small finite SMIL motion: never delay text or keep a background loop running.
    for i, label in enumerate(("SOURCE", "RETRIEVE", "ANSWER")):
        y = 44 + i * 56
        body.append(f'<rect x="548" y="{y - 4}" width="144" height="44" rx="12" '
                    f'stroke="{t["CYAN"]}" stroke-width="1" opacity="0.14">'
                    '<animate attributeName="opacity" values="0.14;0.6;0.14" '
                    f'begin="{i * 0.8}s" dur="2s" repeatCount="1" fill="freeze"/></rect>')
        body.append(f'<rect x="552" y="{y}" width="136" height="36" rx="12" '
                    f'fill="{t["CARD"]}" stroke="{t["CYAN"]}" stroke-opacity="0.5" stroke-width="1"/>')
        body.append(text(620, y + 24, label, 16, t["CYAN"], 500, "middle", True))
        if i < 2:
            body.append(f'<path d="M620 {y + 36}v20m-4-4 4 4 4-4" '
                        f'stroke="{t["PURPLE"]}" stroke-width="1"/>')
            body.append(f'<circle cx="620" cy="{y + 40}" r="3" fill="{t["CYAN"]}" opacity="0">'
                        '<animate attributeName="opacity" values="0;1;1;0" '
                        f'begin="{0.4 + i * 0.8:.1f}s" dur="1.6s" repeatCount="1" fill="freeze"/>'
                        '<animate attributeName="cy" '
                        f'from="{y + 40}" to="{y + 52}" begin="{0.4 + i * 0.8:.1f}s" '
                        'dur="1.6s" repeatCount="1" fill="freeze"/></circle>')
    return svg(W, 228, body, t, "hello2world / helloe365",
               "湖南大学硕士研究生在读，人工智能与机器人方向，长沙。构建可追溯的 AI 工具。", "BG")


def terminal_svg(t):
    body = [
        text(24, 28, "helloe365 / about", 16, t["MUTED"]),
        f'<path d="M1 44h718" stroke="{t["BORDER"]}" stroke-width="1"/>',
        text(24, 76, "$ whoami", 16, t["CYAN"], 600),
        text(24, 100, "hello2world · Hunan University · Master's Student", 16, t["TEXT"]),
        text(24, 140, "$ cat focus", 16, t["CYAN"], 600),
        text(24, 164, "可追溯的 AI 应用 / 可复现的工程流程", 16, t["TEXT"]),
        text(24, 204, "$ pwd", 16, t["CYAN"], 600),
        text(24, 228, "Changsha, China", 16, t["TEXT"]),
        # Three quiet blinks, then a static cursor; all content is present at t=0.
        f'<rect x="156" y="216" width="8" height="16" fill="{t["PURPLE"]}">'
        '<animate attributeName="opacity" values="1;0;1" dur="1.5s" '
        'repeatCount="3" fill="freeze"/></rect>',
    ]
    return svg(W, 252, body, t, "About hello2world",
               "湖南大学人工智能与机器人方向硕士研究生在读，长沙；关注可追溯的 AI 应用与可复现的工程流程。")


def contributions_toggle_svg(t):
    """A full-width summary label; its title stays readable when scaled down."""
    return svg(600, 96, [
        f'<path d="M16 24v48" stroke="{t["CYAN"]}" stroke-width="1"/>',
        text(32, 43, "展开贡献轨迹与里程碑", 32, t["CYAN"], 700),
        text(32, 73, "CONTRIBUTIONS / ACTIVITY / MILESTONES", 16, t["MUTED"]),
        f'<circle cx="548" cy="48" r="24" fill="{t["CYAN"]}" opacity="0.08"/>',
        f'<circle cx="548" cy="48" r="24" stroke="{t["CYAN"]}" stroke-width="1"/>',
        f'<path d="m538 44 10 10 10-10" stroke="{t["CYAN"]}" stroke-width="1"/>',
    ], t, "展开贡献轨迹与里程碑", "点击展开或收起 3D 贡献图、每周活动、开源里程碑和贡献贪吃蛇。")


def divider_svg(t):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 24" '
            f'width="{W}" height="24" role="img">\n<title>Section divider</title>\n'
            f'<path d="M0 12h{W}" fill="none" stroke="{t["BORDER"]}" '
            'stroke-width="1"/>\n</svg>\n')


def footer_svg(t):
    return svg(W, 96, [
        text(32, 44, "Build. Verify. Share.", 28, t["TEXT"], 600),
        text(32, 72, "hello2world / helloe365", 16, t["CYAN"]),
    ], t, "Build. Verify. Share.", "构建、验证、分享。", "BG")


BUILDERS = {"hero": hero_svg, "terminal": terminal_svg,
            "divider": divider_svg, "footer": footer_svg,
            "contributions-toggle": contributions_toggle_svg}


def contribution_settings():
    """Configure the existing 3D Action from the same Tokyo Night palette."""
    settings = []
    for suffix, theme in THEMES.items():
        start, end = theme["CARD"], theme["GREEN"]
        colors = []
        for fraction in (0, 0.25, 0.5, 0.75, 1):
            rgb = [round(int(start[i:i + 2], 16) * (1 - fraction)
                         + int(end[i:i + 2], 16) * fraction) for i in (1, 3, 5)]
            colors.append("#" + "".join(f"{c:02x}" for c in rgb))
        settings.append({
            "type": "normal",
            "fileName": "profile-season-animate.svg" if suffix else "profile-night-rainbow.svg",
            "backgroundColor": theme["CARD"], "foregroundColor": theme["MUTED"],
            "strongColor": theme["TEXT"], "weakColor": theme["MUTED"],
            "radarColor": theme["GREEN"], "growingAnimation": False,
            "contribColors": colors,
        })
    return settings


def style_contribution_svg(path, theme):
    """Keep the existing Action's geometry/data; inline styles and theme its legend."""
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    root = ET.fromstring(path.read_bytes())
    rules = {}
    for element in list(root):
        if element.tag.endswith("}style"):
            for name, declarations in re.findall(r"\.([\w-]+)\s*\{([^}]+)\}", element.text or ""):
                rules[name] = dict(part.strip().split(":", 1) for part in declarations.split(";") if ":" in part)
            root.remove(element)
    for element in root.iter():
        declarations = {}
        for name in element.attrib.pop("class", "").split():
            declarations.update(rules.get(name, {}))
        declarations.update(dict(part.strip().split(":", 1) for part in element.attrib.pop("style", "").split(";") if ":" in part))
        for key, value in declarations.items():
            element.set(key.strip(), value.strip())
        if "font-family" in element.attrib:
            element.set("font-family", FONT)
    # Limit recoloring to the upstream language panel; contribution tiles are
    # also small rectangles and must retain their green intensity encoding.
    legend = root.find('{http://www.w3.org/2000/svg}g[@transform="translate(40, 520)"]')
    if legend is None:
        raise ValueError("The upstream 3D language panel has changed; inspect before styling.")
    swatches = [e for e in legend.iter() if e.tag.endswith("}rect")
                and "fill" in e.attrib and float(e.get("width", "0")) < 40]
    old_colors = list(dict.fromkeys(e.get("fill") for e in swatches))
    color_map = {}
    for i, color in enumerate(old_colors):
        fraction = max(0.35, 1 - i * 0.2)
        rgb = [round(int(theme["CARD"][j:j + 2], 16) * (1 - fraction)
                     + int(theme["PURPLE"][j:j + 2], 16) * fraction) for j in (1, 3, 5)]
        color_map[color] = "#" + "".join(f"{c:02x}" for c in rgb)
    for element in legend.iter():
        if element.get("fill") in color_map:
            element.set("fill", color_map[element.get("fill")])
    root.set("font-family", FONT)
    root.set("role", "img")
    background = next(e for e in root if e.tag.endswith("}rect"))
    for key, value in {"x": "0.5", "y": "0.5", "width": "1279", "height": "849",
                       "rx": str(RADIUS), "stroke": theme["BORDER"], "stroke-width": "1"}.items():
        background.set(key, value)
    path.write_bytes(ET.tostring(root, encoding="utf-8") + b"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--style-contrib", action="store_true",
                        help="Apply the shared theme after the existing 3D Action runs.")
    args = parser.parse_args()
    output = ROOT / "assets"
    output.mkdir(exist_ok=True)
    for suffix, theme in THEMES.items():
        for name, build in BUILDERS.items():
            path = output / f"{name}{suffix}.svg"
            path.write_bytes(build(theme).encode("utf-8"))
            print(f"wrote {path.relative_to(ROOT)}")
    settings = ROOT / ".github" / "profile-3d-settings.json"
    settings.parent.mkdir(exist_ok=True)
    settings.write_bytes((json.dumps(contribution_settings(), indent=2) + "\n").encode("utf-8"))
    if args.style_contrib:
        for suffix, name in (("", "profile-night-rainbow.svg"), ("-light", "profile-season-animate.svg")):
            style_contribution_svg(ROOT / "profile-3d-contrib" / name, THEMES[suffix])


if __name__ == "__main__":
    main()
