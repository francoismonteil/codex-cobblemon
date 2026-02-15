#!/usr/bin/env bash
set -euo pipefail

# Disables background Chunky monitoring cron job.
#
# Usage:
#   ./infra/chunky-monitor-disable-cron.sh

CRON_TAG="minecraft-chunky-monitor"

tmp="$(mktemp)"
crontab -l 2>/dev/null | grep -v "${CRON_TAG}" > "${tmp}" || true
crontab "${tmp}"
rm -f "${tmp}"

echo "OK cron disabled (${CRON_TAG})"

