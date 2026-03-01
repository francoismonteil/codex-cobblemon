#!/usr/bin/env python3
"""Generate a server-side Cobblemon Pokedex comparison report.

Inputs:
- ./data/world/pokedex/<uuid>.nbt
- ./data/world/stats/<uuid>.json
- ./data/usercache.json
- ./data/showdown/data/pokedex.js

Optional:
- post the generated report to a Discord webhook as a file attachment
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import urllib.error
import urllib.request
import uuid as uuid_lib
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Set, Tuple


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


class NBTError(Exception):
    pass


class _Buf:
    __slots__ = ("b", "o")

    def __init__(self, data: bytes):
        self.b = data
        self.o = 0

    def read_bytes(self, n: int) -> bytes:
        out = self.b[self.o : self.o + n]
        if len(out) != n:
            raise NBTError("unexpected EOF")
        self.o += n
        return out

    def read_u8(self) -> int:
        return self.read_bytes(1)[0]

    def read_i8(self) -> int:
        return struct.unpack(">b", self.read_bytes(1))[0]

    def read_i16(self) -> int:
        return struct.unpack(">h", self.read_bytes(2))[0]

    def read_i32(self) -> int:
        return struct.unpack(">i", self.read_bytes(4))[0]

    def read_i64(self) -> int:
        return struct.unpack(">q", self.read_bytes(8))[0]

    def read_string(self) -> str:
        ln = self.read_i16()
        if ln < 0:
            raise NBTError("negative string length")
        return self.read_bytes(ln).decode("utf-8")


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
        return struct.unpack(">f", buf.read_bytes(4))[0]
    if tag == TAG_DOUBLE:
        return struct.unpack(">d", buf.read_bytes(8))[0]
    if tag == TAG_BYTE_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative byte array length")
        return list(buf.read_bytes(ln))
    if tag == TAG_STRING:
        return buf.read_string()
    if tag == TAG_LIST:
        inner = buf.read_u8()
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative list length")
        return [_read_payload(inner, buf) for _ in range(ln)]
    if tag == TAG_COMPOUND:
        out: MutableMapping[str, object] = OrderedDict()
        while True:
            inner = buf.read_u8()
            if inner == TAG_END:
                return out
            name = buf.read_string()
            out[name] = _read_payload(inner, buf)
    if tag == TAG_INT_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative int array length")
        return [buf.read_i32() for _ in range(ln)]
    if tag == TAG_LONG_ARRAY:
        ln = buf.read_i32()
        if ln < 0:
            raise NBTError("negative long array length")
        return [buf.read_i64() for _ in range(ln)]
    raise NBTError(f"unknown tag {tag}")


def load_nbt(path: Path) -> Mapping[str, object]:
    raw = path.read_bytes()
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    buf = _Buf(raw)
    root_tag = buf.read_u8()
    if root_tag != TAG_COMPOUND:
        raise NBTError(f"unexpected root tag {root_tag}")
    _ = buf.read_string()
    out = _read_payload(root_tag, buf)
    if not isinstance(out, Mapping):
        raise NBTError("root payload is not a compound")
    return out


def parse_showdown_species_ids(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8")
    anchor = "const Pokedex = {"
    if anchor not in text:
        raise ValueError(f"anchor not found in {path}")
    start = text.index(anchor) + len(anchor)
    i = start
    depth = 1
    entries: List[Tuple[str, str]] = []
    while i < len(text) and depth > 0:
        match = re.match(r"\s{2}([A-Za-z0-9]+): \{", text[i:])
        if match and depth == 1:
            key = match.group(1)
            i += match.end() - 1
            obj_start = i
            obj_depth = 1
            i += 1
            while i < len(text) and obj_depth > 0:
                ch = text[i]
                if ch == "{":
                    obj_depth += 1
                elif ch == "}":
                    obj_depth -= 1
                i += 1
            entries.append((key.lower(), text[obj_start:i]))
            continue

        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1

    species: Set[str] = set()
    for key, body in entries:
        num_match = re.search(r"\n\s{4}num: (-?\d+),", body)
        if not num_match:
            continue
        num = int(num_match.group(1))
        if num <= 0:
            continue
        if re.search(r"\n\s{4}baseSpecies:", body):
            continue
        if re.search(r'\n\s{4}name: "CAP ', body):
            continue
        species.add(key)
    return sorted(species)


def format_species_list(items: Sequence[str]) -> str:
    return "`" + ", ".join(items) + "`"


def pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def per_hour(count: int, hours: float) -> float:
    if hours <= 0:
        return 0.0
    return round(count / hours, 2)


def load_usercache(path: Path) -> Dict[str, str]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    out: Dict[str, str] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        uuid = row.get("uuid")
        name = row.get("name")
        if isinstance(uuid, str) and isinstance(name, str):
            out[uuid] = name
    return out


def load_player_report(data_dir: Path, player_uuid: str, player_name: str) -> Mapping[str, object]:
    pokedex_path = data_dir / "world" / "pokedex" / player_uuid[:2] / f"{player_uuid}.nbt"
    stats_path = data_dir / "world" / "stats" / f"{player_uuid}.json"

    pokedex = load_nbt(pokedex_path)
    stats = json.loads(stats_path.read_text(encoding="utf-8"))

    custom = (
        stats.get("stats", {}).get("minecraft:custom", {})
        if isinstance(stats, Mapping)
        else {}
    )
    play_ticks = int(custom.get("minecraft:play_time", 0))
    play_hours = play_ticks / 20.0 / 3600.0

    species_records = pokedex.get("speciesRecords", {})
    if not isinstance(species_records, Mapping):
        species_records = {}

    seen: Set[str] = set()
    caught: Set[str] = set()
    encountered_only: Set[str] = set()

    for species_id, record in species_records.items():
        if not isinstance(species_id, str) or not isinstance(record, Mapping):
            continue
        short_id = species_id.removeprefix("cobblemon:")
        form_records = record.get("formRecords", {})
        if not isinstance(form_records, Mapping):
            continue
        knowledge = {
            form_record.get("knowledge")
            for form_record in form_records.values()
            if isinstance(form_record, Mapping) and isinstance(form_record.get("knowledge"), str)
        }
        if knowledge:
            seen.add(short_id)
        if "CAUGHT" in knowledge:
            caught.add(short_id)
        elif "ENCOUNTERED" in knowledge:
            encountered_only.add(short_id)

    return {
        "name": player_name,
        "uuid": player_uuid,
        "play_ticks": play_ticks,
        "play_hours": play_hours,
        "battles_total": int(custom.get("cobblemon:battles_total", 0)),
        "battles_won": int(custom.get("cobblemon:battles_won", 0)),
        "captured_stat": int(custom.get("cobblemon:captured", 0)),
        "dex_entries_stat": int(custom.get("cobblemon:dex_entries", 0)),
        "seen": sorted(seen),
        "caught": sorted(caught),
        "encountered_only": sorted(encountered_only),
    }


def build_report(data_dir: Path) -> str:
    usercache = load_usercache(data_dir / "usercache.json")
    all_species = parse_showdown_species_ids(data_dir / "showdown" / "data" / "pokedex.js")
    all_species_set = set(all_species)

    players = [
        load_player_report(data_dir, player_uuid, player_name)
        for player_uuid, player_name in sorted(usercache.items(), key=lambda item: item[1].lower())
    ]

    world_seen: Set[str] = set()
    world_caught: Set[str] = set()
    for player in players:
        world_seen.update(player["seen"])
        world_caught.update(player["caught"])

    today = dt.date.today().isoformat()
    lines: List[str] = []
    lines.append(f"# Rapport Pokedex serveur - {today}")
    lines.append("")
    lines.append("## Perimetre")
    lines.append("")
    lines.append("- Source joueurs: `data/world/pokedex/<uuid>.nbt`")
    lines.append("- Source temps de jeu: `data/world/stats/<uuid>.json`")
    lines.append("- Base complete des especes: `data/showdown/data/pokedex.js`")
    lines.append("- Joueurs analyses: " + ", ".join(f"`{p['name']}`" for p in players))
    lines.append("")
    lines.append("Definitions:")
    lines.append("- `seen` = espece marquee `ENCOUNTERED` ou `CAUGHT` dans le Pokedex serveur.")
    lines.append("- `caught` = espece marquee `CAUGHT`.")
    lines.append("- `encountered_only` = vue mais pas capturee.")
    lines.append("- `play_time` = statistique vanilla `minecraft:play_time`, convertie en heures.")
    lines.append("")
    lines.append("## Vue d'ensemble")
    lines.append("")
    lines.append(f"- Especes implementees dans la stack: `{len(all_species)}`")
    lines.append(f"- Especes deja vues sur le serveur (union des joueurs): `{len(world_seen)}` soit `{pct(len(world_seen), len(all_species))}%`")
    lines.append(f"- Especes deja capturees sur le serveur (union des joueurs): `{len(world_caught)}` soit `{pct(len(world_caught), len(all_species))}%`")
    lines.append("")
    lines.append("| Joueur | Temps de jeu (h) | Vues | % du monde vu | % du roster total | Vues/h | Capturees | % du monde capture | % du roster total | Capt./h | Combats |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for player in players:
        seen = len(player["seen"])
        caught = len(player["caught"])
        hours = float(player["play_hours"])
        lines.append(
            "| {name} | {hours:.2f} | {seen} | {seen_world:.2f}% | {seen_all:.2f}% | {seen_h:.2f} | {caught} | {caught_world:.2f}% | {caught_all:.2f}% | {caught_h:.2f} | {battles} |".format(
                name=player["name"],
                hours=hours,
                seen=seen,
                seen_world=pct(seen, len(world_seen)),
                seen_all=pct(seen, len(all_species)),
                seen_h=per_hour(seen, hours),
                caught=caught,
                caught_world=pct(caught, len(world_caught)),
                caught_all=pct(caught, len(all_species)),
                caught_h=per_hour(caught, hours),
                battles=player["battles_total"],
            )
        )
    lines.append("")
    lines.append("Lecture rapide:")
    if players:
        best_seen = max(players, key=lambda p: len(p["seen"]))
        best_seen_h = max(players, key=lambda p: per_hour(len(p["seen"]), float(p["play_hours"])))
        best_caught_h = max(players, key=lambda p: per_hour(len(p["caught"]), float(p["play_hours"])))
        lines.append(f"- `{best_seen['name']}` a la meilleure couverture brute en especes vues.")
        lines.append(f"- `{best_seen_h['name']}` a le meilleur rythme en especes vues par heure.")
        lines.append(f"- `{best_caught_h['name']}` a le meilleur rythme en captures par heure.")
    lines.append("")
    lines.append("## Liste exhaustive du monde")
    lines.append("")
    lines.append("### World seen union")
    lines.append("")
    lines.append(format_species_list(sorted(world_seen)))
    lines.append("")
    lines.append("### World caught union")
    lines.append("")
    lines.append(format_species_list(sorted(world_caught)))
    lines.append("")
    lines.append("## Par joueur")
    lines.append("")

    for player in players:
        seen = len(player["seen"])
        caught = len(player["caught"])
        hours = float(player["play_hours"])
        lines.append(f"### {player['name']}")
        lines.append("")
        lines.append(f"- Temps de jeu: `{hours:.2f} h`")
        lines.append(f"- Especes vues: `{seen}`")
        lines.append(f"- Especes capturees: `{caught}`")
        lines.append(f"- Especes vues seulement: `{len(player['encountered_only'])}`")
        lines.append(f"- Couverture du monde vu: `{pct(seen, len(world_seen))}%`")
        lines.append(f"- Couverture du monde capture: `{pct(caught, len(world_caught))}%`")
        lines.append(f"- Couverture du roster complet: `{pct(seen, len(all_species))}%` vu, `{pct(caught, len(all_species))}%` capture")
        lines.append(f"- Rythme: `{per_hour(seen, hours):.2f}` especes vues/h, `{per_hour(caught, hours):.2f}` especes capturees/h")
        lines.append(f"- Combats: `{player['battles_total']}` total, `{player['battles_won']}` gagnes")
        lines.append("")
        lines.append("#### Seen")
        lines.append("")
        lines.append(format_species_list(player["seen"]))
        lines.append("")
        lines.append("#### Caught")
        lines.append("")
        lines.append(format_species_list(player["caught"]))
        lines.append("")
        lines.append("#### Encountered only")
        lines.append("")
        lines.append(format_species_list(player["encountered_only"]))
        lines.append("")

    lines.append("## Roster implemente mais jamais vu sur ce serveur")
    lines.append("")
    unseen = sorted(all_species_set - world_seen)
    lines.append(format_species_list(unseen))
    lines.append("")
    return "\n".join(lines)


def write_report(content: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8", newline="\n")


def _multipart_body(fields: Mapping[str, str], files: Mapping[str, Tuple[str, bytes, str]]) -> Tuple[bytes, str]:
    boundary = f"----codex-{uuid_lib.uuid4().hex}"
    chunks: List[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    for name, (filename, content, content_type) in files.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode(),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                content,
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary


def post_to_discord(webhook_url: str, report_path: Path, message: str) -> None:
    curl_bin = shutil.which("curl")
    if curl_bin:
        payload = json.dumps({"content": message})
        cmd = [
            curl_bin,
            "-fsS",
            "-m",
            "30",
            "-F",
            f"payload_json={payload}",
            "-F",
            f"file1=@{report_path};type=text/markdown",
            webhook_url,
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            return
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"failed to post report to Discord via curl: {stderr or exc}") from exc

    body, boundary = _multipart_body(
        fields={"payload_json": json.dumps({"content": message})},
        files={
            "file1": (
                report_path.name,
                report_path.read_bytes(),
                "text/markdown",
            )
        },
    )
    req = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30):
            return
    except urllib.error.URLError as exc:
        raise RuntimeError(f"failed to post report to Discord: {exc}") from exc


def resolve_webhook_url(args: argparse.Namespace) -> Optional[str]:
    if args.discord_webhook_url:
        return args.discord_webhook_url
    if args.discord_webhook_env:
        value = os.environ.get(args.discord_webhook_env)
        if value:
            return value
    return None


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    today = dt.date.today().strftime("%Y%m%d")
    parser = argparse.ArgumentParser(description="Generate a Cobblemon Pokedex comparison report.")
    parser.add_argument("--data-dir", default="./data", help="Server data directory (default: ./data)")
    parser.add_argument(
        "--output",
        default=f"./audit/pokedex-comparison-{today}.md",
        help="Markdown output path (default: ./audit/pokedex-comparison-YYYYMMDD.md)",
    )
    parser.add_argument("--stdout", action="store_true", help="Also print the report to stdout")
    parser.add_argument("--discord", action="store_true", help="Post the generated report to Discord")
    parser.add_argument("--discord-webhook-url", default="", help="Discord webhook URL override")
    parser.add_argument(
        "--discord-webhook-env",
        default="MONITOR_WEBHOOK_URL",
        help="Environment variable to read the Discord webhook URL from (default: MONITOR_WEBHOOK_URL)",
    )
    parser.add_argument(
        "--discord-message",
        default="Rapport detaille Pokedex serveur en piece jointe.",
        help="Discord message sent with the attachment",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    data_dir = Path(args.data_dir).resolve()
    output = Path(args.output).resolve()

    report = build_report(data_dir)
    write_report(report, output)

    if args.stdout:
        print(report)

    if args.discord:
        webhook_url = resolve_webhook_url(args)
        if not webhook_url:
            print("Discord requested but no webhook URL could be resolved.", file=sys.stderr)
            return 2
        post_to_discord(webhook_url, output, args.discord_message)
        print(f"OK report posted to Discord: {output}")
        return 0

    print(f"OK report written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
