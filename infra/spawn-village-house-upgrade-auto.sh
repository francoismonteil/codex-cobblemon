#!/usr/bin/env bash
set -euo pipefail

# Finds a suitable "house floor" spot in the spawn village and applies
# spawn-village-upgrade.sh there (healer+PC + subtle accents), without manual coords.
#
# Strategy:
# - Read world spawn from ./data/world/level.dat
# - Locate a POI that is inside a village house (prefer home/bed) near spawn
# - Try a small set of candidate offsets around that POI to find a 2-block-wide floor
#   (planks/stone) with enough air above for healer+PC placement
# - Apply ./infra/spawn-village-upgrade.sh at the found floor coords
#
# Usage:
#   ./infra/spawn-village-house-upgrade-auto.sh
#
# Notes:
# - SAFE by default: the upgrade script will refuse to place healer+PC if the target isn't air.
# - If no suitable spot is found, it exits with guidance for the manual flow.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

LOG_FILE="${REPO_ROOT}/data/logs/latest.log"

cmd() {
  ./infra/mc.sh "$1" >/dev/null
  sleep 0.12
}

now_utc() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

log_bytes() {
  stat -c%s "${LOG_FILE}" 2>/dev/null || echo 0
}

log_since_bytes() {
  local start_bytes="$1"
  local b=$((start_bytes+1))
  tail -c +"${b}" "${LOG_FILE}" 2>/dev/null || true
}

locate_poi_near() {
  local near_x="$1" near_y="$2" near_z="$3" poi="$4"
  local start_bytes out xyz x y z
  start_bytes="$(log_bytes)"

  cmd "execute in minecraft:overworld positioned ${near_x} ${near_y} ${near_z} run locate poi ${poi}"

  for _ in {1..45}; do
    out="$(log_since_bytes "${start_bytes}" | grep -E 'The nearest .* is at \[-?[0-9]+, [^,]+, -?[0-9]+\]' | tail -n 1 || true)"
    if [[ -n "${out}" ]]; then
      xyz="$(echo "${out}" | sed -E 's/.*\[(-?[0-9]+), ([^,]+), (-?[0-9]+)\].*/\1 \2 \3/')"
      read -r x y z <<<"${xyz}"
      if [[ "${x}" =~ ^-?[0-9]+$ ]] && [[ "${z}" =~ ^-?[0-9]+$ ]]; then
        if [[ "${y}" == "~" ]]; then
          y="${near_y}"
        fi
        if [[ "${y}" =~ ^-?[0-9]+$ ]]; then
          echo "${x} ${y} ${z}"
          return 0
        fi
      fi
    fi
    start_bytes="$(log_bytes)"
    sleep 0.3
  done

  return 1
}

say_marker_if_floor_ok() {
  # floor_block is optional; if empty, we only require "not air".
  local fx="$1" fy="$2" fz="$3" floor_block="$4" dir="$5" marker="$6"
  local start_bytes
  start_bytes="$(log_bytes)"

  # Conditions:
  # - 2-wide floor exists (depending on dir):
  #   - dir=x: (fx,fy,fz) and (fx+1,fy,fz)
  #   - dir=z: (fx,fy,fz) and (fx,fy,fz+1)
  # - 2-high air above each spot for headroom
  # - Target blocks for healer+PC (at y=fy+1) are air
  # Build floor checks:
  # - If floor_block is set: require that exact block
  # - Else: require "not air" (more permissive, higher hit rate)
  local floor1 floor2
  if [[ -n "${floor_block}" ]]; then
    floor1="if block ${fx} ${fy} ${fz} ${floor_block}"
  else
    floor1="unless block ${fx} ${fy} ${fz} minecraft:air"
  fi

  if [[ "${dir}" == "x" ]]; then
    if [[ -n "${floor_block}" ]]; then
      floor2="if block $((fx+1)) ${fy} ${fz} ${floor_block}"
    else
      floor2="unless block $((fx+1)) ${fy} ${fz} minecraft:air"
    fi
    cmd "execute in minecraft:overworld ${floor1} ${floor2} if block ${fx} $((fy+1)) ${fz} minecraft:air if block $((fx+1)) $((fy+1)) ${fz} minecraft:air if block ${fx} $((fy+2)) ${fz} minecraft:air if block $((fx+1)) $((fy+2)) ${fz} minecraft:air run say ${marker} ${fx} ${fy} ${fz} dir=${dir}"
  else
    if [[ -n "${floor_block}" ]]; then
      floor2="if block ${fx} ${fy} $((fz+1)) ${floor_block}"
    else
      floor2="unless block ${fx} ${fy} $((fz+1)) minecraft:air"
    fi
    cmd "execute in minecraft:overworld ${floor1} ${floor2} if block ${fx} $((fy+1)) ${fz} minecraft:air if block ${fx} $((fy+1)) $((fz+1)) minecraft:air if block ${fx} $((fy+2)) ${fz} minecraft:air if block ${fx} $((fy+2)) $((fz+1)) minecraft:air run say ${marker} ${fx} ${fy} ${fz} dir=${dir}"
  fi

  log_since_bytes "${start_bytes}" | grep -F "${marker} ${fx} ${fy} ${fz} dir=${dir}" >/dev/null 2>&1
}

