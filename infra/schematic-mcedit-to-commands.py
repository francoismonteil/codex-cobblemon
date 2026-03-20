#!/usr/bin/env python3
"""
Convert supported schematic formats into vanilla Minecraft commands (fill/setblock)
using modern block names.

Scope:
- Designed for this repo's infra workflows: generate a command stream that can be
  piped to the running server console (itzg/minecraft-server console pipe).
- Supports:
  - classic MCEdit/WorldEdit "Alpha" `.schematic` files (`Blocks`/`Data`)
  - Sponge `.schem` version 2 files (`Palette`/`BlockData`)
- Not a general purpose converter: legacy block mapping is best-effort and currently
  focuses on the common blocks used by mcbuild_org-style schematics.

Usage (example):
  python3 infra/schematic-mcedit-to-commands.py \
    --schematic "downloads/Windmill - (mcbuild_org).schematic" \
    --origin 1000 70 -1400 \
    --dx 20 --dz 0 \
    --clear \
    --output /tmp/windmill.cmds

Erase (remove a previously pasted schematic at the same origin/offset):
  python3 infra/schematic-mcedit-to-commands.py \
    --schematic "downloads/Windmill - (mcbuild_org).schematic" \
    --origin 1000 70 -1400 \
    --dx 20 --dz 0 \
    --erase \
    --output /tmp/windmill-erase.cmds
"""

from __future__ import annotations

import argparse
import gzip
import math
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# --- Minimal NBT reader (copied/trimmed from infra/prefab-score.py; no external deps) ---
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


class NbtByte(int):
    pass


class NbtShort(int):
    pass


class NbtInt(int):
    pass


class NbtLong(int):
    pass


class NbtFloat(float):
    pass


class NbtDouble(float):
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


def _read_tag_payload(tag: int, buf: _Buf):
    if tag == TAG_BYTE:
        return NbtByte(buf.read_i8())
    if tag == TAG_SHORT:
        return NbtShort(buf.read_i16())
    if tag == TAG_INT:
        return NbtInt(buf.read_i32())
    if tag == TAG_LONG:
        return NbtLong(buf.read_i64())
    if tag == TAG_FLOAT:
        return NbtFloat(struct.unpack(">f", buf.read_bytes(4))[0])
    if tag == TAG_DOUBLE:
        return NbtDouble(struct.unpack(">d", buf.read_bytes(8))[0])
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
        return [NbtInt(struct.unpack(">i", buf.read_bytes(4))[0]) for _ in range(ln)]
    if tag == TAG_LONG_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative long array length")
        return [NbtLong(struct.unpack(">q", buf.read_bytes(8))[0]) for _ in range(ln)]
    raise NBTError(f"unknown tag {tag}")


def _load_nbt(path: Path) -> Dict:
    raw = path.read_bytes()
    # .schematic is usually GZip'd NBT.
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass

    buf = _Buf(raw)
    t = buf.read_u8()
    if t != TAG_COMPOUND:
        raise NBTError(f"unexpected root tag: {t} (expected compound)")
    _ = buf.read_string()  # root name (often empty)
    root = _read_tag_payload(TAG_COMPOUND, buf)
    if not isinstance(root, dict):
        raise NBTError("root compound parse failed")
    return root


def _nibble(arr: Optional[bytes], idx: int) -> int:
    if not arr:
        return 0
    b = arr[idx >> 1]
    if idx & 1:
        return (b >> 4) & 0x0F
    return b & 0x0F


# --- Block mapping ---

_COLOR = [
    "white",
    "orange",
    "magenta",
    "light_blue",
    "yellow",
    "lime",
    "pink",
    "gray",
    "light_gray",
    "cyan",
    "purple",
    "blue",
    "brown",
    "green",
    "red",
    "black",
]

_PLANKS = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak"]
_LOG = ["oak", "spruce", "birch", "jungle"]
_LOG2 = ["acacia", "dark_oak"]


def _stairs_facing_from_meta(m: int) -> str:
    # Pre-flattening stairs:
    # 0 east, 1 west, 2 south, 3 north (+4 => upside down).
    d = m & 3
    if d == 0:
        return "east"
    if d == 1:
        return "west"
    if d == 2:
        return "south"
    return "north"


def _stairs_half_from_meta(m: int) -> str:
    return "top" if (m & 4) else "bottom"


def _chest_facing_from_meta(m: int) -> str:
    # Pre-flattening chest:
    # 2 north, 3 south, 4 west, 5 east.
    if m == 2:
        return "north"
    if m == 3:
        return "south"
    if m == 4:
        return "west"
    return "east"


