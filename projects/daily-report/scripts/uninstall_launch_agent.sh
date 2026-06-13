#!/bin/zsh
set -euo pipefail

LABEL="com.atsushi.daily-report"
TARGET_PLIST="${HOME}/Library/LaunchAgents/${LABEL}.plist"

launchctl bootout "gui/$(id -u)" "${TARGET_PLIST}" 2>/dev/null || true
rm -f "${TARGET_PLIST}"

echo "Uninstalled ${LABEL}"

