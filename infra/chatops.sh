#!/usr/bin/env bash
set -euo pipefail

# ChatOps minimal sans plugin/mod:
# - Lit le chat depuis ./data/logs/latest.log (volume /data/logs/latest.log)
# - Quand un joueur autorise envoie une commande (prefix+token), execute des scripts infra
# - Repond au joueur via "tell" (message prive) pour eviter de spammer le chat global
#
# Exemples (dans le chat Minecraft):
#   !mc <TOKEN> help
#   !mc <TOKEN> status
#   !mc <TOKEN> backup
#   !mc <TOKEN> restart
#
# Exec (sur le serveur Linux, dans le repo):
#   CHATOPS_ENABLED=true CHATOPS_TOKEN=... ./infra/chatops.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${REPO_ROOT}/logs"
CHATOPS_RUN_LOG="${LOG_DIR}/minecraft-chatops.log"

mkdir -p "${LOG_DIR}"
cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

usage() {
  cat <<'USAGE' >&2
Usage:
  ./infra/chatops.sh
  ./infra/chatops.sh --parse-line "<log line>"

Env (.env supported):
  CHATOPS_ENABLED=true|false
  CHATOPS_LOG_FILE=...                (default: ./data/logs/latest.log)
  CHATOPS_PREFIX="!mc"                (default: !mc)
  CHATOPS_TOKEN="..."                 (required for admin)
  CHATOPS_ALLOW_PLAYERS="YourPlayerName,..." (default: DEFAULT_PLAYER_NAME if set)
USAGE
}

log() {
  local msg="$1"
  local ts
  ts="$(date -Iseconds 2>/dev/null || date)"
  echo "ts=${ts} ${msg}" | tee -a "${CHATOPS_RUN_LOG}" >/dev/null
}

trim_leading_ws() {
  local s="$1"
  # shellcheck disable=SC2001
  echo "${s}" | sed -e 's/^[[:space:]]\+//'
}

sanitize_one_line() {
  # Best-effort: keep it readable in MC chat.
  local s="$1"
  s="${s//$'\r'/ }"
  s="${s//$'\n'/ }"
  # Collapse multiple spaces.
  # shellcheck disable=SC2001
  s="$(echo "${s}" | sed -e 's/[[:space:]]\+/ /g' -e 's/^ //; s/ $//')"
  # Truncate to reduce risk of client-side truncation/spam.
  local max=220
  if [[ "${#s}" -gt "${max}" ]]; then
    s="${s:0:${max}}..."
  fi
  echo "${s}"
}

tell_player() {
  local player="$1"
  shift
  local msg
  msg="$(sanitize_one_line "$*")"
  # Prefer private message to the invoking player.
  ./infra/mc.sh "tell ${player} [chatops] ${msg}" >/dev/null 2>&1 || true
}

say_all() {
  local msg
  msg="$(sanitize_one_line "$*")"
  ./infra/mc.sh "say [chatops] ${msg}" >/dev/null 2>&1 || true
}

is_allowed_player() {
  local player="$1"
  local list="${CHATOPS_ALLOW_PLAYERS:-}"
  list="${list// /}"
  list="${list//;/,}"
  [[ -z "${list}" ]] && return 1
  case ",${list}," in
    *",${player},"*) return 0 ;;
    *) return 1 ;;
  esac
}

parse_chat_line() {
  # Input: full log line
  # Output (stdout): "<player>\t<message>"
  local line="$1"

  # Typical format:
  # [08:01:02] [Server thread/INFO]: <Player> message
  # Keep regex permissive so it survives minor format changes.
  if [[ "${line}" =~ \<([^>]*)\>\ (.*)$ ]]; then
    local player="${BASH_REMATCH[1]}"
    local msg="${BASH_REMATCH[2]}"
    if [[ -n "${player}" && -n "${msg}" ]]; then
      printf '%s\t%s\n' "${player}" "${msg}"
      return 0
    fi
  fi

  return 1
}

