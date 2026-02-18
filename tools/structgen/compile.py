#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import gzip
import json
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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

DATA_VERSION_1_21_1 = 3955
SUPPORTED_BIOMES = ("plains", "desert", "savanna", "snowy", "taiga")
VALID_JIGSAW_ORIENTATIONS = {
    "down_east",
    "down_north",
    "down_south",
    "down_west",
    "east_up",
    "north_up",
    "south_up",
    "up_east",
    "up_north",
    "up_south",
    "up_west",
    "west_up",
}
HORIZONTAL = ("north", "east", "south", "west")
STATE_RE = re.compile(r"^(?P<name>[a-z0-9_./-]+:[a-z0-9_./-]+)(?:\[(?P<props>.*)\])?$")
PARAM_TOKEN_RE = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
PLAN_TYPES = {"pokecenter", "pokemart"}
BIOME_SET = set(SUPPORTED_BIOMES)


class StructgenError(Exception):
    pass


@dataclass
class NbtList:
    inner_tag: int
    items: list[Any]


@dataclass
class _Buf:
    b: bytes
    o: int = 0

    def read(self, n: int) -> bytes:
        if self.o + n > len(self.b):
            raise StructgenError("unexpected EOF while reading NBT")
        out = self.b[self.o : self.o + n]
        self.o += n
        return out

    def read_u8(self) -> int:
        return self.read(1)[0]

    def read_i16(self) -> int:
        return struct.unpack(">h", self.read(2))[0]

    def read_i32(self) -> int:
        return struct.unpack(">i", self.read(4))[0]

    def read_i64(self) -> int:
        return struct.unpack(">q", self.read(8))[0]

    def read_f32(self) -> float:
        return struct.unpack(">f", self.read(4))[0]

    def read_f64(self) -> float:
        return struct.unpack(">d", self.read(8))[0]

    def read_string(self) -> str:
        ln = self.read_i16()
        if ln < 0:
            raise StructgenError("negative string length in NBT")
        return self.read(ln).decode("utf-8", errors="strict")


def _read_payload(buf: _Buf, tag: int) -> Any:
    if tag == TAG_BYTE:
        return struct.unpack(">b", buf.read(1))[0]
    if tag == TAG_SHORT:
        return struct.unpack(">h", buf.read(2))[0]
    if tag == TAG_INT:
        return buf.read_i32()
    if tag == TAG_LONG:
        return buf.read_i64()
    if tag == TAG_FLOAT:
        return buf.read_f32()
    if tag == TAG_DOUBLE:
        return buf.read_f64()
    if tag == TAG_BYTE_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise StructgenError("negative byte array length")
        return buf.read(ln)
    if tag == TAG_STRING:
        return buf.read_string()
    if tag == TAG_LIST:
        inner = buf.read_u8()
        ln = buf.read_i32()
        if ln < 0:
            raise StructgenError("negative list length")
        return NbtList(inner_tag=inner, items=[_read_payload(buf, inner) for _ in range(ln)])
    if tag == TAG_COMPOUND:
        out: dict[str, Any] = {}
        while True:
            t = buf.read_u8()
            if t == TAG_END:
                return out
            name = buf.read_string()
            out[name] = _read_payload(buf, t)
    if tag == TAG_INT_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise StructgenError("negative int array length")
        return [buf.read_i32() for _ in range(ln)]
    if tag == TAG_LONG_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise StructgenError("negative long array length")
        return [buf.read_i64() for _ in range(ln)]
    raise StructgenError(f"unsupported NBT tag: {tag}")


