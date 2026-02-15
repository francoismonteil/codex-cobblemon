#!/usr/bin/env bash
set -euo pipefail

# Enforces "Cobblemon chill" baseline server.properties settings.
#
# Applies:
# - PvE only: pvp=false
# - Whitelist enforced: enforce-whitelist=true
# - Casual: difficulty=easy
#
# Then restarts the server (safe restart, skips if players online unless forced).
#
# Usage:
#   ./infra/pve-chill.sh
#   ./infra/pve-chill.sh --force

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

force_flag=""
if [[ "${1:-}" == "--force" ]]; then
  force_flag="--force"
fi

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

set_prop "pvp" "false"
set_prop "enforce-whitelist" "true"
set_prop "difficulty" "easy"

./infra/mc.sh "say [SERVER] Applying PvE/casual settings, restart incoming..." || true
./infra/safe-restart.sh ${force_flag}

