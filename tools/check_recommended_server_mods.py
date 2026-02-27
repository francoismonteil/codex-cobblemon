#!/usr/bin/env python3
"""Verify local server mods directory against the recommended server mod pack.

Recommended pack is defined by the selected installer scripts:
- infra/mods-install-openworld.sh
- infra/mods-install-waystones.sh
- infra/mods-install-better-qol.sh
- infra/mods-install-storage.sh

The script parses `ensure_mod` calls + pinned SHA256 values from these scripts,
then checks `data/mods` for:
- missing files
- hash mismatches
- unexpected extra jars

Usage:
  py -3 tools/check_recommended_server_mods.py
  py -3 tools/check_recommended_server_mods.py --mods-dir .\\data\\mods --write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_SCRIPT_PATHS = [
    "infra/mods-install-openworld.sh",
    "infra/mods-install-waystones.sh",
    "infra/mods-install-better-qol.sh",
    "infra/mods-install-storage.sh",
]


@dataclass
class ExpectedMod:
    name: str
    file_name: str
    sha256: str
    url: str
    source_script: str


@dataclass
class CheckRow:
    name: str
    file_name: str
    source_script: str
    status: str  # missing | ok | hash_mismatch
    expected_sha256: str
    actual_sha256: str
    notes: str


VAR_RE = re.compile(r'^([A-Z0-9_]+)_(URL|SHA256|FILE)="([^"]+)"$')
ENSURE_RE = re.compile(
    r'ensure_mod\s+"([^"]+)"\s+"\$\{([A-Z0-9_]+)_URL\}"\s+"\$\{([A-Z0-9_]+)_SHA256\}"\s+"\$\{([A-Z0-9_]+)_FILE\}"'
)


def parse_installer_script(script_path: Path) -> List[ExpectedMod]:
    text = script_path.read_text(encoding="utf-8")
    vars_map: Dict[str, Dict[str, str]] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        m = VAR_RE.match(line)
        if not m:
            continue
        prefix, kind, value = m.groups()
        vars_map.setdefault(prefix, {})[kind] = value

    expected: List[ExpectedMod] = []
    for raw_line in text.splitlines():
        m = ENSURE_RE.search(raw_line)
        if not m:
            continue
        name, p_url, p_sha, p_file = m.groups()
        if len({p_url, p_sha, p_file}) != 1:
            continue
        prefix = p_url
        data = vars_map.get(prefix, {})
        expected.append(
            ExpectedMod(
                name=name,
                file_name=data.get("FILE", ""),
                sha256=data.get("SHA256", "").lower(),
                url=data.get("URL", ""),
                source_script=script_path.as_posix(),
            )
        )

    return expected


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_expected(repo_root: Path, scripts: List[str]) -> List[ExpectedMod]:
    expected: List[ExpectedMod] = []
    for rel in scripts:
        path = (repo_root / rel).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Installer script not found: {rel}")
        expected.extend(parse_installer_script(path))

    # Deduplicate by filename (same file can be referenced once across scripts).
    dedup: Dict[str, ExpectedMod] = {}
    for mod in expected:
        if not mod.file_name:
            continue
        prev = dedup.get(mod.file_name)
        if prev and (prev.sha256 != mod.sha256):
            raise ValueError(
                f"Conflicting SHA256 for {mod.file_name}: {prev.source_script} vs {mod.source_script}"
            )
        dedup[mod.file_name] = mod
    return sorted(dedup.values(), key=lambda m: (m.source_script, m.name.lower(), m.file_name.lower()))


def check_mods_dir(mods_dir: Path, expected: List[ExpectedMod]) -> Dict[str, object]:
    rows: List[CheckRow] = []
    expected_by_file = {m.file_name: m for m in expected}
    extras: List[str] = []

    if not mods_dir.exists():
        return {
            "mods_dir": mods_dir.as_posix(),
            "mods_dir_present": False,
            "rows": [],
            "extras": [],
            "summary": {
                "expected_total": len(expected),
                "ok": 0,
                "missing": len(expected),
                "hash_mismatch": 0,
                "extras": 0,
            },
            "message": "Mods directory does not exist locally. Sync/copy ./data first, then rerun.",
        }

    actual_files = sorted(mods_dir.glob("*.jar"))
    actual_names = {p.name for p in actual_files}

    for mod in expected:
        path = mods_dir / mod.file_name
        if not path.exists():
            rows.append(
                CheckRow(
                    name=mod.name,
                    file_name=mod.file_name,
                    source_script=mod.source_script,
                    status="missing",
                    expected_sha256=mod.sha256,
                    actual_sha256="",
                    notes="expected file not found",
                )
            )
            continue

        actual_sha = sha256_file(path)
        if mod.sha256 and actual_sha.lower() != mod.sha256.lower():
            rows.append(
                CheckRow(
                    name=mod.name,
                    file_name=mod.file_name,
                    source_script=mod.source_script,
                    status="hash_mismatch",
                    expected_sha256=mod.sha256,
                    actual_sha256=actual_sha,
                    notes="file exists but sha256 differs",
                )
            )
        else:
            rows.append(
                CheckRow(
                    name=mod.name,
                    file_name=mod.file_name,
                    source_script=mod.source_script,
                    status="ok",
                    expected_sha256=mod.sha256,
                    actual_sha256=actual_sha,
                    notes="",
                )
            )

    expected_names = set(expected_by_file.keys())
    extras = sorted(name for name in actual_names if name not in expected_names)

    summary = {
        "expected_total": len(expected),
        "ok": sum(1 for r in rows if r.status == "ok"),
        "missing": sum(1 for r in rows if r.status == "missing"),
        "hash_mismatch": sum(1 for r in rows if r.status == "hash_mismatch"),
        "extras": len(extras),
    }
    return {
        "mods_dir": mods_dir.as_posix(),
        "mods_dir_present": True,
        "rows": [asdict(r) for r in rows],
        "extras": extras,
        "summary": summary,
        "message": "",
    }


def print_human_report(result: Dict[str, object]) -> None:
    summary = result["summary"]
    print(f"mods_dir: {result['mods_dir']}")
    print(f"mods_dir_present: {result['mods_dir_present']}")
    print(
        "summary: "
        f"expected={summary['expected_total']} "
        f"ok={summary['ok']} missing={summary['missing']} "
        f"hash_mismatch={summary['hash_mismatch']} extras={summary['extras']}"
    )
    if result.get("message"):
        print(f"note: {result['message']}")

    rows = result.get("rows", [])
    if rows:
        print("\nchecks:")
        for row in rows:
            print(f"- [{row['status']}] {row['name']} ({row['file_name']})")
    extras = result.get("extras", [])
    if extras:
        print("\nextra jars (not in recommended pack):")
        for name in extras:
            print(f"- {name}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check local server mods against recommended pack")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root (default: parent of tools/)",
    )
    parser.add_argument(
        "--mods-dir",
        default=None,
        help="Server mods directory (default: <repo-root>/data/mods)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write JSON report to audit/recommended-server-mods-check.json",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    mods_dir = Path(args.mods_dir).resolve() if args.mods_dir else (repo_root / "data" / "mods").resolve()

    expected = build_expected(repo_root, DEFAULT_SCRIPT_PATHS)
    result = check_mods_dir(mods_dir, expected)
    result["recommended_scripts"] = DEFAULT_SCRIPT_PATHS
    result["expected"] = [asdict(m) for m in expected]

    if args.write:
        out = repo_root / "audit" / "recommended-server-mods-check.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print_human_report(result)

    # Non-zero exit only when mods_dir exists and there are problems.
    if not result["mods_dir_present"]:
        return 0
    summary = result["summary"]
    if summary["missing"] or summary["hash_mismatch"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
