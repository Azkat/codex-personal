# Codex Personal

Personal Codex skills and supporting local projects. The repository is intended
to live directly at `~/.codex/skills`.

## Layout

```text
daily-report/            Personal Codex skill
_projects/               Local automation or support projects used by skills
_projects/daily-report/  Daily report automation
.system/                 Codex system skills, ignored by Git
```

Local compatibility symlink:

```text
~/.codex/projects/daily-report -> ~/.codex/skills/_projects/daily-report
```

Personal skills are real directories under `~/.codex/skills`, not symlinks, so
Codex can discover them directly.

## Daily Report

Operational details are in `_projects/daily-report/app/README.md`.

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
