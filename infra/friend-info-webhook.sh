#!/usr/bin/env bash
set -euo pipefail

# Post friend connection/setup info to a webhook (Discord supported).
#
# Usage:
#   ./infra/friend-info-webhook.sh
#   ./infra/friend-info-webhook.sh --dry-run
#   ./infra/friend-info-webhook.sh --webhook-url https://discord.com/api/webhooks/...
#
# Env:
#   FRIENDS_WEBHOOK_URL  (preferred)
#   MONITOR_WEBHOOK_URL  (fallback)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

webhook_url="${FRIENDS_WEBHOOK_URL:-${MONITOR_WEBHOOK_URL:-}}"
dry_run="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run="true"
      ;;
    --webhook-url)
      shift
      if [[ $# -eq 0 ]]; then
        echo "Usage: $0 [--dry-run] [--webhook-url <url>]" >&2
        exit 2
      fi
      webhook_url="$1"
      ;;
    *)
      echo "Usage: $0 [--dry-run] [--webhook-url <url>]" >&2
      exit 2
      ;;
  esac
  shift
done

if [[ -z "${webhook_url}" ]]; then
  echo "FRIENDS_WEBHOOK_URL is empty (and MONITOR_WEBHOOK_URL fallback is empty)" >&2
  exit 2
fi

if [[ ! -f "${REPO_ROOT}/infra/friend-info.sh" ]]; then
  echo "Missing infra/friend-info.sh" >&2
  exit 1
fi

body="$(bash "${REPO_ROOT}/infra/friend-info.sh" --markdown)"

# Discord limit for content is 2000 chars. Keep some room for prefix/suffix.
prefix="Infos serveur pour les amis"
content="**${prefix}**"$'\n'"${body}"$'\n'"_Ref: runbooks/friends-guide.md_"

if (( ${#content} > 1900 )); then
  echo "Generated message is too long for Discord webhook content (${#content} chars)" >&2
  exit 1
fi

if [[ "${dry_run}" == "true" ]]; then
  printf '%s\n' "${content}"
  exit 0
fi

if [[ "${webhook_url}" == *"discord.com/api/webhooks"* ]]; then
  escaped="$(
    printf '%s' "${content}" \
      | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e ':a;N;$!ba;s/\r//g;s/\n/\\n/g'
  )"
  payload="$(printf '{"content":"%s"}' "${escaped}")"
  curl -fsS -m 10 -H "Content-Type: application/json" -d "${payload}" "${webhook_url}" >/dev/null
else
  curl -fsS -m 10 -d "${content}" "${webhook_url}" >/dev/null
fi

echo "OK"
