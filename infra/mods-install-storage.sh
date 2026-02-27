#!/usr/bin/env bash
set -euo pipefail

# Installs storage-focused gameplay mods for the Fabric Cobblemon server:
# - Storage Drawers
# - Tom's Simple Storage Mod
#
# Notes:
# - Both mods are required on clients and server.
# - Versions are intentionally pinned for MC 1.21.1 / Fabric.
#
# Usage:
#   ./infra/mods-install-storage.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

DATA_DIR="./data"
MODS_DIR="${DATA_DIR}/mods"
mkdir -p "${MODS_DIR}"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

need_cmd curl
need_cmd sha256sum

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

ensure_mod() {
  local name="$1"
  local url="$2"
  local sha="$3"
  local filename="$4"

  local dst="${MODS_DIR}/${filename}"
  if [[ -f "${dst}" ]]; then
    if echo "${sha}  ${dst}" | sha256sum -c - >/dev/null 2>&1; then
      echo "OK ${name} already installed: ${dst}"
      return 0
    fi
    echo "WARN ${name} exists but hash mismatch, re-downloading: ${dst}" >&2
  fi

  echo "== Installing ${name} =="
  download_verify "${url}" "${sha}" "${dst}"
  echo "OK installed ${name}: ${dst}"
}

# Storage Drawers 1.21.1-13.11.4 (Fabric) (Modrinth version 78LmfH8Z)
STORAGEDRAWERS_URL="https://cdn.modrinth.com/data/guitPqEi/versions/78LmfH8Z/StorageDrawers-fabric-1.21.1-13.11.4.jar"
STORAGEDRAWERS_SHA256="6763a9f28148d5e90af8a5db647f5f8b97eea41ff78ca9870864321c4d4c2977"
STORAGEDRAWERS_FILE="StorageDrawers-fabric-1.21.1-13.11.4.jar"

# Tom's Simple Storage Mod 1.21-2.3.0-fabric (Modrinth version GwLz79tK)
TOMS_STORAGE_URL="https://cdn.modrinth.com/data/XZNI4Cpy/versions/GwLz79tK/toms_storage_fabric-1.21-2.3.0.jar"
TOMS_STORAGE_SHA256="fad39f7ed0ac20ab0345aeb7dbe1be0b2732fa11fd333b6874629e925c45d5d1"
TOMS_STORAGE_FILE="toms_storage_fabric-1.21-2.3.0.jar"

ensure_mod "Storage Drawers" "${STORAGEDRAWERS_URL}" "${STORAGEDRAWERS_SHA256}" "${STORAGEDRAWERS_FILE}"
ensure_mod "Tom's Storage" "${TOMS_STORAGE_URL}" "${TOMS_STORAGE_SHA256}" "${TOMS_STORAGE_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
