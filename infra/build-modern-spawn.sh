#!/usr/bin/env bash
set -euo pipefail

# Builds a modern sky-plaza spawn and sets worldspawn there.
# Safe to run multiple times (it overwrites the area).
#
# Default location: (0,120,0)
#
# Usage:
#   ./infra/build-modern-spawn.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

cmd() {
  ./infra/mc.sh "$1"
  sleep 0.2
}

say() {
  ./infra/mc.sh "say [SPAWN] $*" >/dev/null 2>&1 || true
}

SPAWN_X=0
SPAWN_Y=120
SPAWN_Z=0

say "Building modern spawn plaza..."

# Platform 65x65 (white concrete) and clear air above.
cmd "fill -32 ${SPAWN_Y} -32 32 ${SPAWN_Y} 32 minecraft:white_concrete replace"
cmd "fill -32 $((SPAWN_Y+1)) -32 32 $((SPAWN_Y+15)) 32 minecraft:air replace"

# Glass railing (3 blocks tall).
cmd "fill -32 $((SPAWN_Y+1)) -32 -32 $((SPAWN_Y+3)) 32 minecraft:light_gray_stained_glass"
cmd "fill 32 $((SPAWN_Y+1)) -32 32 $((SPAWN_Y+3)) 32 minecraft:light_gray_stained_glass"
cmd "fill -32 $((SPAWN_Y+1)) -32 32 $((SPAWN_Y+3)) -32 minecraft:light_gray_stained_glass"
cmd "fill -32 $((SPAWN_Y+1)) 32 32 $((SPAWN_Y+3)) 32 minecraft:light_gray_stained_glass"

# Lighting (sea lantern grid).
for x in -24 -12 0 12 24; do
  for z in -24 -12 0 12 24; do
    cmd "setblock ${x} ${SPAWN_Y} ${z} minecraft:sea_lantern"
  done
done

# Plaza paths
cmd "fill -7 ${SPAWN_Y} -2 7 ${SPAWN_Y} 2 minecraft:gray_concrete"
cmd "fill -2 ${SPAWN_Y} -32 2 ${SPAWN_Y} 32 minecraft:gray_concrete"

# Pokecenter building (simple)
PC_X1=-22; PC_X2=-8; PC_Z1=-8; PC_Z2=8
cmd "fill ${PC_X1} $((SPAWN_Y+1)) ${PC_Z1} ${PC_X2} $((SPAWN_Y+8)) ${PC_Z2} minecraft:white_concrete"
cmd "fill $((PC_X1+1)) $((SPAWN_Y+2)) $((PC_Z1+1)) $((PC_X2-1)) $((SPAWN_Y+7)) $((PC_Z2-1)) minecraft:air"
cmd "fill ${PC_X1} $((SPAWN_Y+9)) ${PC_Z1} ${PC_X2} $((SPAWN_Y+9)) ${PC_Z2} minecraft:quartz_block"
cmd "fill ${PC_X1} $((SPAWN_Y+5)) ${PC_Z1} ${PC_X2} $((SPAWN_Y+5)) ${PC_Z2} minecraft:red_concrete replace minecraft:white_concrete"
cmd "fill ${PC_X2} $((SPAWN_Y+2)) -2 ${PC_X2} $((SPAWN_Y+6)) 2 minecraft:glass"
cmd "setblock ${PC_X2} $((SPAWN_Y+2)) 0 minecraft:oak_door[facing=east,half=lower]"
cmd "setblock ${PC_X2} $((SPAWN_Y+3)) 0 minecraft:oak_door[facing=east,half=upper]"

