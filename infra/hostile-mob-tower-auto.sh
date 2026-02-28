#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

world="./data/world"
min_distance="768"
max_distance="2048"
floors="3"
profile="balanced"
dry_run="false"
json_stdout="false"
DRY_RUN_PY="False"

usage() {
  cat <<EOF
Usage:
  $0 [--min-distance <int>] [--max-distance <int>] [--floors <int>]
     [--profile balanced] [--dry-run] [--json]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --min-distance)
      min_distance="${2:?}"
      shift 2
      ;;
    --max-distance)
      max_distance="${2:?}"
      shift 2
      ;;
    --floors)
      floors="${2:?}"
      shift 2
      ;;
    --profile)
      profile="${2:?}"
      shift 2
      ;;
    --dry-run)
      dry_run="true"
      DRY_RUN_PY="True"
      shift
      ;;
    --json)
      json_stdout="true"
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

for v in "${min_distance}" "${max_distance}" "${floors}"; do
  if ! [[ "${v}" =~ ^[0-9]+$ ]]; then
    echo "Invalid integer argument: ${v}" >&2
    exit 2
  fi
done

if (( min_distance <= 0 || max_distance < min_distance )); then
  echo "Invalid distance range: min=${min_distance} max=${max_distance}" >&2
  exit 2
fi
if (( floors < 1 || floors > 5 )); then
  echo "Invalid --floors (expected 1..5): ${floors}" >&2
  exit 2
fi
if [[ "${profile}" != "balanced" ]]; then
  echo "Unsupported --profile: ${profile}" >&2
  exit 2
fi

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
STARTED_AT="$(date -Iseconds)"
MANIFEST_DIR="${REPO_ROOT}/logs/build-manifests"
MANIFEST_PATH="${MANIFEST_DIR}/hostile-mob-tower-${TIMESTAMP}.json"
TMP_DIR="$(mktemp -d)"
SITE_JSON="${TMP_DIR}/site.json"
BUILD_JSON="${TMP_DIR}/build.json"
VALIDATION_JSON="${TMP_DIR}/validation.json"
CLEAN_JSON="${TMP_DIR}/cleanup.json"
CLEAN_VALIDATE_JSON="${TMP_DIR}/cleanup-validation.json"

SITE_STATUS="not_run"
BACKUP_STATUS="skipped"
BACKUP_ARCHIVE=""
BUILD_STATUS="skipped"
VALIDATION_STATUS="skipped"
ROLLBACK_ACTION="none"
ROLLBACK_STATUS="not_needed"
FINAL_EXIT=1
FORCELOAD_ADDED="false"
SITE_BLOCK_BOUNDS=""

