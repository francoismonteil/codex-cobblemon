#!/usr/bin/env python3
"""
Detect Pokemart marker presence density near world spawn.

Why:
- Village pools are probabilistic, so Pokemart presence in the first village is not guaranteed.
- We need a fast, deterministic check to decide whether to keep/regenerate a world.

How:
- Read spawn from level.dat
- Scan chunk section palettes in a radius around spawn
- Look for marker blocks that are used by Pokemart templates
- Group marker chunks into connected components (8-neighborhood) to approximate
  the number of distinct Pokemarts near spawn.

No external dependencies.
"""

from __future__ import annotations

import argparse
import gzip
import struct
import sys
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

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


def _skip_payload(tag: int, buf: _Buf) -> None:
    if tag == TAG_BYTE:
        buf.read_bytes(1)
        return
    if tag == TAG_SHORT:
        buf.read_bytes(2)
        return
    if tag == TAG_INT:
        buf.read_bytes(4)
        return
    if tag == TAG_LONG:
        buf.read_bytes(8)
        return
    if tag == TAG_FLOAT:
        buf.read_bytes(4)
        return
    if tag == TAG_DOUBLE:
        buf.read_bytes(8)
        return
    if tag == TAG_BYTE_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative byte array length")
        buf.read_bytes(ln)
        return
    if tag == TAG_STRING:
        _ = buf.read_string()
        return
    if tag == TAG_LIST:
        inner = buf.read_u8()
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative list length")
        for _ in range(ln):
            _skip_payload(inner, buf)
        return
    if tag == TAG_COMPOUND:
        while True:
            t = buf.read_u8()
            if t == TAG_END:
                return
            _ = buf.read_string()
            _skip_payload(t, buf)
    if tag == TAG_INT_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative int array length")
        buf.read_bytes(4 * ln)
        return
    if tag == TAG_LONG_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative long array length")
        buf.read_bytes(8 * ln)
        return
    raise NBTError(f"unknown tag {tag}")


def _read_payload(tag: int, buf: _Buf):
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
        return [_read_payload(inner, buf) for _ in range(ln)]
    if tag == TAG_COMPOUND:
        out = {}
        while True:
            t = buf.read_u8()
            if t == TAG_END:
                return out
            name = buf.read_string()
            out[name] = _read_payload(t, buf)
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


def _load_nbt(raw: bytes) -> Dict:
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    buf = _Buf(raw)
    root_tag = buf.read_u8()
    if root_tag != TAG_COMPOUND:
        raise NBTError(f"root is not compound (tag={root_tag})")
    _ = buf.read_string()
    root = _read_payload(TAG_COMPOUND, buf)
    if not isinstance(root, dict):
        raise NBTError("invalid root compound")
    return root


def read_spawn(world: Path) -> Tuple[int, int, int]:
    level_dat = world / "level.dat"
    if not level_dat.exists():
        raise FileNotFoundError(f"missing level.dat: {level_dat}")
    root = _load_nbt(level_dat.read_bytes())
    data = root.get("Data")
    if not isinstance(data, dict):
        raise NBTError("missing Data compound in level.dat")
    sx = data.get("SpawnX")
    sy = data.get("SpawnY")
    sz = data.get("SpawnZ")
    if not isinstance(sx, int) or not isinstance(sy, int) or not isinstance(sz, int):
        raise NBTError("SpawnX/SpawnY/SpawnZ missing in level.dat")
    return sx, sy, sz


def _read_chunk_raw(region_file: Path, local_x: int, local_z: int) -> Optional[bytes]:
    b = region_file.read_bytes()
    if len(b) < 8192:
        return None
    idx = local_x + local_z * 32
    loc = struct.unpack(">I", b[idx * 4 : idx * 4 + 4])[0]
    off_sectors = (loc >> 8) & 0xFFFFFF
    sector_count = loc & 0xFF
    if off_sectors == 0 or sector_count == 0:
        return None
    off = off_sectors * 4096
    if off + 5 > len(b):
        return None
    length = struct.unpack(">I", b[off : off + 4])[0]
    compression = b[off + 4]
    payload = b[off + 5 : off + 4 + length]
    if compression == 1:
        return gzip.decompress(payload)
    if compression == 2:
        return zlib.decompress(payload)
    if compression == 3:
        return payload
    return None


def _chunk_palette_markers(chunk_root: Dict, markers: Set[str]) -> Set[str]:
    sections = chunk_root.get("sections")
    if not isinstance(sections, list):
        level = chunk_root.get("Level")
        if isinstance(level, dict):
            sections = level.get("Sections")
    if not isinstance(sections, list):
        return set()

    found: Set[str] = set()
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        block_states = sec.get("block_states")
        if not isinstance(block_states, dict):
            continue
        palette = block_states.get("palette")
        if not isinstance(palette, list):
            continue
        for entry in palette:
            if not isinstance(entry, dict):
                continue
            name = entry.get("Name")
            if isinstance(name, str) and name in markers:
                found.add(name)
    return found


