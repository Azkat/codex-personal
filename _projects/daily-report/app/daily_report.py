#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo


HOME = Path.home()
PROJECT_ROOT = HOME / ".codex/projects/daily-report"
APP_DIR = PROJECT_ROOT / "app"
JST = ZoneInfo("Asia/Tokyo")
VAULT = HOME / "Library/Mobile Documents/iCloud~md~obsidian/Documents/DAILY"
DAILY_DIR = VAULT / "90_DailyMemo"
YOUTUBE_DIR = PROJECT_ROOT / "youtube-liked-videos"
YOUTUBE_SCRIPT = YOUTUBE_DIR / "fetch_liked_videos.py"
YOUTUBE_PYTHON = YOUTUBE_DIR / ".venv/bin/python"
YOUTUBE_JSON = YOUTUBE_DIR / "output/liked_videos.json"
RSS_DIR = PROJECT_ROOT / "inoreader-opml"
RSS_SCRIPT = RSS_DIR / "fetch_recent_feeds.py"
RSS_PYTHON = RSS_DIR / ".venv/bin/python"
RSS_BASE_OPML = HOME / ".config/inoreader/Inoreader Feeds 20260528.xml"
RSS_ADDITIONAL_OPML = HOME / ".config/inoreader/additional_feeds_20260528.xml"
RSS_OUTPUT = RSS_DIR / "output/daily-report"
RAINDROP_TOKEN_FILE = HOME / ".config/raindrop/token.txt"
SLACK_WEBHOOKS_FILE = HOME / ".config/slack/webhooks"
OPENAI_KEY_FILE = HOME / ".config/openai/api_key.txt"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
CODEX_CLI = Path(os.environ.get("CODEX_CLI", str(HOME / ".local/bin/codex")))
CODEX_DISABLED = False
START_MARKER = "<!-- daily-report:start -->"
END_MARKER = "<!-- daily-report:end -->"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)


def python_command(venv_python: Path) -> str:
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def command_error_summary(exc: Exception) -> str:
    if isinstance(exc, subprocess.CalledProcessError):
        detail = (exc.stderr or "").strip().splitlines()
        suffix = f": {detail[-1]}" if detail else ""
        return f"exit code {exc.returncode}{suffix}"
    return str(exc)


