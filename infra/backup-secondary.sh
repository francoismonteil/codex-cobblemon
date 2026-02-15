#!/usr/bin/env bash
set -euo pipefail

# Copies the most recent backup archive to a secondary disk/location.
#
# Env (.env):
# - SECONDARY_BACKUP_DIR: required to enable (example: /mnt/backup2/minecraft-backups)
# - SECONDARY_BACKUP_KEEP: optional, number of archives to keep (default: 30)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${REPO_ROOT}/backups"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

SECONDARY_BACKUP_DIR="${SECONDARY_BACKUP_DIR:-}"
SECONDARY_BACKUP_KEEP="${SECONDARY_BACKUP_KEEP:-30}"

if [[ -z "${SECONDARY_BACKUP_DIR}" ]]; then
  echo "Secondary backup not configured (set SECONDARY_BACKUP_DIR in .env)"
  exit 0
fi

latest="$(ls -1t "${BACKUP_DIR}"/backup-*.tar.gz 2>/dev/null | head -n 1 || true)"
if [[ -z "${latest}" ]]; then
  echo "No backup archives found in ${BACKUP_DIR}"
  exit 0
fi

mkdir -p "${SECONDARY_BACKUP_DIR}"

dest="${SECONDARY_BACKUP_DIR}/$(basename "${latest}")"
tmp="${dest}.partial"

cp -f "${latest}" "${tmp}"
mv -f "${tmp}" "${dest}"

# Prune older archives, keep the most recent N.
if [[ "${SECONDARY_BACKUP_KEEP}" =~ ^[0-9]+$ ]] && [[ "${SECONDARY_BACKUP_KEEP}" -gt 0 ]]; then
  ls -1t "${SECONDARY_BACKUP_DIR}"/backup-*.tar.gz 2>/dev/null | tail -n "+$((SECONDARY_BACKUP_KEEP + 1))" | xargs -r rm -f
fi

echo "Copied: ${latest} -> ${dest}"