find_floor_near_poi() {
  local px="$1" py="$2" pz="$3"

  local marker="[SPAWN] HOUSE_FLOOR_OK"

  # Candidate offsets around an indoor POI (bed/job site).
  # We try a handful of spots that are usually "inside" and have 2-wide space.
  local -a offsets=(
    "2 0"  "2 1"  "2 -1"
    "-3 0" "-3 1" "-3 -1"
    "0 2"  "1 2"  "-1 2"
    "0 -3" "1 -3" "-1 -3"
    "3 0"  "0 3"  "-4 0" "0 -4"
  )

  # Floor Y is typically poi_y-1, but we try a couple variants.
  for fy in $((py-2)) $((py-1)) "${py}"; do
    for off in "${offsets[@]}"; do
      read -r dx dz <<<"${off}"
      fx=$((px+dx))
      fz=$((pz+dz))
      if say_marker_if_floor_ok "${fx}" "${fy}" "${fz}" "" "x" "${marker}"; then
        echo "${fx} ${fy} ${fz} x"
        return 0
      fi
      if say_marker_if_floor_ok "${fx}" "${fy}" "${fz}" "" "z" "${marker}"; then
        echo "${fx} ${fy} ${fz} z"
        return 0
      fi
    done
  done

  return 1
}

echo "== Read world spawn =="
read -r SPAWN_X SPAWN_Y SPAWN_Z < <(./infra/world-spawn.sh)
echo "spawn: ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"

echo "== Locate an indoor village POI near spawn =="
poi_xyz=""
poi_used=""
for poi in minecraft:home minecraft:armorer minecraft:toolsmith minecraft:weaponsmith minecraft:cleric minecraft:cartographer minecraft:butcher; do
  poi_xyz="$(locate_poi_near "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "${poi}" || true)"
  if [[ -n "${poi_xyz}" ]]; then
    poi_used="${poi}"
    break
  fi
done
if [[ -z "${poi_xyz}" ]]; then
  # Fallback to meeting, but it's not always inside a building.
  poi_xyz="$(locate_poi_near "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "minecraft:meeting" || true)"
  poi_used="minecraft:meeting"
fi
if [[ -z "${poi_xyz}" ]]; then
  echo "ERROR: couldn't locate any village POI near spawn." >&2
  exit 1
fi
read -r PX PY PZ <<<"${poi_xyz}"
echo "poi(${poi_used}): ${PX} ${PY} ${PZ}"

echo "== Find a suitable house floor spot near that POI =="
floor_xyz="$(find_floor_near_poi "${PX}" "${PY}" "${PZ}" || true)"
if [[ -z "${floor_xyz}" ]]; then
  echo "ERROR: couldn't find a suitable 2-wide floor spot near the POI." >&2
  echo "Fallback (manual): stand inside a village house, note the floor X/Y/Z (block under you), then run:" >&2
  echo "  ./infra/spawn-village-upgrade.sh <floor_x> <floor_y> <floor_z>" >&2
  exit 1
fi

read -r FX FY FZ DIR <<<"${floor_xyz}"
echo "floor: ${FX} ${FY} ${FZ} (dir=${DIR})"

echo "== Apply village upgrade at that spot =="
./infra/spawn-village-upgrade.sh "${FX}" "${FY}" "${FZ}" --dir "${DIR}"

echo "OK auto house upgrade applied at floor ${FX} ${FY} ${FZ}"
