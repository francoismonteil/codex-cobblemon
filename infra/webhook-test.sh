#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

MONITOR_WEBHOOK_URL="${MONITOR_WEBHOOK_URL:-}"
if [[ -z "${MONITOR_WEBHOOK_URL}" ]]; then
  echo "MONITOR_WEBHOOK_URL is empty"
  exit 2
fi

timestamp="$(date -Iseconds)"
host="$(hostname)"
msg="TEST host=${host} ts=${timestamp} kind=webhook"

if [[ "${MONITOR_WEBHOOK_URL}" == *"discord.com/api/webhooks"* ]]; then
  payload="$(printf '{"content":"%s"}' "${msg//\"/\\\"}")"
  curl -fsS -m 10 -H "Content-Type: application/json" -d "${payload}" "${MONITOR_WEBHOOK_URL}" >/dev/null
else
  curl -fsS -m 10 -d "${msg}" "${MONITOR_WEBHOOK_URL}" >/dev/null
fi

echo "OK"

