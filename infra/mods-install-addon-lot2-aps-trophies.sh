#!/usr/bin/env bash
set -euo pipefail

# Installs addon rollout lot 2 for the Fabric Cobblemon server:
# - APS Trophies
#
# Notes:
# - This mod is required on clients and server.
# - Catch Indicator is handled as a client-only recommendation in the runbook,
#   not as a server artifact.
#
# Usage:
#   ./infra/mods-install-addon-lot2-aps-trophies.sh

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

# APS Trophies 1.1.1 for MC 1.21.1 Fabric (Modrinth version LA6Nn9cA)
APS_TROPHIES_URL="https://cdn.modrinth.com/data/ZmP6jlh0/versions/LA6Nn9cA/aps_trophies-1.21.1-fabric-1.1.1.jar"
APS_TROPHIES_SHA256="17e55ba120ffc80105ad29cd7e34ab4f3a9112a349e6f8f49c995f1029d942bf"
APS_TROPHIES_FILE="aps_trophies-1.21.1-fabric-1.1.1.jar"

ensure_mod "APS Trophies" "${APS_TROPHIES_URL}" "${APS_TROPHIES_SHA256}" "${APS_TROPHIES_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
