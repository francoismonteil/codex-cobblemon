#!/usr/bin/env python3
"""
Convert a classic MCEdit/WorldEdit "Alpha" .schematic (Blocks/Data, optional AddBlocks)
into a modern Minecraft structure template .nbt usable by:
  - /place template <template>
  - worldgen (via jigsaw + structure set)

Output is written as *gzipped* NBT (like vanilla structure resources).

Notes:
- Applies WEOffsetX/Y/Z by default, then recenters so the minimum (x,y,z) becomes (0,0,0).
- Block entities are not converted (most mcbuild_org schematics don't use them). If needed, extend.
"""

from __future__ import annotations

import argparse
import gzip
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


# --- Minimal NBT reader (copied/trimmed from infra/schematic-mcedit-to-commands.py) ---
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
        return struct.unpack(">b", buf.read_bytes(1))[0]
    if tag == TAG_SHORT:
        return struct.unpack(">h", buf.read_bytes(2))[0]
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


def _load_nbt(path: Path) -> Dict:
    raw = path.read_bytes()
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


# --- Block mapping (copied from infra/schematic-mcedit-to-commands.py) ---
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
    if m == 2:
        return "north"
    if m == 3:
        return "south"
    if m == 4:
        return "west"
    return "east"


def _torch_block_from_meta(m: int) -> str:
    if m == 5:
        return "minecraft:torch"
    facing = {1: "west", 2: "east", 3: "north", 4: "south"}.get(m)
    if facing is None:
        return "minecraft:torch"
    return f"minecraft:wall_torch[facing={facing}]"


def _button_block_from_meta(m: int) -> str:
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
    half = "upper" if (m & 8) else "lower"
    if half == "lower":
        facing = {0: "east", 1: "south", 2: "west", 3: "north"}.get(m & 3, "north")
        open_ = "true" if (m & 4) else "false"
        return f"minecraft:{wood}_door[facing={facing},half=lower,hinge=right,open={open_},powered=false]"
    hinge = "left" if (m & 1) else "right"
    return f"minecraft:{wood}_door[facing=north,half=upper,hinge={hinge},open=false,powered=false]"


def _vine_block_from_meta(m: int) -> str:
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
        props.append("up=true")
    return "minecraft:vine[" + ",".join(props) + "]"


def _log_block(block_kind: str, meta: int) -> str:
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

    if axis_bits == 12:
        return f"minecraft:{wood}_wood[axis={axis}]"
    return f"minecraft:{wood}_log[axis={axis}]"


def _hay_block(meta: int) -> str:
    axis_bits = meta & 12
    if axis_bits == 4:
        axis = "x"
    elif axis_bits == 8:
        axis = "z"
    else:
        axis = "y"
    return f"minecraft:hay_block[axis={axis}]"


