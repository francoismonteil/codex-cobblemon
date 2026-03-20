#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from hostile_mob_tower_spec import recommended_afk_positions, reference_player_positions, spawn_distance_metrics


def build_report(origin, floors: int) -> dict:
    diagnostics = []
    for label, pos in reference_player_positions(origin, floors).items():
        diagnostics.append(
            {
                "label": label,
                "pos": {"x": pos[0], "y": pos[1], "z": pos[2]},
                "metrics": spawn_distance_metrics(origin, floors, pos),
            }
        )
    return {
        "schema_version": 1,
        "kind": "hostile_mob_tower_afk_report",
        "origin": {"x": origin[0], "y": origin[1], "z": origin[2]},
        "floors": floors,
        "diagnostics": diagnostics,
        "recommended_positions": recommended_afk_positions(origin, floors),
    }


def _render_text(report: dict) -> str:
    lines = []
    origin = report["origin"]
    lines.append(f"origin: {origin['x']} {origin['y']} {origin['z']} floors={report['floors']}")
    lines.append("diagnostics:")
    for item in report["diagnostics"]:
        m = item["metrics"]
        p = item["pos"]
        lines.append(
            f"  - {item['label']}: {p['x']} {p['y']} {p['z']} "
            f"(min={m['min_distance']}, max={m['max_distance']}, active={m['active_positions']}/{m['total_positions']})"
        )
    lines.append("recommended_positions:")
    for item in report["recommended_positions"]:
        m = item["metrics"]
        p = item["pos"]
        lines.append(
            f"  - {item['label']}: {p['x']} {p['y']} {p['z']} "
            f"(min={m['min_distance']}, max={m['max_distance']}, active={m['active_positions']}/{m['total_positions']})"
        )
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Show AFK spots and distance diagnostics for a hostile mob tower.")
    ap.add_argument("--at", nargs=3, type=int, metavar=("X", "Y", "Z"), required=True)
    ap.add_argument("--floors", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    origin = tuple(args.at)
    report = build_report(origin, args.floors)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