def read_nbt(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    buf = _Buf(raw)
    root_tag = buf.read_u8()
    if root_tag != TAG_COMPOUND:
        raise StructgenError(f"{path}: root tag must be TAG_COMPOUND")
    _ = buf.read_string()
    payload = _read_payload(buf, TAG_COMPOUND)
    if not isinstance(payload, dict):
        raise StructgenError(f"{path}: malformed root payload")
    return payload


def _enc_i16(v: int) -> bytes:
    return struct.pack(">h", int(v))


def _enc_i32(v: int) -> bytes:
    return struct.pack(">i", int(v))


def _enc_i64(v: int) -> bytes:
    return struct.pack(">q", int(v))


def _enc_f32(v: float) -> bytes:
    return struct.pack(">f", float(v))


def _enc_f64(v: float) -> bytes:
    return struct.pack(">d", float(v))


def _enc_string(s: str) -> bytes:
    b = s.encode("utf-8", errors="strict")
    if len(b) > 65535:
        raise StructgenError("NBT string too long")
    return struct.pack(">H", len(b)) + b


def _tag_type(value: Any) -> int:
    if isinstance(value, bool):
        return TAG_BYTE
    if isinstance(value, int):
        return TAG_INT
    if isinstance(value, float):
        return TAG_DOUBLE
    if isinstance(value, str):
        return TAG_STRING
    if isinstance(value, bytes):
        return TAG_BYTE_ARRAY
    if isinstance(value, NbtList):
        return TAG_LIST
    if isinstance(value, dict):
        return TAG_COMPOUND
    if isinstance(value, list):
        if not value:
            return TAG_LIST
        first = value[0]
        inner = _tag_type(first)
        if any(_tag_type(v) != inner for v in value):
            raise StructgenError("NBT list values must be homogeneous")
        return TAG_LIST
    raise StructgenError(f"unsupported Python type for NBT write: {type(value)}")


def _write_payload(value: Any) -> tuple[int, bytes]:
    tag = _tag_type(value)
    if tag == TAG_BYTE:
        return TAG_BYTE, struct.pack(">b", 1 if value else 0)
    if tag == TAG_INT:
        return TAG_INT, _enc_i32(value)
    if tag == TAG_DOUBLE:
        return TAG_DOUBLE, _enc_f64(value)
    if tag == TAG_STRING:
        return TAG_STRING, _enc_string(value)
    if tag == TAG_BYTE_ARRAY:
        return TAG_BYTE_ARRAY, _enc_i32(len(value)) + value
    if tag == TAG_COMPOUND:
        pieces: list[bytes] = []
        assert isinstance(value, dict)
        for k, v in value.items():
            t, p = _write_payload(v)
            pieces.append(bytes([t]) + _enc_string(k) + p)
        pieces.append(bytes([TAG_END]))
        return TAG_COMPOUND, b"".join(pieces)
    if tag == TAG_LIST:
        if isinstance(value, NbtList):
            inner = value.inner_tag
            items = value.items
        else:
            items = value
            inner = _tag_type(items[0]) if items else TAG_END
        payloads = []
        for item in items:
            t, p = _write_payload(item)
            if t != inner:
                raise StructgenError("NBT list item type mismatch")
            payloads.append(p)
        return TAG_LIST, bytes([inner]) + _enc_i32(len(items)) + b"".join(payloads)
    raise StructgenError(f"unsupported write tag {tag}")


def write_nbt(path: Path, root: dict[str, Any]) -> None:
    tag, payload = _write_payload(root)
    if tag != TAG_COMPOUND:
        raise StructgenError("root NBT payload must be compound")
    raw = bytes([TAG_COMPOUND]) + _enc_string("") + payload
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(raw))


def parse_block_state(state: str) -> tuple[str, dict[str, str]]:
    m = STATE_RE.match(state.strip())
    if not m:
        raise StructgenError(f"invalid block state syntax: {state}")
    name = m.group("name")
    props_raw = m.group("props")
    props: dict[str, str] = {}
    if props_raw:
        for segment in props_raw.split(","):
            segment = segment.strip()
            if not segment:
                continue
            if "=" not in segment:
                raise StructgenError(f"invalid property segment '{segment}' in state '{state}'")
            k, v = segment.split("=", 1)
            key = k.strip()
            value = v.strip()
            if not key or not value:
                raise StructgenError(f"invalid property segment '{segment}' in state '{state}'")
            if key in props:
                raise StructgenError(f"duplicate property '{key}' in state '{state}'")
            props[key] = value
    return name, props


def canonical_state(name: str, props: dict[str, str]) -> str:
    if not props:
        return name
    return f"{name}[{','.join(f'{k}={props[k]}' for k in sorted(props))}]"