def parse_dt(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def read_key_value_file(path: Path) -> dict:
    if not path.exists():
        return {}
    values = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def jst_stamp(value: str) -> str:
    dt = parse_dt(value)
    if not dt:
        return ""
    return dt.astimezone(JST).strftime("%H:%M")


def strip_existing_report(note_text: str) -> str:
    if START_MARKER in note_text and END_MARKER in note_text:
        before = note_text.split(START_MARKER, 1)[0]
        after = note_text.split(END_MARKER, 1)[1]
        return before + "\n" + after
    return note_text


def md_link(title: str, url: str) -> str:
    clean = (title or "Untitled").replace("[", "\\[").replace("]", "\\]")
    return f"[{clean}]({url})" if url else clean


def table_cell(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    return value.replace("|", "\\|")


def truncate(value: str, limit: int = 120) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def is_mostly_english(value: str) -> bool:
    letters = [char for char in value if char.isalpha()]
    if not letters:
        return False
    ascii_letters = [char for char in letters if ord(char) < 128]
    return len(ascii_letters) / len(letters) > 0.8


def read_openai_key() -> str:
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"].strip()
    if OPENAI_KEY_FILE.exists():
        raw = OPENAI_KEY_FILE.read_text(encoding="utf-8").strip()
        if "=" in raw:
            raw = raw.split("=", 1)[1].strip().strip('"').strip("'")
        return raw
    return ""


def llm_json(prompt: str, fallback: dict) -> dict:
    codex_result = codex_json(prompt)
    if codex_result is not None:
        return codex_result
    return openai_json(prompt, fallback)


def codex_json(prompt: str) -> Optional[dict]:
    global CODEX_DISABLED
    if CODEX_DISABLED or not CODEX_CLI.exists():
        return None
    with tempfile.NamedTemporaryFile(prefix="daily-report-codex-", suffix=".json", delete=False) as tmp:
        output_path = Path(tmp.name)
    command = [
        str(CODEX_CLI),
        "--ask-for-approval",
        "never",
        "--sandbox",
        "read-only",
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "-o",
        str(output_path),
        prompt,
    ]
    try:
        subprocess.run(
            command,
            check=True,
            cwd=str(HOME),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180,
        )
        text = output_path.read_text(encoding="utf-8").strip()
        return parse_json_object(text)
    except Exception as exc:
        print(f"Codex enrichment skipped: {command_error_summary(exc)}", file=sys.stderr)
        CODEX_DISABLED = True
        return None
    finally:
        try:
            output_path.unlink()
        except OSError:
            pass


def parse_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def openai_json(prompt: str, fallback: dict) -> dict:
    key = read_openai_key()
    if not key:
        return fallback
    payload = {
        "model": OPENAI_MODEL,
        "input": prompt,
        "text": {"format": {"type": "json_object"}},
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = ""
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text += content.get("text", "")
        return json.loads(text) if text else fallback
    except Exception as exc:
        print(f"OpenAI enrichment skipped: {exc}", file=sys.stderr)
        return fallback


def fetch_youtube(cutoff: datetime) -> list[dict]:
    try:
        run([python_command(YOUTUBE_PYTHON), str(YOUTUBE_SCRIPT)])
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"YouTube fetch skipped: {command_error_summary(exc)}", file=sys.stderr)
        return []
    if not YOUTUBE_JSON.exists():
        return []
    rows = json.loads(YOUTUBE_JSON.read_text(encoding="utf-8"))
    recent = []
    for row in rows:
        dt = parse_dt(row.get("liked_playlist_added_at", ""))
        if dt and dt >= cutoff:
            recent.append(row)
    recent.sort(key=lambda r: r.get("liked_playlist_added_at", ""), reverse=True)
    return recent


def fetch_rss(cutoff_hours: int) -> list[dict]:
    if not RSS_BASE_OPML.exists():
        print(f"RSS fetch skipped: OPML is not configured: {RSS_BASE_OPML}", file=sys.stderr)
        return []
    base_dir = RSS_OUTPUT / "base"
    additional_dir = RSS_OUTPUT / "additional"
    python = python_command(RSS_PYTHON)
    try:
        run([python, str(RSS_SCRIPT), "--opml", str(RSS_BASE_OPML), "--output-dir", str(base_dir), "--hours", str(cutoff_hours)])
        if RSS_ADDITIONAL_OPML.exists():
            run([python, str(RSS_SCRIPT), "--opml", str(RSS_ADDITIONAL_OPML), "--output-dir", str(additional_dir), "--hours", str(cutoff_hours)])
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"RSS fetch skipped: {command_error_summary(exc)}", file=sys.stderr)
        return []

    rows = []
    for path in [base_dir / "recent_feed_items.json", additional_dir / "recent_feed_items.json"]:
        if path.exists():
            rows.extend(json.loads(path.read_text(encoding="utf-8")))

    seen = {}
    for row in rows:
        url = row.get("url", "")
        if url and url not in seen:
            row["daily_score"], row["daily_labels"] = score_item(row)
            seen[url] = row
    rows = list(seen.values())
    rows.sort(key=lambda r: (r["daily_score"], r.get("published_at", "")), reverse=True)
    return rows


def fetch_raindrop(cutoff: datetime) -> tuple[list[dict], Optional[str]]:
    token = os.environ.get("RAINDROP_TOKEN", "")
    if not token and RAINDROP_TOKEN_FILE.exists():
        token = RAINDROP_TOKEN_FILE.read_text(encoding="utf-8").strip()
        if "=" in token:
            _, token = token.split("=", 1)
            token = token.strip().strip('"').strip("'")
    if not token:
        return [], f"Raindrop token is not configured: {RAINDROP_TOKEN_FILE}"

    rows = []
    page = 0
    while page < 5:
        query = urllib.parse.urlencode({"page": page, "perpage": 50, "sort": "-created"})
        request = urllib.request.Request(
            f"https://api.raindrop.io/rest/v1/raindrops/0?{query}",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        items = payload.get("items", [])
        if not items:
            break
        stop = False
        for item in items:
            dt = parse_dt(item.get("created", ""))
            if not dt:
                continue
            if dt < cutoff:
                stop = True
                continue
            rows.append(item)
        if stop:
            break
        page += 1
    rows.sort(key=lambda r: r.get("created", ""), reverse=True)
    return rows, None


def score_item(row: dict) -> tuple[int, list[str]]:
    text = " ".join(
        [
            row.get("feed_title", ""),
            row.get("title", ""),
            row.get("summary", ""),
        ]
    ).lower()
    rules = [
        (8, "AI/Product", ["ai", "agent", "agents", "llm", "openai", "anthropic", "生成ai", "プロダクト", "product", "ux", "design", "figma"]),
        (7, "Business", ["business", "startup", "saas", "strategy", "growth", "投資", "経済", "事業", "不動産", "ipo"]),
        (7, "Music", ["music", "音楽", "dtm", "plugin", "プラグイン", "synth", "mix", "ミックス", "kick", "bass", "ableton", "producer"]),
        (6, "Football", ["football", "soccer", "サッカー", "w杯", "world cup", "fifa", "代表"]),
        (5, "Interesting", ["weird", "fun", "culture", "art", "おもしろ", "togetter", "atlas obscura", "kottke"]),
        (2, "News", ["発表", "開始", "発売", "new", "launch", "report"]),
    ]
    score = 0
    labels = []
    for points, label, keywords in rules:
        if any(keyword_matches(text, keyword) for keyword in keywords):
            score += points
            labels.append(label)
    return score, labels


def keyword_matches(text: str, keyword: str) -> bool:
    if any(ord(char) > 127 for char in keyword) or " " in keyword:
        return keyword in text
    return re_search_word(keyword, text)


def re_search_word(keyword: str, text: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text) is not None


def balanced_rss_picks(rows: list[dict], limit: int = 10) -> list[dict]:
    buckets = ["AI/Product", "Business", "Music", "Football", "Interesting"]
    picks = []
    used = set()
    for bucket in buckets:
        for row in rows:
            if row.get("url") in used:
                continue
            if bucket in row.get("daily_labels", []):
                picks.append(row)
                used.add(row.get("url"))
                break
    for row in rows:
        if len(picks) >= limit:
            break
        if row.get("url") not in used and row.get("daily_score", 0) > 0:
            picks.append(row)
            used.add(row.get("url"))
    return picks[:limit]


def open_tasks(note_text: str) -> list[str]:
    note_text = strip_existing_report(note_text)
    tasks = []
    for line in note_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]") and stripped != "- [ ]":
            tasks.append(stripped)
    return tasks[:12]


def extract_memo_text(note_text: str) -> str:
    note_text = strip_existing_report(note_text)
    lines = []
    for raw in note_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("##"):
            continue
        if line.startswith("- [ ]") or line.startswith("- [x]"):
            continue
        lines.append(line.lstrip("- ").strip())
    return "\n".join(lines)


def summarize_memo(note_text: str) -> str:
    memo = extract_memo_text(note_text)
    if not memo:
        return "メモ本文はまだ少ないです。"
    fallback = {"summary": truncate(memo, 180)}
    result = llm_json(
        "以下はObsidianの今日のデイリーメモからタスクを除いた本文です。"
        "重要そうな気づきや文脈を日本語で1〜2文に要約してください。"
        "JSONだけで返してください: {\"summary\":\"...\"}\n\n"
        f"{memo}",
        fallback,
    )
    return result.get("summary") or fallback["summary"]


def enrich_rss_picks(rows: list[dict]) -> list[dict]:
    fallback_items = []
    for row in rows:
        title = row.get("title", "")
        fallback_items.append(
            {
                "url": row.get("url", ""),
                "title_ja": title if not is_mostly_english(title) else title,
                "summary_ja": truncate(row.get("summary", ""), 100) or "概要なし",
            }
        )
    fallback = {"items": fallback_items}
    compact = [
        {
            "url": row.get("url", ""),
            "title": row.get("title", ""),
            "source": row.get("feed_title", ""),
            "summary": truncate(row.get("summary", ""), 500),
        }
        for row in rows
    ]
    result = llm_json(
        "次のRSS記事候補について、日本語の表示用データを作ってください。"
        "英語タイトルは自然な日本語に翻訳し、日本語タイトルは必要なら整える程度にしてください。"
        "summary_ja は各記事の概要を日本語で60字以内にしてください。"
        "JSONだけで返してください: {\"items\":[{\"url\":\"...\",\"title_ja\":\"...\",\"summary_ja\":\"...\"}]}\n\n"
        + json.dumps(compact, ensure_ascii=False),
        fallback,
    )
    by_url = {item.get("url"): item for item in result.get("items", [])}
    enriched = []
    for row, fallback_item in zip(rows, fallback_items):
        item = by_url.get(row.get("url", ""), fallback_item)
        new_row = dict(row)
        new_row["title_ja"] = item.get("title_ja") or fallback_item["title_ja"]
        new_row["summary_ja"] = item.get("summary_ja") or fallback_item["summary_ja"]
        enriched.append(new_row)
    return enriched


def overall_summary(memo_summary: str, rss_picks: list[dict], youtube: list[dict], raindrops: list[dict]) -> list[str]:
    fallback = {
        "bullets": [
            f"RSSは{len(rss_picks)}件を選抜。AI/プロダクト、音楽制作、サッカー、気になる読み物を中心に拾っています。",
            f"YouTubeお気に入りは{len(youtube)}件、Raindropは{len(raindrops)}件ありました。",
            f"Obsidianメモ: {memo_summary}",
        ]
    }
    payload = {
        "memo_summary": memo_summary,
        "rss": [
            {"title": row.get("title_ja") or row.get("title"), "source": row.get("feed_title"), "summary": row.get("summary_ja", "")}
            for row in rss_picks
        ],
        "youtube": [{"title": row.get("title"), "channel": row.get("channel")} for row in youtube[:5]],
        "raindrop": [{"title": row.get("title"), "tags": row.get("tags", [])} for row in raindrops[:5]],
    }
    result = llm_json(
        "以下のデイリーレポート材料をもとに、冒頭に置く全体サマリーを日本語で3 bullet以内にしてください。"
        "行動提案ではなく、今日の情報傾向と気になる論点を短くまとめてください。"
        "JSONだけで返してください: {\"bullets\":[\"...\",\"...\",\"...\"]}\n\n"
        + json.dumps(payload, ensure_ascii=False),
        fallback,
    )
    bullets = result.get("bullets") or fallback["bullets"]
    return [str(bullet) for bullet in bullets[:3]]


def build_report(today: datetime, note_text: str, youtube: list[dict], rss_rows: list[dict], raindrops: list[dict], raindrop_error: Optional[str]) -> str:
    rss_picks = enrich_rss_picks(balanced_rss_picks(rss_rows))
    memo_summary = summarize_memo(note_text)
    summary_bullets = overall_summary(memo_summary, rss_picks, youtube, raindrops)
    return build_report_from_parts(summary_bullets, memo_summary, rss_picks, youtube, raindrops, raindrop_error)


def build_report_from_parts(summary_bullets: list[str], memo_summary: str, rss_picks: list[dict], youtube: list[dict], raindrops: list[dict], raindrop_error: Optional[str]) -> str:
    lines = [
        START_MARKER,
        "## Daily Report",
        "",
        "### 全体サマリー",
    ]
    lines.extend([f"- {bullet}" for bullet in summary_bullets])
    lines.extend(["", "### Obsidianメモ要約", memo_summary])

    lines.extend(["", "### RSS 選抜10件"])
    if rss_picks:
        lines.append("| 分類 | 記事 | 概要 | 出典 |")
        lines.append("|---|---|---|---|")
        for row in rss_picks:
            labels = ", ".join(row.get("daily_labels", []))
            article = md_link(row.get("title_ja") or row.get("title", ""), row.get("url", ""))
            lines.append(
                f"| {table_cell(labels)} | {table_cell(article)} | {table_cell(row.get('summary_ja', ''))} | {table_cell(row.get('feed_title', ''))} |"
            )
    else:
        lines.append("- 直近24時間の候補なし")

    lines.extend(["", "### YouTube お気に入り"])
    if youtube:
        lines.append("| 動画 | チャンネル | 概要 |")
        lines.append("|---|---|---|")
        for row in youtube[:10]:
            summary = truncate(row.get("description", ""), 90) or "お気に入り動画"
            lines.append(
                f"| {table_cell(md_link(row.get('title', ''), row.get('url', '')))} | {table_cell(row.get('channel', ''))} | {table_cell(summary)} |"
            )
    else:
        lines.append("- 直近24時間のお気に入りなし")

    lines.extend(["", "### Raindrop"])
    if raindrops:
        lines.append("| ブックマーク | タグ | 概要 |")
        lines.append("|---|---|---|")
        for row in raindrops:
            tags = ", ".join(row.get("tags", []))
            excerpt = truncate(row.get("excerpt", ""), 90) or "ブックマーク"
            lines.append(
                f"| {table_cell(md_link(row.get('title', ''), row.get('link', '')))} | {table_cell(tags)} | {table_cell(excerpt)} |"
            )
    elif raindrop_error:
        lines.append(f"- 未取得: {raindrop_error}")
    else:
        lines.append("- 直近24時間のブックマークなし")

    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"


def build_slack_payload(summary_bullets: list[str], memo_summary: str, rss_picks: list[dict], youtube: list[dict], raindrops: list[dict]) -> dict:
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "Daily Report", "emoji": False}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*全体サマリー*\n" + "\n".join(f"• {bullet}" for bullet in summary_bullets),
            },
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Obsidianメモ要約*\n{memo_summary}"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*RSS 選抜*"}},
    ]
    for row in rss_picks[:8]:
        labels = ", ".join(row.get("daily_labels", []))
        title = row.get("title_ja") or row.get("title", "")
        url = row.get("url", "")
        summary = row.get("summary_ja", "")
        source = row.get("feed_title", "")
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{url}|{slack_escape(title)}>*\n`{slack_escape(labels)}` {slack_escape(source)}\n{slack_escape(summary)}",
                },
            }
        )

    if youtube:
        blocks.extend([{"type": "divider"}, {"type": "section", "text": {"type": "mrkdwn", "text": "*YouTube お気に入り*"}}])
        for row in youtube[:5]:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• <{row.get('url', '')}|{slack_escape(row.get('title', ''))}> - {slack_escape(row.get('channel', ''))}",
                    },
                }
            )

    if raindrops:
        blocks.extend([{"type": "divider"}, {"type": "section", "text": {"type": "mrkdwn", "text": "*Raindrop*"}}])
        for row in raindrops[:5]:
            tags = ", ".join(row.get("tags", []))
            suffix = f" `{slack_escape(tags)}`" if tags else ""
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• <{row.get('link', '')}|{slack_escape(row.get('title', ''))}>{suffix}",
                    },
                }
            )

    return {"text": "Daily Report", "blocks": blocks[:50]}


