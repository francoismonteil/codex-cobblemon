#!/usr/bin/env bash
set -euo pipefail

# Installs extra server-side mods required for the open-world setup:
# - Chunky (pre-generation)
# - Flan (spawn protection claim with allowed interactions)
# - Flan claim tool config (wooden hoe for claim + inspect)
#
# These are intentionally pinned to known-good builds for MC 1.21.1.
#
# Usage:
#   ./infra/mods-install-openworld.sh

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

# Chunky (Fabric) 1.4.23 (supports MC 1.21.1 according to CurseForge file metadata)
CHUNKY_URL="https://mediafilez.forgecdn.net/files/6383/251/Chunky-Fabric-1.4.23.jar"
CHUNKY_SHA256="3412b170247dde7351e0945d857e713bedf6fae05ab300aa74d06ffbde0ca07e"
CHUNKY_FILE="Chunky-Fabric-1.4.23.jar"

# Flan 1.21.1-1.12.1-fabric (Modrinth version OrDcCAju)
FLAN_URL="https://cdn.modrinth.com/data/Si383TIH/versions/OrDcCAju/flan-1.21.1-1.12.1-fabric.jar"
FLAN_SHA256="a7223d104963a2f6c8fe0aee71d566c8e042ada07706cb08cf12dce9560da510"
FLAN_FILE="flan-1.21.1-1.12.1-fabric.jar"

ensure_mod "Chunky" "${CHUNKY_URL}" "${CHUNKY_SHA256}" "${CHUNKY_FILE}"
ensure_mod "Flan" "${FLAN_URL}" "${FLAN_SHA256}" "${FLAN_FILE}"

bash "${REPO_ROOT}/infra/flan-configure-claim-tools.sh"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
