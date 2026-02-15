#!/usr/bin/env bash
set -euo pipefail

# Build the windmill structure template NBT for the datapack from the local (gitignored) schematic.
#
# Expected schematic path (gitignored): downloads/Windmill - (mcbuild_org).schematic
# Output: datapacks/acm_windmills/data/acm/structure/windmill.nbt

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

schematic="downloads/Windmill - (mcbuild_org).schematic"
out="datapacks/acm_windmills/data/acm/structure/windmill.nbt"
out_alias="datapacks/acm_windmills/data/acm/structure/windmill_template.nbt"

usage() {
  cat <<EOF >&2
Usage:
  $0 [--schematic <path>] [--output <path>]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --schematic) schematic="${2:?}"; shift 2;;
    --output) out="${2:?}"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2;;
  esac
done

if [[ ! -f "${schematic}" ]]; then
  echo "Missing schematic: ${schematic}" >&2
  echo "Place it under ./downloads/ (gitignored), then rerun." >&2
  exit 2
fi

python3 ./infra/schematic-mcedit-to-structure-nbt.py --schematic "${schematic}" --output "${out}"
cp -f "${out}" "${out_alias}"
echo "OK: wrote ${out}"