def slack_escape(value: str) -> str:
    return (value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def post_to_slack(payload: dict) -> None:
    webhook = read_key_value_file(SLACK_WEBHOOKS_FILE).get("DAILY_REPORT", "")
    if not webhook:
        return
    request = urllib.request.Request(
        webhook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        response.read()


def upsert_report(note_path: Path, report: str) -> None:
    note_path.parent.mkdir(parents=True, exist_ok=True)
    text = note_path.read_text(encoding="utf-8") if note_path.exists() else ""
    if START_MARKER in text and END_MARKER in text:
        before = text.split(START_MARKER, 1)[0].rstrip()
        after = text.split(END_MARKER, 1)[1].lstrip()
        new_text = f"{before}\n\n{report}"
        if after:
            new_text += f"\n{after}"
    else:
        new_text = text.rstrip() + "\n\n" + report if text.strip() else report
    note_path.write_text(new_text, encoding="utf-8")


def main() -> int:
    now = datetime.now(JST)
    cutoff = now.astimezone(timezone.utc) - timedelta(hours=24)
    note_path = DAILY_DIR / f"{now.strftime('%Y-%m-%d')}.md"
    note_text = note_path.read_text(encoding="utf-8") if note_path.exists() else ""

    youtube = fetch_youtube(cutoff)
    rss_rows = fetch_rss(24)
    raindrops, raindrop_error = fetch_raindrop(cutoff)
    rss_picks = enrich_rss_picks(balanced_rss_picks(rss_rows))
    memo_summary = summarize_memo(note_text)
    summary_bullets = overall_summary(memo_summary, rss_picks, youtube, raindrops)
    report = build_report_from_parts(summary_bullets, memo_summary, rss_picks, youtube, raindrops, raindrop_error)
    upsert_report(note_path, report)
    post_to_slack(build_slack_payload(summary_bullets, memo_summary, rss_picks, youtube, raindrops))
    print(f"Wrote daily report: {note_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"daily_report failed: {exc}", file=sys.stderr)
        raise
