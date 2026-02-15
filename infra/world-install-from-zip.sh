#!/usr/bin/env bash
set -euo pipefail

# Installs a Minecraft world from a zip archive into ./data/world.
#
# - Takes a backup first.
# - Stops the server, replaces ./data/world, restarts.
#
# Usage:
#   ./infra/world-install-from-zip.sh /path/to/world.zip

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/world.zip" >&2
  exit 2
fi

zip_path="$1"
if [[ ! -f "${zip_path}" ]]; then
  echo "Missing zip: ${zip_path}" >&2
  exit 2
fi

tmp_dir="$(mktemp -d)"
cleanup() { rm -rf "${tmp_dir}" || true; }
trap cleanup EXIT

ts="$(date +%Y%m%d-%H%M%S)"

echo "[1/5] Backup (primary + secondary if configured)..."
./infra/backup.sh
if [[ -x "./infra/backup-secondary.sh" ]]; then
  ./infra/backup-secondary.sh || true
fi

echo "[2/5] Extract..."
unzip -q "${zip_path}" -d "${tmp_dir}"

world_dir="$(find "${tmp_dir}" -maxdepth 3 -type f -name level.dat -print -quit | xargs -r dirname || true)"
if [[ -z "${world_dir}" || ! -f "${world_dir}/level.dat" ]]; then
  echo "Could not find extracted world folder (missing level.dat). Inspect: ${tmp_dir}" >&2
  exit 1
fi

echo "[3/5] Stop server..."
./infra/stop.sh || true

echo "[4/5] Replace ./data/world ..."
mkdir -p ./data
if [[ -d "./data/world" ]]; then
  mv "./data/world" "./data/world.bak.${ts}"
fi
cp -a "${world_dir}" "./data/world"

echo "[5/5] Start server..."
./infra/start.sh

echo "OK: Installed world into ./data/world (backup: ./data/world.bak.${ts})"

