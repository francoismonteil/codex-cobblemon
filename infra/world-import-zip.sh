#!/usr/bin/env bash
set -euo pipefail

# Imports a world zip into the local library ./worlds/<name>.
#
# This does NOT touch the currently running world.
# Use world-switch.sh to activate.
#
# Usage:
#   ./infra/world-import-zip.sh /path/to/world.zip <name>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 /path/to/world.zip <name>" >&2
  exit 2
fi

zip_path="$1"
name="$2"

if [[ ! -f "${zip_path}" ]]; then
  echo "Missing zip: ${zip_path}" >&2
  exit 2
fi

WORLD_LIB="${REPO_ROOT}/worlds"
mkdir -p "${WORLD_LIB}"

tmp_dir="$(mktemp -d)"
cleanup() { rm -rf "${tmp_dir}" || true; }
trap cleanup EXIT

ts="$(date +%Y%m%d-%H%M%S)"

echo "[1/3] Extract..."
unzip -q "${zip_path}" -d "${tmp_dir}"

world_dir="$(find "${tmp_dir}" -maxdepth 4 -type f -name level.dat -print -quit | xargs -r dirname || true)"
if [[ -z "${world_dir}" || ! -f "${world_dir}/level.dat" ]]; then
  echo "Could not find extracted world folder (missing level.dat). Inspect: ${tmp_dir}" >&2
  exit 1
fi

dst="${WORLD_LIB}/${name}"
if [[ -e "${dst}" ]]; then
  mv "${dst}" "${dst}.bak.${ts}"
fi

echo "[2/3] Copy to library: ${dst}"
cp -a "${world_dir}" "${dst}"

echo "[3/3] Done."
echo "Imported: ${name}"
echo "Activate with: ./infra/world-switch.sh ${name}"

