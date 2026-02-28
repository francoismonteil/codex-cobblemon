#!/usr/bin/env bash
set -euo pipefail

# Trim world data outside a square centered on the current world spawn.
#
# This script prunes full Anvil files:
# - r.<rx>.<rz>.mca in region/poi/entities when the full file bounds are outside the keep square
# - c.<cx>.<cz>.mcc (external chunk files) when chunk bounds are outside the keep square
#
# Safety defaults:
# - For non-dry runs, refuses to run while server is online unless --stop-server is used.
# - Takes a backup via ./infra/backup.sh unless --skip-backup.
# - Moves pruned files to ./backups/world-trim-pruned-<timestamp>/ unless --delete-pruned.
#
# Usage:
#   ./infra/world-trim-around-spawn.sh
#   ./infra/world-trim-around-spawn.sh --keep-size 2000 --dry-run
#   ./infra/world-trim-around-spawn.sh --keep-size 2000 --stop-server --restart
#   ./infra/world-trim-around-spawn.sh --keep-size 2000 --include-nether --include-end --stop-server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

WORLD_DIR="${REPO_ROOT}/data/world"
KEEP_SIZE=2000
DRY_RUN="false"
STOP_SERVER="false"
RESTART="false"
SKIP_BACKUP="false"
DELETE_PRUNED="false"
INCLUDE_NETHER="false"
INCLUDE_END="false"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
PRUNED_ROOT="${REPO_ROOT}/backups/world-trim-pruned-${TIMESTAMP}"

usage() {
  cat <<'EOF'
Trim world files outside a square centered on spawn.

Usage:
  ./infra/world-trim-around-spawn.sh [options]

Options:
  --keep-size <blocks>   Keep square size in blocks on X/Z (default: 2000).
                         Example: 2000 keeps 2000x2000 blocks around spawn.
  --dry-run              Show what would be pruned, do not modify files.
  --stop-server          Stop server automatically if running (non-dry run).
  --restart              Restart server at end only if this script stopped it.
  --skip-backup          Skip ./infra/backup.sh (non-dry run).
  --delete-pruned        Delete pruned files instead of moving to backups/.
  --include-nether       Also trim ./data/world/DIM-1.
  --include-end          Also trim ./data/world/DIM1.
  -h, --help             Show this help.

Notes:
  - Spawn is read from ./data/world/level.dat via ./infra/world-spawn.sh.
  - region/poi/entities are trimmed together for consistency.
  - Whole-region trimming is coarse by design (region file granularity = 512x512 blocks).
EOF
}

is_pos_int() {
  [[ "$1" =~ ^[0-9]+$ ]] && [[ "$1" -gt 0 ]]
}

container_running() {
  if ! command -v docker >/dev/null 2>&1; then
    return 1
  fi
  if ! docker inspect cobblemon >/dev/null 2>&1; then
    return 1
  fi
  docker inspect cobblemon --format '{{.State.Running}}' 2>/dev/null | grep -qi true
}

intersects_keep_box() {
  local min_x="$1"
  local max_x="$2"
  local min_z="$3"
  local max_z="$4"

  if (( max_x < KEEP_MIN_X || min_x > KEEP_MAX_X || max_z < KEEP_MIN_Z || min_z > KEEP_MAX_Z )); then
    return 1
  fi
  return 0
}

checked_total=0
checked_mca=0
checked_mcc=0
kept_total=0
pruned_total=0
pruned_mca=0
pruned_mcc=0

prune_file() {
  local file_path="$1"
  local rel="$2"
  local kind="$3"

  pruned_total=$((pruned_total + 1))
  if [[ "${kind}" == "mca" ]]; then
    pruned_mca=$((pruned_mca + 1))
  else
    pruned_mcc=$((pruned_mcc + 1))
  fi

  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY] prune ${rel}"
    return 0
  fi

  if [[ "${DELETE_PRUNED}" == "true" ]]; then
    rm -f "${file_path}"
  else
    local dst="${PRUNED_ROOT}/${rel}"
    mkdir -p "$(dirname "${dst}")"
    mv "${file_path}" "${dst}"
  fi
}

