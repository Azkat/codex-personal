# デイリーレポート設定メモ

この仕組みは、毎日1回、次の情報を集めてObsidianのデイリーノートに追記します。

- Obsidianの今日のデイリーメモ
- YouTubeの高評価動画
- InoreaderからエクスポートしたOPML/RSS
- Raindropの直近ブックマーク

出力先はここです。

```text
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DAILY/90_DailyMemo/YYYY-MM-DD.md
```

## 主要ファイル

```text
~/.codex/projects/daily-report/
~/.codex/projects/daily-report/app/daily_report.py
~/.codex/projects/daily-report/app/render_report_image.py
~/.codex/projects/daily-report/youtube-liked-videos/fetch_liked_videos.py
~/.codex/projects/daily-report/inoreader-opml/fetch_recent_feeds.py
~/.codex/projects/daily-report/launchd/com.atsushi.daily-report.plist
~/.codex/projects/daily-report/scripts/install_launch_agent.sh
~/.config/inoreader/Inoreader Feeds 20260528.xml
~/.config/inoreader/additional_feeds_20260528.xml
~/.config/raindrop/token.txt
~/.config/slack/webhooks
```

## 秘密情報

トークンやAPIキーはGitやObsidianには書かないでください。

RaindropのTest token:

```text
~/.config/raindrop/token.txt
```

どちらの形式でも読めます。

```text
TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

```text
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Codex CLIが使える場合、毎朝の自動実行でもCodexに英語RSSタイトルの日本語化と概要生成をさせます。

```text
~/.local/bin/codex
```

Codex CLIが使えない環境では、OpenAI APIキーを任意のフォールバックとして使えます。

```text
~/.config/openai/api_key.txt
```

どちらの形式でも読めます。

```text
OPENAI_API_KEY=sk-...
```

```text
sk-...
```

Codex CLIもOpenAI APIキーもない場合もレポートは動きます。ただし英語タイトルや英語概要の日本語化は限定的です。会話中に手動で依頼する場合は、Codexが出力済みレポートを読んで日本語に直せます。

Slack Incoming Webhook:

```text
~/.config/slack/webhooks
```

将来別のWebhookも足せるように `KEY=URL` 形式です。

```text
DAILY_REPORT=https://hooks.slack.com/services/...
```

`DAILY_REPORT` が空ならSlack投稿はスキップされます。

## 手動実行

```bash
/usr/bin/python3 ~/.codex/projects/daily-report/app/daily_report.py
```

## 自動実行

LaunchAgentは毎日 08:30 JST に実行する設定です。正本はプロジェクト内にあります。

```text
~/.codex/projects/daily-report/launchd/com.atsushi.daily-report.plist
```

macOSのユーザーLaunchAgentとして自動実行するには、`~/Library/LaunchAgents/` にインストールする必要があります。次のスクリプトがプロジェクト内のplistをコピーして登録します。

```bash
~/.codex/projects/daily-report/scripts/install_launch_agent.sh
```

無効化:

```bash
~/.codex/projects/daily-report/scripts/uninstall_launch_agent.sh
```

launchd経由で即時実行:

```bash
launchctl kickstart -k gui/$(id -u)/com.atsushi.daily-report
```

ログ:

```text
~/Library/Application Support/Codex Daily Report/logs/daily-report.out.log
~/Library/Application Support/Codex Daily Report/logs/daily-report.err.log
```

## 別デバイスへ移すとき

1. コピーする本体はこの1フォルダです。

```text
~/.codex/projects/daily-report/
```

2. 設定ファイルと秘密情報を作り直します。

```text
~/.config/inoreader/
~/.config/raindrop/token.txt
~/.config/slack/webhooks
~/.config/youtube/client_secret_*.json
~/.config/youtube/token.json
~/.config/openai/api_key.txt
```

3. Python環境は新デバイスで作り直します。venvは別Macへコピーせず、再作成してください。

```bash
python3 -m venv ~/.codex/projects/daily-report/youtube-liked-videos/.venv
~/.codex/projects/daily-report/youtube-liked-videos/.venv/bin/python -m pip install --upgrade pip google-api-python-client google-auth-oauthlib

python3 -m venv ~/.codex/projects/daily-report/inoreader-opml/.venv
~/.codex/projects/daily-report/inoreader-opml/.venv/bin/python -m pip install --upgrade pip feedparser

python3 -m venv ~/.codex/projects/daily-report/app/.venv
~/.codex/projects/daily-report/app/.venv/bin/python -m pip install --upgrade pip pillow
```

4. YouTube OAuthを新デバイスで再認証します。

`~/.config/youtube/client_secret_*.json` を置いたあと、次を手動実行します。ブラウザに出るURLで正しいGoogleアカウントを許可すると `~/.config/youtube/token.json` が作られます。

```bash
~/.codex/projects/daily-report/youtube-liked-videos/.venv/bin/python \
  ~/.codex/projects/daily-report/youtube-liked-videos/fetch_liked_videos.py
```

5. 手動実行してObsidianの今日のノートとSlack投稿を確認します。

```bash
/usr/bin/python3 ~/.codex/projects/daily-report/app/daily_report.py
```

6. 自動実行を有効化します。

```bash
~/.codex/projects/daily-report/scripts/install_launch_agent.sh
```

スクリプトは `Path.home()` と `$HOME` を使うため、Macのユーザー名が違っても基本的に動きます。LaunchAgentもインストール時に現在の `$HOME` を埋め込みます。

## スリープ中の実行について

MacBook Proがスリープしている間は、通常の `launchd` ジョブはその時刻ぴったりには実行されません。起きている、またはスリープ解除されたタイミングで実行されることはありますが、毎朝必ず指定時刻に走る保証はありません。

確実に毎日決まった時刻に実行したい場合は、次のどれかが必要です。

- その時刻にMacを起こしておく
- `pmset` でスケジュール起床を設定する
- 常時起動のMac miniやサーバーで実行する
- GitHub Actionsなどクラウド側に寄せる。ただしObsidian/iCloudローカル書き込みやローカルCodex CLI利用は再設計が必要

## 出力仕様

レポートは次のブロックを毎回置き換えます。

```text
<!-- daily-report:start -->
<!-- daily-report:end -->
```

現在の構成:

- 全体サマリー
- Obsidianメモ要約
- RSS選抜10件の表
- YouTube高評価動画の表
- Raindropブックマークの表
- Slackへの短縮版通知

意図的にやっていること:

- `今日のタスク` のチェックボックス一覧は出さない
- 時刻 `10:30` のような列は出さない
- RSSの英語タイトルは、Codex CLIまたはOpenAI APIキーが使える場合に自動で日本語化する
- RSSには短い日本語概要を付ける。どちらも使えない場合、自動実行ではRSS抜粋が英語のまま残ることがある
