#!/usr/bin/env bash
set -euo pipefail

# Lists world snapshots stored in ./worlds.
#
# Usage:
#   ./infra/worlds-list.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

WORLD_LIB="${REPO_ROOT}/worlds"
mkdir -p "${WORLD_LIB}"

echo "World library: ${WORLD_LIB}"
echo ""

shopt -s nullglob
found="false"
for d in "${WORLD_LIB}"/*; do
  [[ -d "${d}" ]] || continue
  found="true"
  name="$(basename "${d}")"
  ok="no"
  [[ -f "${d}/level.dat" ]] && ok="yes"
  size="$(du -sh "${d}" 2>/dev/null | awk '{print $1}')"
  echo "- ${name}  (level.dat=${ok}, size=${size})"
done
shopt -u nullglob

if [[ "${found}" != "true" ]]; then
  echo "(empty)"
fi

