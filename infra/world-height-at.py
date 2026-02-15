#!/usr/bin/env python3
"""
Get surface height (Y) at a world (x,z) by reading the generated world data (Anvil .mca).

Why:
- We want to paste schematics onto terrain (eg plains) without relying on a player being online.
- Vanilla commands don't provide a clean "get heightmap y" output channel.

Implementation notes:
- Uses MOTION_BLOCKING_NO_LEAVES heightmap by default.
- Supports modern chunk NBT layouts (heightmaps at root) and legacy (under "Level").
- No external dependencies.

Examples:
  python3 infra/world-height-at.py --world ./data/world --x 0 --z 0
  python3 infra/world-height-at.py --world ./data/world --x -448 --z 576 --type MOTION_BLOCKING
"""

from __future__ import annotations

import argparse
import gzip
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# --- Minimal NBT reader (same style as other infra scripts; no external deps) ---
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


class NBTError(Exception):
    pass


class _Buf:
    __slots__ = ("b", "o")

    def __init__(self, b: bytes):
        self.b = b
        self.o = 0

    def read_u8(self) -> int:
        if self.o + 1 > len(self.b):
            raise NBTError("unexpected EOF")
        v = self.b[self.o]
        self.o += 1
        return v

    def read_i8(self) -> int:
        if self.o + 1 > len(self.b):
            raise NBTError("unexpected EOF")
        v = struct.unpack(">b", self.b[self.o : self.o + 1])[0]
        self.o += 1
        return v

    def read_i16(self) -> int:
        if self.o + 2 > len(self.b):
            raise NBTError("unexpected EOF")
        v = struct.unpack(">h", self.b[self.o : self.o + 2])[0]
        self.o += 2
        return v

    def read_i32(self) -> int:
        if self.o + 4 > len(self.b):
            raise NBTError("unexpected EOF")
        v = struct.unpack(">i", self.b[self.o : self.o + 4])[0]
        self.o += 4
        return v

    def read_i64(self) -> int:
        if self.o + 8 > len(self.b):
            raise NBTError("unexpected EOF")
        v = struct.unpack(">q", self.b[self.o : self.o + 8])[0]
        self.o += 8
        return v

    def read_bytes(self, n: int) -> bytes:
        if self.o + n > len(self.b):
            raise NBTError("unexpected EOF")
        v = self.b[self.o : self.o + n]
        self.o += n
        return v

    def read_string(self) -> str:
        ln = self.read_i16()
        if ln < 0:
            raise NBTError("negative string length")
        return self.read_bytes(ln).decode("utf-8", errors="strict")


def _read_tag_payload(tag: int, buf: _Buf):
    if tag == TAG_BYTE:
        return buf.read_i8()
    if tag == TAG_SHORT:
        return buf.read_i16()
    if tag == TAG_INT:
        return buf.read_i32()
    if tag == TAG_LONG:
        return buf.read_i64()
    if tag == TAG_FLOAT:
        buf.read_bytes(4)
        return None
    if tag == TAG_DOUBLE:
        buf.read_bytes(8)
        return None
    if tag == TAG_BYTE_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative byte array length")
        return buf.read_bytes(ln)
    if tag == TAG_STRING:
        return buf.read_string()
    if tag == TAG_LIST:
        inner = buf.read_u8()
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative list length")
        return [_read_tag_payload(inner, buf) for _ in range(ln)]
    if tag == TAG_COMPOUND:
        out = {}
        while True:
            t = buf.read_u8()
            if t == TAG_END:
                return out
            name = buf.read_string()
            out[name] = _read_tag_payload(t, buf)
    if tag == TAG_INT_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative int array length")
        return [struct.unpack(">i", buf.read_bytes(4))[0] for _ in range(ln)]
    if tag == TAG_LONG_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative long array length")
        return [struct.unpack(">q", buf.read_bytes(8))[0] for _ in range(ln)]
    raise NBTError(f"unknown tag {tag}")


def _load_nbt_bytes(raw: bytes) -> Dict:
    # Some payloads are gzipped; most region chunks are zlib.
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    buf = _Buf(raw)
    t = buf.read_u8()
    if t != TAG_COMPOUND:
        raise NBTError(f"unexpected root tag: {t} (expected compound)")
    _ = buf.read_string()
    root = _read_tag_payload(TAG_COMPOUND, buf)
    if not isinstance(root, dict):
        raise NBTError("root compound parse failed")
    return root


# --- Region file reader ---


@dataclass(frozen=True)
class ChunkRef:
    region_path: Path
    local_x: int
    local_z: int


