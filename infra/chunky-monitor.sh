#!/usr/bin/env bash
set -euo pipefail

# Background-friendly Chunky progress monitor.
#
# How it works:
# - Sends "chunky progress" to the server console (no RCON).
# - Scrapes recent docker logs for the resulting output.
# - Logs a one-line metric to ./logs/chunky-monitor.log
# - Optionally sends Discord webhook updates via MONITOR_WEBHOOK_URL (reuses infra/monitor.sh env)
#
# Notify policy:
# - On progress buckets (default: every 20%).
# - On completion (100%).
# - On "Chunky not installed" (once).
# - On stall (no progress change for CHUNKY_STALL_MIN minutes, once per window).
#
# Usage:
#   ./infra/chunky-monitor.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${REPO_ROOT}/logs"
METRICS_LOG="${LOG_DIR}/chunky-monitor.log"
STATE_FILE="${LOG_DIR}/.chunky-monitor-state"

mkdir -p "${LOG_DIR}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

MONITOR_WEBHOOK_URL="${MONITOR_WEBHOOK_URL:-}"
CHUNKY_NOTIFY_BUCKET="${CHUNKY_NOTIFY_BUCKET:-20}"   # 20 => 0,20,40,60,80,100
CHUNKY_STALL_MIN="${CHUNKY_STALL_MIN:-90}"

timestamp="$(date -Iseconds)"
host="$(hostname)"

docker_bin="$(command -v docker || true)"
if [[ -z "${docker_bin}" ]]; then
  echo "ERROR docker not found" >&2
  exit 1
fi

container_status="$("${docker_bin}" inspect cobblemon --format '{{.State.Status}}' 2>/dev/null || echo "missing")"
if [[ "${container_status}" != "running" ]]; then
  echo "OK ts=${timestamp} host=${host} status=${container_status} note=container_not_running" >> "${METRICS_LOG}"
  exit 0
fi

send_cmd() {
  "${REPO_ROOT}/infra/mc.sh" "$1" >/dev/null 2>&1 || true
}

now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

logs_since() {
  local since="$1"
  "${docker_bin}" logs cobblemon --since "${since}" --tail 3000 2>/dev/null || true
}

post_webhook() {
  local text="$1"
  if [[ -z "${MONITOR_WEBHOOK_URL}" ]]; then
    return 0
  fi
  if [[ "${MONITOR_WEBHOOK_URL}" == *"discord.com/api/webhooks"* ]]; then
    payload="$(printf '{"content":"%s"}' "${text//\"/\\\"}")"
    curl -fsS -m 10 -H "Content-Type: application/json" -d "${payload}" "${MONITOR_WEBHOOK_URL}" >/dev/null || true
  else
    curl -fsS -m 10 -d "${text}" "${MONITOR_WEBHOOK_URL}" >/dev/null || true
  fi
}

# Load state (best-effort)
last_pct="-1"
last_change_epoch="0"
last_bucket="-1"
notified_no_chunky="false"
last_stall_alert_epoch="0"
if [[ -f "${STATE_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${STATE_FILE}" || true
fi

t0="$(now_utc)"
send_cmd "chunky progress"
sleep 1

recent="$(logs_since "${t0}")"

# Detect "unknown command" (Chunky missing)
if echo "${recent}" | grep -qiE 'Unknown or incomplete command|Unknown command'; then
  echo "OK ts=${timestamp} host=${host} chunky=missing status=${container_status}" >> "${METRICS_LOG}"
  if [[ "${notified_no_chunky}" != "true" ]]; then
    post_webhook "[CHUNKY] ${host}: commande Chunky inconnue (mod Chunky absent?)"
    notified_no_chunky="true"
    cat > "${STATE_FILE}" <<EOF
last_pct=${last_pct}
last_change_epoch=${last_change_epoch}
last_bucket=${last_bucket}
notified_no_chunky=true
last_stall_alert_epoch=${last_stall_alert_epoch}
EOF
  fi
  exit 0
fi

line="$(echo "${recent}" | grep -F '[Chunky]' | grep -E '[0-9]+([.][0-9]+)?%' | tail -n 1 || true)"
if [[ -z "${line}" ]]; then
  # Fallbacks if the progress line didn't show up (or task is idle).
  line="$(echo "${recent}" | grep -F '[Chunky]' | tail -n 1 || true)"
fi
if [[ -z "${line}" ]]; then
  line="$("${docker_bin}" logs cobblemon --tail 3000 2>/dev/null | grep -F '[Chunky]' | tail -n 1 || true)"
fi

pct=""
if [[ -n "${line}" ]]; then
  pct="$(echo "${line}" | grep -oE '[0-9]+([.][0-9]+)?%' | head -n 1 | tr -d '%' || true)"
fi

complete="false"
if [[ -n "${line}" ]] && echo "${line}" | grep -qiE 'complete|completed|finished|done'; then
  complete="true"
fi

if [[ "${complete}" == "true" ]]; then
  pct="100"
fi

pct_int=""
if [[ -n "${pct}" ]]; then
  pct_int="${pct%.*}"
  if ! [[ "${pct_int}" =~ ^[0-9]+$ ]]; then
    pct_int=""
  fi
fi

epoch_now="$(date +%s)"
changed="false"
if [[ -n "${pct_int}" ]] && [[ "${pct_int}" != "${last_pct}" ]]; then
  changed="true"
  last_pct="${pct_int}"
  last_change_epoch="${epoch_now}"
fi

bucket="-1"
if [[ -n "${pct_int}" ]]; then
  bucket=$(( (pct_int / CHUNKY_NOTIFY_BUCKET) * CHUNKY_NOTIFY_BUCKET ))
fi

safe_line="$(echo "${line:-}" | tr '\r' ' ' | tr -s ' ' | cut -c1-220)"
echo "ts=${timestamp} host=${host} chunky_pct=${pct_int:-na} changed=${changed} status=${container_status} line=\"${safe_line//\"/\\\"}\"" >> "${METRICS_LOG}"

# Notify progress buckets
if [[ -n "${pct_int}" ]] && (( bucket >= 0 )) && (( bucket != last_bucket )) && (( bucket % CHUNKY_NOTIFY_BUCKET == 0 )); then
  last_bucket="${bucket}"
  post_webhook "[CHUNKY] ${host}: ${pct_int}%"
fi

# Notify completion (once)
if [[ -n "${pct_int}" ]] && (( pct_int >= 100 )); then
  if (( last_bucket < 100 )); then
    last_bucket="100"
    post_webhook "[CHUNKY] ${host}: pre-generation terminee (100%)"
  fi
fi

# Stall detection
if [[ -n "${pct_int}" ]] && (( pct_int > 0 )) && (( pct_int < 100 )); then
  mins_since_change=$(( (epoch_now - last_change_epoch) / 60 ))
  if (( mins_since_change >= CHUNKY_STALL_MIN )); then
    mins_since_stall_alert=$(( (epoch_now - last_stall_alert_epoch) / 60 ))
    if (( mins_since_stall_alert >= CHUNKY_STALL_MIN )); then
      last_stall_alert_epoch="${epoch_now}"
      post_webhook "[CHUNKY] ${host}: pas de progression depuis ~${mins_since_change} min (actuel: ${pct_int}%)"
    fi
  fi
fi

cat > "${STATE_FILE}" <<EOF
last_pct=${last_pct}
last_change_epoch=${last_change_epoch}
last_bucket=${last_bucket}
notified_no_chunky=${notified_no_chunky}
last_stall_alert_epoch=${last_stall_alert_epoch}
EOF

echo "OK chunky monitor tick (pct=${pct_int:-na})"
