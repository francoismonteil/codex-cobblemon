#!/usr/bin/env bash
set -euo pipefail

# Installs rollout lot 3 for the Fabric Cobblemon server:
# - Moonlight Lib
# - Supplementaries
#
# Notes:
# - Both mods are required on clients and server.
# - Versions are intentionally pinned for MC 1.21.1 / Fabric.
#
# Usage:
#   ./infra/mods-install-progressive-lot3-supplementaries.sh

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

# Moonlight Lib 1.21-2.29.18 for MC 1.21.1 Fabric (Modrinth version S33USEw7)
MOONLIGHT_URL="https://cdn.modrinth.com/data/twkfQtEc/versions/S33USEw7/moonlight-1.21-2.29.18-fabric.jar"
MOONLIGHT_SHA256="0be5b01582836211505a7fc5229340fd028fe4bf6d97760e06041c45fe6e5892"
MOONLIGHT_FILE="moonlight-1.21-2.29.18-fabric.jar"

# Supplementaries 1.21-3.5.25 for MC 1.21.1 Fabric (Modrinth version lCX23NTg)
SUPPLEMENTARIES_URL="https://cdn.modrinth.com/data/fFEIiSDQ/versions/lCX23NTg/supplementaries-1.21-3.5.25-fabric.jar"
SUPPLEMENTARIES_SHA256="5e42d3e5e7d4bbf86b8df269e4abdd1d6c7a1ea530141b6b2670db41a932851a"
SUPPLEMENTARIES_FILE="supplementaries-1.21-3.5.25-fabric.jar"

ensure_mod "Moonlight Lib" "${MOONLIGHT_URL}" "${MOONLIGHT_SHA256}" "${MOONLIGHT_FILE}"
ensure_mod "Supplementaries" "${SUPPLEMENTARIES_URL}" "${SUPPLEMENTARIES_SHA256}" "${SUPPLEMENTARIES_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
