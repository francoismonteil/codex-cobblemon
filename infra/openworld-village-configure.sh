#!/usr/bin/env bash
set -euo pipefail

# Configures an already-generated world for the "Pokemon open world" profile:
# - chooses spawn at a naturally generated village (plains preferred)
# - centers world border on spawn, sets size 4000 (radius 2000)
# - creates a Flan spawn claim (~150 blocks radius) with "no grief, allow interaction"
# - starts Chunky pre-generation inside the world border
#
# Usage:
#   ./infra/openworld-village-configure.sh
#
# Assumptions:
# - Server is running (container "cobblemon")
# - Chunky + Flan mods are installed

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

say() {
  ./infra/mc.sh "say [MAINT] $*" >/dev/null 2>&1 || true
}

cmd() {
  ./infra/mc.sh "$1" >/dev/null
  sleep 0.25
}

cmd_try() {
  ./infra/mc.sh "$1" >/dev/null 2>&1 || true
  sleep 0.25
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

now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

docker_logs_since() {
  local since="$1"
  docker logs cobblemon --since "${since}" --tail 8000 2>/dev/null || true
}

locate_structure() {
  local structure="$1"
  local t0 out xyz
  t0="$(now_utc)"

  cmd "execute in minecraft:overworld run locate structure ${structure}"

  for _ in {1..45}; do
    out="$(docker_logs_since "${t0}" | grep -E 'The nearest .* is at \[-?[0-9]+, [^,]+, -?[0-9]+\]' | tail -n 1 || true)"
    if [[ -n "${out}" ]]; then
      xyz="$(echo "${out}" | sed -E 's/.*\[(-?[0-9]+), ([^,]+), (-?[0-9]+)\].*/\1 \2 \3/')"
      read -r x y z <<<"${xyz}"
      if [[ "${x}" =~ ^-?[0-9]+$ ]] && [[ "${z}" =~ ^-?[0-9]+$ ]]; then
        if [[ "${y}" == "~" ]]; then
          # locate reports "~" for Y in some versions; Y is not critical for spawn placement.
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

echo "== Wait server ready =="
wait_ready

say "Finding a natural plains village for spawn..."
spawn_xyz="$(locate_structure minecraft:village_plains || true)"
if [[ -z "${spawn_xyz}" ]]; then
  spawn_xyz="$(locate_structure minecraft:village_taiga || true)"
fi
if [[ -z "${spawn_xyz}" ]]; then
  spawn_xyz="$(locate_structure minecraft:village_savanna || true)"
fi
if [[ -z "${spawn_xyz}" ]]; then
  echo "ERROR: couldn't locate a village for spawn." >&2
  exit 1
fi

read -r SPAWN_X SPAWN_Y SPAWN_Z <<<"${spawn_xyz}"

echo "== Set world spawn =="
say "Setting spawn at village: ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"
cmd "setworldspawn ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"
cmd "gamerule spawnRadius 0"

echo "== World border =="
cmd "worldborder center ${SPAWN_X} ${SPAWN_Z}"
cmd "worldborder set 4000"
cmd_try "worldborder warning distance 32"
cmd_try "worldborder warning time 15"

echo "== Spawn protection claim (Flan, ~150 blocks) =="
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan add rect 301 301"
run_at "${SPAWN_X}" "${SPAWN_Y}" "${SPAWN_Z}" "flan name Spawn"

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

say "Open world configured. Border active, spawn protected, pre-generation started."
echo "OK open world configured:"
echo "  spawn: ${SPAWN_X} ${SPAWN_Y} ${SPAWN_Z}"
echo "  border: 4000 (radius 2000) centered on spawn"
