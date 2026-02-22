#!/usr/bin/env bash
set -euo pipefail

# Gives a small starter kit to a player (online only), with an optional pending queue.
#
# Usage:
#   ./infra/starter.sh <Pseudo>
#   ./infra/starter.sh --queue-if-offline <Pseudo>
#   ./infra/starter.sh --drain-pending [<Pseudo>]
#   ./infra/starter.sh --pending-list
#
# Notes:
# - Uses emerald economy, so keep it modest.
# - Adjust items as you like.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PENDING_DIR="${REPO_ROOT}/data/admin"
PENDING_FILE="${PENDING_DIR}/starter-pending.txt"

usage() {
  echo "Usage:" >&2
  echo "  $0 <Pseudo>" >&2
  echo "  $0 --queue-if-offline <Pseudo>" >&2
  echo "  $0 --drain-pending [<Pseudo>]" >&2
  echo "  $0 --pending-list" >&2
}

trim() {
  # shellcheck disable=SC2001
  echo "$1" | sed -e 's/^[[:space:]]\+//' -e 's/[[:space:]]\+$//'
}

ensure_pending_store() {
  mkdir -p "${PENDING_DIR}"
  touch "${PENDING_FILE}"
}

list_online_players() {
  # Best-effort from server logs after issuing "list".
  ./infra/mc.sh "list" >/dev/null 2>&1 || true
  local line names
  line="$(docker logs cobblemon --tail 250 2>/dev/null | grep -E 'There are [0-9]+ of a max' | tail -n 1 || true)"
  if [[ -z "${line}" ]]; then
    return 0
  fi

  names="$(printf '%s\n' "${line}" | sed -nE 's/.*There are [0-9]+ of a max of [0-9]+ players online: ?(.*)$/\1/p')"
  names="$(trim "${names}")"
  [[ -z "${names}" ]] && return 0

  printf '%s\n' "${names}" | tr ',' '\n' | while IFS= read -r n; do
    n="$(trim "${n}")"
    [[ -n "${n}" ]] && printf '%s\n' "${n}"
  done
}

is_player_online() {
  local want="$1" n attempt
  for attempt in 1 2 3; do
    while IFS= read -r n; do
      [[ "${n}" == "${want}" ]] && return 0
    done < <(list_online_players)
    sleep 1
  done
  return 1
}

queue_pending() {
  local name="$1"
  ensure_pending_store
  if grep -Fxq "${name}" "${PENDING_FILE}"; then
    echo "starter_pending_exists=${name}"
    return 0
  fi
  printf '%s\n' "${name}" >> "${PENDING_FILE}"
  echo "starter_pending_queued=${name}"
}

remove_pending() {
  local name="$1"
  ensure_pending_store
  local tmp
  tmp="$(mktemp)"
  grep -Fvx "${name}" "${PENDING_FILE}" > "${tmp}" || true
  mv "${tmp}" "${PENDING_FILE}"
}

give_starter_now() {
  local name="$1"
  if ! is_player_online "${name}"; then
    echo "starter_not_online=${name}" >&2
    return 3
  fi

  ./infra/mc.sh "give ${name} minecraft:bread 16"
  ./infra/mc.sh "give ${name} minecraft:torch 64"
  ./infra/mc.sh "give ${name} minecraft:oak_planks 64"
  ./infra/mc.sh "give ${name} minecraft:stone_pickaxe 1"
  ./infra/mc.sh "give ${name} minecraft:stone_axe 1"
  ./infra/mc.sh "give ${name} minecraft:white_bed 1"
  ./infra/mc.sh "give ${name} minecraft:emerald 8"
  ./infra/mc.sh "give ${name} cobblemon:poke_ball 16"
  ./infra/mc.sh "say [STARTER] Kit donne a ${name}."
  echo "starter_delivered=${name}"
}

drain_pending_for() {
  local name="$1"
  ensure_pending_store
  if ! grep -Fxq "${name}" "${PENDING_FILE}"; then
    echo "starter_pending_absent=${name}"
    return 0
  fi

  if give_starter_now "${name}"; then
    remove_pending "${name}"
  fi
}

drain_pending_all_online() {
  ensure_pending_store
  if [[ ! -s "${PENDING_FILE}" ]]; then
    echo "starter_pending_empty"
    return 0
  fi

  local names=()
  while IFS= read -r n; do
    [[ -n "${n}" ]] && names+=("${n}")
  done < "${PENDING_FILE}"

  for n in "${names[@]}"; do
    drain_pending_for "${n}" || true
  done
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

case "$1" in
  --pending-list)
    if [[ $# -ne 1 ]]; then
      usage
      exit 2
    fi
    ensure_pending_store
    if [[ ! -s "${PENDING_FILE}" ]]; then
      echo "(none)"
    else
      cat "${PENDING_FILE}"
    fi
    ;;

  --queue-if-offline)
    if [[ $# -ne 2 ]]; then
      usage
      exit 2
    fi
    name="$2"
    if is_player_online "${name}"; then
      give_starter_now "${name}"
    else
      queue_pending "${name}"
    fi
    ;;

  --drain-pending)
    if [[ $# -gt 2 ]]; then
      usage
      exit 2
    fi
    if [[ $# -eq 2 ]]; then
      drain_pending_for "$2"
    else
      drain_pending_all_online
    fi
    ;;

  *)
    if [[ $# -ne 1 ]]; then
      usage
      exit 2
    fi
    give_starter_now "$1"
    ;;
esac
