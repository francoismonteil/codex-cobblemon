#!/usr/bin/env bash
set -euo pipefail

# Installs/updates the additionalstructures_1211 datapack into the active world.
# This is intended for NEW world rollout only.
#
# Usage:
#   ./infra/install-additionalstructures-datapack.sh --new-world
#   ./infra/install-additionalstructures-datapack.sh --new-world --allow-existing-world

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

src="${REPO_ROOT}/datapacks/additionalstructures_1211"
world="${REPO_ROOT}/data/world"
dst="${world}/datapacks/additionalstructures_1211"
new_world="false"
allow_existing_world="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --new-world)
      new_world="true"
      shift
      ;;
    --allow-existing-world)
      allow_existing_world="true"
      shift
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "${new_world}" != "true" ]]; then
  echo "Refusing install without explicit new-world acknowledgement." >&2
  echo "Use: ./infra/install-additionalstructures-datapack.sh --new-world" >&2
  exit 2
fi

if [[ ! -d "${src}" ]]; then
  echo "Missing datapack source: ${src}" >&2
  exit 2
fi
if [[ ! -f "${src}/pack.mcmeta" ]]; then
  echo "Missing pack.mcmeta in source: ${src}/pack.mcmeta" >&2
  exit 2
fi
if [[ ! -d "${world}" ]]; then
  echo "World not found: ${world}" >&2
  exit 2
fi

if [[ "${allow_existing_world}" != "true" ]]; then
  region_count="$(find "${world}/region" -maxdepth 1 -type f -name '*.mca' 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "${region_count}" != "0" ]]; then
    echo "Refusing install: existing overworld region files detected (${region_count})." >&2
    echo "This flow is intended for a NEW world rollout only." >&2
    echo "If this is an intentional controlled bootstrap flow, use:" >&2
    echo "  ./infra/install-additionalstructures-datapack.sh --new-world --allow-existing-world" >&2
    exit 2
  fi
fi

mkdir -p "${world}/datapacks"

ts="$(date +%Y%m%d-%H%M%S)"
if [[ -d "${dst}" ]]; then
  mkdir -p "${REPO_ROOT}/backups/datapacks"
  mv "${dst}" "${REPO_ROOT}/backups/datapacks/additionalstructures_1211.prev-${ts}"
fi

cp -a "${src}" "${dst}"
echo "Installed: ${dst}"

# Best effort pre-restart datapack command for immediate visibility.
./infra/mc.sh "datapack list enabled" >/dev/null 2>&1 || true

echo "Restart required for worldgen registries. Running safe restart..."
./infra/safe-restart.sh --force

echo "Post-restart datapack command:"
./infra/mc.sh "datapack list enabled" >/dev/null 2>&1 || true

echo "OK"
