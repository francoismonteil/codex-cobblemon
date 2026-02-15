#!/usr/bin/env bash
set -euo pipefail

# Wrapper around infra/prefab-score.py.
#
# Supports 2 input modes:
# 1) Bounding box:
#    ./infra/prefab-score.sh [opts] x1 y1 z1 x2 y2 z2
# 2) 4 corners (same workflow as prefab builders):
#    ./infra/prefab-score.sh [opts] --height 22 FLx FLy FLz FRx FRy FRz BLx BLy BLz BRx BRy BRz

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

source ./infra/prefab-lib.sh

world="./data/world"
dimension="overworld"
profile="generic"
facing=""
nav_start_mode="inside_cell"
doors_passable="true"
trapdoors_passable="true"
floor_y=""
label=""
say="false"
height="22"

args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --world) world="${2:?}"; shift 2 ;;
    --dimension) dimension="${2:?}"; shift 2 ;;
    --profile) profile="${2:?}"; shift 2 ;;
    --facing) facing="${2:?}"; shift 2 ;;
    --nav-start-mode) nav_start_mode="${2:?}"; shift 2 ;;
    --doors-passable) doors_passable="${2:?}"; shift 2 ;;
    --trapdoors-passable) trapdoors_passable="${2:?}"; shift 2 ;;
    --floor-y) floor_y="${2:?}"; shift 2 ;;
    --label) label="${2:?}"; shift 2 ;;
    --height) height="${2:?}"; shift 2 ;;
    --say) say="true"; shift ;;
    -h|--help)
      cat <<EOF
Usage:
  $0 [opts] x1 y1 z1 x2 y2 z2
  $0 [opts] --height 22 FLx FLy FLz FRx FRy FRz BLx BLy BLz BRx BRy BRz

Opts:
  --world <dir>                 (default: ./data/world)
  --dimension overworld|nether|end
  --profile generic|pokecenter
  --facing north|south|east|west
  --nav-start-mode door_cell|inside_cell|both (default: inside_cell)
  --doors-passable true|false   (default: true)
  --trapdoors-passable true|false (default: true)
  --floor-y <int>               (default: y1)
  --label <text>
  --height <int>                (only for 4-corners mode, default: 22)
  --say                         Send short summary to in-game chat
EOF
      exit 0
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

if [[ ${#args[@]} -ne 6 && ${#args[@]} -ne 12 ]]; then
  echo "ERROR: expected 6 (box) or 12 (4 corners) numbers, got ${#args[@]}." >&2
  exit 2
fi

py_args=(
  ./infra/prefab-score.py
  --world "${world}"
  --dimension "${dimension}"
  --profile "${profile}"
  --nav-start-mode "${nav_start_mode}"
  --doors-passable "${doors_passable}"
  --trapdoors-passable "${trapdoors_passable}"
)
if [[ -n "${facing}" ]]; then py_args+=(--facing "${facing}"); fi
if [[ -n "${label}" ]]; then py_args+=(--label "${label}"); fi
if [[ "${say}" == "true" ]]; then py_args+=(--say); fi

if [[ ${#args[@]} -eq 6 ]]; then
  if [[ -z "${floor_y}" ]]; then floor_y="${args[1]}"; fi
  py_args+=(--floor-y "${floor_y}")
  py_args+=("${args[@]}")
else
  read -r X1 X2 Y Z1 Z2 < <(prefab_snap_rect_floor "${args[@]}")
  if (( X1 > X2 )); then t="${X1}"; X1="${X2}"; X2="${t}"; fi
  if (( Z1 > Z2 )); then t="${Z1}"; Z1="${Z2}"; Z2="${t}"; fi
  y1="${Y}"
  y2=$((Y + height))
  py_args+=(--floor-y "${Y}")
  py_args+=("${X1}" "${y1}" "${Z1}" "${X2}" "${y2}" "${Z2}")
fi

python3 "${py_args[@]}"