def map_block(block_id: int, data: int) -> str:
    if block_id == 0:
        return "minecraft:air"

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

    if block_id == 4:
        return "minecraft:cobblestone"
    if block_id == 48:
        return "minecraft:mossy_cobblestone"
    if block_id == 98:
        if data == 1:
            return "minecraft:mossy_stone_bricks"
        if data == 2:
            return "minecraft:cracked_stone_bricks"
        if data == 3:
            return "minecraft:chiseled_stone_bricks"
        return "minecraft:stone_bricks"
    if block_id == 139:
        return "minecraft:cobblestone_wall"

    if block_id == 5:
        wood = _PLANKS[data & 7]
        return f"minecraft:{wood}_planks"
    if block_id == 17:
        return _log_block("log", data)
    if block_id == 162:
        return _log_block("log2", data)

    if block_id == 18:
        wood = _LOG[data & 3]
        return f"minecraft:{wood}_leaves[persistent=true]"

    if block_id == 30:
        return "minecraft:cobweb"
    if block_id == 31:
        if data == 2:
            return "minecraft:fern"
        return "minecraft:short_grass"
    if block_id == 35:
        color = _COLOR[data & 15]
        return f"minecraft:{color}_wool"
    if block_id == 37:
        return "minecraft:dandelion"
    if block_id == 38:
        if data == 3:
            return "minecraft:azure_bluet"
        if data == 8:
            return "minecraft:oxeye_daisy"
        return "minecraft:poppy"

    if block_id == 159:
        color = _COLOR[data & 15]
        return f"minecraft:{color}_terracotta"

    if block_id == 43:
        t = data & 7
        if t == 3:
            return "minecraft:cobblestone_slab[type=double]"
        if t == 5:
            return "minecraft:stone_brick_slab[type=double]"
        return "minecraft:stone"
    if block_id == 44:
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
        top = bool(data & 8)
        slab_type = "bottom" if not top else "top"
        wood = _PLANKS[data & 7]
        return f"minecraft:{wood}_slab[type={slab_type}]"

    if block_id == 50:
        return _torch_block_from_meta(data)
    if block_id == 54:
        facing = _chest_facing_from_meta(data)
        return f"minecraft:chest[facing={facing}]"
    if block_id == 59:
        age = max(0, min(7, data & 7))
        return f"minecraft:wheat[age={age}]"
    if block_id == 60:
        moisture = max(0, min(7, data & 7))
        return f"minecraft:farmland[moisture={moisture}]"
    if block_id == 77:
        return _button_block_from_meta(data)
    if block_id == 85:
        return "minecraft:oak_fence"
    if block_id == 106:
        return _vine_block_from_meta(data)
    if block_id == 154:
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

    if block_id == 137:
        return "minecraft:air"

    raise KeyError(f"unmapped block id={block_id} data={data}")


@dataclass(frozen=True)
class _B:
    x: int
    y: int
    z: int
    block_id: int
    data: int


def _iter_blocks_mcedit(root: Dict) -> Tuple[int, int, int, List[_B], Tuple[int, int, int]]:
    try:
        w = int(root["Width"])
        h = int(root["Height"])
        l = int(root["Length"])
    except Exception as e:
        raise SystemExit(f"Invalid/missing Width/Height/Length: {e}")

    blocks = root.get("Blocks")
    data = root.get("Data")
    add = root.get("AddBlocks")

    if not isinstance(blocks, (bytes, bytearray)) or not isinstance(data, (bytes, bytearray)):
        raise SystemExit("Not an MCEdit Alpha schematic (expected Blocks/Data byte arrays).")

    expected = w * h * l
    if len(blocks) != expected or len(data) != expected:
        raise SystemExit(f"Blocks/Data length mismatch (got {len(blocks)}/{len(data)}, expected {expected}).")

    we_off_x = int(root.get("WEOffsetX") or 0)
    we_off_y = int(root.get("WEOffsetY") or 0)
    we_off_z = int(root.get("WEOffsetZ") or 0)

    out: List[_B] = []
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
        out.append(_B(x=x, y=y, z=z, block_id=int(bid), data=int(md)))

    return w, h, l, out, (we_off_x, we_off_y, we_off_z)


# --- Minimal NBT writer (only the types we use) ---
def _enc_u8(v: int) -> bytes:
    return bytes([v & 0xFF])


def _enc_i16(v: int) -> bytes:
    return struct.pack(">h", int(v))


def _enc_i32(v: int) -> bytes:
    return struct.pack(">i", int(v))


def _enc_string(s: str) -> bytes:
    b = s.encode("utf-8", errors="strict")
    if len(b) > 65535:
        raise ValueError("string too long for NBT")
    return struct.pack(">H", len(b)) + b


def _tag(tag_id: int, name: str, payload: bytes) -> bytes:
    return _enc_u8(tag_id) + _enc_string(name) + payload


def _compound_payload(items: Iterable[bytes]) -> bytes:
    return b"".join(items) + _enc_u8(TAG_END)


def _list_payload(inner_tag: int, items_payload: Iterable[bytes]) -> bytes:
    items = list(items_payload)
    return _enc_u8(inner_tag) + _enc_i32(len(items)) + b"".join(items)


