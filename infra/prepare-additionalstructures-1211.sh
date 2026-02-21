#!/usr/bin/env bash
set -euo pipefail

# Normalizes Additional Structures datapack source for Minecraft 1.21.1 and
# enforces compatibility gates against the official 1.21.x Fabric v5.1.0 jar.
#
# Usage:
#   ./infra/prepare-additionalstructures-1211.sh
#   ./infra/prepare-additionalstructures-1211.sh --allow-changed
#   ./infra/prepare-additionalstructures-1211.sh --source ./downloads/additionalstructures_1211

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

SOURCE_DIR="${REPO_ROOT}/downloads/additionalstructures_1211"
REF_JAR="${REPO_ROOT}/downloads/AdditionalStructures-1.21.x-(v.5.1.0-fabric).jar"
OUT_DIR="${REPO_ROOT}/datapacks/additionalstructures_1211"
REPORT_ROOT="${REPO_ROOT}/reports/additionalstructures_1211"
ALLOW_CHANGED="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE_DIR="$(cd "$2" && pwd)"
      shift 2
      ;;
    --ref-jar)
      REF_JAR="$2"
      shift 2
      ;;
    --out)
      OUT_DIR="$2"
      shift 2
      ;;
    --allow-changed)
      ALLOW_CHANGED="true"
      shift
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "Missing source dir: ${SOURCE_DIR}" >&2
  exit 2
fi
if [[ ! -d "${SOURCE_DIR}/data" ]]; then
  echo "Missing source data dir: ${SOURCE_DIR}/data" >&2
  exit 2
fi
if [[ ! -f "${REF_JAR}" ]]; then
  echo "Missing reference jar: ${REF_JAR}" >&2
  exit 2
fi

ts="$(date +%Y%m%d-%H%M%S)"
REPORT_DIR="${REPORT_ROOT}/${ts}"
mkdir -p "${REPORT_DIR}"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

pybin="python3"
if ! command -v "${pybin}" >/dev/null 2>&1; then
  pybin="python"
fi

"${pybin}" - "${SOURCE_DIR}" "${REF_JAR}" "${tmp}" "${REPORT_DIR}" "${ALLOW_CHANGED}" <<'PY'
import filecmp
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

src = Path(sys.argv[1]).resolve()
ref_jar = Path(sys.argv[2]).resolve()
tmp = Path(sys.argv[3]).resolve()
report_dir = Path(sys.argv[4]).resolve()
allow_changed = sys.argv[5].lower() == "true"

stage = tmp / "stage"
stage_data = stage / "data"
stage_data.mkdir(parents=True, exist_ok=True)

def write_list(path: Path, values):
    path.write_text("\n".join(values) + ("\n" if values else ""), encoding="utf-8")

with zipfile.ZipFile(ref_jar, "r") as zf:
    ref_data = sorted(
        n for n in zf.namelist() if n.startswith("data/") and not n.endswith("/")
    )

src_data = src / "data"
src_files = sorted(
    str(p.relative_to(src)).replace("\\", "/")
    for p in src_data.rglob("*")
    if p.is_file()
)

ref_set = set(ref_data)
src_set = set(src_files)

extra = sorted(src_set - ref_set)
missing = sorted(ref_set - src_set)
common = sorted(ref_set & src_set)

changed = []
for rel in common:
    src_file = src / rel
    with zipfile.ZipFile(ref_jar, "r") as zf:
        jar_bytes = zf.read(rel)
    if src_file.read_bytes() != jar_bytes:
        changed.append(rel)
changed.sort()

write_list(report_dir / "extra.txt", extra)
write_list(report_dir / "missing.txt", missing)
write_list(report_dir / "changed.txt", changed)

if missing:
    print(f"ERROR: missing reference files: {len(missing)}", file=sys.stderr)
    sys.exit(10)
if changed and not allow_changed:
    print(
        f"ERROR: changed files vs reference: {len(changed)} (manual review required)",
        file=sys.stderr,
    )
    sys.exit(11)

for rel in ref_data:
    src_file = src / rel
    dst_file = stage / rel
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_file, dst_file)

json_files = sorted(stage_data.rglob("*.json"))
bad_json = []
bad_placeholder = []
bad_type = []
bad_element_type = []
pattern_ns = re.compile(r'"([a-z0-9_.-]+):([a-z0-9_./-]+)"')

allowed_non_ns_type = {"random_spread", "concentric_rings", "linear", "triangular"}

