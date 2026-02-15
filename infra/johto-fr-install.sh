#!/usr/bin/env bash
set -euo pipefail

# Downloads the offline EN->FR translation model (Argos).
#
# We don't rely on apt/sudo; translation is executed in a disposable python Docker container
# by `infra/johto-fr-generate.sh`.
#
# Usage (on server):
#   ./infra/johto-fr-install.sh
#
# Result:
# - model cache: ./downloads/argos/translate-en_fr.argosmodel

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

MODEL_DIR="${REPO_ROOT}/downloads/argos"
MODEL_PATH="${MODEL_DIR}/translate-en_fr.argosmodel"

mkdir -p "${MODEL_DIR}"

if [[ ! -f "${MODEL_PATH}" ]]; then
  # HuggingFace mirror of Argos model package.
  url="https://huggingface.co/shethjenil/argostranslate/resolve/main/translate-en_fr.argosmodel?download=true"
  curl -fL --retry 3 --retry-delay 2 -o "${MODEL_PATH}" "${url}"
fi
echo "OK: Model downloaded: ${MODEL_PATH}"
