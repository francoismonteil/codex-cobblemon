#!/usr/bin/env bash
set -euo pipefail

# Spawn multiple windmills (schematic paste) in overworld plains, "a bit everywhere", but not too many.
#
# Strategy:
# - Pick random sample points within a radius of center.
# - For each sample, use vanilla `locate biome minecraft:plains` to get a plains coordinate.
# - Read ground Y at that X/Z from the world heightmap (MOTION_BLOCKING_NO_LEAVES) via infra/world-height-at.py.
# - Paste the windmill schematic at that ground Y (best-effort).
#
# Notes:
# - Requires the world to already be generated (chunks exist). If locate returns far-away plains, the chunk may not
#   exist yet and heightmap lookup will fail; we then retry.
# - The schematic uses WEOffsetY=-4; we paste with origin_y = ground_y + 4 so the schematic base sits on ground.
#
# Usage:
#   ./infra/spawn-windmills-plains.sh
#   ./infra/spawn-windmills-plains.sh --count 6 --radius 6000 --min-dist 1200
#   ./infra/spawn-windmills-plains.sh --center 0 120 0 --count 4

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

schematic="downloads/Windmill - (mcbuild_org).schematic"
count="5"
radius="6000"
min_dist="1200"
center_x="0"
center_y="120"
center_z="0"
tries_per="40"
dry_run="false"

usage() {
  cat <<EOF >&2
Usage:
  $0 [--schematic <path>] [--count <n>] [--radius <blocks>] [--min-dist <blocks>]
     [--center <x> <y> <z>] [--tries-per <n>] [--dry-run]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --schematic)
      schematic="${2:?}"; shift 2;;
    --count)
      count="${2:?}"; shift 2;;
    --radius)
      radius="${2:?}"; shift 2;;
    --min-dist)
      min_dist="${2:?}"; shift 2;;
    --center)
      center_x="${2:?}"; center_y="${3:?}"; center_z="${4:?}"; shift 4;;
    --tries-per)
      tries_per="${2:?}"; shift 2;;
    --dry-run)
      dry_run="true"; shift;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 2;;
  esac
done

for v in "${count}" "${radius}" "${min_dist}" "${center_x}" "${center_y}" "${center_z}" "${tries_per}"; do
  if ! [[ "${v}" =~ ^-?[0-9]+$ ]]; then
    echo "Invalid integer arg: ${v}" >&2
    exit 2
  fi
done

if [[ ! -f "${schematic}" ]]; then
  echo "Missing schematic: ${schematic}" >&2
  exit 2
fi

if [[ ! -f "./infra/world-height-at.py" ]]; then
  echo "Missing helper: ./infra/world-height-at.py" >&2
  exit 2
fi

if [[ ! -d "./data/world/region" ]]; then
  echo "World not found or not generated yet: ./data/world/region" >&2
  exit 2
fi

echo "== spawn windmills in plains =="
echo "schematic: ${schematic}"
echo "center: ${center_x} ${center_y} ${center_z}"
echo "count: ${count} radius: ${radius} min_dist: ${min_dist} tries_per: ${tries_per}"
echo "dry_run: ${dry_run}"

placed=() # "x y z"

min_dist_ok() {
  local x="${1:?}" z="${2:?}"
  if [[ "${#placed[@]}" -eq 0 ]]; then
    return 0
  fi
  # newline-separated list to python
  printf "%s\n" "${placed[@]}" | python3 - <<PY
import math, sys
min_dist=int("${min_dist}")
tx=int("${x}"); tz=int("${z}")
placed = sys.stdin.read().strip().splitlines()
for line in placed:
    if not line.strip():
        continue
    px, py, pz = map(int, line.split())
    if math.hypot(tx-px, tz-pz) < min_dist:
        sys.exit(1)
sys.exit(0)
PY
}

rand_point() {
  # Uniform-ish in square; good enough for sampling.
  python3 - <<PY
import random
cx=int("${center_x}"); cz=int("${center_z}"); r=int("${radius}")
print(cx + random.randint(-r, r), cz + random.randint(-r, r))
PY
}

