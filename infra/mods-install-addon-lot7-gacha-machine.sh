#!/usr/bin/env bash
set -euo pipefail

# Installs addon rollout lot 7 for the Fabric Cobblemon server:
# - CobbledGacha
#
# Notes:
# - This mod is required on clients and server.
# - Keep distribution controlled during the initial maintenance window.
#
# Usage:
#   ./infra/mods-install-addon-lot7-gacha-machine.sh

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

# CobbledGacha 3.0.2 for MC 1.21.1 Fabric (Modrinth version Ifh7vKgZ)
GACHA_MACHINE_URL="https://cdn.modrinth.com/data/c1OpnQs3/versions/Ifh7vKgZ/cobbledgacha-fabric-1.21.1-3.0.2.jar"
GACHA_MACHINE_SHA256="67b16b87015b34fcad46a23c2a323287c95cce63b2fac537b0b480df751e9b46"
GACHA_MACHINE_FILE="cobbledgacha-fabric-1.21.1-3.0.2.jar"

ensure_mod "CobbledGacha" "${GACHA_MACHINE_URL}" "${GACHA_MACHINE_SHA256}" "${GACHA_MACHINE_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
