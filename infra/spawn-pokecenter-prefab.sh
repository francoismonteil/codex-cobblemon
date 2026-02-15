#!/usr/bin/env bash
set -euo pipefail

# Builds a Kanto-style "Pokemon Center" prefab (vanilla blocks + Cobblemon blocks)
# using only server console commands (no WorldEdit), at coordinates derived from
# the 4 provided corner points (workflow: 4 corners -> rectangle).
#
# Input coords can be floats (e.g., player position). We snap them to the block
# grid using FLOOR (not truncate), so negative coordinates behave correctly.
#
# Target footprint:
# - 12x10 blocks (facade on the 12 side), wall height = 4, hip roof (stepped) with a low cap (less pointy).
# - Minimum for full details (logo + complex roof): 9x7. If smaller, we fall back to a simpler roof and skip logo.
#
# Coordinates format (positional):
#   FLx FLy FLz  FRx FRy FRz  BLx BLy BLz  BRx BRy BRz
#
# Example:
#   ./infra/spawn-pokecenter-prefab.sh --variant decorated --facing west \
#     420.7 70 -1510.3  420.7 70 -1498.3  434.7 70 -1510.3  434.7 70 -1498.3
#
# Options:
#   --variant basic|decorated          (default: basic)
#   --facing north|south|east|west     (default: west; preserves legacy "front at x=min" behavior)
#   --size <width> <depth>             (default: 12 10; only applies in 1-point mode)
#   --no-clear                         Don't clear the build volume first.
#   --no-score                         Don't compute a quality score after building.
#   --strict                           Fail fast if a blockstate/command is invalid (default is best-effort).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

source ./infra/prefab-lib.sh

no_clear="false"
variant="basic"
facing="west"
strict="false"
do_score="true"
target_w="12"
target_d="10"
template_state="./data/.pokecenter/template-12x10-decorated-west.txt"
args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --variant)
      variant="${2:-}"
      shift 2
      ;;
    --facing)
      facing="${2:-}"
      shift 2
      ;;
    --size)
      target_w="${2:-}"
      target_d="${3:-}"
      shift 3
      ;;
    --no-clear)
      no_clear="true"
      shift
      ;;
    --no-score)
      do_score="false"
      shift
      ;;
    --strict)
      strict="true"
      shift
      ;;
    -h|--help)
      cat <<EOF
Usage:
  $0 [opts] <front_left_x> <front_left_y> <front_left_z>
  $0 [opts] FLx FLy FLz FRx FRy FRz BLx BLy BLz BRx BRy BRz

Opts:
  --variant basic|decorated
  --facing north|south|east|west
  --size <width> <depth>           (only for 1-point mode; default: 12 10)
  --no-clear
  --no-score
  --strict
EOF
      exit 0
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

if [[ "${variant}" != "basic" && "${variant}" != "decorated" ]]; then
  echo "Invalid --variant (expected basic|decorated): ${variant}" >&2
  exit 2
fi

if [[ "${facing}" != "north" && "${facing}" != "south" && "${facing}" != "east" && "${facing}" != "west" ]]; then
  echo "Invalid --facing (expected north|south|east|west): ${facing}" >&2
  exit 2
fi

if ! [[ "${target_w}" =~ ^[0-9]+$ ]] || ! [[ "${target_d}" =~ ^[0-9]+$ ]]; then
  echo "Invalid --size (expected 2 positive integers): ${target_w} ${target_d}" >&2
  exit 2
fi
if (( target_w < 3 || target_d < 3 )); then
  echo "Invalid --size (too small; need at least 3x3): ${target_w} ${target_d}" >&2
  exit 2
fi

