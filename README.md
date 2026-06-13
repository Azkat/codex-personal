# Codex Personal

Personal Codex skills and supporting local projects. The repository is intended
to live directly at `~/.codex/skills`.

Repository:

```text
https://github.com/Azkat/codex-personal.git
```

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

## Set Up On Another Mac

Clone this repository directly into Codex's personal skills directory:

```bash
mkdir -p ~/.codex ~/.codex/projects
git clone https://github.com/Azkat/codex-personal.git ~/.codex/skills
ln -s ~/.codex/skills/_projects/daily-report ~/.codex/projects/daily-report
```

Create the symlink and local virtual environments:

```bash
~/.codex/skills/_projects/daily-report/scripts/setup_device.sh
```

Secrets and local config live outside the repository and must be recreated per
device:

```text
~/.config/inoreader/
~/.config/raindrop/token.txt
~/.config/slack/webhooks
~/.config/youtube/
~/.config/openai/api_key.txt
```

## Local Environment

Recreate virtual environments whenever dependencies are missing:

```bash
~/.codex/skills/_projects/daily-report/scripts/setup_device.sh
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
