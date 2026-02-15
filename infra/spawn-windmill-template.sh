#!/usr/bin/env bash
set -euo pipefail

# Place the windmill via vanilla '/place template acm:windmill' at a specific X/Z, snapped to ground.
#
# Requirements:
# - Datapack installed and enabled in the current world (acm_windmills).
# - World present on disk at ./data/world (needed for offline heightmap lookup).
#
# Usage:
#   ./infra/spawn-windmill-template.sh --at 1000 -1400
#   ./infra/spawn-windmill-template.sh --at 1000 -1400 --heightmap MOTION_BLOCKING_NO_LEAVES

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

source ./infra/prefab-lib.sh

world="./data/world"
template="acm:windmill_template"
x=""
z=""
heightmap_type="MOTION_BLOCKING_NO_LEAVES"

usage() {
  cat <<EOF >&2
Usage:
  $0 --at <x> <z> [--world <path>] [--template <id>] [--heightmap <type>]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --at) x="${2:?}"; z="${3:?}"; shift 3;;
    --world) world="${2:?}"; shift 2;;
    --template) template="${2:?}"; shift 2;;
    --heightmap) heightmap_type="${2:?}"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2;;
  esac
done

for v in "${x}" "${z}"; do
  if ! [[ "${v}" =~ ^-?[0-9]+$ ]]; then
    echo "Invalid --at (expected integers): x=${x} z=${z}" >&2
    exit 2
  fi
done

if [[ -z "${x}" || -z "${z}" ]]; then
  echo "Missing --at <x> <z>" >&2
  usage
  exit 2
fi

if [[ ! -d "${world}/region" ]]; then
  echo "World not found or not generated yet: ${world}/region" >&2
  exit 2
fi

if [[ ! -f "./infra/world-height-at.py" ]]; then
  echo "Missing helper: ./infra/world-height-at.py" >&2
  exit 2
fi

cmd_try() { prefab_cmd_try "$1"; }

gy="$(python3 ./infra/world-height-at.py --world "${world}" --x "${x}" --z "${z}" --type "${heightmap_type}")"
if [[ -z "${gy}" ]]; then
  echo "Failed to compute ground Y at x=${x} z=${z}" >&2
  exit 1
fi

cmd_try "forceload add ${x} ${z} ${x} ${z}"
sleep 2
cmd_try "place template ${template} ${x} ${gy} ${z}"
cmd_try "forceload remove ${x} ${z} ${x} ${z}"

echo "OK"
