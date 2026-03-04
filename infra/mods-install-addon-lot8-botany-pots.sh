#!/usr/bin/env bash
set -euo pipefail

# Installs addon rollout lot 8 for the Fabric Cobblemon server:
# - Architectury API
# - Bookshelf
# - Prickle
# - Botany Pots
# - Cobblemon Botany Pots
#
# Notes:
# - All jars are required together for the supported Fabric 1.21.1 stack.
# - Keep this as a single lot because the Cobblemon integration depends on the
#   Botany Pots stack being present and version-aligned.
#
# Usage:
#   ./infra/mods-install-addon-lot8-botany-pots.sh

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

# Architectury API 13.0.8 for MC 1.21.1 Fabric (Modrinth version Wto0RchG)
ARCHITECTURY_URL="https://cdn.modrinth.com/data/lhGA9TYQ/versions/Wto0RchG/architectury-13.0.8-fabric.jar"
ARCHITECTURY_SHA256="10cbbb6f5f96a2f1853b0cc68428424cec8903409517b299ff02350756b6399d"
ARCHITECTURY_FILE="architectury-13.0.8-fabric.jar"

# Bookshelf 21.1.81 for MC 1.21.1 Fabric (Modrinth version kpkjWpa5)
BOOKSHELF_URL="https://cdn.modrinth.com/data/uy4Cnpcm/versions/kpkjWpa5/bookshelf-fabric-1.21.1-21.1.81.jar"
BOOKSHELF_SHA256="df2dd3a3e75f2dbf56baf9bdb6cc0007f9c0efb0f2b2067f047ddf98ea1b49d8"
BOOKSHELF_FILE="bookshelf-fabric-1.21.1-21.1.81.jar"

# Prickle 21.1.11 for MC 1.21.1 Fabric (Modrinth version Ef7P6Rb7)
PRICKLE_URL="https://cdn.modrinth.com/data/aaRl8GiW/versions/Ef7P6Rb7/prickle-fabric-1.21.1-21.1.11.jar"
PRICKLE_SHA256="d6d639078aecb72770f287d8253e4634114e2536ac9a2ad6ec5f442eb27dd07f"
PRICKLE_FILE="prickle-fabric-1.21.1-21.1.11.jar"

# Botany Pots 21.1.41 for MC 1.21.1 Fabric (Modrinth version Bz6dkTjV)
BOTANY_POTS_URL="https://cdn.modrinth.com/data/U6BUTZ7K/versions/Bz6dkTjV/botanypots-fabric-1.21.1-21.1.41.jar"
BOTANY_POTS_SHA256="14dd5d079030e2b6dfda629a8c48255c82c55ba01e15e15810b1aaaf30110bc4"
BOTANY_POTS_FILE="botanypots-fabric-1.21.1-21.1.41.jar"

# Cobblemon Botany Pots 1.0.1 for MC 1.21.1 Fabric (CurseForge file 7074619)
COBBLEMON_BOTANY_POTS_URL="https://mediafilez.forgecdn.net/files/7074/619/cobblemon_pots-fabric-1.0.1.jar"
COBBLEMON_BOTANY_POTS_SHA256="38884fdf8d968b54c258f15a37316e3d04a35f83a267d4bde3b964d8f1ba076b"
COBBLEMON_BOTANY_POTS_FILE="cobblemon_pots-fabric-1.0.1.jar"

ensure_mod "Architectury API" "${ARCHITECTURY_URL}" "${ARCHITECTURY_SHA256}" "${ARCHITECTURY_FILE}"
ensure_mod "Bookshelf" "${BOOKSHELF_URL}" "${BOOKSHELF_SHA256}" "${BOOKSHELF_FILE}"
ensure_mod "Prickle" "${PRICKLE_URL}" "${PRICKLE_SHA256}" "${PRICKLE_FILE}"
ensure_mod "Botany Pots" "${BOTANY_POTS_URL}" "${BOTANY_POTS_SHA256}" "${BOTANY_POTS_FILE}"
ensure_mod "Cobblemon Botany Pots" "${COBBLEMON_BOTANY_POTS_URL}" "${COBBLEMON_BOTANY_POTS_SHA256}" "${COBBLEMON_BOTANY_POTS_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
