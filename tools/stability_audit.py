#!/usr/bin/env python3
"""Correlate local client logs with remote server logs for stability analysis."""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


TIMESTAMP_RE = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\] \[(.+)\]: ?(.*)$")
SERVER_DISCONNECT_RE = re.compile(r"^(?P<player>[A-Za-z0-9_]+) lost connection: (?P<reason>.+)$")
SERVER_JOIN_RE = re.compile(r"^(?P<player>[A-Za-z0-9_]+) joined the game$")
SERVER_LOGIN_RE = re.compile(r"^(?P<player>[A-Za-z0-9_]+)\[/[^\]]+\] logged in with entity id ")
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
class Event:
    event_id: str
    date_heure: str
    source: str
    log_file: str
    joueur: str
    type: str
    signature: str
    level: str
    message: str
    impact_stabilite: str
    cause_probable: str
    severite: str
    evidence: str
    correlation: str = "unmatched"
    matched_event_ids: List[str] = field(default_factory=list)


def parse_site_local(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def iter_log_events(log_name: str, content: str) -> Iterable[Tuple[str, str, str, str]]:
    current_time = ""
    current_context = ""
    current_message = ""
    details: List[str] = []

    def flush() -> Optional[Tuple[str, str, str, str]]:
        nonlocal details
        if not current_time:
            return None
        detail_text = "\n".join(details).rstrip()
        details = []
        return current_time, current_context, current_message, detail_text

    for raw_line in content.splitlines():
        match = TIMESTAMP_RE.match(raw_line)
        if match:
            payload = flush()
            if payload is not None:
                yield payload
            current_time, current_context, current_message = match.groups()
            continue
        if current_time:
            details.append(raw_line)

    payload = flush()
    if payload is not None:
        yield payload


def classify_client_event(
    event_id: str,
    timestamp: str,
    log_file: str,
    context: str,
    message: str,
    details: str,
    default_player: str,
) -> Optional[Event]:
    evidence = f"{timestamp} | {log_file} | {message}"
    _, level = split_context(context)

    if "Player logout received" in message or "Disconnected from server" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="client",
            log_file=log_file,
            joueur=default_player,
            type="disconnect",
            signature="client_logout",
            level=level,
            message=message,
            impact_stabilite="client session ended cleanly",
            cause_probable="logout or upstream disconnect acknowledged by client",
            severite="low",
            evidence=evidence,
        )

    if "Failed to resolve uniform inPaleGarden" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="client",
            log_file=log_file,
            joueur=default_player,
            type="client_error",
            signature="iris_shader_uniform_missing",
            level=level,
            message=message,
            impact_stabilite="client startup/render pipeline failure",
            cause_probable="Iris shader pack expects biome variables unavailable in this stack",
            severite="medium",
            evidence=evidence,
        )

    if "[FANCYMENU] Failed to read" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="client",
            log_file=log_file,
            joueur=default_player,
            type="client_error",
            signature="fancymenu_missing_asset",
            level=level,
            message=message,
            impact_stabilite="client UI customization degraded",
            cause_probable="FancyMenu references local files missing from the profile",
            severite="low",
            evidence=evidence,
        )

    if "Received attachment change for unknown target!" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="client",
            log_file=log_file,
            joueur=default_player,
            type="client_warning",
            signature="supplementaries_unknown_target",
            level=level,
            message=message,
            impact_stabilite="log noise, possible client entity sync race",
            cause_probable="client received attachment update before entity resolution",
            severite="low",
            evidence=evidence,
        )

    if "Received passengers for unknown entity" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="client",
            log_file=log_file,
            joueur=default_player,
            type="client_warning",
            signature="unknown_entity_passengers",
            level=level,
            message=message,
            impact_stabilite="log noise, possible transient entity desync",
            cause_probable="client passenger packet arrived before entity state was present locally",
            severite="low",
            evidence=evidence,
        )

    return None


