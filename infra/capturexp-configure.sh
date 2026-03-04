#!/usr/bin/env bash
set -euo pipefail

# Configures Cobblemon Capture XP in ./data/config/capture_xp.json5.
#
# Usage:
#   ./infra/capturexp-configure.sh [multiplier]
#
# Defaults:
# - multiplier: 1.0
#
# Notes:
# - This mod currently exposes a single config option: `multiplier`.
# - The config file is JSON5 upstream, but plain JSON is also valid here.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

DATA_DIR="./data"
CONFIG_DIR="${DATA_DIR}/config"
CONFIG_FILE="${CONFIG_DIR}/capture_xp.json5"
MULTIPLIER="${1:-1.0}"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

need_cmd python3

mkdir -p "${CONFIG_DIR}"

applied="$(
  python3 - "${CONFIG_FILE}" "${MULTIPLIER}" <<'PY'
import json
import pathlib
import sys

config_path = pathlib.Path(sys.argv[1])
raw_multiplier = sys.argv[2]

try:
    multiplier = float(raw_multiplier)
except ValueError as exc:
    raise SystemExit(f"ERROR: multiplier must be a number, got: {raw_multiplier}") from exc

if multiplier < 0:
    raise SystemExit(f"ERROR: multiplier must be >= 0, got: {raw_multiplier}")

config_path.write_text(
    json.dumps({"multiplier": multiplier}, indent=2, ensure_ascii=True) + "\n",
    encoding="utf-8",
)

print(multiplier)
PY
)"

echo "OK configured Cobblemon Capture XP:"
echo "  file: ${CONFIG_FILE}"
echo "  multiplier: ${applied}"
echo "Restart the server after applying this config (prefer ./infra/safe-restart.sh or stop/start)."
