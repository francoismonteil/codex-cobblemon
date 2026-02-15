#!/usr/bin/env bash
set -euo pipefail

# "Pokemonize" a naturally generated village house (light-touch, no building):
# - Places Cobblemon PC + Healing Machine
# - Adds a small red/white carpet accent and a couple of utility blocks
#
# This is designed to be subtle and keep the village's wood/stone architecture intact.
#
# Coordinates:
# - Provide FLOOR coordinates (the block under where you want the healer/PC).
# - The script places blocks at Y+1.
#
# Usage:
#   ./infra/spawn-village-upgrade.sh <floor_x> <floor_y> <floor_z> [--dir x|z] [--force]
#
# Example:
#   ./infra/spawn-village-upgrade.sh 400 64 -1488

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

force="false"
dir="x"
args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      force="true"
      shift
      ;;
    --dir)
      dir="${2:-}"
      shift 2
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

if [[ "${dir}" != "x" && "${dir}" != "z" ]]; then
  echo "Invalid --dir (expected x|z): ${dir}" >&2
  exit 2
fi

if [[ ${#args[@]} -ne 3 ]]; then
  echo "Usage: $0 <floor_x> <floor_y> <floor_z> [--dir x|z] [--force]" >&2
  exit 2
fi

FX="${args[0]}"; FY="${args[1]}"; FZ="${args[2]}"
for v in "${FX}" "${FY}" "${FZ}"; do
  if ! [[ "${v}" =~ ^-?[0-9]+$ ]]; then
    echo "Invalid coordinate: ${v} (expected integer)" >&2
    exit 2
  fi
done

X="${FX}"
Y="$((FY+1))"
Z="${FZ}"

PX="${X}"; PZ="${Z}"
if [[ "${dir}" == "x" ]]; then
  PX="$((X+1))"; PZ="${Z}"
else
  PX="${X}"; PZ="$((Z+1))"
fi

cmd() {
  ./infra/mc.sh "$1" >/dev/null
  sleep 0.25
}

cmd_try() {
  ./infra/mc.sh "$1" >/dev/null 2>&1 || true
  sleep 0.25
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

# Core Cobblemon blocks
if [[ "${force}" == "true" ]]; then
  place_replace "${X}" "${Y}" "${Z}" "cobblemon:healing_machine"
  place_pc_replace "${PX}" "${Y}" "${PZ}"
else
  # Place only if BOTH positions are air to avoid half-placement.
  cmd "execute in minecraft:overworld if block ${X} ${Y} ${Z} minecraft:air if block ${PX} ${Y} ${PZ} minecraft:air if block ${PX} $((Y+1)) ${PZ} minecraft:air run setblock ${X} ${Y} ${Z} cobblemon:healing_machine"
  cmd "execute in minecraft:overworld if block ${X} ${Y} ${Z} cobblemon:healing_machine if block ${PX} ${Y} ${PZ} minecraft:air if block ${PX} $((Y+1)) ${PZ} minecraft:air run setblock ${PX} ${Y} ${PZ} cobblemon:pc[part=bottom,on=false]"
  cmd "execute in minecraft:overworld if block ${PX} ${Y} ${PZ} cobblemon:pc[part=bottom] if block ${PX} $((Y+1)) ${PZ} minecraft:air run setblock ${PX} $((Y+1)) ${PZ} cobblemon:pc[part=top,on=false]"
fi

./infra/mc.sh "execute in minecraft:overworld if block ${X} ${Y} ${Z} cobblemon:healing_machine if block ${PX} ${Y} ${PZ} cobblemon:pc[part=bottom] if block ${PX} $((Y+1)) ${PZ} cobblemon:pc[part=top] run say [SPAWN] POKECENTER_OK ${X} ${Y} ${Z} dir=${dir}" >/dev/null
sleep 0.25
if ! docker logs cobblemon --tail 800 2>/dev/null | grep -F "POKECENTER_OK ${X} ${Y} ${Z} dir=${dir}" >/dev/null 2>&1; then
  echo "ERROR: healer+PC not placed (target blocks not air?). Try another floor spot or add --force." >&2
  exit 1
fi

# Subtle "Pokemon Center" vibe: red/white carpet accents (best-effort, don't overwrite important blocks)
if [[ "${dir}" == "x" ]]; then
  cmd_try "setblock ${X} ${Y} $((Z-1)) minecraft:red_carpet keep"
  cmd_try "setblock $((X+1)) ${Y} $((Z-1)) minecraft:red_carpet keep"
  cmd_try "setblock $((X-1)) ${Y} ${Z} minecraft:white_carpet keep"
  cmd_try "setblock $((X-1)) ${Y} $((Z-1)) minecraft:white_carpet keep"
  cmd_try "setblock $((X+2)) ${Y} ${Z} minecraft:white_carpet keep"
  cmd_try "setblock $((X+2)) ${Y} $((Z-1)) minecraft:white_carpet keep"

  cmd_try "setblock ${X} ${Y} $((Z+1)) minecraft:barrel[facing=north] keep"
  cmd_try "setblock $((X+1)) ${Y} $((Z+1)) minecraft:crafting_table keep"
  cmd_try "setblock ${X} $((Y+1)) $((Z+1)) minecraft:lantern keep"
else
  # If PC is placed on Z+1, decorate to the west/east to avoid collisions.
  cmd_try "setblock $((X-1)) ${Y} ${Z} minecraft:red_carpet keep"
  cmd_try "setblock $((X-1)) ${Y} $((Z+1)) minecraft:red_carpet keep"
  cmd_try "setblock ${X} ${Y} $((Z-1)) minecraft:white_carpet keep"
  cmd_try "setblock $((X-1)) ${Y} $((Z-1)) minecraft:white_carpet keep"
  cmd_try "setblock ${X} ${Y} $((Z+2)) minecraft:white_carpet keep"
  cmd_try "setblock $((X-1)) ${Y} $((Z+2)) minecraft:white_carpet keep"

  cmd_try "setblock $((X+1)) ${Y} ${Z} minecraft:barrel[facing=west] keep"
  cmd_try "setblock $((X+1)) ${Y} $((Z+1)) minecraft:crafting_table keep"
  cmd_try "setblock $((X+1)) $((Y+1)) ${Z} minecraft:lantern keep"
fi

cmd_try "say [SPAWN] Village upgraded: healer+PC placed near ${FX} ${FY} ${FZ}."
echo "OK village upgraded at floor ${FX} ${FY} ${FZ} (placed at y=${Y}, dir=${dir})"
