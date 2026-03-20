#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from world_tools import WorldReader


Coord = Tuple[int, int, int]


def scan_spawners(
    world_dir: Path,
    *,
    dimension: str,
    center: Coord,
    radius_xz: int,
    radius_y_down: int,
    radius_y_up: int,
) -> List[Coord]:
    wx, wy, wz = center
    world = WorldReader(world_dir, dimension=dimension)
    coords: List[Coord] = []
    for x in range(wx - radius_xz, wx + radius_xz + 1):
        for y in range(max(-64, wy - radius_y_down), min(319, wy + radius_y_up) + 1):
            for z in range(wz - radius_xz, wz + radius_xz + 1):
                if world.block_name(x, y, z) == "minecraft:spawner":
                    coords.append((x, y, z))
    return coords


def build_filter_condition(coord: Coord, entity_id: str | None) -> str:
    if not entity_id:
        return ""
    x, y, z = coord
    return f'execute if data block {x} {y} {z} {{SpawnData:{{entity:{{id:\\"{entity_id}\\"}}}}}} run '


def build_data_merge_command(coord: Coord, fields: Sequence[str], *, match_entity: str | None) -> str:
    x, y, z = coord
    condition = build_filter_condition(coord, match_entity)
    payload = ",".join(fields)
    return f"{condition}data merge block {x} {y} {z} {{{payload}}}"


def build_clear_command(coord: Coord, *, match_entity: str | None) -> str:
    x, y, z = coord
    condition = build_filter_condition(coord, match_entity)
    return f"{condition}setblock {x} {y} {z} minecraft:air replace"


def run_mc_commands(commands: Iterable[str], *, repo_root: Path, delay_sec: float) -> int:
    mc_path = repo_root / "infra" / "mc.sh"
    applied = 0
    for command in commands:
        subprocess.run([str(mc_path), command], check=True, stdout=subprocess.DEVNULL)
        applied += 1
        if delay_sec > 0:
            time.sleep(delay_sec)
    return applied


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Scan and tune a spawner cluster around a point in the world.")
    ap.add_argument("--world", default="./data/world")
    ap.add_argument("--dimension", choices=["overworld", "nether", "end"], default="overworld")
    ap.add_argument("--center", nargs=3, type=int, metavar=("X", "Y", "Z"), required=True)
    ap.add_argument("--radius-xz", type=int, default=96)
    ap.add_argument("--radius-y-down", type=int, default=96)
    ap.add_argument("--radius-y-up", type=int, default=32)
    ap.add_argument("--match-entity", default=None, help="Only affect spawners whose SpawnData.entity.id matches this value.")
    ap.add_argument("--clear", action="store_true", help="Replace matching spawners with air.")
    ap.add_argument("--required-player-range", type=int, default=None)
    ap.add_argument("--max-nearby-entities", type=int, default=None)
    ap.add_argument("--spawn-count", type=int, default=None)
    ap.add_argument("--min-spawn-delay", type=int, default=None)
    ap.add_argument("--max-spawn-delay", type=int, default=None)
    ap.add_argument("--spawn-range", type=int, default=None)
    ap.add_argument("--apply", action="store_true", help="Send commands via infra/mc.sh. Without this flag, print commands only.")
    ap.add_argument("--save", action="store_true", help="Run 'save-all flush' after applying changes.")
    ap.add_argument("--delay-ms", type=int, default=0, help="Optional delay between console commands.")
    return ap.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    center = tuple(args.center)
    coords = scan_spawners(
        Path(args.world),
        dimension=args.dimension,
        center=center,  # type: ignore[arg-type]
        radius_xz=args.radius_xz,
        radius_y_down=args.radius_y_down,
        radius_y_up=args.radius_y_up,
    )

    fields: List[str] = []
    if args.required_player_range is not None:
        fields.append(f"RequiredPlayerRange:{args.required_player_range}s")
    if args.max_nearby_entities is not None:
        fields.append(f"MaxNearbyEntities:{args.max_nearby_entities}s")
    if args.spawn_count is not None:
        fields.append(f"SpawnCount:{args.spawn_count}s")
    if args.min_spawn_delay is not None:
        fields.append(f"MinSpawnDelay:{args.min_spawn_delay}s")
    if args.max_spawn_delay is not None:
        fields.append(f"MaxSpawnDelay:{args.max_spawn_delay}s")
    if args.spawn_range is not None:
        fields.append(f"SpawnRange:{args.spawn_range}s")

    commands: List[str] = []
    if args.clear:
        commands = [build_clear_command(coord, match_entity=args.match_entity) for coord in coords]
    elif fields:
        commands = [build_data_merge_command(coord, fields, match_entity=args.match_entity) for coord in coords]

    print(f"scanned={len(coords)}")
    for x, y, z in coords:
        print(f"{x} {y} {z}")

    if not commands:
        return 0

    if not args.apply:
        print("commands:")
        for command in commands:
            print(command)
        return 0

    applied = run_mc_commands(commands, repo_root=repo_root, delay_sec=args.delay_ms / 1000.0)
    print(f"applied={applied}")
    if args.save:
        subprocess.run([str(repo_root / "infra" / "mc.sh"), "save-all flush"], check=True, stdout=subprocess.DEVNULL)
        print("saved=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
