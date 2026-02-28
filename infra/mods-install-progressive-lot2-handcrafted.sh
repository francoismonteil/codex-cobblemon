#!/usr/bin/env bash
set -euo pipefail

# Installs rollout lot 2 for the Fabric Cobblemon server:
# - Resourceful Lib
# - Handcrafted
#
# Notes:
# - Both mods are required on clients and server.
# - Versions are intentionally pinned for MC 1.21.1 / Fabric.
#
# Usage:
#   ./infra/mods-install-progressive-lot2-handcrafted.sh

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

# Resourceful Lib 3.0.12 for MC 1.21.x Fabric (Modrinth version Hf91FuVF)
RESOURCEFUL_LIB_URL="https://cdn.modrinth.com/data/G1hIVOrD/versions/Hf91FuVF/resourcefullib-fabric-1.21-3.0.12.jar"
RESOURCEFUL_LIB_SHA256="93064c5aff85bf5e6385470f311fd1c7de172f58b02fefb1d2920db76f8cd8b5"
RESOURCEFUL_LIB_FILE="resourcefullib-fabric-1.21-3.0.12.jar"

# Handcrafted 4.0.3 for MC 1.21.1 Fabric (Modrinth version f0pKpUWd)
HANDCRAFTED_URL="https://cdn.modrinth.com/data/pJmCFF0p/versions/f0pKpUWd/handcrafted-fabric-1.21.1-4.0.3.jar"
HANDCRAFTED_SHA256="9609c27e2eeaed4c633ade2d68ad980cfbed0442a10239846a67e9c62bc1b230"
HANDCRAFTED_FILE="handcrafted-fabric-1.21.1-4.0.3.jar"

ensure_mod "Resourceful Lib" "${RESOURCEFUL_LIB_URL}" "${RESOURCEFUL_LIB_SHA256}" "${RESOURCEFUL_LIB_FILE}"
ensure_mod "Handcrafted" "${HANDCRAFTED_URL}" "${HANDCRAFTED_SHA256}" "${HANDCRAFTED_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
