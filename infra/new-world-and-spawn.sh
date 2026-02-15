#!/usr/bin/env bash
set -euo pipefail

# Creates a new world and builds a simple modern spawn "city" using vanilla commands.
#
# What it does:
# - Announces maintenance, saves, and stops the server
# - Runs a backup (best-effort flush already in backup.sh)
# - Archives the old world folder
# - Starts the server to generate a fresh world
# - Builds a sky plaza spawn and sets worldspawn
#
# Notes:
# - No WorldEdit required.
# - The spawn is built at y=120 to avoid terrain issues.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${REPO_ROOT}/data"
WORLD_DIR="${DATA_DIR}/world"
LOG_DIR="${REPO_ROOT}/logs"

cd "${REPO_ROOT}"
mkdir -p "${LOG_DIR}"

ts="$(date +%Y%m%d-%H%M%S)"

with_windmill="false"
windmills_count="0"
windmills_radius="6000"
windmills_min_dist="1200"

usage() {
  cat <<EOF >&2
Usage:
  $0 [--with-windmill] [--windmills <n>] [--windmills-radius <blocks>] [--windmills-min-dist <blocks>]

Notes:
  --with-windmill will paste downloads/Windmill - (mcbuild_org).schematic near spawn (best-effort).
  --windmills will spawn N windmills scattered in minecraft:plains within a radius (best-effort).
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-windmill)
      with_windmill="true"
      shift
      ;;
    --windmills)
      windmills_count="${2:?}"
      shift 2
      ;;
    --windmills-radius)
      windmills_radius="${2:?}"
      shift 2
      ;;
    --windmills-min-dist)
      windmills_min_dist="${2:?}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 2
      ;;
  esac
done

say() {
  ./infra/mc.sh "say [MAINT] $*" >/dev/null 2>&1 || true
}

wait_ready() {
  for _ in {1..180}; do
    if docker logs cobblemon --tail 300 2>/dev/null | grep -Eq 'Done \\(.*\\)! For help, type \"help\"'; then
      return 0
    fi
    sleep 2
  done
  return 1
}

cmd() {
  ./infra/mc.sh "$1"
  sleep 0.2
}

say "New world generation starting. Server will restart."
cmd "save-all flush" || true
cmd "stop" || true
sleep 4

./infra/stop.sh || true

echo "== Backup =="
./infra/backup.sh

echo "== Archive old world folder =="
if [[ -d "${WORLD_DIR}" ]]; then
  mv "${WORLD_DIR}" "${DATA_DIR}/world.prev-${ts}"
fi

echo "== Start server (generate new world) =="
./infra/start.sh
wait_ready

# Build spawn plaza at fixed coordinates.
SPAWN_X=0
SPAWN_Y=120
SPAWN_Z=0

say "Building spawn plaza..."

# Platform 65x65 (white concrete) and a glass railing.
cmd "fill -32 ${SPAWN_Y} -32 32 ${SPAWN_Y} 32 minecraft:white_concrete replace"
cmd "fill -32 $((SPAWN_Y+1)) -32 32 $((SPAWN_Y+1)) 32 minecraft:air replace"
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

# Modern "Pokecenter" building (simple): white walls, red accents, glass front.
# Footprint: x -22..-8, z -8..8, height 8
PC_X1=-22; PC_X2=-8; PC_Z1=-8; PC_Z2=8
cmd "fill ${PC_X1} $((SPAWN_Y+1)) ${PC_Z1} ${PC_X2} $((SPAWN_Y+8)) ${PC_Z2} minecraft:white_concrete"
cmd "fill $((PC_X1+1)) $((SPAWN_Y+2)) $((PC_Z1+1)) $((PC_X2-1)) $((SPAWN_Y+7)) $((PC_Z2-1)) minecraft:air"
cmd "fill ${PC_X1} $((SPAWN_Y+9)) ${PC_Z1} ${PC_X2} $((SPAWN_Y+9)) ${PC_Z2} minecraft:quartz_block"
# Front glass + door
cmd "fill ${PC_X2} $((SPAWN_Y+2)) -2 ${PC_X2} $((SPAWN_Y+6)) 2 minecraft:glass"
cmd "setblock ${PC_X2} $((SPAWN_Y+2)) 0 minecraft:air"
cmd "setblock ${PC_X2} $((SPAWN_Y+3)) 0 minecraft:air"
cmd "setblock ${PC_X2} $((SPAWN_Y+2)) 0 minecraft:oak_door[facing=east,half=lower]"
cmd "setblock ${PC_X2} $((SPAWN_Y+3)) 0 minecraft:oak_door[facing=east,half=upper]"
# Red stripe
cmd "fill ${PC_X1} $((SPAWN_Y+5)) ${PC_Z1} ${PC_X2} $((SPAWN_Y+5)) ${PC_Z2} minecraft:red_concrete replace minecraft:white_concrete"

