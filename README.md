# Daily Report

Codex daily-report skill and the local automation it operates.

## Layout

```text
app/                     Main report generator and image renderer
youtube-liked-videos/    YouTube liked-video fetcher
inoreader-opml/          OPML/RSS fetcher
launchd/                 LaunchAgent plist template
scripts/                 Install and uninstall scripts for launchd
skills/daily-report/     Codex skill source
requirements/            Python dependency lists
```

The Codex skill is installed through this symlink:

```text
~/.codex/skills/daily-report -> ~/.codex/projects/daily-report/skills/daily-report
```

This keeps the skill source in the same Git repository as the automation code.

## Local setup

Create virtual environments as needed:

```bash
python3 -m venv ~/.codex/projects/daily-report/app/.venv
~/.codex/projects/daily-report/app/.venv/bin/python -m pip install -r ~/.codex/projects/daily-report/requirements/app.txt

python3 -m venv ~/.codex/projects/daily-report/youtube-liked-videos/.venv
~/.codex/projects/daily-report/youtube-liked-videos/.venv/bin/python -m pip install -r ~/.codex/projects/daily-report/requirements/youtube-liked-videos.txt

python3 -m venv ~/.codex/projects/daily-report/inoreader-opml/.venv
~/.codex/projects/daily-report/inoreader-opml/.venv/bin/python -m pip install -r ~/.codex/projects/daily-report/requirements/inoreader-opml.txt
```

Secrets and local config live outside the repository:

```text
~/.config/inoreader/
~/.config/raindrop/token.txt
~/.config/slack/webhooks
~/.config/youtube/
~/.config/openai/api_key.txt
```

## Run

```bash
/usr/bin/python3 ~/.codex/projects/daily-report/app/daily_report.py
```

Install the daily LaunchAgent:

```bash
~/.codex/projects/daily-report/scripts/install_launch_agent.sh
```

Operational details are in `app/README.md`.
