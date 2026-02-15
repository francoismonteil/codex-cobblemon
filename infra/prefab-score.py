#!/usr/bin/env python3
#
# Prefab quality scoring (playability + aesthetics) by reading the live world on disk.
# No external dependencies: parses Anvil region files (.mca) and chunk NBT.
#
# This tool is designed for the server host (repo root), and can optionally emit a
# short in-game chat summary via ./infra/mc.sh.

from __future__ import annotations

import argparse
import collections
import gzip
import json
import math
import struct
import subprocess
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SECTOR_BYTES = 4096
REGION_HEADER_BYTES = SECTOR_BYTES * 2  # locations + timestamps

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
        s = self.read_bytes(ln)
        return s.decode("utf-8", errors="strict")


def _skip_tag_payload(tag: int, buf: _Buf) -> None:
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
            _skip_tag_payload(inner, buf)
        return
    if tag == TAG_COMPOUND:
        while True:
            t = buf.read_u8()
            if t == TAG_END:
                return
            _ = buf.read_string()  # name
            _skip_tag_payload(t, buf)
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
        # We don't need float for scoring; read as bytes and return None to keep memory down.
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


def _nibble(arr: Optional[bytes], idx: int) -> int:
    if not arr:
        return 0
    b = arr[idx >> 1]
    if idx & 1:
        return (b >> 4) & 0x0F
    return b & 0x0F


LIGHT_NIBBLE_BYTES = 2048  # 4096 nibbles for a 16x16x16 section


def _light_arr_ok(arr: Optional[bytes]) -> bool:
    return arr is not None and len(arr) >= LIGHT_NIBBLE_BYTES


@dataclass
class Section:
    y: int  # section Y (world_y >> 4)
    palette: List[str]
    data: Optional[List[int]]  # unsigned 64-bit values
    block_light: Optional[bytes]
    sky_light: Optional[bytes]

    @property
    def bits(self) -> int:
        n = len(self.palette)
        if n <= 1:
            return 0
        return max(4, (n - 1).bit_length())

    def palette_index(self, idx: int) -> int:
        if self.data is None:
            return 0
        bits = self.bits
        if bits <= 0:
            return 0
        # Mojang's BitStorage packs an integer number of entries per long
        # (values_per_long = floor(64/bits)), leaving padding bits at the end.
        values_per_long = 64 // bits
        if values_per_long <= 0:
            return 0
        li = idx // values_per_long
        if li < 0 or li >= len(self.data):
            return 0
        off = (idx % values_per_long) * bits
        mask = (1 << bits) - 1
        return (self.data[li] >> off) & mask

    def block_name(self, lx: int, ly: int, lz: int) -> str:
        idx = (ly << 8) | (lz << 4) | lx
        pi = self.palette_index(idx)
        if pi < 0 or pi >= len(self.palette):
            return "minecraft:air"
        return self.palette[pi]

    def light_value(self, lx: int, ly: int, lz: int, *, require_sky: bool) -> Optional[int]:
        idx = (ly << 8) | (lz << 4) | lx
        if not _light_arr_ok(self.block_light):
            return None
        if require_sky and not _light_arr_ok(self.sky_light):
            return None

        bl = _nibble(self.block_light, idx)
        sl = _nibble(self.sky_light, idx) if _light_arr_ok(self.sky_light) else 0
        return bl if bl >= sl else sl


@dataclass
class Chunk:
    cx: int
    cz: int
    is_light_on: bool
    sections: Dict[int, Section]

    def block_name(self, x: int, y: int, z: int) -> str:
        sy = y >> 4
        sec = self.sections.get(sy)
        if sec is None:
            return "minecraft:air"
        lx = x - (self.cx << 4)
        lz = z - (self.cz << 4)
        ly = y - (sy << 4)
        if not (0 <= lx <= 15 and 0 <= ly <= 15 and 0 <= lz <= 15):
            return "minecraft:air"
        return sec.block_name(lx, ly, lz)

    def light(self, x: int, y: int, z: int) -> int:
        v, ok = self.light_info(x, y, z, require_sky=True)
        if not ok or v is None:
            return 0
        return v

    def light_info(self, x: int, y: int, z: int, *, require_sky: bool) -> Tuple[Optional[int], bool]:
        """
        Returns (light_level, reliable).

        Reliable means:
        - chunk isLightOn == true AND
        - section contains BlockLight, and SkyLight when required (dimension dependent).
        """
        if not self.is_light_on:
            return None, False

        sy = y >> 4
        sec = self.sections.get(sy)
        if sec is None:
            return None, False

        lx = x - (self.cx << 4)
        lz = z - (self.cz << 4)
        ly = y - (sy << 4)
        if not (0 <= lx <= 15 and 0 <= ly <= 15 and 0 <= lz <= 15):
            return None, False

        v = sec.light_value(lx, ly, lz, require_sky=require_sky)
        if v is None:
            return None, False
        return v, True


class RegionFile:
    def __init__(self, path: Path):
        self.path = path
        with path.open("rb") as f:
            hdr = f.read(REGION_HEADER_BYTES)
        if len(hdr) < REGION_HEADER_BYTES:
            raise RuntimeError(f"short region header: {path}")
        self._locations = hdr[:SECTOR_BYTES]

    def read_chunk_nbt(self, cx: int, cz: int) -> Optional[bytes]:
        rx = cx // 32
        rz = cz // 32
        lcx = cx - rx * 32
        lcz = cz - rz * 32
        idx = lcx + lcz * 32
        loc = self._locations[idx * 4 : idx * 4 + 4]
        offset = (loc[0] << 16) | (loc[1] << 8) | loc[2]
        if offset == 0:
            return None

        with self.path.open("rb") as f:
            f.seek(offset * SECTOR_BYTES)
            length = struct.unpack(">I", f.read(4))[0]
            ctype = f.read(1)[0]
            data = f.read(length - 1)

        if ctype == 1:
            return gzip.decompress(data)
        if ctype == 2:
            return zlib.decompress(data)
        raise RuntimeError(f"unknown chunk compression type {ctype} in {self.path}")


