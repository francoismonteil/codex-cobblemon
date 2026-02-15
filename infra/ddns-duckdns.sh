#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${REPO_ROOT}/logs"
LOG_FILE="${LOG_DIR}/ddns-duckdns.log"

mkdir -p "${LOG_DIR}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

DUCKDNS_DOMAINS="${DUCKDNS_DOMAINS:-}"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:-}"

if [[ -z "${DUCKDNS_DOMAINS}" || -z "${DUCKDNS_TOKEN}" ]]; then
  echo "DDNS not configured (set DUCKDNS_DOMAINS and DUCKDNS_TOKEN in .env)" >> "${LOG_FILE}"
  exit 0
fi

timestamp="$(date -Iseconds)"
public_ip="$(curl -fsS -m 10 https://api.ipify.org || echo "unknown")"

# If ip= is omitted, DuckDNS uses the requestor IP. We send it explicitly for logging/debugging.
update_url="https://www.duckdns.org/update?domains=${DUCKDNS_DOMAINS}&token=${DUCKDNS_TOKEN}&ip=${public_ip}"
result="$(curl -fsS -m 15 "${update_url}" || true)"

if [[ "${result}" != "OK" ]]; then
  echo "ts=${timestamp} status=error ip=${public_ip} result=${result:-empty}" >> "${LOG_FILE}"
  exit 1
fi

echo "ts=${timestamp} status=ok ip=${public_ip} domains=${DUCKDNS_DOMAINS}" >> "${LOG_FILE}"

