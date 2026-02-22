#!/usr/bin/env bash
set -euo pipefail

# One-command onboarding for a friend.
#
# Usage:
#   ./infra/onboard.sh <Pseudo> [--op]
#
# What it does:
# - whitelist add
# - optional op
# - sends a small welcome message in chat

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <Pseudo> [--op]" >&2
  exit 2
fi

name="$1"
shift

do_op="false"
if [[ "${1:-}" == "--op" ]]; then
  do_op="true"
fi

if [[ "${do_op}" == "true" ]]; then
  ./infra/player.sh add "${name}" --op
else
  ./infra/player.sh add "${name}"
fi

# Keep it simple and compatible (no fancy JSON/tellraw needed).
./infra/mc.sh "say [WELCOME] ${name} added to whitelist."
domain="<duckdns-domain>.duckdns.org"
if [[ -n "${DUCKDNS_DOMAINS:-}" ]]; then
  # If multiple domains are configured, show the first.
  domain="${DUCKDNS_DOMAINS%%,*}.duckdns.org"
fi
./infra/mc.sh "say [INFO] Server: ${domain}:25565"
./infra/mc.sh "say [INFO] Client: MC 1.21.1 + Cobblemon Official Modpack [Fabric] 1.7.3"
./infra/mc.sh "say [INFO] Si tu ne peux pas rejoindre: verifie que tes versions de mods correspondent au serveur (pas d'auto-update)."

# Optional: give a small starter kit when onboarding.
if [[ "${STARTER_ON_ONBOARD:-true}" == "true" ]]; then
  if [[ -x "./infra/starter.sh" ]]; then
    ./infra/starter.sh --queue-if-offline "${name}" || true
  fi
fi

# Optional: set player's spawnpoint and/or teleport them to spawn.
SPAWN_X="${ONBOARD_SPAWN_X:-0}"
SPAWN_Y="${ONBOARD_SPAWN_Y:-120}"
SPAWN_Z="${ONBOARD_SPAWN_Z:-0}"

# If enabled, use the current world's spawn (from level.dat) instead of fixed coords.
if [[ "${ONBOARD_USE_WORLD_SPAWN:-true}" == "true" ]]; then
  if [[ -x "./infra/world-spawn.sh" ]]; then
    if spawn="$(./infra/world-spawn.sh 2>/dev/null)"; then
      read -r SPAWN_X SPAWN_Y SPAWN_Z <<<"${spawn}"
    fi
  fi
fi

if [[ "${ONBOARD_SET_SPAWNPOINT:-true}" == "true" ]]; then
  ./infra/mc.sh "spawnpoint ${name} ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}" || true
fi
if [[ "${ONBOARD_TP_TO_SPAWN:-true}" == "true" ]]; then
  ./infra/mc.sh "tp ${name} ${SPAWN_X} $((SPAWN_Y+1)) ${SPAWN_Z}" || true
fi
