#!/usr/bin/env python3
"""Audit the Academy compatibility gate against the current Cobblemon base."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = REPO_ROOT / "modpack" / "academy-v2" / "stack.lock.json"


def load_lock(path: Path = LOCK_PATH) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_dependency_version(build_text: str, dependency_prefix: str) -> Optional[str]:
    pattern = re.compile(re.escape(dependency_prefix) + r"([^\"']+)")
    match = pattern.search(build_text)
    return match.group(1) if match else None


def extract_upstream_signals(lock: Dict) -> Dict:
    source = lock["academy_source"]
    fabric_gradle = (REPO_ROOT / source["fabric_build_gradle"]).read_text(encoding="utf-8")
    common_gradle = (REPO_ROOT / source["common_build_gradle"]).read_text(encoding="utf-8")

    return {
        "cobblemon_fabric_version": extract_dependency_version(fabric_gradle, "com.cobblemon:fabric:"),
        "cobblemon_common_version": extract_dependency_version(common_gradle, "com.cobblemon:mod:"),
        "has_ftb_quests": "ftb-quests" in fabric_gradle.lower(),
        "has_numismatic": "numismatic-overhaul" in fabric_gradle.lower(),
        "has_rad_gyms": "rad-gyms" in common_gradle.lower(),
        "has_extraquests": "extraquests" in common_gradle.lower(),
        "has_eternal_starlight": "eternal-starlight" in fabric_gradle.lower(),
    }


def compatibility_decision(lock: Dict, signals: Dict) -> Dict:
    base_cobblemon = lock["base_stack"]["cobblemon_mod"]["version"]
    upstream_cobblemon = signals.get("cobblemon_fabric_version")
    gate = lock["compatibility_gate"]

    if upstream_cobblemon == base_cobblemon:
        return {
            "mode": "full_candidate",
            "reason": "Upstream Academy Integration matches the current Cobblemon base; the full gate can be re-evaluated."
        }

    return {
        "mode": gate["mode"],
        "reason": gate["decision_reason"],
        "base_cobblemon": base_cobblemon,
        "upstream_cobblemon": upstream_cobblemon,
    }


def summarize_components(lock: Dict) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for component in lock["components"]:
        out.setdefault(component["status"], []).append(component["id"])
    return out


def build_report(lock: Dict) -> Dict:
    signals = extract_upstream_signals(lock)
    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "base_stack": lock["base_stack"],
        "academy_source": lock["academy_source"],
        "upstream_signals": signals,
        "decision": compatibility_decision(lock, signals),
        "status_summary": summarize_components(lock),
        "install_groups": lock["install_groups"],
        "blocked_components": [
            {
                "id": component["id"],
                "name": component["name"],
                "blocked_by": component.get("blocked_by"),
                "notes": component.get("notes", []),
            }
            for component in lock["components"]
            if component["status"] == "blocked_without_fork"
        ],
        "viable_components": [
            {
                "id": component["id"],
                "name": component["name"],
                "status": component["status"],
                "install_group": component.get("install_group"),
            }
            for component in lock["components"]
            if component["status"] != "blocked_without_fork"
        ],
    }
    return report


def render_markdown(report: Dict) -> str:
    decision = report["decision"]
    lines = [
        "# Academy Compatibility Audit",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Base Cobblemon: `{report['base_stack']['cobblemon_mod']['version']}`",
        f"- Upstream Academy Cobblemon: `{report['upstream_signals'].get('cobblemon_fabric_version') or 'unknown'}`",
        f"- Decision: `{decision['mode']}`",
        f"- Reason: {decision['reason']}",
        "",
        "## Status Summary",
    ]
    for status, component_ids in sorted(report["status_summary"].items()):
        lines.append(f"- `{status}`: {', '.join(component_ids)}")

    lines.extend(["", "## Install Groups"])
    for group, component_ids in report["install_groups"].items():
        lines.append(f"- `{group}`: {', '.join(component_ids)}")

    lines.extend(["", "## Blocked Components"])
    for component in report["blocked_components"]:
        blocked_by = component.get("blocked_by") or {}
        lines.append(f"- `{component['id']}`: {blocked_by.get('reason', 'blocked')}")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the Academy compatibility gate on top of the current Cobblemon base.")
    parser.add_argument("--lock", default=str(LOCK_PATH), help="Path to modpack/academy-v2/stack.lock.json")
    parser.add_argument("--json-out", default=None, help="Optional explicit JSON output path")
    parser.add_argument("--md-out", default=None, help="Optional explicit markdown output path")
    parser.add_argument("--stdout", action="store_true", help="Print the JSON report to stdout as well")
    return parser.parse_args()


def default_output_paths() -> Dict[str, Path]:
    stamp = dt.datetime.now().strftime("%Y%m%d")
    audit_dir = REPO_ROOT / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    return {
        "json": audit_dir / f"academy-compat-audit-{stamp}.json",
        "md": audit_dir / f"academy-compat-audit-{stamp}.md",
    }


def main() -> int:
    args = parse_args()
    lock_path = Path(args.lock)
    lock = load_lock(lock_path)
    report = build_report(lock)
    defaults = default_output_paths()

    json_out = Path(args.json_out) if args.json_out else defaults["json"]
    md_out = Path(args.md_out) if args.md_out else defaults["md"]

    json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(report), encoding="utf-8")

    if args.stdout:
      print(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"Wrote {json_out}")
    print(f"Wrote {md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