if [[ ${#args[@]} -ne 3 && ${#args[@]} -ne 12 ]]; then
  echo "Usage:" >&2
  echo "  $0 [--variant basic|decorated] [--facing north|south|east|west] [--size <w> <d>] [--no-clear] [--no-score] [--strict] <front_left_x> <front_left_y> <front_left_z>" >&2
  echo "  $0 [--variant basic|decorated] [--facing north|south|east|west] [--no-clear] [--no-score] [--strict] FLx FLy FLz FRx FRy FRz BLx BLy BLz BRx BRy BRz" >&2
  exit 2
fi

if [[ ${#args[@]} -eq 3 ]]; then
  read -r FLX FLY FLZ < <(prefab_snap_point_floor "${args[@]}")
  Y="${FLY}"

  # Derive the rectangle from a "front-left" anchor (outside perspective), respecting --facing.
  case "${facing}" in
    west)
      # front is x1, into is +x, right is +z
      X1="${FLX}"
      X2=$((FLX + target_d - 1))
      Z1="${FLZ}"
      Z2=$((FLZ + target_w - 1))
      ;;
    east)
      # front is x2, into is -x, right is -z
      X2="${FLX}"
      X1=$((FLX - target_d + 1))
      Z2="${FLZ}"
      Z1=$((FLZ - target_w + 1))
      ;;
    south)
      # front is z2, into is -z, right is +x
      X1="${FLX}"
      X2=$((FLX + target_w - 1))
      Z2="${FLZ}"
      Z1=$((FLZ - target_d + 1))
      ;;
    north)
      # front is z1, into is +z, right is -x
      X2="${FLX}"
      X1=$((FLX - target_w + 1))
      Z1="${FLZ}"
      Z2=$((FLZ + target_d - 1))
      ;;
    *)
      echo "Invalid --facing: ${facing}" >&2
      exit 2
      ;;
  esac
else
  read -r X1 X2 Y Z1 Z2 < <(prefab_snap_rect_floor "${args[@]}")
fi

if (( X1 > X2 )); then t="${X1}"; X1="${X2}"; X2="${t}"; fi
if (( Z1 > Z2 )); then t="${Z1}"; Z1="${Z2}"; Z2="${t}"; fi

DX=$((X2 - X1 + 1))
DZ=$((Z2 - Z1 + 1))

echo "== Pokecenter prefab =="
echo "variant: ${variant}"
echo "facing: ${facing}"
echo "snapped_rect:"
echo "  x: ${X1}..${X2} (dx=${DX})"
echo "  z: ${Z1}..${Z2} (dz=${DZ})"
echo "  y: ${Y}"

cmd() { prefab_cmd "$1"; }
cmd_try() { prefab_cmd_try "$1"; }

YF="${Y}"
Y1=$((YF+1))
Y2=$((YF+2))
Y3=$((YF+3))
Y4=$((YF+4))
Y5=$((YF+5))

XI1=$((X1+1)); XI2=$((X2-1))
ZI1=$((Z1+1)); ZI2=$((Z2-1))

if (( XI1 > XI2 || ZI1 > ZI2 )); then
  echo "ERROR: rectangle too small to hollow (need at least 3x3)." >&2
  exit 1
fi

# Local axes for orienting entrance and interior.
read -r AX AZ WIDTH DEPTH DXR DZR DXF DZF IN_DIR RIGHT_DIR < <(prefab_local_axes "${facing}" "${X1}" "${X2}" "${Z1}" "${Z2}")
echo "local_dims: w=${WIDTH} d=${DEPTH} (target: 12x10)"
if (( WIDTH != 12 || DEPTH != 10 )); then
  echo "NOTE: target footprint is 12x10 (w x d); building best-effort in w=${WIDTH} d=${DEPTH}." >&2
fi

clear_volume() {
  echo "== Clear volume =="
  if [[ "${no_clear}" != "true" ]]; then
    # Clear up to a safe height (walls + roof). Keep it bounded to avoid large /fill.
    local clear_top=$((YF+22))
    cmd "fill ${X1} ${YF} ${Z1} ${X2} ${clear_top} ${Z2} minecraft:air replace"
  fi
}

M_FOUNDATION="minecraft:stone_bricks"
M_WALL="minecraft:white_concrete"
M_CORNER_LOG="minecraft:oak_log[axis=y]"
M_STRIPE="minecraft:red_concrete"
M_WINDOW="minecraft:white_stained_glass_pane"
# Use a roof block that has matching stairs/slabs to keep the hip roof coherent.
M_ROOF="minecraft:red_nether_bricks"
M_ROOF_STAIRS="minecraft:red_nether_brick_stairs"
M_ROOF_SLAB="minecraft:red_nether_brick_slab"
M_COUNTER="minecraft:smooth_quartz"
M_COUNTER_SLAB="minecraft:quartz_slab"

want_full="true"
if (( WIDTH < 9 || DEPTH < 7 )); then
  want_full="false"
fi

# Local helpers (based on AX/AZ/DXR/DZR/DXF/DZF computed from --facing).
l2w_point() { prefab_l2w_point_xz "${AX}" "${AZ}" "${DXR}" "${DZR}" "${DXF}" "${DZF}" "$1" "$2"; }
l2w_rect() { prefab_l2w_rect_xz "${AX}" "${AZ}" "${DXR}" "${DZR}" "${DXF}" "${DZF}" "$1" "$2" "$3" "$4"; }

fill_l() {
  local u1="$1" v1="$2" u2="$3" v2="$4" y1="$5" y2="$6" block="$7" mode="${8:-replace}"
  if (( u1 > u2 )); then local t="${u1}"; u1="${u2}"; u2="${t}"; fi
  if (( v1 > v2 )); then local t="${v1}"; v1="${v2}"; v2="${t}"; fi

  # Never write outside the snapped rectangle footprint.
  if (( u1 < 0 )); then u1=0; fi
  if (( v1 < 0 )); then v1=0; fi
  if (( u2 > WIDTH-1 )); then u2=$((WIDTH-1)); fi
  if (( v2 > DEPTH-1 )); then v2=$((DEPTH-1)); fi
  if (( u1 > u2 || v1 > v2 )); then
    return 0
  fi

  read -r x1 z1 x2 z2 < <(l2w_rect "${u1}" "${v1}" "${u2}" "${v2}")
  if [[ "${strict}" == "true" ]]; then
    cmd "fill ${x1} ${y1} ${z1} ${x2} ${y2} ${z2} ${block} ${mode}"
  else
    cmd_try "fill ${x1} ${y1} ${z1} ${x2} ${y2} ${z2} ${block} ${mode}"
  fi
}

setblock_l() {
  local u="$1" v="$2" y="$3" block="$4" mode="${5:-replace}"
  if (( u < 0 || u > WIDTH-1 || v < 0 || v > DEPTH-1 )); then
    return 0
  fi
  read -r x z < <(l2w_point "${u}" "${v}")
  if [[ "${strict}" == "true" ]]; then
    cmd "setblock ${x} ${y} ${z} ${block} ${mode}"
  else
    cmd_try "setblock ${x} ${y} ${z} ${block} ${mode}"
  fi
}

build_from_template_if_available() {
  # If you manually tweak the prefab in-game, capture it with:
  #   ./infra/pokecenter-template-capture.sh
  # Then we can reproduce it exactly with /clone (including tricky blockstates).
  local state_file="${1:?}"

  if [[ ! -f "${state_file}" ]]; then
    return 1
  fi

  local tmpl_x1="" tmpl_y1="" tmpl_z1="" tmpl_x2="" tmpl_y2="" tmpl_z2=""
  local k v
  while IFS='=' read -r k v; do
    case "${k}" in
      dst_x1) tmpl_x1="${v}" ;;
      dst_y1) tmpl_y1="${v}" ;;
      dst_z1) tmpl_z1="${v}" ;;
      dst_x2) tmpl_x2="${v}" ;;
      dst_y2) tmpl_y2="${v}" ;;
      dst_z2) tmpl_z2="${v}" ;;
    esac
  done <"${state_file}"

  for vv in "${tmpl_x1}" "${tmpl_y1}" "${tmpl_z1}" "${tmpl_x2}" "${tmpl_y2}" "${tmpl_z2}"; do
    if ! [[ "${vv}" =~ ^-?[0-9]+$ ]]; then
      echo "WARN: template state invalid (non-int): ${state_file}" >&2
      return 1
    fi
  done

  local tdx=$((tmpl_x2 - tmpl_x1 + 1))
  local tdy=$((tmpl_y2 - tmpl_y1 + 1))
  local tdz=$((tmpl_z2 - tmpl_z1 + 1))
  local want_dy=23
  if (( tdx != DX || tdz != DZ || tdy != want_dy )); then
    echo "WARN: template dims mismatch (tmpl ${tdx}x${tdy}x${tdz}, want ${DX}x${want_dy}x${DZ}); falling back to procedural build." >&2
    return 1
  fi

  echo "== Build from template (clone) =="
  echo "template: ${state_file}"
  echo "src: x=${tmpl_x1}..${tmpl_x2} y=${tmpl_y1}..${tmpl_y2} z=${tmpl_z1}..${tmpl_z2}"
  echo "dst: x=${X1}..${X2} y=${YF}..$((YF+want_dy-1)) z=${Z1}..${Z2}"

  # Best-effort: move the admin away if they're in the destination volume.
  local admin_player="${DEFAULT_PLAYER_NAME:-}"
  if [[ -n "${admin_player}" ]]; then
    cmd_try "execute as ${admin_player} if entity @s[x=${X1},y=$((YF-10)),z=${Z1},dx=$((DX-1)),dy=50,dz=$((DZ-1))] run tp @s 400 81 -1488"
  else
    echo "WARN: DEFAULT_PLAYER_NAME is empty; skipping safety teleport." >&2
  fi

  # /clone requires source and destination chunks to be loaded. Use a short forceload.
  cmd_try "forceload add ${tmpl_x1} ${tmpl_z1} ${tmpl_x2} ${tmpl_z2}"
  cmd_try "forceload add ${X1} ${Z1} ${X2} ${Z2}"
  sleep 1

  # /clone copies air too, so it fully overwrites the destination.
  cmd "clone ${tmpl_x1} ${tmpl_y1} ${tmpl_z1} ${tmpl_x2} ${tmpl_y2} ${tmpl_z2} ${X1} ${YF} ${Z1} replace force"

  cmd_try "forceload remove ${tmpl_x1} ${tmpl_z1} ${tmpl_x2} ${tmpl_z2}"
  cmd_try "forceload remove ${X1} ${Z1} ${X2} ${Z2}"
  return 0
}

