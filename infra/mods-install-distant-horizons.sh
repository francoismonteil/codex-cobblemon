#!/usr/bin/env bash
set -euo pipefail

# Installs Distant Horizons server support for the Fabric Cobblemon server.
#
# Notes:
# - Players without Distant Horizons can still join normally.
# - Players need Distant Horizons client-side to benefit from long-distance LOD.
# - Version is pinned for MC 1.21.1 and verified with SHA512 from Modrinth metadata.
#
# Usage:
#   ./infra/mods-install-distant-horizons.sh

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
need_cmd sha512sum

download_verify() {
  local url="$1"
  local sha512="$2"
  local dst="$3"

  local tmp
  tmp="$(mktemp)"
  trap 'rm -f "${tmp}"' RETURN

  curl -fsSL --retry 3 --retry-delay 2 -o "${tmp}" "${url}"
  echo "${sha512}  ${tmp}" | sha512sum -c - >/dev/null

  mkdir -p "$(dirname "${dst}")"
  mv -f "${tmp}" "${dst}"
  trap - RETURN
}

ensure_mod() {
  local name="$1"
  local url="$2"
  local sha512="$3"
  local filename="$4"

  local dst="${MODS_DIR}/${filename}"
  if [[ -f "${dst}" ]]; then
    if echo "${sha512}  ${dst}" | sha512sum -c - >/dev/null 2>&1; then
      echo "OK ${name} already installed: ${dst}"
      return 0
    fi
    echo "WARN ${name} exists but hash mismatch, re-downloading: ${dst}" >&2
  fi

  echo "== Installing ${name} =="
  download_verify "${url}" "${sha512}" "${dst}"
  echo "OK installed ${name}: ${dst}"
}

# Distant Horizons 2.4.5-b for MC 1.21.1 (Modrinth version bLPLghy9)
DH_URL="https://cdn.modrinth.com/data/uCdwusMi/versions/bLPLghy9/DistantHorizons-2.4.5-b-1.21.1-fabric-neoforge.jar"
DH_SHA512="6ee8b04af858450eac2e0fe6c3a6cb09dfc0f9c1691fb0f76f79bbc73e08e5dca6f18257294ba647b1520d4fb2110bbbb085830e536c8f4638995c75f66fe1eb"
DH_FILE="DistantHorizons-2.4.5-b-1.21.1-fabric-neoforge.jar"

ensure_mod "Distant Horizons" "${DH_URL}" "${DH_SHA512}" "${DH_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
