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

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

BACKUP_KEEP_LOCAL="${BACKUP_KEEP_LOCAL:-0}"

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

prune_local_archives() {
  if ! [[ "${BACKUP_KEEP_LOCAL}" =~ ^[0-9]+$ ]]; then
    echo "Invalid BACKUP_KEEP_LOCAL: ${BACKUP_KEEP_LOCAL}" >&2
    exit 2
  fi

  if [[ "${BACKUP_KEEP_LOCAL}" -le 0 ]]; then
    return 0
  fi

  mapfile -t archives < <(ls -1t "${BACKUP_DIR}"/backup-*.tar.gz 2>/dev/null || true)
  if (( ${#archives[@]} <= BACKUP_KEEP_LOCAL )); then
    return 0
  fi

  for archive in "${archives[@]:BACKUP_KEEP_LOCAL}"; do
    rm -f "${archive}"
  done
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
prune_local_archives

echo "Backup created: ${ARCHIVE_PATH}"
