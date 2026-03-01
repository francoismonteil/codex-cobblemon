#!/usr/bin/env bash
set -euo pipefail

# Ensures Flan uses a wooden hoe instead of the default stick/golden hoe
# for both claim creation and claim inspection.
#
# Usage:
#   ./infra/flan-configure-claim-tools.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

DATA_DIR="./data"
CONFIG_DIR="${DATA_DIR}/config/flan"
CONFIG_FILE="${CONFIG_DIR}/flan_config.json"
CLAIMING_ITEM="minecraft:wooden_hoe"
INSPECTION_ITEM="minecraft:wooden_hoe"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

need_cmd python3

mkdir -p "${CONFIG_DIR}"

if [[ ! -f "${CONFIG_FILE}" ]]; then
  printf '{}\n' >"${CONFIG_FILE}"
fi

python3 - "${CONFIG_FILE}" "${CLAIMING_ITEM}" "${INSPECTION_ITEM}" <<'PY'
import json
import pathlib
import sys

config_path = pathlib.Path(sys.argv[1])
claiming_item = sys.argv[2]
inspection_item = sys.argv[3]

try:
    raw = config_path.read_text(encoding="utf-8").strip()
except FileNotFoundError:
    raw = ""

try:
    data = json.loads(raw or "{}")
except json.JSONDecodeError as exc:
    raise SystemExit(f"ERROR: invalid JSON in {config_path}: {exc}")

if not isinstance(data, dict):
    raise SystemExit(f"ERROR: expected a JSON object in {config_path}")

data["claimingItem"] = claiming_item
data["inspectionItem"] = inspection_item

config_path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
PY

echo "OK configured Flan claim/inspection tool:"
echo "  file: ${CONFIG_FILE}"
echo "  claimingItem: ${CLAIMING_ITEM}"
echo "  inspectionItem: ${INSPECTION_ITEM}"
echo "Restart the server after applying this config (prefer ./infra/safe-restart.sh or stop/start)."