# Pokemart building (simple)
PM_X1=8; PM_X2=22; PM_Z1=-8; PM_Z2=8
cmd "fill ${PM_X1} $((SPAWN_Y+1)) ${PM_Z1} ${PM_X2} $((SPAWN_Y+8)) ${PM_Z2} minecraft:white_concrete"
cmd "fill $((PM_X1+1)) $((SPAWN_Y+2)) $((PM_Z1+1)) $((PM_X2-1)) $((SPAWN_Y+7)) $((PM_Z2-1)) minecraft:air"
cmd "fill ${PM_X1} $((SPAWN_Y+9)) ${PM_Z1} ${PM_X2} $((SPAWN_Y+9)) ${PM_Z2} minecraft:quartz_block"
cmd "fill ${PM_X1} $((SPAWN_Y+5)) ${PM_Z1} ${PM_X2} $((SPAWN_Y+5)) ${PM_Z2} minecraft:light_blue_concrete replace minecraft:white_concrete"
cmd "fill ${PM_X1} $((SPAWN_Y+2)) -2 ${PM_X1} $((SPAWN_Y+6)) 2 minecraft:glass"
cmd "setblock ${PM_X1} $((SPAWN_Y+2)) 0 minecraft:oak_door[facing=west,half=lower]"
cmd "setblock ${PM_X1} $((SPAWN_Y+3)) 0 minecraft:oak_door[facing=west,half=upper]"

# Set world spawn
cmd "setworldspawn ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"
cmd "gamerule spawnRadius 0"

say "Adding utilities (healing/shop/storage)..."

# Pokecenter utilities (inside building)
cmd "setblock -15 $((SPAWN_Y+1)) 0 cobblemon:healing_machine"
cmd "setblock -17 $((SPAWN_Y+1)) 0 cobblemon:pc[part=bottom,on=false]"
cmd "setblock -17 $((SPAWN_Y+2)) 0 cobblemon:pc[part=top,on=false]"
cmd "setblock -20 $((SPAWN_Y+1)) -2 minecraft:ender_chest"
cmd "setblock -20 $((SPAWN_Y+1)) -1 minecraft:crafting_table"
cmd "setblock -20 $((SPAWN_Y+1)) 0 minecraft:anvil"
cmd "setblock -20 $((SPAWN_Y+1)) 1 minecraft:grindstone"
cmd "setblock -18 $((SPAWN_Y+1)) 4 minecraft:enchanting_table"
cmd "fill -19 $((SPAWN_Y+1)) 3 -17 $((SPAWN_Y+2)) 5 minecraft:bookshelf"

# Pokemart utilities (a simple vendor villager)
cmd "fill 10 $((SPAWN_Y+1)) -3 12 $((SPAWN_Y+1)) 3 minecraft:barrel"
cmd "summon villager 15 $((SPAWN_Y+1)) 0 {NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,CustomName:'{\"text\":\"PokeMart\"}',VillagerData:{profession:\"minecraft:cleric\",level:5,type:\"minecraft:plains\"},Offers:{Recipes:[{buy:{id:\"minecraft:emerald\",Count:1b},sell:{id:\"cobblemon:poke_ball\",Count:4b},maxUses:9999999},{buy:{id:\"minecraft:emerald\",Count:3b},sell:{id:\"cobblemon:poke_ball\",Count:16b},maxUses:9999999}]}}"

# Convenience: small nether portal frame (unlit) near the edge.
cmd "fill 26 $((SPAWN_Y+1)) 20 26 $((SPAWN_Y+4)) 22 minecraft:obsidian"
cmd "fill 26 $((SPAWN_Y+1)) 20 26 $((SPAWN_Y+4)) 22 minecraft:air"
cmd "fill 26 $((SPAWN_Y+1)) 20 26 $((SPAWN_Y+4)) 20 minecraft:obsidian"
cmd "fill 26 $((SPAWN_Y+1)) 22 26 $((SPAWN_Y+4)) 22 minecraft:obsidian"
cmd "fill 26 $((SPAWN_Y+1)) 20 26 $((SPAWN_Y+1)) 22 minecraft:obsidian"
cmd "fill 26 $((SPAWN_Y+4)) 20 26 $((SPAWN_Y+4)) 22 minecraft:obsidian"

say "Spawn ready at ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}."
echo "OK"
