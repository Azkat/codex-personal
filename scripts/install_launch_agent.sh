#!/bin/zsh
set -euo pipefail

LABEL="com.atsushi.daily-report"
PROJECT_ROOT="${HOME}/.codex/projects/daily-report"
SOURCE_PLIST="${PROJECT_ROOT}/launchd/${LABEL}.plist"
TARGET_DIR="${HOME}/Library/LaunchAgents"
TARGET_PLIST="${TARGET_DIR}/${LABEL}.plist"
LOG_DIR="${HOME}/Library/Application Support/Codex Daily Report/logs"

mkdir -p "${TARGET_DIR}" "${LOG_DIR}"

# Install a copy with the current user's home path expanded.
sed "s#__HOME__#${HOME}#g" "${SOURCE_PLIST}" > "${TARGET_PLIST}"

launchctl bootout "gui/$(id -u)" "${TARGET_PLIST}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "${TARGET_PLIST}"

echo "Installed ${LABEL}"
echo "Plist: ${TARGET_PLIST}"
