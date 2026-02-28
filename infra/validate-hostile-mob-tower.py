#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from hostile_mob_tower_spec import critical_air_positions, critical_block_expectations, expected_blocks, geometry, planned_spawn_positions, water_channel_positions
from world_tools import WorldReader, is_air


def _base_block(name: str) -> str:
    return name.split("[", 1)[0]


def _passable(name: str) -> bool:
    base = _base_block(name)
    if is_air(name):
        return True
    if base.endswith("_door") or base.endswith("_trapdoor") or base.endswith(":ladder") or base.endswith("_ladder"):
        return True
    if base.endswith("_fence_gate"):
        return True
    if base.endswith("_carpet"):
        return True
    if base.endswith("_sign"):
        return True
    if base.endswith(":torch") or base.endswith("_torch"):
        return True
    return False


def validate_world(world, origin: Tuple[int, int, int], *, floors: int, mode: str = "built") -> Dict[str, object]:
    g = geometry(origin, floors)
    checks: Dict[str, object] = {}
    findings: List[str] = []
    status = "pass"

    exp = expected_blocks(origin, floors)
    critical_blocks = critical_block_expectations(origin, floors)
    critical_air = critical_air_positions(origin, floors)

    matched = 0
    missing = 0
    wrong_type = 0
    missing_critical = 0
    wrong_critical = 0

    for pos, block in exp.items():
        actual = world.block_name(*pos)
        expected_base = _base_block(block)
        actual_base = _base_block(actual)
        if actual_base == expected_base:
            matched += 1
        elif actual == "minecraft:air":
            missing += 1
        else:
            wrong_type += 1
        if pos in critical_blocks:
            if actual == "minecraft:air":
                missing_critical += 1
            elif actual_base != expected_base:
                wrong_critical += 1

    match_ratio = (matched / len(exp)) if exp else 1.0
    checks["integrity"] = {
        "expected_blocks": len(exp),
        "matched_blocks": matched,
        "missing_blocks": missing,
        "wrong_type_blocks": wrong_type,
        "match_ratio": round(match_ratio, 6),
        "critical_expected": len(critical_blocks),
        "critical_missing": missing_critical,
        "critical_wrong_type": wrong_critical,
    }

    if mode == "cleared":
        remaining_critical = sum(1 for pos, block in critical_blocks.items() if _base_block(world.block_name(*pos)) == _base_block(block))
        checks["cleanup"] = {"remaining_critical_blocks": remaining_critical}
        if remaining_critical > 0:
            status = "fail"
            findings.append(f"cleanup: {remaining_critical} bloc(s) critiques encore presents.")
        return {"status": status, "checks": checks, "findings": findings, "origin": {"x": origin[0], "y": origin[1], "z": origin[2]}, "floors": floors}

    if match_ratio < 0.99:
        status = "fail"
        findings.append(f"integrity: match_ratio={match_ratio:.3f} (< 0.99).")
    if missing_critical > 0 or wrong_critical > 0:
        status = "fail"
        findings.append("integrity: blocs critiques manquants ou incorrects.")

    blocked_air = sum(1 for pos in critical_air if not _passable(world.block_name(*pos)))
    checks["air_volumes"] = {"critical_air_positions": len(critical_air), "blocked_positions": blocked_air}
    if blocked_air > 0:
        status = "fail"
        findings.append(f"air: {blocked_air} position(s) critiques bloquees.")

    x0, _y0, z0 = origin
    shaft_water = 0
    for y in range(origin[1] + 1, g.top_y + 1):
        for x in (x0, x0 + 1):
            for z in (z0, z0 + 1):
                if "water" in world.block_name(x, y, z):
                    shaft_water += 1
    checks["shaft"] = {"water_inside": shaft_water}
    if shaft_water > 0:
        status = "fail"
        findings.append("shaft: eau detectee dans le puits.")

    water_sources_ok = sum(1 for pos, block in exp.items() if block == "minecraft:water" and world.block_name(*pos) == "minecraft:water")
    water_allowed = water_channel_positions(origin, floors)
    water_outside_channels = 0
    bx1, by1, bz1, bx2, by2, bz2 = g.build_bbox
    for x in range(bx1, bx2 + 1):
        for y in range(by1, by2 + 1):
            for z in range(bz1, bz2 + 1):
                name = world.block_name(x, y, z)
                if _base_block(name) == "minecraft:water" and (x, y, z) not in water_allowed:
                    water_outside_channels += 1
    checks["water"] = {
        "expected_sources": sum(1 for block in exp.values() if block == "minecraft:water"),
        "sources_present": water_sources_ok,
        "water_outside_channels": water_outside_channels,
    }
    if water_sources_ok != checks["water"]["expected_sources"]:
        status = "fail"
        findings.append("water: source(s) manquante(s).")
    if water_outside_channels > 0:
        status = "fail"
        findings.append(f"water: {water_outside_channels} bloc(s) d'eau hors canaux.")

    spawn_positions = planned_spawn_positions(origin, floors)
    unreliable = 0
    lit = 0
    for x, y, z in sorted(spawn_positions):
        light, ok = world.light_info(x, y, z)
        if not ok or light is None:
            unreliable += 1
            continue
        if light > 0:
            lit += 1
    checks["spawn_surfaces"] = {"positions": len(spawn_positions), "unreliable_light_positions": unreliable, "lit_positions": lit}
    if unreliable > 0:
        status = "fail"
        findings.append(f"spawn: lumiere non fiable sur {unreliable} position(s).")
    if lit > 0:
        status = "fail"
        findings.append(f"spawn: {lit} position(s) de spawn eclairees.")

    checks["structure"] = {
        "roof_present": all(world.block_name(x, g.roof_y, z) == "minecraft:deepslate_tiles" for x in range(g.outer_x1, g.outer_x2 + 1) for z in range(g.outer_z1, g.outer_z2 + 1)),
        "ladder_access": all("ladder" in world.block_name(g.ladder_x, y, g.ladder_z) for y in range(origin[1] + 1, g.roof_y + 1)),
        "floor_count": floors,
    }
    if not checks["structure"]["roof_present"]:
        status = "fail"
        findings.append("structure: toit incomplet.")
    if not checks["structure"]["ladder_access"]:
        status = "fail"
        findings.append("structure: echelle incomplete.")

    return {
        "status": status,
        "checks": checks,
        "findings": findings,
        "origin": {"x": origin[0], "y": origin[1], "z": origin[2]},
        "floors": floors,
        "bbox": {"x1": g.build_bbox[0], "y1": g.build_bbox[1], "z1": g.build_bbox[2], "x2": g.build_bbox[3], "y2": g.build_bbox[4], "z2": g.build_bbox[5]},
    }


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Validate a hostile mob tower by reading the world on disk.")
    ap.add_argument("--world", default="./data/world")
    ap.add_argument("--floors", type=int, default=3)
    ap.add_argument("--mode", choices=["built", "cleared"], default="built")
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--at", nargs=3, type=int, metavar=("X", "Y", "Z"), required=True)
    args = ap.parse_args(argv)

    origin = tuple(args.at)  # type: ignore[arg-type]
    world = WorldReader(Path(args.world))
    result = validate_world(world, origin, floors=args.floors, mode=args.mode)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
