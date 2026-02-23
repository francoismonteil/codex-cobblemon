#!/usr/bin/env bash
set -euo pipefail

# Checks local server mods against the recommended server pack for this repo.
#
# Wrapper around `tools/check_recommended_server_mods.py`.
#
# Default behavior:
# - checks `./data/mods`
# - writes `audit/recommended-server-mods-check.json`
#
# Usage:
#   ./infra/mods-check-recommended.sh
#   ./infra/mods-check-recommended.sh --mods-dir ./data/mods
#   ./infra/mods-check-recommended.sh --mods-dir /path/to/server/mods

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY_SCRIPT="${REPO_ROOT}/tools/check_recommended_server_mods.py"

if [[ ! -f "${PY_SCRIPT}" ]]; then
  echo "Missing script: ${PY_SCRIPT}" >&2
  exit 1
fi

run_checker() {
  if command -v python3 >/dev/null 2>&1; then
    python3 "${PY_SCRIPT}" --write "$@"
    return $?
  fi
  if command -v py >/dev/null 2>&1; then
    py -3 "${PY_SCRIPT}" --write "$@"
    return $?
  fi
  echo "Missing Python runtime (need 'python3' or 'py')." >&2
  return 1
}

run_checker "$@"
