#!/usr/bin/env bash
set -euo pipefail

# Installs addon rollout lot 10 for the Fabric Cobblemon server:
# - Cobblemon: Shiny Cookie
#
# Notes:
# - This mod is required on clients and server.
# - Gameplay persistence is explicitly accepted for this lot.
#
# Usage:
#   ./infra/mods-install-addon-lot10-shiny-cookie.sh

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

# Cobblemon: Shiny Cookie 0.0.1 for MC 1.21.1 Fabric (Modrinth version YIna1pKh)
SHINY_COOKIE_URL="https://cdn.modrinth.com/data/Nf67XeTi/versions/YIna1pKh/shinycookie-fabric-0.0.1.jar"
SHINY_COOKIE_SHA256="7bb5957c4a48a6a5a6130c8c17e0056bce1a7e31c6c94df96f755b1b57992e24"
SHINY_COOKIE_FILE="shinycookie-fabric-0.0.1.jar"

ensure_mod "Cobblemon: Shiny Cookie" "${SHINY_COOKIE_URL}" "${SHINY_COOKIE_SHA256}" "${SHINY_COOKIE_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
