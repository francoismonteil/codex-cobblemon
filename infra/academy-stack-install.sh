#!/usr/bin/env bash
set -euo pipefail

# Install the pinned Academy-compatible server mods from modpack/academy-v2/stack.lock.json.
#
# Usage:
#   ./infra/academy-stack-install.sh --group core
#   ./infra/academy-stack-install.sh --group gyms --group dimension
#   ./infra/academy-stack-install.sh --all
#   ./infra/academy-stack-install.sh --all --dry-run

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

LOCK_PATH="${REPO_ROOT}/modpack/academy-v2/stack.lock.json"
MODS_DIR="${REPO_ROOT}/data/mods"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

verify_hash() {
  local file="$1"
  local algo="$2"
  local expected="$3"

  python3 - "$file" "$algo" "$expected" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
algo = sys.argv[2]
expected = sys.argv[3].lower()
h = hashlib.new(algo)
with path.open("rb") as fh:
    for chunk in iter(lambda: fh.read(1024 * 1024), b""):
        h.update(chunk)
actual = h.hexdigest().lower()
if actual != expected:
    raise SystemExit(1)
PY
}

GROUP_ARGS=()
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --group)
      GROUP_ARGS+=("${2:?missing group name}")
      shift 2
      ;;
    --all)
      GROUP_ARGS=("core" "gyms" "dimension")
      shift
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--group core|gyms|dimension] [--all] [--dry-run]" >&2
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 [--group core|gyms|dimension] [--all] [--dry-run]" >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "${LOCK_PATH}" ]]; then
  echo "Missing lock file: ${LOCK_PATH}" >&2
  exit 2
fi

if [[ ${#GROUP_ARGS[@]} -eq 0 ]]; then
  GROUP_ARGS=("core")
fi

need_cmd curl
need_cmd python3

mkdir -p "${MODS_DIR}"

mapfile -t INSTALL_LINES < <(
  python3 - "${LOCK_PATH}" "${GROUP_ARGS[@]}" <<'PY'
import json
import sys
from pathlib import Path

lock = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
requested_groups = sys.argv[2:]
allowed = {"viable_as_is", "viable_with_simple_config"}

selected_ids = []
for group in requested_groups:
    members = lock["install_groups"].get(group)
    if members is None:
        raise SystemExit(f"Unknown install group: {group}")
    selected_ids.extend(members)

components = {component["id"]: component for component in lock["components"]}
seen = set()
for component_id in selected_ids:
    if component_id in seen:
        continue
    seen.add(component_id)
    component = components[component_id]
    if component["status"] not in allowed:
        continue
    artifact = component.get("artifact")
    if not artifact:
        continue
    hashes = artifact.get("hashes", {})
    algo = "sha512" if "sha512" in hashes else "sha1"
    print("\t".join([
        component["id"],
        component["name"],
        artifact["filename"],
        artifact["download_url"],
        algo,
        hashes[algo],
        component["status"],
    ]))
PY
)

if [[ ${#INSTALL_LINES[@]} -eq 0 ]]; then
  echo "Nothing to install for groups: ${GROUP_ARGS[*]}" >&2
  exit 1
fi

for line in "${INSTALL_LINES[@]}"; do
  IFS=$'\t' read -r component_id component_name filename url algo expected status <<<"${line}"
  dst="${MODS_DIR}/${filename}"

  if [[ -f "${dst}" ]] && verify_hash "${dst}" "${algo}" "${expected}"; then
    echo "OK ${component_name} already installed: ${dst}"
    continue
  fi

  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "DRY-RUN ${component_id} ${filename} ${url}"
    continue
  fi

  tmp="$(mktemp)"
  trap 'rm -f "${tmp}"' RETURN
  echo "== Installing ${component_name} (${status}) =="
  curl -fsSL --retry 3 --retry-delay 2 -o "${tmp}" "${url}"
  verify_hash "${tmp}" "${algo}" "${expected}"
  mv -f "${tmp}" "${dst}"
  trap - RETURN
  echo "OK installed ${component_name}: ${dst}"
done

cat <<'EOF'
Done.

Next steps:
  1. Run ./infra/academy-compat-audit.py and keep the report in audit/
  2. Stage configs and quest content before public rollout
  3. Restart the server with ./infra/safe-restart.sh --force
EOF
