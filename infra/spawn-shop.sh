#!/usr/bin/env bash
set -euo pipefail

# Creates a useful Pokemart at the modern spawn using villagers (emerald economy).
# Idempotent: it clears a small area and respawns the vendors.
#
# Usage:
#   ./infra/spawn-shop.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

cmd() { ./infra/mc.sh "$1"; sleep 0.2; }
say() { ./infra/mc.sh "say [SHOP] $*" >/dev/null 2>&1 || true; }

SPAWN_Y=120

# Pokemart kiosk area (east side, near the building we already place around x=8..22)
BASE_X=16
BASE_Z=0
Y1=$((SPAWN_Y+1))

say "Building Pokemart vendors..."

# Clear a 11x7x11 cube around the vendor area and build a simple kiosk line.
cmd "fill 10 $((Y1)) -6 22 $((Y1+5)) 6 minecraft:air"
cmd "fill 10 $((Y1)) -6 22 $((Y1)) 6 minecraft:smooth_quartz"
cmd "fill 10 $((Y1+1)) -6 22 $((Y1+3)) -6 minecraft:light_gray_concrete"
cmd "fill 10 $((Y1+1)) 6 22 $((Y1+3)) 6 minecraft:light_gray_concrete"
cmd "fill 10 $((Y1+1)) -6 10 $((Y1+3)) 6 minecraft:light_gray_concrete"
cmd "fill 22 $((Y1+1)) -6 22 $((Y1+3)) 6 minecraft:light_gray_concrete"
cmd "fill 10 $((Y1+4)) -6 22 $((Y1+4)) 6 minecraft:light_gray_stained_glass"

# Stalls (barrels + signs)
cmd "fill 12 $((Y1+1)) -4 20 $((Y1+1)) -4 minecraft:barrel"
cmd "fill 12 $((Y1+1)) 0 20 $((Y1+1)) 0 minecraft:barrel"
cmd "fill 12 $((Y1+1)) 4 20 $((Y1+1)) 4 minecraft:barrel"

# Remove any previously summoned vendors by killing named villagers in that area.
cmd "kill @e[type=minecraft:villager,name=\\\"PokeMart Balls\\\",distance=..50]"
cmd "kill @e[type=minecraft:villager,name=\\\"PokeMart Heals\\\",distance=..50]"
cmd "kill @e[type=minecraft:villager,name=\\\"PokeMart Basics\\\",distance=..50]"

# Vendors
# Balls vendor
cmd "summon villager 14 ${Y1} -4 {NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,CustomName:'{\"text\":\"PokeMart Balls\"}',VillagerData:{profession:\"minecraft:cleric\",level:5,type:\"minecraft:plains\"},Offers:{Recipes:["\
\
"{buy:{id:\"minecraft:emerald\",Count:1b},sell:{id:\"cobblemon:poke_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:2b},sell:{id:\"cobblemon:great_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:4b},sell:{id:\"cobblemon:ultra_ball\",Count:8b},maxUses:9999999},"\
\
"{buy:{id:\"minecraft:emerald\",Count:3b},sell:{id:\"cobblemon:premier_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:3b},sell:{id:\"cobblemon:quick_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:3b},sell:{id:\"cobblemon:dusk_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:3b},sell:{id:\"cobblemon:timer_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:3b},sell:{id:\"cobblemon:repeat_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:3b},sell:{id:\"cobblemon:net_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:3b},sell:{id:\"cobblemon:heal_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:4b},sell:{id:\"cobblemon:luxury_ball\",Count:8b},maxUses:9999999},"\
\
"{buy:{id:\"minecraft:emerald\",Count:4b},sell:{id:\"cobblemon:nest_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:4b},sell:{id:\"cobblemon:dive_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:4b},sell:{id:\"cobblemon:friend_ball\",Count:8b},maxUses:9999999},"\
"{buy:{id:\"minecraft:emerald\",Count:4b},sell:{id:\"cobblemon:moon_ball\",Count:8b},maxUses:9999999},"\
\
"{buy:{id:\"minecraft:emerald\",Count:48b},sell:{id:\"cobblemon:master_ball\",Count:1b},maxUses:9999999}"\
"]}}"

# Heals vendor (vanilla supplies; Cobblemon healing is via healing_machine)
cmd "summon villager 14 ${Y1} 0 {NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,CustomName:'{\"text\":\"PokeMart Heals\"}',VillagerData:{profession:\"minecraft:cleric\",level:5,type:\"minecraft:plains\"},Offers:{Recipes:[{buy:{id:\"minecraft:emerald\",Count:1b},sell:{id:\"minecraft:bread\",Count:16b},maxUses:9999999},{buy:{id:\"minecraft:emerald\",Count:2b},sell:{id:\"minecraft:cooked_beef\",Count:16b},maxUses:9999999},{buy:{id:\"minecraft:emerald\",Count:3b},sell:{id:\"minecraft:golden_apple\",Count:1b},maxUses:9999999},{buy:{id:\"minecraft:emerald\",Count:2b},sell:{id:\"minecraft:potion\",Count:1b,tag:{Potion:\"minecraft:healing\"}},maxUses:9999999}]}}"

# Basics vendor
cmd "summon villager 14 ${Y1} 4 {NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,CustomName:'{\"text\":\"PokeMart Basics\"}',VillagerData:{profession:\"minecraft:librarian\",level:5,type:\"minecraft:plains\"},Offers:{Recipes:[{buy:{id:\"minecraft:emerald\",Count:1b},sell:{id:\"minecraft:torch\",Count:64b},maxUses:9999999},{buy:{id:\"minecraft:emerald\",Count:1b},sell:{id:\"minecraft:oak_log\",Count:32b},maxUses:9999999},{buy:{id:\"minecraft:emerald\",Count:1b},sell:{id:\"minecraft:stone_pickaxe\",Count:1b},maxUses:9999999},{buy:{id:\"minecraft:emerald\",Count:1b},sell:{id:\"minecraft:white_bed\",Count:1b},maxUses:9999999}]}}"

# Kiosk containment (glass boxes)
cmd "fill 13 $((Y1)) -5 15 $((Y1+2)) -3 minecraft:glass"
cmd "fill 13 $((Y1+1)) -4 15 $((Y1+1)) -4 minecraft:air"
cmd "fill 13 $((Y1)) -1 15 $((Y1+2)) 1 minecraft:glass"
cmd "fill 13 $((Y1+1)) 0 15 $((Y1+1)) 0 minecraft:air"
cmd "fill 13 $((Y1)) 3 15 $((Y1+2)) 5 minecraft:glass"
cmd "fill 13 $((Y1+1)) 4 15 $((Y1+1)) 4 minecraft:air"

say "Pokemart ready (emerald economy)."
echo "OK"
