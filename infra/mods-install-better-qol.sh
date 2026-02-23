#!/usr/bin/env bash
set -euo pipefail

# Installs a "Better Minecraft-like" QoL stack for the Fabric Cobblemon server.
#
# Included mods (server side):
# - spark (profiling / diagnostics)
# - Cardinal Components API (required dependency for Traveler's Backpack)
# - Traveler's Backpack (adventure backpack gameplay)
# - FallingTree (timber QoL)
# - You're in Grave Danger (YIGD) (gravestones / death recovery)
#
# Notes:
# - Traveler's Backpack and YIGD must also be installed on clients.
# - FallingTree is typically server-compatible; client install is optional/recommended for UX parity.
# - Versions are intentionally pinned for MC 1.21.1 / Fabric.
#
# Usage:
#   ./infra/mods-install-better-qol.sh

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

# spark 1.10.109 (Fabric 1.21.1) (Modrinth version cALUj9l1)
SPARK_URL="https://cdn.modrinth.com/data/l6YH9Als/versions/cALUj9l1/spark-1.10.109-fabric.jar"
SPARK_SHA256="fafc121ac53dab1c32e74b7a1cae47d54435ba4cbeeda1180dc96675a7757047"
SPARK_FILE="spark-1.10.109-fabric.jar"

# Cardinal Components API 6.1.3 (Fabric 1.21.1) (Modrinth version nLsCe2VD)
# Required by Traveler's Backpack.
CCA_URL="https://cdn.modrinth.com/data/K01OU20C/versions/nLsCe2VD/cardinal-components-api-6.1.3.jar"
CCA_SHA256="302a8a4bc2e34cbffaf61af75ab5de47c06bfa159436665870ae61092b0f69a2"
CCA_FILE="cardinal-components-api-6.1.3.jar"

# Traveler's Backpack 10.1.33 for MC 1.21.1 (Fabric) (Modrinth version i6cd1S6S)
TB_URL="https://cdn.modrinth.com/data/rlloIFEV/versions/i6cd1S6S/travelersbackpack-fabric-1.21.1-10.1.33.jar"
TB_SHA256="656d8d85ad703c044519dc4ab551a56e6f401e892a5fe528aee90a475c822b05"
TB_FILE="travelersbackpack-fabric-1.21.1-10.1.33.jar"

# FallingTree 1.21.1-1.21.1.11 (Modrinth version wxGXaJMA)
FALLINGTREE_URL="https://cdn.modrinth.com/data/Fb4jn8m6/versions/wxGXaJMA/FallingTree-1.21.1-1.21.1.11.jar"
FALLINGTREE_SHA256="b07cb3fe67d1f3bb66daf8836373614153790cfaa8c64fadbf53479d1b33cc54"
FALLINGTREE_FILE="FallingTree-1.21.1-1.21.1.11.jar"

# You're in Grave Danger (YIGD) 2.4.18 (Fabric) (Modrinth version T3grMjgj)
YIGD_URL="https://cdn.modrinth.com/data/HnD1GX6e/versions/T3grMjgj/youre-in-grave-danger-fabric-2.4.18.jar"
YIGD_SHA256="4ae15574b52062f1cb3524138cde0a8e2fe537061186a9e31c0847b423aafbf9"
YIGD_FILE="youre-in-grave-danger-fabric-2.4.18.jar"

# Install dependency before the backpack mod.
ensure_mod "spark" "${SPARK_URL}" "${SPARK_SHA256}" "${SPARK_FILE}"
ensure_mod "Cardinal Components API" "${CCA_URL}" "${CCA_SHA256}" "${CCA_FILE}"
ensure_mod "Traveler's Backpack" "${TB_URL}" "${TB_SHA256}" "${TB_FILE}"
ensure_mod "FallingTree" "${FALLINGTREE_URL}" "${FALLINGTREE_SHA256}" "${FALLINGTREE_FILE}"
ensure_mod "YIGD" "${YIGD_URL}" "${YIGD_SHA256}" "${YIGD_FILE}"

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
