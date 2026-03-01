#!/usr/bin/env bash
set -euo pipefail

# Installs/updates the acm_pokemon_worldgen datapack into the active world folder.
#
# Usage:
#   ./infra/install-pokemon-worldgen-datapack.sh
#   ./infra/install-pokemon-worldgen-datapack.sh --restart

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

src="${REPO_ROOT}/datapacks/acm_pokemon_worldgen"
world="${REPO_ROOT}/data/world"
dst="${world}/datapacks/acm_pokemon_worldgen"
restart="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --restart)
      restart="true"
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--restart]" >&2
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      echo "Usage: $0 [--restart]" >&2
      exit 2
      ;;
  esac
done

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
  mkdir -p "${REPO_ROOT}/backups/datapacks"
  mv "${dst}" "${REPO_ROOT}/backups/datapacks/acm_pokemon_worldgen.prev-${ts}"
fi

cp -a "${src}" "${dst}"
echo "Installed: ${dst}"

./infra/mc.sh reload >/dev/null 2>&1 || true
./infra/mc.sh "datapack list enabled" || true

if [[ "${restart}" == "true" ]]; then
  echo "Running forced safe restart to apply worldgen registries..."
  ./infra/safe-restart.sh --force
else
  echo "NOTE: worldgen registries are not always reloaded by /reload."
  echo "Apply reliably with a restart:"
  echo "  ./infra/safe-restart.sh --force"
  echo "NOTE: only NEW chunks/villages are affected."
fi

echo "OK"