def _parse_chunk(raw: bytes) -> Chunk:
    buf = _Buf(raw)
    root_t = buf.read_u8()
    if root_t != TAG_COMPOUND:
        raise NBTError("chunk root is not a compound")
    _ = buf.read_string()  # root name (often empty)

    out = {"sections": []}
    while True:
        t = buf.read_u8()
        if t == TAG_END:
            break
        name = buf.read_string()

        if name == "xPos" and t == TAG_INT:
            out["xPos"] = buf.read_i32()
            continue
        if name == "zPos" and t == TAG_INT:
            out["zPos"] = buf.read_i32()
            continue
        if name == "isLightOn" and t == TAG_BYTE:
            out["isLightOn"] = buf.read_i8()
            continue

        if name != "sections" or t != TAG_LIST:
            _skip_tag_payload(t, buf)
            continue

        inner = buf.read_u8()
        ln = buf.read_i32()
        if inner != TAG_COMPOUND:
            for _ in range(max(0, ln)):
                _skip_tag_payload(inner, buf)
            continue

        for _ in range(max(0, ln)):
            sec = {}
            while True:
                tt = buf.read_u8()
                if tt == TAG_END:
                    break
                nn = buf.read_string()
                if nn == "Y" and tt == TAG_BYTE:
                    sec["Y"] = buf.read_i8()
                    continue
                if nn == "BlockLight" and tt == TAG_BYTE_ARRAY:
                    sec["BlockLight"] = _read_tag_payload(tt, buf)
                    continue
                if nn == "SkyLight" and tt == TAG_BYTE_ARRAY:
                    sec["SkyLight"] = _read_tag_payload(tt, buf)
                    continue
                if nn == "block_states" and tt == TAG_COMPOUND:
                    bs = {}
                    while True:
                        bt = buf.read_u8()
                        if bt == TAG_END:
                            break
                        bn = buf.read_string()
                        if bn == "palette" and bt == TAG_LIST:
                            p_inner = buf.read_u8()
                            p_ln = buf.read_i32()
                            palette: List[str] = []
                            if p_inner == TAG_COMPOUND:
                                for _p in range(max(0, p_ln)):
                                    name_val: Optional[str] = None
                                    while True:
                                        pt = buf.read_u8()
                                        if pt == TAG_END:
                                            break
                                        pn = buf.read_string()
                                        if pn == "Name" and pt == TAG_STRING:
                                            name_val = buf.read_string()
                                        else:
                                            _skip_tag_payload(pt, buf)
                                    palette.append(name_val or "minecraft:air")
                            else:
                                for _p in range(max(0, p_ln)):
                                    _skip_tag_payload(p_inner, buf)
                            bs["palette"] = palette
                            continue
                        if bn == "data" and bt == TAG_LONG_ARRAY:
                            arr = _read_tag_payload(bt, buf)
                            # store as unsigned 64-bit
                            bs["data"] = [v & 0xFFFFFFFFFFFFFFFF for v in arr]
                            continue
                        _skip_tag_payload(bt, buf)
                    sec["block_states"] = bs
                    continue

                _skip_tag_payload(tt, buf)

            out["sections"].append(sec)

    cx = int(out.get("xPos", 0))
    cz = int(out.get("zPos", 0))
    is_light_on = bool(int(out.get("isLightOn", 0)))
    sections: Dict[int, Section] = {}
    for s in out.get("sections", []):
        y = int(s.get("Y", 0))
        bs = s.get("block_states") or {}
        palette = bs.get("palette") or ["minecraft:air"]
        data = bs.get("data")
        bl = s.get("BlockLight")
        sl = s.get("SkyLight")
        sections[y] = Section(y=y, palette=palette, data=data, block_light=bl, sky_light=sl)

    return Chunk(cx=cx, cz=cz, is_light_on=is_light_on, sections=sections)


class WorldReader:
    def __init__(self, world_dir: Path, dimension: str = "overworld"):
        self.world_dir = world_dir
        self.dimension = dimension
        if dimension == "overworld":
            self.region_dir = world_dir / "region"
        elif dimension == "nether":
            self.region_dir = world_dir / "DIM-1" / "region"
        elif dimension == "end":
            self.region_dir = world_dir / "DIM1" / "region"
        else:
            raise ValueError(f"unknown dimension: {dimension}")

        # In Nether there is no skylight. In Overworld/End, we require it for reliable light.
        self._require_sky_light = dimension != "nether"

        self._region_cache: Dict[Tuple[int, int], RegionFile] = {}
        self._chunk_cache: Dict[Tuple[int, int], Optional[Chunk]] = {}

    def _get_region(self, rx: int, rz: int) -> Optional[RegionFile]:
        key = (rx, rz)
        if key in self._region_cache:
            return self._region_cache[key]
        path = self.region_dir / f"r.{rx}.{rz}.mca"
        if not path.exists():
            return None
        rf = RegionFile(path)
        self._region_cache[key] = rf
        return rf

    def get_chunk(self, cx: int, cz: int) -> Optional[Chunk]:
        key = (cx, cz)
        if key in self._chunk_cache:
            return self._chunk_cache[key]
        rx = cx // 32
        rz = cz // 32
        rf = self._get_region(rx, rz)
        if rf is None:
            self._chunk_cache[key] = None
            return None
        raw = rf.read_chunk_nbt(cx, cz)
        if raw is None:
            self._chunk_cache[key] = None
            return None
        ch = _parse_chunk(raw)
        self._chunk_cache[key] = ch
        return ch

    def block_name(self, x: int, y: int, z: int) -> str:
        cx = x // 16
        cz = z // 16
        ch = self.get_chunk(cx, cz)
        if ch is None:
            return "minecraft:air"
        return ch.block_name(x, y, z)

    def light(self, x: int, y: int, z: int) -> int:
        v, ok = self.light_info(x, y, z)
        if not ok or v is None:
            return 0
        return v

    def light_info(self, x: int, y: int, z: int) -> Tuple[Optional[int], bool]:
        cx = x // 16
        cz = z // 16
        ch = self.get_chunk(cx, cz)
        if ch is None:
            return None, False
        return ch.light_info(x, y, z, require_sky=self._require_sky_light)


# --- Local axes (match prefab_local_axes in infra/prefab-lib.sh) ----------------


def _dir_opposite(d: str) -> str:
    return {"north": "south", "south": "north", "east": "west", "west": "east"}[d]


def _dir_rotate_cw(d: str) -> str:
    return {"north": "east", "east": "south", "south": "west", "west": "north"}[d]


DIR_VECTORS_XZ = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}


def dir_vec_xz(d: str) -> Tuple[int, int]:
    return DIR_VECTORS_XZ[d]


