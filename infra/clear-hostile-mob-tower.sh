#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

source ./infra/prefab-lib.sh

player="${DEFAULT_PLAYER_NAME:-PlayerName}"
at_mode="false"
at_x=""
at_y=""
at_z=""
dx="24"
dy="0"
dz="0"
floors="3"
forceload="false"
json_out=""

usage() {
  cat <<EOF
Usage:
  $0 [--player <name> | --at <x> <y> <z>] [--dx <int>] [--dy <int>] [--dz <int>]
     [--floors <int>] [--forceload] [--json-out <path>]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --player)
      player="${2:?}"
      shift 2
      ;;
    --at)
      at_mode="true"
      at_x="${2:?}"
      at_y="${3:?}"
      at_z="${4:?}"
      shift 4
      ;;
    --dx)
      dx="${2:?}"
      shift 2
      ;;
    --dy)
      dy="${2:?}"
      shift 2
      ;;
    --dz)
      dz="${2:?}"
      shift 2
      ;;
    --floors)
      floors="${2:?}"
      shift 2
      ;;
    --forceload)
      forceload="true"
      shift
      ;;
    --json-out)
      json_out="${2:?}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

for v in "${dx}" "${dy}" "${dz}" "${floors}"; do
  if ! [[ "${v}" =~ ^-?[0-9]+$ ]]; then
    echo "Invalid integer argument: ${v}" >&2
    exit 2
  fi
done

if [[ "${at_mode}" == "true" ]]; then
  for v in "${at_x}" "${at_y}" "${at_z}"; do
    if ! [[ "${v}" =~ ^-?[0-9]+$ ]]; then
      echo "Invalid --at coordinate: ${v}" >&2
      exit 2
    fi
  done
fi

if (( floors < 1 || floors > 5 )); then
  echo "Invalid --floors (expected 1..5): ${floors}" >&2
  exit 2
fi

cmd() { prefab_cmd "$1"; }
cmd_try() { prefab_cmd_try "$1"; }

tell_target() {
  local msg="$*"
  if [[ "${at_mode}" == "true" ]]; then
    cmd_try "say [SPAWN] ${msg}"
  else
    cmd_try "tell ${player} [SPAWN] ${msg}"
  fi
}

resolve_player_origin() {
  local prev_line pos_line px py pz
  prev_line="$(docker logs cobblemon --tail 400 2>/dev/null | grep -F "${player} has the following entity data" | tail -n 1 || true)"
  ./infra/mc.sh "data get entity ${player} Pos" >/dev/null 2>&1 || true
  pos_line=""
  for _ in $(seq 1 30); do
    pos_line="$(docker logs cobblemon --tail 400 2>/dev/null | grep -F "${player} has the following entity data" | tail -n 1 || true)"
    if [[ -n "${pos_line}" && "${pos_line}" != "${prev_line}" ]]; then
      break
    fi
    sleep 0.2
  done
  if [[ -z "${pos_line}" || "${pos_line}" == "${prev_line}" ]]; then
    echo "Failed to read player position from logs. Is ${player} online?" >&2
    exit 1
  fi

  read -r px py pz < <(echo "${pos_line}" | sed -nE 's/.*\[(-?[0-9.]+)d, (-?[0-9.]+)d, (-?[0-9.]+)d\].*/\1 \2 \3/p')
  python3 - <<PY
import math
print(math.floor(float("${px}")), math.floor(float("${py}")) - 1, math.floor(float("${pz}")))
PY
}

if [[ "${at_mode}" == "true" ]]; then
  base_x="${at_x}"
  base_y="${at_y}"
  base_z="${at_z}"
  mode_label="absolute"
else
  read -r base_x base_y base_z < <(resolve_player_origin)
  mode_label="player"
fi

X0=$((base_x + dx))
Y0=$((base_y + dy))
Z0=$((base_z + dz))

FIRST_FLOOR_Y=$((Y0 + 22))
TOP_Y=$((FIRST_FLOOR_Y + (floors - 1) * 5 + 4))
ROOF_Y=$((TOP_Y + 1))
OUTER_X1=$((X0 - 8))
OUTER_X2=$((X0 + 9))
OUTER_Z1=$((Z0 - 8))
OUTER_Z2=$((Z0 + 9))
ROOM_X1=$((X0 - 3))
ROOM_X2=$((X0 + 4))
ROOM_Z1=$((Z0 + 3))
ROOM_Z2=$((Z0 + 7))
LADDER_X=$((OUTER_X1 - 1))
LADDER_Z="${Z0}"

