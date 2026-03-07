#!/usr/bin/env python3
"""Plan and place a global in-game map wall from existing vanilla map_*.dat files.

This script does not generate new maps; it reuses already created filled maps from
the active world and places them in a wall of item frames.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from world_tools import _load_nbt_bytes, read_world_spawn


MAP_FILE_RE = re.compile(r"^map_(\d+)\.dat$")
DIMENSION_LEGACY_MAP = {
    0: "minecraft:overworld",
    -1: "minecraft:the_nether",
    1: "minecraft:the_end",
}
FACING_BYTE = {"north": 2, "south": 3, "west": 4, "east": 5}
FACING_VEC = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}


@dataclass(frozen=True)
class MapMeta:
    map_id: int
    scale: int
    x_center: int
    z_center: int
    dimension: str


@dataclass(frozen=True)
class ExpectedTile:
    row: int
    col: int
    expected_x_center: int
    expected_z_center: int


@dataclass(frozen=True)
class PlannedTile:
    tile: ExpectedTile
    matched_map: Optional[MapMeta]
    match_kind: str  # exact|nearest|missing
    distance: Optional[int]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Plan/place a wall of global filled maps from world/data/map_*.dat."
    )
    ap.add_argument("--world", default="./data/world", help="World directory path")
    ap.add_argument("--scale", type=int, default=4, help="Map scale level (default: 4)")
    ap.add_argument(
        "--dimension",
        default="minecraft:overworld",
        help="Dimension id in map data (default: minecraft:overworld)",
    )
    ap.add_argument("--diameter", type=int, default=4000, help="Target square size in blocks")
    ap.add_argument("--center-x", type=int, help="Center X for target square (default: world spawn X)")
    ap.add_argument("--center-z", type=int, help="Center Z for target square (default: world spawn Z)")
    ap.add_argument("--x-min", type=int, help="Explicit min X (overrides center/diameter)")
    ap.add_argument("--x-max", type=int, help="Explicit max X (overrides center/diameter)")
    ap.add_argument("--z-min", type=int, help="Explicit min Z (overrides center/diameter)")
    ap.add_argument("--z-max", type=int, help="Explicit max Z (overrides center/diameter)")
    ap.add_argument("--wall-x", type=int, help="Wall anchor X (top-left tile)")
    ap.add_argument("--wall-y", type=int, help="Wall anchor Y (top-left tile)")
    ap.add_argument("--wall-z", type=int, help="Wall anchor Z (top-left tile)")
    ap.add_argument(
        "--facing",
        choices=("north", "south", "east", "west"),
        default="south",
        help="Item frame facing direction (default: south)",
    )
    ap.add_argument(
        "--frame-type",
        choices=("item_frame", "glow_item_frame"),
        default="glow_item_frame",
        help="Frame entity type (default: glow_item_frame)",
    )
    ap.add_argument(
        "--wall-block",
        default="minecraft:polished_andesite",
        help="Backing block behind frames (default: minecraft:polished_andesite)",
    )
    ap.add_argument(
        "--allow-missing",
        action="store_true",
        help="Allow apply even if some expected tiles are missing",
    )
    ap.add_argument(
        "--interactive-frames",
        action="store_true",
        help="Use interactive frames (Fixed/Invulnerable disabled) to allow manual edits in-game",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Apply build/place commands via ./infra/mc.sh",
    )
    ap.add_argument(
        "--json-out",
        help="Write computed plan as JSON",
    )
    return ap.parse_args()


def _normalize_dimension(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return DIMENSION_LEGACY_MAP.get(value, str(value))
    return str(value)


def _load_map_meta(path: Path) -> Optional[MapMeta]:
    m = MAP_FILE_RE.match(path.name)
    if not m:
        return None
    map_id = int(m.group(1))
    raw = path.read_bytes()
    root = _load_nbt_bytes(raw)
    data = root.get("data")
    if not isinstance(data, dict):
        data = root.get("Data")
    if not isinstance(data, dict):
        return None
    scale = data.get("scale")
    x_center = data.get("xCenter")
    z_center = data.get("zCenter")
    dim = data.get("dimension")
    if not isinstance(scale, int) or not isinstance(x_center, int) or not isinstance(z_center, int):
        return None
    return MapMeta(
        map_id=map_id,
        scale=int(scale),
        x_center=int(x_center),
        z_center=int(z_center),
        dimension=_normalize_dimension(dim),
    )


def load_maps(world_dir: Path, *, scale: int, dimension: str) -> List[MapMeta]:
    data_dir = world_dir / "data"
    if not data_dir.is_dir():
        raise FileNotFoundError(f"missing data dir: {data_dir}")
    out: List[MapMeta] = []
    for p in sorted(data_dir.glob("map_*.dat")):
        meta = _load_map_meta(p)
        if meta is None:
            continue
        if meta.scale != scale:
            continue
        if meta.dimension != dimension:
            continue
        out.append(meta)
    out.sort(key=lambda x: x.map_id)
    return out


def compute_extent(args: argparse.Namespace, world_dir: Path) -> Tuple[int, int, int, int]:
    explicit = [args.x_min, args.x_max, args.z_min, args.z_max]
    if any(v is not None for v in explicit):
        if not all(v is not None for v in explicit):
            raise ValueError("when using explicit bounds, provide all --x-min --x-max --z-min --z-max")
        x_min = int(args.x_min)
        x_max = int(args.x_max)
        z_min = int(args.z_min)
        z_max = int(args.z_max)
        if x_min > x_max or z_min > z_max:
            raise ValueError("invalid explicit bounds")
        return x_min, x_max, z_min, z_max

    if args.diameter <= 0:
        raise ValueError("--diameter must be > 0")
    center_x = args.center_x
    center_z = args.center_z
    if center_x is None or center_z is None:
        sx, _sy, sz = read_world_spawn(world_dir)
        if center_x is None:
            center_x = sx
        if center_z is None:
            center_z = sz
    half = args.diameter // 2
    x_min = int(center_x) - half
    z_min = int(center_z) - half
    x_max = x_min + int(args.diameter) - 1
    z_max = z_min + int(args.diameter) - 1
    return x_min, x_max, z_min, z_max


def expected_tiles(
    *,
    x_min: int,
    x_max: int,
    z_min: int,
    z_max: int,
    scale: int,
) -> Tuple[int, int, int, List[ExpectedTile]]:
    tile_span = 128 * (1 << scale)
    half = tile_span // 2
    # Vanilla map center formula:
    # center = floor((coord + 64) / tile_span) * tile_span + (tile_span / 2 - 64)
    center_offset = half - 64

    def _first_center_covering(min_coord: int) -> int:
        return math.floor((min_coord + 64) / tile_span) * tile_span + center_offset

    centers_x: List[int] = []
    cx = _first_center_covering(x_min)
    while cx - half <= x_max:
        if cx + half - 1 >= x_min:
            centers_x.append(cx)
        cx += tile_span

    centers_z: List[int] = []
    cz = _first_center_covering(z_min)
    while cz - half <= z_max:
        if cz + half - 1 >= z_min:
            centers_z.append(cz)
        cz += tile_span

    cols = len(centers_x)
    rows = len(centers_z)
    tiles: List[ExpectedTile] = []
    for row, zc in enumerate(centers_z):
        for col, xc in enumerate(centers_x):
            tiles.append(
                ExpectedTile(
                    row=row,
                    col=col,
                    expected_x_center=xc,
                    expected_z_center=zc,
                )
            )
    return tile_span, rows, cols, tiles


def plan_tiles(
    expected: Sequence[ExpectedTile],
    available_maps: Sequence[MapMeta],
    *,
    tile_span: int,
) -> List[PlannedTile]:
    by_center: Dict[Tuple[int, int], List[MapMeta]] = {}
    for m in available_maps:
        by_center.setdefault((m.x_center, m.z_center), []).append(m)
    for v in by_center.values():
        v.sort(key=lambda mm: mm.map_id, reverse=True)

    used: set[int] = set()
    out: List[PlannedTile] = []

    # Exact center match first.
    for t in expected:
        key = (t.expected_x_center, t.expected_z_center)
        matched: Optional[MapMeta] = None
        for cand in by_center.get(key, []):
            if cand.map_id in used:
                continue
            matched = cand
            break
        if matched is not None:
            used.add(matched.map_id)
            out.append(
                PlannedTile(tile=t, matched_map=matched, match_kind="exact", distance=0)
            )
        else:
            out.append(PlannedTile(tile=t, matched_map=None, match_kind="missing", distance=None))

    # Nearest fallback for missing entries.
    fallback_radius = tile_span // 2
    remaining = [m for m in available_maps if m.map_id not in used]
    for i, p in enumerate(out):
        if p.matched_map is not None:
            continue
        best: Optional[Tuple[int, MapMeta]] = None
        for cand in remaining:
            dx = abs(cand.x_center - p.tile.expected_x_center)
            dz = abs(cand.z_center - p.tile.expected_z_center)
            if dx > fallback_radius or dz > fallback_radius:
                continue
            dist = dx + dz
            if best is None or dist < best[0] or (dist == best[0] and cand.map_id > best[1].map_id):
                best = (dist, cand)
        if best is None:
            continue
        dist, matched = best
        used.add(matched.map_id)
        remaining = [m for m in remaining if m.map_id != matched.map_id]
        out[i] = PlannedTile(tile=p.tile, matched_map=matched, match_kind="nearest", distance=dist)

    return out


def _slot_position(anchor_x: int, anchor_y: int, anchor_z: int, facing: str, row: int, col: int) -> Tuple[int, int, int]:
    if facing in ("north", "south"):
        return anchor_x + col, anchor_y - row, anchor_z
    return anchor_x, anchor_y - row, anchor_z + col


def _mc(minecraft_command: str) -> None:
    proc = subprocess.run(
        ["bash", "./infra/mc.sh", minecraft_command],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        raise RuntimeError(f"mc command failed: {minecraft_command}\n{err}")


def apply_plan(
    *,
    plan: Sequence[PlannedTile],
    rows: int,
    cols: int,
    anchor_x: int,
    anchor_y: int,
    anchor_z: int,
    facing: str,
    frame_type: str,
    wall_block: str,
    allow_missing: bool,
    interactive_frames: bool,
) -> None:
    missing = [p for p in plan if p.matched_map is None]
    if missing and not allow_missing:
        raise RuntimeError(
            f"refusing apply: {len(missing)} tile(s) missing. Use --allow-missing to place partial wall."
        )

    fx0, fy0, fz0 = _slot_position(anchor_x, anchor_y, anchor_z, facing, 0, 0)
    fx1, fy1, fz1 = _slot_position(anchor_x, anchor_y, anchor_z, facing, rows - 1, cols - 1)
    min_x, max_x = sorted((fx0, fx1))
    min_y, max_y = sorted((fy0, fy1))
    min_z, max_z = sorted((fz0, fz1))

    dx = max_x - min_x + 1
    dy = max_y - min_y + 1
    dz = max_z - min_z + 1

    # Clean old frames in target volume.
    _mc(f"kill @e[type=minecraft:item_frame,x={min_x},y={min_y},z={min_z},dx={dx},dy={dy},dz={dz}]")
    _mc(f"kill @e[type=minecraft:glow_item_frame,x={min_x},y={min_y},z={min_z},dx={dx},dy={dy},dz={dz}]")

    face_dx, face_dz = FACING_VEC[facing]
    facing_byte = FACING_BYTE[facing]

    # Build backing wall and place frames/maps.
    for p in plan:
        fx, fy, fz = _slot_position(anchor_x, anchor_y, anchor_z, facing, p.tile.row, p.tile.col)
        bx = fx - face_dx
        bz = fz - face_dz
        _mc(f"setblock {bx} {fy} {bz} {wall_block} replace")

        # Summon a frame in the target slot.
        sx = fx + 0.5
        sy = fy + 0.5
        sz = fz + 0.5
        inv = "0b" if interactive_frames else "1b"
        fixed = "0b" if interactive_frames else "1b"
        _mc(
            f"summon minecraft:{frame_type} {sx} {sy} {sz} "
            f"{{Facing:{facing_byte}b,Invisible:0b,Invulnerable:{inv},Fixed:{fixed}}}"
        )

        if p.matched_map is not None:
            selector = (
                f"@e[type=minecraft:{frame_type},x={fx},y={fy},z={fz},dx=1,dy=1,dz=1,limit=1,sort=nearest]"
            )
            _mc(
                "item replace entity "
                f"{selector} container.0 with minecraft:filled_map[minecraft:map_id={p.matched_map.map_id}] 1"
            )


def load_default_player(repo_root: Path) -> Optional[str]:
    env_path = repo_root / ".env"
    if not env_path.is_file():
        return None
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "DEFAULT_PLAYER_NAME":
            v = value.strip()
            return v if v else None
    return None


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    args = parse_args()
    world_dir = Path(args.world).resolve()
    if not world_dir.is_dir():
        raise FileNotFoundError(f"missing world dir: {world_dir}")

    x_min, x_max, z_min, z_max = compute_extent(args, world_dir)
    tile_span, rows, cols, expected = expected_tiles(
        x_min=x_min,
        x_max=x_max,
        z_min=z_min,
        z_max=z_max,
        scale=args.scale,
    )
    maps = load_maps(world_dir, scale=args.scale, dimension=args.dimension)
    plan = plan_tiles(expected, maps, tile_span=tile_span)

    matched = [p for p in plan if p.matched_map is not None]
    missing = [p for p in plan if p.matched_map is None]
    nearest = [p for p in plan if p.match_kind == "nearest"]
    exact = [p for p in plan if p.match_kind == "exact"]

    print("== Map Wall Plan ==")
    print(f"world: {world_dir}")
    print(f"dimension: {args.dimension}")
    print(f"scale: {args.scale} (tile_span={tile_span})")
    print(f"extent: x=[{x_min}..{x_max}] z=[{z_min}..{z_max}]")
    print(f"grid: {cols} cols x {rows} rows ({len(plan)} tiles)")
    print(f"available matching maps: {len(maps)}")
    print(f"matched: {len(matched)} (exact={len(exact)} nearest={len(nearest)})")
    print(f"missing: {len(missing)}")

    if missing:
        print("\nMissing tile centers (create maps for these centers):")
        for p in missing:
            print(
                f"- row={p.tile.row} col={p.tile.col} "
                f"center=({p.tile.expected_x_center},{p.tile.expected_z_center})"
            )
        player = load_default_player(repo_root)
        if player:
            print("\nSuggested teleport commands:")
            for p in missing:
                print(
                    f'./infra/mc.sh "tp {player} {p.tile.expected_x_center} 120 {p.tile.expected_z_center}"'
                )

    if nearest:
        print("\nNearest matches used (not exact centers):")
        for p in nearest:
            mm = p.matched_map
            assert mm is not None
            print(
                f"- row={p.tile.row} col={p.tile.col} expected=({p.tile.expected_x_center},{p.tile.expected_z_center}) "
                f"map_id={mm.map_id} actual=({mm.x_center},{mm.z_center}) dist={p.distance}"
            )

    plan_payload = {
        "world": str(world_dir),
        "dimension": args.dimension,
        "scale": args.scale,
        "tile_span": tile_span,
        "extent": {
            "x_min": x_min,
            "x_max": x_max,
            "z_min": z_min,
            "z_max": z_max,
        },
        "grid": {"rows": rows, "cols": cols},
        "summary": {
            "total": len(plan),
            "available_maps": len(maps),
            "matched": len(matched),
            "exact": len(exact),
            "nearest": len(nearest),
            "missing": len(missing),
        },
        "tiles": [
            {
                "row": p.tile.row,
                "col": p.tile.col,
                "expected_x_center": p.tile.expected_x_center,
                "expected_z_center": p.tile.expected_z_center,
                "match_kind": p.match_kind,
                "distance": p.distance,
                "map_id": None if p.matched_map is None else p.matched_map.map_id,
                "actual_x_center": None if p.matched_map is None else p.matched_map.x_center,
                "actual_z_center": None if p.matched_map is None else p.matched_map.z_center,
            }
            for p in plan
        ],
    }

    if args.json_out:
        out_path = Path(args.json_out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(plan_payload, indent=2), encoding="utf-8")
        print(f"\nWrote JSON plan: {out_path}")

    if args.apply:
        for k, v in (("wall-x", args.wall_x), ("wall-y", args.wall_y), ("wall-z", args.wall_z)):
            if v is None:
                raise ValueError(f"--{k} is required with --apply")
        apply_plan(
            plan=plan,
            rows=rows,
            cols=cols,
            anchor_x=int(args.wall_x),
            anchor_y=int(args.wall_y),
            anchor_z=int(args.wall_z),
            facing=args.facing,
            frame_type=args.frame_type,
            wall_block=args.wall_block,
            allow_missing=bool(args.allow_missing),
            interactive_frames=bool(args.interactive_frames),
        )
        print(
            "\nApplied map wall: "
            f"anchor=({args.wall_x},{args.wall_y},{args.wall_z}) facing={args.facing} frame_type={args.frame_type}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
