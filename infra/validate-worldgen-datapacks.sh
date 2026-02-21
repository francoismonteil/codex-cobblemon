#!/usr/bin/env bash
set -euo pipefail

# Strict validation for ACM + Additional Structures worldgen datapacks.
#
# Usage:
#   ./infra/validate-worldgen-datapacks.sh
#   ./infra/validate-worldgen-datapacks.sh --skip-restart

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

WORLD_DIR="${REPO_ROOT}/data/world"
AS_REPO="${REPO_ROOT}/datapacks/additionalstructures_1211"
ACM_REPO="${REPO_ROOT}/datapacks/acm_pokemon_worldgen"
AS_WORLD="${WORLD_DIR}/datapacks/additionalstructures_1211"
ACM_WORLD="${WORLD_DIR}/datapacks/acm_pokemon_worldgen"
skip_restart="false"
service_name="cobblemon"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-restart)
      skip_restart="true"
      shift
      ;;
    --service)
      service_name="$2"
      shift 2
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

for p in "${WORLD_DIR}" "${AS_REPO}" "${ACM_REPO}" "${AS_WORLD}" "${ACM_WORLD}"; do
  if [[ ! -d "${p}" ]]; then
    echo "Missing required dir: ${p}" >&2
    exit 2
  fi
done
if [[ ! -f "${AS_REPO}/pack.mcmeta" ]]; then
  echo "Missing AS pack.mcmeta: ${AS_REPO}/pack.mcmeta" >&2
  exit 2
fi

pybin="python3"
if ! command -v "${pybin}" >/dev/null 2>&1; then
  pybin="python"
fi

"${pybin}" - "${AS_REPO}" <<'PY'
import json
import re
import sys
from pathlib import Path

pack = Path(sys.argv[1]).resolve()
pack_mcmeta = pack / "pack.mcmeta"
obj = json.loads(pack_mcmeta.read_text(encoding="utf-8"))
pf = int(obj["pack"]["pack_format"])
if pf != 48:
    raise SystemExit(f"pack_format mismatch: expected 48, got {pf}")

json_files = sorted((pack / "data").rglob("*.json"))
for p in json_files:
    text = p.read_text(encoding="utf-8")
    if "${" in text:
        raise SystemExit(f"placeholder found: {p}")
    data = json.loads(text)
    for m in re.finditer(r'"type"\s*:\s*"([^"]+)"', text):
        v = m.group(1)
        if not (v.startswith("minecraft:") or v in {"random_spread", "concentric_rings", "linear", "triangular"}):
            raise SystemExit(f"non-vanilla type: {v} in {p}")
    for m in re.finditer(r'"element_type"\s*:\s*"([^"]+)"', text):
        v = m.group(1)
        if not v.startswith("minecraft:"):
            raise SystemExit(f"non-vanilla element_type: {v} in {p}")

base = pack / "data" / "additionalstructures"
for p in (base / "worldgen" / "structure_set").glob("*.json"):
    data = json.loads(p.read_text(encoding="utf-8"))
    for it in data.get("structures", []):
        sid = it.get("structure", "")
        if sid.startswith("additionalstructures:"):
            name = sid.split(":", 1)[1]
            if not (base / "worldgen" / "structure" / f"{name}.json").exists():
                raise SystemExit(f"missing structure ref: {sid} in {p.name}")

for p in (base / "worldgen" / "structure").glob("*.json"):
    data = json.loads(p.read_text(encoding="utf-8"))
    sp = data.get("start_pool", "")
    if sp.startswith("additionalstructures:"):
        name = sp.split(":", 1)[1]
        if not (base / "worldgen" / "template_pool" / f"{name}.json").exists():
            raise SystemExit(f"missing start_pool ref: {sp} in {p.name}")

for p in (base / "worldgen" / "template_pool").glob("*.json"):
    data = json.loads(p.read_text(encoding="utf-8"))
    for el in data.get("elements", []):
        loc = (((el or {}).get("element") or {}).get("location")) or ""
        if not isinstance(loc, str) or not loc.startswith("additionalstructures:"):
            continue
        name = loc.split(":", 1)[1]
        candidates = [name]
        if name.endswith(".json"):
            candidates.append(name[:-5])
        if not any((base / "structure" / f"{c}.nbt").exists() for c in candidates):
            raise SystemExit(f"missing nbt for template pool location: {loc} in {p.name}")

print("Static checks: OK")
PY

if [[ "${skip_restart}" != "true" ]]; then
  echo "Running safe restart for startup validation..."
  ./infra/safe-restart.sh
fi

sleep 3
log_tail="$(docker logs "${service_name}" --tail 800 2>&1 || true)"
printf '%s\n' "${log_tail}" > "${REPO_ROOT}/logs/validate-worldgen-datapacks.last.log"

if printf '%s\n' "${log_tail}" | grep -Eqi \
  "failed to load datapacks|error loading datapack|error loading registry data|couldn't parse data file|error loading data packs"; then
  echo "Detected datapack/worldgen load errors in recent logs." >&2
  echo "See: logs/validate-worldgen-datapacks.last.log" >&2
  exit 1
fi

echo "No datapack/worldgen load errors found in recent logs."
echo "Saved log snapshot: logs/validate-worldgen-datapacks.last.log"
echo
echo "Manual strict checks to run in-game (new chunks):"
echo "  /locate structure additionalstructures:well_1"
echo "  /locate structure additionalstructures:maya_temple"
echo "  /locate structure additionalstructures:tower_1"
echo "  /locate structure minecraft:village_plains"
echo "Then verify Pokemart presence in newly generated villages."
echo "OK"

