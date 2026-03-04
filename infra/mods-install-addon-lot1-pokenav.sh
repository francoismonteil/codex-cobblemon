#!/usr/bin/env bash
set -euo pipefail

# Installs addon rollout lot 1 for the Fabric Cobblemon server:
# - Cobblemon Pokenav
#
# Notes:
# - This mod is required on clients and server.
# - Versions are intentionally pinned for MC 1.21.1 / Fabric / Cobblemon 1.7.3.
#
# Usage:
#   ./infra/mods-install-addon-lot1-pokenav.sh

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

# Cobblemon Pokenav 2.2.5 for MC 1.21.1 Fabric (Modrinth version VjtSuwwW)
POKENAV_URL="https://cdn.modrinth.com/data/bI8Nt3uA/versions/VjtSuwwW/cobblenav-fabric-2.2.5.jar"
POKENAV_SHA256="3fd669b03f152ab9f5ed3da71b25ea6b95944876367e6e289948bf8a1f159333"
POKENAV_FILE="cobblenav-fabric-2.2.5.jar"

ensure_mod "Cobblemon Pokenav" "${POKENAV_URL}" "${POKENAV_SHA256}" "${POKENAV_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
