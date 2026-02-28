#!/usr/bin/env bash
set -euo pipefail

# Installs rollout lot 1 for the Fabric Cobblemon server:
# - Macaw's Furniture
#
# Notes:
# - This mod is required on clients and server.
# - Versions are intentionally pinned for MC 1.21.1 / Fabric.
#
# Usage:
#   ./infra/mods-install-progressive-lot1-macaws-furniture.sh

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

# Macaw's Furniture 3.4.1 for MC 1.21.1 Fabric (Modrinth version x2pXgG0s)
MACAWS_FURNITURE_URL="https://cdn.modrinth.com/data/dtWC90iB/versions/x2pXgG0s/mcw-furniture-3.4.1-mc1.21.1fabric.jar"
MACAWS_FURNITURE_SHA256="73d3f1f7b8a78c274919280161eefa36a3486f6b343e27f2bdd055ecf9a1da95"
MACAWS_FURNITURE_FILE="mcw-furniture-3.4.1-mc1.21.1fabric.jar"

ensure_mod "Macaw's Furniture" "${MACAWS_FURNITURE_URL}" "${MACAWS_FURNITURE_SHA256}" "${MACAWS_FURNITURE_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
