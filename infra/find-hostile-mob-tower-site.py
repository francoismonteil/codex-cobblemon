#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from hostile_mob_tower_spec import geometry
from world_tools import WorldReader, is_air, is_liquid, read_world_spawn


def candidate_origins(
    spawn_x: int,
    spawn_z: int,
    *,
    min_distance: int,
    max_distance: int,
    step: int,
    preferred_radius: Optional[int] = None,
) -> List[Tuple[int, int]]:
    if preferred_radius is None:
        preferred_radius = (min_distance + max_distance) // 2

    x_start = (spawn_x - max_distance) // step * step
    x_end = (spawn_x + max_distance) // step * step
    z_start = (spawn_z - max_distance) // step * step
    z_end = (spawn_z + max_distance) // step * step

    pts: List[Tuple[int, int, int, int]] = []
    for x in range(x_start, x_end + 1, step):
        for z in range(z_start, z_end + 1, step):
            dist = int(round(math.hypot(x - spawn_x, z - spawn_z)))
            if dist < min_distance or dist > max_distance:
                continue
            pts.append((abs(dist - preferred_radius), dist, x, z))
    pts.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
    return [(x, z) for _pref_delta, _dist, x, z in pts]


def _obstruction_weight(name: str) -> float:
    if is_air(name):
        return 0.0
    if any(tok in name for tok in ("leaves", "vine", "grass", "fern", "flower", "snow")):
        return 0.25
    return 1.0


def evaluate_site(
    world,
    origin_x: int,
    origin_z: int,
    *,
    floors: int,
    min_surface_y: int = 62,
    max_surface_y: int = 90,
) -> Optional[Dict[str, object]]:
    g0 = geometry((origin_x, 0, origin_z), floors)
    x1, z1, x2, z2 = g0.select_bbox
    region_exists = getattr(world, "region_exists_for_chunk", None)
    if callable(region_exists):
        for cx in range(x1 >> 4, (x2 >> 4) + 1):
            for cz in range(z1 >> 4, (z2 >> 4) + 1):
                if not region_exists(cx, cz):
                    return None
    heights: List[int] = []
    surface_blocks: Dict[Tuple[int, int], str] = {}

    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            try:
                y = world.height_at(x, z)
            except Exception:
                return None
            heights.append(y)
            surface_blocks[(x, z)] = world.block_name(x, y, z)

    if not heights:
        return None

    surface_mode = Counter(heights).most_common(1)[0][0]
    if max(heights) - min(heights) > 1:
        return None
    if surface_mode < min_surface_y or surface_mode > max_surface_y:
        return None
    if any(is_liquid(name) for name in surface_blocks.values()):
        return None

    g = geometry((origin_x, surface_mode, origin_z), floors)
    bx1, by1, bz1, bx2, by2, bz2 = g.clear_bbox
    obstruction = 0.0
    for x in range(bx1, bx2 + 1):
        for z in range(bz1, bz2 + 1):
            for y in range(by1, by2 + 1):
                obstruction += _obstruction_weight(world.block_name(x, y, z))
                if obstruction > 96:
                    return None

    return {
        "origin": {"x": origin_x, "y": surface_mode, "z": origin_z},
        "bbox": {"x1": g.build_bbox[0], "y1": g.build_bbox[1], "z1": g.build_bbox[2], "x2": g.build_bbox[3], "y2": g.build_bbox[4], "z2": g.build_bbox[5]},
        "chunk_box": {"x1": g.chunk_box[0], "z1": g.chunk_box[1], "x2": g.chunk_box[2], "z2": g.chunk_box[3]},
        "metrics": {
            "surface_min_y": min(heights),
            "surface_max_y": max(heights),
            "surface_avg_y": round(sum(heights) / len(heights), 2),
            "surface_mode_y": surface_mode,
            "obstruction_weight": round(obstruction, 2),
        },
    }


def select_site(
    world,
    spawn: Tuple[int, int, int],
    *,
    min_distance: int,
    max_distance: int,
    step: int,
    floors: int,
    preferred_radius: Optional[int] = None,
) -> Dict[str, object]:
    spawn_x, _spawn_y, spawn_z = spawn
    attempts = 0
    for x, z in candidate_origins(
        spawn_x,
        spawn_z,
        min_distance=min_distance,
        max_distance=max_distance,
        step=step,
        preferred_radius=preferred_radius,
    ):
        attempts += 1
        site = evaluate_site(world, x, z, floors=floors)
        if site is not None:
            return {"spawn": {"x": spawn[0], "y": spawn[1], "z": spawn[2]}, "site": site, "attempts": attempts}
    raise RuntimeError("no valid hostile mob tower site found")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Find a deterministic build site for the hostile mob tower.")
    ap.add_argument("--world", default="./data/world")
    ap.add_argument("--min-distance", type=int, default=768)
    ap.add_argument("--max-distance", type=int, default=2048)
    ap.add_argument("--step", type=int, default=32)
    ap.add_argument("--preferred-radius", type=int, default=None)
    ap.add_argument("--floors", type=int, default=3)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args(argv)

    world_dir = Path(args.world)
    spawn = read_world_spawn(world_dir)
    world = WorldReader(world_dir)
    result = select_site(
        world,
        spawn,
        min_distance=args.min_distance,
        max_distance=args.max_distance,
        step=args.step,
        floors=args.floors,
        preferred_radius=args.preferred_radius,
    )
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
