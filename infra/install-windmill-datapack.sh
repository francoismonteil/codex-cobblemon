#!/usr/bin/env bash
set -euo pipefail

# Installs/updates the acm_windmills datapack into the current world folder and reloads the server.
#
# This script is meant to be run on the Minecraft host (Linux), inside the repo root.
#
# Usage:
#   ./infra/install-windmill-datapack.sh
#   ./infra/install-windmill-datapack.sh --restart

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

src="${REPO_ROOT}/datapacks/acm_windmills"
world="${REPO_ROOT}/data/world"
dst="${world}/datapacks/acm_windmills"
restart="false"

if [[ "${1:-}" == "--restart" ]]; then
  restart="true"
fi

if [[ ! -d "${src}" ]]; then
  echo "Missing datapack source: ${src}" >&2
  exit 2
fi

if [[ ! -d "${world}" ]]; then
  echo "World not found: ${world}" >&2
  exit 2
fi

mkdir -p "${world}/datapacks"

ts="$(date +%Y%m%d-%H%M%S)"
if [[ -d "${dst}" ]]; then
  # Do not keep backups inside world/datapacks, otherwise Minecraft may auto-enable them and change overrides/order.
  mkdir -p "${REPO_ROOT}/backups/datapacks"
  mv "${dst}" "${REPO_ROOT}/backups/datapacks/acm_windmills.prev-${ts}"
fi

cp -a "${src}" "${dst}"
echo "Installed: ${dst}"

# Best-effort reload and verification.
./infra/mc.sh reload >/dev/null 2>&1 || true
./infra/mc.sh "datapack list enabled" || true

if [[ "${restart}" == "true" ]]; then
  # /reload does NOT reload dynamic registries (worldgen structures, etc). Restart to apply.
  ./infra/safe-restart.sh || true
else
  echo "NOTE: for worldgen structures to register (e.g. /place structure acm:windmill), restart the server:"
  echo "  ./infra/safe-restart.sh"
fi

echo "OK"
