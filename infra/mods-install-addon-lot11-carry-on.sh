#!/usr/bin/env bash
set -euo pipefail

# Installs addon rollout lot 11 for the Fabric Cobblemon server:
# - Carry On
#
# Notes:
# - This mod is required on clients and server.
#
# Usage:
#   ./infra/mods-install-addon-lot11-carry-on.sh

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

# Carry On 2.2.4.4 for MC 1.21.1 Fabric (CurseForge file 7393887)
CARRY_ON_URL="https://mediafilez.forgecdn.net/files/7393/887/carryon-fabric-1.21.1-2.2.4.4.jar"
CARRY_ON_SHA256="968ebd25576aaee7dcf1e839956e3749302a74516c55f9e3b8b5a3e4d1cf251b"
CARRY_ON_FILE="carryon-fabric-1.21.1-2.2.4.4.jar"

ensure_mod "Carry On" "${CARRY_ON_URL}" "${CARRY_ON_SHA256}" "${CARRY_ON_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