@dataclass(frozen=True)
class LocalAxes:
    ax: int
    az: int
    width: int
    depth: int
    dxr: int
    dzr: int
    dxf: int
    dzf: int
    in_dir: str
    right_dir: str

    def l2w(self, u: int, v: int) -> Tuple[int, int]:
        x = self.ax + u * self.dxr + v * self.dxf
        z = self.az + u * self.dzr + v * self.dzf
        return x, z


def local_axes(facing: str, x1: int, x2: int, z1: int, z2: int) -> LocalAxes:
    dx = x2 - x1 + 1
    dz = z2 - z1 + 1
    in_dir = _dir_opposite(facing)
    right_dir = _dir_rotate_cw(in_dir)

    if facing == "north":
        # front is z1, into is +z, right is -x
        return LocalAxes(ax=x2, az=z1, width=dx, depth=dz, dxr=-1, dzr=0, dxf=0, dzf=1, in_dir=in_dir, right_dir=right_dir)
    if facing == "south":
        # front is z2, into is -z, right is +x
        return LocalAxes(ax=x1, az=z2, width=dx, depth=dz, dxr=1, dzr=0, dxf=0, dzf=-1, in_dir=in_dir, right_dir=right_dir)
    if facing == "west":
        # front is x1, into is +x, right is +z
        return LocalAxes(ax=x1, az=z1, width=dz, depth=dx, dxr=0, dzr=1, dxf=1, dzf=0, in_dir=in_dir, right_dir=right_dir)
    if facing == "east":
        # front is x2, into is -x, right is -z
        return LocalAxes(ax=x2, az=z2, width=dz, depth=dx, dxr=0, dzr=-1, dxf=-1, dzf=0, in_dir=in_dir, right_dir=right_dir)

    raise ValueError(f"invalid facing: {facing}")


# --- Scoring -------------------------------------------------------------------


PASSABLE_AIR = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}


def is_air(name: str) -> bool:
    return name in PASSABLE_AIR


def is_walk_passable(name: str) -> bool:
    # Back-compat default: assume doors and trapdoors are passable (player can open).
    return is_walk_passable_cfg(name, doors_passable=True, trapdoors_passable=True)


def is_walk_passable_cfg(name: str, *, doors_passable: bool, trapdoors_passable: bool) -> bool:
    if is_air(name):
        return True
    if name.endswith("_carpet"):
        return True
    if name.endswith("_pressure_plate"):
        return True
    if name.endswith("_door"):
        return doors_passable
    if name.endswith("_trapdoor"):
        return trapdoors_passable
    return False


def is_spawn_air(name: str) -> bool:
    return is_air(name)


def is_support_block(name: str) -> bool:
    if is_air(name):
        return False
    if name in ("minecraft:water", "minecraft:lava"):
        return False
    return True


SPAWN_SURFACE_DENY_SUFFIXES = (
    "_slab",
    "_stairs",
    "_wall",
    "_pane",
    "_carpet",
    "_pressure_plate",
    "_button",
    "_rail",
    "_fence",
    "_fence_gate",
)

SPAWN_SURFACE_DENY_CONTAINS = (
    "glass",
    "leaves",
    "trapdoor",
    "door",
    "lantern",
    "torch",
    "snow",
)


def is_spawnable_surface(name: str) -> bool:
    """
    Heuristic: blocks that behave like a full solid top surface for hostile spawning.
    We keep this intentionally strict to avoid false positives.
    """
    if is_air(name):
        return False
    if name in ("minecraft:water", "minecraft:lava"):
        return False

    # "minecraft:rail" (and modded "<ns>:rail") doesn't match the "_rail" suffix rule.
    if name.endswith(":rail"):
        return False

    if name.endswith(SPAWN_SURFACE_DENY_SUFFIXES):
        return False
    if any(tok in name for tok in SPAWN_SURFACE_DENY_CONTAINS):
        return False

    # Not full-height blocks that show up often.
    if name in ("minecraft:farmland", "minecraft:dirt_path"):
        return False

    return True


def is_hazard(name: str) -> bool:
    return name in {
        "minecraft:lava",
        "minecraft:fire",
        "minecraft:soul_fire",
        "minecraft:magma_block",
        "minecraft:cactus",
        "minecraft:sweet_berry_bush",
        "minecraft:campfire",
        "minecraft:soul_campfire",
    }


DETAIL_HINTS = (
    "_stairs",
    "_slab",
    "_wall",
    "_fence",
    "_trapdoor",
    "_button",
    "_pressure_plate",
    "_pane",
)


def is_detail_block(name: str) -> bool:
    if name.endswith(DETAIL_HINTS):
        return True
    if name in {"minecraft:lantern", "minecraft:soul_lantern"}:
        return True
    if name.endswith("_torch"):
        return True
    if name.endswith("_sign") or name.endswith("_hanging_sign"):
        return True
    return False


UGLY_BLOCKS = {
    "minecraft:dirt",
    "minecraft:coarse_dirt",
    "minecraft:grass_block",
    "minecraft:cobblestone",
    "minecraft:gravel",
    "minecraft:netherrack",
}


@dataclass
class ScoreResult:
    total: int
    playability: int
    beauty: int
    subs: Dict[str, int]
    findings: List[str]
    caps: Dict[str, int]
    metrics: Dict[str, object]

    def to_json(self) -> str:
        return json.dumps(
            {
                "total": self.total,
                "playability": self.playability,
                "beauty": self.beauty,
                "subs": self.subs,
                "findings": self.findings,
                "caps": self.caps,
                "metrics": self.metrics,
            },
            indent=2,
            sort_keys=True,
        )


