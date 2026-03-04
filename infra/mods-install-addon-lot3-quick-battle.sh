#!/usr/bin/env bash
set -euo pipefail

# Installs addon rollout lot 3 for the Fabric Cobblemon server:
# - Cobblemon Quick Battle
#
# Notes:
# - This mod is required on clients and server.
# - Versions are intentionally pinned for MC 1.21.1 / Fabric / Cobblemon 1.7.3.
#
# Usage:
#   ./infra/mods-install-addon-lot3-quick-battle.sh

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

# Cobblemon Quick Battle 1.2.5 for MC 1.21.1 Fabric (Modrinth version dTaK0vNR)
QUICK_BATTLE_URL="https://cdn.modrinth.com/data/55fHndP6/versions/dTaK0vNR/cobblemon_quick_battle-fabric-1.2.5.jar"
QUICK_BATTLE_SHA256="5f230102ae4575b615204ee8ce71e289dbbfc4113d3ebf2996a5464f5693501b"
QUICK_BATTLE_FILE="cobblemon_quick_battle-fabric-1.2.5.jar"

ensure_mod "Cobblemon Quick Battle" "${QUICK_BATTLE_URL}" "${QUICK_BATTLE_SHA256}" "${QUICK_BATTLE_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
