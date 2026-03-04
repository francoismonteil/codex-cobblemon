#!/usr/bin/env bash
set -euo pipefail

# Installs addon rollout lot 5 for the Fabric Cobblemon server:
# - GeckoLib
# - Cobblemon Raid Dens
#
# Notes:
# - GeckoLib is a required dependency for Raid Dens.
# - Raid Dens is required on clients and server.
# - Raid Dens Design stays out of scope until a primary source is pinned.
#
# Usage:
#   ./infra/mods-install-addon-lot5-raiddens.sh

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

# GeckoLib 4.8.4 for MC 1.21.1 Fabric (Modrinth version 3GjkJptS)
GECKOLIB_URL="https://cdn.modrinth.com/data/8BmcQJ2H/versions/3GjkJptS/geckolib-fabric-1.21.1-4.8.4.jar"
GECKOLIB_SHA256="905df8858ed4aa3a5c2a845b7c83bf1e3274c348d8e623269e7e245a3e2e647d"
GECKOLIB_FILE="geckolib-fabric-1.21.1-4.8.4.jar"

# Cobblemon Raid Dens 0.8.1+1.21.1 for MC 1.21.1 Fabric (Modrinth version viyx90Qw)
RAID_DENS_URL="https://cdn.modrinth.com/data/GebWh45l/versions/viyx90Qw/cobblemonraiddens-fabric-0.8.1%2B1.21.1.jar"
RAID_DENS_SHA256="2dfc086e3a9ce8621d5c3a55202baeec416cde1819f2b8653b61a7ea3641bf5f"
RAID_DENS_FILE="cobblemonraiddens-fabric-0.8.1+1.21.1.jar"

ensure_mod "GeckoLib" "${GECKOLIB_URL}" "${GECKOLIB_SHA256}" "${GECKOLIB_FILE}"
ensure_mod "Cobblemon Raid Dens" "${RAID_DENS_URL}" "${RAID_DENS_SHA256}" "${RAID_DENS_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
