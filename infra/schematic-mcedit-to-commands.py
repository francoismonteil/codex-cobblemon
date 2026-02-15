#!/usr/bin/env python3
"""
Convert a classic MCEdit/WorldEdit "Alpha" .schematic (Blocks/Data, optional AddBlocks)
into vanilla Minecraft commands (fill/setblock) using modern (flattened) block names.

Scope:
- Designed for this repo's infra workflows: generate a command stream that can be
  piped to the running server console (itzg/minecraft-server console pipe).
- Not a general purpose converter: block mapping is best-effort and currently
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
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


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
        return buf.read_i8()
    if tag == TAG_SHORT:
        return buf.read_i16()
    if tag == TAG_INT:
        return buf.read_i32()
    if tag == TAG_LONG:
        return buf.read_i64()
    if tag == TAG_FLOAT:
        # Not needed here; keep parser simple and memory-light.
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


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Convert MCEdit Alpha .schematic to Minecraft commands")
    ap.add_argument("--schematic", required=True, help="Path to .schematic (MCEdit/Alpha format)")
    ap.add_argument("--origin", nargs=3, required=True, type=int, metavar=("X", "Y", "Z"), help="Paste origin in world coords (integers)")
    ap.add_argument("--dx", type=int, default=0, help="Extra offset on X (applied on top of origin)")
    ap.add_argument("--dy", type=int, default=0, help="Extra offset on Y (applied on top of origin)")
    ap.add_argument("--dz", type=int, default=0, help="Extra offset on Z (applied on top of origin)")
    ap.add_argument("--no-we-offset", action="store_true", help="Ignore WEOffsetX/Y/Z tags if present")
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
    w, h, l, blocks, we_off = _iter_blocks_mcedit(root)

    off_x, off_y, off_z = we_off
    if args.no_we_offset:
        off_x = off_y = off_z = 0

    origin_x, origin_y, origin_z = args.origin
    base_x = origin_x + args.dx + off_x
    base_y = origin_y + args.dy + off_y
    base_z = origin_z + args.dz + off_z

    if args.print_bounds:
        x1 = base_x
        y1 = base_y
        z1 = base_z
        x2 = base_x + (w - 1)
        y2 = base_y + (h - 1)
        z2 = base_z + (l - 1)
        print(x1, y1, z1, x2, y2, z2)
        return 0

    if args.erase and args.clear:
        print("ERROR: --erase and --clear are mutually exclusive", file=sys.stderr)
        return 2

    # Sort: main blocks first, then attachables. Within a phase, low->high Y reduces support breakage.
    blocks_sorted = sorted(blocks, key=lambda b: (b.phase, b.y, b.z, b.x))

    out_lines: List[str] = []

    if args.erase:
        for b in blocks_sorted:
            wx = base_x + b.x
            wy = base_y + b.y
            wz = base_z + b.z
            out_lines.append(f"setblock {wx} {wy} {wz} minecraft:air replace")
        payload = "\n".join(out_lines) + "\n"

        if args.output == "-" or args.output == "":
            sys.stdout.write(payload)
            return 0

        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8", errors="strict")
        return 0

    if args.clear:
        pad = max(0, args.clear_pad)
        x1 = base_x - pad
        y1 = base_y - pad
        z1 = base_z - pad
        x2 = base_x + (w - 1) + pad
        y2 = base_y + (h - 1) + pad
        z2 = base_z + (l - 1) + pad
        out_lines.append(f"fill {x1} {y1} {z1} {x2} {y2} {z2} minecraft:air replace")

    unmapped: Dict[Tuple[int, int], int] = {}
    for b in blocks_sorted:
        try:
            block_str = map_block(b.block_id, b.data)
        except Exception:
            unmapped[(b.block_id, b.data)] = unmapped.get((b.block_id, b.data), 0) + 1
            continue

        wx = base_x + b.x
        wy = base_y + b.y
        wz = base_z + b.z
        out_lines.append(f"setblock {wx} {wy} {wz} {block_str} replace")

    if unmapped:
        print("ERROR: unmapped blocks encountered:", file=sys.stderr)
        for (bid, md), cnt in sorted(unmapped.items()):
            print(f"  id={bid} data={md} count={cnt}", file=sys.stderr)
        print("Refusing to output partial command stream.", file=sys.stderr)
        return 1

    payload = "\n".join(out_lines) + "\n"

    if args.output == "-" or args.output == "":
        sys.stdout.write(payload)
        return 0

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload, encoding="utf-8", errors="strict")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
