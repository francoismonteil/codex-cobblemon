#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TOOL="${REPO_ROOT}/tools/modpack_release.py"

if [[ ! -f "${TOOL}" ]]; then
  echo "Missing tool: ${TOOL}" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "${TOOL}" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "${TOOL}" "$@"
fi

echo "Python is required to run ${TOOL}" >&2
exit 1
