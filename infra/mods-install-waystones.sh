#!/usr/bin/env bash
set -euo pipefail

# Installs Waystones + Balm for the Fabric Cobblemon server.
#
# Notes:
# - Waystones is a gameplay mod and must also be installed on clients.
# - Versions are intentionally pinned to known-good builds for MC 1.21.1.
#
# Usage:
#   ./infra/mods-install-waystones.sh

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

# Waystones (Fabric) 21.1.27 for MC 1.21.1 (Modrinth version iemNwSsG)
WAYSTONES_URL="https://cdn.modrinth.com/data/LOpKHB2A/versions/iemNwSsG/waystones-fabric-1.21.1-21.1.27.jar"
WAYSTONES_SHA256="fb4b74ff72d835aef1c1f336ea8b4947ba8e4ff4833523d07435d76f8f2d1ed1"
WAYSTONES_FILE="waystones-fabric-1.21.1-21.1.27.jar"

# Balm (Fabric) 21.0.56 for MC 1.21.1 (Modrinth version x4SzggaK)
BALM_URL="https://cdn.modrinth.com/data/MBAkmtvl/versions/x4SzggaK/balm-fabric-1.21.1-21.0.56.jar"
BALM_SHA256="928f71d90b0064ba450e31211273c87491af13f820b3c1992b26811e0bd22d38"
BALM_FILE="balm-fabric-1.21.1-21.0.56.jar"

# Install dependency first, then the mod itself.
ensure_mod "Balm" "${BALM_URL}" "${BALM_SHA256}" "${BALM_FILE}"
ensure_mod "Waystones" "${WAYSTONES_URL}" "${WAYSTONES_SHA256}" "${WAYSTONES_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
