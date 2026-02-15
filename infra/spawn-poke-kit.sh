#!/usr/bin/env bash
set -euo pipefail

# Places a minimal "Pokemon Center" kit (Cobblemon) at the given coordinates:
# - Healing Machine
# - PC
#
# This is meant to be used in a naturally generated village near spawn, without building a full structure.
#
# Usage:
#   ./infra/spawn-poke-kit.sh <x> <y> <z> [--force]
#
# Default behavior is SAFE: it only places blocks if the target is air.
# Use --force to overwrite existing blocks.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

force="false"
if [[ $# -ge 1 ]] && [[ "${*: -1}" == "--force" ]]; then
  force="true"
  set -- "${@:1:$(($#-1))}"
fi

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <x> <y> <z> [--force]" >&2
  exit 2
fi

X="$1"; Y="$2"; Z="$3"
for v in "${X}" "${Y}" "${Z}"; do
  if ! [[ "${v}" =~ ^-?[0-9]+$ ]]; then
    echo "Invalid coordinate: ${v} (expected integer)" >&2
    exit 2
  fi
done

cmd() {
  ./infra/mc.sh "$1" >/dev/null
  sleep 0.2
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
  local x="$1" y="$2" z="$3"
  ./infra/mc.sh "execute in minecraft:overworld if block ${x} ${y} ${z} cobblemon:healing_machine if block $((x+1)) ${y} ${z} cobblemon:pc[part=bottom] if block $((x+1)) $((y+1)) ${z} cobblemon:pc[part=top] run say [SPAWN] POKECENTER_OK ${x} ${y} ${z}" >/dev/null
  sleep 0.2
  docker logs cobblemon --tail 500 2>/dev/null | grep -F "POKECENTER_OK ${x} ${y} ${z}" >/dev/null 2>&1
}

if [[ "${force}" == "true" ]]; then
  place_replace "${X}" "${Y}" "${Z}" "cobblemon:healing_machine"
  place_pc_replace "$((X+1))" "${Y}" "${Z}"
else
  place_air_only "${X}" "${Y}" "${Z}" "cobblemon:healing_machine"
  place_pc_air_only "$((X+1))" "${Y}" "${Z}"
fi

if verify_kit "${X}" "${Y}" "${Z}"; then
  cmd "say [SPAWN] Cobblemon kit placed at ${X} ${Y} ${Z} (healer + PC)."
  echo "OK placed healer+pc at ${X} ${Y} ${Z}"
else
  echo "ERROR: kit not placed (target blocks not air?). Try another spot or add --force." >&2
  exit 1
fi