locate_plains_from() {
  local sx="${1:?}" sz="${2:?}"
  local prev
  prev="$(docker logs cobblemon --tail 200 2>/dev/null | grep -F 'The nearest minecraft:plains is at [' | tail -n 1 || true)"
  docker exec -u 1000 cobblemon mc-send-to-console "execute positioned ${sx} 64 ${sz} run locate biome minecraft:plains" >/dev/null 2>&1 || true

  local line=""
  for _ in $(seq 1 40); do
    line="$(docker logs cobblemon --tail 200 2>/dev/null | grep -F 'The nearest minecraft:plains is at [' | tail -n 1 || true)"
    if [[ -n "${line}" && "${line}" != "${prev}" ]]; then
      break
    fi
    sleep 0.2
  done

  if [[ -z "${line}" || "${line}" == "${prev}" ]]; then
    return 1
  fi

  # Example:
  # [..] The nearest minecraft:plains is at [-448, 64, 576] (729 blocks away)
  python3 -c "import re,sys; s=sys.stdin.read(); m=re.search(r'at \\[(-?\\d+), (-?\\d+), (-?\\d+)\\]', s); print(f'{m.group(1)} {m.group(2)} {m.group(3)}' if m else '')" <<<"${line}"
}

height_at() {
  local x="${1:?}" z="${2:?}"
  python3 ./infra/world-height-at.py --world ./data/world --x "${x}" --z "${z}"
}

warm_chunk() {
  local x="${1:?}" z="${2:?}"
  docker exec -u 1000 cobblemon mc-send-to-console "forceload add ${x} ${z} ${x} ${z}" >/dev/null 2>&1 || true
  # Give the server a moment to generate/load, then flush so the region file is present for offline reads.
  sleep 2
  docker exec -u 1000 cobblemon mc-send-to-console "save-all flush" >/dev/null 2>&1 || true
}

for i in $(seq 1 "${count}"); do
  echo "-- placing ${i}/${count} --"
  ok="false"

  for _try in $(seq 1 "${tries_per}"); do
    read -r sx sz < <(rand_point)
    read -r px py pz < <(locate_plains_from "${sx}" "${sz}" || echo "")
    if [[ -z "${px:-}" || -z "${pz:-}" ]]; then
      continue
    fi

    # Keep placements within radius of center.
    if ! python3 -c "import math; cx=int('${center_x}'); cz=int('${center_z}'); r=int('${radius}'); px=int('${px}'); pz=int('${pz}'); raise SystemExit(0 if math.hypot(px-cx, pz-cz) <= r else 1)"; then
      continue
    fi

    if ! min_dist_ok "${px}" "${pz}"; then
      continue
    fi

    # Ensure the chunk exists on disk before height lookup.
    warm_chunk "${px}" "${pz}"

    gy="$(height_at "${px}" "${pz}" 2>/dev/null || true)"
    if [[ -z "${gy}" ]]; then
      continue
    fi

    # Paste origin Y so that (origin_y + WEOffsetY=-4) => base_y == ground_y.
    oy=$((gy + 4))

    echo "target: plains at ${px},${gy},${pz}"
    if [[ "${dry_run}" != "true" ]]; then
      ./infra/spawn-schematic-mcedit.sh \
        --schematic "${schematic}" \
        --at "${px}" "${oy}" "${pz}" \
        --dx 0 --dy 0 --dz 0 \
        --clear \
        >/dev/null 2>&1 || true
    fi

    placed+=("${px} ${gy} ${pz}")
    ok="true"
    break
  done

  if [[ "${ok}" != "true" ]]; then
    echo "WARN: failed to place windmill ${i}/${count} after ${tries_per} tries" >&2
  fi
done

echo "== placed =="
if [[ "${#placed[@]}" -eq 0 ]]; then
  echo "(none)"
else
  printf "%s\n" "${placed[@]}"
fi
echo "OK"
