#!/usr/bin/env bash
set -euo pipefail

# Paste a classic MCEdit/WorldEdit "Alpha" .schematic near a player by:
# 1) querying the player's current Pos via a vanilla command (logged to console)
# 2) generating a command stream (fill/setblock) with modern block names
# 3) piping the commands directly into the server console named pipe
#
# This avoids needing WorldEdit installed on the server.
#
# Usage:
#   ./infra/spawn-schematic-mcedit.sh --schematic "downloads/Windmill - (mcbuild_org).schematic" --player <player>
#   ./infra/spawn-schematic-mcedit.sh --schematic "downloads/Windmill - (mcbuild_org).schematic" --dx 20 --dz 0
#   ./infra/spawn-schematic-mcedit.sh --schematic "downloads/Windmill - (mcbuild_org).schematic" --at 0 124 0 --dx 80 --dz 0
#   ./infra/spawn-schematic-mcedit.sh --schematic ... --no-clear

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

player="${DEFAULT_PLAYER_NAME:-PlayerName}"
schematic=""
at=""
dx="20"
dy="0"
dz="0"
do_clear="true"
ignore_we_offset="false"

usage() {
  cat <<EOF >&2
Usage:
  $0 --schematic <path> [--player <name> | --at <x> <y> <z>] [--dx <int>] [--dy <int>] [--dz <int>] [--no-clear] [--no-we-offset]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --schematic)
      schematic="${2:?}"
      shift 2
      ;;
    --player)
      player="${2:?}"
      shift 2
      ;;
    --at)
      at="${2:?} ${3:?} ${4:?}"
      shift 4
      ;;
    --dx)
      dx="${2:?}"
      shift 2
      ;;
    --dy)
      dy="${2:?}"
      shift 2
      ;;
    --dz)
      dz="${2:?}"
      shift 2
      ;;
    --no-clear)
      do_clear="false"
      shift
      ;;
    --no-we-offset)
      ignore_we_offset="true"
      shift
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

if [[ -z "${schematic}" ]]; then
  echo "Missing --schematic" >&2
  usage
  exit 2
fi

if [[ ! -f "${schematic}" ]]; then
  echo "Schematic not found: ${schematic}" >&2
  exit 2
fi

for v in "${dx}" "${dy}" "${dz}"; do
  if ! [[ "${v}" =~ ^-?[0-9]+$ ]]; then
    echo "Invalid integer offset: ${v}" >&2
    exit 2
  fi
done

if [[ -n "${at}" ]]; then
  read -r ox oy oz <<<"${at}"
  for v in "${ox}" "${oy}" "${oz}"; do
    if ! [[ "${v}" =~ ^-?[0-9]+$ ]]; then
      echo "Invalid --at (expected integers): ${at}" >&2
      exit 2
    fi
  done
  px=""; py=""; pz=""
else
  prev_line="$(docker logs cobblemon --tail 400 2>/dev/null | grep -F "${player} has the following entity data" | tail -n 1 || true)"

  # Ask the server to print the current player position to console.
  docker exec -u 1000 cobblemon mc-send-to-console data get entity "${player}" Pos >/dev/null 2>&1 || true

  pos_line=""
  for _ in $(seq 1 30); do
    pos_line="$(docker logs cobblemon --tail 400 2>/dev/null | grep -F "${player} has the following entity data" | tail -n 1 || true)"
    if [[ -n "${pos_line}" && "${pos_line}" != "${prev_line}" ]]; then
      break
    fi
    sleep 0.2
  done

  if [[ -z "${pos_line}" || "${pos_line}" == "${prev_line}" ]]; then
    echo "Failed to read player position from logs. Is ${player} online? (or use --at x y z)" >&2
    exit 1
  fi

  # Extract floats: [...d, ...d, ...d]
  read -r px py pz < <(echo "${pos_line}" | sed -nE 's/.*\[(-?[0-9.]+)d, (-?[0-9.]+)d, (-?[0-9.]+)d\].*/\1 \2 \3/p')
  if [[ -z "${px:-}" || -z "${py:-}" || -z "${pz:-}" ]]; then
    echo "Failed to parse position line: ${pos_line}" >&2
    exit 1
  fi

  # Snap to block grid like other infra scripts: floor(), and use Y-1 as the block under feet.
  read -r ox oy oz < <(python3 - <<PY
import math
px=float("${px}"); py=float("${py}"); pz=float("${pz}")
print(math.floor(px), math.floor(py)-1, math.floor(pz))
PY
  )
fi

clear_args=()
if [[ "${do_clear}" == "true" ]]; then
  clear_args+=(--clear)
fi

we_args=()
if [[ "${ignore_we_offset}" == "true" ]]; then
  we_args+=(--no-we-offset)
fi

echo "== spawn schematic (mcedit/alpha) =="
echo "player: ${player}"
if [[ -n "${at}" ]]; then
  echo "origin: ${ox} ${oy} ${oz} (--at)"
else
  echo "player_pos: ${px} ${py} ${pz} (snapped origin under feet: ${ox} ${oy} ${oz})"
fi
echo "schematic: ${schematic}"
echo "offset: dx=${dx} dy=${dy} dz=${dz}"

read -r x1 y1 z1 x2 y2 z2 < <(python3 ./infra/schematic-mcedit-to-commands.py \
  --schematic "${schematic}" \
  --origin "${ox}" "${oy}" "${oz}" \
  --dx "${dx}" --dy "${dy}" --dz "${dz}" \
  "${we_args[@]}" \
  --print-bounds)

tmp="$(mktemp)"
cleanup() {
  rm -f "${tmp}" >/dev/null 2>&1 || true
  if [[ -n "${x1:-}" && -n "${z1:-}" && -n "${x2:-}" && -n "${z2:-}" ]]; then
    docker exec -u 1000 cobblemon mc-send-to-console forceload remove "${x1}" "${z1}" "${x2}" "${z2}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "bounds: x=${x1}..${x2} y=${y1}..${y2} z=${z1}..${z2}"

# Ensure all target chunks are loaded before we start streaming setblock commands.
docker exec -u 1000 cobblemon mc-send-to-console forceload add "${x1}" "${z1}" "${x2}" "${z2}" >/dev/null 2>&1 || true
sleep 5

python3 ./infra/schematic-mcedit-to-commands.py \
  --schematic "${schematic}" \
  --origin "${ox}" "${oy}" "${oz}" \
  --dx "${dx}" --dy "${dy}" --dz "${dz}" \
  "${clear_args[@]}" \
  "${we_args[@]}" \
  --output "${tmp}"

# Stream the generated commands into the server console named pipe in a single docker exec.
docker exec -u 1000 -i cobblemon sh -lc 'cat > /tmp/minecraft-console-in' <"${tmp}"

docker exec -u 1000 cobblemon mc-send-to-console tell "${player}" "[SPAWN] Schematic pasted (${schematic##*/}) at origin=${ox},${oy},${oz} dx=${dx} dy=${dy} dz=${dz}" >/dev/null 2>&1 || true

# Best-effort: clean up forceload once pasted.
docker exec -u 1000 cobblemon mc-send-to-console forceload remove "${x1}" "${z1}" "${x2}" "${z2}" >/dev/null 2>&1 || true

echo "OK"