build_shell() {
  clear_volume

  echo "== Foundation + floor =="
  cmd "fill ${X1} ${YF} ${Z1} ${X2} ${YF} ${Z2} ${M_FOUNDATION} replace"
  if (( XI1 <= XI2 && ZI1 <= ZI2 )); then
    cmd "fill ${XI1} ${YF} ${ZI1} ${XI2} ${YF} ${ZI2} ${M_WALL} replace"
  fi

  echo "== Walls (stone base + white concrete) =="
  cmd "fill ${X1} ${Y1} ${Z1} ${X2} ${Y1} ${Z2} ${M_FOUNDATION} replace"
  cmd "fill ${XI1} ${Y1} ${ZI1} ${XI2} ${Y1} ${ZI2} minecraft:air replace"

  cmd "fill ${X1} ${Y2} ${Z1} ${X2} ${Y4} ${Z2} ${M_WALL} replace"
  cmd "fill ${XI1} ${Y2} ${ZI1} ${XI2} ${Y4} ${ZI2} minecraft:air replace"

  echo "== Red band under roof =="
  cmd "fill $((X1+1)) ${Y4} ${Z1} $((X2-1)) ${Y4} ${Z1} ${M_STRIPE} replace"
  cmd "fill $((X1+1)) ${Y4} ${Z2} $((X2-1)) ${Y4} ${Z2} ${M_STRIPE} replace"
  cmd "fill ${X1} ${Y4} $((Z1+1)) ${X1} ${Y4} $((Z2-1)) ${M_STRIPE} replace"
  cmd "fill ${X2} ${Y4} $((Z1+1)) ${X2} ${Y4} $((Z2-1)) ${M_STRIPE} replace"

  echo "== Corner logs =="
  cmd "fill ${X1} ${Y1} ${Z1} ${X1} ${Y4} ${Z1} ${M_CORNER_LOG} replace"
  cmd "fill ${X1} ${Y1} ${Z2} ${X1} ${Y4} ${Z2} ${M_CORNER_LOG} replace"
  cmd "fill ${X2} ${Y1} ${Z1} ${X2} ${Y4} ${Z1} ${M_CORNER_LOG} replace"
  cmd "fill ${X2} ${Y1} ${Z2} ${X2} ${Y4} ${Z2} ${M_CORNER_LOG} replace"
}

