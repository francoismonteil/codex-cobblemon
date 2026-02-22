#!/usr/bin/env bash
set -euo pipefail

# Helper around infra/mc.sh to manage whitelist/op quickly.
#
# Usage:
#   ./infra/player.sh add <Pseudo> [--op]
#   ./infra/player.sh remove <Pseudo>
#   ./infra/player.sh op <Pseudo>
#   ./infra/player.sh deop <Pseudo>
#   ./infra/player.sh list
#
# Notes:
# - This does not need RCON.
# - Requires infra/mc.sh and CREATE_CONSOLE_IN_PIPE=true in the container env.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

mc() {
  "${REPO_ROOT}/infra/mc.sh" "$@"
}

usage() {
  echo "Usage:" >&2
  echo "  $0 add <Pseudo> [--op]" >&2
  echo "  $0 remove <Pseudo>" >&2
  echo "  $0 op <Pseudo>" >&2
  echo "  $0 deop <Pseudo>" >&2
  echo "  $0 list" >&2
}

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi
  echo "Missing python3/python (required for 'list' to read data/whitelist.json)" >&2
  return 1
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

action="$1"
shift

case "${action}" in
  add)
    if [[ $# -lt 1 ]]; then usage; exit 2; fi
    name="$1"
    shift

    do_op="false"
    if [[ $# -ge 1 ]]; then
      if [[ "$1" == "--op" ]]; then
        do_op="true"
      else
        usage
        exit 2
      fi
    fi

    mc "whitelist add ${name}"
    if [[ "${do_op}" == "true" ]]; then
      mc "op ${name}"
    fi
    ;;

  remove)
    if [[ $# -ne 1 ]]; then usage; exit 2; fi
    name="$1"
    # Deop first (no-op if not op), then remove from whitelist.
    mc "deop ${name}" || true
    mc "whitelist remove ${name}"
    ;;

  op)
    if [[ $# -ne 1 ]]; then usage; exit 2; fi
    mc "op $1"
    ;;

  deop)
    if [[ $# -ne 1 ]]; then usage; exit 2; fi
    mc "deop $1"
    ;;

  list)
    pybin="$(find_python)"
    "${pybin}" - "${REPO_ROOT}/data/whitelist.json" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])

if not path.exists():
    print("(whitelist file missing)")
    sys.exit(0)

try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"Failed to read {path}: {exc}", file=sys.stderr)
    sys.exit(1)

if not isinstance(data, list):
    print("(invalid whitelist format)")
    sys.exit(0)

names = []
for entry in data:
    if isinstance(entry, dict) and "name" in entry:
        names.append(str(entry["name"]))

names.sort(key=str.casefold)

if not names:
    print("(none)")
else:
    for name in names:
        print(name)
PY
    ;;

  *)
    usage
    exit 2
    ;;
esac