cleanup() {
  if [[ "${FORCELOAD_ADDED}" == "true" && -n "${SITE_BLOCK_BOUNDS}" ]]; then
    read -r FX1 FZ1 FX2 FZ2 <<<"${SITE_BLOCK_BOUNDS}"
    ./infra/mc.sh "forceload remove ${FX1} ${FZ1} ${FX2} ${FZ2}" >/dev/null 2>&1 || true
  fi
  rm -rf "${TMP_DIR}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

get_players_online() {
  if ! docker inspect cobblemon >/dev/null 2>&1; then
    echo ""
    return 0
  fi
  if ! docker inspect cobblemon --format '{{.State.Running}}' 2>/dev/null | grep -qi true; then
    echo ""
    return 0
  fi
  ./infra/mc.sh list >/dev/null 2>&1 || true
  local line
  line="$(docker logs cobblemon --tail 200 2>/dev/null | grep -E 'There are [0-9]+ of a max' | tail -n 1 || true)"
  echo "${line}" | sed -nE 's/.*There are ([0-9]+) of a max.*/\1/p'
}

wait_healthy() {
  local max_secs="${1:-120}"
  local interval="2"
  local max_iters=$(( max_secs / interval ))
  local ok="false"
  for _ in $(seq 1 "${max_iters}"); do
    if docker inspect cobblemon --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null | grep -qi '^running healthy$'; then
      ok="true"
      break
    fi
    sleep "${interval}"
  done
  [[ "${ok}" == "true" ]]
}

write_manifest() {
  mkdir -p "${MANIFEST_DIR}"
  MANIFEST_PATH_ENV="${MANIFEST_PATH}" \
  SITE_JSON_ENV="${SITE_JSON}" \
  BUILD_JSON_ENV="${BUILD_JSON}" \
  VALIDATION_JSON_ENV="${VALIDATION_JSON}" \
  CLEAN_JSON_ENV="${CLEAN_JSON}" \
  CLEAN_VALIDATE_JSON_ENV="${CLEAN_VALIDATE_JSON}" \
  python3 - <<PY
import json
import os
from pathlib import Path

def load(path):
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

site = load(os.environ["SITE_JSON_ENV"])
build = load(os.environ["BUILD_JSON_ENV"])
validation = load(os.environ["VALIDATION_JSON_ENV"])
cleanup = load(os.environ["CLEAN_JSON_ENV"])
cleanup_validation = load(os.environ["CLEAN_VALIDATE_JSON_ENV"])

payload = {
    "schema_version": 1,
    "kind": "hostile_mob_tower",
    "started_at": "${STARTED_AT}",
    "finished_at": "$(date -Iseconds)",
    "world_path": "${world}",
    "inputs": {
        "min_distance": int("${min_distance}"),
        "max_distance": int("${max_distance}"),
        "floors": int("${floors}"),
        "profile": "${profile}",
        "dry_run": ${DRY_RUN_PY},
    },
    "selection": {
        "status": "${SITE_STATUS}",
    },
    "spawn": (site or {}).get("spawn"),
    "site": (site or {}).get("site"),
    "backup": {
        "archive": "${BACKUP_ARCHIVE}",
        "status": "${BACKUP_STATUS}",
    },
    "build": {
        "status": "${BUILD_STATUS}",
        "details": build,
    },
    "validation": {
        "status": "${VALIDATION_STATUS}",
        "checks": validation.get("checks") if validation else {},
        "findings": validation.get("findings") if validation else [],
    },
    "rollback": {
        "action": "${ROLLBACK_ACTION}",
        "status": "${ROLLBACK_STATUS}",
        "cleanup": cleanup,
        "cleanup_validation": cleanup_validation,
    },
}
path = Path(os.environ["MANIFEST_PATH_ENV"])
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
PY
}

if ! docker inspect cobblemon --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null | grep -qi '^running healthy$'; then
  echo "Minecraft service is not healthy." >&2
  write_manifest
  exit 1
fi

site_rc=0
python3 ./infra/find-hostile-mob-tower-site.py \
  --world "${world}" \
  --min-distance "${min_distance}" \
  --max-distance "${max_distance}" \
  --floors "${floors}" \
  --json-out "${SITE_JSON}" >/dev/null || site_rc=$?
if [[ "${site_rc}" -ne 0 ]]; then
  SITE_STATUS="failed"
  write_manifest
  exit 1
fi
SITE_STATUS="ok"

read -r ORIGIN_X ORIGIN_Y ORIGIN_Z BBOX_X1 BBOX_Z1 BBOX_X2 BBOX_Z2 <<<"$(python3 - <<PY
import json
from pathlib import Path
d = json.loads(Path("${SITE_JSON}").read_text(encoding="utf-8"))
o = d["site"]["origin"]
b = d["site"]["bbox"]
print(o["x"], o["y"], o["z"], b["x1"], b["z1"], b["x2"], b["z2"])
PY
)"
SITE_BLOCK_BOUNDS="${BBOX_X1} ${BBOX_Z1} ${BBOX_X2} ${BBOX_Z2}"

if [[ "${dry_run}" == "true" ]]; then
  VALIDATION_STATUS="dry_run"
  FINAL_EXIT=0
  write_manifest
  if [[ "${json_stdout}" == "true" ]]; then
    cat "${MANIFEST_PATH}"
  else
    echo "Manifest written: ${MANIFEST_PATH}"
  fi
  exit 0
fi

./infra/mc.sh "forceload add ${BBOX_X1} ${BBOX_Z1} ${BBOX_X2} ${BBOX_Z2}" >/dev/null
FORCELOAD_ADDED="true"

backup_output=""
if ! backup_output="$(./infra/backup.sh)"; then
  BACKUP_STATUS="failed"
  write_manifest
  exit 1
