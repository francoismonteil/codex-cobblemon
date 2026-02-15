#!/usr/bin/env bash
set -euo pipefail

# Builds a decorative gym + arena north of the spawn plaza.
# No automation, just a nice-looking battle space.
#
# Usage:
#   ./infra/spawn-gym.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

cmd() { ./infra/mc.sh "$1"; sleep 0.2; }
say() { ./infra/mc.sh "say [GYM] $*" >/dev/null 2>&1 || true; }

SPAWN_Y=120
Y1=$((SPAWN_Y+1))

# Gym anchor north of plaza
GX=0
GZ=-42

say "Building gym + arena..."

# Clear volume
cmd "fill -30 ${Y1} $((GZ-30)) 30 $((Y1+25)) $((GZ+30)) minecraft:air"

# Base platform
cmd "fill -26 ${SPAWN_Y} $((GZ-26)) 26 ${SPAWN_Y} $((GZ+26)) minecraft:black_concrete"
cmd "fill -24 ${SPAWN_Y} $((GZ-24)) 24 ${SPAWN_Y} $((GZ+24)) minecraft:gray_concrete"

# Arena ring (circular-ish, octagon)
cmd "fill -12 ${SPAWN_Y} $((GZ-12)) 12 ${SPAWN_Y} $((GZ+12)) minecraft:light_gray_concrete"
cmd "fill -10 ${SPAWN_Y} $((GZ-10)) 10 ${SPAWN_Y} $((GZ+10)) minecraft:white_concrete"
cmd "fill -8 ${SPAWN_Y} $((GZ-8)) 8 ${SPAWN_Y} $((GZ+8)) minecraft:sea_lantern"
cmd "fill -7 ${SPAWN_Y} $((GZ-7)) 7 ${SPAWN_Y} $((GZ+7)) minecraft:smooth_quartz"

# Arena boundary (glass + iron bars accents)
cmd "fill -13 $((Y1)) $((GZ-13)) 13 $((Y1+4)) $((GZ-13)) minecraft:light_gray_stained_glass"
cmd "fill -13 $((Y1)) $((GZ+13)) 13 $((Y1+4)) $((GZ+13)) minecraft:light_gray_stained_glass"
cmd "fill -13 $((Y1)) $((GZ-13)) -13 $((Y1+4)) $((GZ+13)) minecraft:light_gray_stained_glass"
cmd "fill 13 $((Y1)) $((GZ-13)) 13 $((Y1+4)) $((GZ+13)) minecraft:light_gray_stained_glass"
cmd "fill -13 $((Y1+2)) $((GZ-13)) 13 $((Y1+2)) $((GZ-13)) minecraft:iron_bars replace minecraft:light_gray_stained_glass"
cmd "fill -13 $((Y1+2)) $((GZ+13)) 13 $((Y1+2)) $((GZ+13)) minecraft:iron_bars replace minecraft:light_gray_stained_glass"
cmd "fill -13 $((Y1+2)) $((GZ-13)) -13 $((Y1+2)) $((GZ+13)) minecraft:iron_bars replace minecraft:light_gray_stained_glass"
cmd "fill 13 $((Y1+2)) $((GZ-13)) 13 $((Y1+2)) $((GZ+13)) minecraft:iron_bars replace minecraft:light_gray_stained_glass"

# Gym building shell behind arena (north side)
cmd "fill -18 $((Y1)) $((GZ-26)) 18 $((Y1+10)) $((GZ-16)) minecraft:white_concrete"
cmd "fill -17 $((Y1+1)) $((GZ-25)) 17 $((Y1+9)) $((GZ-17)) minecraft:air"
cmd "fill -18 $((Y1+11)) $((GZ-26)) 18 $((Y1+11)) $((GZ-16)) minecraft:quartz_block"
cmd "fill -2 $((Y1+2)) $((GZ-16)) 2 $((Y1+5)) $((GZ-16)) minecraft:glass"
cmd "setblock 0 $((Y1+2)) $((GZ-16)) minecraft:oak_door[facing=south,half=lower]"
cmd "setblock 0 $((Y1+3)) $((GZ-16)) minecraft:oak_door[facing=south,half=upper]"

# Signage (banners)
cmd "setblock -3 $((Y1+6)) $((GZ-16)) minecraft:white_banner[rotation=0]"
cmd "setblock 3 $((Y1+6)) $((GZ-16)) minecraft:white_banner[rotation=0]"

say "Gym ready. Arena is the center ring."
echo "OK"

