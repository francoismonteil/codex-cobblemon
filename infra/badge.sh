#!/usr/bin/env bash
set -euo pipefail

# Grants/checks simple gym badges using vanilla scoreboards.
#
# Usage:
#   ./infra/badge.sh init
#   ./infra/badge.sh grant <PlayerName> <badge>
#   ./infra/badge.sh revoke <PlayerName> <badge>
#   ./infra/badge.sh status <PlayerName>
#
# Badges:
#   boulder | cascade | thunder | rainbow | soul | marsh | volcano | earth

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

usage() {
  echo "Usage:" >&2
  echo "  $0 init" >&2
  echo "  $0 grant <PlayerName> <badge>" >&2
  echo "  $0 revoke <PlayerName> <badge>" >&2
  echo "  $0 status <PlayerName>" >&2
  echo "" >&2
  echo "Badges: boulder cascade thunder rainbow soul marsh volcano earth" >&2
}

badge_to_obj() {
  local b
  b="$(echo "${1}" | tr '[:upper:]' '[:lower:]')"
  case "${b}" in
    boulder) echo "badge_boulder" ;;
    cascade) echo "badge_cascade" ;;
    thunder) echo "badge_thunder" ;;
    rainbow) echo "badge_rainbow" ;;
    soul) echo "badge_soul" ;;
    marsh) echo "badge_marsh" ;;
    volcano) echo "badge_volcano" ;;
    earth) echo "badge_earth" ;;
    *) return 1 ;;
  esac
}

recalc_total() {
  local player="$1"

  ./infra/mc.sh "scoreboard players set ${player} badge_total 0" || true
  for obj in badge_boulder badge_cascade badge_thunder badge_rainbow badge_soul badge_marsh badge_volcano badge_earth; do
    ./infra/mc.sh "execute if score ${player} ${obj} matches 1.. run scoreboard players add ${player} badge_total 1" || true
  done
}

cmd="${1:-}"
case "${cmd}" in
  init)
    ./infra/progression-init.sh
    ;;

  grant)
    if [[ $# -lt 3 ]]; then
      usage
      exit 2
    fi
    player="$2"
    badge="$3"
    if ! obj="$(badge_to_obj "${badge}")"; then
      echo "Unknown badge: ${badge}" >&2
      usage
      exit 2
    fi

    # Ensure objectives exist.
    ./infra/progression-init.sh >/dev/null 2>&1 || true

    # Set the badge to 1 and tag the player for quick future checks.
    ./infra/mc.sh "scoreboard players set ${player} ${obj} 1" || true
    ./infra/mc.sh "tag ${player} add ${obj}" || true

    recalc_total "${player}"

    pretty="$(echo "${badge}" | tr '[:lower:]' '[:upper:]' | cut -c1)$(echo "${badge}" | tr '[:upper:]' '[:lower:]' | cut -c2-)"
    ./infra/mc.sh "say [BADGE] ${player} a obtenu le badge ${pretty}." || true
    ;;

  revoke)
    if [[ $# -lt 3 ]]; then
      usage
      exit 2
    fi
    player="$2"
    badge="$3"
    if ! obj="$(badge_to_obj "${badge}")"; then
      echo "Unknown badge: ${badge}" >&2
      usage
      exit 2
    fi

    ./infra/progression-init.sh >/dev/null 2>&1 || true
    ./infra/mc.sh "scoreboard players reset ${player} ${obj}" || true
    ./infra/mc.sh "tag ${player} remove ${obj}" || true
    recalc_total "${player}"
    ;;

  status)
    if [[ $# -lt 2 ]]; then
      usage
      exit 2
    fi
    player="$2"

    # Ensure objectives exist (so gets don't error for missing objectives).
    ./infra/progression-init.sh >/dev/null 2>&1 || true

    ./infra/mc.sh "scoreboard players get ${player} badge_total" || true
    for obj in badge_boulder badge_cascade badge_thunder badge_rainbow badge_soul badge_marsh badge_volcano badge_earth; do
      ./infra/mc.sh "scoreboard players get ${player} ${obj}" || true
    done
    ;;

  *)
    usage
    exit 2
    ;;
esac