def _torch_block_from_meta(m: int) -> str:
    # Pre-flattening torch:
    # 1 east, 2 west, 3 south, 4 north, 5 up.
    if m == 5:
        return "minecraft:torch"
    # NOTE: For wall_torch, the modern "facing" points *toward* the supporting block.
    # Example: if the torch is on a block's east face, the supporting block is west.
    facing = {1: "west", 2: "east", 3: "north", 4: "south"}.get(m)
    if facing is None:
        # Fallback: a standing torch is always safe.
        return "minecraft:torch"
    return f"minecraft:wall_torch[facing={facing}]"


def _button_block_from_meta(m: int) -> str:
    # Pre-flattening stone button:
    # 2 west, 3 east, 4 north, 5 south, 1 top, 0/6 bottom.
    if m == 2:
        return "minecraft:stone_button[face=wall,facing=west]"
    if m == 3:
        return "minecraft:stone_button[face=wall,facing=east]"
    if m == 4:
        return "minecraft:stone_button[face=wall,facing=north]"
    if m == 5:
        return "minecraft:stone_button[face=wall,facing=south]"
    if m == 1:
        return "minecraft:stone_button[face=ceiling,facing=north]"
    return "minecraft:stone_button[face=floor,facing=north]"


def _door_blocks_from_meta(m: int, wood: str) -> str:
    # Pre-flattening doors:
    # - lower half (m<8): 0 east, 1 south, 2 west, 3 north; +4=open; +8=upper half marker (not used here)
    # - upper half (m>=8): 8..15 with hinge bit in LSB (0 right, 1 left)
    half = "upper" if (m & 8) else "lower"
    if half == "lower":
        facing = {0: "east", 1: "south", 2: "west", 3: "north"}.get(m & 3, "north")
        open_ = "true" if (m & 4) else "false"
        return f"minecraft:{wood}_door[facing={facing},half=lower,hinge=right,open={open_},powered=false]"
    hinge = "left" if (m & 1) else "right"
    return f"minecraft:{wood}_door[facing=north,half=upper,hinge={hinge},open=false,powered=false]"


def _vine_block_from_meta(m: int) -> str:
    # Pre-flattening vines: bitmask of sides
    # 0x1 south, 0x2 west, 0x4 north, 0x8 east
    props = []
    if m & 1:
        props.append("south=true")
    if m & 2:
        props.append("west=true")
    if m & 4:
        props.append("north=true")
    if m & 8:
        props.append("east=true")
    if not props:
        # Shouldn't happen in sane schematics; use an 'up' vine as fallback.
        props.append("up=true")
    return "minecraft:vine[" + ",".join(props) + "]"


def _log_block(block_kind: str, meta: int) -> str:
    # block_kind: "log" (id 17) or "log2" (id 162)
    if block_kind == "log":
        wood = _LOG[meta & 3]
    else:
        wood = _LOG2[meta & 1]

    axis_bits = meta & 12
    if axis_bits == 4:
        axis = "x"
    elif axis_bits == 8:
        axis = "z"
    else:
        axis = "y"

    # 12 means "all bark" in pre-flattening metadata.
    if axis_bits == 12:
        return f"minecraft:{wood}_wood[axis={axis}]"
    return f"minecraft:{wood}_log[axis={axis}]"


def _hay_block(meta: int) -> str:
    # Hay bale uses rotation data similar to logs: 0=y, 4=x, 8=z.
    axis_bits = meta & 12
    if axis_bits == 4:
        axis = "x"
    elif axis_bits == 8:
        axis = "z"
    else:
        axis = "y"
    return f"minecraft:hay_block[axis={axis}]"


