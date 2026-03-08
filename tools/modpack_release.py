#!/usr/bin/env python3
"""Build and validate the public client modpack release artifacts.

Commands:
  - sync-lock
  - validate
  - build --version <semver>
  - publish-checklist --version <semver>

The lock catalog is the source of truth for release builds.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = REPO_ROOT / "modpack" / "public-client-pack"
LOCK_PATH = PUBLIC_ROOT / "catalog.lock.json"
PACKWIZ_DIR = PUBLIC_ROOT / "packwiz"
OVERRIDES_DIR = PUBLIC_ROOT / "overrides"
CACHE_DIR = PUBLIC_ROOT / ".cache" / "http"
DIST_DIR = REPO_ROOT / "dist"

RUNBOOK_PATH = REPO_ROOT / "runbooks" / "client-pack-recommended.md"
BASE_MANIFEST_PATH = REPO_ROOT / "manifest.Lydu1ZNo.json"

MODRINTH_API = "https://api.modrinth.com/v2"
CURSE_TOOLS_API = "https://api.curse.tools/v1/cf"
USER_AGENT = "codex-cobblemon-modpack-release/1.0"

MC_VERSION = "1.21.1"
LOADER = "fabric"
LOADER_TYPE_FABRIC = 4
BASE_MODRINTH_VERSION_ID = "Lydu1ZNo"
FALLBACK_FABRIC_LOADER_VERSION = "0.16.14"
LOCK_SCHEMA_VERSION = 1

PACK_META = {
    "name": "Cobblemon Community Client Pack",
    "slug": "cobblemon-community-client-pack",
    "author": "Cobblemon Community",
    "summary_fr": "Pack client complet Cobblemon 1.21.1 Fabric, aligne serveur, publie sur CurseForge + Modrinth.",
    "summary_en": "Complete Cobblemon client pack for 1.21.1 Fabric, server-aligned, published on CurseForge + Modrinth.",
}

EXTRA_MODRINTH_PINS: Dict[str, Tuple[str, str]] = {
    "Waystones": ("LOpKHB2A", "iemNwSsG"),
    "Traveler's Backpack": ("rlloIFEV", "i6cd1S6S"),
    "You're in Grave Danger (YIGD)": ("HnD1GX6e", "T3grMjgj"),
    "Storage Drawers": ("guitPqEi", "78LmfH8Z"),
    "Tom's Simple Storage Mod": ("XZNI4Cpy", "GwLz79tK"),
    "Macaw's Furniture": ("dtWC90iB", "x2pXgG0s"),
    "Resourceful Lib": ("G1hIVOrD", "Hf91FuVF"),
    "Handcrafted": ("pJmCFF0p", "f0pKpUWd"),
    "Moonlight Lib": ("twkfQtEc", "S33USEw7"),
    "Supplementaries": ("fFEIiSDQ", "lCX23NTg"),
    "Cristel Lib": ("cl223EMc", "h5nfApnW"),
    "Towns and Towers": ("DjLobEOy", "E4Wy3O8Y"),
    "Inventory Profiles Next (IPN)": ("O7RBXm3n", "A2gB9UGG"),
    "libIPN": ("onSQdWhM", "3rPzmg5m"),
    "Fabric Language Kotlin": ("Ha28R6CL", "ViT4gucI"),
    "FallingTree": ("Fb4jn8m6", "wxGXaJMA"),
}

CURSEFORGE_SLUG_OVERRIDES: Dict[str, str] = {
    "better-leaves": "motschens-better-leaves",
    "sodium-extras": "magnesium-extras",
    "make_bubbles_pop": "make-bubbles-pop",
    "almanac": "almanac-lib",
    "bookshelf-lib": "bookshelf",
    "emi-professions-(emip)": "emi-professions-emip",
    "fallingleaves": "falling-leaves-fabric",
    "entitytexturefeatures": "entity-texture-features-fabric",
    "lmd": "let-me-despawn",
    "moonlight": "selene",
    "travelers-backpack": "travelers-backpack-fabric",
    "bisect-mod": "bisecthosting-server-integration-menu-fabric",
    "ferrite-core": "ferritecore-fabric",
    "iris": "irisshaders",
    "travelersbackpack": "travelers-backpack-fabric",
}

PROJECT_TYPE_CLASS_HINT = {
    "mod": 6,
    "resourcepack": 12,
    "shader": 6552,
    "shaderpack": 6552,
}

# Explicit exclusions to keep strict cross-platform intersection.
# These upstream components do not currently have matching CurseForge files
# for the pinned 1.21.1/Fabric line.
INTERSECTION_EXCLUDE_SLUGS = {
    "particular",
    "bad-wither-no-cookie",
    "enhanced-attack-indicator",
    "presence-footsteps",
    "swingthrough",
}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def semver_ok(version: str) -> bool:
    return re.match(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$", version) is not None


def slugify(s: str) -> str:
    v = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return v or "unnamed"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def toml_str(value: str) -> str:
    return json.dumps(value)


def sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    aset = set(a)
    bset = set(b)
    inter = len(aset & bset)
    union = len(aset | bset)
    return inter / union if union else 0.0


def extract_version_tokens(version_number: str) -> List[str]:
    return re.findall(r"\d+(?:\.\d+)+", version_number or "")


def primary_version_token(version_number: str, mc_version: str) -> str:
    tokens = extract_version_tokens(version_number)
    filtered = [t for t in tokens if t != mc_version]
    base = filtered if filtered else tokens
    if not base:
        return ""
    base.sort(key=lambda t: (t.count("."), len(t)), reverse=True)
    return base[0]


class JsonHttpClient:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        ensure_dir(cache_dir)
        self.mem: Dict[str, Any] = {}

    def _cache_path(self, key: str, ext: str = "json") -> Path:
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.{ext}"

    def get_json(self, url: str, retries: int = 3) -> Any:
        if url in self.mem:
            return self.mem[url]
        cache_path = self._cache_path(url, "json")
        if cache_path.exists():
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            self.mem[url] = data
            return data

        last_err: Optional[Exception] = None
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        for i in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:
                    raw = resp.read().decode("utf-8")
                data = json.loads(raw)
                cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                self.mem[url] = data
                return data
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                time.sleep(0.5 * (i + 1))
        raise RuntimeError(f"HTTP JSON failed for {url}: {last_err}")

    def get_bytes(self, url: str, retries: int = 3) -> bytes:
        if url in self.mem:
            payload = self.mem[url]
            if isinstance(payload, bytes):
                return payload
        cache_path = self._cache_path(url, "bin")
        if cache_path.exists():
            raw = cache_path.read_bytes()
            self.mem[url] = raw
            return raw

        last_err: Optional[Exception] = None
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        for i in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    raw = resp.read()
                cache_path.write_bytes(raw)
                self.mem[url] = raw
                return raw
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                time.sleep(0.8 * (i + 1))
        raise RuntimeError(f"HTTP bytes failed for {url}: {last_err}")


def modrinth_project(client: JsonHttpClient, project_id_or_slug: str) -> Dict[str, Any]:
    return client.get_json(f"{MODRINTH_API}/project/{project_id_or_slug}")


def modrinth_version(client: JsonHttpClient, version_id: str) -> Dict[str, Any]:
    return client.get_json(f"{MODRINTH_API}/version/{version_id}")


def modrinth_project_versions(client: JsonHttpClient, project_id: str, mc_version: str, loader: str) -> List[Dict[str, Any]]:
    params = urllib.parse.urlencode(
        {
            "game_versions": json.dumps([mc_version]),
            "loaders": json.dumps([loader]),
        }
    )
    return client.get_json(f"{MODRINTH_API}/project/{project_id}/version?{params}")


def parse_runbook_recommended_mods(runbook_path: Path) -> List[Dict[str, Any]]:
    text = runbook_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_target = False
    optional_section = False
    items: List[Dict[str, Any]] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Mods client a ajouter"):
            in_target = True
            continue
        if in_target and stripped.startswith("## Deja dans le modpack officiel"):
            break
        if not in_target:
            continue
        if stripped.startswith("###"):
            optional_section = "optionnel" in stripped.lower()
            continue
        m = re.match(r"- `([^`]+)`(?: -> `([^`]+)`)?", stripped)
        if not m:
            continue
        items.append(
            {
                "name": m.group(1).strip(),
                "version_hint": (m.group(2) or "").strip(),
                "optional": optional_section,
            }
        )
    return items


def infer_side_from_modrinth_project(project: Dict[str, Any]) -> str:
    client_side = (project.get("client_side") or "").lower()
    server_side = (project.get("server_side") or "").lower()
    client_ok = client_side in {"required", "optional"}
    server_ok = server_side in {"required", "optional"}
    if client_ok and not server_ok:
        return "client_only"
    if client_ok and server_ok:
        return "both"
    if server_ok and not client_ok:
        return "server_only"
    return "both"


def select_primary_file(version_meta: Dict[str, Any]) -> Dict[str, Any]:
    files = version_meta.get("files") or []
    for f in files:
        if f.get("primary"):
            return f
    return files[0] if files else {}


def get_modrinth_compatible_version_id(
    client: JsonHttpClient,
    project_id: str,
    mc_version: str,
    loader: str,
) -> Optional[str]:
    versions = modrinth_project_versions(client, project_id, mc_version, loader)
    if not versions:
        return None
    releases = [v for v in versions if (v.get("version_type") or "").lower() == "release"]
    chosen = releases[0] if releases else versions[0]
    return chosen.get("id")


@dataclass
class VersionPin:
    project_id: str
    version_id: str
    origin: str
    optional: bool


def collect_target_pins(client: JsonHttpClient) -> Tuple[Dict[str, VersionPin], List[str]]:
    warnings: List[str] = []
    manifest = read_json(BASE_MANIFEST_PATH)
    pins: Dict[str, VersionPin] = {}

    for dep in manifest.get("dependencies", []):
        project_id = dep.get("project_id")
        version_id = dep.get("version_id")
        dep_type = dep.get("dependency_type")
        if dep_type != "embedded":
            continue
        if not project_id or not version_id:
            continue
        pins[project_id] = VersionPin(
            project_id=project_id,
            version_id=version_id,
            origin="base_official",
            optional=False,
        )

    runbook_mods = parse_runbook_recommended_mods(RUNBOOK_PATH)
    missing_map: List[str] = []
    extra_pin_list: List[VersionPin] = []
    for item in runbook_mods:
        name = item["name"]
        pin = EXTRA_MODRINTH_PINS.get(name)
        if not pin:
            missing_map.append(name)
            continue
        extra_pin_list.append(
            VersionPin(
                project_id=pin[0],
                version_id=pin[1],
                origin="recommended_extra",
                optional=bool(item["optional"]),
            )
        )
    if missing_map:
        raise RuntimeError(
            "Missing EXTRA_MODRINTH_PINS entries for runbook mods: " + ", ".join(sorted(missing_map))
        )

    for ep in extra_pin_list:
        existing = pins.get(ep.project_id)
        if existing and existing.version_id != ep.version_id:
            warnings.append(
                f"Version override ignored for project {ep.project_id}: "
                f"base={existing.version_id}, extra={ep.version_id}"
            )
            continue
        if not existing:
            pins[ep.project_id] = ep

    queue: List[VersionPin] = extra_pin_list[:]
    visited: set[str] = set()
    while queue:
        cur = queue.pop(0)
        key = f"{cur.project_id}:{cur.version_id}"
        if key in visited:
            continue
        visited.add(key)
        version_meta = modrinth_version(client, cur.version_id)
        for dep in version_meta.get("dependencies", []):
            dep_type = (dep.get("dependency_type") or "").lower()
            if dep_type not in {"required", "embedded"}:
                continue
            dep_project = dep.get("project_id")
            dep_version = dep.get("version_id")
            if not dep_project:
                continue
            if dep_project in pins:
                continue
            if not dep_version:
                dep_version = get_modrinth_compatible_version_id(client, dep_project, MC_VERSION, LOADER)
                if not dep_version:
                    warnings.append(f"Unable to resolve transitive dependency version for project {dep_project}")
                    continue
            new_pin = VersionPin(
                project_id=dep_project,
                version_id=dep_version,
                origin="transitive_dependency",
                optional=False,
            )
            pins[dep_project] = new_pin
            queue.append(new_pin)

    return pins, warnings


def resolve_fabric_loader_version(client: JsonHttpClient) -> Tuple[str, str]:
    source = "upstream_mrpack"
    try:
        import io

        base_version = modrinth_version(client, BASE_MODRINTH_VERSION_ID)
        primary = select_primary_file(base_version)
        mrpack_url = primary.get("url")
        if not mrpack_url:
            raise RuntimeError("No primary mrpack url in base version")
        raw = client.get_bytes(mrpack_url)
        with zipfile.ZipFile(io.BytesIO(raw), mode="r") as zf:
            with zf.open("modrinth.index.json") as fh:
                index = json.loads(fh.read().decode("utf-8"))
        deps = index.get("dependencies") or {}
        loader_version = str(deps.get("fabric-loader") or "").strip()
        if loader_version:
            return loader_version, source
        return FALLBACK_FABRIC_LOADER_VERSION, "fallback_default"
    except Exception:
        return FALLBACK_FABRIC_LOADER_VERSION, "fallback_default"


def curse_search(client: JsonHttpClient, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = urllib.parse.urlencode(params)
    payload = client.get_json(f"{CURSE_TOOLS_API}/mods/search?{query}")
    return payload.get("data") or []


def curse_mod_files(client: JsonHttpClient, mod_id: int, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = urllib.parse.urlencode(params)
    payload = client.get_json(f"{CURSE_TOOLS_API}/mods/{mod_id}/files?{query}")
    return payload.get("data") or []


def choose_best_curse_file(
    client: JsonHttpClient,
    mod_id: int,
    modrinth_filename: str,
    modrinth_version_number: str,
    project_type: str,
) -> Tuple[Optional[Dict[str, Any]], float]:
    params_list: List[Dict[str, Any]] = []
    if project_type == "mod":
        params_list.append({"gameVersion": MC_VERSION, "modLoaderType": LOADER_TYPE_FABRIC, "pageSize": 50})
        params_list.append({"gameVersion": MC_VERSION, "pageSize": 50})
    else:
        params_list.append({"gameVersion": MC_VERSION, "pageSize": 50})
        params_list.append({"pageSize": 50})

    files: Dict[int, Dict[str, Any]] = {}
    for params in params_list:
        for f in curse_mod_files(client, mod_id, params):
            if isinstance(f, dict) and f.get("id"):
                files[int(f["id"])] = f
        if files:
            break

    if project_type == "mod" and not files:
        return None, -1.0

    target_file_norm = norm(modrinth_filename)
    primary_version = primary_version_token(modrinth_version_number, MC_VERSION)
    best: Optional[Dict[str, Any]] = None
    best_score = -1.0
    for f in files.values():
        fname = str(f.get("fileName") or "")
        fname_norm = norm(fname)
        score = 0.0
        if fname.lower() == modrinth_filename.lower():
            score += 100.0
        score += sim(fname_norm, target_file_norm) * 25.0
        if primary_version:
            if primary_version in fname:
                score += 6.0
            else:
                score -= 8.0
        if norm(MC_VERSION) in fname_norm:
            score += 1.0
        if "fabric" in fname.lower():
            score += 3.0
        if "neoforge" in fname.lower():
            score -= 3.0
        elif "forge" in fname.lower() and "fabric" not in fname.lower():
            score -= 2.0
        if f.get("isAvailable"):
            score += 1.0
        if float(score) > best_score:
            best_score = float(score)
            best = f
    return best, best_score


def resolve_curseforge_for_entry(client: JsonHttpClient, entry: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    m = entry["modrinth"]
    slug = m["slug"]
    name = entry["name"]
    title = m["title"]
    filename = m["file"]["filename"]
    version_number = m["version_number"]
    project_type = m.get("project_type") or "mod"
    class_hint = PROJECT_TYPE_CLASS_HINT.get(project_type)

    candidate_map: Dict[int, Dict[str, Any]] = {}
    preferred_slug = CURSEFORGE_SLUG_OVERRIDES.get(slug, slug)
    query_variants: List[Dict[str, Any]] = [
        {"gameId": 432, "slug": preferred_slug},
    ]
    if preferred_slug != slug:
        query_variants.append({"gameId": 432, "slug": slug})
    query_variants.extend(
        [
            {"gameId": 432, "searchFilter": title, "pageSize": 20},
            {"gameId": 432, "searchFilter": name, "pageSize": 20},
            {"gameId": 432, "searchFilter": slug.replace("-", " "), "pageSize": 20},
        ]
    )

    for q in query_variants:
        try:
            for c in curse_search(client, q):
                cid = c.get("id")
                if cid:
                    candidate_map[int(cid)] = c
        except Exception:
            continue
        if candidate_map and "slug" in q:
            break

    if not candidate_map:
        return None, "no_curseforge_project_candidate"

    best_project: Optional[Dict[str, Any]] = None
    best_file: Optional[Dict[str, Any]] = None
    best_score = -1.0
    for c in candidate_map.values():
        cslug = str(c.get("slug") or "")
        cname = str(c.get("name") or "")
        cclass = c.get("classId")
        score = 0.0
        if cslug == preferred_slug:
            score += 12.0
        if cslug == slug:
            score += 8.0
        score += sim(norm(cslug), norm(preferred_slug)) * 4.0
        score += sim(norm(cname), norm(title or name)) * 3.0
        if class_hint and cclass == class_hint:
            score += 2.0
        file_candidate, file_score = choose_best_curse_file(
            client=client,
            mod_id=int(c["id"]),
            modrinth_filename=filename,
            modrinth_version_number=version_number,
            project_type=project_type,
        )
        if file_candidate is None:
            continue
        score += min(file_score, 15.0)
        if score > best_score:
            best_score = score
            best_project = c
            best_file = file_candidate

    if not best_project or not best_file:
        return None, "no_curseforge_file_candidate"
    if best_score < 8.0:
        return None, f"low_confidence_match_score={best_score:.2f}"
    primary_version = primary_version_token(version_number, MC_VERSION)
    best_file_name = str(best_file.get("fileName") or "")
    if primary_version and primary_version not in best_file_name and best_file_name.lower() != filename.lower():
        return None, "no_version_aligned_file"

    sha1 = ""
    md5 = ""
    for h in best_file.get("hashes") or []:
        algo = h.get("algo")
        value = h.get("value") or ""
        if algo == 1:
            sha1 = value
        elif algo == 2:
            md5 = value

    result = {
        "project_id": int(best_project["id"]),
        "slug": best_project.get("slug") or "",
        "class_id": int(best_project.get("classId") or 0),
        "file_id": int(best_file["id"]),
        "file_name": best_file.get("fileName") or "",
        "display_name": best_file.get("displayName") or "",
        "download_url": best_file.get("downloadUrl") or "",
        "sha1": sha1,
        "md5": md5,
    }
    return result, None


def build_lock_data(client: JsonHttpClient, allow_unresolved: bool) -> Dict[str, Any]:
    pins, warnings = collect_target_pins(client)
    loader_version, loader_source = resolve_fabric_loader_version(client)

    entries: List[Dict[str, Any]] = []
    unresolved: List[Dict[str, Any]] = []

    ordered_pins = sorted(pins.values(), key=lambda p: p.project_id)
    total = len(ordered_pins)
    for idx, pin in enumerate(ordered_pins, start=1):
        version_meta = modrinth_version(client, pin.version_id)
        project_meta = modrinth_project(client, pin.project_id)
        project_slug = project_meta.get("slug") or ""
        if project_slug in INTERSECTION_EXCLUDE_SLUGS:
            warnings.append(f"Excluded by intersection policy: {project_slug}")
            continue
        primary = select_primary_file(version_meta)
        side = infer_side_from_modrinth_project(project_meta)
        if side == "server_only":
            warnings.append(
                f"Excluded server-only project from client pack: {project_meta.get('title') or pin.project_id}"
            )
            continue
        entry = {
            "name": project_meta.get("title") or project_meta.get("name") or pin.project_id,
            "slug": project_meta.get("slug") or pin.project_id,
            "side": side,
            "optional": bool(pin.optional),
            "origin": pin.origin,
            "modrinth": {
                "project_id": pin.project_id,
                "slug": project_meta.get("slug") or "",
                "title": project_meta.get("title") or "",
                "project_type": project_meta.get("project_type") or "mod",
                "version_id": pin.version_id,
                "version_number": version_meta.get("version_number") or "",
                "file": {
                    "filename": primary.get("filename") or "",
                    "url": primary.get("url") or "",
                    "size": int(primary.get("size") or 0),
                    "sha1": (primary.get("hashes") or {}).get("sha1", ""),
                    "sha512": (primary.get("hashes") or {}).get("sha512", ""),
                },
            },
        }
        print(f"[{idx}/{total}] resolve CurseForge: {entry['name']}", flush=True)
        curse, err = resolve_curseforge_for_entry(client, entry)
        if curse is None:
            unresolved.append(
                {
                    "project_id": pin.project_id,
                    "version_id": pin.version_id,
                    "name": entry["name"],
                    "slug": entry["slug"],
                    "reason": err or "unknown",
                }
            )
        else:
            entry["curseforge"] = curse
        entries.append(entry)

    entries.sort(key=lambda x: (x["origin"], x["slug"]))

    if unresolved and not allow_unresolved:
        warnings.append(
            "Unresolved CurseForge mappings present; validation/build will fail until resolved."
        )

    lock = {
        "schema_version": LOCK_SCHEMA_VERSION,
        "generated_at": now_iso(),
        "policy": {
            "intersection_strict": True,
            "mc_version": MC_VERSION,
            "loader": LOADER,
            "base_modrinth_version_id": BASE_MODRINTH_VERSION_ID,
            "fabric_loader_version": loader_version,
            "fabric_loader_version_source": loader_source,
            "java_version": 21,
        },
        "pack": PACK_META,
        "sources": {
            "runbook_client_recommended": str(RUNBOOK_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
            "base_manifest": str(BASE_MANIFEST_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
        },
        "mods": entries,
        "unresolved": unresolved,
        "warnings": warnings,
    }
    return lock


def validate_lock(lock: Dict[str, Any], online: bool, client: Optional[JsonHttpClient] = None) -> List[str]:
    errors: List[str] = []
    if lock.get("schema_version") != LOCK_SCHEMA_VERSION:
        errors.append(f"schema_version must be {LOCK_SCHEMA_VERSION}")
    policy = lock.get("policy") or {}
    if policy.get("mc_version") != MC_VERSION:
        errors.append(f"policy.mc_version must be {MC_VERSION}")
    if policy.get("loader") != LOADER:
        errors.append(f"policy.loader must be {LOADER}")

    mods = lock.get("mods") or []
    if not mods:
        errors.append("mods is empty")

    seen_slug: set[str] = set()
    seen_modrinth_proj: set[str] = set()
    for idx, mod in enumerate(mods):
        ref = f"mods[{idx}]"
        slug = mod.get("slug") or ""
        if not slug:
            errors.append(f"{ref}.slug missing")
        if slug in seen_slug:
            errors.append(f"duplicate slug: {slug}")
        seen_slug.add(slug)

        side = mod.get("side")
        if side not in {"both", "client_only"}:
            errors.append(f"{ref}.side invalid: {side}")

        m = mod.get("modrinth") or {}
        c = mod.get("curseforge") or {}
        proj = m.get("project_id")
        if not proj:
            errors.append(f"{ref}.modrinth.project_id missing")
        if proj in seen_modrinth_proj:
            errors.append(f"duplicate modrinth project_id: {proj}")
        seen_modrinth_proj.add(str(proj))

        if not m.get("version_id"):
            errors.append(f"{ref}.modrinth.version_id missing")
        if not m.get("version_number"):
            errors.append(f"{ref}.modrinth.version_number missing")
        mf = m.get("file") or {}
        for k in ("filename", "url", "sha1", "sha512"):
            if not mf.get(k):
                errors.append(f"{ref}.modrinth.file.{k} missing")

        if not c:
            errors.append(f"{ref}.curseforge missing (intersection strict)")
        else:
            for k in ("project_id", "file_id", "file_name", "download_url", "sha1"):
                if not c.get(k):
                    errors.append(f"{ref}.curseforge.{k} missing")

            ver_token = primary_version_token(str(m.get("version_number") or ""), MC_VERSION)
            file_name = str(c.get("file_name") or "")
            file_norm = norm(file_name)
            if ver_token and ver_token not in file_name and norm(str(mf.get("filename") or "")) != file_norm:
                errors.append(
                    f"{ref} version alignment failed: modrinth={m.get('version_number')} "
                    f"curseforge_file={c.get('file_name')}"
                )

    unresolved = lock.get("unresolved") or []
    if unresolved:
        errors.append(f"unresolved mappings present: {len(unresolved)}")

    if online:
        if client is None:
            client = JsonHttpClient(CACHE_DIR)
        for idx, mod in enumerate(mods):
            ref = f"mods[{idx}]"
            try:
                mv = modrinth_version(client, mod["modrinth"]["version_id"])
                if mv.get("project_id") != mod["modrinth"]["project_id"]:
                    errors.append(f"{ref} modrinth project/version mismatch")
                if (mv.get("version_number") or "") != (mod["modrinth"]["version_number"] or ""):
                    errors.append(f"{ref} modrinth version_number mismatch")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{ref} modrinth online validation failed: {type(exc).__name__}")
            try:
                c = mod["curseforge"]
                cf = client.get_json(f"{CURSE_TOOLS_API}/mods/{c['project_id']}/files/{c['file_id']}")
                data = cf.get("data") or {}
                if int(data.get("modId") or 0) != int(c["project_id"]):
                    errors.append(f"{ref} curseforge mod/file mismatch")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{ref} curseforge online validation failed: {type(exc).__name__}")
    return errors


def write_packwiz_source(lock: Dict[str, Any], out_dir: Path, pack_version: str) -> None:
    ensure_dir(out_dir / "mods")
    mods = lock["mods"]
    file_rows: List[Tuple[str, str]] = []

    for mod in mods:
        slug = slugify(mod["slug"])
        path = out_dir / "mods" / f"{slug}.pw.toml"
        m = mod["modrinth"]
        c = mod["curseforge"]
        side = "client" if mod["side"] == "client_only" else "both"
        content = "\n".join(
            [
                f"name = {toml_str(mod['name'])}",
                f"filename = {toml_str(m['file']['filename'])}",
                f"side = {toml_str(side)}",
                "",
                "[download]",
                f"url = {toml_str(m['file']['url'])}",
                'hash-format = "sha512"',
                f"hash = {toml_str(m['file']['sha512'])}",
                "",
                "[update.modrinth]",
                f"mod-id = {toml_str(m['project_id'])}",
                f"version = {toml_str(m['version_id'])}",
                "",
                "[update.curseforge]",
                f"project-id = {int(c['project_id'])}",
                f"file-id = {int(c['file_id'])}",
                "",
            ]
        )
        data = content.encode("utf-8")
        path.write_bytes(data)
        rel = path.relative_to(out_dir).as_posix()
        file_rows.append((rel, sha256_hex(data)))

    index_lines: List[str] = ['hash-format = "sha256"', ""]
    for rel, h in sorted(file_rows, key=lambda x: x[0]):
        index_lines.extend(
            [
                "[[files]]",
                f"file = {toml_str(rel)}",
                f"hash = {toml_str(h)}",
                "metafile = true",
                "",
            ]
        )
    index_data = "\n".join(index_lines).encode("utf-8")
    (out_dir / "index.toml").write_bytes(index_data)
    index_hash = sha256_hex(index_data)

    policy = lock["policy"]
    pack = lock["pack"]
    pack_toml = "\n".join(
        [
            f"name = {toml_str(pack['name'])}",
            f"author = {toml_str(pack['author'])}",
            f"version = {toml_str(pack_version)}",
            'pack-format = "packwiz:1.1.0"',
            "",
            "[index]",
            'file = "index.toml"',
            'hash-format = "sha256"',
            f"hash = {toml_str(index_hash)}",
            "",
            "[versions]",
            f"minecraft = {toml_str(policy['mc_version'])}",
            f"fabric = {toml_str(policy['fabric_loader_version'])}",
            "",
        ]
    )
    (out_dir / "pack.toml").write_text(pack_toml, encoding="utf-8")


def copy_overrides(src: Path, zipf: zipfile.ZipFile, prefix: str) -> None:
    if not src.exists():
        return
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src).as_posix()
        arc = f"{prefix}/{rel}"
        zipf.write(path, arcname=arc)


def build_modrinth_mrpack(lock: Dict[str, Any], out_path: Path, pack_version: str) -> None:
    ensure_dir(out_path.parent)
    policy = lock["policy"]
    files: List[Dict[str, Any]] = []
    for mod in lock["mods"]:
        m = mod["modrinth"]
        files.append(
            {
                "path": f"mods/{m['file']['filename']}",
                "hashes": {"sha1": m["file"]["sha1"], "sha512": m["file"]["sha512"]},
                "downloads": [m["file"]["url"]],
                "fileSize": int(m["file"]["size"]),
                "env": {
                    "client": "required",
                    "server": "unsupported" if mod["side"] == "client_only" else "optional",
                },
            }
        )
    index_payload = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": pack_version,
        "name": lock["pack"]["name"],
        "summary": lock["pack"]["summary_en"],
        "files": sorted(files, key=lambda x: x["path"]),
        "dependencies": {
            "minecraft": policy["mc_version"],
            "fabric-loader": policy["fabric_loader_version"],
        },
    }
    index_bytes = json.dumps(index_payload, ensure_ascii=False, indent=2).encode("utf-8")
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("modrinth.index.json", index_bytes)
        copy_overrides(OVERRIDES_DIR, zf, "overrides")


def build_curseforge_zip(lock: Dict[str, Any], out_path: Path, pack_version: str) -> None:
    ensure_dir(out_path.parent)
    policy = lock["policy"]
    files = []
    for mod in lock["mods"]:
        cf = mod["curseforge"]
        files.append(
            {
                "projectID": int(cf["project_id"]),
                "fileID": int(cf["file_id"]),
                "required": not bool(mod.get("optional")),
            }
        )
    manifest = {
        "minecraft": {
            "version": policy["mc_version"],
            "modLoaders": [{"id": f"fabric-{policy['fabric_loader_version']}", "primary": True}],
        },
        "manifestType": "minecraftModpack",
        "manifestVersion": 1,
        "name": lock["pack"]["name"],
        "version": pack_version,
        "author": lock["pack"]["author"],
        "files": sorted(files, key=lambda x: (x["projectID"], x["fileID"])),
        "overrides": "overrides",
    }
    manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", manifest_bytes)
        copy_overrides(OVERRIDES_DIR, zf, "overrides")


def generate_changelog(lock: Dict[str, Any], version: str, out_path: Path) -> None:
    ensure_dir(out_path.parent)
    mods = lock["mods"]
    base_count = sum(1 for m in mods if m["origin"] == "base_official")
    extra_count = sum(1 for m in mods if m["origin"] == "recommended_extra")
    transitive_count = sum(1 for m in mods if m["origin"] == "transitive_dependency")
    today = dt.datetime.now().date().isoformat()
    content = "\n".join(
        [
            f"# {lock['pack']['name']} {version}",
            "",
            f"Date: {today}",
            "",
            "## FR",
            f"- Publication publique de la version `{version}`.",
            f"- Cible: Minecraft `{lock['policy']['mc_version']}` + Fabric `{lock['policy']['fabric_loader_version']}`.",
            f"- Catalogue verrouille: `{len(mods)}` composants ({base_count} base Cobblemon, {extra_count} ajouts recommandes, {transitive_count} dependances).",
            "- Export double plateforme: `.mrpack` (Modrinth) + `.zip` CurseForge (`manifest.json`).",
            "",
            "## EN (Short)",
            f"- Public release `{version}`.",
            f"- Target: Minecraft `{lock['policy']['mc_version']}` + Fabric `{lock['policy']['fabric_loader_version']}`.",
            f"- Locked catalog: `{len(mods)}` components.",
            "- Dual export: Modrinth `.mrpack` + CurseForge `.zip` with `manifest.json`.",
            "",
        ]
    )
    out_path.write_text(content, encoding="utf-8")


def generate_publish_checklist(lock: Dict[str, Any], version: str, out_path: Path) -> None:
    ensure_dir(out_path.parent)
    pack = lock["pack"]
    content = "\n".join(
        [
            f"# Publish Checklist - {pack['name']} {version}",
            "",
            "## Pre-upload",
            "- [ ] `./modpack/release.ps1 validate` passe sans erreur.",
            f"- [ ] Artefacts presents sous `dist/{version}/modrinth/` et `dist/{version}/curseforge/`.",
            f"- [ ] Changelog present: `dist/{version}/notes/changelog.fr-en.md`.",
            "- [ ] Branding minimal v1 pret: 1 icone + 1 capture.",
            "",
            "## Modrinth",
            "- [ ] Ouvrir le projet public (nouvelle identite serveur).",
            "- [ ] Uploader le fichier `.mrpack` genere.",
            "- [ ] Renseigner version Minecraft `1.21.1`, loader `Fabric`, type `release`.",
            "- [ ] Coller le changelog FR + resume EN.",
            "- [ ] Publier.",
            "",
            "## CurseForge",
            "- [ ] Ouvrir le projet public correspondant (meme branding/version).",
            "- [ ] Uploader le `.zip` contenant `manifest.json`.",
            "- [ ] Verifier categorie `Modpacks`, version Minecraft `1.21.1`, loader `Fabric`.",
            "- [ ] Coller le meme changelog FR + resume EN.",
            "- [ ] Publier.",
            "",
            "## Post-publish",
            "- [ ] Verifier installation launcher Modrinth (import `.mrpack`).",
            "- [ ] Verifier installation launcher CurseForge/Prism (import `.zip`).",
            "- [ ] Verifier connexion au serveur sans `version mismatch`.",
            "- [ ] Archiver les URLs de publication dans le journal de release.",
            "",
        ]
    )
    out_path.write_text(content, encoding="utf-8")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_release_metadata(
    lock: Dict[str, Any],
    version: str,
    mrpack_path: Path,
    curseforge_zip_path: Path,
    out_path: Path,
) -> None:
    ensure_dir(out_path.parent)
    warnings = lock.get("warnings") or []
    excluded = [w for w in warnings if w.startswith("Excluded")]
    lines = [
        f"# Release Metadata - {lock['pack']['name']} {version}",
        "",
        "## Pack",
        f"- Name: `{lock['pack']['name']}`",
        f"- Slug: `{lock['pack']['slug']}`",
        f"- Version: `{version}`",
        f"- Minecraft: `{lock['policy']['mc_version']}`",
        f"- Loader: `Fabric {lock['policy']['fabric_loader_version']}`",
        f"- Locked mods count: `{len(lock.get('mods') or [])}`",
        "",
        "## Artifacts",
        f"- Modrinth file: `{mrpack_path.name}`",
        f"- Modrinth SHA256: `{file_sha256(mrpack_path)}`",
        f"- CurseForge file: `{curseforge_zip_path.name}`",
        f"- CurseForge SHA256: `{file_sha256(curseforge_zip_path)}`",
        "",
        "## Notes",
        "- Visibility target: `Public`",
        "- Release mode: `Manual guided upload`",
        "- Language: `FR primary + short EN`",
        "",
        "## Intersection Exclusions",
    ]
    if excluded:
        lines.extend([f"- {w}" for w in excluded])
    else:
        lines.append("- none")
    lines.append("")
    content = "\n".join(lines)
    out_path.write_text(content, encoding="utf-8")


def docker_packwiz_available() -> bool:
    try:
        proc = subprocess.run(
            ["docker", "info"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return proc.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def cmd_sync_lock(args: argparse.Namespace) -> int:
    client = JsonHttpClient(CACHE_DIR)
    lock = build_lock_data(client=client, allow_unresolved=args.allow_unresolved)
    write_json(LOCK_PATH, lock)
    if lock.get("unresolved"):
        print(f"Wrote lock with unresolved entries: {len(lock['unresolved'])}")
        for item in lock["unresolved"][:20]:
            print(f" - {item['name']}: {item['reason']}")
    else:
        print(f"Wrote lock with {len(lock['mods'])} fully resolved entries: {LOCK_PATH}")

    if not lock.get("unresolved"):
        if PACKWIZ_DIR.exists():
            shutil.rmtree(PACKWIZ_DIR)
        ensure_dir(PACKWIZ_DIR)
        write_packwiz_source(lock=lock, out_dir=PACKWIZ_DIR, pack_version="0.0.0-dev")
        print(f"Updated packwiz source: {PACKWIZ_DIR}")
    elif not args.allow_unresolved:
        return 2
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    lock = read_json(LOCK_PATH)
    client = JsonHttpClient(CACHE_DIR) if args.online else None
    errors = validate_lock(lock=lock, online=args.online, client=client)
    if errors:
        print("Validation failed:")
        for e in errors:
            print(f" - {e}")
        return 2
    print(f"Validation OK: {len(lock.get('mods') or [])} mods")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    version = args.version.strip()
    if not semver_ok(version):
        print(f"Invalid semver: {version}")
        return 2
    lock = read_json(LOCK_PATH)
    client = JsonHttpClient(CACHE_DIR)
    errors = validate_lock(lock=lock, online=not args.offline, client=client)
    if errors:
        print("Build blocked by validation errors:")
        for e in errors:
            print(f" - {e}")
        return 2

    dist_root = DIST_DIR / version
    modrinth_dir = dist_root / "modrinth"
    curseforge_dir = dist_root / "curseforge"
    notes_dir = dist_root / "notes"
    packwiz_dist_dir = dist_root / "packwiz-source"

    if dist_root.exists() and not args.force:
        print(f"Refusing to overwrite existing dist folder without --force: {dist_root}")
        return 2
    if dist_root.exists():
        shutil.rmtree(dist_root)
    ensure_dir(modrinth_dir)
    ensure_dir(curseforge_dir)
    ensure_dir(notes_dir)
    ensure_dir(packwiz_dist_dir)

    write_packwiz_source(lock=lock, out_dir=packwiz_dist_dir, pack_version=version)
    if PACKWIZ_DIR.exists():
        shutil.rmtree(PACKWIZ_DIR)
    shutil.copytree(packwiz_dist_dir, PACKWIZ_DIR)

    mrpack_name = f"{lock['pack']['slug']}-{version}.mrpack"
    cf_name = f"{lock['pack']['slug']}-{version}-curseforge.zip"
    mrpack_path = modrinth_dir / mrpack_name
    curseforge_zip_path = curseforge_dir / cf_name
    build_modrinth_mrpack(lock=lock, out_path=mrpack_path, pack_version=version)
    build_curseforge_zip(lock=lock, out_path=curseforge_zip_path, pack_version=version)
    generate_changelog(lock=lock, version=version, out_path=notes_dir / "changelog.fr-en.md")
    generate_publish_checklist(lock=lock, version=version, out_path=notes_dir / "publish-checklist.md")
    generate_release_metadata(
        lock=lock,
        version=version,
        mrpack_path=mrpack_path,
        curseforge_zip_path=curseforge_zip_path,
        out_path=notes_dir / "release-metadata.md",
    )

    if docker_packwiz_available():
        print("Docker engine detected: packwiz Docker workflow can be used for local verification.")
    else:
        print("Docker engine unavailable: artifacts built with internal exporter, packwiz source still generated.")

    print("Build complete:")
    print(f" - {modrinth_dir / mrpack_name}")
    print(f" - {curseforge_dir / cf_name}")
    print(f" - {notes_dir / 'changelog.fr-en.md'}")
    return 0


def cmd_publish_checklist(args: argparse.Namespace) -> int:
    version = args.version.strip()
    if not semver_ok(version):
        print(f"Invalid semver: {version}")
        return 2
    lock = read_json(LOCK_PATH)
    notes_dir = DIST_DIR / version / "notes"
    out_path = notes_dir / "publish-checklist.md"
    generate_publish_checklist(lock=lock, version=version, out_path=out_path)
    print(f"Wrote publish checklist: {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Modpack release utility")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sync = sub.add_parser("sync-lock", help="Generate/refresh catalog.lock.json from pinned sources")
    p_sync.add_argument("--allow-unresolved", action="store_true", help="Write lock even if CurseForge mapping is incomplete")
    p_sync.set_defaults(func=cmd_sync_lock)

    p_val = sub.add_parser("validate", help="Validate lock integrity and cross-platform strict policy")
    p_val.add_argument("--online", action="store_true", help="Validate against live APIs (Modrinth + Curse tools)")
    p_val.set_defaults(func=cmd_validate)

    p_build = sub.add_parser("build", help="Build dist artifacts for both platforms")
    p_build.add_argument("--version", required=True, help="SemVer release version")
    p_build.add_argument("--offline", action="store_true", help="Skip online API validation")
    p_build.add_argument("--force", action="store_true", help="Overwrite existing dist/<version>")
    p_build.set_defaults(func=cmd_build)

    p_pub = sub.add_parser("publish-checklist", help="Generate publication checklist markdown")
    p_pub.add_argument("--version", required=True, help="SemVer release version")
    p_pub.set_defaults(func=cmd_publish_checklist)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("Interrupted")
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
