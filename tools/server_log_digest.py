#!/usr/bin/env python3
"""Summarize remote Minecraft server activity and stability signals."""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


TIMESTAMP_RE = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\] \[(.+)\]: ?(.*)$")
JOIN_RE = re.compile(r"^(?P<player>[A-Za-z0-9_]+) joined the game$")
LOST_RE = re.compile(r"^(?P<player>[A-Za-z0-9_]+) lost connection: (?P<reason>.+)$")
DISCARDED_RE = re.compile(
    r"Entity PokemonEntity\['(?P<species>[^']+)'/(?P<entity_id>\d+).+removed=DISCARDED\]"
)
MOVED_TOO_QUICKLY_RE = re.compile(r"^(?P<actor>.+?) moved too quickly!")
MOVED_WRONGLY_RE = re.compile(r"^(?P<actor>.+?) moved wrongly!")
REMOTE_PYTHON_TEMPLATE = """
import gzip
import json
import pathlib

paths = {paths_literal}
payload = {{}}
for path in paths:
    p = pathlib.Path(path)
    if not p.exists():
        continue
    opener = gzip.open if p.suffix == '.gz' else open
    with opener(p, 'rt', encoding='utf-8', errors='replace') as fh:
        payload[p.name] = fh.read()
print(json.dumps(payload, ensure_ascii=False))
"""


@dataclass
class Signal:
    timestamp: str
    log_file: str
    kind: str
    actor: str
    message: str


