#!/usr/bin/env bash
set -euo pipefail

# Repeats openworld world initialization until a Pokemart marker is detected
# near the spawn village (or max attempts reached).
#
# Why:
# - Pokemart village generation is probabilistic.
# - We want a practical "retry until first village has Pokemart" workflow.
#
# Usage:
#   ./infra/openworld-village-init-until-pokemart.sh
#   ./infra/openworld-village-init-until-pokemart.sh --with-additionalstructures
#   ./infra/openworld-village-init-until-pokemart.sh --max-attempts 6 --radius 256
#   ./infra/openworld-village-init-until-pokemart.sh --min-components 1 --max-components 1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

with_additionalstructures="false"
max_attempts=6
radius=256
settle_seconds=20
min_components=1
max_components=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-additionalstructures)
      with_additionalstructures="true"
      shift
      ;;
    --max-attempts)
      max_attempts="${2:-}"
      shift 2
      ;;
    --radius)
      radius="${2:-}"
      shift 2
      ;;
    --settle-seconds)
      settle_seconds="${2:-}"
      shift 2
      ;;
    --min-components)
      min_components="${2:-}"
      shift 2
      ;;
    --max-components)
      max_components="${2:-}"
      shift 2
      ;;
    -h|--help)
      cat <<EOF
Usage: $0 [--with-additionalstructures] [--max-attempts N] [--radius BLOCKS] [--settle-seconds N] [--min-components N] [--max-components N]

Defaults:
  --max-attempts 6
  --radius 256
  --settle-seconds 20
  --min-components 1
  --max-components 1
EOF
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

if ! [[ "${max_attempts}" =~ ^[0-9]+$ ]] || [[ "${max_attempts}" -lt 1 ]]; then
  echo "Invalid --max-attempts: ${max_attempts}" >&2
  exit 2
fi
if ! [[ "${radius}" =~ ^[0-9]+$ ]] || [[ "${radius}" -lt 32 ]]; then
  echo "Invalid --radius: ${radius} (min 32)" >&2
  exit 2
fi
if ! [[ "${settle_seconds}" =~ ^[0-9]+$ ]] || [[ "${settle_seconds}" -lt 0 ]]; then
  echo "Invalid --settle-seconds: ${settle_seconds}" >&2
  exit 2
fi
if ! [[ "${min_components}" =~ ^[0-9]+$ ]]; then
  echo "Invalid --min-components: ${min_components}" >&2
  exit 2
fi
if ! [[ "${max_components}" =~ ^[0-9]+$ ]]; then
  echo "Invalid --max-components: ${max_components}" >&2
  exit 2
fi
if [[ "${max_components}" -lt "${min_components}" ]]; then
  echo "Invalid component bounds: --max-components must be >= --min-components" >&2
  exit 2
fi

if [[ ! -x "${REPO_ROOT}/infra/openworld-village-init.sh" ]]; then
  echo "Missing executable: ./infra/openworld-village-init.sh" >&2
  exit 2
fi
if [[ ! -f "${REPO_ROOT}/infra/detect-pokemart-near-spawn.py" ]]; then
  echo "Missing detector: ./infra/detect-pokemart-near-spawn.py" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "Missing python3 (required by detect-pokemart-near-spawn.py)" >&2
  exit 2
fi

say() {
  ./infra/mc.sh "say [MAINT] $*" >/dev/null 2>&1 || true
}

for attempt in $(seq 1 "${max_attempts}"); do
  echo "== Attempt ${attempt}/${max_attempts}: init openworld =="
  say "Openworld init attempt ${attempt}/${max_attempts} (Pokemart cluster check enabled)."

  if [[ "${with_additionalstructures}" == "true" ]]; then
    ./infra/openworld-village-init.sh --with-additionalstructures
  else
    ./infra/openworld-village-init.sh
  fi

  if [[ "${settle_seconds}" -gt 0 ]]; then
    echo "== Settle ${settle_seconds}s before detection =="
    sleep "${settle_seconds}"
  fi

  ./infra/mc.sh "save-all flush" >/dev/null 2>&1 || true
  sleep 2

  echo "== Detect Pokemart markers near spawn (radius=${radius}, components=${min_components}..${max_components}) =="
  if python3 ./infra/detect-pokemart-near-spawn.py --world ./data/world --radius "${radius}" --min-components "${min_components}" --max-components "${max_components}"; then
    echo "OK Pokemart marker components in accepted range on attempt ${attempt}/${max_attempts}."
    say "Pokemart cluster count is acceptable near spawn. Keeping this world."
    exit 0
  fi

  echo "WARN: Pokemart marker component count out of accepted range on attempt ${attempt}/${max_attempts}."
  say "Pokemart cluster count not acceptable on attempt ${attempt}. Regenerating world..."
done

echo "ERROR: reached max attempts (${max_attempts}) without accepted Pokemart cluster count near spawn." >&2
say "Max attempts reached without acceptable Pokemart cluster count near spawn. Manual review needed."
exit 1
