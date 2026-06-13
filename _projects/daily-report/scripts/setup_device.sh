#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${HOME}/.codex/skills/_projects/daily-report"
LINK_ROOT="${HOME}/.codex/projects/daily-report"

if [ ! -d "${PROJECT_ROOT}" ]; then
  echo "Project not found: ${PROJECT_ROOT}" >&2
  echo "Clone https://github.com/Azkat/codex-personal.git to ~/.codex/skills first." >&2
  exit 1
fi

mkdir -p "${HOME}/.codex/projects"
if [ ! -e "${LINK_ROOT}" ]; then
  ln -s "${PROJECT_ROOT}" "${LINK_ROOT}"
fi

python3 -m venv "${LINK_ROOT}/app/.venv"
"${LINK_ROOT}/app/.venv/bin/python" -m pip install -r "${LINK_ROOT}/requirements/app.txt"

python3 -m venv "${LINK_ROOT}/youtube-liked-videos/.venv"
"${LINK_ROOT}/youtube-liked-videos/.venv/bin/python" -m pip install -r "${LINK_ROOT}/requirements/youtube-liked-videos.txt"

python3 -m venv "${LINK_ROOT}/inoreader-opml/.venv"
"${LINK_ROOT}/inoreader-opml/.venv/bin/python" -m pip install -r "${LINK_ROOT}/requirements/inoreader-opml.txt"

echo "Daily report local environment is ready."
echo "Recreate per-device secrets under ~/.config before expecting all sources to populate."
