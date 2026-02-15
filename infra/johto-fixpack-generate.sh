#!/usr/bin/env bash
set -euo pipefail

# Generates a small "fix" datapack to make Cobblemon Johto work on a standard server:
# - Adds NPC alias json files so mcfunctions using short IDs (e.g. "weekday_monica") resolve.
# - Provides missing npc preset file (trainer_basics).
# - Overrides a few mcfunctions that reference optional mods/commands not present by default.
#
# This avoids editing the original CobblemonJohto.zip.
#
# Usage (on server):
#   ./infra/johto-fixpack-generate.sh
#
# Optional env:
#   JOHTO_ZIP=/path/to/CobblemonJohto.zip
#   JOHTO_FIXPACK_DIR=/data/world/datapacks/JohtoFixes
#   JOHTO_RELOAD=true|false (default true)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

JOHTO_ZIP="${JOHTO_ZIP:-./data/world/datapacks/CobblemonJohto.zip}"
JOHTO_FIXPACK_DIR="${JOHTO_FIXPACK_DIR:-./data/world/datapacks/JohtoFixes}"
JOHTO_RELOAD="${JOHTO_RELOAD:-true}"

if [[ ! -f "${JOHTO_ZIP}" ]]; then
  echo "Missing Johto datapack zip: ${JOHTO_ZIP}" >&2
  exit 1
fi

rm -rf "${JOHTO_FIXPACK_DIR}"
mkdir -p "${JOHTO_FIXPACK_DIR}"

cat >"${JOHTO_FIXPACK_DIR}/pack.mcmeta" <<'EOF'
{
  "pack": {
    "pack_format": 48,
    "description": "Johto fixes (generated)"
  }
}
EOF

# Pass paths explicitly to avoid any env oddities.
JOHTO_ZIP="${JOHTO_ZIP}" JOHTO_FIXPACK_DIR="${JOHTO_FIXPACK_DIR}" python3 - <<'PY'
import os
import re
import zipfile
from pathlib import Path

ZIP = Path(os.environ.get("JOHTO_ZIP", "./data/world/datapacks/CobblemonJohto.zip")).resolve()
OUT = Path(os.environ.get("JOHTO_FIXPACK_DIR", "./data/world/datapacks/JohtoFixes")).resolve()

z = zipfile.ZipFile(str(ZIP))

def write_text(rel, text):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", errors="strict")

def write_bytes(rel, b):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b)

def read_zip_text(name):
    return z.read(name).decode("utf-8", "ignore")

def list_zip(prefix, suffix=None):
    for n in z.namelist():
        if n.startswith(prefix) and (suffix is None or n.endswith(suffix)):
            yield n

# 1) Collect short NPC IDs used by mcfunctions: npcspawnat/spawnnpcat ... <id> ...
npc_ids = set()
cmd_re = re.compile(r"\b(?:npcspawnat|spawnnpcat)\b\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+([A-Za-z0-9_\-\.]+)")

for fn in list_zip("data/johto/function/", ".mcfunction"):
    for line in read_zip_text(fn).splitlines():
        m = cmd_re.search(line)
        if m:
            npc_ids.add(m.group(4))

# 2) Map short IDs -> source NPC json (by basename match) inside the Johto datapack.
src_by_id = {}
for n in list_zip("data/cobblemon/npcs/", ".json"):
    base = Path(n).name
    if base.endswith(".json"):
        sid = base[:-5]
        # Prefer first match; duplicates are unlikely and basename-only is how the map references them.
        src_by_id.setdefault(sid, n)

missing = sorted([i for i in npc_ids if i not in src_by_id])
found = sorted([i for i in npc_ids if i in src_by_id])

# 3) Write alias NPC json files at root: data/cobblemon/npcs/<id>.json
for i in found:
    write_bytes(f"data/cobblemon/npcs/{i}.json", z.read(src_by_id[i]))

# 4) Provide missing NPC preset (trainer_basics) expected by some trader NPCs.
behavior_src = "data/cobblemon/behaviors/trainer_basics.json"
if behavior_src in z.namelist():
    write_bytes("data/cobblemon/npc_preset/trainer_basics.json", z.read(behavior_src))

# 5) Override: johto:tools/reload (referenced by minecraft:load tag)
write_text("data/johto/function/tools/reload.mcfunction", "# Johto fixpack: stub reload function (was missing)\\n")

# 6) Override: remove 'givemark' lines that fail on servers without that command.
dialogue_src = "data/johto/function/dialogue/dialogue.mcfunction"
if dialogue_src in z.namelist():
    lines = read_zip_text(dialogue_src).splitlines()
    patched = []
    for ln in lines:
        if " givemark " in ln or ln.strip().startswith("givemark "):
            patched.append("# Johto fixpack: removed unsupported command: " + ln)
        else:
            patched.append(ln)
    write_text("data/johto/function/dialogue/dialogue.mcfunction", "\n".join(patched) + "\n")

# 7) Override: optional side-mod integrations that error if mods aren't installed.
write_text("data/johto/function/spawn/travelersbackpack.mcfunction", "# Johto fixpack: Travelers Backpack not installed (noop)\\n")
write_text("data/johto/function/spawn/pokemonhome.mcfunction", "# Johto fixpack: Cobblemon Home not installed (noop)\\n")

print(f"fixpack_out={OUT}")
print(f"npc_ids_total={len(npc_ids)} npc_alias_written={len(found)} npc_missing={len(missing)}")
if missing:
    print("npc_missing_ids=" + ",".join(missing[:50]))
PY

if [[ "${JOHTO_RELOAD}" == "true" ]]; then
  # Reload datapacks so fixes apply immediately.
  ./infra/mc.sh "reload" || true
fi

echo "Generated: ${JOHTO_FIXPACK_DIR}"
