#!/usr/bin/env bash
set -euo pipefail

# Spawns a simple windmill near a player using only vanilla server commands (no WorldEdit).
#
# Default:
# - target player: DEFAULT_PLAYER_NAME (or "PlayerName")
# - spawn offset: +20 blocks on X (east), 0 on Z
#
# The build is executed with:
#   execute at <player> positioned ~ ~-1 ~ run ...
# so Y=0 is the block under the player's feet.
#
# Usage:
#   ./infra/spawn-windmill.sh
#   ./infra/spawn-windmill.sh --player <player>
#   ./infra/spawn-windmill.sh --player <player> --dx 20 --dz 0
#   ./infra/spawn-windmill.sh --no-clear

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

source ./infra/prefab-lib.sh

player="${DEFAULT_PLAYER_NAME:-PlayerName}"
dx="20"
dz="0"
no_clear="false"

usage() {
  cat <<EOF
Usage:
  $0 [--player <name>] [--dx <int>] [--dz <int>] [--no-clear]

Defaults:
  --player ${player}
  --dx ${dx}
  --dz ${dz}
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --player)
      player="${2:?}"
      shift 2
      ;;
    --dx)
      dx="${2:?}"
      shift 2
      ;;
    --dz)
      dz="${2:?}"
      shift 2
      ;;
    --no-clear)
      no_clear="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! [[ "${dx}" =~ ^-?[0-9]+$ ]] || ! [[ "${dz}" =~ ^-?[0-9]+$ ]]; then
  echo "Invalid --dx/--dz (expected integers): dx=${dx} dz=${dz}" >&2
  exit 2
fi

cmd() { prefab_cmd "$1"; }
cmd_try() { prefab_cmd_try "$1"; }

exec_at_player() {
  local inner="${1:?}"
  # NOTE: best-effort. If the player is offline, the selector is empty and nothing runs.
  cmd_try "execute at @a[name=${player},limit=1] positioned ~ ~-1 ~ run ${inner}"
}

tell_player() {
  local msg="$*"
  cmd_try "tell ${player} [SPAWN] ${msg}"
}

X0="${dx}"
Z0="${dz}"

# Footprints (relative offsets to the positioned origin).
XF1=$((X0 - 5)); XF2=$((X0 + 5))
ZF1=$((Z0 - 5)); ZF2=$((Z0 + 5))

XT1=$((X0 - 3)); XT2=$((X0 + 3))
ZT1=$((Z0 - 3)); ZT2=$((Z0 + 3))

XC1=$((X0 - 12)); XC2=$((X0 + 12))
ZC1=$((Z0 - 12)); ZC2=$((Z0 + 12))

# Blade hub position (in front of the west face).
XH=$((X0 - 7))
YH=13
ZH="${Z0}"

M_FOUND="minecraft:stone_bricks"
M_BASE="minecraft:cobblestone"
M_WALL="minecraft:spruce_planks"
M_LOG_Y="minecraft:spruce_log[axis=y]"
M_LOG_X="minecraft:spruce_log[axis=x]"
M_ROOF="minecraft:dark_oak_planks"
M_GLASS="minecraft:glass_pane"
M_FENCE="minecraft:spruce_fence"

tell_player "Windmill: generation start (offset dx=${dx} dz=${dz})."

if [[ "${no_clear}" != "true" ]]; then
  # Clear only above the ground (y=1..35) to avoid digging a crater.
  exec_at_player "fill ~${XC1} ~1 ~${ZC1} ~${XC2} ~35 ~${ZC2} minecraft:air replace"
fi

# Foundation platform.
exec_at_player "fill ~${XF1} ~0 ~${ZF1} ~${XF2} ~0 ~${ZF2} ${M_FOUND} replace"

# Tower shell (stone base 1..4, wood 5..17), 7x7, hollow.
exec_at_player "fill ~${XT1} ~1 ~${ZT1} ~${XT2} ~4 ~${ZT2} ${M_BASE} replace"
exec_at_player "fill ~$((XT1 + 1)) ~1 ~$((ZT1 + 1)) ~$((XT2 - 1)) ~4 ~$((ZT2 - 1)) minecraft:air replace"

