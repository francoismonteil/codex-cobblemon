#!/usr/bin/env bash
set -euo pipefail

# Checks the cumulative progressive rollout pack for the Fabric Cobblemon server.
#
# Usage:
#   ./infra/mods-check-progressive.sh --through-lot 1
#   ./infra/mods-check-progressive.sh --through-lot 5 --mods-dir ./data/mods

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY_SCRIPT="${REPO_ROOT}/tools/check_recommended_server_mods.py"

if [[ ! -f "${PY_SCRIPT}" ]]; then
  echo "Missing script: ${PY_SCRIPT}" >&2
  exit 1
fi

through_lot=""
mods_dir=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --through-lot)
      through_lot="${2:-}"
      shift 2
      ;;
    --mods-dir)
      mods_dir="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: ./infra/mods-check-progressive.sh --through-lot <1..5> [--mods-dir <path>]" >&2
      exit 1
      ;;
  esac
done

if [[ -z "${through_lot}" ]]; then
  echo "Missing required argument: --through-lot <1..5>" >&2
  exit 1
fi

case "${through_lot}" in
  1|2|3|4|5) ;;
  *)
    echo "Invalid lot number: ${through_lot} (expected 1..5)" >&2
    exit 1
    ;;
esac

scripts=(
  "infra/mods-install-openworld.sh"
  "infra/mods-install-waystones.sh"
  "infra/mods-install-better-qol.sh"
  "infra/mods-install-storage.sh"
)

lot_scripts=(
  "infra/mods-install-progressive-lot1-macaws-furniture.sh"
  "infra/mods-install-progressive-lot2-handcrafted.sh"
  "infra/mods-install-progressive-lot3-supplementaries.sh"
  "infra/mods-install-progressive-lot4-yungs-strongholds.sh"
  "infra/mods-install-progressive-lot5-towns-and-towers.sh"
)

for ((i = 0; i < through_lot; i++)); do
  scripts+=("${lot_scripts[$i]}")
done

args=(
  "--write"
  "--out" "${REPO_ROOT}/audit/progressive-server-mods-check-lot${through_lot}.json"
)

if [[ -n "${mods_dir}" ]]; then
  args+=("--mods-dir" "${mods_dir}")
fi

for script in "${scripts[@]}"; do
  args+=("--script" "${script}")
done

if command -v python3 >/dev/null 2>&1; then
  python3 "${PY_SCRIPT}" "${args[@]}"
  exit $?
fi
if command -v py >/dev/null 2>&1; then
  py -3 "${PY_SCRIPT}" "${args[@]}"
  exit $?
fi

echo "Missing Python runtime (need 'python3' or 'py')." >&2
exit 1
