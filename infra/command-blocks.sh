#!/usr/bin/env bash
set -euo pipefail

# Enables or disables command blocks (server.properties) and restarts the server safely.
#
# Usage:
#   ./infra/command-blocks.sh on
#   ./infra/command-blocks.sh off
#
# Notes:
# - Required by some adventure maps that rely on pre-placed command blocks.
# - Keep whitelist enforced and avoid OP for non-admins.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

mode="${1:-}"
case "${mode}" in
  on|off) ;;
  *) echo "Usage: $0 on|off" >&2; exit 2 ;;
esac

props="./data/server.properties"
if [[ ! -f "${props}" ]]; then
  echo "Missing ${props}" >&2
  exit 1
fi

ts="$(date +%Y%m%d-%H%M%S)"
cp -a "${props}" "${props}.bak.${ts}"

val="false"
if [[ "${mode}" == "on" ]]; then
  val="true"
fi

if grep -qE '^enable-command-block=' "${props}"; then
  sed -i -E "s/^enable-command-block=.*/enable-command-block=${val}/" "${props}"
else
  printf '\nenable-command-block=%s\n' "${val}" >>"${props}"
fi

./infra/safe-restart.sh --force

# Reduce chat spam if the map uses command blocks heavily.
if [[ "${val}" == "true" ]]; then
  ./infra/mc.sh "gamerule commandBlockOutput false" || true
fi

echo "enable-command-block=${val}"

