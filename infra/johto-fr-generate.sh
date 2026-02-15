#!/usr/bin/env bash
set -euo pipefail

# Generates a partial French translation datapack for Cobblemon Johto.
#
# Scope:
# - All Cobblemon dialogue json files from the Johto datapack (auto translation).
# - Optionally translate tellraw JSON blobs in mcfunctions (off by default).
#
# This avoids editing the original CobblemonJohto.zip and can be extended over time.
#
# Usage (on server):
#   ./infra/johto-fr-generate.sh
#
# Optional env:
#   JOHTO_ZIP=/path/to/CobblemonJohto.zip
#   JOHTO_FRPACK_DIR=/data/world/datapacks/JohtoFR
#   JOHTO_RELOAD=true|false (default true)
#   JOHTO_FR_INCLUDE_TELLRAW=true|false (default false)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

JOHTO_ZIP="${JOHTO_ZIP:-./data/world/datapacks/CobblemonJohto.zip}"
JOHTO_FRPACK_DIR="${JOHTO_FRPACK_DIR:-./data/world/datapacks/JohtoFR}"
JOHTO_RELOAD="${JOHTO_RELOAD:-true}"
JOHTO_FR_INCLUDE_TELLRAW="${JOHTO_FR_INCLUDE_TELLRAW:-false}"
JOHTO_DOCKER_IMAGE="${JOHTO_DOCKER_IMAGE:-python:3.12}"

if [[ ! -f "${JOHTO_ZIP}" ]]; then
  echo "Missing Johto datapack zip: ${JOHTO_ZIP}" >&2
  exit 1
fi

rm -rf "${JOHTO_FRPACK_DIR}"
mkdir -p "${JOHTO_FRPACK_DIR}"

./infra/johto-fr-install.sh

args=(--johto-zip "${JOHTO_ZIP}" --out-dir "${JOHTO_FRPACK_DIR}" --johto-fixes-dir "./data/world/datapacks/JohtoFixes")
if [[ "${JOHTO_FR_INCLUDE_TELLRAW}" == "true" ]]; then
  args+=(--include-mcfunction-tellraw)
fi

mkdir -p "./downloads/pip-cache"

# Run translation inside a disposable container to avoid requiring python3-venv/pip on the host.
docker run --rm \
  -v "${REPO_ROOT}:/work" \
  -v "${REPO_ROOT}/downloads/pip-cache:/root/.cache/pip" \
  -w /work \
  "${JOHTO_DOCKER_IMAGE}" \
  bash -lc "export PIP_DISABLE_PIP_VERSION_CHECK=1; python -m pip install 'argostranslate==1.9.6' && python - <<'PY'
from argostranslate import package
import os, sys
path = '/work/downloads/argos/translate-en_fr.argosmodel'
if not os.path.exists(path):
    print('missing model:', path, file=sys.stderr)
    sys.exit(1)
installed = package.get_installed_packages()
for p in installed:
    if getattr(p, 'from_code', None) == 'en' and getattr(p, 'to_code', None) == 'fr':
        break
else:
    package.install_from_path(path)
PY
python /work/infra/johto-fr-generate.py ${args[*]}"

# Translation files are created by root inside the container; make them writable for the server user.
chown -R "$(id -u):$(id -g)" "${JOHTO_FRPACK_DIR}" || true

if [[ "${JOHTO_RELOAD}" == "true" ]]; then
  ./infra/mc.sh "reload" || true
fi

echo "Generated: ${JOHTO_FRPACK_DIR}"