place_doors_2wide_auto() {
  # 2-wide entrance: 2 doors, auto-open via pressure plates.
  # Door facing should point "into" the building for consistent visuals across orientations.
  local door_u1="$1" door_v="$2"
  local u_left="${door_u1}" u_right="$((door_u1+1))"
  local v_out="$((door_v-1))"
  local v_in="$((door_v+1))"

  # Clear the 2-wide, 2-tall opening.
  fill_l "${u_left}" "${door_v}" "${u_right}" "${door_v}" "${Y1}" "${Y2}" "minecraft:air" "replace"

  # Double door.
  setblock_l "${u_left}" "${door_v}" "${Y1}" "minecraft:oak_door[facing=${IN_DIR},half=lower,hinge=left,open=false,powered=false]"
  setblock_l "${u_left}" "${door_v}" "${Y2}" "minecraft:oak_door[facing=${IN_DIR},half=upper,hinge=left,open=false,powered=false]"
  setblock_l "${u_right}" "${door_v}" "${Y1}" "minecraft:oak_door[facing=${IN_DIR},half=lower,hinge=right,open=false,powered=false]"
  setblock_l "${u_right}" "${door_v}" "${Y2}" "minecraft:oak_door[facing=${IN_DIR},half=upper,hinge=right,open=false,powered=false]"

  # Auto-open (pressure plates). Plates are passable in-game and work with both wooden/iron doors.
  if (( v_out >= 0 )); then
    setblock_l "${u_left}" "${v_out}" "${Y1}" "minecraft:stone_pressure_plate"
    setblock_l "${u_right}" "${v_out}" "${Y1}" "minecraft:stone_pressure_plate"
  fi
  if (( v_in <= DEPTH-1 )); then
    setblock_l "${u_left}" "${v_in}" "${Y1}" "minecraft:stone_pressure_plate"
    setblock_l "${u_right}" "${v_in}" "${Y1}" "minecraft:stone_pressure_plate"
  fi
}

build_facade_basic() {
  echo "== Facade (basic entrance) =="
  local door_u1=$(((WIDTH - 2) / 2))
  local u_left="${door_u1}" u_right="$((door_u1+1))"
  # Make a shallow recess so the outer pressure plates can sit in front of the doors.
  fill_l "${u_left}" 0 "${u_right}" 0 "${Y1}" "${Y2}" "minecraft:air" "replace"
  place_doors_2wide_auto "${door_u1}" 1
}

