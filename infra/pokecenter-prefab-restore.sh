#!/usr/bin/env bash
set -euo pipefail

# Restores a previously stashed Pokecenter prefab created by
# infra/pokecenter-prefab-stash.sh.
#
# Usage:
#   ./infra/pokecenter-prefab-restore.sh
#
# Notes:
# - Reads state from ./data/.pokecenter/prefab-stash.txt
# - Clears destination (stash) after restore.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

cmd() { ./infra/mc.sh "$1" >/dev/null; sleep 0.2; }
cmd_try() { ./infra/mc.sh "$1" >/dev/null 2>&1 || true; sleep 0.2; }

state_file="./data/.pokecenter/prefab-stash.txt"
if [[ ! -f "${state_file}" ]]; then
  echo "ERROR: missing stash state: ${state_file}" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "${state_file}"

echo "== Pokecenter prefab restore =="
echo "src(stash): x=${dst_x1}..${dst_x2} y=${dst_y1}..${dst_y2} z=${dst_z1}..${dst_z2}"
echo "dst(orig):  x=${src_x1}..${src_x2} y=${src_y1}..${src_y2} z=${src_z1}..${src_z2}"

dx=$((src_x2-src_x1+1)); dy=$((src_y2-src_y1+1)); dz=$((src_z2-src_z1+1))

cmd_try "say [MAINT] Pokecenter: restauration dans 5s."
sleep 5
admin_player="${DEFAULT_PLAYER_NAME:-}"
if [[ -n "${admin_player}" ]]; then
  cmd_try "execute as ${admin_player} if entity @s[x=${src_x1},y=$((src_y1-10)),z=${src_z1},dx=$((dx-1)),dy=$((dy+30)),dz=$((dz-1))] run tp @s 400 81 -1488"
else
  echo "WARN: DEFAULT_PLAYER_NAME is empty; skipping safety teleport." >&2
fi

echo "== Clear original volume =="
cmd "fill ${src_x1} ${src_y1} ${src_z1} ${src_x2} ${src_y2} ${src_z2} minecraft:air replace"

echo "== Clone back =="
cmd "clone ${dst_x1} ${dst_y1} ${dst_z1} ${dst_x2} ${dst_y2} ${dst_z2} ${src_x1} ${src_y1} ${src_z1} replace force"

echo "== Clear stash volume =="
cmd "fill ${dst_x1} ${dst_y1} ${dst_z1} ${dst_x2} ${dst_y2} ${dst_z2} minecraft:air replace"

rm -f "${state_file}"
cmd_try "say [MAINT] Pokecenter restaure. (stash supprime)"
echo "OK restored. State cleared."