BUILD_X1="${LADDER_X}"
BUILD_X2="${OUTER_X2}"
BUILD_Y1="${Y0}"
BUILD_Y2=$((ROOF_Y + 1))
BUILD_Z1="${OUTER_Z1}"
BUILD_Z2="${OUTER_Z2}"
CHUNK_X1=$((BUILD_X1 >> 4))
CHUNK_X2=$((BUILD_X2 >> 4))
CHUNK_Z1=$((BUILD_Z1 >> 4))
CHUNK_Z2=$((BUILD_Z2 >> 4))
FORCELOAD_PY="False"
if [[ "${forceload}" == "true" ]]; then FORCELOAD_PY="True"; fi

forceload_added="false"
cleanup_forceload() {
  if [[ "${forceload}" == "true" && "${forceload_added}" == "true" ]]; then
    ./infra/mc.sh "forceload remove ${BUILD_X1} ${BUILD_Z1} ${BUILD_X2} ${BUILD_Z2}" >/dev/null 2>&1 || true
  fi
}
trap cleanup_forceload EXIT

clear_fill() {
  local x1="${1:?}" y1="${2:?}" z1="${3:?}" x2="${4:?}" y2="${5:?}" z2="${6:?}" block="${7:?}"
  cmd "fill ${x1} ${y1} ${z1} ${x2} ${y2} ${z2} minecraft:air replace ${block}"
}

clear_block() {
  local x="${1:?}" y="${2:?}" z="${3:?}" block="${4:?}"
  cmd "fill ${x} ${y} ${z} ${x} ${y} ${z} minecraft:air replace ${block}"
}

run_generated_cleanup() {
  python3 - <<PY | while IFS= read -r mc_command; do
from pathlib import Path
import sys

sys.path.insert(0, str(Path("./infra").resolve()))
from hostile_mob_tower_spec import build_operations, water_channel_positions

seen = set()
for op in build_operations((${X0}, ${Y0}, ${Z0}), ${floors}, include_clear=False):
    if op.block == "minecraft:air":
        continue
    if op.kind == "fill":
        cmd = f"fill {op.x1} {op.y1} {op.z1} {op.x2} {op.y2} {op.z2} minecraft:air replace {op.block}"
    else:
        cmd = f"fill {op.x1} {op.y1} {op.z1} {op.x1} {op.y1} {op.z1} minecraft:air replace {op.block}"
    if cmd not in seen:
        seen.add(cmd)
        print(cmd)

for x, y, z in sorted(water_channel_positions((${X0}, ${Y0}, ${Z0}), ${floors})):
    cmd = f"fill {x} {y} {z} {x} {y} {z} minecraft:air replace minecraft:water"
    if cmd not in seen:
        seen.add(cmd)
        print(cmd)
PY
    [[ -n "${mc_command}" ]] || continue
    cmd "${mc_command}"
  done
}

write_json() {
  [[ -z "${json_out}" ]] && return 0
  JSON_OUT="${json_out}" python3 - <<PY
import json
import os
from pathlib import Path

payload = {
    "schema_version": 1,
    "kind": "hostile_mob_tower_cleanup",
    "mode": "${mode_label}",
    "player": None if "${at_mode}" == "true" else "${player}",
    "origin": {"x": ${X0}, "y": ${Y0}, "z": ${Z0}},
    "inputs": {
        "base": {"x": ${base_x}, "y": ${base_y}, "z": ${base_z}},
        "dx": ${dx},
        "dy": ${dy},
        "dz": ${dz},
        "floors": ${floors},
        "forceload": ${FORCELOAD_PY},
    },
    "bbox": {"x1": ${BUILD_X1}, "y1": ${BUILD_Y1}, "z1": ${BUILD_Z1}, "x2": ${BUILD_X2}, "y2": ${BUILD_Y2}, "z2": ${BUILD_Z2}},
    "chunk_box": {"x1": ${CHUNK_X1}, "z1": ${CHUNK_Z1}, "x2": ${CHUNK_X2}, "z2": ${CHUNK_Z2}},
}
path = Path(os.environ["JSON_OUT"])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
PY
}

tell_target "Hostile tower: targeted cleanup start."

if [[ "${forceload}" == "true" ]]; then
  ./infra/mc.sh "forceload add ${BUILD_X1} ${BUILD_Z1} ${BUILD_X2} ${BUILD_Z2}" >/dev/null
  forceload_added="true"
fi

run_generated_cleanup

write_json
tell_target "Hostile tower: targeted cleanup done."
echo "OK"
