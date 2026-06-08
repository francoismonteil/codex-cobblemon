#!/usr/bin/env bash
set -euo pipefail

# Build the Academy portal areas and marker entities in the overworld and Academy dimension.
#
# Usage:
#   ./infra/spawn-academy-portals.sh
#   OVERWORLD_OFFSET_X=32 OVERWORLD_OFFSET_Z=8 ./infra/spawn-academy-portals.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ ! -d "./data/world" ]]; then
  echo "Missing ./data/world" >&2
  exit 1
fi

read -r SPAWN_X SPAWN_Y SPAWN_Z < <(./infra/world-spawn.sh)
OVERWORLD_OFFSET_X="${OVERWORLD_OFFSET_X:-24}"
OVERWORLD_OFFSET_Z="${OVERWORLD_OFFSET_Z:-0}"
OVERWORLD_Y="${OVERWORLD_Y:-$SPAWN_Y}"

OW_PORTAL_X=$((SPAWN_X + OVERWORLD_OFFSET_X))
OW_PORTAL_Y="${OVERWORLD_Y}"
OW_PORTAL_Z=$((SPAWN_Z + OVERWORLD_OFFSET_Z))
OW_ARRIVAL_X="${OW_PORTAL_X}"
OW_ARRIVAL_Y=$((OW_PORTAL_Y + 1))
OW_ARRIVAL_Z=$((OW_PORTAL_Z + 3))

ACA_PORTAL_X="${ACA_PORTAL_X:-0}"
ACA_PORTAL_Y="${ACA_PORTAL_Y:-90}"
ACA_PORTAL_Z="${ACA_PORTAL_Z:-0}"
ACA_ARRIVAL_X="${ACA_ARRIVAL_X:-0}"
ACA_ARRIVAL_Y="${ACA_ARRIVAL_Y:-91}"
ACA_ARRIVAL_Z="${ACA_ARRIVAL_Z:-4}"

run_mc() {
  ./infra/mc.sh "$@"
}

echo "Building overworld Academy portal around ${OW_PORTAL_X} ${OW_PORTAL_Y} ${OW_PORTAL_Z}"
run_mc "execute in minecraft:overworld run fill $((OW_PORTAL_X - 4)) ${OW_PORTAL_Y} $((OW_PORTAL_Z - 1)) $((OW_PORTAL_X + 4)) ${OW_PORTAL_Y} $((OW_PORTAL_Z + 6)) minecraft:stone_bricks hollow"
run_mc "execute in minecraft:overworld run fill $((OW_PORTAL_X - 1)) $((OW_PORTAL_Y + 1)) ${OW_PORTAL_Z} $((OW_PORTAL_X + 1)) $((OW_PORTAL_Y + 4)) ${OW_PORTAL_Z} minecraft:crying_obsidian"
run_mc "execute in minecraft:overworld run setblock ${OW_PORTAL_X} $((OW_PORTAL_Y + 1)) $((OW_PORTAL_Z + 1)) minecraft:lodestone"
run_mc "execute in minecraft:overworld run setblock $((OW_PORTAL_X - 2)) $((OW_PORTAL_Y + 1)) ${OW_PORTAL_Z} minecraft:soul_lantern"
run_mc "execute in minecraft:overworld run setblock $((OW_PORTAL_X + 2)) $((OW_PORTAL_Y + 1)) ${OW_PORTAL_Z} minecraft:soul_lantern"

run_mc "execute in minecraft:overworld run kill @e[type=minecraft:marker,tag=acm_academy.portal_overworld,distance=..16]"
run_mc "execute in minecraft:overworld run kill @e[type=minecraft:marker,tag=acm_academy.arrival_overworld,distance=..16]"
run_mc "execute in minecraft:overworld run summon minecraft:marker ${OW_PORTAL_X} ${OW_PORTAL_Y} ${OW_PORTAL_Z} {Tags:[\"acm_academy.portal_overworld\"]}"
run_mc "execute in minecraft:overworld run summon minecraft:marker ${OW_ARRIVAL_X} ${OW_ARRIVAL_Y} ${OW_ARRIVAL_Z} {Tags:[\"acm_academy.arrival_overworld\"]}"

echo "Building Academy hub portal around ${ACA_PORTAL_X} ${ACA_PORTAL_Y} ${ACA_PORTAL_Z}"
run_mc "execute in acm_academy:academy run fill $((ACA_PORTAL_X - 6)) ${ACA_PORTAL_Y} $((ACA_PORTAL_Z - 6)) $((ACA_PORTAL_X + 6)) ${ACA_PORTAL_Y} $((ACA_PORTAL_Z + 6)) minecraft:smooth_stone"
run_mc "execute in acm_academy:academy run fill $((ACA_PORTAL_X - 2)) $((ACA_PORTAL_Y + 1)) ${ACA_PORTAL_Z} $((ACA_PORTAL_X + 2)) $((ACA_PORTAL_Y + 5)) ${ACA_PORTAL_Z} minecraft:quartz_bricks hollow"
run_mc "execute in acm_academy:academy run setblock ${ACA_PORTAL_X} $((ACA_PORTAL_Y + 1)) $((ACA_PORTAL_Z + 1)) minecraft:lodestone"
run_mc "execute in acm_academy:academy run setblock $((ACA_PORTAL_X - 3)) $((ACA_PORTAL_Y + 1)) ${ACA_PORTAL_Z} minecraft:sea_lantern"
run_mc "execute in acm_academy:academy run setblock $((ACA_PORTAL_X + 3)) $((ACA_PORTAL_Y + 1)) ${ACA_PORTAL_Z} minecraft:sea_lantern"

run_mc "execute in acm_academy:academy run kill @e[type=minecraft:marker,tag=acm_academy.portal_return_marker,distance=..24]"
run_mc "execute in acm_academy:academy run kill @e[type=minecraft:marker,tag=acm_academy.arrival_academy,distance=..24]"
run_mc "execute in acm_academy:academy run kill @e[type=minecraft:marker,tag=acm_academy.boundary_center,distance=..24]"
run_mc "execute in acm_academy:academy run summon minecraft:marker ${ACA_PORTAL_X} ${ACA_PORTAL_Y} ${ACA_PORTAL_Z} {Tags:[\"acm_academy.portal_return_marker\"]}"
run_mc "execute in acm_academy:academy run summon minecraft:marker ${ACA_ARRIVAL_X} ${ACA_ARRIVAL_Y} ${ACA_ARRIVAL_Z} {Tags:[\"acm_academy.arrival_academy\"]}"
run_mc "execute in acm_academy:academy run summon minecraft:marker ${ACA_PORTAL_X} ${ACA_PORTAL_Y} ${ACA_PORTAL_Z} {Tags:[\"acm_academy.boundary_center\"]}"

cat <<EOF
Academy portal bootstrap complete.

Overworld portal trigger : ${OW_PORTAL_X} ${OW_PORTAL_Y} ${OW_PORTAL_Z}
Overworld arrival marker: ${OW_ARRIVAL_X} ${OW_ARRIVAL_Y} ${OW_ARRIVAL_Z}
Academy portal trigger  : ${ACA_PORTAL_X} ${ACA_PORTAL_Y} ${ACA_PORTAL_Z}
Academy arrival marker : ${ACA_ARRIVAL_X} ${ACA_ARRIVAL_Y} ${ACA_ARRIVAL_Z}

Smoke test:
  1. stand on the lodestone in the overworld portal for ~1.5 seconds
  2. verify transfer to acm_academy:academy
  3. stand on the Academy lodestone to return
EOF
