#!/bin/zsh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/skills"
TARGET_DIR="${HOME}/.codex/skills"

mkdir -p "${TARGET_DIR}"

for skill_dir in "${SOURCE_DIR}"/*; do
  [[ -d "${skill_dir}" ]] || continue
  skill_name="$(basename "${skill_dir}")"
  target="${TARGET_DIR}/${skill_name}"

  if [[ -e "${target}" || -L "${target}" ]]; then
    rm -rf "${target}"
  fi

  cp -R "${skill_dir}" "${target}"
  find "${target}" -name ".DS_Store" -delete
  echo "Installed skill: ${skill_name}"
done
