#!/usr/bin/env bash
set -euo pipefail

# Adds simple spawn signage (vanilla signs) and a small "info board".
# Idempotent: overwrites the board area.
#
# Usage:
#   ./infra/spawn-signage.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

DUCKDNS_DOMAINS="${DUCKDNS_DOMAINS:-}"
SERVER_HOST="<duckdns-domain>.duckdns.org"
if [[ -n "${DUCKDNS_DOMAINS}" ]]; then
  # If multiple domains are configured, use the first.
  SERVER_HOST="${DUCKDNS_DOMAINS%%,*}.duckdns.org"
fi

cmd() { ./infra/mc.sh "$1"; sleep 0.2; }

SPAWN_Y=120
Y1=$((SPAWN_Y+1))

# Board location near center path
X1=-6; Z1=6

cmd "fill ${X1} ${Y1} ${Z1} $((X1+6)) $((Y1+4)) $((Z1+1)) minecraft:air"
cmd "fill ${X1} ${Y1} ${Z1} $((X1+6)) ${Y1} ${Z1} minecraft:smooth_quartz"
cmd "fill ${X1} $((Y1+1)) ${Z1} $((X1+6)) $((Y1+4)) ${Z1} minecraft:dark_oak_planks"
cmd "fill $((X1+1)) $((Y1+2)) ${Z1} $((X1+5)) $((Y1+3)) ${Z1} minecraft:glowstone"

# 3 signs
cmd "setblock $((X1+1)) $((Y1+2)) $((Z1-1)) minecraft:oak_wall_sign[facing=south]{front_text:{messages:['{\"text\":\"Welcome\"}','{\"text\":\"Spawn City\"}','{\"text\":\"\"}','{\"text\":\"\"}']}}"
cmd "setblock $((X1+3)) $((Y1+2)) $((Z1-1)) minecraft:oak_wall_sign[facing=south]{front_text:{messages:['{\"text\":\"Server\"}','{\"text\":\"${SERVER_HOST}\"}','{\"text\":\":25565\"}','{\"text\":\"\"}']}}"
cmd "setblock $((X1+5)) $((Y1+2)) $((Z1-1)) minecraft:oak_wall_sign[facing=south]{front_text:{messages:['{\"text\":\"Directions\"}','{\"text\":\"West: Center\"}','{\"text\":\"East: Mart\"}','{\"text\":\"North: Gym\"}']}}"

echo "OK"
