#!/usr/bin/env bash
set -euo pipefail

# One-command rebuild of the whole spawn city.
#
# Usage:
#   ./infra/spawn-city.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./infra/build-modern-spawn.sh
./infra/spawn-shop.sh
./infra/spawn-gym.sh
./infra/spawn-signage.sh

./infra/mc.sh "say [SPAWN] City rebuild complete."

