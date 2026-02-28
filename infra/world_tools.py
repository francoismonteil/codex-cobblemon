#!/usr/bin/env python3
"""Shared Anvil/NBT helpers for infra world inspection tools."""

from __future__ import annotations

import gzip
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SECTOR_BYTES = 4096
REGION_HEADER_BYTES = SECTOR_BYTES * 2
LIGHT_NIBBLE_BYTES = 2048

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

AIR_BLOCKS = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}
LIQUID_BLOCKS = {"minecraft:water", "minecraft:lava"}


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


def _nibble(arr: Optional[bytes], idx: int) -> int:
    if not arr:
        return 0
    b = arr[idx >> 1]
    if idx & 1:
        return (b >> 4) & 0x0F
    return b & 0x0F


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
            _ = buf.read_string()
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
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    buf = _Buf(raw)
    root_t = buf.read_u8()
    if root_t != TAG_COMPOUND:
        raise NBTError(f"unexpected root tag: {root_t}")
    _ = buf.read_string()
    root = _read_tag_payload(TAG_COMPOUND, buf)
    if not isinstance(root, dict):
        raise NBTError("root compound parse failed")
    return root


def load_level_dat(level_path: Path) -> Dict:
    with gzip.open(level_path, "rb") as f:
        raw = f.read()
    return _load_nbt_bytes(raw)


def read_world_spawn(world_dir: Path) -> Tuple[int, int, int]:
    root = load_level_dat(world_dir / "level.dat")
    data = root.get("Data")
    if not isinstance(data, dict):
        raise NBTError("level.dat: missing Data compound")
    keys = ("SpawnX", "SpawnY", "SpawnZ")
    if not all(isinstance(data.get(k), int) for k in keys):
        raise NBTError("level.dat: missing SpawnX/SpawnY/SpawnZ")
    return int(data["SpawnX"]), int(data["SpawnY"]), int(data["SpawnZ"])


def _heightmap_get(hm_longs: List[int], x_in: int, z_in: int, bits: int = 9) -> int:
    idx = (z_in & 15) * 16 + (x_in & 15)
    bit_index = idx * bits
    long_index = bit_index >> 6
    start = bit_index & 63
    mask = (1 << bits) - 1
    a0 = hm_longs[long_index] & ((1 << 64) - 1)
    v = (a0 >> start) & mask
    spill = start + bits - 64
    if spill > 0:
        a1 = hm_longs[long_index + 1] & ((1 << 64) - 1)
        v |= (a1 & ((1 << spill) - 1)) << (bits - spill)
    return int(v)


def _light_arr_ok(arr: Optional[bytes]) -> bool:
    return arr is not None and len(arr) >= LIGHT_NIBBLE_BYTES


@dataclass
class Section:
    y: int
    palette: List[str]
    data: Optional[List[int]]
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
    heightmaps: Dict[str, List[int]]

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

    def light_info(self, x: int, y: int, z: int, *, require_sky: bool) -> Tuple[Optional[int], bool]:
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

    def height_at(self, x: int, z: int, *, heightmap_type: str, min_y: int) -> int:
        hm = self.heightmaps.get(heightmap_type)
        if not hm:
            raise NBTError(f"heightmap missing: {heightmap_type}")
        lx = x - (self.cx << 4)
        lz = z - (self.cz << 4)
        if not (0 <= lx <= 15 and 0 <= lz <= 15):
            raise NBTError("local height coords out of bounds")
        return min_y + _heightmap_get(hm, lx, lz, bits=9) - 1


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
    _ = buf.read_string()

    out = {"sections": [], "heightmaps": {}}
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
        if name == "Heightmaps" and t == TAG_COMPOUND:
            out["heightmaps"] = _read_tag_payload(t, buf)
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
                                for _ in range(max(0, p_ln)):
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
                                for _ in range(max(0, p_ln)):
                                    _skip_tag_payload(p_inner, buf)
                            bs["palette"] = palette
                            continue
                        if bn == "data" and bt == TAG_LONG_ARRAY:
                            arr = _read_tag_payload(bt, buf)
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
    heightmaps: Dict[str, List[int]] = {}
    for key, value in (out.get("heightmaps") or {}).items():
        if isinstance(value, list):
            heightmaps[str(key)] = [int(v) for v in value]
    sections: Dict[int, Section] = {}
    for s in out.get("sections", []):
        y = int(s.get("Y", 0))
        bs = s.get("block_states") or {}
        palette = bs.get("palette") or ["minecraft:air"]
        sections[y] = Section(
            y=y,
            palette=palette,
            data=bs.get("data"),
            block_light=s.get("BlockLight"),
            sky_light=s.get("SkyLight"),
        )
    return Chunk(cx=cx, cz=cz, is_light_on=is_light_on, sections=sections, heightmaps=heightmaps)