build_facade_decorated() {
  echo "== Facade (entrance + logo) =="

  local porch_u1=$(((WIDTH - 5) / 2))
  local door_u1=$(((WIDTH - 2) / 2))
  local porch_u2=$((porch_u1+4))
  local door_u2=$((door_u1+1))
  local center_u=$((WIDTH/2))

  # Carve a 1-block deep porch (front wall), keep the red band at y=Y4 intact.
  fill_l "${porch_u1}" 0 "${porch_u2}" 0 "${Y1}" "${Y3}" "minecraft:air" "replace"

  # Porch pillars for a "Kanto chill" vibe.
  fill_l "${porch_u1}" 0 "${porch_u1}" 0 "${Y1}" "${Y3}" "${M_CORNER_LOG}" "replace"
  fill_l "${porch_u2}" 0 "${porch_u2}" 0 "${Y1}" "${Y3}" "${M_CORNER_LOG}" "replace"

  # Recessed inner facade wall (v=1).
  fill_l "${porch_u1}" 1 "${porch_u2}" 1 "${Y1}" "${Y1}" "${M_FOUNDATION}" "replace"
  fill_l "${porch_u1}" 1 "${porch_u2}" 1 "${Y2}" "${Y3}" "${M_WALL}" "replace"
  fill_l "${porch_u1}" 1 "${porch_u2}" 1 "${Y4}" "${Y4}" "${M_STRIPE}" "replace"

  # Door opening in the recessed wall.
  place_doors_2wide_auto "${door_u1}" 1

  # NOTE: avoid a low awning here. It inflates "boundary detail" and makes the facade relief
  # scanner think the facade is flat (because it fills v=0 around y=Y3).

  # Logo is applied later (after the roof), so it can sit on the facade/roof line cleanly.
}

build_windows() {
  echo "== Windows =="
  local door_u1=$(((WIDTH - 2) / 2))
  local door_u2=$((door_u1+1))
  # Only the entrance area is recessed (porch) in the full decorated build; windows should
  # stay on the outer wall unless they overlap the porch segment.
  local porch_u1=$(((WIDTH - 5) / 2))
  local porch_u2=$((porch_u1+4))

  place_front_windows() {
    local u_start="$1" u_end="$2"
    if (( u_start > u_end )); then
      return 0
    fi

    if [[ "${variant}" == "decorated" && "${want_full}" == "true" ]]; then
      # Avoid placing windows in the porch void (v=0 within porch_u1..porch_u2).
      # If the segment overlaps the porch, clamp/split around it.
      local left_end=$((porch_u1-1))
      local right_start=$((porch_u2+1))

      local s e
      s="${u_start}"; e="${u_end}"
      if (( s <= left_end )); then
        if (( e > left_end )); then e="${left_end}"; fi
        if (( s <= e )); then
          fill_l "${s}" 0 "${e}" 0 "${Y2}" "${Y3}" "${M_WINDOW}" "replace"
        fi
      fi

      s="${u_start}"; e="${u_end}"
      if (( e >= right_start )); then
        if (( s < right_start )); then s="${right_start}"; fi
        if (( s <= e )); then
          fill_l "${s}" 0 "${e}" 0 "${Y2}" "${Y3}" "${M_WINDOW}" "replace"
        fi
      fi

      return 0
    fi

    fill_l "${u_start}" 0 "${u_end}" 0 "${Y2}" "${Y3}" "${M_WINDOW}" "replace"
  }

  # Front windows (left/right of the entrance) if there's room.
  if (( WIDTH >= 11 )); then
    local fl_u1=$((door_u1-4)) fl_u2=$((door_u1-2))
    local fr_u1=$((door_u2+2)) fr_u2=$((door_u2+4))
    if (( fl_u1 < 1 )); then fl_u1=1; fi
    if (( fl_u2 > WIDTH-2 )); then fl_u2=$((WIDTH-2)); fi
    if (( fr_u1 < 1 )); then fr_u1=1; fi
    if (( fr_u2 > WIDTH-2 )); then fr_u2=$((WIDTH-2)); fi
    if (( fl_u1 <= fl_u2 )); then place_front_windows "${fl_u1}" "${fl_u2}"; fi
    if (( fr_u1 <= fr_u2 )); then place_front_windows "${fr_u1}" "${fr_u2}"; fi
  fi

  # Side windows (centered).
  local mid_v=$((DEPTH/2))
  local sv1=$((mid_v-1))
  local sv2=$((mid_v+1))
  if (( sv1 < 2 )); then sv1=2; fi
  if (( sv2 > DEPTH-3 )); then sv2=$((DEPTH-3)); fi
  if (( sv1 <= sv2 )); then
    local side_window_block="${M_WINDOW}"
    if [[ "${variant}" == "decorated" && "${want_full}" == "true" ]]; then
      # Keep the side walls walkable (no inset panes blocking headroom) while lowering boundary "detail_ratio".
      side_window_block="minecraft:white_stained_glass"
    fi
    fill_l 0 "${sv1}" 0 "${sv2}" "${Y2}" "${Y3}" "${side_window_block}" "replace"
    fill_l "$((WIDTH-1))" "${sv1}" "$((WIDTH-1))" "${sv2}" "${Y2}" "${Y3}" "${side_window_block}" "replace"
  fi

  # Back window (above the counter zone).
  local center_u=$((WIDTH/2))
  local bw1=$((center_u-2))
  local bw2=$((center_u+2))
  if (( bw1 < 2 )); then bw1=2; fi
  if (( bw2 > WIDTH-3 )); then bw2=$((WIDTH-3)); fi
  if (( bw1 <= bw2 )); then
    # Keep the back window on the boundary: insetting it would place panes above the Cobblemon kit row (v=DEPTH-2),
    # which can block headroom and make healer/PC "not accessible" for navigation scoring.
    fill_l "${bw1}" "$((DEPTH-1))" "${bw2}" "$((DEPTH-1))" "${Y2}" "${Y3}" "${M_WINDOW}" "replace"
  fi
}

