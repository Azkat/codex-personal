# Codex Personal

Personal Codex skills and supporting local projects.

## Layout

```text
skills/                  Codex skills installed into ~/.codex/skills
projects/                Local automation or support projects used by skills
projects/daily-report/   Daily report automation
```

Installed symlinks:

```text
~/.codex/skills/daily-report -> ~/.codex/codex-personal/skills/daily-report
~/.codex/projects/daily-report -> ~/.codex/codex-personal/projects/daily-report
```

This keeps all personal Codex assets in one Git repository while preserving the
paths used by existing automation.

## Daily Report

Operational details are in `projects/daily-report/app/README.md`.

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
