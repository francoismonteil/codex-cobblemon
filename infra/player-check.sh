#!/usr/bin/env bash
set -euo pipefail

# Check whether a player is in whitelist and/or ops list (offline, from JSON files).
#
# Usage:
#   ./infra/player-check.sh <Pseudo>
#   ./infra/player-check.sh --json <Pseudo>

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
  echo "Missing python3/python (required to parse whitelist.json / ops.json)" >&2
  return 1
}

format="plain"
if [[ "${1:-}" == "--json" ]]; then
  format="json"
  shift
fi

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 [--json] <Pseudo>" >&2
  exit 2
fi

name="$1"
pybin="$(find_python)"

"${pybin}" - "${REPO_ROOT}/data/whitelist.json" "${REPO_ROOT}/data/ops.json" "${name}" "${format}" <<'PY'
import json
import pathlib
import sys

whitelist_path = pathlib.Path(sys.argv[1])
ops_path = pathlib.Path(sys.argv[2])
query = sys.argv[3]
fmt = sys.argv[4]
needle = query.casefold()

def load_list(path: pathlib.Path):
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Failed to read {path}: {exc}", file=sys.stderr)
        sys.exit(1)
    if isinstance(data, list):
        return data
    return []

def find_entry(entries):
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", ""))
        if name.casefold() == needle:
            return entry
    return None

whitelist = load_list(whitelist_path)
ops = load_list(ops_path)

w_entry = find_entry(whitelist)
o_entry = find_entry(ops)

result = {
    "player_query": query,
    "whitelisted": w_entry is not None,
    "op": o_entry is not None,
}

if w_entry is not None:
    result["whitelist_name"] = w_entry.get("name")
    if "uuid" in w_entry:
        result["whitelist_uuid"] = w_entry.get("uuid")

if o_entry is not None:
    result["op_name"] = o_entry.get("name")
    if "uuid" in o_entry:
        result["op_uuid"] = o_entry.get("uuid")
    if "level" in o_entry:
        result["op_level"] = o_entry.get("level")
    if "bypassesPlayerLimit" in o_entry:
        result["bypasses_player_limit"] = o_entry.get("bypassesPlayerLimit")

if fmt == "json":
    print(json.dumps(result, ensure_ascii=True, indent=2))
else:
    print(f"Player: {query}")
    print(f"Whitelist: {'yes' if result['whitelisted'] else 'no'}")
    print(f"Op: {'yes' if result['op'] else 'no'}")
    if "op_level" in result:
        print(f"Op level: {result['op_level']}")
PY