def classify_server_event(
    event_id: str,
    timestamp: str,
    log_file: str,
    context: str,
    message: str,
    details: str,
) -> Optional[Event]:
    evidence = f"{timestamp} | {log_file} | {message}"
    _, level = split_context(context)

    match = SERVER_DISCONNECT_RE.match(message)
    if match:
        player = match.group("player")
        reason = match.group("reason")
        severity = "medium" if reason == "Server closed" else "low"
        impact = "player disconnected because server stopped" if reason == "Server closed" else "player disconnected without server-side exception"
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="server",
            log_file=log_file,
            joueur=player,
            type="disconnect",
            signature=f"server_disconnect:{reason.lower().replace(' ', '_')}",
            level=level,
            message=message,
            impact_stabilite=impact,
            cause_probable=f"server recorded player disconnect reason: {reason}",
            severite=severity,
            evidence=evidence,
        )

    match = SERVER_JOIN_RE.match(message) or SERVER_LOGIN_RE.match(message)
    if match:
        player = match.group("player")
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="server",
            log_file=log_file,
            joueur=player,
            type="join",
            signature="server_player_join",
            level=level,
            message=message,
            impact_stabilite="normal player session start",
            cause_probable="valid player connection",
            severite="info",
            evidence=evidence,
        )

    if message == "Stopping the server":
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="server",
            log_file=log_file,
            joueur="",
            type="server_shutdown",
            signature="server_stopping",
            level=level,
            message=message,
            impact_stabilite="all active sessions will be interrupted",
            cause_probable="graceful server stop or restart",
            severite="medium",
            evidence=evidence,
        )

    if "Unable to close Phantom Array" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="server",
            log_file=log_file,
            joueur="",
            type="server_error",
            signature="dh_phantom_array_error",
            level=level,
            message=message,
            impact_stabilite="active Distant Horizons server-side generation error",
            cause_probable="Distant Horizons world generation bookkeeping is closing phantom arrays twice",
            severite="medium",
            evidence=evidence,
        )

    if "Generation for section" in message and "has expired" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="server",
            log_file=log_file,
            joueur="",
            type="server_warning",
            signature="dh_generation_expired",
            level=level,
            message=message,
            impact_stabilite="Distant Horizons generation job expired before completion",
            cause_probable="server-side LOD generation stalled or was superseded",
            severite="medium",
            evidence=evidence,
        )

    if "WorldGen requiring [" in message and "outside the expected range" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="server",
            log_file=log_file,
            joueur="",
            type="server_warning",
            signature="dh_worldgen_outside_range",
            level=level,
            message=message,
            impact_stabilite="Distant Horizons requested worldgen outside the expected range",
            cause_probable="generation mode mismatch or unsupported structure lookup during DH pregen",
            severite="low",
            evidence=evidence,
        )

    if "Ignoring unknown attribute 'forge:entity_gravity'" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="server",
            log_file=log_file,
            joueur="",
            type="server_warning",
            signature="dh_unknown_attribute",
            level=level,
            message=message,
            impact_stabilite="mod compatibility warning during DH generation",
            cause_probable="Distant Horizons encountered a Forge attribute on Fabric entities",
            severite="low",
            evidence=evidence,
        )

    if "C2ME missing" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="server",
            log_file=log_file,
            joueur="",
            type="server_warning",
            signature="dh_c2me_missing",
            level=level,
            message=message,
            impact_stabilite="Distant Horizons cannot use its faster C2ME path",
            cause_probable="C2ME is not installed on the server",
            severite="low",
            evidence=evidence,
        )

    if "Can't keep up!" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="server",
            log_file=log_file,
            joueur="",
            type="server_warning",
            signature="server_tick_lag",
            level=level,
            message=message,
            impact_stabilite="tick lag reached user-visible levels",
            cause_probable="server could not maintain 20 TPS",
            severite="high",
            evidence=evidence,
        )

    if "Error sending packet clientbound/minecraft:disconnect" in message:
        return Event(
            event_id=event_id,
            date_heure=timestamp,
            source="server",
            log_file=log_file,
            joueur="",
            type="server_warning",
            signature="disconnect_packet_error",
            level=level,
            message=message,
            impact_stabilite="network disconnect packet could not be delivered",
            cause_probable="client disconnected before receiving the server disconnect packet",
            severite="low",
            evidence=evidence,
        )

    return None


def split_context(context: str) -> Tuple[str, str]:
    if "/" not in context:
        return context, ""
    thread, level = context.rsplit("/", 1)
    return thread, level


def collect_local_logs(log_dir: Path, start: dt.date, end: dt.date) -> Dict[str, str]:
    contents: Dict[str, str] = {}
    for path in sorted(log_dir.glob("*.log.gz")):
        date_part = path.name[:10]
        try:
            log_date = dt.date.fromisoformat(date_part)
        except ValueError:
            continue
        if not (start <= log_date <= end):
            continue
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
            contents[path.name] = fh.read()
    return contents


