#!/usr/bin/env bash
set -euo pipefail

# Installs the CurseForge world "Cobblemon Johto" into ./data/world.
#
# IMPORTANT:
# - Automated downloads from CurseForge may return HTTP 403 (bot protection).
# - If that happens, download the zip from your browser and then run:
#   ./infra/world-install-from-zip.sh ./downloads/<file>.zip
#
# Notes:
# - This project on CurseForge is "All Rights Reserved". Use it for your server,
#   but avoid re-uploading/redistributing the archive.
#
# Usage:
#   ./infra/world-install-cobblemon-johto.sh
#
# Optional env:
#   CF_FILE_ID=7507302 (default)
#   WORLD_ZIP=/path/to/world.zip (skip download and install this zip)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

CF_FILE_ID="${CF_FILE_ID:-7507302}" # Cobblemon Johto 1.3.1 (1.21.1) as of 2026-01-22
CF_URL="https://www.curseforge.com/minecraft/worlds/cobblemon-johto/download/${CF_FILE_ID}"

DOWNLOAD_DIR="${REPO_ROOT}/downloads"
mkdir -p "${DOWNLOAD_DIR}"

ts="$(date +%Y%m%d-%H%M%S)"
zip_path="${WORLD_ZIP:-${DOWNLOAD_DIR}/cobblemon-johto-${CF_FILE_ID}-${ts}.zip}"

if [[ -z "${WORLD_ZIP:-}" ]]; then
  echo "[1/2] Download world archive from CurseForge..."
  set +e
  curl -fL --retry 3 --retry-delay 2 -A "Mozilla/5.0" -o "${zip_path}" "${CF_URL}"
  rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    echo "Download failed (likely 403). Do this instead:" >&2
    echo "1) Download the map zip from your browser:" >&2
    echo "   CurseForge -> Cobblemon Johto -> Files -> Download" >&2
    echo "2) Upload it to the server into: ${DOWNLOAD_DIR}" >&2
    echo "3) Install with:" >&2
    echo "   ./infra/world-install-from-zip.sh ${DOWNLOAD_DIR}/<your-file>.zip" >&2
    exit 3
  fi
fi

echo "[2/2] Install world from zip: ${zip_path}"
./infra/world-install-from-zip.sh "${zip_path}"
