#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${REPO_ROOT}/backups"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

BACKUP_KEEP_LOCAL="${BACKUP_KEEP_LOCAL:-0}"
DRY_RUN=0
QUIET=0

usage() {
  cat <<'EOF' >&2
Usage:
  ./infra/backup-prune-local.sh [--keep N] [--dry-run] [--quiet]

Env (.env):
  BACKUP_KEEP_LOCAL=14
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      BACKUP_KEEP_LOCAL="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --quiet)
      QUIET=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

if ! [[ "${BACKUP_KEEP_LOCAL}" =~ ^[0-9]+$ ]]; then
  echo "Invalid BACKUP_KEEP_LOCAL: ${BACKUP_KEEP_LOCAL}" >&2
  exit 2
fi

if [[ "${BACKUP_KEEP_LOCAL}" -le 0 ]]; then
  (( QUIET == 1 )) || echo "Local backup pruning disabled (BACKUP_KEEP_LOCAL=${BACKUP_KEEP_LOCAL})"
  exit 0
fi

mapfile -t archives < <(ls -1t "${BACKUP_DIR}"/backup-*.tar.gz 2>/dev/null || true)
if (( ${#archives[@]} <= BACKUP_KEEP_LOCAL )); then
  (( QUIET == 1 )) || echo "Nothing to prune (${#archives[@]} archive(s), keep=${BACKUP_KEEP_LOCAL})"
  exit 0
fi

prune_count=$(( ${#archives[@]} - BACKUP_KEEP_LOCAL ))
for archive in "${archives[@]:BACKUP_KEEP_LOCAL}"; do
  if (( DRY_RUN == 1 )); then
    (( QUIET == 1 )) || echo "Would prune: ${archive}"
  else
    rm -f "${archive}"
    (( QUIET == 1 )) || echo "Pruned: ${archive}"
  fi
done

if (( QUIET == 0 )); then
  if (( DRY_RUN == 1 )); then
    echo "Dry-run complete: ${prune_count} archive(s) would be pruned"
  else
    echo "Pruned ${prune_count} archive(s); kept ${BACKUP_KEEP_LOCAL}"
  fi
fi
