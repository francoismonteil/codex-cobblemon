#!/usr/bin/env bash
set -euo pipefail

# Enables background Chunky monitoring via user crontab (linux user).
#
# Installs:
#   */5 * * * * cd <MC_PROJECT_DIR> && <MC_PROJECT_DIR>/infra/chunky-monitor.sh >> <MC_PROJECT_DIR>/logs/chunky-monitor-cron.log 2>&1 # minecraft-chunky-monitor
#
# Usage:
#   ./infra/chunky-monitor-enable-cron.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PROJECT_DIR="${PROJECT_DIR:-${REPO_ROOT}}"
CRON_TAG="minecraft-chunky-monitor"

line="*/5 * * * * cd ${PROJECT_DIR} && ${PROJECT_DIR}/infra/chunky-monitor.sh >> ${PROJECT_DIR}/logs/chunky-monitor-cron.log 2>&1 # ${CRON_TAG}"

tmp="$(mktemp)"
crontab -l 2>/dev/null | grep -v "${CRON_TAG}" > "${tmp}" || true
printf '%s\n' "${line}" >> "${tmp}"
crontab "${tmp}"
rm -f "${tmp}"

echo "OK cron enabled (${CRON_TAG})"
