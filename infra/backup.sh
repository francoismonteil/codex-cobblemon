#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${REPO_ROOT}/data"
BACKUP_DIR="${REPO_ROOT}/backups"
STAGING_ROOT="${BACKUP_DIR}/_staging"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE_NAME="backup-${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"
STAGING_DIR="${STAGING_ROOT}/${TIMESTAMP}"

maybe_flush_world() {
  # Best-effort: ask server to flush world state before copying.
  if ! docker inspect cobblemon >/dev/null 2>&1; then
    return 0
  fi
  if ! docker inspect cobblemon --format '{{.State.Running}}' 2>/dev/null | grep -qi true; then
    return 0
  fi
  # Requires CREATE_CONSOLE_IN_PIPE=true in the container env.
  docker exec -u 1000 cobblemon mc-send-to-console "save-all flush" >/dev/null 2>&1 || true
  sleep 2
}

TARGETS=(
  "world"
  "config"
  "mods"
  "kubejs"
  "server.properties"
  "whitelist.json"
  "ops.json"
  "banned-ips.json"
  "banned-players.json"
  "allowed_symlinks.txt"
)

mkdir -p "${BACKUP_DIR}" "${STAGING_DIR}"

maybe_flush_world

found=0
for target in "${TARGETS[@]}"; do
  src="${DATA_DIR}/${target}"
  if [[ -e "${src}" ]]; then
    cp -a "${src}" "${STAGING_DIR}/"
    found=1
  else
    echo "Skip missing: ${src}"
  fi
done

if [[ "${found}" -eq 0 ]]; then
  rm -rf "${STAGING_DIR}"
  echo "No data found to back up. Skipping."
  exit 0
fi

(
  cd "${STAGING_DIR}"
  find . -type f ! -name "manifest.sha256" -print0 | sort -z | xargs -0 sha256sum > manifest.sha256
)

tar -czf "${ARCHIVE_PATH}" -C "${STAGING_DIR}" .
rm -rf "${STAGING_DIR}"

echo "Backup created: ${ARCHIVE_PATH}"
