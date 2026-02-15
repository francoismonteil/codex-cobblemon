#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || -z "${1:-}" ]]; then
  echo "Usage: ./infra/restore.sh <archive-path>"
  exit 1
fi

ARCHIVE_INPUT="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${REPO_ROOT}/data"
BACKUP_DIR="${REPO_ROOT}/backups"
RESTORE_ROOT="${BACKUP_DIR}/_restore"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
EXTRACT_DIR="${RESTORE_ROOT}/${TIMESTAMP}"

if [[ -f "${ARCHIVE_INPUT}" ]]; then
  ARCHIVE_PATH="${ARCHIVE_INPUT}"
elif [[ -f "${BACKUP_DIR}/${ARCHIVE_INPUT}" ]]; then
  ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_INPUT}"
else
  echo "Archive not found: ${ARCHIVE_INPUT}"
  exit 1
fi

mkdir -p "${EXTRACT_DIR}"
tar -xzf "${ARCHIVE_PATH}" -C "${EXTRACT_DIR}"

MANIFEST_PATH="${EXTRACT_DIR}/manifest.sha256"
if [[ -f "${MANIFEST_PATH}" ]]; then
  (
    cd "${EXTRACT_DIR}"
    sha256sum -c manifest.sha256
  )
else
  echo "Manifest not found, skipping hash verification."
fi

mkdir -p "${DATA_DIR}"
while IFS= read -r -d '' item; do
  name="$(basename "${item}")"
  if [[ "${name}" == "manifest.sha256" ]]; then
    continue
  fi
  cp -a "${item}" "${DATA_DIR}/"
done < <(find "${EXTRACT_DIR}" -mindepth 1 -maxdepth 1 -print0)

rm -rf "${EXTRACT_DIR}"
echo "Restore completed from: ${ARCHIVE_PATH}"