exec_at_player "fill ~${XT1} ~5 ~${ZT1} ~${XT2} ~17 ~${ZT2} ${M_WALL} replace"
exec_at_player "fill ~$((XT1 + 1)) ~5 ~$((ZT1 + 1)) ~$((XT2 - 1)) ~17 ~$((ZT2 - 1)) minecraft:air replace"

# Corner logs (wood part only).
exec_at_player "fill ~${XT1} ~5 ~${ZT1} ~${XT1} ~17 ~${ZT1} ${M_LOG_Y} replace"
exec_at_player "fill ~${XT1} ~5 ~${ZT2} ~${XT1} ~17 ~${ZT2} ${M_LOG_Y} replace"
exec_at_player "fill ~${XT2} ~5 ~${ZT1} ~${XT2} ~17 ~${ZT1} ${M_LOG_Y} replace"
exec_at_player "fill ~${XT2} ~5 ~${ZT2} ~${XT2} ~17 ~${ZT2} ${M_LOG_Y} replace"

# Door (south face).
exec_at_player "fill ~${X0} ~1 ~${ZT2} ~${X0} ~2 ~${ZT2} minecraft:air replace"
exec_at_player "setblock ~${X0} ~1 ~${ZT2} minecraft:spruce_door[facing=south,half=lower,hinge=left,open=false,powered=false]"
exec_at_player "setblock ~${X0} ~2 ~${ZT2} minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]"

# Windows (simple 1x2 panes).
exec_at_player "setblock ~${X0} ~8 ~${ZT1} ${M_GLASS} replace"
exec_at_player "setblock ~${X0} ~9 ~${ZT1} ${M_GLASS} replace"
exec_at_player "setblock ~${XT2} ~8 ~${Z0} ${M_GLASS} replace"
exec_at_player "setblock ~${XT2} ~9 ~${Z0} ${M_GLASS} replace"
exec_at_player "setblock ~${XT1} ~8 ~${Z0} ${M_GLASS} replace"
exec_at_player "setblock ~${XT1} ~9 ~${Z0} ${M_GLASS} replace"

# Roof (stepped pyramid, slight overhang).
exec_at_player "fill ~$((X0 - 4)) ~18 ~$((Z0 - 4)) ~$((X0 + 4)) ~18 ~$((Z0 + 4)) ${M_ROOF} replace"
exec_at_player "fill ~$((X0 - 3)) ~19 ~$((Z0 - 3)) ~$((X0 + 3)) ~19 ~$((Z0 + 3)) ${M_ROOF} replace"
exec_at_player "fill ~$((X0 - 2)) ~20 ~$((Z0 - 2)) ~$((X0 + 2)) ~20 ~$((Z0 + 2)) ${M_ROOF} replace"
exec_at_player "fill ~$((X0 - 1)) ~21 ~$((Z0 - 1)) ~$((X0 + 1)) ~21 ~$((Z0 + 1)) ${M_ROOF} replace"
exec_at_player "setblock ~${X0} ~22 ~${Z0} ${M_ROOF} replace"
exec_at_player "setblock ~${X0} ~23 ~${Z0} ${M_FENCE} replace"
exec_at_player "setblock ~${X0} ~24 ~${Z0} minecraft:lantern[hanging=false] replace"

# Axle (from tower west wall to hub).
exec_at_player "fill ~${XH} ~${YH} ~${ZH} ~${XT1} ~${YH} ~${ZH} ${M_LOG_X} replace"

# Blades (wool cross) + simple fence skeleton.
exec_at_player "fill ~${XH} ~$((YH - 6)) ~$((Z0 - 1)) ~${XH} ~$((YH + 6)) ~$((Z0 + 1)) minecraft:white_wool replace"
exec_at_player "fill ~${XH} ~$((YH - 1)) ~$((Z0 - 6)) ~${XH} ~$((YH + 1)) ~$((Z0 + 6)) minecraft:white_wool replace"

exec_at_player "fill ~${XH} ~$((YH - 6)) ~${Z0} ~${XH} ~$((YH + 6)) ~${Z0} ${M_FENCE} replace"
exec_at_player "fill ~${XH} ~${YH} ~$((Z0 - 6)) ~${XH} ~${YH} ~$((Z0 + 6)) ${M_FENCE} replace"
exec_at_player "setblock ~${XH} ~${YH} ~${Z0} ${M_LOG_X} replace"

tell_player "Windmill: done."
echo "OK"
