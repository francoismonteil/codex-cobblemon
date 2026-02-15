#!/usr/bin/env bash
set -euo pipefail

# Automatically places a minimal Cobblemon "Pokemon Center" kit in the spawn village
# without manual building:
# - Finds the world spawn from ./data/world/level.dat
# - Uses /locate poi near spawn (tries a few POI types) to find a village anchor
# - Places Healing Machine + PC next to that anchor (air-only by default)
#
# Usage:
#   ./infra/spawn-village-pokecenter-auto.sh [--force]
#
# Notes:
# - Default is SAFE (air-only). Use --force to overwrite blocks.
# - If no POI is found, it exits with an error and suggests a manual fallback.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

force="false"
if [[ $# -ge 1 ]] && [[ "${*: -1}" == "--force" ]]; then
  force="true"
  set -- "${@:1:$(($#-1))}"
fi

if [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--force]" >&2
  exit 2
fi

cmd() {
  ./infra/mc.sh "$1" >/dev/null
  sleep 0.25
}

now_utc() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

docker_logs_since() {
  local since="$1"
  docker logs cobblemon --since "${since}" --tail 8000 2>/dev/null || true
}

locate_poi_near() {
  local near_x="$1" near_y="$2" near_z="$3" poi="$4"
  local t0 out xyz x y z
  t0="$(now_utc)"

  cmd "execute in minecraft:overworld positioned ${near_x} ${near_y} ${near_z} run locate poi ${poi}"

  for _ in {1..45}; do
    out="$(docker_logs_since "${t0}" | grep -E 'The nearest .* is at \[-?[0-9]+, [^,]+, -?[0-9]+\]' | tail -n 1 || true)"
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
    sleep 1
  done

  return 1
}

place_air_only() {
  local x="$1" y="$2" z="$3" block="$4"
  cmd "execute in minecraft:overworld if block ${x} ${y} ${z} minecraft:air run setblock ${x} ${y} ${z} ${block}"
}

place_replace() {
  local x="$1" y="$2" z="$3" block="$4"
  cmd "setblock ${x} ${y} ${z} ${block} replace"
}

place_pc_replace() {
  local x="$1" y="$2" z="$3"
  place_replace "${x}" "${y}" "${z}" "cobblemon:pc[part=bottom,on=false]"
  place_replace "${x}" "$((y+1))" "${z}" "cobblemon:pc[part=top,on=false]"
}

place_pc_air_only() {
  local x="$1" y="$2" z="$3"
  # Only place if BOTH blocks are air, to avoid a broken half-PC.
  cmd "execute in minecraft:overworld if block ${x} ${y} ${z} minecraft:air if block ${x} $((y+1)) ${z} minecraft:air run setblock ${x} ${y} ${z} cobblemon:pc[part=bottom,on=false]"
  cmd "execute in minecraft:overworld if block ${x} ${y} ${z} cobblemon:pc[part=bottom] if block ${x} $((y+1)) ${z} minecraft:air run setblock ${x} $((y+1)) ${z} cobblemon:pc[part=top,on=false]"
}

verify_kit() {
  local since="$1" x="$2" y="$3" z="$4"
  # Emit a unique marker only if both blocks are present.
  cmd "execute in minecraft:overworld if block ${x} ${y} ${z} cobblemon:healing_machine if block $((x+1)) ${y} ${z} cobblemon:pc[part=bottom] if block $((x+1)) $((y+1)) ${z} cobblemon:pc[part=top] run say [SPAWN] POKECENTER_OK ${x} ${y} ${z}"
  docker_logs_since "${since}" | grep -F "POKECENTER_OK ${x} ${y} ${z}" >/dev/null 2>&1
}

echo "== Read world spawn =="
read -r SPAWN_X SPAWN_Y SPAWN_Z < <(./infra/world-spawn.sh)
echo "spawn: ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"

echo "== Locate a village POI near spawn =="
poi_xyz=""
for poi in minecraft:meeting minecraft:home minecraft:armorer minecraft:toolsmith minecraft:weaponsmith minecraft:cleric; do
  poi_xyz="$(locate_poi_near "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "${poi}" || true)"
  if [[ -n "${poi_xyz}" ]]; then
    echo "poi(${poi}): ${poi_xyz}"
    break
  fi
done

if [[ -z "${poi_xyz}" ]]; then
  echo "ERROR: couldn't locate a village POI near spawn via /locate poi." >&2
  echo "Fallback: pick a clear spot in the spawn village and run:" >&2
  echo "  ./infra/spawn-village-upgrade.sh <floor_x> <floor_y> <floor_z>" >&2
  exit 1
fi

read -r PX PY PZ <<<"${poi_xyz}"

echo "== Place healer + PC near POI (safe by default) =="
# Try a few candidate placements around the POI. We place on the same Y level as the POI.
candidates=(
  "$((PX+2)) ${PY} ${PZ}"
  "$((PX-3)) ${PY} ${PZ}"
  "${PX} ${PY} $((PZ+2))"
  "${PX} ${PY} $((PZ-3))"
  "$((PX+2)) ${PY} $((PZ+1))"
  "$((PX-3)) ${PY} $((PZ-1))"
)

placed="false"
PLACED_X=""; PLACED_Y=""; PLACED_Z=""
for c in "${candidates[@]}"; do
  read -r X Y Z <<<"${c}"
  t0="$(now_utc)"
  if [[ "${force}" == "true" ]]; then
    place_replace "${X}" "${Y}" "${Z}" "cobblemon:healing_machine"
    place_pc_replace "$((X+1))" "${Y}" "${Z}"
    if verify_kit "${t0}" "${X}" "${Y}" "${Z}"; then
      placed="true"
      PLACED_X="${X}"; PLACED_Y="${Y}"; PLACED_Z="${Z}"
      break
    fi
  else
    # Place only if BOTH positions are air to avoid half-placement.
    cmd "execute in minecraft:overworld if block ${X} ${Y} ${Z} minecraft:air if block $((X+1)) ${Y} ${Z} minecraft:air if block $((X+1)) $((Y+1)) ${Z} minecraft:air run setblock ${X} ${Y} ${Z} cobblemon:healing_machine"
    place_pc_air_only "$((X+1))" "${Y}" "${Z}"
    if verify_kit "${t0}" "${X}" "${Y}" "${Z}"; then
      placed="true"
      PLACED_X="${X}"; PLACED_Y="${Y}"; PLACED_Z="${Z}"
      break
    fi
  fi
done

if [[ "${placed}" != "true" ]]; then
  echo "ERROR: failed to place kit automatically (no suitable air spot near POI)." >&2
  echo "Try again with --force OR use the manual village upgrade script:" >&2
  echo "  ./infra/spawn-village-upgrade.sh <floor_x> <floor_y> <floor_z>" >&2
  exit 1
fi

cmd "say [SPAWN] Cobblemon kit placed near village center: healer=${PLACED_X} ${PLACED_Y} ${PLACED_Z}, pc=$((PLACED_X+1)) ${PLACED_Y} ${PLACED_Z} (auto)."
echo "OK auto pokecenter placed:"
echo "  poi:    ${PX} ${PY} ${PZ}"
echo "  healer: ${PLACED_X} ${PLACED_Y} ${PLACED_Z}"
echo "  pc:     $((PLACED_X+1)) ${PLACED_Y} ${PLACED_Z}"
