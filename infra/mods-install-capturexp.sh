#!/usr/bin/env bash
set -euo pipefail

# Installs Cobblemon Capture XP + Cobblemon Tim Core for the Fabric Cobblemon server.
#
# Notes:
# - Both mods are server-only according to their Modrinth metadata.
# - Versions are intentionally pinned to known-good builds for MC 1.21.1 / Cobblemon 1.7.3.
# - Optional config: set CAPTUREXP_MULTIPLIER=<value> to write ./data/config/capture_xp.json5.
#
# Usage:
#   ./infra/mods-install-capturexp.sh
#   CAPTUREXP_MULTIPLIER=1.5 ./infra/mods-install-capturexp.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

DATA_DIR="./data"
MODS_DIR="${DATA_DIR}/mods"
CONFIG_FILE="${DATA_DIR}/config/capture_xp.json5"
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

# Cobblemon Tim Core 1.7.3-fabric-1.31.0 (Modrinth version yPG8odLw)
TIMCORE_URL="https://cdn.modrinth.com/data/lVP9aUaY/versions/yPG8odLw/timcore-fabric-1.7.3-1.31.0.jar"
TIMCORE_SHA256="95c14e7ea6f64abd89e145d23f2d2b55fbc9d1c1c93d5233655d79bf9891b02b"
TIMCORE_FILE="timcore-fabric-1.7.3-1.31.0.jar"

# Cobblemon Capture XP 1.7.3-fabric-1.3.0 (Modrinth version hjQp9Aq3)
CAPTUREXP_URL="https://cdn.modrinth.com/data/LBl4Qguc/versions/hjQp9Aq3/capturexp-fabric-1.7.3-1.3.0.jar"
CAPTUREXP_SHA256="8f5ab9ce3ea2957f75033f3adc8a6195d303a96c3a8c1eebd1d5ee254bf88cf7"
CAPTUREXP_FILE="capturexp-fabric-1.7.3-1.3.0.jar"

ensure_mod "Cobblemon Tim Core" "${TIMCORE_URL}" "${TIMCORE_SHA256}" "${TIMCORE_FILE}"
ensure_mod "Cobblemon Capture XP" "${CAPTUREXP_URL}" "${CAPTUREXP_SHA256}" "${CAPTUREXP_FILE}"

if [[ -n "${CAPTUREXP_MULTIPLIER:-}" ]]; then
  bash "${REPO_ROOT}/infra/capturexp-configure.sh" "${CAPTUREXP_MULTIPLIER}"
elif [[ ! -f "${CONFIG_FILE}" ]]; then
  bash "${REPO_ROOT}/infra/capturexp-configure.sh" "1.0"
else
  echo "OK preserving existing Capture XP config: ${CONFIG_FILE}"
fi

echo "Done. Restart the server after installation (prefer ./infra/safe-restart.sh or stop/start)."