process_storage_dir() {
  local storage_dir="$1"
  local rel_prefix="$2"

  if [[ ! -d "${storage_dir}" ]]; then
    return 0
  fi

  local file base rx rz cx cz
  local min_x max_x min_z max_z

  while IFS= read -r -d '' file; do
    base="$(basename "${file}")"
    checked_total=$((checked_total + 1))
    checked_mca=$((checked_mca + 1))

    if [[ "${base}" =~ ^r\.(-?[0-9]+)\.(-?[0-9]+)\.mca$ ]]; then
      rx="${BASH_REMATCH[1]}"
      rz="${BASH_REMATCH[2]}"

      min_x=$((rx * 512))
      max_x=$((min_x + 511))
      min_z=$((rz * 512))
      max_z=$((min_z + 511))

      if intersects_keep_box "${min_x}" "${max_x}" "${min_z}" "${max_z}"; then
        kept_total=$((kept_total + 1))
      else
        prune_file "${file}" "${rel_prefix}/${base}" "mca"
      fi
    else
      kept_total=$((kept_total + 1))
    fi
  done < <(find "${storage_dir}" -maxdepth 1 -type f -name 'r.*.*.mca' -print0)

  while IFS= read -r -d '' file; do
    base="$(basename "${file}")"
    checked_total=$((checked_total + 1))
    checked_mcc=$((checked_mcc + 1))

    if [[ "${base}" =~ ^c\.(-?[0-9]+)\.(-?[0-9]+)\.mcc$ ]]; then
      cx="${BASH_REMATCH[1]}"
      cz="${BASH_REMATCH[2]}"

      min_x=$((cx * 16))
      max_x=$((min_x + 15))
      min_z=$((cz * 16))
      max_z=$((min_z + 15))

      if intersects_keep_box "${min_x}" "${max_x}" "${min_z}" "${max_z}"; then
        kept_total=$((kept_total + 1))
      else
        prune_file "${file}" "${rel_prefix}/${base}" "mcc"
      fi
    else
      kept_total=$((kept_total + 1))
    fi
  done < <(find "${storage_dir}" -maxdepth 1 -type f -name 'c.*.*.mcc' -print0)
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-size)
      KEEP_SIZE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    --stop-server)
      STOP_SERVER="true"
      shift
      ;;
    --restart)
      RESTART="true"
      shift
      ;;
    --skip-backup)
      SKIP_BACKUP="true"
      shift
      ;;
    --delete-pruned)
      DELETE_PRUNED="true"
      shift
      ;;
    --include-nether)
      INCLUDE_NETHER="true"
      shift
      ;;
    --include-end)
      INCLUDE_END="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! is_pos_int "${KEEP_SIZE}"; then
  echo "Invalid --keep-size '${KEEP_SIZE}' (expected integer > 0)." >&2
  exit 2
fi

if [[ ! -d "${WORLD_DIR}" || ! -f "${WORLD_DIR}/level.dat" ]]; then
  echo "Missing world directory or level.dat: ${WORLD_DIR}" >&2
  exit 1
fi

if [[ ! -x "./infra/world-spawn.sh" ]]; then
  echo "Missing executable ./infra/world-spawn.sh" >&2
  exit 1
fi

read -r SPAWN_X SPAWN_Y SPAWN_Z < <(./infra/world-spawn.sh)

half=$((KEEP_SIZE / 2))
KEEP_MIN_X=$((SPAWN_X - half))
KEEP_MIN_Z=$((SPAWN_Z - half))
KEEP_MAX_X=$((KEEP_MIN_X + KEEP_SIZE - 1))
KEEP_MAX_Z=$((KEEP_MIN_Z + KEEP_SIZE - 1))

stopped_by_script="false"
if [[ "${DRY_RUN}" == "false" ]] && container_running; then
  if [[ "${STOP_SERVER}" != "true" ]]; then
    echo "Server is running (container 'cobblemon')." >&2
    echo "Use --stop-server, or stop manually before trimming." >&2
    exit 1
  fi
  echo "== Stop server =="
  ./infra/stop.sh
  stopped_by_script="true"
fi

if [[ "${DRY_RUN}" == "false" && "${SKIP_BACKUP}" != "true" ]]; then
  echo "== Backup =="
  ./infra/backup.sh
fi

if [[ "${DRY_RUN}" == "false" && "${DELETE_PRUNED}" != "true" ]]; then
  mkdir -p "${PRUNED_ROOT}"
fi

echo "== Trim world around spawn =="
echo "spawn: ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"
echo "keep-size: ${KEEP_SIZE}x${KEEP_SIZE}"
echo "keep-box-x: ${KEEP_MIN_X}..${KEEP_MAX_X}"
echo "keep-box-z: ${KEEP_MIN_Z}..${KEEP_MAX_Z}"
if [[ "${DRY_RUN}" == "true" ]]; then
  echo "mode: dry-run"
elif [[ "${DELETE_PRUNED}" == "true" ]]; then
  echo "mode: delete-pruned"
else
  echo "mode: move-pruned -> ${PRUNED_ROOT}"
fi

dim_labels=("overworld")
dim_paths=("${WORLD_DIR}")

if [[ "${INCLUDE_NETHER}" == "true" ]]; then
  dim_labels+=("nether")
  dim_paths+=("${WORLD_DIR}/DIM-1")
fi
if [[ "${INCLUDE_END}" == "true" ]]; then
  dim_labels+=("end")
  dim_paths+=("${WORLD_DIR}/DIM1")
fi

for i in "${!dim_paths[@]}"; do
  dim_label="${dim_labels[$i]}"
  dim_path="${dim_paths[$i]}"

  if [[ ! -d "${dim_path}" ]]; then
    echo "skip missing dimension path: ${dim_path}"
    continue
  fi

  for storage_kind in region poi entities; do
    storage_dir="${dim_path}/${storage_kind}"
    rel_prefix="${dim_label}/${storage_kind}"
    process_storage_dir "${storage_dir}" "${rel_prefix}"
  done
done

echo "== Summary =="
echo "checked_total: ${checked_total}"
echo "checked_mca: ${checked_mca}"
echo "checked_mcc: ${checked_mcc}"
echo "kept_total: ${kept_total}"
echo "pruned_total: ${pruned_total}"
echo "pruned_mca: ${pruned_mca}"
echo "pruned_mcc: ${pruned_mcc}"

if [[ "${DRY_RUN}" == "false" && "${DELETE_PRUNED}" != "true" ]]; then
  echo "pruned_backup: ${PRUNED_ROOT}"
fi

if [[ "${stopped_by_script}" == "true" && "${RESTART}" == "true" ]]; then
  echo "== Restart server =="
  ./infra/start.sh
fi

echo "OK world trim completed."