def map_block(block_id: int, data: int) -> str:
    # NOTE: This mapping is intentionally conservative. Unknown blocks will raise,
    # so we don't silently place the wrong thing.
    if block_id == 0:
        return "minecraft:air"

    # Natural
    if block_id == 2:
        return "minecraft:grass_block"
    if block_id == 3:
        if data == 0:
            return "minecraft:dirt"
        if data == 1:
            return "minecraft:coarse_dirt"
        if data == 2:
            return "minecraft:podzol"
        return "minecraft:dirt"

    # Stone / building
    if block_id == 4:
        return "minecraft:cobblestone"
    if block_id == 48:
        return "minecraft:mossy_cobblestone"
    if block_id == 98:
        # 0 normal, 1 mossy, 2 cracked, 3 chiseled
        if data == 1:
            return "minecraft:mossy_stone_bricks"
        if data == 2:
            return "minecraft:cracked_stone_bricks"
        if data == 3:
            return "minecraft:chiseled_stone_bricks"
        return "minecraft:stone_bricks"
    if block_id == 139:
        return "minecraft:cobblestone_wall"

    # Wood
    if block_id == 5:
        wood = _PLANKS[data & 7]
        return f"minecraft:{wood}_planks"
    if block_id == 17:
        return _log_block("log", data)
    if block_id == 162:
        return _log_block("log2", data)

    # Leaves
    if block_id == 18:
        wood = _LOG[data & 3]
        # Ensure leaves don't decay when placed by commands.
        return f"minecraft:{wood}_leaves[persistent=true]"

    # Plants / decor
    if block_id == 30:
        return "minecraft:cobweb"
    if block_id == 31:
        # Tallgrass: 1 short grass, 2 fern.
        if data == 2:
            return "minecraft:fern"
        return "minecraft:short_grass"
    if block_id == 35:
        color = _COLOR[data & 15]
        return f"minecraft:{color}_wool"
    if block_id == 37:
        return "minecraft:dandelion"
    if block_id == 38:
        # Red flower variants (1.7+): 0 poppy, 3 azure bluet, 8 oxeye daisy
        if data == 3:
            return "minecraft:azure_bluet"
        if data == 8:
            return "minecraft:oxeye_daisy"
        return "minecraft:poppy"

    # Terracotta
    if block_id == 159:
        color = _COLOR[data & 15]
        return f"minecraft:{color}_terracotta"

    # Slabs / stairs
    if block_id == 43:
        # Double stone slab variants (data 0..7).
        t = data & 7
        if t == 3:
            return "minecraft:cobblestone_slab[type=double]"
        if t == 5:
            return "minecraft:stone_brick_slab[type=double]"
        # Fallback: solid block if we don't know the slab variant.
        return "minecraft:stone"
    if block_id == 44:
        # Stone slab variants. +8 means top.
        top = bool(data & 8)
        t = data & 7
        slab_type = "bottom" if not top else "top"
        if t == 3:
            return f"minecraft:cobblestone_slab[type={slab_type}]"
        if t == 5:
            return f"minecraft:stone_brick_slab[type={slab_type}]"
        return f"minecraft:stone_slab[type={slab_type}]"
    if block_id == 53:
        return f"minecraft:oak_stairs[facing={_stairs_facing_from_meta(data)},half={_stairs_half_from_meta(data)}]"
    if block_id == 67:
        return f"minecraft:cobblestone_stairs[facing={_stairs_facing_from_meta(data)},half={_stairs_half_from_meta(data)}]"
    if block_id == 109:
        return f"minecraft:stone_brick_stairs[facing={_stairs_facing_from_meta(data)},half={_stairs_half_from_meta(data)}]"
    if block_id == 126:
        # Wooden slab. 0 oak, +8 top.
        top = bool(data & 8)
        slab_type = "bottom" if not top else "top"
        wood = _PLANKS[data & 7]
        return f"minecraft:{wood}_slab[type={slab_type}]"

    # Functional
    if block_id == 50:
        return _torch_block_from_meta(data)
    if block_id == 54:
        facing = _chest_facing_from_meta(data)
        return f"minecraft:chest[facing={facing}]"
    if block_id == 59:
        # wheat age 0..7
        age = max(0, min(7, data & 7))
        return f"minecraft:wheat[age={age}]"
    if block_id == 60:
        # farmland moisture 0..7
        moisture = max(0, min(7, data & 7))
        return f"minecraft:farmland[moisture={moisture}]"
    if block_id == 77:
        return _button_block_from_meta(data)
    if block_id == 85:
        return "minecraft:oak_fence"
    if block_id == 106:
        return _vine_block_from_meta(data)
    if block_id == 154:
        # Hopper: 0 down, 2 north, 3 south, 4 west, 5 east. +8 disabled.
        enabled = "false" if (data & 8) else "true"
        d = data & 7
        facing = {0: "down", 2: "north", 3: "south", 4: "west", 5: "east"}.get(d, "down")
        return f"minecraft:hopper[facing={facing},enabled={enabled}]"
    if block_id == 170:
        return _hay_block(data)
    if block_id == 171:
        color = _COLOR[data & 15]
        return f"minecraft:{color}_carpet"
    if block_id == 197:
        return _door_blocks_from_meta(data, "dark_oak")

    # Avoid placing command blocks by default; they are commonly used as placeholders in older schematics.
    if block_id == 137:
        return "minecraft:air"

    raise KeyError(f"unmapped block id={block_id} data={data}")


ATTACH_AFTER_IDS = {
    31,  # short grass / fern
    37,  # dandelion
    38,  # flowers
    50,  # torches
    59,  # wheat
    77,  # button
    106,  # vines
    171,  # carpet
}

ATTACH_AFTER_BLOCKS = {
    "minecraft:comparator",
    "minecraft:ladder",
    "minecraft:lever",
    "minecraft:redstone_torch",
    "minecraft:redstone_wall_torch",
    "minecraft:redstone_wire",
    "minecraft:repeater",
    "minecraft:tripwire",
    "minecraft:tripwire_hook",
    "minecraft:vine",
}

