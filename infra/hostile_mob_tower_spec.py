#!/usr/bin/env python3
"""Single-source geometry for the hostile mob tower prefab."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple


M_FOUND = "minecraft:cobblestone"
M_WALL = "minecraft:cobblestone"
M_FLOOR = "minecraft:stone_bricks"
M_CEIL = "minecraft:stone_bricks"
M_ROOF = "minecraft:deepslate_tiles"
M_GLASS = "minecraft:iron_bars"
M_CARPET = "minecraft:gray_carpet"
M_LIGHT = "minecraft:torch"
M_DOOR_LOWER = "minecraft:oak_door[facing=south,half=lower,hinge=left,open=false,powered=false]"
M_DOOR_UPPER = "minecraft:oak_door[facing=south,half=upper,hinge=left,open=false,powered=false]"
M_LADDER = "minecraft:ladder[facing=east,waterlogged=false]"
M_GATE_NS = "minecraft:oak_fence_gate[facing=north,in_wall=false,open=true,powered=false]"
M_GATE_EW = "minecraft:oak_fence_gate[facing=east,in_wall=false,open=true,powered=false]"
M_WATER = "minecraft:water"

FLOOR_SPACING = 5
FLOOR_CEILING_OFFSET = 4


@dataclass(frozen=True)
class Op:
    kind: str
    x1: int
    y1: int
    z1: int
    x2: int
    y2: int
    z2: int
    block: str
    category: str
    critical: bool = False


@dataclass(frozen=True)
class Geometry:
    origin: Tuple[int, int, int]
    floors: int
    first_floor_y: int
    top_y: int
    roof_y: int
    outer_x1: int
    outer_x2: int
    outer_z1: int
    outer_z2: int
    room_x1: int
    room_x2: int
    room_z1: int
    room_z2: int
    ladder_x: int
    ladder_z: int
    build_bbox: Tuple[int, int, int, int, int, int]
    select_bbox: Tuple[int, int, int, int]
    clear_bbox: Tuple[int, int, int, int, int, int]
    chunk_box: Tuple[int, int, int, int]


def geometry(origin: Tuple[int, int, int], floors: int) -> Geometry:
    x0, y0, z0 = origin
    first_floor_y = y0 + 22
    top_y = first_floor_y + (floors - 1) * FLOOR_SPACING + FLOOR_CEILING_OFFSET
    roof_y = top_y + 1

    outer_x1 = x0 - 8
    outer_x2 = x0 + 9
    outer_z1 = z0 - 8
    outer_z2 = z0 + 9

    room_x1 = x0 - 3
    room_x2 = x0 + 4
    room_z1 = z0 + 3
    room_z2 = z0 + 7

    ladder_x = outer_x1 - 1
    ladder_z = z0

    build_x1 = ladder_x
    build_x2 = outer_x2
    build_y1 = y0
    build_y2 = roof_y + 1
    build_z1 = outer_z1
    build_z2 = outer_z2

    clear_x1 = outer_x1 - 2
    clear_x2 = outer_x2 + 2
    clear_y1 = y0 + 1
    clear_y2 = top_y + 2
    clear_z1 = outer_z1 - 2
    clear_z2 = outer_z2 + 2

    select_x1 = build_x1 - 2
    select_x2 = build_x2 + 2
    select_z1 = build_z1 - 2
    select_z2 = build_z2 + 2

    return Geometry(
        origin=origin,
        floors=floors,
        first_floor_y=first_floor_y,
        top_y=top_y,
        roof_y=roof_y,
        outer_x1=outer_x1,
        outer_x2=outer_x2,
        outer_z1=outer_z1,
        outer_z2=outer_z2,
        room_x1=room_x1,
        room_x2=room_x2,
        room_z1=room_z1,
        room_z2=room_z2,
        ladder_x=ladder_x,
        ladder_z=ladder_z,
        build_bbox=(build_x1, build_y1, build_z1, build_x2, build_y2, build_z2),
        select_bbox=(select_x1, select_z1, select_x2, select_z2),
        clear_bbox=(clear_x1, clear_y1, clear_z1, clear_x2, clear_y2, clear_z2),
        chunk_box=(build_x1 >> 4, build_z1 >> 4, build_x2 >> 4, build_z2 >> 4),
    )


def _fill(ops: List[Op], x1: int, y1: int, z1: int, x2: int, y2: int, z2: int, block: str, category: str, critical: bool = False) -> None:
    ops.append(Op("fill", x1, y1, z1, x2, y2, z2, block, category, critical))


def _set(ops: List[Op], x: int, y: int, z: int, block: str, category: str, critical: bool = False) -> None:
    ops.append(Op("setblock", x, y, z, x, y, z, block, category, critical))


def _range(a: int, b: int) -> range:
    return range(min(a, b), max(a, b) + 1)


def _expand(op: Op) -> List[Tuple[int, int, int]]:
    pts: List[Tuple[int, int, int]] = []
    for x in _range(op.x1, op.x2):
        for y in _range(op.y1, op.y2):
            for z in _range(op.z1, op.z2):
                pts.append((x, y, z))
    return pts


def _quadrant_pad_ranges(g: Geometry, x0: int, z0: int) -> List[Tuple[int, int, int, int]]:
    return [
        (g.outer_x1 + 1, x0 - 1, g.outer_z1 + 1, z0 - 1),
        (x0 + 2, g.outer_x2 - 1, g.outer_z1 + 1, z0 - 1),
        (g.outer_x1 + 1, x0 - 1, z0 + 2, g.outer_z2 - 1),
        (x0 + 2, g.outer_x2 - 1, z0 + 2, g.outer_z2 - 1),
    ]


def stopper_blocks(origin: Tuple[int, int, int], floors: int) -> Dict[Tuple[int, int, int], str]:
    g = geometry(origin, floors)
    x0, _y0, z0 = origin
    pts: Dict[Tuple[int, int, int], str] = {}
    for floor_idx in range(floors):
        pad_y = g.first_floor_y + floor_idx * FLOOR_SPACING + 1
        for pt in (
            (x0 - 1, pad_y, z0),
            (x0 - 1, pad_y, z0 + 1),
            (x0 + 2, pad_y, z0),
            (x0 + 2, pad_y, z0 + 1),
        ):
            pts[pt] = M_GATE_NS
        for pt in (
            (x0, pad_y, z0 - 1),
            (x0 + 1, pad_y, z0 - 1),
            (x0, pad_y, z0 + 2),
            (x0 + 1, pad_y, z0 + 2),
        ):
            pts[pt] = M_GATE_EW
    return pts


def water_source_positions(origin: Tuple[int, int, int], floors: int) -> Set[Tuple[int, int, int]]:
    g = geometry(origin, floors)
    x0, _y0, z0 = origin
    pts: Set[Tuple[int, int, int]] = set()
    for floor_idx in range(floors):
        pad_y = g.first_floor_y + floor_idx * FLOOR_SPACING + 1
        for pt in (
            (x0, pad_y, z0 - 7),
            (x0 + 1, pad_y, z0 - 7),
            (x0, pad_y, z0 + 8),
            (x0 + 1, pad_y, z0 + 8),
            (x0 - 7, pad_y, z0),
            (x0 - 7, pad_y, z0 + 1),
            (x0 + 8, pad_y, z0),
            (x0 + 8, pad_y, z0 + 1),
        ):
            pts.add(pt)
    return pts


def water_channel_positions(origin: Tuple[int, int, int], floors: int) -> Set[Tuple[int, int, int]]:
    g = geometry(origin, floors)
    x0, _y0, z0 = origin
    out: Set[Tuple[int, int, int]] = set()
    for floor_idx in range(floors):
        pad_y = g.first_floor_y + floor_idx * FLOOR_SPACING + 1
        for z in _range(g.outer_z1 + 1, z0 - 2):
            out.add((x0, pad_y, z))
            out.add((x0 + 1, pad_y, z))
        for z in _range(z0 + 3, g.outer_z2 - 1):
            out.add((x0, pad_y, z))
            out.add((x0 + 1, pad_y, z))
        for x in _range(g.outer_x1 + 1, x0 - 2):
            out.add((x, pad_y, z0))
            out.add((x, pad_y, z0 + 1))
        for x in _range(x0 + 3, g.outer_x2 - 1):
            out.add((x, pad_y, z0))
            out.add((x, pad_y, z0 + 1))
    return out


def build_operations(origin: Tuple[int, int, int], floors: int, *, include_clear: bool = True) -> List[Op]:
    g = geometry(origin, floors)
    x0, y0, z0 = origin
    ops: List[Op] = []

    if include_clear:
        cx1, cy1, cz1, cx2, cy2, cz2 = g.clear_bbox
        _fill(ops, cx1, cy1, cz1, cx2, cy2, cz2, "minecraft:air", "clear")
        _fill(ops, g.room_x1 - 1, y0 + 1, g.room_z1 - 1, g.room_x2 + 1, y0 + 6, g.room_z2 + 1, "minecraft:air", "clear")

    _fill(ops, g.room_x1, y0, z0 - 1, g.room_x2, y0, g.room_z2, M_FOUND, "foundation", True)
    _fill(ops, x0 - 1, y0, z0 - 1, x0 + 2, y0, z0 + 2, M_FOUND, "foundation", True)
    _fill(ops, g.room_x1, y0 + 1, g.room_z1, g.room_x2, y0 + 3, g.room_z2, M_WALL, "kill_room", True)
    _fill(ops, g.room_x1 + 1, y0 + 1, g.room_z1, g.room_x2 - 1, y0 + 2, g.room_z2 - 1, "minecraft:air", "kill_room_air")

    _fill(ops, x0, y0 + 1, g.room_z2, x0, y0 + 2, g.room_z2, "minecraft:air", "door_air")
    _set(ops, x0, y0 + 1, g.room_z2, M_DOOR_LOWER, "door", True)
    _set(ops, x0, y0 + 2, g.room_z2, M_DOOR_UPPER, "door", True)
    _set(ops, g.room_x1 + 1, y0 + 2, g.room_z2 - 1, M_LIGHT, "lights")
    _set(ops, g.room_x2 - 1, y0 + 2, g.room_z2 - 1, M_LIGHT, "lights")

    _fill(ops, x0 - 1, y0 + 1, z0 - 1, x0 + 2, g.top_y, z0 + 2, M_WALL, "shaft_walls", True)
    _fill(ops, x0, y0 + 1, z0, x0 + 1, g.top_y, z0 + 1, "minecraft:air", "shaft_air")
    _set(ops, x0, y0 + 1, z0 + 2, M_GLASS, "kill_window")
    _set(ops, x0 + 1, y0 + 1, z0 + 2, M_GLASS, "kill_window")
    _set(ops, x0, y0 + 2, z0 + 2, M_GLASS, "kill_window")
    _set(ops, x0 + 1, y0 + 2, z0 + 2, M_GLASS, "kill_window")

    _fill(ops, g.outer_x1, y0, g.outer_z1, g.outer_x1, g.top_y, g.outer_z1, M_WALL, "support_pillars")
    _fill(ops, g.outer_x1, y0, g.outer_z2, g.outer_x1, g.top_y, g.outer_z2, M_WALL, "support_pillars")
    _fill(ops, g.outer_x2, y0, g.outer_z1, g.outer_x2, g.top_y, g.outer_z1, M_WALL, "support_pillars")
    _fill(ops, g.outer_x2, y0, g.outer_z2, g.outer_x2, g.top_y, g.outer_z2, M_WALL, "support_pillars")

    for floor_idx in range(floors):
        floor_y = g.first_floor_y + floor_idx * FLOOR_SPACING
        pad_y = floor_y + 1
        wall_top_y = pad_y + 2
        ceil_y = floor_y + FLOOR_CEILING_OFFSET

        _fill(ops, g.outer_x1, floor_y, g.outer_z1, g.outer_x2, floor_y, g.outer_z2, M_FLOOR, "floor_base", True)
        _fill(ops, x0, floor_y, z0, x0 + 1, ceil_y, z0 + 1, "minecraft:air", "shaft_air")

        _fill(ops, g.outer_x1, pad_y, g.outer_z1, g.outer_x2, wall_top_y, g.outer_z1, M_WALL, "floor_walls")
        _fill(ops, g.outer_x1, pad_y, g.outer_z2, g.outer_x2, wall_top_y, g.outer_z2, M_WALL, "floor_walls")
        _fill(ops, g.outer_x1, pad_y, g.outer_z1, g.outer_x1, wall_top_y, g.outer_z2, M_WALL, "floor_walls")
        _fill(ops, g.outer_x2, pad_y, g.outer_z1, g.outer_x2, wall_top_y, g.outer_z2, M_WALL, "floor_walls")
        _fill(ops, g.outer_x1 + 1, pad_y, g.outer_z1 + 1, g.outer_x2 - 1, wall_top_y, g.outer_z2 - 1, "minecraft:air", "floor_air")

        for x1, x2, z1, z2 in _quadrant_pad_ranges(g, x0, z0):
            _fill(ops, x1, pad_y, z1, x2, pad_y, z2, M_FLOOR, "spawn_pads", True)

        _fill(ops, g.outer_x1, ceil_y, g.outer_z1, g.outer_x2, ceil_y, g.outer_z2, M_CEIL, "floor_ceiling", True)
        _fill(ops, x0, ceil_y, z0, x0 + 1, ceil_y, z0 + 1, "minecraft:air", "shaft_air")

        for x, y, z in sorted(water_source_positions(origin, floors)):
            if y == pad_y:
                _set(ops, x, y, z, M_WATER, "water_sources", True)

        for (x, y, z), block in sorted(stopper_blocks(origin, floors).items()):
            if y == pad_y:
                _set(ops, x, y, z, block, "water_stops", True)

        carpet_y = pad_y + 1
        for x in (x0 - 6, x0 - 3, x0 + 3, x0 + 6):
            for z in (z0 - 6, z0 - 3, z0 + 3, z0 + 6):
                _set(ops, x, carpet_y, z, M_CARPET, "carpet_grid")

    _fill(ops, g.outer_x1, g.roof_y, g.outer_z1, g.outer_x2, g.roof_y, g.outer_z2, M_ROOF, "roof", True)
    _set(ops, g.outer_x1, g.roof_y + 1, g.outer_z1, M_LIGHT, "roof_lights")
    _set(ops, g.outer_x2, g.roof_y + 1, g.outer_z1, M_LIGHT, "roof_lights")
    _set(ops, g.outer_x1, g.roof_y + 1, g.outer_z2, M_LIGHT, "roof_lights")
    _set(ops, g.outer_x2, g.roof_y + 1, g.outer_z2, M_LIGHT, "roof_lights")

    _fill(ops, g.ladder_x, y0, g.ladder_z - 1, g.ladder_x, g.roof_y, g.ladder_z + 1, M_WALL, "ladder_wall")
    _fill(ops, g.ladder_x, y0 + 1, g.ladder_z, g.ladder_x, g.roof_y, g.ladder_z, "minecraft:air", "ladder_air")
    for y in _range(y0 + 1, g.roof_y):
        _set(ops, g.ladder_x, y, g.ladder_z, M_LADDER, "ladder", True)

    return ops


def expected_blocks(origin: Tuple[int, int, int], floors: int) -> Dict[Tuple[int, int, int], str]:
    blocks: Dict[Tuple[int, int, int], str] = {}
    for op in build_operations(origin, floors, include_clear=False):
        if op.block == "minecraft:air":
            for pt in _expand(op):
                blocks.pop(pt, None)
            continue
        for pt in _expand(op):
            blocks[pt] = op.block
    for pt in water_channel_positions(origin, floors):
        blocks[pt] = M_WATER
    return blocks


def cleanup_operations(origin: Tuple[int, int, int], floors: int) -> List[Op]:
    out: List[Op] = []
    for (x, y, z), block in expected_blocks(origin, floors).items():
        out.append(Op("fill", x, y, z, x, y, z, block, "cleanup"))
    return out


def critical_block_expectations(origin: Tuple[int, int, int], floors: int) -> Dict[Tuple[int, int, int], str]:
    blocks: Dict[Tuple[int, int, int], str] = {}
    for op in build_operations(origin, floors, include_clear=False):
        if not op.critical or op.block == "minecraft:air":
            continue
        for pt in _expand(op):
            blocks[pt] = op.block
    for pt in water_channel_positions(origin, floors):
        blocks[pt] = M_WATER
    return blocks


def critical_air_positions(origin: Tuple[int, int, int], floors: int) -> Set[Tuple[int, int, int]]:
    g = geometry(origin, floors)
    x0, y0, z0 = origin
    cells: Set[Tuple[int, int, int]] = set()

    for y in _range(y0 + 1, g.top_y):
        for x in (x0, x0 + 1):
            for z in (z0, z0 + 1):
                cells.add((x, y, z))

    for x in _range(g.room_x1 + 1, g.room_x2 - 1):
        for y in _range(y0 + 1, y0 + 2):
            for z in _range(g.room_z1, g.room_z2 - 1):
                cells.add((x, y, z))

    for y in _range(y0 + 1, y0 + 2):
        cells.add((x0, y, g.room_z2))

    for y in _range(y0 + 1, g.roof_y):
        cells.add((g.ladder_x, y, g.ladder_z))

    return cells


def planned_spawn_positions(origin: Tuple[int, int, int], floors: int) -> Set[Tuple[int, int, int]]:
    g = geometry(origin, floors)
    blocks = expected_blocks(origin, floors)
    out: Set[Tuple[int, int, int]] = set()
    for floor_idx in range(floors):
        floor_y = g.first_floor_y + floor_idx * FLOOR_SPACING
        pad_y = floor_y + 1
        for x1, x2, z1, z2 in _quadrant_pad_ranges(g, origin[0], origin[2]):
            for x in _range(x1, x2):
                for z in _range(z1, z2):
                    if blocks.get((x, pad_y, z)) != M_FLOOR:
                        continue
                    if blocks.get((x, pad_y + 1, z), "minecraft:air") != "minecraft:air":
                        continue
                    if blocks.get((x, pad_y + 2, z), "minecraft:air") != "minecraft:air":
                        continue
                    out.add((x, pad_y + 1, z))
    return out
