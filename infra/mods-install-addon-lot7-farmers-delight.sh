#!/usr/bin/env bash
set -euo pipefail

# Installs addon rollout lot 7 for the Fabric Cobblemon server:
# - Farmer's Delight Refabricated
#
# Notes:
# - This is the Fabric-compatible Farmer's Delight line for MC 1.21.1.
# - The main CurseForge "Farmer's Delight" page targets Forge/NeoForge.
#
# Usage:
#   ./infra/mods-install-addon-lot7-farmers-delight.sh

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

# Farmer's Delight Refabricated 3.2.5 for MC 1.21.1 Fabric (Modrinth version Sddkv0PO)
FARMERS_DELIGHT_URL="https://cdn.modrinth.com/data/7vxePowz/versions/Sddkv0PO/FarmersDelight-1.21.1-3.2.5+refabricated.jar"
FARMERS_DELIGHT_SHA256="023bb687d0453dec1ad5de17c4d55a750bb0144046d6ad37022f99ef0a39fa4d"
FARMERS_DELIGHT_FILE="FarmersDelight-1.21.1-3.2.5+refabricated.jar"

ensure_mod "Farmer's Delight Refabricated" "${FARMERS_DELIGHT_URL}" "${FARMERS_DELIGHT_SHA256}" "${FARMERS_DELIGHT_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
