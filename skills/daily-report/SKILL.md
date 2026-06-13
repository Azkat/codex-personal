---
name: daily-report
description: ユーザーのローカル日次レポート自動化を扱うときに使う。Obsidianデイリーノート、YouTube高評価、Inoreader OPML/RSS、Raindrop API、launchd定期実行、出力フォーマットの修正やトラブルシュートを対象にする。
---

# Daily Report Skill

このskillは、ユーザーのローカル日次レポート自動化を保守・変更するときに使う。

## まず見る場所

- リポジトリ正本: `~/.codex/projects/daily-report`
- 運用README: `~/.codex/projects/daily-report/app/README.md`
- GitHub向けREADME: `~/.codex/projects/daily-report/README.md`
- メインスクリプト: `~/.codex/projects/daily-report/app/daily_report.py`
- LaunchAgent正本: `~/.codex/projects/daily-report/launchd/com.atsushi.daily-report.plist`
- LaunchAgentインストール: `~/.codex/projects/daily-report/scripts/install_launch_agent.sh`
- Obsidian Vault: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DAILY`
- デイリーノート: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DAILY/90_DailyMemo`
- YouTube取得: `~/.codex/projects/daily-report/youtube-liked-videos/fetch_liked_videos.py`
- RSS取得: `~/.codex/projects/daily-report/inoreader-opml/fetch_recent_feeds.py`
- Inoreader OPML: `~/.config/inoreader/Inoreader Feeds 20260528.xml`
- 追加OPML: `~/.config/inoreader/additional_feeds_20260528.xml`
- Raindrop token: `~/.config/raindrop/token.txt`
- Slack webhooks: `~/.config/slack/webhooks`
- 任意OpenAI key: `~/.config/openai/api_key.txt`

## 作業手順

1. まずREADMEを読む。
2. 仕様変更は原則 `daily_report.py` に反映する。
3. 秘密情報は絶対に表示・保存しない。存在確認、文字数、API疎通確認だけにする。
4. 構文確認:

```bash
/usr/bin/python3 -m py_compile ~/.codex/projects/daily-report/app/daily_report.py
```

5. 手動実行:

```bash
/usr/bin/python3 ~/.codex/projects/daily-report/app/daily_report.py
```

6. 今日のObsidianデイリーノートで、次のブロックを確認する。

```text
<!-- daily-report:start -->
<!-- daily-report:end -->
```

## 出力ルール

- 冒頭に全体サマリーを書く。
- Obsidianのチェックボックスタスク一覧は出さない。
- Obsidian本文にメモっぽい内容があれば、それを要約する。
- RSS、YouTube、RaindropはMarkdown表で出す。
- `10:30` のような時刻列は出さない。
- RSSの英語タイトルは日本語に訳す。自動実行ではまずCodex CLI `~/.local/bin/codex` を使う。使えない場合はOpenAI APIキーをフォールバックにする。
- RSSには短い日本語概要を付ける。会話中にユーザーが依頼した場合は、Codexが出力済みレポートを読んで手動で日本語化してよい。
- Slack投稿は `~/.config/slack/webhooks` の `DAILY_REPORT=` を読む。URL値は表示しない。

## 認証情報

Raindrop tokenは次のどちらでも読める。

```text
TOKEN=...
```

```text
...
```

OpenAI keyも次のどちらでも読める。

```text
OPENAI_API_KEY=...
```

```text
...
```