def _int_array_payload(vals: List[int]) -> bytes:
    return _enc_i32(len(vals)) + b"".join(_enc_i32(v) for v in vals)


def _parse_block_state(s: str) -> Tuple[str, Dict[str, str]]:
    # Input in command-ish form: minecraft:foo[prop=a,bar=b]
    # Output suitable for NBT palette: Name + Properties compound of strings.
    if "[" not in s:
        return s, {}
    if not s.endswith("]"):
        raise ValueError(f"invalid block state string: {s}")
    name, props = s.split("[", 1)
    props = props[:-1].strip()
    if not props:
        return name, {}
    out: Dict[str, str] = {}
    for part in props.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"invalid block property segment: {part} in {s}")
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return name, out


def _nbt_string(name: str, s: str) -> bytes:
    return _tag(TAG_STRING, name, _enc_string(s))


def _nbt_int(name: str, v: int) -> bytes:
    return _tag(TAG_INT, name, _enc_i32(v))


def _nbt_int_array(name: str, vals: List[int]) -> bytes:
    return _tag(TAG_INT_ARRAY, name, _int_array_payload(vals))

def _nbt_list_int(name: str, vals: List[int]) -> bytes:
    # Structure templates use TAG_List(TAG_Int) for e.g. "size" and block "pos".
    return _tag(TAG_LIST, name, _enc_u8(TAG_INT) + _enc_i32(len(vals)) + b"".join(_enc_i32(v) for v in vals))


def _nbt_compound(name: str, children: Iterable[bytes]) -> bytes:
    return _tag(TAG_COMPOUND, name, _compound_payload(children))


def _nbt_list_compound(name: str, compounds_payload: Iterable[bytes]) -> bytes:
    return _tag(TAG_LIST, name, _list_payload(TAG_COMPOUND, compounds_payload))


def _palette_entry_payload(block_state: str) -> bytes:
    bname, props = _parse_block_state(block_state)
    kids = [_nbt_string("Name", bname)]
    if props:
        prop_kids = [_nbt_string(k, v) for k, v in sorted(props.items())]
        kids.append(_nbt_compound("Properties", prop_kids))
    return _compound_payload(kids)


def _blocks_entry_payload(state_idx: int, x: int, y: int, z: int) -> bytes:
    kids = [
        _nbt_int("state", state_idx),
        _nbt_list_int("pos", [x, y, z]),
    ]
    return _compound_payload(kids)


def _write_structure_nbt_gz(
    path: Path,
    *,
    size_xyz: Tuple[int, int, int],
    palette: List[str],
    blocks: List[Tuple[int, int, int, int]],
    data_version: int,
) -> None:
    # Root compound payload.
    sx, sy, sz = size_xyz

    palette_payloads = (_palette_entry_payload(p) for p in palette)
    blocks_payloads = (_blocks_entry_payload(state, x, y, z) for (x, y, z, state) in blocks)

    root_children = [
        _nbt_int("DataVersion", data_version),
        _nbt_list_int("size", [sx, sy, sz]),
        _nbt_list_compound("palette", palette_payloads),
        _nbt_list_compound("blocks", blocks_payloads),
        _nbt_list_compound("entities", []),
    ]

    root = _enc_u8(TAG_COMPOUND) + _enc_string("") + _compound_payload(root_children)
    gz = gzip.compress(root)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gz)


