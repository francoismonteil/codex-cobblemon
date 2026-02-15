#!/usr/bin/env bash
set -euo pipefail

# Adds a subtle "Pokemon Center" vibe around an existing Cobblemon healer+PC kit
# in the spawn village, without manual building and without overwriting blocks:
# - Red/white carpet accents (keep)
# - Barrel + crafting table (keep)
# - Lantern (keep)
#
# It auto-detects the kit location by:
# - reading world spawn from ./data/world/level.dat
# - locating the nearest village meeting POI near spawn
# - scanning a small set of candidate offsets for healer+PC blocks
#
# Usage:
#   ./infra/spawn-village-pokecenter-decorate.sh
#
# Notes:
# - Idempotent-ish: uses "keep" for decor blocks to avoid overwriting.
# - If the kit can't be found, run ./infra/spawn-village-pokecenter-auto.sh first.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

cmd() {
  ./infra/mc.sh "$1" >/dev/null
  sleep 0.25
}

cmd_try() {
  ./infra/mc.sh "$1" >/dev/null 2>&1 || true
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

find_kit_near_poi() {
  local px="$1" py="$2" pz="$3"

  # Candidate offsets: must match spawn-village-pokecenter-auto.sh + a couple extras.
  candidates=(
    "$((px+2)) ${py} ${pz}"
    "$((px-3)) ${py} ${pz}"
    "${px} ${py} $((pz+2))"
    "${px} ${py} $((pz-3))"
    "$((px+2)) ${py} $((pz+1))"
    "$((px-3)) ${py} $((pz-1))"
    "$((px+1)) ${py} ${pz}"
    "$((px-1)) ${py} ${pz}"
  )

  for c in "${candidates[@]}"; do
    read -r x y z <<<"${c}"
    t0="$(now_utc)"
    cmd "execute in minecraft:overworld if block ${x} ${y} ${z} cobblemon:healing_machine if block $((x+1)) ${y} ${z} cobblemon:pc run say [SPAWN] KIT_AT ${x} ${y} ${z}"
    if docker_logs_since "${t0}" | grep -F "KIT_AT ${x} ${y} ${z}" >/dev/null 2>&1; then
      echo "${x} ${y} ${z}"
      return 0
    fi
  done

  return 1
}

echo "== Read world spawn =="
read -r SPAWN_X SPAWN_Y SPAWN_Z < <(./infra/world-spawn.sh)
echo "spawn: ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"

echo "== Locate meeting POI near spawn =="
poi_xyz="$(locate_poi_near "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "minecraft:meeting" || true)"
if [[ -z "${poi_xyz}" ]]; then
  echo "ERROR: couldn't locate minecraft:meeting POI near spawn." >&2
  exit 1
fi
read -r PX PY PZ <<<"${poi_xyz}"
echo "poi: ${PX} ${PY} ${PZ}"

echo "== Find existing healer+PC kit near POI =="
kit_xyz="$(find_kit_near_poi "${PX}" "${PY}" "${PZ}" || true)"
if [[ -z "${kit_xyz}" ]]; then
  echo "ERROR: couldn't find a healer+PC kit near the meeting POI." >&2
  echo "Run first: ./infra/spawn-village-pokecenter-auto.sh" >&2
  exit 1
fi
read -r X Y Z <<<"${kit_xyz}"
echo "kit: healer=${X} ${Y} ${Z} pc=$((X+1)) ${Y} ${Z}"

echo "== Decorate (keep / best-effort) =="
# Carpets in front of the kit (red/white accents)
cmd_try "setblock ${X} ${Y} $((Z-1)) minecraft:red_carpet keep"
cmd_try "setblock $((X+1)) ${Y} $((Z-1)) minecraft:red_carpet keep"
cmd_try "setblock $((X-1)) ${Y} ${Z} minecraft:white_carpet keep"
cmd_try "setblock $((X-1)) ${Y} $((Z-1)) minecraft:white_carpet keep"
cmd_try "setblock $((X+2)) ${Y} ${Z} minecraft:white_carpet keep"
cmd_try "setblock $((X+2)) ${Y} $((Z-1)) minecraft:white_carpet keep"

# Useful blocks (still subtle)
cmd_try "setblock ${X} ${Y} $((Z+1)) minecraft:barrel[facing=north] keep"
cmd_try "setblock $((X+1)) ${Y} $((Z+1)) minecraft:crafting_table keep"

# A bit of warmth
cmd_try "setblock ${X} $((Y+1)) $((Z+1)) minecraft:lantern keep"

cmd_try "say [SPAWN] Pokecenter area upgraded (carpets + barrel + crafting + lantern)."
echo "OK decorated near kit at ${X} ${Y} ${Z}"

