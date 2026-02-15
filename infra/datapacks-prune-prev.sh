#!/usr/bin/env bash
set -euo pipefail

# Removes legacy "*.prev-*" datapack folders from the current world and disables them first (best-effort).
#
# Why:
# - Keeping backup datapacks inside data/world/datapacks makes Minecraft auto-discover and often auto-enable them.
# - That breaks override ordering and makes worldgen behavior unpredictable.
#
# This script is meant to be run on the Minecraft host (Linux), inside the repo root.
#
# Usage:
#   ./infra/datapacks-prune-prev.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

world="${REPO_ROOT}/data/world"
dp_dir="${world}/datapacks"

if [[ ! -d "${dp_dir}" ]]; then
  echo "World datapacks dir not found: ${dp_dir}" >&2
  exit 2
fi

shopt -s nullglob
prevs=("${dp_dir}"/*.prev-*)
shopt -u nullglob

if [[ ${#prevs[@]} -eq 0 ]]; then
  echo "No *.prev-* datapacks found in ${dp_dir}"
  exit 0
fi

echo "Found ${#prevs[@]} prev datapacks. Disabling + archiving..."
mkdir -p "${REPO_ROOT}/backups/datapacks"
ts="$(date +%Y%m%d-%H%M%S)"

for p in "${prevs[@]}"; do
  base="$(basename "${p}")"
  # Disable best-effort (do not fail if already disabled / server down).
  ./infra/mc.sh "datapack disable \"file/${base}\"" >/dev/null 2>&1 || true
  mv "${p}" "${REPO_ROOT}/backups/datapacks/${base}.pruned-${ts}"
  echo "  pruned: ${base}"
done

./infra/mc.sh reload >/dev/null 2>&1 || true
./infra/mc.sh "datapack list enabled" || true

echo "OK"

