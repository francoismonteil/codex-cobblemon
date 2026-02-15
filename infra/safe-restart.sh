#!/usr/bin/env bash
set -euo pipefail

# Safe daily restart:
# - If players are online: skip (unless forced)
# - Restart the cobblemon service
# - Validate it comes back (port 25565 + "Done" log)
# - On failure: post to MONITOR_WEBHOOK_URL (Discord supported)
#
# Usage:
#   ./infra/safe-restart.sh            # skip if players online
#   ./infra/safe-restart.sh --force    # restart even if players online

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${REPO_ROOT}/logs"
LOG_FILE="${LOG_DIR}/minecraft-safe-restart.log"

mkdir -p "${LOG_DIR}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

MONITOR_WEBHOOK_URL="${MONITOR_WEBHOOK_URL:-}"
force="false"
if [[ "${1:-}" == "--force" ]]; then
  force="true"
fi

timestamp="$(date -Iseconds)"
host="$(hostname)"

post_webhook() {
  local msg="$1"
  [[ -z "${MONITOR_WEBHOOK_URL}" ]] && return 0

  if [[ "${MONITOR_WEBHOOK_URL}" == *"discord.com/api/webhooks"* ]]; then
    local payload
    payload="$(printf '{"content":"%s"}' "${msg//\"/\\\"}")"
    curl -fsS -m 10 -H "Content-Type: application/json" -d "${payload}" "${MONITOR_WEBHOOK_URL}" >/dev/null || true
  else
    curl -fsS -m 10 -d "${msg}" "${MONITOR_WEBHOOK_URL}" >/dev/null || true
  fi
}

get_players_online() {
  # Returns a single integer, or empty if unknown.
  if ! docker inspect cobblemon >/dev/null 2>&1; then
    return 0
  fi

  if ! docker inspect cobblemon --format '{{.State.Running}}' 2>/dev/null | grep -qi true; then
    return 0
  fi

  # Requires console in pipe enabled, which we enable in .env/docker-compose.yml.
  if ! docker exec -u 1000 cobblemon mc-send-to-console "list" >/dev/null 2>&1; then
    return 0
  fi

  local line
  line="$(docker logs cobblemon --tail 200 2>/dev/null | grep -E 'There are [0-9]+ of a max' | tail -n 1 || true)"
  if [[ -z "${line}" ]]; then
    return 0
  fi

  echo "${line}" | sed -nE 's/.*There are ([0-9]+) of a max.*/\1/p'
}

players="$(get_players_online || true)"
if [[ -n "${players}" && "${players}" != "0" && "${force}" != "true" ]]; then
  echo "ts=${timestamp} host=${host} action=skip reason=players_online players=${players}" | tee -a "${LOG_FILE}"
  exit 0
fi

echo "ts=${timestamp} host=${host} action=restart force=${force} players=${players:-unknown}" | tee -a "${LOG_FILE}"

set +e
docker compose restart cobblemon >>"${LOG_FILE}" 2>&1
rc=$?
set -e
if [[ $rc -ne 0 ]]; then
  echo "ts=${timestamp} host=${host} action=restart_result status=error step=compose_restart rc=${rc}" | tee -a "${LOG_FILE}"
  post_webhook "ALERT host=${host} ts=${timestamp} safe_restart=failed step=compose_restart rc=${rc}"
  exit 1
fi

# Wait for startup confirmation. We only validate that the server is listening and has completed startup at least once
# after the restart, not that we saw a new "Done" line.
ok="false"
VALIDATE_MAX_SECS="${VALIDATE_MAX_SECS:-120}"
VALIDATE_INTERVAL_SECS="${VALIDATE_INTERVAL_SECS:-2}"
max_iters="$(( VALIDATE_MAX_SECS / VALIDATE_INTERVAL_SECS ))"
if [[ "${max_iters}" -lt 1 ]]; then
  max_iters=1
fi

for _ in $(seq 1 "${max_iters}"); do
  if ss -ltn '( sport = :25565 )' 2>/dev/null | tail -n +2 | grep -q 25565; then
    if docker inspect cobblemon --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null | grep -qi healthy; then
      ok="true"
      break
    fi
  fi
  sleep "${VALIDATE_INTERVAL_SECS}"
done

if [[ "${ok}" != "true" ]]; then
  echo "ts=${timestamp} host=${host} action=restart_result status=error step=validate" | tee -a "${LOG_FILE}"
  # Include a tiny hint for debugging without dumping huge logs.
  port_state="$(ss -ltn 2>/dev/null | grep -c ':25565 ' || true)"
  health_state="$(docker inspect cobblemon --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo 'missing')"
  echo "ts=${timestamp} host=${host} hint=validate port_listen_count=${port_state} health=${health_state}" | tee -a "${LOG_FILE}"
  post_webhook "ALERT host=${host} ts=${timestamp} safe_restart=failed step=validate (port/log not ready)"
  exit 1
fi

echo "ts=${timestamp} host=${host} action=restart_result status=ok" | tee -a "${LOG_FILE}"
