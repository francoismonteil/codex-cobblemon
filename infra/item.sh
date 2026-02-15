#!/usr/bin/env bash
set -euo pipefail

# Give an item quickly.
#
# Usage:
#   ./infra/item.sh <item_id> [count] [player]
#
# Examples:
#   ./infra/item.sh minecraft:cobblestone 64
#   ./infra/item.sh cobblestone 64
#   ./infra/item.sh minecraft:diamond 3 <player>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <item_id> [count] [player]" >&2
  exit 2
fi

item="$1"
count="${2:-64}"
player="${3:-${DEFAULT_PLAYER_NAME:-}}"

if [[ -z "${player}" ]]; then
  echo "No target player. Set DEFAULT_PLAYER_NAME in .env or pass [player]." >&2
  exit 2
fi

if [[ "${item}" != *:* ]]; then
  item="minecraft:${item}"
fi

./infra/mc.sh "give ${player} ${item} ${count}"
