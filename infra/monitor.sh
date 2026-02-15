#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${REPO_ROOT}/logs"
METRICS_LOG="${LOG_DIR}/minecraft-monitor.log"
STATE_FILE="${LOG_DIR}/.minecraft-monitor-last-alert"

mkdir -p "${LOG_DIR}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

MONITOR_DISK_MAX_PCT="${MONITOR_DISK_MAX_PCT:-85}"
MONITOR_MEM_MAX_PCT="${MONITOR_MEM_MAX_PCT:-92}"
MONITOR_LOAD1_MAX="${MONITOR_LOAD1_MAX:-6}"
MONITOR_CONTAINER_MEM_MAX_PCT="${MONITOR_CONTAINER_MEM_MAX_PCT:-95}"
MONITOR_WEBHOOK_URL="${MONITOR_WEBHOOK_URL:-}"

timestamp="$(date -Iseconds)"
host="$(hostname)"
alerts=()

container_status="$(docker inspect cobblemon --format '{{.State.Status}}' 2>/dev/null || echo "missing")"
container_health="$(docker inspect cobblemon --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo "missing")"
if [[ "${container_status}" != "running" ]]; then
  alerts+=("container_status=${container_status}")
fi
if [[ "${container_health}" != "healthy" ]]; then
  alerts+=("container_health=${container_health}")
fi

if ! ss -ltn '( sport = :25565 )' | tail -n +2 | grep -q 25565; then
  alerts+=("port_25565=closed")
fi

disk_pct="$(df -P / | awk 'NR==2{gsub("%","",$5); print $5}')"
if (( disk_pct >= MONITOR_DISK_MAX_PCT )); then
  alerts+=("disk_pct=${disk_pct}")
fi

mem_pct="$(free | awk '/Mem:/{printf "%d", ($3/$2)*100}')"
if (( mem_pct >= MONITOR_MEM_MAX_PCT )); then
  alerts+=("host_mem_pct=${mem_pct}")
fi

load1="$(awk '{print int($1+0.5)}' /proc/loadavg)"
if (( load1 >= MONITOR_LOAD1_MAX )); then
  alerts+=("load1=${load1}")
fi

container_mem_pct="$(
  docker stats --no-stream --format '{{.Name}} {{.MemPerc}}' 2>/dev/null \
    | awk '$1=="cobblemon"{gsub("%","",$2); print int($2+0.5)}'
)"
if [[ -n "${container_mem_pct}" ]] && (( container_mem_pct >= MONITOR_CONTAINER_MEM_MAX_PCT )); then
  alerts+=("container_mem_pct=${container_mem_pct}")
fi

metrics="ts=${timestamp} host=${host} status=${container_status} health=${container_health} disk_pct=${disk_pct} mem_pct=${mem_pct} load1=${load1} container_mem_pct=${container_mem_pct:-na}"
echo "${metrics}" >> "${METRICS_LOG}"

if (( ${#alerts[@]} == 0 )); then
  echo "OK ${metrics}"
  exit 0
fi

alert_text="ALERT host=${host} ts=${timestamp} issues=$(IFS=,; echo "${alerts[*]}")"
alert_key="$(printf '%s' "${alert_text}" | sha256sum | awk '{print $1}')"
last_key="$(cat "${STATE_FILE}" 2>/dev/null || true)"

if [[ "${alert_key}" != "${last_key}" ]]; then
  echo "${alert_key}" > "${STATE_FILE}"
  echo "${alert_text}" | tee -a "${METRICS_LOG}"

  if [[ -n "${MONITOR_WEBHOOK_URL}" ]]; then
    if [[ "${MONITOR_WEBHOOK_URL}" == *"discord.com/api/webhooks"* ]]; then
      payload="$(printf '{"content":"%s"}' "${alert_text//\"/\\\"}")"
      curl -fsS -m 10 -H "Content-Type: application/json" -d "${payload}" "${MONITOR_WEBHOOK_URL}" >/dev/null || true
    else
      curl -fsS -m 10 -d "${alert_text}" "${MONITOR_WEBHOOK_URL}" >/dev/null || true
    fi
  fi
else
  echo "ALERT_UNCHANGED ${alert_text}" >> "${METRICS_LOG}"
fi

exit 1
