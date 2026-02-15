#!/usr/bin/env bash

# Shared helpers for building "prefabs" via vanilla server console commands.
# Intended to be sourced by scripts in infra/.

prefab_cmd() {
  local command="${1:?}"
  ./infra/mc.sh "${command}" >/dev/null
  sleep "${PREFAB_CMD_SLEEP:-0.18}"
}

prefab_cmd_try() {
  local command="${1:?}"
  if ! ./infra/mc.sh "${command}" >/dev/null 2>&1; then
    echo "WARN: mc command failed: ${command}" >&2
  fi
  sleep "${PREFAB_CMD_SLEEP:-0.18}"
}

prefab_dir_opposite() {
  case "${1:?}" in
    north) echo "south" ;;
    south) echo "north" ;;
    east) echo "west" ;;
    west) echo "east" ;;
    *) return 1 ;;
  esac
}

prefab_dir_rotate_cw() {
  case "${1:?}" in
    north) echo "east" ;;
    east) echo "south" ;;
    south) echo "west" ;;
    west) echo "north" ;;
    *) return 1 ;;
  esac
}

prefab_snap_rect_floor() {
  python3 - "$@" <<'PY'
import math
import sys
from collections import Counter

vals = list(map(float, sys.argv[1:]))
if len(vals) != 12:
    raise SystemExit("expected 12 numbers (4 corners x/y/z)")

pts = [(vals[i], vals[i + 1], vals[i + 2]) for i in range(0, 12, 3)]

sx = [math.floor(p[0]) for p in pts]
sy = [math.floor(p[1]) for p in pts]
sz = [math.floor(p[2]) for p in pts]

minx, maxx = min(sx), max(sx)
minz, maxz = min(sz), max(sz)

# Use the most common Y (or min if tie).
cy = Counter(sy).most_common()
y = sorted([v for v, c in cy if c == cy[0][1]])[0]

print(minx, maxx, y, minz, maxz)
PY
}

prefab_snap_point_floor() {
  python3 - "$@" <<'PY'
import math
import sys

vals = list(map(float, sys.argv[1:]))
if len(vals) != 3:
    raise SystemExit("expected 3 numbers (x y z)")

x, y, z = vals
print(math.floor(x), math.floor(y), math.floor(z))
PY
}

# Computes a simple local coordinate system for a rectangular footprint, based on which
# side is the "front" (entrance) via --facing.
#
# Output (space-separated):
#   ax az width depth dx_right dz_right dx_fwd dz_fwd in_dir right_dir
#
# Local coords:
# - u: 0..width-1 (left->right when looking into the building from outside)
# - v: 0..depth-1 (front->back, into the building)
prefab_local_axes() {
  local facing="${1:?}" X1="${2:?}" X2="${3:?}" Z1="${4:?}" Z2="${5:?}"
  local DX=$((X2 - X1 + 1))
  local DZ=$((Z2 - Z1 + 1))

  local in_dir right_dir
  in_dir="$(prefab_dir_opposite "${facing}")"
  right_dir="$(prefab_dir_rotate_cw "${in_dir}")"

  # Anchor is the "front-left" corner from the outside perspective.
  case "${facing}" in
    north)
      # Front is Z1, into building is +Z, right is -X.
      echo "${X2} ${Z1} ${DX} ${DZ} -1 0 0 1 ${in_dir} ${right_dir}"
      ;;
    south)
      # Front is Z2, into building is -Z, right is +X.
      echo "${X1} ${Z2} ${DX} ${DZ} 1 0 0 -1 ${in_dir} ${right_dir}"
      ;;
    west)
      # Front is X1, into building is +X, right is +Z.
      echo "${X1} ${Z1} ${DZ} ${DX} 0 1 1 0 ${in_dir} ${right_dir}"
      ;;
    east)
      # Front is X2, into building is -X, right is -Z.
      echo "${X2} ${Z2} ${DZ} ${DX} 0 -1 -1 0 ${in_dir} ${right_dir}"
      ;;
    *)
      return 1
      ;;
  esac
}

prefab_l2w_point_xz() {
  local ax="${1:?}" az="${2:?}" dxr="${3:?}" dzr="${4:?}" dxf="${5:?}" dzf="${6:?}" u="${7:?}" v="${8:?}"
  local x=$((ax + u * dxr + v * dxf))
  local z=$((az + u * dzr + v * dzf))
  echo "${x} ${z}"
}

prefab_l2w_rect_xz() {
  local ax="${1:?}" az="${2:?}" dxr="${3:?}" dzr="${4:?}" dxf="${5:?}" dzf="${6:?}" u1="${7:?}" v1="${8:?}" u2="${9:?}" v2="${10:?}"

  local x1=$((ax + u1 * dxr + v1 * dxf))
  local z1=$((az + u1 * dzr + v1 * dzf))
  local x2=$((ax + u2 * dxr + v2 * dxf))
  local z2=$((az + u2 * dzr + v2 * dzf))

  if (( x1 > x2 )); then local t="${x1}"; x1="${x2}"; x2="${t}"; fi
  if (( z1 > z2 )); then local t="${z1}"; z1="${z2}"; z2="${t}"; fi

  echo "${x1} ${z1} ${x2} ${z2}"
}
