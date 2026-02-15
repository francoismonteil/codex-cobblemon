#!/usr/bin/env bash
set -euo pipefail

# Removes a player from the server access list.
#
# Usage:
#   ./infra/kickoff.sh <Pseudo>
#
# What it does:
# - kick (best-effort)
# - deop (best-effort)
# - remove from whitelist

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <Pseudo>" >&2
  exit 2
fi

name="$1"

./infra/mc.sh "kick ${name} Removed from server access list." || true
./infra/mc.sh "deop ${name}" || true
./infra/mc.sh "whitelist remove ${name}"
./infra/mc.sh "say [ACCESS] ${name} removed from whitelist."