fi
BACKUP_ARCHIVE="$(echo "${backup_output}" | sed -nE 's/^Backup created: (.*)$/\1/p' | tail -n 1)"
if [[ -z "${BACKUP_ARCHIVE}" ]]; then
  BACKUP_STATUS="failed"
  write_manifest
  exit 1
fi
BACKUP_STATUS="ok"

build_rc=0
./infra/spawn-hostile-mob-tower.sh --at "${ORIGIN_X}" "${ORIGIN_Y}" "${ORIGIN_Z}" --dx 0 --dy 0 --dz 0 --floors "${floors}" --json-out "${BUILD_JSON}" || build_rc=$?
if [[ "${build_rc}" -eq 0 ]]; then
  BUILD_STATUS="ok"
else
  BUILD_STATUS="failed"
fi

./infra/mc.sh "save-all flush" >/dev/null 2>&1 || true
sleep 2

validation_rc=0
python3 ./infra/validate-hostile-mob-tower.py --world "${world}" --at "${ORIGIN_X}" "${ORIGIN_Y}" "${ORIGIN_Z}" --floors "${floors}" --json-out "${VALIDATION_JSON}" || validation_rc=$?
if [[ "${build_rc}" -eq 0 && "${validation_rc}" -eq 0 ]]; then
  VALIDATION_STATUS="pass"
  FINAL_EXIT=0
  write_manifest
  if [[ "${json_stdout}" == "true" ]]; then
    cat "${MANIFEST_PATH}"
  else
    echo "Manifest written: ${MANIFEST_PATH}"
  fi
  exit 0
fi

VALIDATION_STATUS="fail"
ROLLBACK_ACTION="cleanup_only"
ROLLBACK_STATUS="running"

cleanup_rc=0
./infra/clear-hostile-mob-tower.sh --at "${ORIGIN_X}" "${ORIGIN_Y}" "${ORIGIN_Z}" --dx 0 --dy 0 --dz 0 --floors "${floors}" --json-out "${CLEAN_JSON}" || cleanup_rc=$?
./infra/mc.sh "save-all flush" >/dev/null 2>&1 || true
sleep 2

cleanup_validate_rc=0
python3 ./infra/validate-hostile-mob-tower.py --world "${world}" --mode cleared --at "${ORIGIN_X}" "${ORIGIN_Y}" "${ORIGIN_Z}" --floors "${floors}" --json-out "${CLEAN_VALIDATE_JSON}" || cleanup_validate_rc=$?
if [[ "${cleanup_rc}" -eq 0 && "${cleanup_validate_rc}" -eq 0 ]]; then
  ROLLBACK_STATUS="ok"
  FINAL_EXIT=1
  write_manifest
  if [[ "${json_stdout}" == "true" ]]; then
    cat "${MANIFEST_PATH}"
  else
    echo "Manifest written: ${MANIFEST_PATH}"
  fi
  exit 1
fi

ROLLBACK_ACTION="full_restore"
ROLLBACK_STATUS="running"
players_online="$(get_players_online || true)"
if [[ -n "${players_online}" && "${players_online}" != "0" ]]; then
  ./infra/mc.sh "say [SPAWN] Rollback hostile tower: restauration depuis backup en cours." >/dev/null 2>&1 || true
fi

FORCELOAD_ADDED="false"
if ! ./infra/stop.sh >/dev/null; then
  ROLLBACK_STATUS="stop_failed"
  write_manifest
  exit 1
fi
if ! ./infra/restore.sh "${BACKUP_ARCHIVE}" >/dev/null; then
  ROLLBACK_STATUS="restore_failed"
  write_manifest
  exit 1
fi
if ! ./infra/start.sh >/dev/null; then
  ROLLBACK_STATUS="start_failed"
  write_manifest
  exit 1
fi
if wait_healthy 120; then
  ROLLBACK_STATUS="ok"
else
  ROLLBACK_STATUS="restore_failed"
fi

write_manifest
if [[ "${json_stdout}" == "true" ]]; then
  cat "${MANIFEST_PATH}"
else
  echo "Manifest written: ${MANIFEST_PATH}"
fi
exit 1
