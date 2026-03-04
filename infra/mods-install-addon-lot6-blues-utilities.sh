#!/usr/bin/env bash
set -euo pipefail

# Installs addon rollout lot 6 for the Fabric Cobblemon server:
# - Blue's Cobblemon Utilities (published upstream as a datapack archive)
#
# Notes:
# - This lot installs a datapack zip into the active world.
# - Exact gameplay rollback still requires a world backup if players used the
#   datapack features before removal.
#
# Usage:
#   ./infra/mods-install-addon-lot6-blues-utilities.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

DATA_DIR="./data"
WORLD_DIR="${DATA_DIR}/world"
DATAPACKS_DIR="${WORLD_DIR}/datapacks"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

need_cmd curl
need_cmd sha256sum

if [[ ! -d "${WORLD_DIR}" ]]; then
  echo "World not found: ${WORLD_DIR}" >&2
  exit 2
fi

mkdir -p "${DATAPACKS_DIR}"

download_verify() {
  local url="$1"
  local sha="$2"
  local dst="$3"

  local tmp
  tmp="$(mktemp)"
  trap 'rm -f "${tmp}"' RETURN

  curl -fsSL --retry 3 --retry-delay 2 -o "${tmp}" "${url}"
  echo "${sha}  ${tmp}" | sha256sum -c - >/dev/null

  mkdir -p "$(dirname "${dst}")"
  mv -f "${tmp}" "${dst}"
  trap - RETURN
}

ensure_datapack_archive() {
  local name="$1"
  local url="$2"
  local sha="$3"
  local filename="$4"

  local dst="${DATAPACKS_DIR}/${filename}"
  if [[ -f "${dst}" ]]; then
    if echo "${sha}  ${dst}" | sha256sum -c - >/dev/null 2>&1; then
      echo "OK ${name} already installed: ${dst}"
      return 0
    fi

    local ts
    ts="$(date +%Y%m%d-%H%M%S)"
    mkdir -p "${REPO_ROOT}/backups/datapacks"
    mv "${dst}" "${REPO_ROOT}/backups/datapacks/${filename}.prev-${ts}"
    echo "WARN ${name} exists but hash mismatch, archived previous copy before re-download." >&2
  fi

  echo "== Installing ${name} =="
  download_verify "${url}" "${sha}" "${dst}"
  echo "OK installed ${name}: ${dst}"
}

# Blue's Cobblemon Utilities 4.0.0 for MC 1.21.1 (Modrinth version 9kqOqPlg)
BLUES_UTILITIES_URL="https://cdn.modrinth.com/data/HMbKoqXZ/versions/9kqOqPlg/Blue%27s%20Cobblemon%20Utilities.zip"
BLUES_UTILITIES_SHA256="6295c2e17be8ed92cb9a6668ab221afde613736329103edc37a97083a3f4f037"
BLUES_UTILITIES_FILE="blues-cobblemon-utilities-4.0.0.zip"

ensure_datapack_archive "Blue's Cobblemon Utilities" "${BLUES_UTILITIES_URL}" "${BLUES_UTILITIES_SHA256}" "${BLUES_UTILITIES_FILE}"

./infra/mc.sh reload >/dev/null 2>&1 || true
./infra/mc.sh "datapack list enabled" || true

echo "Done. If the server was offline during install, start it and verify datapack state."
echo "Rollback note: removing the zip is easy, but exact gameplay rollback still requires a world backup."
