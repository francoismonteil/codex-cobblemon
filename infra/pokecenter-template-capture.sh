#!/usr/bin/env bash
set -euo pipefail

# Captures (clones) the current Pokecenter prefab area into a hidden "template" area
# in the same world, so future spawns can reproduce manual in-game edits exactly.
#
# Why:
# - Some mod blocks (ex: Cobblemon PC) are multi-block and/or have states that are hard
#   to reproduce reliably with a pure procedural script.
# - If you tweak the prefab manually in-game, re-capturing the template lets automation
#   reproduce those changes with /clone.
#
# Default source (current 12x10 pokecenter area):
#   x=419..428, y=69..91, z=-1512..-1501
#
# Default template destination (same x/z, higher Y so it doesn't interfere):
#   dst: x=419..428, y=230..252, z=-1512..-1501
#
# Usage:
#   ./infra/pokecenter-template-capture.sh
#   ./infra/pokecenter-template-capture.sh --src 419 69 -1512 428 91 -1501 --dst 419 230 -1512

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

cmd() { ./infra/mc.sh "$1" >/dev/null; sleep 0.25; }
cmd_try() { ./infra/mc.sh "$1" >/dev/null 2>&1 || true; sleep 0.25; }

src_x1=419; src_y1=69; src_z1=-1512
src_x2=428; src_y2=91; src_z2=-1501

dst_x1=419; dst_y1=230; dst_z1=-1512

while [[ $# -gt 0 ]]; do
  case "$1" in
    --src)
      src_x1="${2:?}"; src_y1="${3:?}"; src_z1="${4:?}"
      src_x2="${5:?}"; src_y2="${6:?}"; src_z2="${7:?}"
      shift 7
      ;;
    --dst)
      dst_x1="${2:?}"; dst_y1="${3:?}"; dst_z1="${4:?}"
      shift 4
      ;;
    -h|--help)
      cat <<EOF
Usage:
  $0 [--src x1 y1 z1 x2 y2 z2] [--dst x y z]
EOF
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

for v in "${src_x1}" "${src_y1}" "${src_z1}" "${src_x2}" "${src_y2}" "${src_z2}" "${dst_x1}" "${dst_y1}" "${dst_z1}"; do
  if ! [[ "${v}" =~ ^-?[0-9]+$ ]]; then
    echo "Invalid integer: ${v}" >&2
    exit 2
  fi
done

if (( src_x1 > src_x2 )); then t="${src_x1}"; src_x1="${src_x2}"; src_x2="${t}"; fi
if (( src_y1 > src_y2 )); then t="${src_y1}"; src_y1="${src_y2}"; src_y2="${t}"; fi
if (( src_z1 > src_z2 )); then t="${src_z1}"; src_z1="${src_z2}"; src_z2="${t}"; fi

dx=$((src_x2-src_x1+1))
dy=$((src_y2-src_y1+1))
dz=$((src_z2-src_z1+1))

dst_x2=$((dst_x1+dx-1))
dst_y2=$((dst_y1+dy-1))
dst_z2=$((dst_z1+dz-1))

state_dir="./data/.pokecenter"
state_file="${state_dir}/template-12x10-decorated-west.txt"
mkdir -p "${state_dir}"

echo "== Pokecenter template capture =="
echo "src: x=${src_x1}..${src_x2} y=${src_y1}..${src_y2} z=${src_z1}..${src_z2} (size ${dx}x${dy}x${dz})"
echo "dst: x=${dst_x1}..${dst_x2} y=${dst_y1}..${dst_y2} z=${dst_z1}..${dst_z2}"
echo "state: ${state_file}"

cmd_try "say [MAINT] Pokecenter: capture template (clone) dans 3s."
sleep 3

# Best-effort: move the admin away if they're in the source/destination volumes.
admin_player="${DEFAULT_PLAYER_NAME:-}"
if [[ -n "${admin_player}" ]]; then
  cmd_try "execute as ${admin_player} if entity @s[x=${src_x1},y=$((src_y1-10)),z=${src_z1},dx=$((dx-1)),dy=$((dy+30)),dz=$((dz-1))] run tp @s 400 81 -1488"
  cmd_try "execute as ${admin_player} if entity @s[x=${dst_x1},y=$((dst_y1-10)),z=${dst_z1},dx=$((dx-1)),dy=$((dy+30)),dz=$((dz-1))] run tp @s 400 81 -1488"
else
  echo "WARN: DEFAULT_PLAYER_NAME is empty; skipping safety teleport." >&2
fi

cmd_try "save-all flush"

echo "== Clone to template =="
cmd "clone ${src_x1} ${src_y1} ${src_z1} ${src_x2} ${src_y2} ${src_z2} ${dst_x1} ${dst_y1} ${dst_z1} replace force"

cat >"${state_file}" <<EOF
src_x1=${src_x1}
src_y1=${src_y1}
src_z1=${src_z1}
src_x2=${src_x2}
src_y2=${src_y2}
src_z2=${src_z2}
dst_x1=${dst_x1}
dst_y1=${dst_y1}
dst_z1=${dst_z1}
dst_x2=${dst_x2}
dst_y2=${dst_y2}
dst_z2=${dst_z2}
variant=decorated
facing=west
width=12
depth=10
EOF

cmd_try "say [MAINT] Pokecenter template updated (12x10 decorated west)."
echo "OK captured template."
