#!/usr/bin/env bash
set -euo pipefail

# Gives a small starter kit to a player.
#
# Usage:
#   ./infra/starter.sh <Pseudo>
#
# Notes:
# - Uses emerald economy, so keep it modest.
# - Adjust items as you like.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <Pseudo>" >&2
  exit 2
fi

name="$1"

./infra/mc.sh "give ${name} minecraft:bread 16"
./infra/mc.sh "give ${name} minecraft:torch 64"
./infra/mc.sh "give ${name} minecraft:oak_planks 64"
./infra/mc.sh "give ${name} minecraft:stone_pickaxe 1"
./infra/mc.sh "give ${name} minecraft:stone_axe 1"
./infra/mc.sh "give ${name} minecraft:white_bed 1"
./infra/mc.sh "give ${name} minecraft:emerald 8"
./infra/mc.sh "give ${name} cobblemon:poke_ball 16"

./infra/mc.sh "say [STARTER] Kit donne a ${name}."
