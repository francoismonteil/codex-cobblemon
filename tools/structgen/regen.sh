#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

out="datapacks/acm_pokemon_worldgen/data/acm/structure"
if [[ -n "${PYTHON_BIN:-}" ]]; then
  py_cmd=("${PYTHON_BIN}")
elif command -v python3 >/dev/null 2>&1; then
  py_cmd=("python3")
elif command -v py >/dev/null 2>&1; then
  py_cmd=("py" "-3")
else
  echo "Missing Python interpreter (python3 or py -3)." >&2
  exit 2
fi

"${py_cmd[@]}" tools/structgen/compile.py \
  --out "${out}" \
  --include-entities \
  "$@"

echo "OK: regenerated structures under ${out}"