build_roof_simple() {
  echo "== Roof (simple) =="
  cmd "fill ${X1} ${Y5} ${Z1} ${X2} ${Y5} ${Z2} ${M_ROOF} replace"
}

build_roof_hip() {
  echo "== Roof (hip) =="

  local xlo="${X1}" xhi="${X2}" zlo="${Z1}" zhi="${Z2}"
  local y="${Y5}"
  local sx sz
  local sx0=$((xhi - xlo + 1))
  local sz0=$((zhi - zlo + 1))
  local min0="${sx0}"
  if (( sz0 < min0 )); then min0="${sz0}"; fi
  # Stop on a centered flat cap to keep the roof lower and less pointy.
  local cap_min=5
  local cap_enabled="false"
  if (( min0 >= 9 )); then
    cap_enabled="true"
  fi

  while :; do
    sx=$((xhi - xlo + 1))
    sz=$((zhi - zlo + 1))

    cmd "fill ${xlo} ${y} ${zlo} ${xhi} ${y} ${zhi} ${M_ROOF} replace"

    # Perimeter detail: stairs on edges + slabs on corners. Best-effort for thin rectangles.
    if (( sx >= 2 && sz >= 2 )); then
      if (( sz > 2 )); then
        cmd_try "fill ${xlo} ${y} $((zlo+1)) ${xlo} ${y} $((zhi-1)) ${M_ROOF_STAIRS}[facing=east,half=bottom] replace"
        cmd_try "fill ${xhi} ${y} $((zlo+1)) ${xhi} ${y} $((zhi-1)) ${M_ROOF_STAIRS}[facing=west,half=bottom] replace"
      fi
      if (( sx > 2 )); then
        cmd_try "fill $((xlo+1)) ${y} ${zlo} $((xhi-1)) ${y} ${zlo} ${M_ROOF_STAIRS}[facing=south,half=bottom] replace"
        cmd_try "fill $((xlo+1)) ${y} ${zhi} $((xhi-1)) ${y} ${zhi} ${M_ROOF_STAIRS}[facing=north,half=bottom] replace"
      fi
      cmd_try "setblock ${xlo} ${y} ${zlo} ${M_ROOF_SLAB}[type=bottom] replace"
      cmd_try "setblock ${xlo} ${y} ${zhi} ${M_ROOF_SLAB}[type=bottom] replace"
      cmd_try "setblock ${xhi} ${y} ${zlo} ${M_ROOF_SLAB}[type=bottom] replace"
      cmd_try "setblock ${xhi} ${y} ${zhi} ${M_ROOF_SLAB}[type=bottom] replace"
    fi

    # Optional flat cap (less pointy + lower).
    if [[ "${cap_enabled}" == "true" ]] && (( sx <= cap_min || sz <= cap_min )); then
      break
    fi

    # Stop on a centered cap for even sizes (2x2 / 2x1 / 1x2) to avoid an off-center 1x1.
    # Add a tiny slab finish for thin caps (2x1 / 1x2) but keep a true 1x1 peak as a full block.
    if (( sx <= 2 && sz <= 2 )); then
      if ! (( sx == 1 && sz == 1 )); then
        cmd_try "setblock ${xlo} ${y} ${zlo} ${M_ROOF_SLAB}[type=bottom] replace"
        cmd_try "setblock ${xlo} ${y} ${zhi} ${M_ROOF_SLAB}[type=bottom] replace"
        cmd_try "setblock ${xhi} ${y} ${zlo} ${M_ROOF_SLAB}[type=bottom] replace"
        cmd_try "setblock ${xhi} ${y} ${zhi} ${M_ROOF_SLAB}[type=bottom] replace"
      fi
      break
    fi

    # Shrink each dimension toward 1x1, but never shrink past 2 to keep even caps centered.
    if (( sx > 2 )); then xlo=$((xlo+1)); xhi=$((xhi-1)); fi
    if (( sz > 2 )); then zlo=$((zlo+1)); zhi=$((zhi-1)); fi

    y=$((y+1))
  done
}

