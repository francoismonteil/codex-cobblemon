#!/usr/bin/env bash
set -euo pipefail

# Creates/uses a small communal "welcome cache" container in the spawn village,
# near the existing Cobblemon healer+PC kit, and stocks it with basic supplies.
#
# Goals:
# - Help new players start quickly (food/torches/bed/pokeballs)
# - No manual coordinates
# - Minimal and subtle (uses a barrel placed with keep)
#
# Usage:
#   ./infra/spawn-village-welcome-cache.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

cmd() {
  ./infra/mc.sh "$1" >/dev/null
  sleep 0.2
}

cmd_try() {
  ./infra/mc.sh "$1" >/dev/null 2>&1 || true
  sleep 0.2
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
    sleep 0.3
  done

  return 1
}

find_kit_near_poi() {
  local px="$1" py="$2" pz="$3"

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

is_block() {
  local x="$1" y="$2" z="$3" block="$4"
  local t0
  t0="$(now_utc)"
  cmd "execute in minecraft:overworld if block ${x} ${y} ${z} ${block} run say [SPAWN] IS_${block//:/_} ${x} ${y} ${z}"
  docker_logs_since "${t0}" | grep -F "IS_${block//:/_} ${x} ${y} ${z}" >/dev/null 2>&1
}

echo "== Locate spawn village center =="
read -r SPAWN_X SPAWN_Y SPAWN_Z < <(./infra/world-spawn.sh)
poi_xyz="$(locate_poi_near "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "minecraft:meeting" || true)"
if [[ -z "${poi_xyz}" ]]; then
  echo "ERROR: couldn't locate meeting POI near spawn." >&2
  exit 1
fi
read -r PX PY PZ <<<"${poi_xyz}"

echo "== Find existing healer+PC kit =="
kit_xyz="$(find_kit_near_poi "${PX}" "${PY}" "${PZ}" || true)"
if [[ -z "${kit_xyz}" ]]; then
  echo "ERROR: couldn't find existing healer+PC kit near village center." >&2
  echo "Run first: ./infra/spawn-village-pokecenter-auto.sh" >&2
  exit 1
fi
read -r X Y Z <<<"${kit_xyz}"
echo "kit: healer=${X} ${Y} ${Z} pc=$((X+1)) ${Y} ${Z}"

echo "== Ensure a barrel near the kit =="
# Prefer the "behind" position used by decorate/upgrade: (X, Y, Z+1)
barrel_x="${X}"
barrel_y="${Y}"
barrel_z="$((Z+1))"

if ! is_block "${barrel_x}" "${barrel_y}" "${barrel_z}" "minecraft:barrel"; then
  # Try a couple alternatives to avoid collisions.
  for pos in \
    "${X} ${Y} $((Z+2))" \
    "$((X-1)) ${Y} $((Z+1))" \
    "$((X+2)) ${Y} $((Z+1))" \
    "${X} ${Y} $((Z-2))"
  do
    read -r bx by bz <<<"${pos}"
    # Place only if air.
    cmd_try "execute in minecraft:overworld if block ${bx} ${by} ${bz} minecraft:air run setblock ${bx} ${by} ${bz} minecraft:barrel[facing=north] keep"
    if is_block "${bx}" "${by}" "${bz}" "minecraft:barrel"; then
      barrel_x="${bx}"; barrel_y="${by}"; barrel_z="${bz}"
      break
    fi
  done
fi

if ! is_block "${barrel_x}" "${barrel_y}" "${barrel_z}" "minecraft:barrel"; then
  echo "ERROR: couldn't place/find a barrel near the kit." >&2
  exit 1
fi
echo "barrel: ${barrel_x} ${barrel_y} ${barrel_z}"

echo "== Stock the welcome cache (fixed slots) =="
# These commands are safe and simple; they will overwrite the slots listed.
cmd_try "item replace block ${barrel_x} ${barrel_y} ${barrel_z} container.0 with minecraft:bread 32"
cmd_try "item replace block ${barrel_x} ${barrel_y} ${barrel_z} container.1 with minecraft:torch 64"
cmd_try "item replace block ${barrel_x} ${barrel_y} ${barrel_z} container.2 with minecraft:white_bed 2"
cmd_try "item replace block ${barrel_x} ${barrel_y} ${barrel_z} container.3 with minecraft:oak_planks 64"
cmd_try "item replace block ${barrel_x} ${barrel_y} ${barrel_z} container.4 with minecraft:stone_pickaxe 1"
cmd_try "item replace block ${barrel_x} ${barrel_y} ${barrel_z} container.5 with minecraft:stone_axe 1"
cmd_try "item replace block ${barrel_x} ${barrel_y} ${barrel_z} container.6 with cobblemon:poke_ball 16"

cmd_try "say [SPAWN] Welcome cache stocked near Pokecenter (barrel at ${barrel_x} ${barrel_y} ${barrel_z})."
echo "OK welcome cache stocked at barrel ${barrel_x} ${barrel_y} ${barrel_z}"

