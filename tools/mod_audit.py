#!/usr/bin/env python3
"""Audit Cobblemon mods inventory (modpack + repo extras + optional local server mods).

Generates:
  - audit/mods-current-inventory.csv
  - audit/mods-current-inventory.json

This script is intentionally best-effort:
- If `data/mods` is missing, it still builds a repo/modpack inventory.
- It resolves Modrinth project/version metadata for the pinned modpack dependencies.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


MODRINTH_API = "https://api.modrinth.com/v2"
USER_AGENT = "codex-cobblemon-mod-audit/1.0 (+local script)"

CSV_COLUMNS = [
    "source",
    "mod_name",
    "mod_id",
    "file_name",
    "version",
    "mc_version",
    "loader",
    "side",
    "category",
    "dependency_of",
    "status",
    "notes",
]


KNOWN_CATEGORY_OVERRIDES = {
    "cobblemon": "cobblemon_core",
    "waystones": "travel",
    "balm": "other",
    "chunky": "perf",
    "flan": "admin",
    "spark": "perf",
    "simple voice chat": "social",
    "voice chat": "social",
    "journeymap": "ui",
    "xaero": "ui",
    "wthit": "ui",
    "jade": "ui",
    "rei": "ui",
    "emi": "ui",
    "ferritecore": "perf",
    "lithium": "perf",
    "sodium": "perf",
    "starlight": "perf",
    "modernfix": "perf",
    "flan claim": "admin",
    "make bubbles pop": "other",
    "not enough animations": "other",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def _safe_join(values: Iterable[str], sep: str = "; ") -> str:
    cleaned = [v for v in values if v]
    return sep.join(cleaned)


class ModrinthClient:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._mem: Dict[str, Any] = {}

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def _get_json(self, url: str, cache_key: str) -> Any:
        if cache_key in self._mem:
            return self._mem[cache_key]

        cache_path = self._cache_path(cache_key)
        if cache_path.exists():
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            self._mem[cache_key] = data
            return data

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        last_err: Optional[Exception] = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    raw = resp.read()
                data = json.loads(raw.decode("utf-8"))
                cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                self._mem[cache_key] = data
                return data
            except Exception as exc:  # noqa: BLE001 - best-effort network retry
                last_err = exc
                time.sleep(0.6 * (attempt + 1))
        raise RuntimeError(f"Modrinth API request failed for {url}: {last_err}")

    def version(self, version_id: str) -> Dict[str, Any]:
        return self._get_json(f"{MODRINTH_API}/version/{version_id}", f"version_{version_id}")

    def project(self, project_id: str) -> Dict[str, Any]:
        return self._get_json(f"{MODRINTH_API}/project/{project_id}", f"project_{project_id}")

    def project_versions(self, project_id: str, game_version: str, loader: str) -> List[Dict[str, Any]]:
        params = urllib.parse.urlencode(
            {
                "game_versions": json.dumps([game_version]),
                "loaders": json.dumps([loader]),
            }
        )
        return self._get_json(
            f"{MODRINTH_API}/project/{project_id}/version?{params}",
            f"project_versions_{project_id}_{game_version}_{loader}",
        )


@dataclass
class ModRow:
    source: str
    mod_name: str
    mod_id: str
    file_name: str
    version: str
    mc_version: str
    loader: str
    side: str
    category: str
    dependency_of: str
    status: str
    notes: str

    def as_csv_row(self) -> Dict[str, str]:
        return {k: str(getattr(self, k, "")) for k in CSV_COLUMNS}

    def key(self) -> str:
        # Prefer mod_id when available, fallback to file stem/name.
        if self.mod_id and self.mod_id not in ("unknown", ""):
            return f"id:{_norm(self.mod_id)}"
        if self.file_name:
            return f"file:{_norm(Path(self.file_name).stem)}"
        return f"name:{_norm(self.mod_name)}"


def infer_side_from_modrinth_project(project: Dict[str, Any]) -> str:
    client = (project.get("client_side") or "").lower()
    server = (project.get("server_side") or "").lower()
    client_supported = client in {"required", "optional"}
    server_supported = server in {"required", "optional"}
    if server_supported and not client_supported:
        return "server_only"
    if client_supported and not server_supported:
        return "client_required"
    if client_supported and server_supported:
        return "both"
    return "unknown"


def infer_category(name: str, mod_id: str, modrinth_categories: Optional[List[str]] = None) -> str:
    haystack = f"{name} {mod_id}".lower()
    for token, cat in KNOWN_CATEGORY_OVERRIDES.items():
        if token in haystack:
            return cat

    cats = {c.lower() for c in (modrinth_categories or [])}
    if "optimization" in cats or "performance" in cats:
        return "perf"
    if "social" in cats or "communication" in cats:
        return "social"
    if "utility" in cats:
        # "utility" is too broad; keep as qol unless overridden.
        return "qol"
    if "worldgen" in cats:
        return "worldgen"
    if "adventure" in cats:
        return "structures"
    if "storage" in cats:
        return "qol"
    return "other"


def parse_mc_version_from_filename(filename: str) -> str:
    m = re.search(r"(1\.\d+(?:\.\d+)?)", filename or "")
    return m.group(1) if m else ""


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_modpack_rows(repo_root: Path, client: ModrinthClient) -> Tuple[List[ModRow], Dict[str, Any]]:
    manifest_path = repo_root / "manifest.Lydu1ZNo.json"
    manifest = load_json(manifest_path)
    game_versions = manifest.get("game_versions") or []
    loaders = manifest.get("loaders") or []
    mc_version = game_versions[0] if game_versions else ""
    loader = loaders[0] if loaders else ""

    rows: List[ModRow] = []
    for dep in manifest.get("dependencies", []):
        if dep.get("dependency_type") != "embedded":
            continue
        project_id = dep.get("project_id", "")
        version_id = dep.get("version_id", "")
        notes = [f"modrinth_project_id={project_id}", f"modrinth_version_id={version_id}"]

        version_meta: Dict[str, Any] = {}
        project_meta: Dict[str, Any] = {}
        try:
            if version_id:
                version_meta = client.version(version_id)
            if project_id:
                project_meta = client.project(project_id)
        except Exception as exc:  # noqa: BLE001 - keep audit going
            notes.append(f"resolve_error={type(exc).__name__}")

        file_name = ""
        files = version_meta.get("files") or []
        for f in files:
            if f.get("primary"):
                file_name = f.get("filename", "")
                break
        if not file_name and files:
            file_name = files[0].get("filename", "")

        version_number = version_meta.get("version_number", "")
        version_loaders = version_meta.get("loaders") or []
        version_gv = version_meta.get("game_versions") or []
        project_title = project_meta.get("title") or project_meta.get("name") or ""
        project_slug = project_meta.get("slug") or ""

        mod_name = project_title or version_meta.get("name") or file_name or project_id or version_id
        mod_id = project_slug or project_id or "unknown"
        side = infer_side_from_modrinth_project(project_meta) if project_meta else "unknown"
        category = infer_category(mod_name, mod_id, project_meta.get("categories") if project_meta else [])
        if project_meta:
            notes.append(
                f"client_side={project_meta.get('client_side','')};server_side={project_meta.get('server_side','')}"
            )
        if project_meta.get("project_type"):
            notes.append(f"project_type={project_meta['project_type']}")

        rows.append(
            ModRow(
                source="modpack_manifest",
                mod_name=mod_name,
                mod_id=mod_id,
                file_name=file_name,
                version=version_number,
                mc_version=mc_version or (version_gv[0] if version_gv else ""),
                loader=loader or (version_loaders[0] if version_loaders else ""),
                side=side,
                category=category,
                dependency_of="",
                status="embedded_in_pack",
                notes=_safe_join(notes),
            )
        )

    meta = {
        "mc_version": mc_version,
        "loader": loader,
        "modpack": manifest.get("name", ""),
        "modpack_version_number": manifest.get("version_number", ""),
        "modpack_version_id": manifest.get("id", ""),
        "modpack_project_id": manifest.get("project_id", ""),
    }
    return rows, meta


def parse_repo_script_mods(repo_root: Path, client: ModrinthClient, default_mc: str, default_loader: str) -> List[ModRow]:
    rows: List[ModRow] = []
    infra_dir = repo_root / "infra"
    var_re = re.compile(r'^([A-Z0-9_]+)_(URL|SHA256|FILE)="([^"]+)"$')
    ensure_re = re.compile(
        r'ensure_mod\s+"([^"]+)"\s+"\$\{([A-Z0-9_]+)_URL\}"\s+"\$\{([A-Z0-9_]+)_SHA256\}"\s+"\$\{([A-Z0-9_]+)_FILE\}"'
    )

    for script_path in sorted(infra_dir.glob("mods-install-*.sh")):
        text = script_path.read_text(encoding="utf-8")
        vars_map: Dict[str, Dict[str, str]] = {}
        for line in text.splitlines():
            m = var_re.match(line.strip())
            if not m:
                continue
            prefix, kind, value = m.groups()
            vars_map.setdefault(prefix, {})[kind] = value

        for line in text.splitlines():
            m = ensure_re.search(line)
            if not m:
                continue
            name, prefix_url, prefix_sha, prefix_file = m.groups()
            if len({prefix_url, prefix_sha, prefix_file}) != 1:
                continue
            prefix = prefix_url
            data = vars_map.get(prefix, {})
            url = data.get("URL", "")
            file_name = data.get("FILE", "")
            sha = data.get("SHA256", "")
            notes = [
                f"declared_in={script_path.relative_to(repo_root).as_posix()}",
                "planned_extra_from_repo_script",
            ]
            if sha:
                notes.append(f"sha256={sha}")
            if url:
                notes.append(f"url={url}")

            mod_id = _slugify(name) or "unknown"
            version = parse_mc_version_from_filename(file_name)
            side = "unknown"
            category = infer_category(name, mod_id)

            # Resolve Modrinth metadata when URL is a Modrinth CDN URL.
            modrinth_match = re.search(r"/data/([^/]+)/versions/([^/]+)/", url)
            if modrinth_match:
                project_id, version_id = modrinth_match.groups()
                notes.append(f"modrinth_project_id={project_id}")
                notes.append(f"modrinth_version_id={version_id}")
                try:
                    version_meta = client.version(version_id)
                    project_meta = client.project(project_id)
                    mod_id = project_meta.get("slug") or project_id
                    version = version_meta.get("version_number") or version
                    side = infer_side_from_modrinth_project(project_meta)
                    category = infer_category(
                        project_meta.get("title") or name,
                        mod_id,
                        project_meta.get("categories") or [],
                    )
                    name = project_meta.get("title") or name
                except Exception as exc:  # noqa: BLE001
                    notes.append(f"resolve_error={type(exc).__name__}")

            if name.lower() == "balm":
                dep_of = "Waystones"
            else:
                dep_of = ""

            rows.append(
                ModRow(
                    source="repo_script",
                    mod_name=name,
                    mod_id=mod_id,
                    file_name=file_name,
                    version=version,
                    mc_version=default_mc or parse_mc_version_from_filename(file_name),
                    loader=default_loader or "fabric",
                    side=side,
                    category=category,
                    dependency_of=dep_of,
                    status="candidate",
                    notes=_safe_join(notes),
                )
            )
    return rows


def read_fabric_mod_json_from_jar(jar_path: Path) -> Dict[str, Any]:
    with zipfile.ZipFile(jar_path, "r") as zf:
        # Fabric mods expose `fabric.mod.json`.
        for candidate in ("fabric.mod.json",):
            try:
                with zf.open(candidate) as fh:
                    return json.loads(fh.read().decode("utf-8"))
            except KeyError:
                continue
    return {}


def parse_server_mods_dir(mods_dir: Path, default_loader: str) -> List[ModRow]:
    rows: List[ModRow] = []
    if not mods_dir.exists():
        return rows

    for jar in sorted(mods_dir.glob("*.jar")):
        notes = [f"path={jar.as_posix()}"]
        meta = {}
        try:
            meta = read_fabric_mod_json_from_jar(jar)
        except Exception as exc:  # noqa: BLE001 - keep audit running
            notes.append(f"manifest_parse_error={type(exc).__name__}")

        mod_name = meta.get("name") or jar.stem
        mod_id = meta.get("id") or "unknown"
        version = str(meta.get("version") or "")
        env = str(meta.get("environment") or "*").lower()
        if env == "server":
            side = "server_only"
        elif env == "client":
            side = "client_required"
        elif env in {"*", "universal"}:
            side = "both"
        else:
            side = "unknown"

        mc_version = ""
        depends = meta.get("depends") or {}
        if isinstance(depends, dict) and "minecraft" in depends:
            mc_version = str(depends.get("minecraft") or "")
        dep_of = "Waystones" if _norm(mod_name) == "balm" or _norm(mod_id) == "balm" else ""

        rows.append(
            ModRow(
                source="server_mods_dir",
                mod_name=mod_name,
                mod_id=mod_id,
                file_name=jar.name,
                version=version,
                mc_version=mc_version,
                loader=default_loader or "fabric",
                side=side,
                category=infer_category(mod_name, mod_id),
                dependency_of=dep_of,
                status="active",
                notes=_safe_join(notes),
            )
        )
    return rows


def reconcile_statuses(rows: List[ModRow]) -> None:
    """Adjust server/repo statuses based on overlaps with modpack rows."""
    modpack_keys = {row.key() for row in rows if row.source == "modpack_manifest"}
    server_keys = {row.key() for row in rows if row.source == "server_mods_dir"}

    for row in rows:
        if row.source == "server_mods_dir":
            row.status = "active" if row.key() in modpack_keys else "extra_added"
        elif row.source == "repo_script":
            if row.key() in modpack_keys:
                row.notes = _safe_join([row.notes, "overlap_with_modpack=true"])
            if row.key() in server_keys:
                row.notes = _safe_join([row.notes, "observed_in_server_mods=true"])


def collect_duplicate_findings(rows: List[ModRow]) -> List[Dict[str, Any]]:
    groups: Dict[str, List[ModRow]] = {}
    for row in rows:
        groups.setdefault(row.key(), []).append(row)
    findings = []
    for key, group in sorted(groups.items()):
        versions = sorted({g.version for g in group if g.version})
        if len(group) > 1:
            findings.append(
                {
                    "key": key,
                    "count": len(group),
                    "sources": [g.source for g in group],
                    "mod_names": sorted({g.mod_name for g in group}),
                    "versions": versions,
                    "file_names": sorted({g.file_name for g in group if g.file_name}),
                }
            )
    return findings


def write_csv(path: Path, rows: List[ModRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_csv_row())


def write_json(path: Path, meta: Dict[str, Any], rows: List[ModRow], duplicates: List[Dict[str, Any]], limitations: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": meta,
        "mods": [asdict(r) for r in rows],
        "observations": {
            "counts_by_source": {
                src: sum(1 for r in rows if r.source == src) for src in sorted({r.source for r in rows})
            },
            "duplicates_or_overlaps": duplicates,
            "limitations": limitations,
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_inventory(repo_root: Path, mods_dir: Optional[Path] = None) -> Tuple[Dict[str, Any], List[ModRow], List[Dict[str, Any]], List[str]]:
    audit_dir = repo_root / "audit"
    cache_dir = audit_dir / ".cache"
    client = ModrinthClient(cache_dir)

    modpack_rows, meta = resolve_modpack_rows(repo_root, client)
    repo_rows = parse_repo_script_mods(repo_root, client, meta.get("mc_version", ""), meta.get("loader", ""))

    effective_mods_dir = mods_dir or (repo_root / "data" / "mods")
    server_rows = parse_server_mods_dir(effective_mods_dir, meta.get("loader", ""))

    rows = modpack_rows + repo_rows + server_rows
    reconcile_statuses(rows)

    # Keep deterministic ordering.
    rows.sort(key=lambda r: (r.source, r.category, r.mod_name.lower(), r.file_name.lower()))

    duplicates = collect_duplicate_findings(rows)
    limitations: List[str] = []
    if not effective_mods_dir.exists():
        limitations.append(f"Local server mods directory not found: {effective_mods_dir.as_posix()}")
        limitations.append("`server_mods_dir` rows are absent; statuses are repo/modpack-only except repo_script candidates.")
    if not server_rows:
        limitations.append("No local runtime boot log (`data/logs/latest.log`) was parsed in this audit.")

    meta.update(
        {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo_root": repo_root.as_posix(),
            "server_mods_dir": effective_mods_dir.as_posix(),
            "server_mods_dir_present": effective_mods_dir.exists(),
        }
    )
    return meta, rows, duplicates, limitations


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Cobblemon mods inventory")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root (default: parent of tools/)",
    )
    parser.add_argument(
        "--mods-dir",
        default=None,
        help="Optional local server mods dir (default: <repo-root>/data/mods)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write audit/mods-current-inventory.csv and .json",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    mods_dir = Path(args.mods_dir).resolve() if args.mods_dir else None

    meta, rows, duplicates, limitations = build_inventory(repo_root, mods_dir)

    if args.write:
        audit_dir = repo_root / "audit"
        write_csv(audit_dir / "mods-current-inventory.csv", rows)
        write_json(audit_dir / "mods-current-inventory.json", meta, rows, duplicates, limitations)

    # Human-readable summary for terminal use.
    counts_by_source: Dict[str, int] = {}
    for row in rows:
        counts_by_source[row.source] = counts_by_source.get(row.source, 0) + 1
    summary = {
        "meta": meta,
        "counts_by_source": counts_by_source,
        "total_rows": len(rows),
        "overlap_groups": len(duplicates),
        "limitations": limitations,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
