#!/usr/bin/env python3
"""
Backfill Waystones into already-generated villages on an existing world.

V1 scope:
- Offline scan of village structure starts from Anvil region chunk NBT.
- Online placement batch via ./infra/mc.sh (forceload + setblock + verification).
- JSONL journal for resume/idempotence.

This avoids direct chunk editing for Waystones block entities and now uses
the native Waystones placement command for proper registration + naming.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import re
import struct
import subprocess
import sys
import time
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12

VILLAGE_PREFIX = "minecraft:village_"
DEFAULT_PLACE_BLOCK = "waystones:waystone"


class NBTError(Exception):
    pass


class _Buf:
    __slots__ = ("b", "o")

    def __init__(self, b: bytes):
        self.b = b
        self.o = 0

    def read_u8(self) -> int:
        if self.o + 1 > len(self.b):
            raise NBTError("unexpected EOF")
        v = self.b[self.o]
        self.o += 1
        return v

    def read_i8(self) -> int:
        if self.o + 1 > len(self.b):
            raise NBTError("unexpected EOF")
        v = struct.unpack(">b", self.b[self.o : self.o + 1])[0]
        self.o += 1
        return v

    def read_i16(self) -> int:
        if self.o + 2 > len(self.b):
            raise NBTError("unexpected EOF")
        v = struct.unpack(">h", self.b[self.o : self.o + 2])[0]
        self.o += 2
        return v

    def read_i32(self) -> int:
        if self.o + 4 > len(self.b):
            raise NBTError("unexpected EOF")
        v = struct.unpack(">i", self.b[self.o : self.o + 4])[0]
        self.o += 4
        return v

    def read_i64(self) -> int:
        if self.o + 8 > len(self.b):
            raise NBTError("unexpected EOF")
        v = struct.unpack(">q", self.b[self.o : self.o + 8])[0]
        self.o += 8
        return v

    def read_bytes(self, n: int) -> bytes:
        if self.o + n > len(self.b):
            raise NBTError("unexpected EOF")
        v = self.b[self.o : self.o + n]
        self.o += n
        return v

    def read_string(self) -> str:
        ln = self.read_i16()
        if ln < 0:
            raise NBTError("negative string length")
        return self.read_bytes(ln).decode("utf-8", errors="strict")


def _read_payload(tag: int, buf: _Buf):
    if tag == TAG_BYTE:
        return buf.read_i8()
    if tag == TAG_SHORT:
        return buf.read_i16()
    if tag == TAG_INT:
        return buf.read_i32()
    if tag == TAG_LONG:
        return buf.read_i64()
    if tag == TAG_FLOAT:
        buf.read_bytes(4)
        return None
    if tag == TAG_DOUBLE:
        buf.read_bytes(8)
        return None
    if tag == TAG_BYTE_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative byte array length")
        return buf.read_bytes(ln)
    if tag == TAG_STRING:
        return buf.read_string()
    if tag == TAG_LIST:
        inner = buf.read_u8()
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative list length")
        return [_read_payload(inner, buf) for _ in range(ln)]
    if tag == TAG_COMPOUND:
        out = {}
        while True:
            t = buf.read_u8()
            if t == TAG_END:
                return out
            name = buf.read_string()
            out[name] = _read_payload(t, buf)
    if tag == TAG_INT_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative int array length")
        return [struct.unpack(">i", buf.read_bytes(4))[0] for _ in range(ln)]
    if tag == TAG_LONG_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative long array length")
        return [struct.unpack(">q", buf.read_bytes(8))[0] for _ in range(ln)]
    raise NBTError(f"unknown tag {tag}")


def _load_nbt(raw: bytes) -> Dict:
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    buf = _Buf(raw)
    t = buf.read_u8()
    if t != TAG_COMPOUND:
        raise NBTError(f"root is not compound (tag={t})")
    _ = buf.read_string()
    root = _read_payload(TAG_COMPOUND, buf)
    if not isinstance(root, dict):
        raise NBTError("invalid root")
    return root


def _read_chunk_raw(region_path: Path, local_x: int, local_z: int) -> Optional[bytes]:
    b = region_path.read_bytes()
    if len(b) < 8192:
        return None
    idx = local_x + local_z * 32
    loc = struct.unpack(">I", b[idx * 4 : idx * 4 + 4])[0]
    off_sectors = (loc >> 8) & 0xFFFFFF
    sector_count = loc & 0xFF
    if off_sectors == 0 or sector_count == 0:
        return None
    off = off_sectors * 4096
    if off + 5 > len(b):
        return None
    length = struct.unpack(">I", b[off : off + 4])[0]
    compression = b[off + 4]
    payload = b[off + 5 : off + 4 + length]
    if compression == 1:
        return gzip.decompress(payload)
    if compression == 2:
        return zlib.decompress(payload)
    if compression == 3:
        return payload
    return None


def _iter_region_files(region_dir: Path) -> Iterator[Path]:
    for p in sorted(region_dir.glob("r.*.*.mca")):
        if p.is_file():
            yield p


def _chunk_coords_from_root(root: Dict, fallback_cx: int, fallback_cz: int) -> Tuple[int, int]:
    x = root.get("xPos")
    z = root.get("zPos")
    if isinstance(x, int) and isinstance(z, int):
        return int(x), int(z)
    lvl = root.get("Level")
    if isinstance(lvl, dict):
        x = lvl.get("xPos")
        z = lvl.get("zPos")
        if isinstance(x, int) and isinstance(z, int):
            return int(x), int(z)
    return fallback_cx, fallback_cz


def _structures_starts_from_root(root: Dict) -> Dict[str, Dict]:
    candidates = []
    for k in ("structures", "Structures"):
        v = root.get(k)
        if isinstance(v, dict):
            candidates.append(v)
    lvl = root.get("Level")
    if isinstance(lvl, dict):
        for k in ("structures", "Structures"):
            v = lvl.get(k)
            if isinstance(v, dict):
                candidates.append(v)
    for s in candidates:
        starts = s.get("starts")
        if not isinstance(starts, dict):
            starts = s.get("Starts")
        if isinstance(starts, dict):
            return {k: v for k, v in starts.items() if isinstance(k, str) and isinstance(v, dict)}
    return {}


def _parse_bbox(struct_start: Dict) -> Optional[Tuple[int, int, int, int, int, int]]:
    bb = struct_start.get("BB")
    if not isinstance(bb, list):
        bb = struct_start.get("bb")
    if isinstance(bb, list) and len(bb) >= 6 and all(isinstance(v, int) for v in bb[:6]):
        x1, y1, z1, x2, y2, z2 = [int(v) for v in bb[:6]]
        return (min(x1, x2), min(y1, y2), min(z1, z2), max(x1, x2), max(y1, y2), max(z1, z2))
    return None


@dataclass
class Village:
    village_id: str
    structure_type: str
    start_cx: int
    start_cz: int
    center_x: int
    center_z: int
    bbox: Optional[Tuple[int, int, int, int, int, int]]
    source_chunk_cx: int
    source_chunk_cz: int

    def to_dict(self) -> Dict:
        out = {
            "village_id": self.village_id,
            "structure_type": self.structure_type,
            "start_chunk": {"cx": self.start_cx, "cz": self.start_cz},
            "approx_center": {"x": self.center_x, "z": self.center_z},
            "source_chunk": {"cx": self.source_chunk_cx, "cz": self.source_chunk_cz},
        }
        if self.bbox is not None:
            x1, y1, z1, x2, y2, z2 = self.bbox
            out["bbox"] = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
        return out


def scan_villages(world_dir: Path, *, verbose: bool = False) -> List[Village]:
    region_dir = world_dir / "region"
    if not region_dir.exists():
        raise FileNotFoundError(f"missing region dir: {region_dir}")
    out: Dict[str, Village] = {}
    regions = chunks = 0
    for region_path in _iter_region_files(region_dir):
        regions += 1
        m = re.match(r"r\.(-?\d+)\.(-?\d+)\.mca$", region_path.name)
        if not m:
            continue
        rx, rz = int(m.group(1)), int(m.group(2))
        for lz in range(32):
            for lx in range(32):
                raw = _read_chunk_raw(region_path, lx, lz)
                if raw is None:
                    continue
                chunks += 1
                cx = (rx << 5) + lx
                cz = (rz << 5) + lz
                try:
                    root = _load_nbt(raw)
                except Exception:
                    continue
                chunk_cx, chunk_cz = _chunk_coords_from_root(root, cx, cz)
                starts = _structures_starts_from_root(root)
                for key, start in starts.items():
                    sid = start.get("id")
                    if not isinstance(sid, str):
                        sid = start.get("ID")
                    if not isinstance(sid, str):
                        sid = key
                    sid_s = sid.strip()
                    if not sid_s:
                        continue
                    if sid_s.upper() in {"INVALID", "INVALID_START"}:
                        continue
                    structure_type = sid_s if sid_s.startswith("minecraft:") else key
                    if not (structure_type.lower().startswith(VILLAGE_PREFIX) or key.lower().startswith(VILLAGE_PREFIX)):
                        continue
                    if not structure_type.lower().startswith(VILLAGE_PREFIX):
                        structure_type = key
                    sx = start.get("ChunkX")
                    sz = start.get("ChunkZ")
                    if not isinstance(sx, int):
                        sx = start.get("chunkX")
                    if not isinstance(sz, int):
                        sz = start.get("chunkZ")
                    start_cx = int(sx) if isinstance(sx, int) else chunk_cx
                    start_cz = int(sz) if isinstance(sz, int) else chunk_cz
                    bbox = _parse_bbox(start)
                    if bbox is not None:
                        center_x = (bbox[0] + bbox[3]) // 2
                        center_z = (bbox[2] + bbox[5]) // 2
                    else:
                        center_x = (start_cx << 4) + 8
                        center_z = (start_cz << 4) + 8
                    village_id = f"{structure_type}@{start_cx},{start_cz}"
                    prev = out.get(village_id)
                    v = Village(
                        village_id=village_id,
                        structure_type=structure_type,
                        start_cx=start_cx,
                        start_cz=start_cz,
                        center_x=center_x,
                        center_z=center_z,
                        bbox=bbox,
                        source_chunk_cx=chunk_cx,
                        source_chunk_cz=chunk_cz,
                    )
                    if prev is None or (prev.bbox is None and bbox is not None):
                        out[village_id] = v
        if verbose and regions % 10 == 0:
            print(f"[scan] regions={regions} chunks={chunks} villages={len(out)}", file=sys.stderr)
    villages = list(out.values())
    villages.sort(key=lambda v: (v.structure_type, v.start_cx, v.start_cz))
    return villages


def read_spawn(world_dir: Path) -> Tuple[int, int, int]:
    level_dat = world_dir / "level.dat"
    root = _load_nbt(level_dat.read_bytes())
    data = root.get("Data")
    if not isinstance(data, dict):
        raise NBTError("missing Data in level.dat")
    sx = data.get("SpawnX")
    sy = data.get("SpawnY")
    sz = data.get("SpawnZ")
    if not all(isinstance(v, int) for v in (sx, sy, sz)):
        raise NBTError("invalid spawn fields")
    return int(sx), int(sy), int(sz)


def _distance_xz(x1: int, z1: int, x2: int, z2: int) -> float:
    dx = x1 - x2
    dz = z1 - z2
    return math.sqrt(dx * dx + dz * dz)


def _spiral_offsets(max_radius: int) -> Iterable[Tuple[int, int]]:
    yield (0, 0)
    for r in range(1, max_radius + 1):
        x, z = -r, -r
        for _ in range(2 * r):
            yield (x, z)
            x += 1
        for _ in range(2 * r):
            yield (x, z)
            z += 1
        for _ in range(2 * r):
            yield (x, z)
            x -= 1
        for _ in range(2 * r):
            yield (x, z)
            z -= 1


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_token(s: str) -> str:
    s = s.replace("minecraft:", "").replace("@", "_").replace(",", "_")
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", s)
    return s[:80]


def _waystone_style_from_block(place_block: str) -> Optional[str]:
    if ":" not in place_block:
        return None
    ns, block = place_block.split(":", 1)
    if ns != "waystones":
        return None
    allowed = {
        "waystone",
        "mossy_waystone",
        "sandy_waystone",
        "blackstone_waystone",
        "deepslate_waystone",
        "end_stone_waystone",
    }
    return block if block in allowed else None


def _village_biome_label(structure_type: str) -> str:
    st = structure_type.lower()
    if "village_plains" in st:
        return "Plains"
    if "village_savanna" in st:
        return "Savanna"
    if "village_snowy" in st:
        return "Snowy"
    if "village_taiga" in st:
        return "Taiga"
    if "village_desert" in st:
        return "Desert"
    return "Village"


def _assign_waystone_names(villages: List[Village]) -> Dict[str, str]:
    counts: Dict[str, int] = {}
    out: Dict[str, str] = {}
    for v in villages:
        biome = _village_biome_label(v.structure_type)
        counts[biome] = counts.get(biome, 0) + 1
        out[v.village_id] = f"Village {biome} {counts[biome]:02d}"
    return out


def _journal_load(path: Path) -> Dict[str, List[Dict]]:
    if not path.exists():
        return {}
    out: Dict[str, List[Dict]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict) and isinstance(row.get("village_id"), str):
            out.setdefault(row["village_id"], []).append(row)
    return out


def _journal_append(path: Path, row: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


class MC:
    def __init__(self, repo_root: Path, *, verbose: bool = False):
        self.repo_root = repo_root
        self.verbose = verbose

    def send(self, cmd: str) -> None:
        if self.verbose:
            print(f"[mc] {cmd}", file=sys.stderr)
        subprocess.run(
            ["./infra/mc.sh", cmd],
            cwd=str(self.repo_root),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

    def logs_tail(self, n: int = 1200) -> str:
        p = subprocess.run(
            ["docker", "logs", "cobblemon", "--tail", str(n)],
            cwd=str(self.repo_root),
            check=False,
            capture_output=True,
            text=True,
        )
        return (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")

    def wait_marker(self, marker: str, *, retries: int = 6, delay: float = 0.35) -> bool:
        for _ in range(retries):
            time.sleep(delay)
            if marker in self.logs_tail():
                return True
        return False

    def say_if(self, condition_cmd: str, marker: str) -> bool:
        self.send(f"{condition_cmd} run say {marker}")
        return self.wait_marker(marker)


class HeightResolver:
    def __init__(self, repo_root: Path, world_dir: Path, *, min_y: int, hm_type: str, verbose: bool = False):
        self.repo_root = repo_root
        self.world_dir = world_dir
        self.min_y = min_y
        self.hm_type = hm_type
        self.verbose = verbose
        self._cache: Dict[Tuple[int, int], Optional[int]] = {}

    def get(self, x: int, z: int) -> Optional[int]:
        k = (x, z)
        if k in self._cache:
            return self._cache[k]
        cmd = [
            sys.executable,
            str((self.repo_root / "infra" / "world-height-at.py").resolve()),
            "--world",
            str(self.world_dir),
            "--x",
            str(x),
            "--z",
            str(z),
            "--min-y",
            str(self.min_y),
            "--type",
            self.hm_type,
        ]
        p = subprocess.run(cmd, cwd=str(self.repo_root), check=False, capture_output=True, text=True)
        if p.returncode != 0:
            if self.verbose:
                print(f"[height] miss ({x},{z}): {(p.stderr or '').strip()}", file=sys.stderr)
            self._cache[k] = None
            return None
        try:
            y = int((p.stdout or "").strip())
        except Exception:
            self._cache[k] = None
            return None
        self._cache[k] = y
        return y


def _forceload_bounds(cx: int, cz: int, margin_blocks: int = 48) -> Tuple[int, int, int, int]:
    return (cx - margin_blocks, cz - margin_blocks, cx + margin_blocks, cz + margin_blocks)


def _find_spot_online(
    mc: MC,
    heights: HeightResolver,
    *,
    center_x: int,
    center_z: int,
    primary_radius: int,
    fallback_radius: int,
    place_block: str,
    force: bool,
    village_token: str,
) -> Optional[Tuple[int, int, int]]:
    max_r = fallback_radius
    for dx, dz in _spiral_offsets(max_r):
        r = max(abs(dx), abs(dz))
        if r > fallback_radius:
            continue
        x = center_x + dx
        z = center_z + dz
        surface_y = heights.get(x, z)
        if surface_y is None:
            continue
        y = surface_y + 1
        if r > primary_radius and r <= fallback_radius:
            pass
        # First skip if a waystone is already exactly there.
        marker_existing = f"WB_EXIST_{village_token}_{x}_{y}_{z}"
        if mc.say_if(
            f"execute in minecraft:overworld if block {x} {y} {z} {place_block}",
            marker_existing,
        ):
            return (x, y, z)
        if force:
            marker_ok = f"WB_OKF_{village_token}_{x}_{y}_{z}"
            if mc.say_if(
                f"execute in minecraft:overworld if block {x} {y+1} {z} minecraft:air "
                f"unless block {x} {y-1} {z} minecraft:air "
                f"unless block {x} {y-1} {z} minecraft:water "
                f"unless block {x} {y-1} {z} minecraft:lava",
                marker_ok,
            ):
                return (x, y, z)
        else:
            marker_ok = f"WB_OK_{village_token}_{x}_{y}_{z}"
            if mc.say_if(
                f"execute in minecraft:overworld if block {x} {y} {z} minecraft:air "
                f"if block {x} {y+1} {z} minecraft:air "
                f"unless block {x} {y-1} {z} minecraft:air "
                f"unless block {x} {y-1} {z} minecraft:water "
                f"unless block {x} {y-1} {z} minecraft:lava",
                marker_ok,
            ):
                return (x, y, z)
    return None


def _place_and_verify(
    mc: MC,
    *,
    x: int,
    y: int,
    z: int,
    place_block: str,
    force: bool,
    token: str,
    waystone_name: str,
) -> bool:
    style = _waystone_style_from_block(place_block)
    if style is not None:
        # Use native Waystones placement to register a real named waystone.
        if force:
            mc.send(f"setblock {x} {y+1} {z} minecraft:air replace")
            mc.send(f"setblock {x} {y} {z} minecraft:air replace")
        mc.send(f"waystones place {x} {y} {z} {style} {waystone_name}")
    else:
        # Fallback for non-waystones blocks (kept for script flexibility).
        if force:
            mc.send(f"execute in minecraft:overworld run setblock {x} {y} {z} {place_block} replace")
        else:
            mc.send(
                f"execute in minecraft:overworld if block {x} {y} {z} minecraft:air "
                f"if block {x} {y+1} {z} minecraft:air run setblock {x} {y} {z} {place_block}"
            )

    marker = f"WB_DONE_{token}_{x}_{y}_{z}"
    if not mc.say_if(f"execute in minecraft:overworld if block {x} {y} {z} {place_block}", marker):
        return False
    top_marker = f"WB_TOP_{token}_{x}_{y+1}_{z}"
    return mc.say_if(
        f"execute in minecraft:overworld if block {x} {y+1} {z} {place_block}[half=upper]",
        top_marker,
    )


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Backfill Waystones into already-generated villages.")
    ap.add_argument("--world", default="./data/world", help="World directory (default: ./data/world)")
    ap.add_argument("--dimension", default="overworld", choices=["overworld"], help="Dimension (v1: overworld only)")
    ap.add_argument("--execute", action="store_true", help="Execute placement via ./infra/mc.sh")
    ap.add_argument("--scan-only", action="store_true", help="Scan/plan only")
    ap.add_argument("--dry-run", action="store_true", help="Alias for --scan-only")
    ap.add_argument("--out", default=None, help="Write JSON report")
    ap.add_argument("--journal", default="./logs/waystones-backfill.jsonl", help="JSONL journal path")
    ap.add_argument("--resume", action="store_true", help="Skip villages already marked placed in journal")
    ap.add_argument("--offset", type=int, default=0, help="Skip first N filtered villages")
    ap.add_argument("--limit", type=int, default=None, help="Process at most N villages")
    ap.add_argument("--min-distance-spawn", type=int, default=0, help="Skip villages closer than N blocks to spawn")
    ap.add_argument("--min-y", type=int, default=-64, help="World min Y for heightmap decode")
    ap.add_argument("--heightmap-type", default="MOTION_BLOCKING_NO_LEAVES", help="Heightmap type for Y placement")
    ap.add_argument("--search-radius-primary", type=int, default=8, help="Primary spot search radius")
    ap.add_argument("--search-radius-fallback", type=int, default=16, help="Fallback spot search radius")
    ap.add_argument("--place-block", default=DEFAULT_PLACE_BLOCK, help=f"Block to place (default: {DEFAULT_PLACE_BLOCK})")
    ap.add_argument("--force", action="store_true", help="Allow target overwrite (still requires air above)")
    ap.add_argument("--verbose", action="store_true", help="Verbose logging to stderr")
    args = ap.parse_args(list(argv))
    if args.scan_only or args.dry_run:
        args.execute = False
    if args.offset < 0:
        ap.error("--offset must be >= 0")
    if args.limit is not None and args.limit < 0:
        ap.error("--limit must be >= 0")
    if args.min_distance_spawn < 0:
        ap.error("--min-distance-spawn must be >= 0")
    if args.search_radius_primary < 0 or args.search_radius_fallback < 0:
        ap.error("search radii must be >= 0")
    if args.search_radius_fallback < args.search_radius_primary:
        ap.error("--search-radius-fallback must be >= --search-radius-primary")
    return args


def main(argv: Sequence[str]) -> int:
    args = _parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    world_dir = Path(args.world)
    if not world_dir.is_absolute():
        world_dir = (repo_root / world_dir).resolve()
    if not world_dir.exists():
        print(f"ERROR: world not found: {world_dir}", file=sys.stderr)
        return 2

    spawn: Optional[Tuple[int, int, int]]
    try:
        spawn = read_spawn(world_dir)
    except Exception as e:
        spawn = None
        print(f"WARN: spawn unavailable ({e})", file=sys.stderr)

    villages = scan_villages(world_dir, verbose=args.verbose)
    if spawn is not None and args.min_distance_spawn > 0:
        sx, _sy, sz = spawn
        villages = [
            v
            for v in villages
            if _distance_xz(v.center_x, v.center_z, sx, sz) >= float(args.min_distance_spawn)
        ]
    filtered_villages = list(villages)
    village_names = _assign_waystone_names(filtered_villages)
    if args.offset:
        villages = filtered_villages[args.offset :]
    else:
        villages = filtered_villages
    if args.limit is not None:
        villages = villages[: args.limit]

    print("== Waystones Village Backfill ==")
    print(f"world: {world_dir}")
    print(f"mode: {'execute' if args.execute else 'scan-only'}")
    print(f"villages_selected: {len(villages)}")

    journal_path = Path(args.journal)
    if not journal_path.is_absolute():
        journal_path = (repo_root / journal_path).resolve()
    journal_state = _journal_load(journal_path) if args.resume else {}
    if args.resume:
        print(f"resume_entries: {sum(len(v) for v in journal_state.values())}")

    counts = {
        "placed": 0,
        "placed_already": 0,
        "skipped_resume": 0,
        "skipped_no_spot": 0,
        "failed": 0,
    }
    report_rows: List[Dict] = []

    if args.execute:
        mc = MC(repo_root, verbose=args.verbose)
        heights = HeightResolver(
            repo_root,
            world_dir,
            min_y=args.min_y,
            hm_type=args.heightmap_type,
            verbose=args.verbose,
        )
        for i, v in enumerate(villages, start=1):
            token = _safe_token(v.village_id)
            if args.resume and any(
                row.get("result") in {"placed", "placed_already"} for row in journal_state.get(v.village_id, [])
            ):
                counts["skipped_resume"] += 1
                continue
            if args.verbose:
                print(f"[exec] {i}/{len(villages)} {v.village_id}", file=sys.stderr)
            x1, z1, x2, z2 = _forceload_bounds(v.center_x, v.center_z)
            base = {
                "timestamp": _utc_now_iso(),
                "village_id": v.village_id,
                "structure_type": v.structure_type,
                "center": {"x": v.center_x, "z": v.center_z},
            }
            try:
                mc.send(f"forceload add {x1} {z1} {x2} {z2}")
                time.sleep(0.2)
                spot = _find_spot_online(
                    mc,
                    heights,
                    center_x=v.center_x,
                    center_z=v.center_z,
                    primary_radius=args.search_radius_primary,
                    fallback_radius=args.search_radius_fallback,
                    place_block=args.place_block,
                    force=bool(args.force),
                    village_token=token,
                )
                if spot is None:
                    counts["skipped_no_spot"] += 1
                    row = dict(base)
                    row.update({"result": "skipped", "reason": "no_valid_spot"})
                    _journal_append(journal_path, row)
                    report_rows.append(row)
                    continue
                x, y, z = spot
                waystone_name = village_names.get(v.village_id, "Village")
                if mc.say_if(f"execute in minecraft:overworld if block {x} {y} {z} {args.place_block}", f"WB_ALREADY_{token}_{x}_{y}_{z}"):
                    counts["placed_already"] += 1
                    row = dict(base)
                    row.update({"result": "placed_already", "coords": {"x": x, "y": y, "z": z}, "name": waystone_name})
                    _journal_append(journal_path, row)
                    report_rows.append(row)
                    continue
                ok = _place_and_verify(
                    mc,
                    x=x,
                    y=y,
                    z=z,
                    place_block=args.place_block,
                    force=bool(args.force),
                    token=token,
                    waystone_name=waystone_name,
                )
                if ok:
                    counts["placed"] += 1
                    row = dict(base)
                    row.update({"result": "placed", "coords": {"x": x, "y": y, "z": z}, "name": waystone_name})
                else:
                    counts["failed"] += 1
                    row = dict(base)
                    row.update({"result": "failed", "reason": "verify_failed", "coords": {"x": x, "y": y, "z": z}, "name": waystone_name})
                _journal_append(journal_path, row)
                report_rows.append(row)
            except Exception as e:
                counts["failed"] += 1
                row = dict(base)
                row.update({"result": "failed", "reason": "exception", "error": str(e)[:500]})
                _journal_append(journal_path, row)
                report_rows.append(row)
            finally:
                try:
                    mc.send(f"forceload remove {x1} {z1} {x2} {z2}")
                except Exception:
                    pass
    else:
        for v in villages[:12]:
            print(f"- {v.village_id} center=({v.center_x},{v.center_z})")

    for k, v in counts.items():
        if args.execute:
            print(f"{k}: {v}")

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = (repo_root / out_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": _utc_now_iso(),
            "world": str(world_dir),
            "dimension": args.dimension,
            "mode": "execute" if args.execute else "scan-only",
            "config": {
                "min_y": args.min_y,
                "heightmap_type": args.heightmap_type,
                "search_radius_primary": args.search_radius_primary,
                "search_radius_fallback": args.search_radius_fallback,
                "place_block": args.place_block,
                "force": bool(args.force),
                "resume": bool(args.resume),
                "offset": args.offset,
                "limit": args.limit,
                "min_distance_spawn": args.min_distance_spawn,
            },
            "spawn": {"x": spawn[0], "y": spawn[1], "z": spawn[2]} if spawn else None,
            "summary": {
                "villages_selected": len(villages),
                **counts,
            },
            "villages": [v.to_dict() for v in villages],
            "execution_results": report_rows if args.execute else [],
        }
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print(f"report_written: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
