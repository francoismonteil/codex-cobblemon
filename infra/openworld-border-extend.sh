#!/usr/bin/env bash
set -euo pipefail

# Extends the open-world border and (re)starts Chunky pre-generation using the new worldborder.
#
# Usage:
#   ./infra/openworld-border-extend.sh <new_border_size>
#
# Example:
#   ./infra/openworld-border-extend.sh 6000

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <new_border_size>" >&2
  exit 2
fi

NEW_SIZE="$1"
if ! [[ "${NEW_SIZE}" =~ ^[0-9]+$ ]]; then
  echo "Invalid border size: ${NEW_SIZE} (expected integer, e.g. 6000)" >&2
  exit 2
fi

if [[ ! -x "./infra/world-spawn.sh" ]]; then
  echo "Missing ./infra/world-spawn.sh" >&2
  exit 1
fi

spawn="$(./infra/world-spawn.sh)"
read -r SPAWN_X SPAWN_Y SPAWN_Z <<<"${spawn}"

cmd() {
  ./infra/mc.sh "$1" >/dev/null
  sleep 0.25
}

cmd_try() {
  ./infra/mc.sh "$1" >/dev/null 2>&1 || true
  sleep 0.25
}

echo "== World border =="
cmd "worldborder center ${SPAWN_X} ${SPAWN_Z}"
cmd "worldborder set ${NEW_SIZE}"
cmd_try "worldborder warning distance 32"
cmd_try "worldborder warning time 15"

echo "== Chunky pre-generation =="
cmd_try "chunky shape square"
cmd "chunky worldborder"
cmd_try "chunky quiet"
cmd "chunky start"

echo "OK border extended and Chunky started:"
echo "  center: ${SPAWN_X} ${SPAWN_Z}"
echo "  size: ${NEW_SIZE}"