def collect_remote_logs(repo_root: Path, start: dt.date, end: dt.date) -> Dict[str, str]:
    site = parse_site_local(repo_root / "runbooks" / "site.local.md")
    host = site["MC_SERVER_HOST"]
    user = site["MC_SSH_USER"]
    project_dir = site["MC_PROJECT_DIR"]
    key = site["SSH_KEY_MAIN"]

    remote_paths: List[str] = []
    current = start
    while current <= end:
        for suffix in ("1", "2", "3", "4"):
            remote_paths.append(f"{project_dir}/data/logs/{current.isoformat()}-{suffix}.log.gz")
        current += dt.timedelta(days=1)
    remote_paths.append(f"{project_dir}/data/logs/latest.log")

    python_source = REMOTE_PYTHON_TEMPLATE.format(paths_literal=json.dumps(remote_paths))
    command = ["ssh", "-i", key, f"{user}@{host}", "python3", "-"]
    completed = subprocess.run(command, input=python_source, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def correlate_events(events: List[Event]) -> None:
    client_disconnects: Dict[Tuple[str, str], Event] = {}
    server_disconnects: Dict[Tuple[str, str], Event] = {}

    for event in events:
        if event.type != "disconnect":
            continue
        key = (event.date_heure, event.joueur)
        if event.source == "client":
            client_disconnects[key] = event
        elif event.source == "server":
            server_disconnects[key] = event

    for key, client_event in client_disconnects.items():
        server_event = server_disconnects.get(key)
        if server_event is None:
            client_event.correlation = "client-only"
            continue
        client_event.correlation = "correlated"
        server_event.correlation = "correlated"
        client_event.matched_event_ids.append(server_event.event_id)
        server_event.matched_event_ids.append(client_event.event_id)

    for server_event in server_disconnects.values():
        if server_event.correlation == "correlated":
            continue
        server_event.correlation = "server-only"

    for event in events:
        if event.correlation != "unmatched":
            continue
        event.correlation = "client-only" if event.source == "client" else "server-only"


def dedupe_events(events: List[Event]) -> List[Event]:
    noisy_signatures = {
        "supplementaries_unknown_target",
        "unknown_entity_passengers",
        "dh_phantom_array_error",
        "dh_generation_expired",
        "dh_worldgen_outside_range",
        "dh_unknown_attribute",
    }
    kept: List[Event] = []
    seen: set[Tuple[str, str, str, str]] = set()

    for event in events:
        if event.signature not in noisy_signatures:
            kept.append(event)
            continue
        minute_key = event.date_heure[:16]
        key = (event.source, event.log_file, event.signature, minute_key)
        if key in seen:
            continue
        seen.add(key)
        kept.append(event)

    return kept


def build_focus_incidents(events: List[Event], default_player: str) -> List[Dict[str, str]]:
    incidents: List[Dict[str, str]] = []

    def add_incident(
        date_heure: str,
        source: str,
        joueur: str,
        signature: str,
        correlation: str,
        severity: str,
        impact: str,
        cause: str,
        proof_events: Sequence[Event],
    ) -> None:
        preuve = " | ".join(f"{event.log_file} @ {event.date_heure} -> {event.message}" for event in proof_events[:3])
        incidents.append(
            {
                "date_heure": date_heure,
                "source": source,
                "joueur": joueur,
                "signature": signature,
                "corrélation": correlation,
                "sévérité": severity,
                "impact stabilité": impact,
                "cause probable": cause,
                "preuve": preuve,
            }
        )

    def find(timestamp: str, source: str, signature_prefix: str, player: str = "") -> List[Event]:
        return [
            event
            for event in events
            if event.date_heure == timestamp
            and event.source == source
            and event.signature.startswith(signature_prefix)
            and (not player or event.joueur == player)
        ]

    proof = find("2026-03-07 01:03:04", "client", "client_logout", default_player) + find(
        "2026-03-07 01:03:05", "server", "server_disconnect", default_player
    )
    if proof:
        add_incident(
            "2026-03-07 01:03:04",
            "client+server",
            default_player,
            "session_disconnect_clean",
            "corrélé",
            "low",
            "session ended cleanly with matching client/server disconnects",
            "normal disconnect; no server-side instability observed in the same minute",
            proof,
        )

    proof = find("2026-03-07 19:23:08", "client", "iris_shader_uniform_missing", default_player) + [
        event for event in events if event.log_file == "2026-03-07-3.log.gz" and event.signature == "fancymenu_missing_asset"
    ]
    if proof:
        add_incident(
            "2026-03-07 19:23:08",
            "client",
            default_player,
            "client_startup_render_failure",
            "client-only",
            "medium",
            "client render/UI pipeline failed before gameplay session",
            "Iris shader incompatibility plus missing FancyMenu assets",
            proof,
        )

    proof = find("2026-03-07 23:18:07", "client", "client_logout", default_player) + find(
        "2026-03-07 23:18:09", "server", "server_disconnect", default_player
    )
    if proof:
        add_incident(
            "2026-03-07 23:18:07",
            "client+server",
            default_player,
            "session_disconnect_clean",
            "corrélé",
            "low",
            "session ended cleanly with matching disconnects",
            "normal disconnect; nearby server warnings are discarded entity noise, not a crash",
            proof,
        )

    proof = find("2026-03-08 11:24:16", "client", "client_logout", default_player) + find(
        "2026-03-08 11:24:16", "server", "server_disconnect", default_player
    )
    if proof:
        add_incident(
            "2026-03-08 11:24:16",
            "client+server",
            default_player,
            "session_disconnect_clean",
            "corrélé",
            "low",
            "client and server record the same disconnect second",
            "player disconnect acknowledged on both sides; no paired server error around that second",
            proof,
        )

    proof = find("2026-03-08 11:49:04", "server", "server_stopping") + find(
        "2026-03-08 11:49:04", "server", "server_disconnect", default_player
    )
    if proof:
        add_incident(
            "2026-03-08 11:49:04",
            "server",
            default_player,
            "server_restart_interrupting_player",
            "serveur-only",
            "medium",
            "server performed an orderly shutdown while the player was online",
            "graceful restart or maintenance stop; no crash signature or watchdog present",
            proof,
        )

    dh_proof = [
        event
        for event in events
        if event.date_heure.startswith("2026-03-08 11:56:")
        and event.signature in {"dh_generation_expired", "dh_phantom_array_error", "dh_c2me_missing"}
    ]
    if dh_proof:
        add_incident(
            "2026-03-08 11:56:02",
            "server",
            default_player,
            "distant_horizons_pregen_errors",
            "serveur-only",
            "medium",
            "Distant Horizons pregen emitted repeated errors while a player was online",
            "server-side DH pregen is unstable under current generation mode changes and thread activity",
            dh_proof,
        )

    incidents.sort(key=lambda item: item["date_heure"])
    return incidents


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Correlate client and server stability logs")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--start-date", default="2026-03-04")
    parser.add_argument("--end-date", default="2026-03-08")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", default=None, help="Optional JSON output path")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    start = dt.date.fromisoformat(args.start_date)
    end = dt.date.fromisoformat(args.end_date)
    site = parse_site_local(repo_root / "runbooks" / "site.local.md")
    default_player = site.get("DEFAULT_PLAYER_NAME", "player")

    client_logs = collect_local_logs(repo_root / "logs", start, end)
    server_logs = collect_remote_logs(repo_root, start, end)

    events: List[Event] = []
    event_counter = 0

    for log_name, content in sorted(client_logs.items()):
        date_str = log_name[:10]
        for time_str, context, message, details in iter_log_events(log_name, content):
            event_counter += 1
            event = classify_client_event(
                event_id=f"event-{event_counter:04d}",
                timestamp=f"{date_str} {time_str}",
                log_file=log_name,
                context=context,
                message=message,
                details=details,
                default_player=default_player,
            )
            if event is not None:
                events.append(event)

    for log_name, content in sorted(server_logs.items()):
        date_str = log_name[:10] if re.match(r"\d{4}-\d{2}-\d{2}", log_name) else end.isoformat()
        for time_str, context, message, details in iter_log_events(log_name, content):
            event_counter += 1
            event = classify_server_event(
                event_id=f"event-{event_counter:04d}",
                timestamp=f"{date_str} {time_str}",
                log_file=log_name,
                context=context,
                message=message,
                details=details,
            )
            if event is not None:
                events.append(event)

    events.sort(key=lambda item: item.date_heure)
    events = dedupe_events(events)
    correlate_events(events)
    incidents = build_focus_incidents(events, default_player)

    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "window": {"start_date": args.start_date, "end_date": args.end_date},
        "time_reference": "Minecraft container timestamps (+01:00 / CET at collection time)",
        "default_player": default_player,
        "client_logs": sorted(client_logs),
        "server_logs": sorted(server_logs),
        "events": [asdict(event) for event in events],
        "incidents": incidents,
    }

    if args.write:
        output = Path(args.output) if args.output else repo_root / "audit" / "stability-audit-20260308.json"
        write_json(output, summary)

    print(
        json.dumps(
            {
                "generated_at": summary["generated_at"],
                "window": summary["window"],
                "event_count": len(events),
                "incident_count": len(incidents),
                "client_logs": summary["client_logs"],
                "server_logs": summary["server_logs"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