def _region_path(world: Path, cx: int, cz: int) -> ChunkRef:
    rx = cx >> 5
    rz = cz >> 5
    local_x = cx & 31
    local_z = cz & 31
    p = world / "region" / f"r.{rx}.{rz}.mca"
    return ChunkRef(region_path=p, local_x=local_x, local_z=local_z)


def _read_chunk_nbt(world: Path, cx: int, cz: int) -> Dict:
    ref = _region_path(world, cx, cz)
    if not ref.region_path.exists():
        raise FileNotFoundError(f"Missing region file: {ref.region_path}")

    b = ref.region_path.read_bytes()
    if len(b) < 8192:
        raise NBTError(f"Invalid region file (too small): {ref.region_path}")

    idx = ref.local_x + ref.local_z * 32
    loc = struct.unpack(">I", b[idx * 4 : idx * 4 + 4])[0]
    off_sectors = (loc >> 8) & 0xFFFFFF
    sector_count = loc & 0xFF
    if off_sectors == 0 or sector_count == 0:
        raise NBTError(f"Chunk not present in region: cx={cx} cz={cz}")

    off = off_sectors * 4096
    if off + 5 > len(b):
        raise NBTError("Chunk offset out of bounds")

    length = struct.unpack(">I", b[off : off + 4])[0]
    compression = b[off + 4]
    payload = b[off + 5 : off + 4 + length]

    if compression == 1:
        raw = gzip.decompress(payload)
    elif compression == 2:
        raw = zlib.decompress(payload)
    elif compression == 3:
        raw = payload
    else:
        raise NBTError(f"Unknown compression type {compression}")

    return _load_nbt_bytes(raw)


# --- Heightmap decode ---


def _heightmap_get(hm_longs: List[int], x_in: int, z_in: int, bits: int = 9) -> int:
    """Return the packed height value for local (x,z) in a chunk.

    In modern versions, heightmaps store Y+1 (eg surface at y=120 => value 121).
    """

    idx = (z_in & 15) * 16 + (x_in & 15)
    bit_index = idx * bits
    long_index = bit_index >> 6
    start = bit_index & 63
    mask = (1 << bits) - 1

    # NBT longs are signed; treat them as unsigned 64-bit for bit packing.
    a0 = hm_longs[long_index] & ((1 << 64) - 1)
    v = (a0 >> start) & mask
    spill = start + bits - 64
    if spill > 0:
        a1 = hm_longs[long_index + 1] & ((1 << 64) - 1)
        v2 = a1 & ((1 << spill) - 1)
        v |= v2 << (bits - spill)
    return int(v)


def _chunk_heightmaps(root: Dict) -> Dict:
    # Modern: root["Heightmaps"]
    hm = root.get("Heightmaps")
    if isinstance(hm, dict):
        return hm
    # Legacy: root["Level"]["Heightmaps"]
    lvl = root.get("Level")
    if isinstance(lvl, dict):
        hm2 = lvl.get("Heightmaps")
        if isinstance(hm2, dict):
            return hm2
    raise NBTError("No Heightmaps compound found in chunk NBT")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Get surface Y at (x,z) by reading world region files (.mca).")
    ap.add_argument("--world", required=True, help="World folder (contains region/)")
    ap.add_argument("--x", required=True, type=int, help="World X (block)")
    ap.add_argument("--z", required=True, type=int, help="World Z (block)")
    ap.add_argument(
        "--min-y",
        type=int,
        default=-64,
        help="World minimum Y (default: -64 for modern worlds)",
    )
    ap.add_argument(
        "--type",
        default="MOTION_BLOCKING_NO_LEAVES",
        help="Heightmap type (default: MOTION_BLOCKING_NO_LEAVES)",
    )
    args = ap.parse_args(argv)

    world = Path(args.world)
    if not world.exists():
        print(f"Missing world folder: {world}", file=sys.stderr)
        return 2

    x = int(args.x)
    z = int(args.z)
    cx = x >> 4
    cz = z >> 4
    lx = x & 15
    lz = z & 15

    try:
        root = _read_chunk_nbt(world, cx, cz)
        hms = _chunk_heightmaps(root)
        hm_arr = hms.get(args.type)
        if not isinstance(hm_arr, list) or not hm_arr:
            raise NBTError(f"Heightmap missing or invalid: {args.type}")
        v = _heightmap_get(hm_arr, lx, lz, bits=9)
        # In modern Anvil, heightmap values are relative to the world's minimum Y.
        # y = (min_y + v) - 1
        y = args.min_y + v - 1
        print(y)
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