place_logo_pokeball() {
  echo "== Logo (pokeball) =="
  local center_u=$((WIDTH/2))

  local u1=$((center_u-2))
  local u2=$((center_u+2))
  # In decorated mode, the facade is recessed by 1 block (porch at v=0, wall at v=1).
  local v_logo=1

  # Keep the logo strictly on the facade (walls are Y2..Y4, roof starts at Y5).
  # With a 2-high window above the door, we draw a compact 5x2 Pokeball hint:
  # - Row Y4 (red stripe): B R R R B
  # - Row Y3 (band/button): B B W B B
  local y_stripe="${Y4}"
  local y_band="${Y3}"

  # Skip if we don't have enough margin from the facade edges.
  if (( u1 < 2 || u2 > WIDTH-3 )); then
    echo "NOTE: logo skipped (footprint too tight for 5-wide logo; w=${WIDTH})." >&2
    return 0
  fi

  # Ensure background exists where we draw.
  fill_l "${u1}" "${v_logo}" "${u2}" "${v_logo}" "${y_band}" "${y_band}" "${M_WALL}" "replace"
  fill_l "${u1}" "${v_logo}" "${u2}" "${v_logo}" "${y_stripe}" "${y_stripe}" "${M_STRIPE}" "replace"

  # Stripe row outline.
  setblock_l "${u1}" "${v_logo}" "${y_stripe}" "minecraft:black_concrete"
  setblock_l "${u2}" "${v_logo}" "${y_stripe}" "minecraft:black_concrete"

  # Band row + button.
  fill_l "${u1}" "${v_logo}" "${u2}" "${v_logo}" "${y_band}" "${y_band}" "minecraft:black_concrete" "replace"
  setblock_l "${center_u}" "${v_logo}" "${y_band}" "${M_WALL}"
}

build_interior_basic() {
  echo "== Interior (basic) =="
  local door_u1=$(((WIDTH - 2) / 2))
  local center_u=$((WIDTH/2))

  local v_entry_inside=1
  local machine_v=$((DEPTH-2))
  local counter_v=$((DEPTH-3))

  if (( machine_v <= v_entry_inside+1 )); then
    echo "NOTE: footprint too shallow for a full interior layout; placing kit near center." >&2
    machine_v=$((v_entry_inside+1))
    counter_v="${machine_v}"
  fi

  # Minimal carpet runner.
  if (( DEPTH >= 7 )); then
    fill_l "${door_u1}" "${v_entry_inside}" "$((door_u1+1))" "$((counter_v-1))" "${Y1}" "${Y1}" "minecraft:red_carpet" "replace"
  fi
  # Keep the door auto-open plates even if the carpet runner overwrote them.
  setblock_l "${door_u1}" 2 "${Y1}" "minecraft:stone_pressure_plate"
  setblock_l "$((door_u1+1))" 2 "${Y1}" "minecraft:stone_pressure_plate"

  # Simple counter + kit near the back.
  fill_l "$((center_u-2))" "${counter_v}" "$((center_u+2))" "${counter_v}" "${Y1}" "${Y1}" "${M_COUNTER}" "replace"
  setblock_l "${center_u}" "${machine_v}" "${Y1}" "cobblemon:healing_machine[facing=${facing}]"
  # PC: keep it inside the room (not embedded in a side wall) and face the entrance.
  local pc_u=$((WIDTH-2))
  local pc_v=$((DEPTH-2))
  if (( pc_u < 0 || pc_u > WIDTH-1 || pc_v < 0 || pc_v > DEPTH-1 )); then
    pc_u="$((center_u+1 <= WIDTH-2 ? center_u+1 : center_u-1))"
    pc_v="${machine_v}"
  fi
  # Cobblemon PC is a 2-block structure: place bottom + top so it doesn't look "upside down"/sunken.
  fill_l "${pc_u}" "${pc_v}" "${pc_u}" "${pc_v}" "${Y1}" "${Y2}" "minecraft:air" "replace"
  setblock_l "${pc_u}" "${pc_v}" "${Y1}" "cobblemon:pc[facing=${IN_DIR},part=bottom,on=false]"
  setblock_l "${pc_u}" "${pc_v}" "${Y2}" "cobblemon:pc[facing=${IN_DIR},part=top,on=false]"

  # Light.
  setblock_l "${center_u}" "$((v_entry_inside+2))" "${Y4}" "minecraft:lantern[hanging=true]"
}

