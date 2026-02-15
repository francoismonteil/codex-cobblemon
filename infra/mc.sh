#!/usr/bin/env bash
set -euo pipefail

# Sends a command to the Minecraft server console (no RCON) using itzg/minecraft-server console pipe.
# Requires CREATE_CONSOLE_IN_PIPE=true in container env.
#
# Usage:
#   ./infra/mc.sh list
#   ./infra/mc.sh "gamemode creative <player>"
#   ./infra/mc.sh gamemode creative <player>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <minecraft-command...>" >&2
  exit 2
fi

cmd="$*"

# mc-send-to-console requires exec as UID 1000 on this image.
docker exec -u 1000 cobblemon mc-send-to-console "${cmd}"