ATTACH_AFTER_SUFFIXES = (
    "_banner",
    "_button",
    "_carpet",
    "_coral_fan",
    "_pressure_plate",
    "_sign",
    "_torch",
    "_wall_banner",
    "_wall_hanging_sign",
    "_wall_sign",
)

_SNBT_SIMPLE_KEY_RE = re.compile(r"^[A-Za-z0-9._+-]+$")
_CARDINAL_ORDER = ("north", "east", "south", "west")
_ROTATE_STEPS = {"none": 0, "y90": 1, "y180": 2, "y270": 3}


@dataclass(frozen=True)
class Block:
    x: int
    y: int
    z: int
    block_id: int
    data: int

    @property
    def phase(self) -> int:
        # 0: main blocks, 1: attachables/plants (needs supports placed first)
        return 1 if self.block_id in ATTACH_AFTER_IDS else 0


@dataclass(frozen=True)
class ModernBlock:
    x: int
    y: int
    z: int
    block_state: str
    block_entity_nbt: Optional[Dict[str, Any]] = None

    @property
    def phase(self) -> int:
        return _phase_from_block_state(self.block_state)


def _phase_from_block_state(block_state: str) -> int:
    name = block_state.split("[", 1)[0]
    if name in ATTACH_AFTER_BLOCKS:
        return 1
    if name.endswith(ATTACH_AFTER_SUFFIXES):
        return 1
    if name in {
        "minecraft:beetroots",
        "minecraft:carrots",
        "minecraft:dandelion",
        "minecraft:fern",
        "minecraft:potatoes",
        "minecraft:short_grass",
        "minecraft:sunflower",
        "minecraft:tall_grass",
        "minecraft:wheat",
    }:
        return 1
    return 0


def _decode_varints(raw: bytes) -> List[int]:
    out: List[int] = []
    i = 0
    while i < len(raw):
        value = 0
        shift = 0
        for _ in range(5):
            if i >= len(raw):
                raise SystemExit("Invalid Sponge BlockData: truncated varint")
            b = raw[i]
            i += 1
            value |= (b & 0x7F) << shift
            if (b & 0x80) == 0:
                out.append(value)
                break
            shift += 7
        else:
            raise SystemExit("Invalid Sponge BlockData: varint exceeds 5 bytes")
    return out