def detect_markers_near_spawn(world: Path, radius: int, markers: Set[str]) -> Tuple[Tuple[int, int, int], List[Tuple[int, int, Set[str]]]]:
    sx, sy, sz = read_spawn(world)
    min_x = sx - radius
    max_x = sx + radius
    min_z = sz - radius
    max_z = sz + radius
    min_cx = min_x // 16
    max_cx = max_x // 16
    min_cz = min_z // 16
    max_cz = max_z // 16

    region_dir = world / "region"
    hits: List[Tuple[int, int, Set[str]]] = []

    for cx in range(min_cx, max_cx + 1):
        for cz in range(min_cz, max_cz + 1):
            rx = cx >> 5
            rz = cz >> 5
            lx = cx & 31
            lz = cz & 31
            rp = region_dir / f"r.{rx}.{rz}.mca"
            if not rp.exists():
                continue
            raw = _read_chunk_raw(rp, lx, lz)
            if raw is None:
                continue
            try:
                root = _load_nbt(raw)
            except Exception:
                continue
            found = _chunk_palette_markers(root, markers)
            if found:
                hits.append((cx, cz, found))

    return (sx, sy, sz), hits


def _cluster_hit_chunks(hits: List[Tuple[int, int, Set[str]]]) -> List[Tuple[List[Tuple[int, int]], Set[str]]]:
    by_coord: Dict[Tuple[int, int], Set[str]] = {}
    for cx, cz, found in hits:
        by_coord.setdefault((cx, cz), set()).update(found)

    remaining: Set[Tuple[int, int]] = set(by_coord.keys())
    components: List[Tuple[List[Tuple[int, int]], Set[str]]] = []

    while remaining:
        start = remaining.pop()
        stack = [start]
        coords: List[Tuple[int, int]] = [start]
        comp_markers: Set[str] = set(by_coord[start])

        while stack:
            x, z = stack.pop()
            for nx in range(x - 1, x + 2):
                for nz in range(z - 1, z + 2):
                    key = (nx, nz)
                    if key in remaining:
                        remaining.remove(key)
                        stack.append(key)
                        coords.append(key)
                        comp_markers.update(by_coord[key])

        components.append((coords, comp_markers))

    components.sort(
        key=lambda c: (
            -len(c[0]),
            min(cx for cx, _ in c[0]),
            min(cz for _, cz in c[0]),
        )
    )
    return components


def main(argv: Sequence[str]) -> int:
    ap = argparse.ArgumentParser(description="Detect Pokemart markers near world spawn.")
    ap.add_argument("--world", default="./data/world", help="World directory (default: ./data/world)")
    ap.add_argument("--radius", type=int, default=256, help="Scan radius in blocks around spawn (default: 256)")
    ap.add_argument(
        "--markers",
        default="cobblemon:blue_plaque,cobblemon:saccharine_wall_hanging_sign,cobblemon:saccharine_hanging_sign",
        help="Comma-separated marker block ids",
    )
    ap.add_argument(
        "--min-components",
        type=int,
        default=1,
        help="Minimum connected marker components required to succeed (default: 1)",
    )
    ap.add_argument(
        "--max-components",
        type=int,
        default=None,
        help="Maximum connected marker components allowed to succeed (default: no max)",
    )
    args = ap.parse_args(argv)

    world = Path(args.world)
    marker_set = {m.strip() for m in args.markers.split(",") if m.strip()}
    if not marker_set:
        print("ERROR: no markers provided", file=sys.stderr)
        return 2
    if args.min_components < 0:
        print("ERROR: --min-components must be >= 0", file=sys.stderr)
        return 2
    if args.max_components is not None and args.max_components < 0:
        print("ERROR: --max-components must be >= 0", file=sys.stderr)
        return 2
    if args.max_components is not None and args.max_components < args.min_components:
        print("ERROR: --max-components must be >= --min-components", file=sys.stderr)
        return 2

    try:
        spawn, hits = detect_markers_near_spawn(world, args.radius, marker_set)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    sx, sy, sz = spawn
    print(f"spawn: {sx} {sy} {sz}")
    print(f"radius: {args.radius}")
    print(f"markers: {','.join(sorted(marker_set))}")
    print(f"hit_chunks: {len(hits)}")
    components = _cluster_hit_chunks(hits)
    print(f"hit_components: {len(components)}")
    for cx, cz, found in hits[:12]:
        print(f"  chunk {cx} {cz}: {','.join(sorted(found))}")

    for i, (coords, found_markers) in enumerate(components[:8], start=1):
        min_cx = min(cx for cx, _ in coords)
        max_cx = max(cx for cx, _ in coords)
        min_cz = min(cz for _, cz in coords)
        max_cz = max(cz for _, cz in coords)
        print(
            f"  component {i}: chunks={len(coords)} span=({min_cx},{min_cz})..({max_cx},{max_cz}) markers={','.join(sorted(found_markers))}"
        )

    ok = len(components) >= args.min_components
    if args.max_components is not None:
        ok = ok and (len(components) <= args.max_components)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