def _convert(*, schematic_path: Path, output_path: Path, apply_we_offset: bool, data_version: int) -> None:
    root = _load_nbt(schematic_path)
    _w, _h, _l, blocks0, we_off = _iter_blocks_mcedit(root)

    off_x, off_y, off_z = we_off
    if not apply_we_offset:
        off_x = off_y = off_z = 0

    # First pass: map blocks and apply WE offsets.
    unmapped: Dict[Tuple[int, int], int] = {}
    mapped: List[Tuple[int, int, int, str]] = []
    for b in blocks0:
        try:
            bs = map_block(b.block_id, b.data)
        except Exception:
            unmapped[(b.block_id, b.data)] = unmapped.get((b.block_id, b.data), 0) + 1
            continue
        mapped.append((b.x + off_x, b.y + off_y, b.z + off_z, bs))

    if unmapped:
        print("ERROR: unmapped blocks encountered:", file=sys.stderr)
        for (bid, md), cnt in sorted(unmapped.items()):
            print(f"  id={bid} data={md} count={cnt}", file=sys.stderr)
        raise SystemExit(1)

    if not mapped:
        raise SystemExit("ERROR: schematic contains no non-air blocks after mapping")

    min_x = min(x for x, _y, _z, _bs in mapped)
    min_y = min(y for _x, y, _z, _bs in mapped)
    min_z = min(z for _x, _y, z, _bs in mapped)
    max_x = max(x for x, _y, _z, _bs in mapped)
    max_y = max(y for _x, y, _z, _bs in mapped)
    max_z = max(z for _x, _y, z, _bs in mapped)

    # Recenter so mins are at 0,0,0.
    shifted: List[Tuple[int, int, int, str]] = [(x - min_x, y - min_y, z - min_z, bs) for (x, y, z, bs) in mapped]

    size_xyz = (max_x - min_x + 1, max_y - min_y + 1, max_z - min_z + 1)

    # Palette + blocks array.
    pal_idx: Dict[str, int] = {}
    palette: List[str] = []
    blocks: List[Tuple[int, int, int, int]] = []
    for x, y, z, bs in shifted:
        if bs == "minecraft:air":
            continue
        idx = pal_idx.get(bs)
        if idx is None:
            idx = len(palette)
            pal_idx[bs] = idx
            palette.append(bs)
        blocks.append((x, y, z, idx))

    _write_structure_nbt_gz(output_path, size_xyz=size_xyz, palette=palette, blocks=blocks, data_version=data_version)


def _self_test(output_path: Path, *, data_version: int) -> None:
    palette = [
        "minecraft:stone",
        "minecraft:oak_stairs[facing=east,half=bottom]",
    ]
    blocks = [
        (0, 0, 0, 0),
        (1, 0, 0, 1),
    ]
    _write_structure_nbt_gz(output_path, size_xyz=(2, 1, 1), palette=palette, blocks=blocks, data_version=data_version)

    # Read back to catch obvious writer mistakes.
    root = _load_nbt(output_path)
    if root.get("size") != [2, 1, 1]:
        raise SystemExit("self-test: unexpected size after reload")
    if not isinstance(root.get("palette"), list) or len(root["palette"]) != 2:
        raise SystemExit("self-test: palette missing/invalid after reload")
    if not isinstance(root.get("blocks"), list) or len(root["blocks"]) != 2:
        raise SystemExit("self-test: blocks missing/invalid after reload")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Convert MCEdit Alpha .schematic to structure template .nbt (gzipped)")
    ap.add_argument("--schematic", help="Path to .schematic (MCEdit/Alpha format)")
    ap.add_argument("--output", required=True, help="Output .nbt path (will be gzipped NBT)")
    ap.add_argument("--no-we-offset", action="store_true", help="Ignore WEOffsetX/Y/Z tags if present")
    ap.add_argument(
        "--data-version",
        type=int,
        default=3955,  # Minecraft 1.21.1
        help="Structure NBT DataVersion (default: 3955 for Minecraft 1.21.1)",
    )
    ap.add_argument("--self-test", action="store_true", help="Write a tiny structure to --output and verify by reloading it")
    args = ap.parse_args(argv)

    out = Path(args.output)
    if args.self_test:
        _self_test(out, data_version=int(args.data_version))
        return 0

    if not args.schematic:
        print("Missing --schematic (or use --self-test)", file=sys.stderr)
        return 2

    schematic_path = Path(args.schematic)
    if not schematic_path.exists():
        print(f"Missing schematic: {schematic_path}", file=sys.stderr)
        return 2

    _convert(
        schematic_path=schematic_path,
        output_path=out,
        apply_we_offset=(not args.no_we_offset),
        data_version=int(args.data_version),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