# Modern "Pokemart" building (blue accents): x 8..22, z -8..8
PM_X1=8; PM_X2=22; PM_Z1=-8; PM_Z2=8
cmd "fill ${PM_X1} $((SPAWN_Y+1)) ${PM_Z1} ${PM_X2} $((SPAWN_Y+8)) ${PM_Z2} minecraft:white_concrete"
cmd "fill $((PM_X1+1)) $((SPAWN_Y+2)) $((PM_Z1+1)) $((PM_X2-1)) $((SPAWN_Y+7)) $((PM_Z2-1)) minecraft:air"
cmd "fill ${PM_X1} $((SPAWN_Y+9)) ${PM_Z1} ${PM_X2} $((SPAWN_Y+9)) ${PM_Z2} minecraft:quartz_block"
cmd "fill ${PM_X1} $((SPAWN_Y+5)) ${PM_Z1} ${PM_X2} $((SPAWN_Y+5)) ${PM_Z2} minecraft:light_blue_concrete replace minecraft:white_concrete"
cmd "fill ${PM_X1} $((SPAWN_Y+2)) -2 ${PM_X1} $((SPAWN_Y+6)) 2 minecraft:glass"
cmd "setblock ${PM_X1} $((SPAWN_Y+2)) 0 minecraft:oak_door[facing=west,half=lower]"
cmd "setblock ${PM_X1} $((SPAWN_Y+3)) 0 minecraft:oak_door[facing=west,half=upper]"

# Simple plaza paths
cmd "fill -7 ${SPAWN_Y} -2 7 ${SPAWN_Y} 2 minecraft:gray_concrete"
cmd "fill -2 ${SPAWN_Y} -32 2 ${SPAWN_Y} 32 minecraft:gray_concrete"

# Set world spawn
cmd "setworldspawn ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"
cmd "gamerule spawnRadius 0"

if [[ "${windmills_count}" =~ ^[0-9]+$ ]] && [[ "${windmills_count}" -gt 0 ]]; then
  say "Spawning ${windmills_count} windmills in plains..."
  ./infra/spawn-windmills-plains.sh \
    --center "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" \
    --count "${windmills_count}" \
    --radius "${windmills_radius}" \
    --min-dist "${windmills_min_dist}" \
    >/dev/null 2>&1 || true
  say "Windmills spawn done."
elif [[ "${with_windmill}" == "true" ]]; then
  say "Pasting windmill schematic near spawn..."
  schem="downloads/Windmill - (mcbuild_org).schematic"
  if [[ -f "${schem}" ]]; then
    # The schematic has WEOffsetY=-4, and spawn-schematic-mcedit interprets origin as "block under feet".
    # Add +4 so the schematic base starts at SPAWN_Y (instead of hanging below the spawn platform).
    wm_at_y=$((SPAWN_Y + 4))
    ./infra/spawn-schematic-mcedit.sh \
      --schematic "${schem}" \
      --at "${SPAWN_X}" "${wm_at_y}" "${SPAWN_Z}" \
      --dx 80 --dy 0 --dz 0 \
      --no-clear \
      >/dev/null 2>&1 || true
    say "Windmill pasted."
  else
    say "Windmill schematic missing: ${schem} (skipping)."
  fi
fi

say "Spawn ready at ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}."
echo "OK new world + spawn built at ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"
