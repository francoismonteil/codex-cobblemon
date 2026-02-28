#!/usr/bin/env bash
set -euo pipefail

# Installs rollout lot 5 for the Fabric Cobblemon server:
# - Cristel Lib
# - Towns and Towers
#
# Notes:
# - This is the highest-risk rollout lot because it affects future village generation.
# - Versions are intentionally pinned for MC 1.21.1 / Fabric.
#
# Usage:
#   ./infra/mods-install-progressive-lot5-towns-and-towers.sh

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

# Cristel Lib 3.0.3 for MC 1.21.1 Fabric (Modrinth version h5nfApnW)
CRISTEL_LIB_URL="https://cdn.modrinth.com/data/cl223EMc/versions/h5nfApnW/cristellib-fabric-1.21.1-3.0.3.jar"
CRISTEL_LIB_SHA256="7a970af615b45e99d0d4f5446e6929603a769d6d7a6747aa726ed81019a298cd"
CRISTEL_LIB_FILE="cristellib-fabric-1.21.1-3.0.3.jar"

# Towns and Towers 1.13.7 for MC 1.21.1 Fabric (Modrinth version E4Wy3O8Y)
TOWNS_AND_TOWERS_URL="https://cdn.modrinth.com/data/DjLobEOy/versions/E4Wy3O8Y/t_and_t-neoforge-fabric-1.13.7%2B1.21.1.jar"
TOWNS_AND_TOWERS_SHA256="925d61a8cee8ca013bac15cda2fcfbdf647eb1cde50c414c18298ea3a627c640"
TOWNS_AND_TOWERS_FILE="t_and_t-neoforge-fabric-1.13.7+1.21.1.jar"

ensure_mod "Cristel Lib" "${CRISTEL_LIB_URL}" "${CRISTEL_LIB_SHA256}" "${CRISTEL_LIB_FILE}"
ensure_mod "Towns and Towers" "${TOWNS_AND_TOWERS_URL}" "${TOWNS_AND_TOWERS_SHA256}" "${TOWNS_AND_TOWERS_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
