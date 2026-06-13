#!/usr/bin/env python3
import argparse
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont


HOME = Path.home()
APP_DIR = HOME / ".codex/projects/daily-report/app"
DATA_DIR = HOME / "Library/Application Support/Codex Daily Report"
JST = ZoneInfo("Asia/Tokyo")
DAILY_DIR = HOME / "Library/Mobile Documents/iCloud~md~obsidian/Documents/DAILY/90_DailyMemo"
OUT_DIR = DATA_DIR / "images"
START_MARKER = "<!-- daily-report:start -->"
END_MARKER = "<!-- daily-report:end -->"
FONT_REGULAR = Path("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc")
FONT_BOLD = Path("/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc")


def font(size: int, bold: bool = False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size=size)


def extract_report(markdown: str) -> str:
    if START_MARKER in markdown and END_MARKER in markdown:
        return markdown.split(START_MARKER, 1)[1].split(END_MARKER, 1)[0]
    return markdown


def section(report: str, heading: str) -> str:
    pattern = rf"### {re.escape(heading)}\n(.*?)(?=\n### |\Z)"
    match = re.search(pattern, report, re.S)
    return match.group(1).strip() if match else ""


def bullets(text: str) -> list[str]:
    return [line[2:].strip() for line in text.splitlines() if line.startswith("- ")]


def parse_table(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or cells[0] in {"分類", "動画", "ブックマーク"}:
            headers = cells
            continue
        if len(cells) >= 4:
            rows.append({"a": clean_link(cells[0]), "b": clean_link(cells[1]), "c": clean_link(cells[2]), "d": clean_link(cells[3])})
        elif len(cells) >= 3:
            rows.append({"a": clean_link(cells[0]), "b": clean_link(cells[1]), "c": clean_link(cells[2]), "d": ""})
    return rows


def clean_link(value: str) -> str:
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("\\|", "|")
    return re.sub(r"\s+", " ", value).strip()


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, width: int, max_lines: int = 3) -> list[str]:
    words = list(text)
    lines = []
    current = ""
    for ch in words:
        trial = current + ch
        if draw.textlength(trial, font=fnt) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and draw.textlength(lines[-1], font=fnt) > width - draw.textlength("…", font=fnt):
        while lines[-1] and draw.textlength(lines[-1] + "…", font=fnt) > width:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return lines


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_text_block(draw, x, y, title, body_lines, accent, max_width):
    title_font = font(30, True)
    body_font = font(22)
    small_font = font(18)
    card_h = 42 + sum(28 * len(wrap(draw, line, body_font, max_width - 56, 2)) + 8 for line in body_lines) + 28
    rounded(draw, (x, y, x + max_width, y + card_h), 22, "#111827", "#243244", 1)
    draw.rounded_rectangle((x + 22, y + 24, x + 34, y + 58), radius=6, fill=accent)
    draw.text((x + 48, y + 20), title, fill="#f8fafc", font=title_font)
    cy = y + 70
    for line in body_lines:
        for wrapped in wrap(draw, line, body_font, max_width - 56, 2):
            draw.text((x + 28, cy), wrapped, fill="#d7dee9", font=body_font)
            cy += 28
        cy += 8
    return card_h


def draw_item(draw, x, y, w, label, title, summary, source, accent):
    title_font = font(23, True)
    body_font = font(18)
    meta_font = font(16)
    rounded(draw, (x, y, x + w, y + 146), 18, "#0f172a", "#27364a", 1)
    draw.rounded_rectangle((x + 18, y + 18, x + 120, y + 44), radius=10, fill=accent)
    draw.text((x + 28, y + 20), label[:12], fill="#07111f", font=meta_font)
    tx = x + 18
    cy = y + 54
    for line in wrap(draw, title, title_font, w - 36, 2):
        draw.text((tx, cy), line, fill="#f8fafc", font=title_font)
        cy += 28
    cy += 4
    for line in wrap(draw, summary, body_font, w - 36, 2):
        draw.text((tx, cy), line, fill="#c7d2e0", font=body_font)
        cy += 23
    draw.text((tx, y + 120), source[:38], fill="#8ea0b8", font=meta_font)


def render(note_path: Path, out_path: Path) -> None:
    report = extract_report(note_path.read_text(encoding="utf-8"))
    summary = bullets(section(report, "全体サマリー"))
    memo = section(report, "Obsidianメモ要約").splitlines()[0:2]
    rss = parse_table(section(report, "RSS 選抜10件"))[:10]
    youtube_section = section(report, "YouTube お気に入り") or section(report, "YouTube 高評価")
    youtube = parse_table(youtube_section)[:4]
    raindrop = parse_table(section(report, "Raindrop"))[:5]

    width = 1600
    height = 2200
    img = Image.new("RGB", (width, height), "#07111f")
    draw = ImageDraw.Draw(img)

    # Background bands
    draw.rectangle((0, 0, width, 520), fill="#0b1b2f")
    draw.ellipse((1100, -220, 1800, 520), fill="#123b4a")
    draw.ellipse((-240, 120, 520, 780), fill="#111f3f")

    title_font = font(58, True)
    subtitle_font = font(24)
    draw.text((70, 58), "Daily Report", fill="#f8fafc", font=title_font)
    draw.text((74, 132), datetime.now(JST).strftime("%Y.%m.%d"), fill="#9fb0c7", font=subtitle_font)

    y = 190
    y += draw_text_block(draw, 70, y, "全体サマリー", summary[:3], "#5eead4", 1460) + 26
    if memo:
        y += draw_text_block(draw, 70, y, "Obsidianメモ", memo, "#fbbf24", 1460) + 38

    section_font = font(34, True)
    draw.text((70, y), "RSS Picks", fill="#f8fafc", font=section_font)
    y += 52
    col_w = 710
    gap = 40
    for idx, row in enumerate(rss):
        x = 70 + (idx % 2) * (col_w + gap)
        iy = y + (idx // 2) * 166
        draw_item(draw, x, iy, col_w, row["a"], row["b"], row["c"], row["d"], "#93c5fd")
    y += ((len(rss) + 1) // 2) * 166 + 52

    draw.text((70, y), "YouTube / Raindrop", fill="#f8fafc", font=section_font)
    y += 52
    for idx, row in enumerate(youtube[:4]):
        x = 70 + (idx % 2) * (col_w + gap)
        iy = y + (idx // 2) * 166
        draw_item(draw, x, iy, col_w, "YouTube", row["a"], row["c"], row["b"], "#fca5a5")
    y += 2 * 166 + 24
    for idx, row in enumerate(raindrop[:4]):
        x = 70 + (idx % 2) * (col_w + gap)
        iy = y + (idx // 2) * 166
        draw_item(draw, x, iy, col_w, "Raindrop", row["a"], row["c"], row["b"], "#86efac")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)


def main():
    parser = argparse.ArgumentParser()
    today = datetime.now(JST).strftime("%Y-%m-%d")
    parser.add_argument("--date", default=today)
    parser.add_argument("--out", type=Path, default=OUT_DIR / f"daily-report-card-{today}.png")
    args = parser.parse_args()
    render(DAILY_DIR / f"{args.date}.md", args.out)
    print(args.out)


if __name__ == "__main__":
    main()