def load_allowlist(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "allowed_blocks" not in data or not isinstance(data["allowed_blocks"], dict):
        raise StructgenError("allowlist must contain object key 'allowed_blocks'")
    return data


def validate_state(state: str, allowlist: dict[str, Any]) -> None:
    name, props = parse_block_state(state)
    rules = allowlist["allowed_blocks"].get(name)
    if rules is None:
        raise StructgenError(f"block not allowlisted: {name}")
    allowed_props = rules.get("allowed_properties", {})
    if not isinstance(allowed_props, dict):
        raise StructgenError(f"allowlist misconfigured for block {name}")
    for prop, value in props.items():
        if prop not in allowed_props:
            raise StructgenError(f"property '{prop}' is not allowlisted for block {name}")
        values = allowed_props[prop]
        if not isinstance(values, list):
            raise StructgenError(f"allowlist misconfigured for property {name}.{prop}")
        if value not in values:
            raise StructgenError(f"value '{value}' is not allowlisted for property {name}.{prop}")


def transform_dir(dir_name: str, rot: int, mirror: str) -> str:
    d = dir_name
    if d in HORIZONTAL:
        idx = HORIZONTAL.index(d)
        d = HORIZONTAL[(idx + (rot // 90)) % 4]
    if mirror == "left_right":
        if d == "north":
            d = "south"
        elif d == "south":
            d = "north"
    elif mirror == "front_back":
        if d == "east":
            d = "west"
        elif d == "west":
            d = "east"
    return d


def transform_orientation(orientation: str, rot: int, mirror: str) -> str:
    if "_" not in orientation:
        return orientation
    a, b = orientation.split("_", 1)
    if a in HORIZONTAL:
        a = transform_dir(a, rot, mirror)
    if b in HORIZONTAL:
        b = transform_dir(b, rot, mirror)
    return f"{a}_{b}"


def transform_axis(axis: str, rot: int) -> str:
    if axis not in ("x", "y", "z"):
        return axis
    if axis == "y":
        return axis
    if rot in (90, 270):
        return "z" if axis == "x" else "x"
    return axis


def transform_state(state: str, rot: int, mirror: str) -> str:
    name, props = parse_block_state(state)
    out = dict(props)
    for k in ("facing", "horizontal_facing"):
        if k in out:
            out[k] = transform_dir(out[k], rot, mirror)
    if "orientation" in out:
        out["orientation"] = transform_orientation(out["orientation"], rot, mirror)
    if "axis" in out:
        out["axis"] = transform_axis(out["axis"], rot)
    return canonical_state(name, out)


def transform_rotation_yaw(rot_value: float, rot: int, mirror: str) -> float:
    out = float(rot_value) + float(rot)
    out = out % 360.0
    if mirror == "left_right":
        out = (180.0 - out) % 360.0
    elif mirror == "front_back":
        out = (-out) % 360.0
    return out


def rotate_size(size: tuple[int, int, int], rot: int) -> tuple[int, int, int]:
    sx, sy, sz = size
    if rot in (90, 270):
        return (sz, sy, sx)
    return (sx, sy, sz)


def rotate_pos(x: int, y: int, z: int, size: tuple[int, int, int], rot: int) -> tuple[int, int, int]:
    sx, _sy, sz = size
    if rot == 0:
        return x, y, z
    if rot == 90:
        return z, y, sx - 1 - x
    if rot == 180:
        return sx - 1 - x, y, sz - 1 - z
    if rot == 270:
        return sz - 1 - z, y, x
    raise StructgenError(f"unsupported rotation {rot}")


def mirror_pos(x: int, y: int, z: int, size: tuple[int, int, int], mirror: str) -> tuple[int, int, int]:
    sx, _sy, sz = size
    if mirror == "none":
        return x, y, z
    if mirror == "left_right":
        return x, y, sz - 1 - z
    if mirror == "front_back":
        return sx - 1 - x, y, z
    raise StructgenError(f"unsupported mirror {mirror}")


def transform_pos(pos: list[int], size: tuple[int, int, int], rot: int, mirror: str) -> tuple[int, int, int]:
    if len(pos) != 3:
        raise StructgenError(f"position must have 3 values, got: {pos}")
    x, y, z = int(pos[0]), int(pos[1]), int(pos[2])
    rx, ry, rz = rotate_pos(x, y, z, size, rot)
    s2 = rotate_size(size, rot)
    return mirror_pos(rx, ry, rz, s2, mirror)


def assert_in_bounds(pos: tuple[int, int, int], size: tuple[int, int, int], context: str) -> None:
    x, y, z = pos
    sx, sy, sz = size
    if x < 0 or y < 0 or z < 0 or x >= sx or y >= sy or z >= sz:
        raise StructgenError(f"{context}: pos={pos} out of bounds for size={size}")


def load_template_compound(path: Path) -> dict[str, Any]:
    nbt_root = read_nbt(path)
    tpl = nbt_root.get("template")
    if not isinstance(tpl, dict):
        raise StructgenError(f"{path}: root must contain compound key 'template'")
    return tpl


def apply_params(value: Any, params: dict[str, Any]) -> Any:
    if isinstance(value, str):
        for k, v in params.items():
            token = "{{" + str(k) + "}}"
            if value == token:
                return copy.deepcopy(v)
            value = value.replace(token, str(v))
        return value
    if isinstance(value, dict):
        return {k: apply_params(v, params) for k, v in value.items()}
    if isinstance(value, NbtList):
        return NbtList(value.inner_tag, [apply_params(v, params) for v in value.items])
    if isinstance(value, list):
        return [apply_params(v, params) for v in value]
    return copy.deepcopy(value)


def collect_param_tokens(value: Any) -> set[str]:
    tokens: set[str] = set()
    if isinstance(value, str):
        for match in PARAM_TOKEN_RE.finditer(value):
            tokens.add(match.group(1))
        return tokens
    if isinstance(value, dict):
        for v in value.values():
            tokens.update(collect_param_tokens(v))
        return tokens
    if isinstance(value, NbtList):
        for item in value.items:
            tokens.update(collect_param_tokens(item))
        return tokens
    if isinstance(value, list):
        for item in value:
            tokens.update(collect_param_tokens(item))
        return tokens
    return tokens


def _check_keys(context: str, obj: dict[str, Any], required: set[str], optional: set[str] | None = None) -> None:
    optional = optional or set()
    allowed = required | optional
    unknown = sorted(set(obj.keys()) - allowed)
    missing = sorted(required - set(obj.keys()))
    if missing:
        raise StructgenError(f"{context}: missing keys: {', '.join(missing)}")
    if unknown:
        raise StructgenError(f"{context}: unknown keys: {', '.join(unknown)}")


def _as_int_triplet(value: Any, context: str, *, positive: bool = False) -> tuple[int, int, int]:
    if not isinstance(value, list) or len(value) != 3:
        raise StructgenError(f"{context}: expected a 3-item list")
    out: list[int] = []
    for i, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, int):
            raise StructgenError(f"{context}[{i}]: expected integer")
        if positive and item <= 0:
            raise StructgenError(f"{context}[{i}]: expected integer > 0")
        out.append(int(item))
    return (out[0], out[1], out[2])


def _as_num_triplet(value: Any, context: str) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise StructgenError(f"{context}: expected a 3-item list")
    out: list[float] = []
    for i, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise StructgenError(f"{context}[{i}]: expected number")
        out.append(float(item))
    return (out[0], out[1], out[2])


def validate_plan_shape(plan_path: Path, plan: dict[str, Any]) -> None:
    if not isinstance(plan, dict):
        raise StructgenError(f"{plan_path}: plan root must be an object")
    _check_keys(
        str(plan_path),
        plan,
        required={
            "schema_version",
            "id",
            "type",
            "size",
            "origin",
            "blocks",
            "jigsaws",
            "block_entities",
            "entities",
            "palette_refs",
            "tags",
        },
    )

    schema_version = plan["schema_version"]
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise StructgenError(f"{plan_path}: schema_version must be integer")
    if schema_version != 1:
        raise StructgenError(f"{plan_path}: schema_version must be 1")

    plan_id = plan["id"]
    if not isinstance(plan_id, str) or not plan_id.strip():
        raise StructgenError(f"{plan_path}: id must be non-empty string")

    plan_type = plan["type"]
    if not isinstance(plan_type, str) or plan_type not in PLAN_TYPES:
        raise StructgenError(f"{plan_path}: type must be one of {sorted(PLAN_TYPES)}")

    size = _as_int_triplet(plan["size"], f"{plan_path}: size", positive=True)
    _ = _as_int_triplet(plan["origin"], f"{plan_path}: origin", positive=False)

    tags = plan["tags"]
    if not isinstance(tags, list):
        raise StructgenError(f"{plan_path}: tags must be a list")
    for i, t in enumerate(tags):
        if not isinstance(t, str):
            raise StructgenError(f"{plan_path}: tags[{i}] must be string")

    palette_refs = plan["palette_refs"]
    if not isinstance(palette_refs, dict) or not palette_refs:
        raise StructgenError(f"{plan_path}: palette_refs must be a non-empty object")
    palette_keys = set(palette_refs.keys())
    if palette_keys != BIOME_SET:
        missing = sorted(BIOME_SET - palette_keys)
        extra = sorted(palette_keys - BIOME_SET)
        parts: list[str] = []
        if missing:
            parts.append(f"missing biomes: {', '.join(missing)}")
        if extra:
            parts.append(f"unknown biomes: {', '.join(extra)}")
        raise StructgenError(f"{plan_path}: palette_refs must contain exactly {', '.join(SUPPORTED_BIOMES)} ({'; '.join(parts)})")

    for biome in SUPPORTED_BIOMES:
        palette = palette_refs[biome]
        if not isinstance(palette, dict):
            raise StructgenError(f"{plan_path}: palette_refs.{biome} must be an object")
        for mk, state in palette.items():
            if not isinstance(mk, str) or not mk:
                raise StructgenError(f"{plan_path}: palette_refs.{biome} has invalid material key")
            if not isinstance(state, str):
                raise StructgenError(f"{plan_path}: palette_refs.{biome}.{mk} must be string")
            n, p = parse_block_state(state)
            _ = canonical_state(n, p)

    blocks = plan["blocks"]
    if not isinstance(blocks, list) or not blocks:
        raise StructgenError(f"{plan_path}: blocks must be a non-empty list")
    for i, block in enumerate(blocks):
        context = f"{plan_path}: blocks[{i}]"
        if not isinstance(block, dict):
            raise StructgenError(f"{context}: block entry must be object")
        _check_keys(context, block, required={"pos", "state"}, optional={"material_key"})
        _as_int_triplet(block["pos"], f"{context}.pos", positive=False)
        if not isinstance(block["state"], str):
            raise StructgenError(f"{context}.state must be string")
        n, p = parse_block_state(block["state"])
        _ = canonical_state(n, p)
        if "material_key" in block:
            mk = block["material_key"]
            if not isinstance(mk, str) or not mk:
                raise StructgenError(f"{context}.material_key must be non-empty string")
            for biome in SUPPORTED_BIOMES:
                if mk not in palette_refs[biome]:
                    raise StructgenError(f"{context}: material_key '{mk}' missing in palette_refs.{biome}")
        # source-space bounds check
        assert_in_bounds((int(block["pos"][0]), int(block["pos"][1]), int(block["pos"][2])), size, context)

    jigsaws = plan["jigsaws"]
    if not isinstance(jigsaws, list):
        raise StructgenError(f"{plan_path}: jigsaws must be a list")
    if len(jigsaws) < 1:
        raise StructgenError(f"{plan_path}: jigsaws must contain at least one entry")
    for i, jigsaw in enumerate(jigsaws):
        context = f"{plan_path}: jigsaws[{i}]"
        if not isinstance(jigsaw, dict):
            raise StructgenError(f"{context}: jigsaw entry must be object")
        _check_keys(
            context,
            jigsaw,
            required={"pos", "name", "target", "pool", "final_state", "joint", "orientation"},
        )
        _as_int_triplet(jigsaw["pos"], f"{context}.pos", positive=False)
        assert_in_bounds((int(jigsaw["pos"][0]), int(jigsaw["pos"][1]), int(jigsaw["pos"][2])), size, context)
        for f in ("name", "target", "pool", "final_state", "joint", "orientation"):
            if not isinstance(jigsaw[f], str) or not jigsaw[f].strip():
                raise StructgenError(f"{context}.{f} must be non-empty string")
        if jigsaw["joint"] not in ("rollable", "aligned"):
            raise StructgenError(f"{context}.joint must be 'rollable' or 'aligned'")
        if jigsaw["orientation"] not in VALID_JIGSAW_ORIENTATIONS:
            raise StructgenError(f"{context}.orientation is invalid")
        n, p = parse_block_state(jigsaw["final_state"])
        _ = canonical_state(n, p)

    block_entities = plan["block_entities"]
    if not isinstance(block_entities, list):
        raise StructgenError(f"{plan_path}: block_entities must be a list")
    for i, block_entity in enumerate(block_entities):
        context = f"{plan_path}: block_entities[{i}]"
        if not isinstance(block_entity, dict):
            raise StructgenError(f"{context}: block_entity entry must be object")
        _check_keys(context, block_entity, required={"pos", "template", "params"})
        _as_int_triplet(block_entity["pos"], f"{context}.pos", positive=False)
        assert_in_bounds((int(block_entity["pos"][0]), int(block_entity["pos"][1]), int(block_entity["pos"][2])), size, context)
        template = block_entity["template"]
        if not isinstance(template, str) or not template.strip():
            raise StructgenError(f"{context}.template must be non-empty string")
        if not isinstance(block_entity["params"], dict):
            raise StructgenError(f"{context}.params must be an object")

    entities = plan["entities"]
    if not isinstance(entities, list):
        raise StructgenError(f"{plan_path}: entities must be a list")
    for i, entity in enumerate(entities):
        context = f"{plan_path}: entities[{i}]"
        if not isinstance(entity, dict):
            raise StructgenError(f"{context}: entity entry must be object")
        _check_keys(context, entity, required={"pos", "block_pos", "template", "params"})
        _as_num_triplet(entity["pos"], f"{context}.pos")
        _as_int_triplet(entity["block_pos"], f"{context}.block_pos", positive=False)
        assert_in_bounds(
            (int(entity["block_pos"][0]), int(entity["block_pos"][1]), int(entity["block_pos"][2])),
            size,
            context,
        )
        template = entity["template"]
        if not isinstance(template, str) or not template.strip():
            raise StructgenError(f"{context}.template must be non-empty string")
        if not isinstance(entity["params"], dict):
            raise StructgenError(f"{context}.params must be an object")


def _transformed_params(params: dict[str, Any], rot: int, mirror: str) -> dict[str, Any]:
    out = dict(params)
    if isinstance(out.get("facing"), str):
        out["facing"] = transform_dir(out["facing"], rot, mirror)
    if "rotation" in out and isinstance(out["rotation"], (int, float)):
        out["rotation"] = transform_rotation_yaw(float(out["rotation"]), rot, mirror)
    return out


def _build_structure(
    *,
    plan: dict[str, Any],
    biome: str,
    allowlist: dict[str, Any],
    block_tpl_dir: Path,
    entity_tpl_dir: Path,
    rot: int,
    mirror: str,
    include_entities: bool,
    warnings: list[str],
) -> tuple[tuple[int, int, int], list[tuple[int, int, int, str, dict[str, Any] | None]], list[dict[str, Any]]]:
    base_size = (int(plan["size"][0]), int(plan["size"][1]), int(plan["size"][2]))
    out_size = rotate_size(base_size, rot)
    if any(v <= 0 for v in out_size):
        raise StructgenError(f"invalid transformed size {out_size}")

    palettes = plan["palette_refs"]
    if biome not in palettes:
        raise StructgenError(f"plan '{plan['id']}' does not define palette for biome '{biome}'")
    material_map = palettes[biome]
    if not isinstance(material_map, dict):
        raise StructgenError("palette entry must be an object")

    placed: dict[tuple[int, int, int], tuple[str, dict[str, Any] | None]] = {}

    for block in plan["blocks"]:
        if not isinstance(block, dict):
            raise StructgenError("each block entry must be an object")
        src_pos = block.get("pos")
        if not isinstance(src_pos, list):
            raise StructgenError("block.pos must be list")
        pos = transform_pos(src_pos, base_size, rot, mirror)
        assert_in_bounds(pos, out_size, "block")

        raw_state = block.get("state")
        if not isinstance(raw_state, str):
            raise StructgenError("block.state must be string")
        material_key = block.get("material_key")
        if material_key is not None:
            if material_key not in material_map:
                raise StructgenError(f"missing palette mapping for material_key '{material_key}'")
            raw_state = str(material_map[material_key])
        transformed_state = transform_state(raw_state, rot, mirror)
        validate_state(transformed_state, allowlist)
        placed[pos] = (transformed_state, None)

    for j in plan["jigsaws"]:
        if not isinstance(j, dict):
            raise StructgenError("each jigsaw entry must be an object")
        pos = transform_pos(j["pos"], base_size, rot, mirror)
        assert_in_bounds(pos, out_size, "jigsaw")
        orientation = transform_orientation(str(j["orientation"]), rot, mirror)
        if orientation not in VALID_JIGSAW_ORIENTATIONS:
            raise StructgenError(f"invalid jigsaw orientation '{orientation}'")
        state = canonical_state("minecraft:jigsaw", {"orientation": orientation})
        validate_state(state, allowlist)
        final_state = transform_state(str(j["final_state"]), rot, mirror)
        validate_state(final_state, allowlist)
        jnbt = {
            "name": str(j["name"]),
            "target": str(j["target"]),
            "pool": str(j["pool"]),
            "final_state": final_state,
            "joint": str(j["joint"]),
        }
        if not jnbt["name"] or not jnbt["target"] or not jnbt["pool"]:
            raise StructgenError("jigsaw name/target/pool must be non-empty")
        placed[pos] = (state, jnbt)

    for be in plan["block_entities"]:
        if not isinstance(be, dict):
            raise StructgenError("each block_entities entry must be an object")
        pos = transform_pos(be["pos"], base_size, rot, mirror)
        assert_in_bounds(pos, out_size, "block_entity")
        if pos not in placed:
            raise StructgenError(f"block entity at {pos} has no block")
        template_path = block_tpl_dir / str(be["template"])
        if not template_path.exists():
            raise StructgenError(f"missing block entity template: {template_path}")
        params = _transformed_params(dict(be.get("params", {})), rot, mirror)
        template_compound = load_template_compound(template_path)
        supported_tokens = collect_param_tokens(template_compound)
        for key in sorted(params.keys()):
            if key not in supported_tokens:
                warnings.append(
                    f"[warn] {plan['id']} ({biome}): block entity template '{template_path.name}' does not use param '{key}'"
                )
        nbt = apply_params(template_compound, params)
        state, existing_nbt = placed[pos]
        merged = dict(existing_nbt or {})
        merged.update(nbt)
        placed[pos] = (state, merged)

    entities_out: list[dict[str, Any]] = []
    if include_entities:
        for ent in plan["entities"]:
            if not isinstance(ent, dict):
                raise StructgenError("each entities entry must be an object")
            src_pos = ent.get("pos")
            if not isinstance(src_pos, list) or len(src_pos) != 3:
                raise StructgenError("entity.pos must be a 3-value list")
            src_block = ent.get("block_pos")
            if not isinstance(src_block, list) or len(src_block) != 3:
                raise StructgenError("entity.block_pos must be a 3-value list")
            bp = transform_pos(src_block, base_size, rot, mirror)
            assert_in_bounds(bp, out_size, "entity.block_pos")

            ex = int(src_pos[0])
            ey = float(src_pos[1])
            ez = int(src_pos[2])
            ep = transform_pos([ex, int(ey), ez], base_size, rot, mirror)

            template_path = entity_tpl_dir / str(ent["template"])
            if not template_path.exists():
                raise StructgenError(f"missing entity template: {template_path}")
            params = _transformed_params(dict(ent.get("params", {})), rot, mirror)
            template_compound = load_template_compound(template_path)
            supported_tokens = collect_param_tokens(template_compound)
            for key in sorted(params.keys()):
                if key not in supported_tokens:
                    warnings.append(
                        f"[warn] {plan['id']} ({biome}): entity template '{template_path.name}' does not use param '{key}'"
                    )
            enbt = apply_params(template_compound, params)
            if not isinstance(enbt, dict):
                raise StructgenError("entity template must resolve to a compound")
            enbt["Pos"] = NbtList(TAG_DOUBLE, [float(ep[0]) + 0.5, ey, float(ep[2]) + 0.5])
            enbt["blockPos"] = NbtList(TAG_INT, [int(bp[0]), int(bp[1]), int(bp[2])])
            if "rotation" in params:
                yaw = float(params["rotation"])
                enbt["Rotation"] = NbtList(TAG_DOUBLE, [yaw, 0.0])
            entities_out.append(enbt)

    blocks_out: list[tuple[int, int, int, str, dict[str, Any] | None]] = []
    for (x, y, z), (state, nbt) in sorted(placed.items()):
        blocks_out.append((x, y, z, state, nbt))
    return out_size, blocks_out, entities_out


def _structure_root(
    *,
    size: tuple[int, int, int],
    blocks: list[tuple[int, int, int, str, dict[str, Any] | None]],
    entities: list[dict[str, Any]],
) -> dict[str, Any]:
    palette_idx: dict[str, int] = {}
    palette: list[dict[str, Any]] = []
    block_entries: list[dict[str, Any]] = []
    for x, y, z, state, nbt in blocks:
        n, p = parse_block_state(state)
        if state not in palette_idx:
            idx = len(palette)
            palette_idx[state] = idx
            entry: dict[str, Any] = {"Name": n}
            if p:
                entry["Properties"] = {k: p[k] for k in sorted(p)}
            palette.append(entry)
        be: dict[str, Any] = {
            "state": int(palette_idx[state]),
            "pos": NbtList(TAG_INT, [int(x), int(y), int(z)]),
        }
        if nbt:
            be["nbt"] = nbt
        block_entries.append(be)

    return {
        "DataVersion": DATA_VERSION_1_21_1,
        "size": NbtList(TAG_INT, [size[0], size[1], size[2]]),
        "palette": NbtList(TAG_COMPOUND, palette),
        "blocks": NbtList(TAG_COMPOUND, block_entries),
        "entities": NbtList(TAG_COMPOUND, entities),
    }


def compile_all(
    *,
    plans_root: Path,
    out_root: Path,
    allowlist_path: Path,
    templates_root: Path,
    rot: int,
    mirror: str,
    include_entities: bool,
    biomes: tuple[str, ...],
) -> int:
    allowlist = load_allowlist(allowlist_path)
    block_tpl_dir = templates_root / "block_entities"
    entity_tpl_dir = templates_root / "entities"
    plan_files = sorted(plans_root.rglob("*.json"))
    if not plan_files:
        raise StructgenError(f"no plan files found under {plans_root}")
    compiled = 0
    for plan_path in plan_files:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        validate_plan_shape(plan_path, plan)
        plan_type = str(plan["type"]).strip()
        plan_id = str(plan["id"]).strip()
        if not plan_type or not plan_id:
            raise StructgenError(f"{plan_path}: invalid type/id")
        variant = plan_id
        prefix = plan_type + "_"
        if variant.startswith(prefix):
            variant = variant[len(prefix) :]
        variant = re.sub(r"[^a-z0-9_/-]", "_", variant.lower())
        if not variant:
            raise StructgenError(f"{plan_path}: empty variant after normalization")
        warnings: list[str] = []
        for biome in biomes:
            size, blocks, entities = _build_structure(
                plan=plan,
                biome=biome,
                allowlist=allowlist,
                block_tpl_dir=block_tpl_dir,
                entity_tpl_dir=entity_tpl_dir,
                rot=rot,
                mirror=mirror,
                include_entities=include_entities,
                warnings=warnings,
            )
            out_path = out_root / "village" / f"{plan_type}_{variant}_{biome}.nbt"
            root = _structure_root(size=size, blocks=blocks, entities=entities)
            write_nbt(out_path, root)
            compiled += 1
            print(f"[ok] {plan_path.as_posix()} -> {out_path.as_posix()}")
        for warning in warnings:
            print(warning, file=sys.stderr)
    return compiled


def _parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Compile structgen plans into Minecraft structure NBT files")
    ap.add_argument(
        "--plans",
        default="tools/structgen/plans",
        help="Path to plans root (default: tools/structgen/plans)",
    )
    ap.add_argument(
        "--templates",
        default="tools/structgen/templates",
        help="Path to template root (default: tools/structgen/templates)",
    )
    ap.add_argument(
        "--allowlist",
        default="tools/structgen/allowlist_blocks.json",
        help="Path to allowlist (default: tools/structgen/allowlist_blocks.json)",
    )
    ap.add_argument(
        "--out",
        default="datapacks/acm_pokemon_worldgen/data/acm/structure",
        help="Output structures root (default: datapacks/acm_pokemon_worldgen/data/acm/structure)",
    )
    ap.add_argument("--rotate", choices=("0", "90", "180", "270"), default="0", help="Rotate plans around Y axis")
    ap.add_argument(
        "--mirror",
        choices=("none", "left_right", "front_back"),
        default="none",
        help="Mirror plans after rotation",
    )
    ap.add_argument("--include-entities", action="store_true", help="Include mobile entities in generated NBT")
    ap.add_argument(
        "--biome",
        action="append",
        choices=SUPPORTED_BIOMES,
        help="Restrict compilation to one or more biome(s). Defaults to all supported biomes.",
    )
    return ap.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    plans_root = Path(args.plans)
    templates_root = Path(args.templates)
    allowlist = Path(args.allowlist)
    out_root = Path(args.out)
    biomes = tuple(args.biome) if args.biome else SUPPORTED_BIOMES
    try:
        compiled = compile_all(
            plans_root=plans_root,
            out_root=out_root,
            allowlist_path=allowlist,
            templates_root=templates_root,
            rot=int(args.rotate),
            mirror=str(args.mirror),
            include_entities=bool(args.include_entities),
            biomes=biomes,
        )
    except StructgenError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1
    print(f"[done] compiled {compiled} structure(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