def _clamp(v: int, lo: int, hi: int) -> int:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def compute_score(
    world: WorldReader,
    box: Tuple[int, int, int, int, int, int],
    *,
    profile: str = "generic",
    facing: Optional[str] = None,
    nav_start_mode: str = "inside_cell",
    doors_passable: bool = True,
    trapdoors_passable: bool = True,
    floor_y: Optional[int] = None,
    label: Optional[str] = None,
) -> ScoreResult:
    x1, y1, z1, x2, y2, z2 = box
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    if z1 > z2:
        z1, z2 = z2, z1

    w = x2 - x1 + 1
    h = y2 - y1 + 1
    d = z2 - z1 + 1
    vol = w * h * d

    floor = floor_y if floor_y is not None else y1
    wall_top = floor + 4
    roof_start = floor + 5
    y_walk = floor + 1

    # Load the full box (small volumes: fine; larger volumes could be optimized later).
    name_to_id: Dict[str, int] = {}
    id_to_name: List[str] = []

    def bid(name: str) -> int:
        if name in name_to_id:
            return name_to_id[name]
        i = len(id_to_name)
        name_to_id[name] = i
        id_to_name.append(name)
        return i

    blocks = [0] * vol
    key: Dict[str, List[Tuple[int, int, int]]] = collections.defaultdict(list)

    def idx(x: int, y: int, z: int) -> int:
        return ((y - y1) * d + (z - z1)) * w + (x - x1)

    for y in range(y1, y2 + 1):
        for z in range(z1, z2 + 1):
            for x in range(x1, x2 + 1):
                name = world.block_name(x, y, z)
                blocks[idx(x, y, z)] = bid(name)
                if name in ("cobblemon:healing_machine", "cobblemon:pc"):
                    key[name].append((x, y, z))
                if name.endswith("_door"):
                    key["*door"].append((x, y, z))

    def name_at(x: int, y: int, z: int) -> str:
        if not (x1 <= x <= x2 and y1 <= y <= y2 and z1 <= z <= z2):
            return "minecraft:air"
        return id_to_name[blocks[idx(x, y, z)]]

    cnt = collections.Counter(blocks)
    total_non_air = sum(c for i, c in cnt.items() if id_to_name[i] != "minecraft:air")
    uniq_non_air = sum(1 for i in cnt if id_to_name[i] != "minecraft:air")

    top_blocks: List[Tuple[str, int]] = []
    for i, c in cnt.most_common(25):
        n = id_to_name[i]
        if n == "minecraft:air":
            continue
        top_blocks.append((n, c))

    # Roof + silhouette
    roof_blocks = 0
    heights: List[int] = []
    for z in range(z1, z2 + 1):
        for x in range(x1, x2 + 1):
            col_top = None
            for y in range(y2, y1 - 1, -1):
                if name_at(x, y, z) != "minecraft:air":
                    col_top = y
                    break
            if col_top is not None:
                heights.append(col_top)
            for y in range(roof_start, y2 + 1):
                if name_at(x, y, z) != "minecraft:air":
                    roof_blocks += 1

    if heights:
        h_min = min(heights)
        h_max = max(heights)
        h_range = h_max - h_min
        h_avg = sum(heights) / len(heights)
        h_var = sum((v - h_avg) ** 2 for v in heights) / len(heights)
        h_std = math.sqrt(h_var)
    else:
        h_min = h_max = h_range = 0
        h_std = 0.0

    # Boundary detail ratio (facade band only: ignore roof/floor noise).
    boundary_non_air = 0
    boundary_detail = 0
    for y in range(floor, min(y2, wall_top) + 1):
        for z in range(z1, z2 + 1):
            for x in range(x1, x2 + 1):
                if x not in (x1, x2) and z not in (z1, z2):
                    continue
                n = name_at(x, y, z)
                if n == "minecraft:air":
                    continue
                boundary_non_air += 1
                if is_detail_block(n):
                    boundary_detail += 1
    detail_ratio = (boundary_detail / boundary_non_air) if boundary_non_air else 0.0

    # --- Interior / navigation: 2D flood fill at y_walk (robust to porches/alcoves) ---
    def inside_box(x: int, z: int) -> bool:
        return x1 <= x <= x2 and z1 <= z <= z2

    if nav_start_mode not in ("door_cell", "inside_cell", "both"):
        raise ValueError(f"invalid nav_start_mode: {nav_start_mode}")

    walkable: Dict[Tuple[int, int], bool] = {}
    for z in range(z1, z2 + 1):
        for x in range(x1, x2 + 1):
            feet = name_at(x, y_walk, z)
            head = name_at(x, y_walk + 1, z)
            below = name_at(x, y_walk - 1, z)
            walkable[(x, z)] = (
                is_walk_passable_cfg(feet, doors_passable=doors_passable, trapdoors_passable=trapdoors_passable)
                and is_walk_passable_cfg(head, doors_passable=doors_passable, trapdoors_passable=trapdoors_passable)
                and is_support_block(below)
            )
    total_walkable_bbox = sum(1 for v in walkable.values() if v)

    # Denominator stability: ignore a 1-block bbox border ring (avoids "bbox drift" pulling in exterior).
    # For very small boxes we keep the bbox definition.
    use_inner_box = w >= 3 and d >= 3
    interest_x1 = x1 + 1 if use_inner_box else x1
    interest_x2 = x2 - 1 if use_inner_box else x2
    interest_z1 = z1 + 1 if use_inner_box else z1
    interest_z2 = z2 - 1 if use_inner_box else z2

    def in_interest(x: int, z: int) -> bool:
        return interest_x1 <= x <= interest_x2 and interest_z1 <= z <= interest_z2

    total_walkable = sum(1 for (x, z), ok in walkable.items() if ok and in_interest(x, z))

    # Detect entry doors near the facade. Doors are 2 blocks tall, so scan y_walk and y_walk-1.
    scan_ys = [y_walk, y_walk - 1]
    door_positions: List[Tuple[int, int, int]] = []

    def maybe_add_door(x: int, y: int, z: int) -> None:
        if not (x1 <= x <= x2 and y1 <= y <= y2 and z1 <= z <= z2):
            return
        if name_at(x, y, z).endswith("_door"):
            door_positions.append((x, y, z))

    if facing:
        if facing == "west":
            xs = [x1, x1 + 1, x1 + 2]
            for x in xs:
                for z in range(z1, z2 + 1):
                    for yy in scan_ys:
                        maybe_add_door(x, yy, z)
        elif facing == "east":
            xs = [x2, x2 - 1, x2 - 2]
            for x in xs:
                for z in range(z1, z2 + 1):
                    for yy in scan_ys:
                        maybe_add_door(x, yy, z)
        elif facing == "north":
            zs = [z1, z1 + 1, z1 + 2]
            for z in zs:
                for x in range(x1, x2 + 1):
                    for yy in scan_ys:
                        maybe_add_door(x, yy, z)
        elif facing == "south":
            zs = [z2, z2 - 1, z2 - 2]
            for z in zs:
                for x in range(x1, x2 + 1):
                    for yy in scan_ys:
                        maybe_add_door(x, yy, z)
    else:
        # Best-effort: scan perimeter for doors if facing not provided.
        for x in range(x1, x2 + 1):
            for yy in scan_ys:
                maybe_add_door(x, yy, z1)
                maybe_add_door(x, yy, z2)
        for z in range(z1, z2 + 1):
            for yy in scan_ys:
                maybe_add_door(x1, yy, z)
                maybe_add_door(x2, yy, z)

    door_positions = list({(x, y, z) for (x, y, z) in door_positions})

    door_cells = list({(x, z) for (x, _y, z) in door_positions})

    # Start nodes represent the entry surface.
    # - door_cell: start on the doorway itself (can be blocked by --doors-passable).
    # - inside_cell: start just behind the door (recommended default, stable vs door passability).
    # - both: union of both.
    inside_cells: List[Tuple[int, int]] = []
    if door_cells:
        if facing:
            axes_nav = local_axes(facing, x1, x2, z1, z2)
            dx_in, dz_in = dir_vec_xz(axes_nav.in_dir)
            for x, z in door_cells:
                p = (x + dx_in, z + dz_in)
                if inside_box(p[0], p[1]):
                    inside_cells.append(p)
        else:
            # Best-effort: pick the neighbor closest to box center as "inside".
            cx = (x1 + x2) / 2.0
            cz = (z1 + z2) / 2.0
            for x, z in door_cells:
                candidates = [(x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)]
                candidates = [p for p in candidates if inside_box(p[0], p[1])]
                if not candidates:
                    continue
                candidates.sort(key=lambda p: (p[0] - cx) ** 2 + (p[1] - cz) ** 2)
                inside_cells.append(candidates[0])

    if nav_start_mode == "door_cell":
        start_candidates = door_cells
    elif nav_start_mode == "inside_cell":
        start_candidates = inside_cells or door_cells
    else:
        start_candidates = list({*door_cells, *inside_cells})

    start_nodes: List[Tuple[int, int]] = [p for p in start_candidates if walkable.get(p, False)]

    # Fallback: only if no door was detected at all (e.g., open arch entrance).
    if not start_nodes and not door_cells:
        cx = (x1 + x2) // 2
        cz = (z1 + z2) // 2
        candidates = [
            (cx, cz),
            (cx, z1 + 1),
            (cx, z2 - 1),
            (x1 + 1, cz),
            (x2 - 1, cz),
        ]
        for sx, sz in candidates:
            if walkable.get((sx, sz), False):
                start_nodes.append((sx, sz))
                break

    # BFS reachability in 2D (flat). Reachable cells define the "accessible interior".
    reachable: Dict[Tuple[int, int], int] = {}
    q = collections.deque()
    for s in list({p for p in start_nodes}):
        reachable[s] = 0
        q.append(s)

    while q:
        x, z = q.popleft()
        dist = reachable[(x, z)]
        for nx, nz in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
            if not inside_box(nx, nz):
                continue
            if not walkable.get((nx, nz), False):
                continue
            if (nx, nz) in reachable:
                continue
            reachable[(nx, nz)] = dist + 1
            q.append((nx, nz))

    reachable_count_bbox = len(reachable)
    reachable_interest = {p for p in reachable.keys() if in_interest(p[0], p[1])}
    reachable_count = len(reachable_interest)
    reachable_ratio = (reachable_count / total_walkable) if total_walkable else 0.0
    unreachable_walkables = max(0, total_walkable - reachable_count)
    unreachable_samples: List[Dict[str, int]] = []
    if unreachable_walkables > 0:
        for (x, z), ok in walkable.items():
            if not ok or not in_interest(x, z) or (x, z) in reachable_interest:
                continue
            unreachable_samples.append({"x": x, "z": z})
            if len(unreachable_samples) >= 10:
                break

    def adjacent_reachable(tx: int, ty: int, tz: int) -> bool:
        if ty != y_walk:
            return True
        for nx, nz in ((tx + 1, tz), (tx - 1, tz), (tx, tz + 1), (tx, tz - 1)):
            if (nx, nz) in reachable_interest:
                return True
        return False

    healer_ok = bool(key.get("cobblemon:healing_machine")) and all(adjacent_reachable(x, y, z) for x, y, z in key["cobblemon:healing_machine"])
    pc_ok = bool(key.get("cobblemon:pc")) and all(adjacent_reachable(x, y, z) for x, y, z in key["cobblemon:pc"])

    # Spawnability (geometry + light reliability).
    spawnable = 0
    spawnable_dark = 0
    unknown_light_positions = 0
    min_light: Optional[int] = None
    dark_spots: List[Dict[str, int]] = []
    dark_quadrants = {"nw": 0, "ne": 0, "sw": 0, "se": 0}
    light_unknown_reasons: Dict[str, int] = collections.Counter()

    if reachable_count > 0:
        mid_x = (x1 + x2) / 2.0
        mid_z = (z1 + z2) / 2.0

        def add_quadrant(xx: int, zz: int) -> None:
            if xx <= mid_x and zz <= mid_z:
                dark_quadrants["nw"] += 1
            elif xx > mid_x and zz <= mid_z:
                dark_quadrants["ne"] += 1
            elif xx <= mid_x and zz > mid_z:
                dark_quadrants["sw"] += 1
            else:
                dark_quadrants["se"] += 1

        def classify_unknown_light(xx: int, yy: int, zz: int) -> None:
            # Best-effort only when we have a real WorldReader.
            if not hasattr(world, "get_chunk"):
                light_unknown_reasons["unknown"] += 1
                return
            try:
                ch = world.get_chunk(xx // 16, zz // 16)  # type: ignore[attr-defined]
            except Exception:
                light_unknown_reasons["unknown"] += 1
                return
            if ch is None:
                light_unknown_reasons["missing_chunk"] += 1
                return
            if not getattr(ch, "is_light_on", False):
                light_unknown_reasons["isLightOn_false"] += 1
                return
            sec = getattr(ch, "sections", {}).get(yy >> 4)
            if sec is None:
                light_unknown_reasons["missing_section"] += 1
                return
            if not _light_arr_ok(getattr(sec, "block_light", None)):
                light_unknown_reasons["missing_block_light"] += 1
                return
            require_sky = getattr(world, "_require_sky_light", True)
            if require_sky and not _light_arr_ok(getattr(sec, "sky_light", None)):
                light_unknown_reasons["missing_sky_light"] += 1
                return
            light_unknown_reasons["unknown"] += 1

        for (x, z) in reachable_interest:
            feet = name_at(x, y_walk, z)
            head = name_at(x, y_walk + 1, z)
            below = name_at(x, y_walk - 1, z)
            if not (is_spawn_air(feet) and is_spawn_air(head) and is_spawnable_surface(below)):
                continue

            spawnable += 1
            lv, ok = world.light_info(x, y_walk, z)
            if not ok or lv is None:
                unknown_light_positions += 1
                classify_unknown_light(x, y_walk, z)
                continue

            if min_light is None or lv < min_light:
                min_light = int(lv)
            if int(lv) == 0:
                spawnable_dark += 1
                add_quadrant(x, z)
                if len(dark_spots) < 12:
                    dark_spots.append({"x": x, "y": y_walk, "z": z, "light": int(lv)})

    spawn_check_applicable = spawnable > 0
    # Light data reliability is evaluated only for the positions we actually need to score (spawnable positions).
    # This avoids bbox/chunk-rectangle false negatives when the bbox includes unrelated outside chunks.
    light_eval_positions = int(spawnable)
    light_data_reliable = bool(spawn_check_applicable and (unknown_light_positions == 0))
    light_data_coverage: Optional[float] = None
    if spawnable > 0:
        light_data_coverage = float(spawnable - unknown_light_positions) / float(spawnable)
    light_data_issues = light_unknown_reasons

    # Hazards in accessible interior (columns under reachable cells) up to wall height.
    hazard_blocks = 0
    hazard_samples: List[Dict[str, int]] = []
    if reachable_count > 0:
        for (x, z) in reachable_interest:
            for y in range(floor, min(y2, wall_top) + 1):
                if is_hazard(name_at(x, y, z)):
                    hazard_blocks += 1
                    if len(hazard_samples) < 8:
                        hazard_samples.append({"x": x, "y": y, "z": z})

    # Facade relief (more informative: depth distribution in v=0..k).
    facade_k = 4
    facade_depth_mean = 0.0
    facade_recessed_frac = 0.0
    facade_depth_p95 = 0
    facade_missing = 0
    facade_scan_total = 0
    facade_missing_frac = 0.0
    if facing:
        axes = local_axes(facing, x1, x2, z1, z2)
        depths: List[int] = []
        max_v = min(facade_k, max(0, axes.depth - 1))
        scan_y1 = floor + 2
        scan_y2 = min(y2, wall_top)
        scan_y_count = max(0, scan_y2 - scan_y1 + 1)
        facade_scan_total = int(axes.width * scan_y_count)
        for u in range(axes.width):
            for y in range(scan_y1, scan_y2 + 1):
                first_v: Optional[int] = None
                for v in range(0, max_v + 1):
                    xx, zz = axes.l2w(u, v)
                    if name_at(xx, y, zz) != "minecraft:air":
                        first_v = v
                        break
                if first_v is None:
                    facade_missing += 1
                else:
                    depths.append(first_v)
        facade_missing_frac = float(facade_missing) / float(facade_scan_total) if facade_scan_total else 0.0
        if depths:
            facade_depth_mean = float(sum(depths)) / float(len(depths))
            facade_recessed_frac = float(sum(1 for v in depths if v > 0)) / float(len(depths))
            depths_sorted = sorted(depths)
            facade_depth_p95 = int(depths_sorted[int(0.95 * (len(depths_sorted) - 1))])

    # --- Subscores and findings
    findings: List[str] = []
    caps: Dict[str, int] = {}

    # Spawn-proof (25)
    spawn_score = 25
    if not spawn_check_applicable:
        # No spawnable surfaces => skip spawn check; keep full score.
        findings.append("Spawn: aucune surface spawnable detectee (OK).")
    elif not light_data_reliable:
        if unknown_light_positions > 0:
            findings.append(
                f"Lumiere inconnue: data light non fiable ({unknown_light_positions} position(s) spawnable(s) avec light inconnu)."
            )
        # No light-based penalty when unreliable.
    else:
        if spawnable_dark > 0:
            spawn_score = _clamp(25 - spawnable_dark * 5, 0, 25)
            findings.append(f"{spawnable_dark} spot(s) spawnable(s) en light=0 dans l'interieur (risque mobs).")
            caps["spawn_dark"] = spawnable_dark
        else:
            findings.append("OK spawn-proof: 0 spot spawnable en light=0 dans l'interieur.")

    # Navigation (25)
    nav_score = 25
    if total_walkable <= 0:
        nav_score = 0
        findings.append("Navigation: aucun espace praticable detecte (plan y_walk).")
        caps["nav_blocked"] = 1
    else:
        if reachable_ratio < 0.85:
            nav_score = int(round(25 * reachable_ratio))
            findings.append(f"Navigation: seulement {reachable_ratio*100:.1f}% accessible depuis l'entree.")
        else:
            findings.append(f"Navigation: {reachable_ratio*100:.1f}% accessible depuis l'entree.")

    if profile in ("pokecenter", "generic"):
        if not key.get("cobblemon:healing_machine"):
            nav_score = max(0, nav_score - 6)
            findings.append("Manque: cobblemon:healing_machine (kit absent).")
            caps["missing_healer"] = 1
        elif not healer_ok:
            nav_score = max(0, nav_score - 4)
            findings.append("Acces: healing_machine non accessible (adjacent walkable non reachable).")
            caps["healer_blocked"] = 1

        if not key.get("cobblemon:pc"):
            nav_score = max(0, nav_score - 6)
            findings.append("Manque: cobblemon:pc (kit absent).")
            caps["missing_pc"] = 1
        elif not pc_ok:
            nav_score = max(0, nav_score - 4)
            findings.append("Acces: PC non accessible (adjacent walkable non reachable).")
            caps["pc_blocked"] = 1

    # Safety (10)
    safety_score = 10
    if hazard_blocks > 0:
        safety_score = _clamp(10 - hazard_blocks * 2, 0, 10)
        findings.append(f"Securite: {hazard_blocks} bloc(s) dangereux dans l'interieur.")
        caps["hazards"] = hazard_blocks

    playability = _clamp(spawn_score + nav_score + safety_score, 0, 60)

    # Palette (15)
    palette_score = 15
    dom_threshold = max(10, int(math.ceil(total_non_air * 0.01)))
    dominant = [name for name, c in top_blocks if c >= dom_threshold]
    dom_n = len(dominant)
    if dom_n < 6:
        palette_score = _clamp(15 - (6 - dom_n) * 2, 0, 15)
        findings.append(f"Palette: un peu monotone (dominants={dom_n}, cible 6..12).")
    elif dom_n > 12:
        palette_score = _clamp(15 - (dom_n - 12), 0, 15)
        findings.append(f"Palette: un peu bruyante (dominants={dom_n}, cible 6..12).")

    ugly_hits = 0
    for name, c in top_blocks:
        if name in UGLY_BLOCKS and c >= 4:
            ugly_hits += c
    if ugly_hits > 0:
        findings.append(f"Warning palette: {ugly_hits} bloc(s) 'terrain' (dirt/cobble/etc) dans le volume.")
        if profile == "pokecenter":
            palette_score = max(0, palette_score - 3)

    # Volumes (15)
    volume_score = 15
    if roof_blocks <= 0:
        volume_score = 0
        findings.append("Volumes: pas de toit detecte au-dessus de la ligne de mur.")
    else:
        if h_range < 3:
            volume_score = _clamp(volume_score - 5, 0, 15)
            findings.append(f"Volumes: silhouette de toit assez plate (range={h_range}).")
        if facing and facade_recessed_frac < 0.08:
            volume_score = _clamp(volume_score - 4, 0, 15)
            findings.append(f"Facade: assez plate (recessed={facade_recessed_frac*100:.1f}%, depth_mean={facade_depth_mean:.2f}).")
        if facing and facade_scan_total > 0 and facade_missing_frac > 0.35:
            findings.append(f"bbox_or_facing_suspect: facade_missing={facade_missing_frac*100:.1f}% (check bbox/--facing).")

    # Detail (10)
    detail_score = 10
    if boundary_non_air <= 0:
        detail_score = 0
        findings.append("Detail: aucun bloc exterieur detecte (volume vide?).")
    else:
        if detail_ratio < 0.04:
            detail_score = _clamp(detail_score - 4, 0, 10)
            findings.append(f"Detail: exterieur un peu plat (detail_ratio={detail_ratio*100:.1f}%).")
        elif detail_ratio > 0.25:
            detail_score = _clamp(detail_score - 4, 0, 10)
            findings.append(f"Detail: exterieur surcharge (detail_ratio={detail_ratio*100:.1f}%).")

    # Pokecenter profile: expect some windows and red accents.
    if profile == "pokecenter":
        pane_count = 0
        red_count = 0
        for name, c in top_blocks:
            if name.endswith("_stained_glass_pane") or name.endswith("_glass_pane"):
                pane_count += c
            if name in ("minecraft:red_concrete", "minecraft:red_terracotta", "minecraft:red_nether_bricks"):
                red_count += c
        if pane_count < 10:
            detail_score = max(0, detail_score - 2)
            findings.append(f"Pokecenter: peu de fenetres (glass_pane={pane_count}).")
        if red_count < 20:
            volume_score = max(0, volume_score - 1)
            findings.append(f"Pokecenter: accents rouges faibles (red_blocks={red_count}).")

    beauty = _clamp(palette_score + volume_score + detail_score, 0, 40)
    total = playability + beauty

    # Hard caps.
    if light_data_reliable and spawn_check_applicable and spawnable_dark >= 5:
        total = min(total, 60)
        caps["total_cap"] = 60
    elif light_data_reliable and spawn_check_applicable and spawnable_dark > 0:
        total = min(total, 80)
        caps["total_cap"] = 80
    if total_walkable > 0 and reachable_ratio < 0.5:
        total = min(total, 60)
        caps["total_cap_nav"] = 60

    # Keep findings short and actionable.
    bad = [f for f in findings if any(w in f.lower() for w in ("manque", "non", "risque", "dangereux", "plat", "bruyant", "monotone", "surcharge"))]
    good = [f for f in findings if f not in bad]
    findings_out = (bad + good)[:10]

    subs = {
        "spawn_proof": spawn_score,
        "navigation": nav_score,
        "safety": safety_score,
        "palette": palette_score,
        "volumes": volume_score,
        "detail": detail_score,
    }

    metrics = {
        "label": label,
        "config": {
            "profile": profile,
            "facing": facing,
            "nav_start_mode": nav_start_mode,
            "doors_passable": bool(doors_passable),
            "trapdoors_passable": bool(trapdoors_passable),
        },
        "box": {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2, "w": w, "h": h, "d": d, "volume": vol},
        "non_air_blocks": int(total_non_air),
        "unique_non_air": int(uniq_non_air),
        "dominant_blocks": dominant,
        "dominant_threshold": int(dom_threshold),
        "roof_blocks": int(roof_blocks),
        "silhouette": {"min": int(h_min), "max": int(h_max), "range": int(h_range), "std": float(h_std)},
        "boundary": {"non_air": int(boundary_non_air), "detail": int(boundary_detail), "detail_ratio": float(detail_ratio)},
        "walk": {
            "y_walk": int(y_walk),
            "floor_y": int(floor),
            "wall_top_y": int(wall_top),
            "roof_start_y": int(roof_start),
            "denominator": "inner_box" if use_inner_box else "bbox",
            "use_inner_box": bool(use_inner_box),
            "interest_box": {"x1": int(interest_x1), "z1": int(interest_z1), "x2": int(interest_x2), "z2": int(interest_z2)},
            "total_walkable_bbox": int(total_walkable_bbox),
            "total_walkable": int(total_walkable),
            "reachable_bbox": int(reachable_count_bbox),
            "reachable": int(reachable_count),
            "reachable_ratio": float(reachable_ratio),
            "unreachable_walkables": int(unreachable_walkables),
            "unreachable_samples": unreachable_samples,
            "start_mode": nav_start_mode,
            "start_nodes": [{"x": x, "z": z} for (x, z) in start_nodes[:6]],
            "doors_found": int(len(door_cells)),
            "doors_found_blocks": int(len(door_positions)),
        },
        "navigation": {
            "start_mode": nav_start_mode,
            "doors_passable": bool(doors_passable),
            "trapdoors_passable": bool(trapdoors_passable),
            "start_nodes": [{"x": x, "z": z} for (x, z) in start_nodes[:6]],
            "doors_found": int(len(door_cells)),
            "doors_found_blocks": int(len(door_positions)),
            "door_cells_sample": [{"x": x, "z": z} for (x, z) in sorted(door_cells)[:10]],
            "entry_door_positions_sample": [{"x": x, "y": y, "z": z} for (x, y, z) in sorted(door_positions)[:10]],
            "doors_detected": int(len({(x, y, z) for (x, y, z) in key.get("*door", [])})),
            "door_positions_sample": [
                {"x": x, "y": y, "z": z} for (x, y, z) in sorted({(x, y, z) for (x, y, z) in key.get("*door", [])})[:10]
            ],
            "denominator": "inner_box" if use_inner_box else "bbox",
            "use_inner_box": bool(use_inner_box),
            "interest_box": {"x1": int(interest_x1), "z1": int(interest_z1), "x2": int(interest_x2), "z2": int(interest_z2)},
            "total_walkable_bbox": int(total_walkable_bbox),
            "total_walkable": int(total_walkable),
            "reachable_bbox": int(reachable_count_bbox),
            "reachable": int(reachable_count),
            "reachable_ratio": float(reachable_ratio),
            "unreachable_walkables": int(unreachable_walkables),
            "unreachable_samples": unreachable_samples,
        },
        "spawn": {
            # Back-compat: keep "light_reliable" but make it mean "data reliable" (no more spawnable==0 shortcut).
            "light_reliable": bool(light_data_reliable),
            "light_data_reliable": bool(light_data_reliable),
            "light_data_coverage": light_data_coverage,
            "light_eval_positions": int(light_eval_positions),
            "light_data_issues": dict(light_data_issues),
            "spawn_check_applicable": bool(spawn_check_applicable),
            "unknown_light_positions": int(unknown_light_positions),
            "unknown_light_reasons": dict(light_unknown_reasons),
            "spawnable_positions": int(spawnable),
            "spawnable_dark": int(spawnable_dark),
            "min_light": int(min_light) if min_light is not None else None,
            "dark_spots_samples": dark_spots,
            "dark_quadrants": dark_quadrants,
        },
        "hazards": {"count": int(hazard_blocks), "samples": hazard_samples},
        "facade": {
            "k": int(facade_k),
            "depth_mean": float(facade_depth_mean),
            "depth_p95": int(facade_depth_p95),
            "recessed_frac": float(facade_recessed_frac),
            "scan_total": int(facade_scan_total),
            "missing_columns": int(facade_missing),
            "missing_frac": float(facade_missing_frac),
        },
        "keys": {k: len(v) for k, v in key.items()},
        "top_blocks": [{"name": n, "count": int(c)} for n, c in top_blocks[:12]],
    }

    return ScoreResult(
        total=int(total),
        playability=int(playability),
        beauty=int(beauty),
        subs=subs,
        findings=findings_out,
        caps=caps,
        metrics=metrics,
    )


def _say(msg: str) -> None:
    msg = msg.replace("\n", " ")
    msg = " ".join(msg.split())
    if len(msg) > 220:
        msg = msg[:217] + "..."
    subprocess.run(["./infra/mc.sh", f"say {msg}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Score a prefab build by reading blocks/light from the world on disk.")
    ap.add_argument("--world", default="./data/world", help="World directory (default: ./data/world).")
    ap.add_argument("--dimension", default="overworld", choices=["overworld", "nether", "end"], help="Dimension (default: overworld).")
    ap.add_argument("--profile", default="generic", choices=["generic", "pokecenter"], help="Scoring profile/ruleset.")
    ap.add_argument("--facing", default=None, choices=["north", "south", "east", "west"], help="Facade/outside direction (improves facade/nav checks).")
    ap.add_argument(
        "--nav-start-mode",
        default="inside_cell",
        choices=["door_cell", "inside_cell", "both"],
        help="Navigation start node mode (default: inside_cell).",
    )
    ap.add_argument("--doors-passable", default="true", choices=["true", "false"], help="Treat doors as passable for navigation (default: true).")
    ap.add_argument("--trapdoors-passable", default="true", choices=["true", "false"], help="Treat trapdoors as passable for navigation (default: true).")
    ap.add_argument("--floor-y", type=int, default=None, help="Floor Y (default: y1 of the box).")
    ap.add_argument("--label", default=None, help="Optional label (for logs).")
    ap.add_argument("--json", action="store_true", help="Output JSON (in addition to human output).")
    ap.add_argument("--say", action="store_true", help="Send a short summary to in-game chat via ./infra/mc.sh.")
    # NOTE: Python 3.9 argparse crashes when metavar is a tuple for fixed nargs.
    ap.add_argument("box", nargs=6, type=int, metavar="N", help="Bounding box coords: x1 y1 z1 x2 y2 z2.")
    args = ap.parse_args(argv)

    world_dir = Path(args.world)
    if not world_dir.exists():
        print(f"ERROR: world directory not found: {world_dir}", file=sys.stderr)
        return 2

    world = WorldReader(world_dir, dimension=args.dimension)
    res = compute_score(
        world,
        tuple(args.box),  # type: ignore[arg-type]
        profile=args.profile,
        facing=args.facing,
        nav_start_mode=args.nav_start_mode,
        doors_passable=(args.doors_passable == "true"),
        trapdoors_passable=(args.trapdoors_passable == "true"),
        floor_y=args.floor_y,
        label=args.label,
    )

    print("== Prefab Score ==")
    print(f"label: {args.label or '-'}")
    x1, y1, z1, x2, y2, z2 = args.box
    print(f"box: x={x1}..{x2} y={y1}..{y2} z={z1}..{z2}")
    print(f"score: {res.total}/100 (playability {res.playability}/60, beauty {res.beauty}/40)")
    print(
        "subs: "
        + ", ".join(
            f"{k}={v}"
            for k, v in (
                ("spawn", res.subs["spawn_proof"]),
                ("nav", res.subs["navigation"]),
                ("safety", res.subs["safety"]),
                ("palette", res.subs["palette"]),
                ("volumes", res.subs["volumes"]),
                ("detail", res.subs["detail"]),
            )
        )
    )
    if res.caps:
        print(f"caps: {res.caps}")
    print("findings:")
    for f in res.findings:
        print(f"- {f}")

    if args.json:
        print("json:")
        print(res.to_json())

    if args.say:
        prefix = f"{args.label} " if args.label else ""
        short = f"[SCORE] {prefix}{res.total}/100 (play {res.playability}/60, beauty {res.beauty}/40)"
        if res.caps.get("total_cap"):
            short += f" cap={res.caps['total_cap']}"
        if res.findings:
            short += f" | {res.findings[0]}"
        _say(short)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