handle_chat_command() {
  local player="$1"
  local msg="$2"

  local prefix="${CHATOPS_PREFIX:-!mc}"
  local token="${CHATOPS_TOKEN:-}"
  local require_token="${CHATOPS_REQUIRE_TOKEN:-true}"

  if [[ "${msg}" != "${prefix}" && "${msg}" != "${prefix} "* ]]; then
    return 0
  fi

  if ! is_allowed_player "${player}"; then
    log "event=reject reason=player_not_allowed player=${player}"
    return 0
  fi

  local payload
  # Avoid glob-pattern surprises: slice by prefix length.
  payload="${msg:${#prefix}}"
  payload="$(trim_leading_ws "${payload}")"

  if [[ "${require_token}" == "true" ]]; then
    if [[ -z "${token}" ]]; then
      # Hard fail-safe: admin actions without auth token are too risky.
      tell_player "${player}" "CHATOPS_TOKEN manquant: refuse (config serveur requise)"
      log "event=reject reason=token_missing player=${player}"
      return 0
    fi

    # Require token as first argument.
    local got_token="${payload%% *}"
    if [[ "${got_token}" != "${token}" ]]; then
      tell_player "${player}" "token invalide"
      log "event=reject reason=token_invalid player=${player}"
      return 0
    fi

    if [[ "${payload}" == "${got_token}" ]]; then
      payload=""
    else
      payload="${payload:${#got_token}}"
    fi
    payload="$(trim_leading_ws "${payload}")"
  fi

  local cmd="${payload%% *}"
  local args=""
  if [[ "${payload}" == *" "* ]]; then
    args="${payload#${cmd} }"
  fi

  if [[ -z "${cmd}" ]]; then
    tell_player "${player}" "commande manquante. Essaye: ${prefix} <token> help"
    return 0
  fi

  log "event=cmd player=${player} cmd=${cmd}"

  case "${cmd}" in
    help)
      tell_player "${player}" "cmds: help | status | backup | restart"
      if [[ "${require_token}" == "true" ]]; then
        tell_player "${player}" "ex: ${prefix} <token> status"
      else
        tell_player "${player}" "ex: ${prefix} status"
      fi
      ;;
    status)
      local health port_listen players_line players_count
      health="$(docker inspect cobblemon --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo 'cobblemon:missing')"
      port_listen="$(ss -ltn '( sport = :25565 )' 2>/dev/null | tail -n +2 | wc -l | tr -d ' ' || echo 0)"
      players_line="$(docker logs cobblemon --tail 200 2>/dev/null | grep -E 'There are [0-9]+ of a max' | tail -n 1 || true)"
      players_count="$(echo "${players_line}" | sed -nE 's/.*There are ([0-9]+) of a max.*/\1/p' || true)"
      [[ -z "${players_count}" ]] && players_count="unknown"
      tell_player "${player}" "${health} port25565_listen=${port_listen} players=${players_count}"
      ;;
    backup)
      tell_player "${player}" "backup: start"
      set +e
      local out
      out="$(./infra/backup.sh 2>&1)"
      local rc=$?
      set -e
      if [[ $rc -ne 0 ]]; then
        tell_player "${player}" "backup: error (rc=${rc})"
        log "event=backup status=error rc=${rc} out=$(sanitize_one_line "${out}")"
      else
        tell_player "${player}" "$(sanitize_one_line "${out}")"
        log "event=backup status=ok out=$(sanitize_one_line "${out}")"
      fi
      ;;
    restart)
      # Restart depuis le chat = forcement "force" (le joueur qui demande est en ligne).
      say_all "Restart demande par ${player}. Save + restart dans 10s."
      ./infra/mc.sh "save-all flush" >/dev/null 2>&1 || true
      sleep 10
      set +e
      local out
      out="$(./infra/safe-restart.sh --force 2>&1)"
      local rc=$?
      set -e
      if [[ $rc -ne 0 ]]; then
        say_all "Restart: erreur (rc=${rc}). Voir logs serveur."
        log "event=restart status=error rc=${rc} out=$(sanitize_one_line "${out}")"
      else
        say_all "Restart: OK"
        log "event=restart status=ok"
      fi
      ;;
    *)
      tell_player "${player}" "commande inconnue: ${cmd}. Essaye: help"
      ;;
  esac
}

main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
  fi

  if [[ "${1:-}" == "--parse-line" ]]; then
    shift
    local line="${1:-}"
    if [[ -z "${line}" ]]; then
      usage
      exit 2
    fi
    if parse_chat_line "${line}"; then
      exit 0
    fi
    exit 1
  fi

  local enabled="${CHATOPS_ENABLED:-false}"
  if [[ "${enabled}" != "true" ]]; then
    echo "CHATOPS_ENABLED is not true (got: ${enabled}). Exiting." >&2
    exit 2
  fi

  local log_file="${CHATOPS_LOG_FILE:-${REPO_ROOT}/data/logs/latest.log}"
  CHATOPS_LOG_FILE="${log_file}"

  if [[ ! -e "${CHATOPS_LOG_FILE}" ]]; then
    echo "CHATOPS_LOG_FILE not found: ${CHATOPS_LOG_FILE}" >&2
    echo "Tip: default is ./data/logs/latest.log (volume /data/logs/latest.log)" >&2
    exit 2
  fi

  if [[ -z "${CHATOPS_ALLOW_PLAYERS:-}" && -n "${DEFAULT_PLAYER_NAME:-}" ]]; then
    CHATOPS_ALLOW_PLAYERS="${DEFAULT_PLAYER_NAME}"
  fi

  log "event=start log_file=${CHATOPS_LOG_FILE} prefix=${CHATOPS_PREFIX:-!mc} allow_players=${CHATOPS_ALLOW_PLAYERS:-}"

  # Follow only new lines (no spam at start).
  tail -n 0 -F "${CHATOPS_LOG_FILE}" 2>/dev/null | while IFS= read -r line; do
    parsed="$(parse_chat_line "${line}" 2>/dev/null || true)"
    [[ -z "${parsed}" ]] && continue
    player="${parsed%%$'\t'*}"
    msg="${parsed#*$'\t'}"
    handle_chat_command "${player}" "${msg}" || true
  done
}

main "$@"