build_interior_decorated() {
  echo "== Interior (decorated) =="
  local door_u1=$(((WIDTH - 2) / 2))
  local center_u=$((WIDTH/2))

  local v_entry_inside=2
  local machine_v=$((DEPTH-2))
  local counter_v=$((DEPTH-3))
  local counter_front_v=$((DEPTH-4))

  if (( machine_v <= v_entry_inside+2 )); then
    echo "NOTE: footprint too shallow for a full interior layout; using compact positions." >&2
    v_entry_inside=1
    machine_v=$((DEPTH-2))
    counter_v=$((DEPTH-3))
    counter_front_v=$((DEPTH-4))
  fi

  # Red carpet runner from door inward.
  if (( counter_front_v >= v_entry_inside )); then
    fill_l "${door_u1}" "${v_entry_inside}" "$((door_u1+1))" "${counter_front_v}" "${Y1}" "${Y1}" "minecraft:red_carpet" "replace"
  fi
  # Keep the door auto-open plates even if the carpet runner overwrote them.
  setblock_l "${door_u1}" 2 "${Y1}" "minecraft:stone_pressure_plate"
  setblock_l "$((door_u1+1))" 2 "${Y1}" "minecraft:stone_pressure_plate"

  # Reception counter.
  local cu1=$((center_u-3))
  local cu2=$((center_u+3))
  if (( cu1 < 2 )); then cu1=2; fi
  if (( cu2 > WIDTH-3 )); then cu2=$((WIDTH-3)); fi
  fill_l "${cu1}" "${counter_v}" "${cu2}" "${counter_v}" "${Y1}" "${Y1}" "${M_COUNTER}" "replace"
  if (( counter_front_v >= v_entry_inside )); then
    fill_l "${cu1}" "${counter_front_v}" "${cu2}" "${counter_front_v}" "${Y1}" "${Y1}" "${M_COUNTER_SLAB}[type=top]" "replace"
  fi

  # Cobblemon blocks (healing machine).
  setblock_l "${center_u}" "${machine_v}" "${Y1}" "cobblemon:healing_machine[facing=${facing}]"
  # PC: keep it inside the room (not embedded in a side wall) and face the entrance.
  local pc_u=$((WIDTH-2))
  local pc_v=$((DEPTH-2))
  if (( pc_u < 0 || pc_u > WIDTH-1 || pc_v < 0 || pc_v > DEPTH-1 )); then
    pc_u="$((center_u+1 <= WIDTH-2 ? center_u+1 : center_u-1))"
    pc_v="${machine_v}"
  fi
  # Cobblemon PC is a 2-block structure: place bottom + top so it doesn't look "upside down"/sunken.
  fill_l "${pc_u}" "${pc_v}" "${pc_u}" "${pc_v}" "${Y1}" "${Y2}" "minecraft:air" "replace"
  setblock_l "${pc_u}" "${pc_v}" "${Y1}" "cobblemon:pc[facing=${IN_DIR},part=bottom,on=false]"
  setblock_l "${pc_u}" "${pc_v}" "${Y2}" "cobblemon:pc[facing=${IN_DIR},part=top,on=false]"

  # Waiting benches (oak slabs).
  local bench_v=$((v_entry_inside+2))
  if (( WIDTH >= 13 && bench_v <= DEPTH-4 )); then
    fill_l 2 "${bench_v}" 4 "${bench_v}" "${Y1}" "${Y1}" "minecraft:oak_slab[type=bottom]" "replace"
    fill_l "$((WIDTH-5))" "${bench_v}" "$((WIDTH-3))" "${bench_v}" "${Y1}" "${Y1}" "minecraft:oak_slab[type=bottom]" "replace"
  fi

  # Warm lighting (hanging lanterns).
  local lv
  for lv in "$((v_entry_inside+2))" "$((v_entry_inside+5))" "$((counter_front_v))"; do
    if (( lv >= 2 && lv <= DEPTH-3 )); then
      setblock_l "${center_u}" "${lv}" "${Y4}" "minecraft:lantern[hanging=true]"
    fi
  done
}

echo "== Build mode =="
if [[ "${variant}" == "decorated" && "${want_full}" != "true" ]]; then
  echo "NOTE: footprint below 9x7 (w=${WIDTH}, d=${DEPTH}); disabling logo + complex roof." >&2
fi

built_via_template="false"
if [[ "${variant}" == "decorated" && "${facing}" == "west" ]] && (( WIDTH == 12 && DEPTH == 10 )) && [[ "${want_full}" == "true" ]]; then
  if build_from_template_if_available "${template_state}"; then
    built_via_template="true"
  fi
fi

if [[ "${built_via_template}" != "true" ]]; then
  build_shell

  if [[ "${variant}" == "decorated" && "${want_full}" == "true" ]]; then
    build_facade_decorated
  else
    build_facade_basic
  fi

  build_windows

  if [[ "${variant}" == "decorated" && "${want_full}" == "true" ]]; then
    build_roof_hip
  else
    build_roof_simple
  fi

  if [[ "${variant}" == "decorated" && "${want_full}" == "true" ]]; then
    place_logo_pokeball
  fi

  if [[ "${variant}" == "decorated" && "${want_full}" == "true" ]]; then
    build_interior_decorated
  else
    build_interior_basic
  fi
fi

cmd_try "say [SPAWN] Pokecenter prefab built (${variant}, facing=${facing}) at x=${X1}..${X2} y=${YF} z=${Z1}..${Z2}"

if [[ "${do_score}" == "true" ]]; then
  # Ensure chunks are flushed to disk before reading the world files.
  cmd_try "save-all flush"
  python3 ./infra/prefab-score.py --world ./data/world --profile pokecenter --facing "${facing}" --floor-y "${YF}" --label "Pokecenter(${variant})" --say \
    "${X1}" "${YF}" "${Z1}" "${X2}" "$((YF+22))" "${Z2}" || true
fi

echo "OK built pokecenter prefab (${variant})."
