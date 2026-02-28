#!/usr/bin/env bash
set -euo pipefail

# Installs rollout lot 4 for the Fabric Cobblemon server:
# - YUNG's API
# - YUNG's Better Strongholds
#
# Notes:
# - YUNG's Better Strongholds is server-required and client-unsupported.
# - Versions are intentionally pinned for MC 1.21.1 / Fabric.
#
# Usage:
#   ./infra/mods-install-progressive-lot4-yungs-strongholds.sh

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

# YUNG's API 1.21.1-Fabric-5.1.6 (Modrinth version 9aZPNrZC)
YUNGS_API_URL="https://cdn.modrinth.com/data/Ua7DFN59/versions/9aZPNrZC/YungsApi-1.21.1-Fabric-5.1.6.jar"
YUNGS_API_SHA256="36fb903a1ebcf1511745be2da9e5144f1d2465bff7a5c17beffd347399acd1ba"
YUNGS_API_FILE="YungsApi-1.21.1-Fabric-5.1.6.jar"

# YUNG's Better Strongholds 1.21.1-Fabric-5.1.3 (Modrinth version uYZShp1p)
YUNGS_BETTER_STRONGHOLDS_URL="https://cdn.modrinth.com/data/kidLKymU/versions/uYZShp1p/YungsBetterStrongholds-1.21.1-Fabric-5.1.3.jar"
YUNGS_BETTER_STRONGHOLDS_SHA256="1cb412c83aa0e8273d29a1122c5799eb15a48acc8f0b770efe451c516647f5f8"
YUNGS_BETTER_STRONGHOLDS_FILE="YungsBetterStrongholds-1.21.1-Fabric-5.1.3.jar"

ensure_mod "YUNG's API" "${YUNGS_API_URL}" "${YUNGS_API_SHA256}" "${YUNGS_API_FILE}"
ensure_mod "YUNG's Better Strongholds" "${YUNGS_BETTER_STRONGHOLDS_URL}" "${YUNGS_BETTER_STRONGHOLDS_SHA256}" "${YUNGS_BETTER_STRONGHOLDS_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