class WorldReader:
    def __init__(self, world_dir: Path, *, dimension: str = "overworld", min_y: int = -64):
        self.world_dir = world_dir
        self.min_y = min_y
        if dimension == "overworld":
            self.region_dir = world_dir / "region"
        elif dimension == "nether":
            self.region_dir = world_dir / "DIM-1" / "region"
        elif dimension == "end":
            self.region_dir = world_dir / "DIM1" / "region"
        else:
            raise ValueError(f"unknown dimension: {dimension}")
        self._require_sky_light = dimension != "nether"
        self._region_cache: Dict[Tuple[int, int], Optional[RegionFile]] = {}
        self._chunk_cache: Dict[Tuple[int, int], Optional[Chunk]] = {}

    def region_exists_for_chunk(self, cx: int, cz: int) -> bool:
        return (self.region_dir / f"r.{cx // 32}.{cz // 32}.mca").exists()

    def _get_region(self, rx: int, rz: int) -> Optional[RegionFile]:
        key = (rx, rz)
        if key in self._region_cache:
            return self._region_cache[key]
        path = self.region_dir / f"r.{rx}.{rz}.mca"
        if not path.exists():
            self._region_cache[key] = None
            return None
        rf = RegionFile(path)
        self._region_cache[key] = rf
        return rf

    def get_chunk(self, cx: int, cz: int) -> Optional[Chunk]:
        key = (cx, cz)
        if key in self._chunk_cache:
            return self._chunk_cache[key]
        rf = self._get_region(cx // 32, cz // 32)
        if rf is None:
            self._chunk_cache[key] = None
            return None
        raw = rf.read_chunk_nbt(cx, cz)
        if raw is None:
            self._chunk_cache[key] = None
            return None
        chunk = _parse_chunk(raw)
        self._chunk_cache[key] = chunk
        return chunk

    def block_name(self, x: int, y: int, z: int) -> str:
        chunk = self.get_chunk(x // 16, z // 16)
        if chunk is None:
            return "minecraft:air"
        return chunk.block_name(x, y, z)

    def light_info(self, x: int, y: int, z: int) -> Tuple[Optional[int], bool]:
        chunk = self.get_chunk(x // 16, z // 16)
        if chunk is None:
            return None, False
        return chunk.light_info(x, y, z, require_sky=self._require_sky_light)

    def height_at(self, x: int, z: int, *, heightmap_type: str = "MOTION_BLOCKING_NO_LEAVES") -> int:
        chunk = self.get_chunk(x // 16, z // 16)
        if chunk is None:
            raise FileNotFoundError(f"missing chunk for x={x} z={z}")
        return chunk.height_at(x, z, heightmap_type=heightmap_type, min_y=self.min_y)


def chunk_box_from_block_box(x1: int, z1: int, x2: int, z2: int) -> Tuple[int, int, int, int]:
    return x1 >> 4, z1 >> 4, x2 >> 4, z2 >> 4


def is_air(name: str) -> bool:
    return name in AIR_BLOCKS


def is_liquid(name: str) -> bool:
    return name in LIQUID_BLOCKS
