#!/usr/bin/env python3
import argparse
import csv
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser


HOME = Path.home()
DEFAULT_OPML = HOME / ".config/inoreader/Inoreader Feeds 20260528.xml"
DEFAULT_OUTPUT_DIR = HOME / ".codex/projects/daily-report/inoreader-opml/output"
TAG_RE = re.compile(r"<[^>]+>")


def parse_feeds(opml_path: Path) -> list[dict]:
    root = ET.parse(opml_path).getroot()
    feeds = []
    for outline in root.iter("outline"):
        url = outline.attrib.get("xmlUrl")
        if not url:
            continue
        feeds.append(
            {
                "title": outline.attrib.get("title") or outline.attrib.get("text") or url,
                "url": url,
                "html_url": outline.attrib.get("htmlUrl", ""),
            }
        )
    return feeds


def entry_datetime(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime.fromtimestamp(time.mktime(value), timezone.utc)
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if value:
            try:
                dt = parsedate_to_datetime(value)
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
    return None


def clean_html(value: str) -> str:
    value = TAG_RE.sub(" ", value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def fetch_recent(feeds: list[dict], cutoff: datetime) -> list[dict]:
    rows = []
    for feed in feeds:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries:
            dt = entry_datetime(entry)
            if not dt or dt < cutoff:
                continue
            summary = clean_html(entry.get("summary", "") or entry.get("description", ""))
            rows.append(
                {
                    "feed_title": feed["title"],
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published_at": dt.isoformat(),
                    "summary": summary,
                }
            )
    rows.sort(key=lambda row: row["published_at"], reverse=True)
    return rows


def score(row: dict) -> tuple[int, list[str]]:
    text = f"{row['feed_title']} {row['title']} {row['summary']}".lower()
    rules = [
        (5, "music", ["music", "音楽", "dtm", "plugin", "プラグイン", "synth", "mix", "ミックス", "vocal", "ableton"]),
        (5, "product", ["product", "プロダクト", "ui", "ux", "saas", "app", "アプリ", "design", "デザイン"]),
        (4, "business", ["business", "投資", "不動産", "経済", "startup", "スタートアップ", "ai", "生成ai"]),
        (4, "soccer", ["soccer", "サッカー", "w杯", "world cup"]),
        (3, "culture", ["fashion", "映画", "アニメ", "ゲーム", "gadget", "ギズモード", "ign"]),
        (2, "news", ["速報", "発表", "開始", "発売", "新機能"]),
    ]
    total = 0
    labels = []
    for points, label, keywords in rules:
        if any(keyword in text for keyword in keywords):
            total += points
            labels.append(label)
    return total, labels


def write_outputs(rows: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        row["score"], row["labels"] = score(row)

    (output_dir / "recent_feed_items.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (output_dir / "recent_feed_items.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["published_at", "feed_title", "title", "url", "score", "labels", "summary"],
        )
        writer.writeheader()
        writer.writerows(rows)

    picks = [row for row in rows if row["score"] > 0]
    picks.sort(key=lambda row: (row["score"], row["published_at"]), reverse=True)
    lines = ["# Recent Inoreader OPML Picks", ""]
    for row in picks[:30]:
        labels = ", ".join(row["labels"])
        lines.append(f"- ({row['score']} / {labels}) [{row['title']}]({row['url']}) - {row['feed_title']}")
    (output_dir / "recommended.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Fetched recent items: {len(rows)}")
    print(f"Recommended items: {len(picks)}")
    print(f"JSON: {output_dir / 'recent_feed_items.json'}")
    print(f"CSV:  {output_dir / 'recent_feed_items.csv'}")
    print(f"MD:   {output_dir / 'recommended.md'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--opml", type=Path, default=DEFAULT_OPML)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    rows = fetch_recent(parse_feeds(args.opml), cutoff)
    write_outputs(rows, args.output_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Inoreader OPML fetch failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
