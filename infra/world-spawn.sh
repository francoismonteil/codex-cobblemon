#!/usr/bin/env bash
set -euo pipefail

# Prints the world spawn coordinates from ./data/world/level.dat.
#
# Output:
#   x y z
#
# Usage:
#   ./infra/world-spawn.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

level="./data/world/level.dat"
if [[ ! -f "${level}" ]]; then
  echo "Missing ${level}" >&2
  exit 1
fi

python3 - <<'PY'
import gzip
import struct

PATH = "./data/world/level.dat"

class NBTError(Exception):
    pass

def read_u8(b, o): return b[o], o+1
def read_i16(b, o): return struct.unpack(">h", b[o:o+2])[0], o+2
def read_i32(b, o): return struct.unpack(">i", b[o:o+4])[0], o+4
def read_i64(b, o): return struct.unpack(">q", b[o:o+8])[0], o+8
def read_f32(b, o): return struct.unpack(">f", b[o:o+4])[0], o+4
def read_f64(b, o): return struct.unpack(">d", b[o:o+8])[0], o+8

def read_bytes(b, o, n):
    return b[o:o+n], o+n

def read_string(b, o):
    ln, o = read_i16(b, o)
    if ln < 0:
        raise NBTError("negative string length")
    s, o = read_bytes(b, o, ln)
    return s.decode("utf-8", errors="strict"), o

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12

def skip_payload(tag, b, o):
    if tag == TAG_BYTE:
        return o+1
    if tag == TAG_SHORT:
        return o+2
    if tag == TAG_INT:
        return o+4
    if tag == TAG_LONG:
        return o+8
    if tag == TAG_FLOAT:
        return o+4
    if tag == TAG_DOUBLE:
        return o+8
    if tag == TAG_BYTE_ARRAY:
        ln, o = read_i32(b, o)
        return o + ln
    if tag == TAG_STRING:
        _, o = read_string(b, o)
        return o
    if tag == TAG_LIST:
        inner, o = read_u8(b, o)
        ln, o = read_i32(b, o)
        for _ in range(max(0, ln)):
            o = skip_payload(inner, b, o)
        return o
    if tag == TAG_COMPOUND:
        while True:
            t, o = read_u8(b, o)
            if t == TAG_END:
                return o
            _, o = read_string(b, o)  # name
            o = skip_payload(t, b, o)
    if tag == TAG_INT_ARRAY:
        ln, o = read_i32(b, o)
        return o + 4 * ln
    if tag == TAG_LONG_ARRAY:
        ln, o = read_i32(b, o)
        return o + 8 * ln
    raise NBTError(f"unknown tag {tag}")

def find_spawn_xyz(b):
    # root: tag type + name + payload
    o = 0
    root_tag, o = read_u8(b, o)
    if root_tag != TAG_COMPOUND:
        raise NBTError("root is not a compound")
    _, o = read_string(b, o)  # root name

    # Scan for compound named "Data"
    while True:
        t, o = read_u8(b, o)
        if t == TAG_END:
            break
        name, o = read_string(b, o)
        if t == TAG_COMPOUND and name == "Data":
            # parse Data compound and pick SpawnX/Y/Z
            spawn = {}
            while True:
                tt, o = read_u8(b, o)
                if tt == TAG_END:
                    break
                n, o = read_string(b, o)
                if tt == TAG_INT and n in ("SpawnX", "SpawnY", "SpawnZ"):
                    v, o = read_i32(b, o)
                    spawn[n] = v
                else:
                    o = skip_payload(tt, b, o)
            if all(k in spawn for k in ("SpawnX", "SpawnY", "SpawnZ")):
                return spawn["SpawnX"], spawn["SpawnY"], spawn["SpawnZ"]
            break
        else:
            o = skip_payload(t, b, o)
    raise NBTError("SpawnX/SpawnY/SpawnZ not found")

with gzip.open(PATH, "rb") as f:
    raw = f.read()

x, y, z = find_spawn_xyz(raw)
print(f"{x} {y} {z}")
PY

