#!/usr/bin/env python3
"""Verify the current live server baseline plus addon rollout artifacts.

The addon rollout mixes standard mod jars (in ``data/mods``) and at least one
downloaded datapack archive (in ``data/world/datapacks``). This checker parses
the selected installer scripts and validates the expected artifacts.

Usage:
  py -3 tools/check_addons_rollout.py --script infra/mods-install-openworld.sh
  py -3 tools/check_addons_rollout.py --write --out audit/addons-server-mods-check-lot1.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DEFAULT_SCRIPT_PATHS = [
    "infra/mods-install-openworld.sh",
    "infra/mods-install-waystones.sh",
    "infra/mods-install-better-qol.sh",
    "infra/mods-install-storage.sh",
    "infra/mods-install-progressive-lot1-macaws-furniture.sh",
    "infra/mods-install-progressive-lot2-handcrafted.sh",
    "infra/mods-install-progressive-lot3-supplementaries.sh",
    "infra/mods-install-progressive-lot4-yungs-strongholds.sh",
    "infra/mods-install-progressive-lot5-towns-and-towers.sh",
]

VAR_RE = re.compile(r'^([A-Z0-9_]+)_(URL|SHA256|FILE)="([^"]+)"$')
CALL_RE = re.compile(
    r'(ensure_mod|ensure_datapack_archive)\s+"([^"]+)"\s+"'
    r"\$\{([A-Z0-9_]+)_URL\}\"\s+\""
    r"\$\{([A-Z0-9_]+)_SHA256\}\"\s+\""
    r"\$\{([A-Z0-9_]+)_FILE\}\""
)


@dataclass
class ExpectedArtifact:
    kind: str  # mod | datapack_archive
    name: str
    file_name: str
    sha256: str
    url: str
    source_script: str


@dataclass
class CheckRow:
    kind: str
    name: str
    file_name: str
    source_script: str
    status: str  # missing | ok | hash_mismatch
    expected_sha256: str
    actual_sha256: str
    notes: str


def parse_installer_script(script_path: Path) -> List[ExpectedArtifact]:
    text = script_path.read_text(encoding="utf-8")
    vars_map: Dict[str, Dict[str, str]] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = VAR_RE.match(line)
        if not match:
            continue
        prefix, kind, value = match.groups()
        vars_map.setdefault(prefix, {})[kind] = value

    expected: List[ExpectedArtifact] = []
    for raw_line in text.splitlines():
        match = CALL_RE.search(raw_line)
        if not match:
            continue
        func_name, name, p_url, p_sha, p_file = match.groups()
        if len({p_url, p_sha, p_file}) != 1:
            continue
        prefix = p_url
        data = vars_map.get(prefix, {})
        kind = "mod" if func_name == "ensure_mod" else "datapack_archive"
        expected.append(
            ExpectedArtifact(
                kind=kind,
                name=name,
                file_name=data.get("FILE", ""),
                sha256=data.get("SHA256", "").lower(),
                url=data.get("URL", ""),
                source_script=script_path.as_posix(),
            )
        )

    return expected


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_expected(repo_root: Path, scripts: List[str]) -> List[ExpectedArtifact]:
    expected: List[ExpectedArtifact] = []
    for rel in scripts:
        path = (repo_root / rel).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Installer script not found: {rel}")
        expected.extend(parse_installer_script(path))

    dedup: Dict[Tuple[str, str], ExpectedArtifact] = {}
    for artifact in expected:
        if not artifact.file_name:
            continue
        key = (artifact.kind, artifact.file_name)
        prev = dedup.get(key)
        if prev and prev.sha256 != artifact.sha256:
            raise ValueError(
                f"Conflicting SHA256 for {artifact.kind}:{artifact.file_name}: "
                f"{prev.source_script} vs {artifact.source_script}"
            )
        dedup[key] = artifact

    return sorted(
        dedup.values(),
        key=lambda item: (item.kind, item.source_script, item.name.lower(), item.file_name.lower()),
    )


def check_expected_dir(
    expected: List[ExpectedArtifact],
    root_dir: Path,
    kind: str,
    pattern: str,
) -> Dict[str, object]:
    rows: List[CheckRow] = []

    if not expected:
        return {
            "dir": root_dir.as_posix(),
            "present": root_dir.exists(),
            "rows": [],
            "extras": [],
            "summary": {"expected_total": 0, "ok": 0, "missing": 0, "hash_mismatch": 0, "extras": 0},
            "message": "",
        }

    if not root_dir.exists():
        return {
            "dir": root_dir.as_posix(),
            "present": False,
            "rows": [
                asdict(
                    CheckRow(
                        kind=artifact.kind,
                        name=artifact.name,
                        file_name=artifact.file_name,
                        source_script=artifact.source_script,
                        status="missing",
                        expected_sha256=artifact.sha256,
                        actual_sha256="",
                        notes="expected directory does not exist locally",
                    )
                )
                for artifact in expected
            ],
            "extras": [],
            "summary": {
                "expected_total": len(expected),
                "ok": 0,
                "missing": len(expected),
                "hash_mismatch": 0,
                "extras": 0,
            },
            "message": f"Directory does not exist locally: {root_dir.as_posix()}",
        }

    actual_files = sorted(root_dir.glob(pattern))
    actual_names = {path.name for path in actual_files}

    for artifact in expected:
        path = root_dir / artifact.file_name
        if not path.exists():
            rows.append(
                CheckRow(
                    kind=artifact.kind,
                    name=artifact.name,
                    file_name=artifact.file_name,
                    source_script=artifact.source_script,
                    status="missing",
                    expected_sha256=artifact.sha256,
                    actual_sha256="",
                    notes="expected file not found",
                )
            )
            continue

        actual_sha = sha256_file(path)
        if artifact.sha256 and actual_sha.lower() != artifact.sha256.lower():
            rows.append(
                CheckRow(
                    kind=artifact.kind,
                    name=artifact.name,
                    file_name=artifact.file_name,
                    source_script=artifact.source_script,
                    status="hash_mismatch",
                    expected_sha256=artifact.sha256,
                    actual_sha256=actual_sha,
                    notes="file exists but sha256 differs",
                )
            )
        else:
            rows.append(
                CheckRow(
                    kind=artifact.kind,
                    name=artifact.name,
                    file_name=artifact.file_name,
                    source_script=artifact.source_script,
                    status="ok",
                    expected_sha256=artifact.sha256,
                    actual_sha256=actual_sha,
                    notes="",
                )
            )

    expected_names = {artifact.file_name for artifact in expected}
    extras = sorted(name for name in actual_names if name not in expected_names)

    summary = {
        "expected_total": len(expected),
        "ok": sum(1 for row in rows if row.status == "ok"),
        "missing": sum(1 for row in rows if row.status == "missing"),
        "hash_mismatch": sum(1 for row in rows if row.status == "hash_mismatch"),
        "extras": len(extras),
    }
    return {
        "dir": root_dir.as_posix(),
        "present": True,
        "rows": [asdict(row) for row in rows],
        "extras": extras,
        "summary": summary,
        "message": "",
    }


def print_human_report(result: Dict[str, object]) -> None:
    summary = result["summary"]
    print(
        "summary: "
        f"expected={summary['expected_total']} "
        f"ok={summary['ok']} missing={summary['missing']} "
        f"hash_mismatch={summary['hash_mismatch']} extras={summary['extras']}"
    )

    for section_name in ("mods", "datapacks"):
        section = result[section_name]
        print(f"\n[{section_name}] dir={section['dir']} present={section['present']}")
        if section.get("message"):
            print(f"note: {section['message']}")
        for row in section.get("rows", []):
            print(f"- [{row['status']}] {row['name']} ({row['file_name']})")
        extras = section.get("extras", [])
        if extras:
            print("extra files:")
            for name in extras:
                print(f"- {name}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check addon rollout artifacts against selected installer scripts")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root (default: parent of tools/)",
    )
    parser.add_argument(
        "--mods-dir",
        default=None,
        help="Mods directory (default: <repo-root>/data/mods)",
    )
    parser.add_argument(
        "--datapacks-dir",
        default=None,
        help="Datapacks directory (default: <repo-root>/data/world/datapacks)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write a JSON report",
    )
    parser.add_argument(
        "--script",
        action="append",
        default=[],
        help="Installer script to include in the expected rollout (repeatable).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional JSON report path when used with --write",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    mods_dir = Path(args.mods_dir).resolve() if args.mods_dir else (repo_root / "data" / "mods").resolve()
    datapacks_dir = (
        Path(args.datapacks_dir).resolve()
        if args.datapacks_dir
        else (repo_root / "data" / "world" / "datapacks").resolve()
    )
    script_paths = args.script or DEFAULT_SCRIPT_PATHS

    expected = build_expected(repo_root, script_paths)
    expected_mods = [item for item in expected if item.kind == "mod"]
    expected_datapacks = [item for item in expected if item.kind == "datapack_archive"]

    mods_result = check_expected_dir(expected_mods, mods_dir, "mod", "*.jar")
    datapacks_result = check_expected_dir(expected_datapacks, datapacks_dir, "datapack_archive", "*.zip")

    summary = {
        "expected_total": mods_result["summary"]["expected_total"] + datapacks_result["summary"]["expected_total"],
        "ok": mods_result["summary"]["ok"] + datapacks_result["summary"]["ok"],
        "missing": mods_result["summary"]["missing"] + datapacks_result["summary"]["missing"],
        "hash_mismatch": mods_result["summary"]["hash_mismatch"] + datapacks_result["summary"]["hash_mismatch"],
        "extras": mods_result["summary"]["extras"] + datapacks_result["summary"]["extras"],
    }

    result = {
        "mods": mods_result,
        "datapacks": datapacks_result,
        "summary": summary,
        "recommended_scripts": script_paths,
        "expected": [asdict(item) for item in expected],
    }

    if args.write:
        out = Path(args.out).resolve() if args.out else (repo_root / "audit" / "addons-rollout-check.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print_human_report(result)

    if not mods_result["present"] or not datapacks_result["present"] and expected_datapacks:
        return 0
    if summary["missing"] or summary["hash_mismatch"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