for jf in json_files:
    text = jf.read_text(encoding="utf-8")
    if "${" in text:
        bad_placeholder.append(str(jf.relative_to(stage)).replace("\\", "/"))
    try:
        obj = json.loads(text)
    except Exception:
        bad_json.append(str(jf.relative_to(stage)).replace("\\", "/"))
        continue
    for m in re.finditer(r'"type"\s*:\s*"([^"]+)"', text):
        val = m.group(1)
        if not (val.startswith("minecraft:") or val in allowed_non_ns_type):
            bad_type.append((str(jf.relative_to(stage)).replace("\\", "/"), val))
    for m in re.finditer(r'"element_type"\s*:\s*"([^"]+)"', text):
        val = m.group(1)
        if not val.startswith("minecraft:"):
            bad_element_type.append((str(jf.relative_to(stage)).replace("\\", "/"), val))

if bad_json:
    write_list(report_dir / "invalid_json.txt", bad_json)
if bad_placeholder:
    write_list(report_dir / "invalid_placeholders.txt", bad_placeholder)
if bad_type:
    write_list(
        report_dir / "invalid_type.txt",
        [f"{f} => {v}" for f, v in bad_type],
    )
if bad_element_type:
    write_list(
        report_dir / "invalid_element_type.txt",
        [f"{f} => {v}" for f, v in bad_element_type],
    )

if bad_json or bad_placeholder or bad_type or bad_element_type:
    print("ERROR: static JSON compatibility checks failed", file=sys.stderr)
    sys.exit(12)

base = stage / "data" / "additionalstructures"
missing_refs = []

for p in (base / "worldgen" / "structure_set").glob("*.json"):
    obj = json.loads(p.read_text(encoding="utf-8"))
    for it in obj.get("structures", []):
        sid = it.get("structure", "")
        if sid.startswith("additionalstructures:"):
            name = sid.split(":", 1)[1]
            if not (base / "worldgen" / "structure" / f"{name}.json").exists():
                missing_refs.append(f"{p.name} -> {sid}")

for p in (base / "worldgen" / "structure").glob("*.json"):
    obj = json.loads(p.read_text(encoding="utf-8"))
    sp = obj.get("start_pool", "")
    if sp.startswith("additionalstructures:"):
        name = sp.split(":", 1)[1]
        if not (base / "worldgen" / "template_pool" / f"{name}.json").exists():
            missing_refs.append(f"{p.name} -> {sp}")

for p in (base / "worldgen" / "template_pool").glob("*.json"):
    obj = json.loads(p.read_text(encoding="utf-8"))
    for el in obj.get("elements", []):
        loc = (((el or {}).get("element") or {}).get("location")) or ""
        if not isinstance(loc, str) or not loc.startswith("additionalstructures:"):
            continue
        name = loc.split(":", 1)[1]
        candidates = [name]
        if name.endswith(".json"):
            candidates.append(name[:-5])
        ok = any((base / "structure" / f"{c}.nbt").exists() for c in candidates)
        if not ok:
            missing_refs.append(f"{p.name} -> {loc}")

missing_refs = sorted(set(missing_refs))
write_list(report_dir / "missing_worldgen_refs.txt", missing_refs)
if missing_refs:
    print(f"ERROR: missing worldgen refs: {len(missing_refs)}", file=sys.stderr)
    sys.exit(13)

summary = {
    "reference_file_count": len(ref_data),
    "source_file_count": len(src_files),
    "extra_count": len(extra),
    "missing_count": len(missing),
    "changed_count": len(changed),
    "json_count": len(json_files),
    "worldgen_missing_ref_count": len(missing_refs),
}
(report_dir / "summary.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=True) + "\n",
    encoding="utf-8",
)
PY

mkdir -p "${REPO_ROOT}/backups/datapacks"
if [[ -d "${OUT_DIR}" ]]; then
  mv "${OUT_DIR}" "${REPO_ROOT}/backups/datapacks/additionalstructures_1211.src-prev-${ts}"
fi

mkdir -p "${OUT_DIR}"
cp -a "${tmp}/stage/data" "${OUT_DIR}/data"

cat > "${OUT_DIR}/pack.mcmeta" <<'EOF'
{
  "pack": {
    "description": "Additional Structures datapack (normalized for MC 1.21.1)",
    "pack_format": 48
  }
}
EOF

jar_sha1="$(sha1sum "${REF_JAR}" | awk '{print $1}')"
cat > "${OUT_DIR}/AS-SOURCE.lock" <<EOF
source_dir=${SOURCE_DIR}
reference_jar=${REF_JAR}
reference_jar_sha1=${jar_sha1}
generated_at=${ts}
report_dir=${REPORT_DIR}
policy_extra=excluded_by_default
policy_missing=blocking
policy_changed=manual_review_required
EOF

echo "Prepared datapack: ${OUT_DIR}"
echo "Report: ${REPORT_DIR}"
echo "OK"