def parse_site_local(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def ssh_hosts(site: Dict[str, str]) -> List[str]:
    hosts: List[str] = []
    for key in ("MC_SERVER_HOST", "MC_SERVER_HOST_FALLBACK", "MC_SERVER_HOST_SECONDARY"):
        value = site.get(key, "").strip()
        if value and value not in hosts:
            hosts.append(value)
    return hosts


def ssh_python_json(site: Dict[str, str], python_source: str, timeout: int = 60) -> Dict[str, str]:
    user = site["MC_SSH_USER"]
    key = site["SSH_KEY_MAIN"]
    last_error: Optional[subprocess.CalledProcessError] = None
    for host in ssh_hosts(site):
        command = [
            "ssh",
            "-o",
            "ConnectTimeout=5",
            "-i",
            key,
            f"{user}@{host}",
            "python3",
            "-",
        ]
        try:
            completed = subprocess.run(
                command,
                input=python_source,
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return json.loads(completed.stdout)
        except subprocess.CalledProcessError as exc:
            last_error = exc
        except subprocess.TimeoutExpired:
            continue
    if last_error is not None:
        raise last_error
    raise RuntimeError("No SSH host configured")


def ssh_bash(site: Dict[str, str], script: str, timeout: int = 20) -> str:
    user = site["MC_SSH_USER"]
    key = site["SSH_KEY_MAIN"]
    last_error: Optional[subprocess.CalledProcessError] = None
    for host in ssh_hosts(site):
        command = [
            "ssh",
            "-o",
            "ConnectTimeout=5",
            "-i",
            key,
            f"{user}@{host}",
            "bash",
            "-lc",
            script,
        ]
        try:
            completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=timeout)
            return completed.stdout
        except subprocess.CalledProcessError as exc:
            last_error = exc
        except subprocess.TimeoutExpired:
            continue
    if last_error is not None:
        raise last_error
    raise RuntimeError("No SSH host configured")


def iter_log_lines(log_name: str, content: str) -> Iterable[Tuple[str, str, str]]:
    for raw_line in content.splitlines():
        match = TIMESTAMP_RE.match(raw_line)
        if match:
            yield match.groups()


def collect_remote_logs(repo_root: Path, start: dt.date, end: dt.date) -> Dict[str, str]:
    site = parse_site_local(repo_root / "runbooks" / "site.local.md")
    project_dir = site["MC_PROJECT_DIR"]

    remote_paths: List[str] = []
    current = start
    while current <= end:
        for suffix in ("1", "2", "3", "4"):
            remote_paths.append(f"{project_dir}/data/logs/{current.isoformat()}-{suffix}.log.gz")
        current += dt.timedelta(days=1)
    if end >= dt.date.today():
        remote_paths.append(f"{project_dir}/data/logs/latest.log")

    python_source = REMOTE_PYTHON_TEMPLATE.format(paths_literal=json.dumps(remote_paths))
    return ssh_python_json(site, python_source)


def detect_signals(log_name: str, log_date: str, content: str) -> Tuple[List[Signal], Counter[str]]:
    signals: List[Signal] = []
    counters: Counter[str] = Counter()

    for time_str, _context, message in iter_log_lines(log_name, content):
        timestamp = f"{log_date} {time_str}"
        if JOIN_RE.match(message):
            player = JOIN_RE.match(message).group("player")  # type: ignore[union-attr]
            signals.append(Signal(timestamp, log_name, "join", player, message))
            counters["join"] += 1
            continue

        lost_match = LOST_RE.match(message)
        if lost_match:
            signals.append(Signal(timestamp, log_name, "disconnect", lost_match.group("player"), message))
            counters["disconnect"] += 1
            if lost_match.group("player") == "MCScans":
                counters["scanner_disconnect"] += 1
            continue

        if "Can't keep up!" in message:
            signals.append(Signal(timestamp, log_name, "cant_keep_up", "", message))
            counters["cant_keep_up"] += 1
            continue

        discarded_match = DISCARDED_RE.search(message)
        if discarded_match:
            signals.append(Signal(timestamp, log_name, "discarded", discarded_match.group("species"), message))
            counters["discarded"] += 1
            continue

        moved_too_quickly_match = MOVED_TOO_QUICKLY_RE.match(message)
        if moved_too_quickly_match:
            signals.append(Signal(timestamp, log_name, "moved_too_quickly", moved_too_quickly_match.group("actor"), message))
            counters["moved_too_quickly"] += 1
            continue

        moved_wrongly_match = MOVED_WRONGLY_RE.match(message)
        if moved_wrongly_match:
            signals.append(Signal(timestamp, log_name, "moved_wrongly", moved_wrongly_match.group("actor"), message))
            counters["moved_wrongly"] += 1
            continue

        if "Server Watchdog" in message or "A single server tick took" in message:
            signals.append(Signal(timestamp, log_name, "watchdog", "", message))
            counters["watchdog"] += 1
            continue

        if message == "Stopping the server":
            signals.append(Signal(timestamp, log_name, "server_stop", "", message))
            counters["server_stop"] += 1
            continue

        if message.startswith("Done ("):
            signals.append(Signal(timestamp, log_name, "server_done", "", message))
            counters["server_done"] += 1
            continue

        if "Error sending packet clientbound/minecraft:disconnect" in message:
            signals.append(Signal(timestamp, log_name, "disconnect_packet_error", "", message))
            counters["disconnect_packet_error"] += 1
            continue

    return signals, counters


def format_markdown(summary: Dict[str, object]) -> str:
    window = summary["window"]
    current = summary["current_state"]
    counts = summary["counts"]
    players = summary["players"]
    top_species = summary["top_discarded_species"]
    discarded_hours = summary["discarded_by_hour"]
    lag_hours = summary["lag_by_hour"]
    recent = summary["recent_signals"]
    recommendations = summary["recommendations"]

    lines = [
        "# Synthese journaliere serveur",
        "",
        f"- Fenetre: `{window['start_date']}` a `{window['end_date']}`",
        f"- Genere le: `{summary['generated_at']}`",
        "",
        "## Etat courant",
        "",
        f"- Statut conteneur: `{current['container_status']}`",
        f"- Sante conteneur: `{current['container_health']}`",
        f"- Players online au relevé: `{current['players_online']}`",
        f"- CPU conteneur: `{current['container_cpu']}`",
        f"- Memoire conteneur: `{current['container_mem']}`",
        "",
        "## Compteurs",
        "",
    ]

    for key in (
        "join",
        "disconnect",
        "cant_keep_up",
        "discarded",
        "moved_too_quickly",
        "moved_wrongly",
        "disconnect_packet_error",
        "watchdog",
        "server_stop",
        "server_done",
    ):
        lines.append(f"- `{key}`: `{counts.get(key, 0)}`")

    lines.extend(["", "## Activite joueurs", ""])
    if players:
        for player, events in players.items():
            rendered = " | ".join(f"{item['timestamp']} {item['kind']}" for item in events[:8])
            lines.append(f"- `{player}`: {rendered}")
    else:
        lines.append("- aucun evenement joueur sur la fenetre")

    lines.extend(["", "## DISCARDED", ""])
    if top_species:
        for item in top_species:
            lines.append(f"- `{item['species']}`: `{item['count']}`")
    else:
        lines.append("- aucun `removed=DISCARDED`")

    lines.extend(["", "## Repartition horaire", ""])
    if discarded_hours:
        lines.append("- `discarded_by_hour`:")
        for hour, count in discarded_hours.items():
            lines.append(f"  - `{hour}`: `{count}`")
    else:
        lines.append("- `discarded_by_hour`: aucun")
    if lag_hours:
        lines.append("- `lag_by_hour`:")
        for hour, count in lag_hours.items():
            lines.append(f"  - `{hour}`: `{count}`")
    else:
        lines.append("- `lag_by_hour`: aucun")

    lines.extend(["", "## Signaux recents", ""])
    if recent:
        for item in recent:
            lines.append(
                f"- `{item['timestamp']}` `{item['kind']}` `{item['actor']}`: {item['message']}"
            )
    else:
        lines.append("- aucun signal recent retenu")

    lines.extend(["", "## Actions recommandees", ""])
    for item in recommendations:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def current_state(repo_root: Path) -> Dict[str, str]:
    site = parse_site_local(repo_root / "runbooks" / "site.local.md")
    project_dir = site["MC_PROJECT_DIR"]
    script = """
cd __PROJECT_DIR__
container_status=$(docker inspect cobblemon --format '{{.State.Status}}' 2>/dev/null || echo missing)
container_health=$(docker inspect cobblemon --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo missing)
players_line=$(docker logs cobblemon --tail 200 2>/dev/null | grep -E 'There are [0-9]+ of a max' | tail -n 1 || true)
players_online=$(printf '%s' "$players_line" | sed -nE 's/.*There are ([0-9]+) of a max.*/\\1/p')
docker_line=$(docker stats --no-stream --format '{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}' 2>/dev/null | awk -F'|' '$1=="cobblemon"{{print $0}}')
printf 'container_status=%s\n' "$container_status"
printf 'container_health=%s\n' "$container_health"
printf 'players_online=%s\n' "${players_online:-0}"
printf 'docker_line=%s\n' "$docker_line"
""".replace("__PROJECT_DIR__", project_dir)
    raw = ssh_bash(site, script)
    payload: Dict[str, str] = {}
    for line in raw.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        payload[key] = value
    docker_parts = payload["docker_line"].split("|") if payload.get("docker_line") else ["", "n/a", "n/a"]
    return {
        "container_status": payload.get("container_status", "missing"),
        "container_health": payload.get("container_health", "missing"),
        "players_online": payload.get("players_online", "0"),
        "container_cpu": docker_parts[1] if len(docker_parts) > 1 else "n/a",
        "container_mem": docker_parts[2] if len(docker_parts) > 2 else "n/a",
    }


def write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_summary(repo_root: Path, start: dt.date, end: dt.date) -> Dict[str, object]:
    logs = collect_remote_logs(repo_root, start, end)
    counts: Counter[str] = Counter()
    all_signals: List[Signal] = []
    players: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    discarded_species: Counter[str] = Counter()
    discarded_by_hour: Counter[str] = Counter()
    lag_by_hour: Counter[str] = Counter()
    moved_by_actor: Counter[str] = Counter()

    for log_name, content in sorted(logs.items()):
        if re.match(r"\d{4}-\d{2}-\d{2}", log_name):
            log_date = log_name[:10]
        else:
            log_date = end.isoformat()
        signals, log_counts = detect_signals(log_name, log_date, content)
        counts.update(log_counts)
        all_signals.extend(signals)

    all_signals.sort(key=lambda item: item.timestamp)
    for signal in all_signals:
        hour = signal.timestamp[:13]
        if signal.kind in {"join", "disconnect"}:
            players[signal.actor].append({"timestamp": signal.timestamp, "kind": signal.kind, "message": signal.message})
        if signal.kind == "discarded":
            discarded_species[signal.actor] += 1
            discarded_by_hour[hour] += 1
        if signal.kind == "cant_keep_up":
            lag_by_hour[hour] += 1
        if signal.kind in {"moved_too_quickly", "moved_wrongly"}:
            moved_by_actor[signal.actor] += 1

    recommendations: List[str] = []
    if counts["watchdog"]:
        recommendations.append("Traiter le risque watchdog en priorite avant tout nouveau changement de modpack.")
    if counts["cant_keep_up"] >= 10:
        recommendations.append("Conserver la baseline et suivre les pics de `Can't keep up!` par heure de jeu.")
    if counts["discarded"] >= 10:
        recommendations.append("Ouvrir un incident Cobblemon centre sur `removed=DISCARDED` avec les especes et horaires dominants.")
    if counts["moved_too_quickly"] or counts["moved_wrongly"]:
        recommendations.append("Conserver les warnings de mouvement comme signature secondaire pour corriger le probleme d'entites Cobblemon.")
    if counts["disconnect_packet_error"]:
        recommendations.append("Traiter `clientbound/minecraft:disconnect` comme bruit reseau secondaire, pas comme cause racine.")
    if not recommendations:
        recommendations.append("Aucun signal majeur sur la fenetre; continuer le suivi quotidien sans changement de configuration.")

    recent_signals = [
        {
            "timestamp": item.timestamp,
            "kind": item.kind,
            "actor": item.actor,
            "message": item.message,
        }
        for item in all_signals[-20:]
    ]

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "window": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "counts": dict(counts),
        "players": dict(players),
        "top_discarded_species": [
            {"species": species, "count": count} for species, count in discarded_species.most_common(10)
        ],
        "discarded_by_hour": dict(sorted(discarded_by_hour.items())),
        "lag_by_hour": dict(sorted(lag_by_hour.items())),
        "moved_by_actor": [{"actor": actor, "count": count} for actor, count in moved_by_actor.most_common(10)],
        "recent_signals": recent_signals,
        "recommendations": recommendations,
        "current_state": current_state(repo_root),
        "source_logs": sorted(logs),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize remote Minecraft server activity and stability signals")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--start-date", default=dt.date.today().isoformat())
    parser.add_argument("--end-date", default=dt.date.today().isoformat())
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output-prefix", default=None, help="Path prefix without extension for generated files")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    start = dt.date.fromisoformat(args.start_date)
    end = dt.date.fromisoformat(args.end_date)
    summary = build_summary(repo_root, start, end)

    if args.write:
        if args.output_prefix:
            prefix = Path(args.output_prefix)
        else:
            suffix = start.strftime("%Y%m%d") if start == end else f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
            prefix = repo_root / "audit" / f"server-log-digest-{suffix}"
        write_output(prefix.with_suffix(".json"), json.dumps(summary, ensure_ascii=False, indent=2))
        write_output(prefix.with_suffix(".md"), format_markdown(summary))

    print(
        json.dumps(
            {
                "window": summary["window"],
                "counts": summary["counts"],
                "top_discarded_species": summary["top_discarded_species"][:5],
                "current_state": summary["current_state"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