def _clean_block_entity_nbt(value: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    cleaned = {k: v for k, v in value.items() if k not in {"Id", "Pos", "id", "x", "y", "z"}}
    return cleaned or None


def _iter_blocks_sponge_v2(root: Dict) -> Tuple[int, int, int, List[ModernBlock], Tuple[int, int, int]]:
    try:
        w = int(root["Width"])
        h = int(root["Height"])
        l = int(root["Length"])
        version = int(root["Version"])
    except Exception as e:
        raise SystemExit(f"Invalid/missing Sponge dimensions/version: {e}")

    if version != 2:
        raise SystemExit(f"Unsupported Sponge schematic version: {version} (expected 2)")

    palette = root.get("Palette")
    block_data = root.get("BlockData")
    if not isinstance(palette, dict) or not isinstance(block_data, (bytes, bytearray)):
        raise SystemExit("Not a Sponge .schem v2 file (expected Palette/BlockData).")

    entities = root.get("Entities") or []
    if entities:
        raise SystemExit("Sponge .schem entities are not supported yet.")

    inv_palette: Dict[int, str] = {}
    for block_state, palette_idx in palette.items():
        if not isinstance(block_state, str):
            raise SystemExit("Invalid Sponge Palette entry: block state key must be string")
        idx = int(palette_idx)
        if idx in inv_palette:
            raise SystemExit(f"Invalid Sponge Palette: duplicate index {idx}")
        inv_palette[idx] = block_state

    values = _decode_varints(bytes(block_data))
    expected = w * h * l
    if len(values) != expected:
        raise SystemExit(f"Sponge BlockData length mismatch (got {len(values)}, expected {expected}).")

    raw_offset = root.get("Offset")
    if raw_offset is None:
        meta = root.get("Metadata")
        if isinstance(meta, dict):
            raw_offset = [meta.get("WEOffsetX", 0), meta.get("WEOffsetY", 0), meta.get("WEOffsetZ", 0)]
    if raw_offset is None:
        raw_offset = [0, 0, 0]
    if not isinstance(raw_offset, list) or len(raw_offset) != 3:
        raise SystemExit("Invalid Sponge Offset (expected integer[3])")
    offset = (int(raw_offset[0]), int(raw_offset[1]), int(raw_offset[2]))

    block_entities: Dict[Tuple[int, int, int], Dict[str, Any]] = {}
    for entry in root.get("BlockEntities") or []:
        if not isinstance(entry, dict):
            raise SystemExit("Invalid Sponge BlockEntities entry (expected compound)")
        pos = entry.get("Pos")
        if not isinstance(pos, list) or len(pos) != 3:
            raise SystemExit("Invalid Sponge BlockEntities.Pos (expected integer[3])")
        key = (int(pos[0]), int(pos[1]), int(pos[2]))
        cleaned = _clean_block_entity_nbt(entry)
        if cleaned:
            block_entities[key] = cleaned

    out: List[ModernBlock] = []
    for idx, palette_idx in enumerate(values):
        block_state = inv_palette.get(palette_idx)
        if block_state is None:
            raise SystemExit(f"Sponge BlockData references missing palette index: {palette_idx}")
        if block_state == "minecraft:air":
            continue
        x = idx % w
        z = (idx // w) % l
        y = idx // (w * l)
        out.append(
            ModernBlock(
                x=x,
                y=y,
                z=z,
                block_state=block_state,
                block_entity_nbt=block_entities.get((x, y, z)),
            )
        )

    return w, h, l, out, offset


def _iter_blocks_sponge_v3(root: Dict) -> Tuple[int, int, int, List[ModernBlock], Tuple[int, int, int]]:
    schem = root.get("Schematic")
    if not isinstance(schem, dict):
        raise SystemExit("Not a Sponge .schem v3 file (expected nested Schematic compound).")

    try:
        w = int(schem["Width"])
        h = int(schem["Height"])
        l = int(schem["Length"])
        version = int(schem["Version"])
    except Exception as e:
        raise SystemExit(f"Invalid/missing Sponge v3 dimensions/version: {e}")

    if version != 3:
        raise SystemExit(f"Unsupported Sponge schematic version: {version} (expected 3)")

    blocks = schem.get("Blocks")
    if not isinstance(blocks, dict):
        raise SystemExit("Invalid Sponge .schem v3 file (expected Blocks container).")

    palette = blocks.get("Palette")
    block_data = blocks.get("Data")
    if not isinstance(palette, dict) or not isinstance(block_data, (bytes, bytearray)):
        raise SystemExit("Invalid Sponge .schem v3 Blocks container (expected Palette/Data).")

    entities = schem.get("Entities") or []
    if entities:
        raise SystemExit("Sponge .schem entities are not supported yet.")

    inv_palette: Dict[int, str] = {}
    for block_state, palette_idx in palette.items():
        if not isinstance(block_state, str):
            raise SystemExit("Invalid Sponge v3 Palette entry: block state key must be string")
        idx = int(palette_idx)
        if idx in inv_palette:
            raise SystemExit(f"Invalid Sponge v3 Palette: duplicate index {idx}")
        inv_palette[idx] = block_state

    values = _decode_varints(bytes(block_data))
    expected = w * h * l
    if len(values) != expected:
        raise SystemExit(f"Sponge v3 Blocks.Data length mismatch (got {len(values)}, expected {expected}).")

    raw_offset = schem.get("Offset") or [0, 0, 0]
    if not isinstance(raw_offset, list) or len(raw_offset) != 3:
        raise SystemExit("Invalid Sponge v3 Offset (expected integer[3])")
    offset = (int(raw_offset[0]), int(raw_offset[1]), int(raw_offset[2]))

    block_entities: Dict[Tuple[int, int, int], Dict[str, Any]] = {}
    for entry in blocks.get("BlockEntities") or []:
        if not isinstance(entry, dict):
            raise SystemExit("Invalid Sponge v3 BlockEntities entry (expected compound)")
        pos = entry.get("Pos")
        if not isinstance(pos, list) or len(pos) != 3:
            raise SystemExit("Invalid Sponge v3 BlockEntities.Pos (expected integer[3])")
        key = (int(pos[0]), int(pos[1]), int(pos[2]))

        data = entry.get("Data")
        if isinstance(data, dict):
            cleaned = {k: v for k, v in data.items() if k not in {"id", "x", "y", "z"}}
        else:
            cleaned = _clean_block_entity_nbt(entry)
        if cleaned:
            block_entities[key] = cleaned

    out: List[ModernBlock] = []
    for idx, palette_idx in enumerate(values):
        block_state = inv_palette.get(palette_idx)
        if block_state is None:
            raise SystemExit(f"Sponge v3 Blocks.Data references missing palette index: {palette_idx}")
        if block_state == "minecraft:air":
            continue
        x = idx % w
        z = (idx // w) % l
        y = idx // (w * l)
        out.append(
            ModernBlock(
                x=x,
                y=y,
                z=z,
                block_state=block_state,
                block_entity_nbt=block_entities.get((x, y, z)),
            )
        )

    return w, h, l, out, offset


def _quote_snbt_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _format_snbt_float(value: float) -> str:
    if not math.isfinite(value):
        raise SystemExit(f"Unsupported non-finite float in NBT payload: {value!r}")
    text = repr(float(value))
    if "." not in text and "e" not in text and "E" not in text:
        text += ".0"
    return text


def _to_snbt(value: Any) -> str:
    if isinstance(value, str):
        return _quote_snbt_string(value)
    if isinstance(value, NbtByte):
        return f"{int(value)}b"
    if isinstance(value, NbtShort):
        return f"{int(value)}s"
    if isinstance(value, NbtLong):
        return f"{int(value)}l"
    if isinstance(value, NbtFloat):
        return f"{_format_snbt_float(float(value))}f"
    if isinstance(value, NbtDouble):
        return f"{_format_snbt_float(float(value))}d"
    if isinstance(value, bool):
        return "1b" if value else "0b"
    if isinstance(value, int):
        return str(int(value))
    if isinstance(value, float):
        return f"{_format_snbt_float(value)}d"
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            key = k if _SNBT_SIMPLE_KEY_RE.match(k) else _quote_snbt_string(k)
            parts.append(f"{key}:{_to_snbt(v)}")
        return "{" + ",".join(parts) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_to_snbt(v) for v in value) + "]"
    if isinstance(value, (bytes, bytearray)):
        return "[B;" + ",".join(f"{NbtByte(struct.unpack('>b', bytes([b]))[0])}b" for b in value) + "]"
    raise SystemExit(f"Unsupported NBT value for SNBT serialization: {type(value).__name__}")


def _write_payload(output: str, payload: str) -> int:
    if output == "-" or output == "":
        sys.stdout.write(payload)
        return 0

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload, encoding="utf-8", errors="strict")
    return 0


def _rotate_cardinal(value: str, steps: int) -> str:
    if value not in _CARDINAL_ORDER:
        return value
    idx = _CARDINAL_ORDER.index(value)
    return _CARDINAL_ORDER[(idx + steps) % 4]


def _parse_block_state(block_state: str) -> Tuple[str, List[Tuple[str, str]]]:
    if "[" not in block_state or not block_state.endswith("]"):
        return block_state, []
    name, rest = block_state.split("[", 1)
    props_raw = rest[:-1]
    props: List[Tuple[str, str]] = []
    if props_raw:
        for item in props_raw.split(","):
            key, value = item.split("=", 1)
            props.append((key, value))
    return name, props


def _join_block_state(name: str, props: List[Tuple[str, str]]) -> str:
    if not props:
        return name
    return f"{name}[{','.join(f'{k}={v}' for k, v in props)}]"


def _rotate_state_properties(name: str, props: List[Tuple[str, str]], steps: int) -> List[Tuple[str, str]]:
    if steps == 0 or not props:
        return props

    prop_map = {k: v for k, v in props}
    original_keys = [k for k, _ in props]

    if "facing" in prop_map:
        prop_map["facing"] = _rotate_cardinal(prop_map["facing"], steps)
    if "axis" in prop_map:
        axis = prop_map["axis"]
        if axis == "x":
            prop_map["axis"] = "z" if steps % 2 == 1 else "x"
        elif axis == "z":
            prop_map["axis"] = "x" if steps % 2 == 1 else "z"
    if "shape" in prop_map:
        shape = prop_map["shape"]
        rail_shapes = {
            "north_south": ("east_west", "north_south", "east_west"),
            "east_west": ("north_south", "east_west", "north_south"),
            "ascending_north": ("ascending_east", "ascending_south", "ascending_west"),
            "ascending_east": ("ascending_south", "ascending_west", "ascending_north"),
            "ascending_south": ("ascending_west", "ascending_north", "ascending_east"),
            "ascending_west": ("ascending_north", "ascending_east", "ascending_south"),
            "south_east": ("south_west", "north_west", "north_east"),
            "south_west": ("north_west", "north_east", "south_east"),
            "north_west": ("north_east", "south_east", "south_west"),
            "north_east": ("south_east", "south_west", "north_west"),
        }
        if shape in rail_shapes:
            prop_map["shape"] = rail_shapes[shape][steps - 1]
    cardinal_snapshot = {key: prop_map[key] for key in ("north", "east", "south", "west") if key in prop_map}
    for key in cardinal_snapshot:
        prop_map.pop(key, None)
    for key, value in cardinal_snapshot.items():
        prop_map[_rotate_cardinal(key, steps)] = value

    seen = set()
    out: List[Tuple[str, str]] = []
    for key in original_keys:
        target = _rotate_cardinal(key, steps) if key in ("north", "east", "south", "west") else key
        if target in prop_map and target not in seen:
            out.append((target, prop_map[target]))
            seen.add(target)
    for key, value in prop_map.items():
        if key not in seen:
            out.append((key, value))
            seen.add(key)
    return out


def _rotate_block_state(block_state: str, steps: int) -> str:
    if steps == 0:
        return block_state
    name, props = _parse_block_state(block_state)
    rotated = _rotate_state_properties(name, props, steps)
    return _join_block_state(name, rotated)


def _rotate_coords(x: int, z: int, width: int, length: int, steps: int) -> Tuple[int, int]:
    if steps == 0:
        return x, z
    if steps == 1:
        return length - 1 - z, x
    if steps == 2:
        return width - 1 - x, length - 1 - z
    if steps == 3:
        return z, width - 1 - x
    raise AssertionError(f"invalid rotation steps: {steps}")


def _iter_blocks_mcedit(root: Dict) -> Tuple[int, int, int, List[Block], Tuple[int, int, int]]:
    try:
        w = int(root["Width"])
        h = int(root["Height"])
        l = int(root["Length"])
    except Exception as e:
        raise SystemExit(f"Invalid/missing Width/Height/Length: {e}")

    blocks = root.get("Blocks")
    data = root.get("Data")
    add = root.get("AddBlocks")  # optional

    if not isinstance(blocks, (bytes, bytearray)) or not isinstance(data, (bytes, bytearray)):
        raise SystemExit("Not an MCEdit Alpha schematic (expected Blocks/Data byte arrays).")

    expected = w * h * l
    if len(blocks) != expected or len(data) != expected:
        raise SystemExit(f"Blocks/Data length mismatch (got {len(blocks)}/{len(data)}, expected {expected}).")

    we_off_x = int(root.get("WEOffsetX") or 0)
    we_off_y = int(root.get("WEOffsetY") or 0)
    we_off_z = int(root.get("WEOffsetZ") or 0)

    out: List[Block] = []
    for idx in range(expected):
        bid = blocks[idx]
        if add:
            bid = bid | (_nibble(add, idx) << 8)
        if bid == 0:
            continue
        md = data[idx]
        x = idx % w
        z = (idx // w) % l
        y = idx // (w * l)
        out.append(Block(x=x, y=y, z=z, block_id=int(bid), data=int(md)))

    return w, h, l, out, (we_off_x, we_off_y, we_off_z)


def _detect_format(root: Dict) -> str:
    if isinstance(root.get("Blocks"), (bytes, bytearray)) and isinstance(root.get("Data"), (bytes, bytearray)):
        return "mcedit"
    if isinstance(root.get("Palette"), dict) and isinstance(root.get("BlockData"), (bytes, bytearray)):
        return "sponge_v2"
    schem = root.get("Schematic")
    if isinstance(schem, dict) and int(schem.get("Version") or 0) == 3:
        return "sponge_v3"
    raise SystemExit("Unsupported schematic format: expected MCEdit Alpha .schematic or Sponge .schem v2/v3.")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Convert supported schematic files to Minecraft commands")
    ap.add_argument("--schematic", required=True, help="Path to .schematic/.schem")
    ap.add_argument("--origin", nargs=3, required=True, type=int, metavar=("X", "Y", "Z"), help="Paste origin in world coords (integers)")
    ap.add_argument("--dx", type=int, default=0, help="Extra offset on X (applied on top of origin)")
    ap.add_argument("--dy", type=int, default=0, help="Extra offset on Y (applied on top of origin)")
    ap.add_argument("--dz", type=int, default=0, help="Extra offset on Z (applied on top of origin)")
    ap.add_argument("--rotate", choices=("none", "y90", "y180", "y270"), default="none", help="Rotate around Y before placing (clockwise when viewed from above)")
    ap.add_argument("--no-we-offset", action="store_true", help="Ignore stored paste offsets (WEOffsetX/Y/Z or Sponge Offset)")
    ap.add_argument("--print-bounds", action="store_true", help="Print computed bounds (x1 y1 z1 x2 y2 z2) and exit")
    ap.add_argument("--erase", action="store_true", help="Erase mode: emit setblock air for every non-air schematic block (no block mapping required)")
    ap.add_argument("--clear", action="store_true", help="Emit an initial /fill ... air to clear the target volume")
    ap.add_argument("--clear-pad", type=int, default=0, help="Extra padding around clear volume (default: 0)")
    ap.add_argument("--output", default="-", help="Output file (default stdout)")
    args = ap.parse_args(argv)

    schematic_path = Path(args.schematic)
    if not schematic_path.exists():
        print(f"Missing schematic: {schematic_path}", file=sys.stderr)
        return 2

    root = _load_nbt(schematic_path)
    fmt = _detect_format(root)
    modern_blocks: List[ModernBlock] = []
    legacy_blocks: List[Block] = []
    if fmt == "mcedit":
        w, h, l, legacy_blocks, stored_off = _iter_blocks_mcedit(root)
    elif fmt == "sponge_v2":
        w, h, l, modern_blocks, stored_off = _iter_blocks_sponge_v2(root)
    else:
        w, h, l, modern_blocks, stored_off = _iter_blocks_sponge_v3(root)

    off_x, off_y, off_z = stored_off
    if args.no_we_offset:
        off_x = off_y = off_z = 0

    origin_x, origin_y, origin_z = args.origin
    base_x = origin_x + args.dx + off_x
    base_y = origin_y + args.dy + off_y
    base_z = origin_z + args.dz + off_z
    rotate_steps = _ROTATE_STEPS[args.rotate]
    rot_w = l if rotate_steps % 2 == 1 else w
    rot_l = w if rotate_steps % 2 == 1 else l

    if args.print_bounds:
        x1 = base_x
        y1 = base_y
        z1 = base_z
        x2 = base_x + (rot_w - 1)
        y2 = base_y + (h - 1)
        z2 = base_z + (rot_l - 1)
        print(x1, y1, z1, x2, y2, z2)
        return 0

    if args.erase and args.clear:
        print("ERROR: --erase and --clear are mutually exclusive", file=sys.stderr)
        return 2

    out_lines: List[str] = []

    if args.erase:
        if fmt == "mcedit":
            blocks_sorted = sorted(legacy_blocks, key=lambda b: (b.phase, b.y, b.z, b.x))
            for b in blocks_sorted:
                rx, rz = _rotate_coords(b.x, b.z, w, l, rotate_steps)
                wx = base_x + rx
                wy = base_y + b.y
                wz = base_z + rz
                out_lines.append(f"setblock {wx} {wy} {wz} minecraft:air replace")
        else:
            blocks_sorted = sorted(modern_blocks, key=lambda b: (b.phase, b.y, b.z, b.x))
            for b in blocks_sorted:
                rx, rz = _rotate_coords(b.x, b.z, w, l, rotate_steps)
                wx = base_x + rx
                wy = base_y + b.y
                wz = base_z + rz
                out_lines.append(f"setblock {wx} {wy} {wz} minecraft:air replace")
        payload = "\n".join(out_lines) + "\n"
        return _write_payload(args.output, payload)

    if args.clear:
        pad = max(0, args.clear_pad)
        x1 = base_x - pad
        y1 = base_y - pad
        z1 = base_z - pad
        x2 = base_x + (rot_w - 1) + pad
        y2 = base_y + (h - 1) + pad
        z2 = base_z + (rot_l - 1) + pad
        out_lines.append(f"fill {x1} {y1} {z1} {x2} {y2} {z2} minecraft:air replace")

    if fmt == "mcedit":
        # Sort: main blocks first, then attachables. Within a phase, low->high Y reduces support breakage.
        blocks_sorted = sorted(legacy_blocks, key=lambda b: (b.phase, b.y, b.z, b.x))
        unmapped: Dict[Tuple[int, int], int] = {}
        for b in blocks_sorted:
            try:
                block_str = map_block(b.block_id, b.data)
            except Exception:
                unmapped[(b.block_id, b.data)] = unmapped.get((b.block_id, b.data), 0) + 1
                continue

            rx, rz = _rotate_coords(b.x, b.z, w, l, rotate_steps)
            wx = base_x + rx
            wy = base_y + b.y
            wz = base_z + rz
            out_lines.append(f"setblock {wx} {wy} {wz} {_rotate_block_state(block_str, rotate_steps)} replace")

        if unmapped:
            print("ERROR: unmapped blocks encountered:", file=sys.stderr)
            for (bid, md), cnt in sorted(unmapped.items()):
                print(f"  id={bid} data={md} count={cnt}", file=sys.stderr)
            print("Refusing to output partial command stream.", file=sys.stderr)
            return 1
    else:
        blocks_sorted = sorted(modern_blocks, key=lambda b: (b.phase, b.y, b.z, b.x))
        for b in blocks_sorted:
            rx, rz = _rotate_coords(b.x, b.z, w, l, rotate_steps)
            wx = base_x + rx
            wy = base_y + b.y
            wz = base_z + rz
            out_lines.append(f"setblock {wx} {wy} {wz} {_rotate_block_state(b.block_state, rotate_steps)} replace")
        for b in blocks_sorted:
            if not b.block_entity_nbt:
                continue
            rx, rz = _rotate_coords(b.x, b.z, w, l, rotate_steps)
            wx = base_x + rx
            wy = base_y + b.y
            wz = base_z + rz
            out_lines.append(f"data merge block {wx} {wy} {wz} {_to_snbt(b.block_entity_nbt)}")

    payload = "\n".join(out_lines) + "\n"
    return _write_payload(args.output, payload)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
