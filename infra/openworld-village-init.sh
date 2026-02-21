#!/usr/bin/env bash
set -euo pipefail

# Creates a new open-world Cobblemon world and configures:
# - Spawn at a naturally generated plains village (nearest)
# - World border: size 4000 (radius 2000) centered on spawn
# - Pre-generation inside the border using Chunky
# - Spawn protection via a Flan claim (~150 blocks) while keeping doors/chests usable
#
# Safety:
# - Takes a backup
# - Archives the previous ./data/world folder
#
# Usage:
#   ./infra/openworld-village-init.sh
#   ./infra/openworld-village-init.sh --with-additionalstructures
#
# Notes:
# - This script assumes the server runs via Docker Compose with container name "cobblemon".
# - Pre-generation can take a long time; the script starts it and exits.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${REPO_ROOT}/data"
WORLD_DIR="${DATA_DIR}/world"
LOG_DIR="${REPO_ROOT}/logs"

cd "${REPO_ROOT}"
mkdir -p "${LOG_DIR}"

ts="$(date +%Y%m%d-%H%M%S)"
with_additionalstructures="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-additionalstructures)
      with_additionalstructures="true"
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--with-additionalstructures]" >&2
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      echo "Usage: $0 [--with-additionalstructures]" >&2
      exit 2
      ;;
  esac
done

say() {
  ./infra/mc.sh "say [MAINT] $*" >/dev/null 2>&1 || true
}

wait_ready() {
  # Prefer container health over log scraping (log tail can miss "Done" if noisy).
  for _ in {1..360}; do
    if docker inspect cobblemon --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null | grep -qE '^running healthy$'; then
      return 0
    fi
    sleep 2
  done
  return 1
}

compose_up() {
  # Use pregen override if available (limits CPU usage via JVM_OPTS_PREGEN/JVM_OPTS).
  if [[ -f "${REPO_ROOT}/docker-compose.pregen.yml" ]]; then
    docker compose -f "${REPO_ROOT}/docker-compose.yml" -f "${REPO_ROOT}/docker-compose.pregen.yml" up -d
  else
    docker compose -f "${REPO_ROOT}/docker-compose.yml" up -d
  fi
}

cmd() {
  ./infra/mc.sh "$1" >/dev/null
  sleep 0.25
}

cmd_try() {
  ./infra/mc.sh "$1" >/dev/null 2>&1 || true
  sleep 0.25
}

now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

docker_logs_since() {
  local since="$1"
  docker logs cobblemon --since "${since}" --tail 5000 2>/dev/null || true
}

locate_structure() {
  local structure="$1"

  local t0 out xyz
  t0="$(now_utc)"

  # Force the locate to run in the overworld regardless of where the server source is.
  cmd "execute in minecraft:overworld run locate structure ${structure}"

  for _ in {1..30}; do
    out="$(docker_logs_since "${t0}" | grep -E 'The nearest .* is at \[-?[0-9]+, [^,]+, -?[0-9]+\]' | tail -n 1 || true)"
    if [[ -n "${out}" ]]; then
      xyz="$(echo "${out}" | sed -E 's/.*\[(-?[0-9]+), ([^,]+), (-?[0-9]+)\].*/\1 \2 \3/')"
      read -r x y z <<<"${xyz}"
      if [[ "${x}" =~ ^-?[0-9]+$ ]] && [[ "${z}" =~ ^-?[0-9]+$ ]]; then
        if [[ "${y}" == "~" ]]; then
          y="80"
        fi
        if [[ "${y}" =~ ^-?[0-9]+$ ]]; then
          echo "${x} ${y} ${z}"
          return 0
        fi
      fi
    fi
    sleep 1
  done

  return 1
}

run_at() {
  local x="$1"
  local y="$2"
  local z="$3"
  shift 3
  cmd "execute in minecraft:overworld positioned ${x} ${y} ${z} run $*"
}

echo "== Apply server profile (open world, 4 players) =="
./infra/server-profile-openworld-4p.sh

echo "== Ensure extra mods (Chunky + Flan) =="
./infra/mods-install-openworld.sh

