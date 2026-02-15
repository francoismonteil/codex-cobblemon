#!/usr/bin/env bash
set -euo pipefail

# Temporarily removes the Pokecenter prefab by stashing it elsewhere (clone) and clearing
# the original area. This is reversible via infra/pokecenter-prefab-restore.sh.
#
# Default target is the prefab we built in this repo/runbook:
# - x=420..428, z=-1510..-1500, y=70..79
#
# Usage:
#   ./infra/pokecenter-prefab-stash.sh
#   ./infra/pokecenter-prefab-stash.sh --x1 420 --x2 428 --z1 -1510 --z2 -1500 --y1 70 --y2 79 --stash-y 200
#
# Notes:
# - Requires OP permissions (console command).
# - Uses /clone which is limited in volume (this prefab is small).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

cmd() { ./infra/mc.sh "$1" >/dev/null; sleep 0.2; }
cmd_try() { ./infra/mc.sh "$1" >/dev/null 2>&1 || true; sleep 0.2; }

x1=420; x2=428
z1=-1510; z2=-1500
y1=70; y2=79
stash_y=200
stash_x=""
stash_z=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --x1) x1="$2"; shift 2 ;;
    --x2) x2="$2"; shift 2 ;;
    --z1) z1="$2"; shift 2 ;;
    --z2) z2="$2"; shift 2 ;;
    --y1) y1="$2"; shift 2 ;;
    --y2) y2="$2"; shift 2 ;;
    --stash-y) stash_y="$2"; shift 2 ;;
    --stash-x) stash_x="$2"; shift 2 ;;
    --stash-z) stash_z="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

for v in "${x1}" "${x2}" "${y1}" "${y2}" "${z1}" "${z2}" "${stash_y}"; do
  if ! [[ "${v}" =~ ^-?[0-9]+$ ]]; then
    echo "Invalid integer: ${v}" >&2
    exit 2
  fi
done

if [[ -z "${stash_x}" ]]; then stash_x="${x1}"; fi
if [[ -z "${stash_z}" ]]; then stash_z="${z1}"; fi
for v in "${stash_x}" "${stash_z}"; do
  if ! [[ "${v}" =~ ^-?[0-9]+$ ]]; then
    echo "Invalid integer: ${v}" >&2
    exit 2
  fi
done

if (( x1 > x2 )); then t="${x1}"; x1="${x2}"; x2="${t}"; fi
if (( y1 > y2 )); then t="${y1}"; y1="${y2}"; y2="${t}"; fi
if (( z1 > z2 )); then t="${z1}"; z1="${z2}"; z2="${t}"; fi

dx=$((x2-x1+1)); dy=$((y2-y1+1)); dz=$((z2-z1+1))
sx1="${stash_x}"; sy1="${stash_y}"; sz1="${stash_z}"
sx2=$((sx1+dx-1)); sy2=$((sy1+dy-1)); sz2=$((sz1+dz-1))

state_dir="./data/.pokecenter"
state_file="${state_dir}/prefab-stash.txt"
mkdir -p "${state_dir}"

if [[ -f "${state_file}" ]]; then
  echo "ERROR: stash state already exists: ${state_file}" >&2
  echo "If you already stashed it, run: ./infra/pokecenter-prefab-restore.sh" >&2
  exit 1
fi

echo "== Pokecenter prefab stash =="
echo "src: x=${x1}..${x2} y=${y1}..${y2} z=${z1}..${z2} (size ${dx}x${dy}x${dz})"
echo "dst: x=${sx1}..${sx2} y=${sy1}..${sy2} z=${sz1}..${sz2}"

# Best-effort: warn + move the admin away if they're in the build area.
cmd_try "say [MAINT] Pokecenter: stash temporaire (suppression reversible) dans 5s."
sleep 5
admin_player="${DEFAULT_PLAYER_NAME:-}"
if [[ -n "${admin_player}" ]]; then
  cmd_try "execute as ${admin_player} if entity @s[x=${x1},y=$((y1-10)),z=${z1},dx=$((dx-1)),dy=$((dy+30)),dz=$((dz-1))] run tp @s 400 81 -1488"
else
  echo "WARN: DEFAULT_PLAYER_NAME is empty; skipping safety teleport." >&2
fi

echo "== Clear destination volume =="
cmd "fill ${sx1} ${sy1} ${sz1} ${sx2} ${sy2} ${sz2} minecraft:air replace"

echo "== Clone to stash =="
cmd "clone ${x1} ${y1} ${z1} ${x2} ${y2} ${z2} ${sx1} ${sy1} ${sz1} replace force"

echo "== Clear original volume =="
cmd "fill ${x1} ${y1} ${z1} ${x2} ${y2} ${z2} minecraft:air replace"

cat >"${state_file}" <<EOF
src_x1=${x1}
src_x2=${x2}
src_y1=${y1}
src_y2=${y2}
src_z1=${z1}
src_z2=${z2}
dst_x1=${sx1}
dst_x2=${sx2}
dst_y1=${sy1}
dst_y2=${sy2}
dst_z1=${sz1}
dst_z2=${sz2}
EOF

cmd_try "say [MAINT] Pokecenter stashed. Pour restaurer: ./infra/pokecenter-prefab-restore.sh"
echo "OK stashed. State saved to ${state_file}"
