#!/usr/bin/env bash
set -euo pipefail

# Quick operational status for the Minecraft stack.
#
# Usage:
#   ./infra/status.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

DUCKDNS_DOMAINS="${DUCKDNS_DOMAINS:-}"
DEFAULT_PLAYER_NAME="${DEFAULT_PLAYER_NAME:-}"

echo "== compose =="
docker compose ps || true

echo "== health =="
docker inspect cobblemon --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo "cobblemon: missing"

echo "== port 25565 =="
ss -ltn '( sport = :25565 )' 2>/dev/null | tail -n +1 || true

echo "== players =="
if docker inspect cobblemon >/dev/null 2>&1; then
  docker exec -u 1000 cobblemon mc-send-to-console "list" >/dev/null 2>&1 || true
  docker logs cobblemon --tail 250 2>/dev/null | grep -E 'There are [0-9]+ of a max' | tail -n 1 || true
fi

echo "== whitelist =="
if docker inspect cobblemon >/dev/null 2>&1; then
  docker exec -u 1000 cobblemon mc-send-to-console "whitelist list" >/dev/null 2>&1 || true
  docker logs cobblemon --tail 250 2>/dev/null | grep -E 'There are [0-9]+ whitelisted player' | tail -n 1 || true
fi

if [[ -n "${DEFAULT_PLAYER_NAME}" ]]; then
  echo "== default player =="
  echo "${DEFAULT_PLAYER_NAME}"
fi

if [[ -n "${DUCKDNS_DOMAINS}" ]]; then
  echo "== ddns =="
  echo "${DUCKDNS_DOMAINS}.duckdns.org"
  getent ahostsv4 "${DUCKDNS_DOMAINS}.duckdns.org" 2>/dev/null | head -n 3 || true
fi

