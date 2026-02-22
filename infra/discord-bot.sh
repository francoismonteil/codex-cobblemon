#!/usr/bin/env bash
set -euo pipefail

# Minimal wrapper to install/run the Discord whitelist bot.
#
# Usage:
#   ./infra/discord-bot.sh install
#   ./infra/discord-bot.sh run
#   ./infra/discord-bot.sh check-env

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv-discord-bot"
REQ_FILE="${REPO_ROOT}/infra/discord-bot.requirements.txt"
BOT_FILE="${REPO_ROOT}/infra/discord_whitelist_bot.py"

cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

find_py() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi
  echo "Missing python3/python" >&2
  return 1
}

usage() {
  cat <<'EOF' >&2
Usage:
  ./infra/discord-bot.sh install
  ./infra/discord-bot.sh run
  ./infra/discord-bot.sh check-env

Env (.env supported):
  DISCORD_BOT_TOKEN=...
  DISCORD_BOT_GUILD_ID=123456789012345678       (recommended for fast slash sync)
  DISCORD_BOT_ALLOWED_CHANNEL_IDS=1,2,3         (optional)
  DISCORD_BOT_ALLOWED_ROLE_IDS=4,5,6            (optional but recommended)
EOF
}

check_env() {
  local missing=0
  if [[ -z "${DISCORD_BOT_TOKEN:-}" ]]; then
    echo "DISCORD_BOT_TOKEN: missing"
    missing=1
  else
    echo "DISCORD_BOT_TOKEN: set"
  fi

  if [[ -n "${DISCORD_BOT_GUILD_ID:-}" ]]; then
    echo "DISCORD_BOT_GUILD_ID: set"
  else
    echo "DISCORD_BOT_GUILD_ID: missing (global slash sync can take longer)"
  fi

  if [[ -n "${DISCORD_BOT_ALLOWED_CHANNEL_IDS:-}" ]]; then
    echo "DISCORD_BOT_ALLOWED_CHANNEL_IDS: set"
  else
    echo "DISCORD_BOT_ALLOWED_CHANNEL_IDS: not set (all channels in guild allowed)"
  fi

  if [[ -n "${DISCORD_BOT_ALLOWED_ROLE_IDS:-}" ]]; then
    echo "DISCORD_BOT_ALLOWED_ROLE_IDS: set"
  else
    echo "DISCORD_BOT_ALLOWED_ROLE_IDS: not set (any member in allowed guild/channel can whitelist)"
  fi

  return "${missing}"
}

install_deps() {
  local pybin
  pybin="$(find_py)"
  "${pybin}" -m venv "${VENV_DIR}"
  "${VENV_DIR}/bin/python" -m pip install --upgrade pip
  "${VENV_DIR}/bin/pip" install -r "${REQ_FILE}"
  echo "OK installed venv: ${VENV_DIR}"
}

run_bot() {
  if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    echo "Venv missing. Run: ./infra/discord-bot.sh install" >&2
    exit 2
  fi
  exec "${VENV_DIR}/bin/python" "${BOT_FILE}"
}

cmd="${1:-}"
case "${cmd}" in
  install)
    install_deps
    ;;
  run)
    run_bot
    ;;
  check-env)
    check_env
    ;;
  *)
    usage
    exit 2
    ;;
esac
