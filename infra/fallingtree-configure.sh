#!/usr/bin/env bash
set -euo pipefail

# Configures FallingTree tree size limits in ./data/config/fallingtree.json.
#
# Usage:
#   ./infra/fallingtree-configure.sh [max_size] [max_scan_size]
#
# Defaults:
# - max_size: 256
# - max_scan_size: auto (keeps current value, but is raised to max_size if needed)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

DATA_DIR="./data"
CONFIG_DIR="${DATA_DIR}/config"
CONFIG_FILE="${CONFIG_DIR}/fallingtree.json"
MAX_SIZE="${1:-256}"
MAX_SCAN_SIZE="${2:-}"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

need_cmd python3

case "${MAX_SIZE}" in
  ''|*[!0-9]*)
    echo "ERROR: max_size must be a non-negative integer, got: ${MAX_SIZE}" >&2
    exit 1
    ;;
esac

if [[ -n "${MAX_SCAN_SIZE}" ]]; then
  case "${MAX_SCAN_SIZE}" in
    ''|*[!0-9]*)
      echo "ERROR: max_scan_size must be a non-negative integer, got: ${MAX_SCAN_SIZE}" >&2
      exit 1
      ;;
  esac
fi

mkdir -p "${CONFIG_DIR}"

if [[ ! -f "${CONFIG_FILE}" ]]; then
  printf '{}\n' >"${CONFIG_FILE}"
fi

mapfile -t applied < <(python3 - "${CONFIG_FILE}" "${MAX_SIZE}" "${MAX_SCAN_SIZE}" <<'PY'
import json
import pathlib
import sys

config_path = pathlib.Path(sys.argv[1])
max_size = int(sys.argv[2])
max_scan_size_arg = sys.argv[3].strip()

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

trees = data.get("trees")
if trees is None:
    trees = {}
    data["trees"] = trees
elif not isinstance(trees, dict):
    raise SystemExit(f"ERROR: expected 'trees' to be a JSON object in {config_path}")

current_scan_size = trees.get("maxScanSize")
if not isinstance(current_scan_size, int):
    current_scan_size = 500

if max_scan_size_arg:
    max_scan_size = int(max_scan_size_arg)
else:
    max_scan_size = max(current_scan_size, max_size)

trees["maxSize"] = max_size
trees["maxScanSize"] = max_scan_size

config_path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

print(max_size)
print(max_scan_size)
PY
)

echo "OK configured FallingTree:"
echo "  file: ${CONFIG_FILE}"
echo "  trees.maxSize: ${applied[0]}"
echo "  trees.maxScanSize: ${applied[1]}"
echo "Restart the server after applying this config (prefer ./infra/safe-restart.sh or stop/start)."