say "Open world setup starting. Server will restart."
cmd_try "save-all flush"
cmd_try "stop"
sleep 4
./infra/stop.sh || true

echo "== Backup =="
./infra/backup.sh

echo "== Archive old world folder =="
if [[ -d "${WORLD_DIR}" ]]; then
  mv "${WORLD_DIR}" "${DATA_DIR}/world.prev-${ts}"
fi

echo "== Start server (generate fresh world) =="
compose_up
wait_ready

echo "== Install pokemon worldgen datapack =="
if [[ -x "${REPO_ROOT}/infra/install-pokemon-worldgen-datapack.sh" ]]; then
  # Ensure worldgen registries include acm_pokemon_worldgen before village pregen starts.
  "${REPO_ROOT}/infra/install-pokemon-worldgen-datapack.sh" --restart
  wait_ready
else
  echo "WARN: install-pokemon-worldgen-datapack.sh not found/executable; continuing without explicit datapack install."
fi

if [[ "${with_additionalstructures}" == "true" ]]; then
  echo "== Install additionalstructures datapack =="
  if [[ ! -x "${REPO_ROOT}/infra/install-additionalstructures-datapack.sh" ]]; then
    echo "ERROR: missing executable infra/install-additionalstructures-datapack.sh" >&2
    exit 1
  fi
  # World exists at this point and may already contain bootstrap region files from first startup.
  "${REPO_ROOT}/infra/install-additionalstructures-datapack.sh" --new-world --allow-existing-world
  wait_ready

  echo "== Validate worldgen datapacks (ACM + Additional Structures) =="
  if [[ ! -x "${REPO_ROOT}/infra/validate-worldgen-datapacks.sh" ]]; then
    echo "ERROR: missing executable infra/validate-worldgen-datapacks.sh" >&2
    exit 1
  fi
  "${REPO_ROOT}/infra/validate-worldgen-datapacks.sh"
  wait_ready
fi

say "Finding a natural plains village for spawn..."
spawn_xyz="$(locate_structure minecraft:village_plains || true)"
if [[ -z "${spawn_xyz}" ]]; then
  # Fallbacks to keep the workflow moving.
  spawn_xyz="$(locate_structure minecraft:village_taiga || true)"
fi
if [[ -z "${spawn_xyz}" ]]; then
  spawn_xyz="$(locate_structure minecraft:village_savanna || true)"
fi
if [[ -z "${spawn_xyz}" ]]; then
  echo "ERROR: couldn't locate a village for spawn. Try again or locate manually in-game." >&2
  exit 1
fi

read -r SPAWN_X SPAWN_Y SPAWN_Z <<<"${spawn_xyz}"

say "Setting spawn at village: ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"
cmd "setworldspawn ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"
cmd "gamerule spawnRadius 0"

echo "== World border (size 4000, centered on spawn) =="
cmd "worldborder center ${SPAWN_X} ${SPAWN_Z}"
cmd "worldborder set 4000"
cmd_try "worldborder warning distance 32"
cmd_try "worldborder warning time 15"

echo "== Spawn protection claim (Flan, ~150 blocks) =="
# Create a square claim centered on spawn. 301 ~= (150*2)+1.
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan add rect 301 301"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan name Spawn"

# Deny griefing, allow interaction.
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:break false"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:place false"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:explosions false"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:fire_spread false"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:raid false"

run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:door true"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:trapdoor true"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:fence_gate true"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:button_lever true"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:pressure_plate true"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:open_container true"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:interact_block true"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:trading true"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:bed true"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:pickup true"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan permission global flan:drop true"

echo "== Chunk pre-generation (Chunky) =="
say "Starting chunk pre-generation inside the world border (Chunky)."
cmd_try "chunky shape square"
cmd "chunky worldborder"
cmd_try "chunky quiet"
cmd "chunky start"

say "Open world init done. Spawn is set, border is active, pre-generation started."
echo "OK open world init:"
echo "  spawn: ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"
echo "  border: 4000 (radius 2000) centered on spawn"
echo "  chunky: running (check progress with: ./infra/mc.sh \"chunky progress\")"
