#!/usr/bin/env bash
set -euo pipefail

# Switches the active world to a snapshot from ./worlds/<name>.
#
# This stops the server, moves ./data/world to a timestamped backup, copies the selected world,
# then starts the server.
#
# Usage:
#   ./infra/world-switch.sh <name>
#   ./infra/world-switch.sh <name> --save-current-as <snapshotName>
#
# Notes:
# - Each world includes its own playerdata inside the world folder, so switching worlds also
#   switches player inventories/progress for that world.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <name> [--save-current-as <snapshotName>]" >&2
  exit 2
fi

name="$1"
shift

save_current_as=""
if [[ "${1:-}" == "--save-current-as" ]]; then
  save_current_as="${2:-}"
  if [[ -z "${save_current_as}" ]]; then
    echo "Missing snapshot name after --save-current-as" >&2
    exit 2
  fi
fi

WORLD_LIB="${REPO_ROOT}/worlds"
src="${WORLD_LIB}/${name}"

if [[ ! -d "${src}" || ! -f "${src}/level.dat" ]]; then
  echo "World not found in library (missing level.dat): ${src}" >&2
  echo "Tip: ./infra/worlds-list.sh" >&2
  exit 2
fi

ts="$(date +%Y%m%d-%H%M%S)"

if [[ -n "${save_current_as}" ]]; then
  if [[ -d "./data/world" && -f "./data/world/level.dat" ]]; then
    dst="${WORLD_LIB}/${save_current_as}"
    if [[ -e "${dst}" ]]; then
      mv "${dst}" "${dst}.bak.${ts}"
    fi
    echo "[0/4] Saving current world to library: ${dst}"
    cp -a ./data/world "${dst}"
  fi
fi

echo "[1/4] Stop server..."
./infra/stop.sh || true

echo "[2/4] Backup current active world..."
if [[ -d "./data/world" ]]; then
  mv "./data/world" "./data/world.bak.${ts}"
fi

echo "[3/4] Activate world from library: ${name}"
cp -a "${src}" "./data/world"

echo "[4/4] Start server..."
./infra/start.sh

echo "OK: Active world is now '${name}' (previous saved as ./data/world.bak.${ts})"

