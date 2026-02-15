#!/usr/bin/env bash
set -euo pipefail

# Installs/updates the acm_village_pokecenter datapack into the current world folder and reloads the server.
#
# This script is meant to be run on the Minecraft host (Linux), inside the repo root.
#
# Usage:
#   ./infra/install-village-pokecenter-datapack.sh
#   ./infra/install-village-pokecenter-datapack.sh --restart

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

src="${REPO_ROOT}/datapacks/acm_village_pokecenter"
world="${REPO_ROOT}/data/world"
dst="${world}/datapacks/acm_village_pokecenter"
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
  mv "${dst}" "${dst}.prev-${ts}"
fi

cp -a "${src}" "${dst}"
echo "Installed: ${dst}"

# If we keep backups, make sure they are not left enabled (they can override the active pack due to ordering).
for prev in "${world}/datapacks/acm_village_pokecenter.prev-"*; do
  [[ -d "${prev}" ]] || continue
  prev_id="file/$(basename "${prev}")"
  ./infra/mc.sh "datapack disable \"${prev_id}\"" >/dev/null 2>&1 || true
done

# Ensure the active pack is enabled (and loaded last so its overrides win).
./infra/mc.sh "datapack enable \"file/acm_village_pokecenter\" last" >/dev/null 2>&1 || true

# Best-effort reload and verification.
./infra/mc.sh reload >/dev/null 2>&1 || true
./infra/mc.sh "datapack list enabled" || true

if [[ "${restart}" == "true" ]]; then
  # /reload does NOT reload dynamic registries (worldgen structures, etc). Restart to apply.
  ./infra/safe-restart.sh || true
else
  echo "NOTE: this changes village worldgen (template pools). To apply reliably, restart the server:"
  echo "  ./infra/safe-restart.sh"
  echo "NOTE: only NEW villages in newly generated chunks are affected."
fi

echo "OK"
