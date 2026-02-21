#!/usr/bin/env bash
set -euo pipefail

# Applies an "open world Cobblemon (4 players)" baseline to ./data/server.properties.
#
# Goals:
# - PvP off
# - Max 4 players
# - Distances tuned for a small LAN server
# - Natural terrain worldgen with structures enabled for village-based spawn
# - No vanilla spawn-protection (we rely on Flan claim for ~150 blocks spawn protection)
# - RCON off (we use console pipe via infra/mc.sh)
#
# Usage:
#   ./infra/server-profile-openworld-4p.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

props="./data/server.properties"
if [[ ! -f "${props}" ]]; then
  echo "Missing ${props} (server not bootstrapped yet?)" >&2
  exit 1
fi

ts="$(date +%Y%m%d-%H%M%S)"
cp -a "${props}" "${props}.bak.${ts}"

set_prop() {
  local key="$1"
  local value="$2"
  if grep -qE "^${key}=" "${props}"; then
    # Use | as sed delimiter to avoid escaping : in values.
    sed -i -E "s|^${key}=.*$|${key}=${value}|" "${props}"
  else
    printf '%s=%s\n' "${key}" "${value}" >>"${props}"
  fi
}

# Gameplay / rules
set_prop "pvp" "false"
set_prop "max-players" "4"
set_prop "difficulty" "easy"

# Ensure a natural world can generate villages/structures on fresh resets.
set_prop "generate-structures" "true"
set_prop "level-type" "minecraft\\:normal"
set_prop "generator-settings" "{}"

# Small server performance baseline (4 players)
set_prop "view-distance" "8"
set_prop "simulation-distance" "7"
set_prop "sync-chunk-writes" "false"
set_prop "network-compression-threshold" "512"
set_prop "entity-broadcast-range-percentage" "90"
set_prop "max-tick-time" "120000"

# Spawn protection: handled by Flan (allows doors/chests while preventing grief)
set_prop "spawn-protection" "0"

# Security / ops
set_prop "enable-rcon" "false"
set_prop "enforce-whitelist" "true"
set_prop "white-list" "true"

echo "OK applied open world profile to ${props}"
