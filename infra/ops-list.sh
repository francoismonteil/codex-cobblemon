#!/usr/bin/env bash
set -euo pipefail

# List operators from data/ops.json (admin-only informational helper).
#
# Usage:
#   ./infra/ops-list.sh
#   ./infra/ops-list.sh --full
#   ./infra/ops-list.sh --json

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi
  echo "Missing python3/python (required to parse ops.json)" >&2
  return 1
}

format="names"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --full)
      format="full"
      ;;
    --json)
      format="json"
      ;;
    *)
      echo "Usage: $0 [--full|--json]" >&2
      exit 2
      ;;
  esac
  shift
done

pybin="$(find_python)"

"${pybin}" - "${REPO_ROOT}/data/ops.json" "${format}" <<'PY'
import json
import pathlib
import sys

ops_path = pathlib.Path(sys.argv[1])
fmt = sys.argv[2]

if not ops_path.exists():
    data = []
else:
    try:
        data = json.loads(ops_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Failed to read {ops_path}: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, list):
        data = []

entries = [e for e in data if isinstance(e, dict)]
entries.sort(key=lambda e: str(e.get("name", "")).casefold())

if fmt == "json":
    print(json.dumps(entries, ensure_ascii=True, indent=2))
    sys.exit(0)

if not entries:
    print("(none)")
    sys.exit(0)

for entry in entries:
    name = str(entry.get("name", "<unknown>"))
    if fmt == "full":
        level = entry.get("level", "?")
        bypass = entry.get("bypassesPlayerLimit", False)
        print(f"{name} level={level} bypassesPlayerLimit={str(bool(bypass)).lower()}")
    else:
        print(name)
PY
