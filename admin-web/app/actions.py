from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import docker
from docker.errors import DockerException, NotFound

PLAYER_STATUS_RE = re.compile(r"There are (?P<online>\d+) of a max of (?P<max>\d+) players online")
_STDOUT_TAIL_LIMIT = 8_192
_DEFAULT_RESTART_TIMEOUT_SEC = 120
_POLL_INTERVAL_SEC = 2


class ActionError(RuntimeError):
    """Raised when a requested admin action cannot be completed."""


@dataclass
class AppSettings:
    repo_root: Path
    password: str
    session_secret: str
    cookie_secure: bool
    job_history: int

    @classmethod
    def from_env(cls) -> "AppSettings":
        repo_root = Path(os.environ.get("MC_ADMIN_WEB_REPO_ROOT", "/workspace")).resolve()
        password = os.environ.get("MC_ADMIN_WEB_PASSWORD", "")
        session_secret = os.environ.get("MC_ADMIN_WEB_SESSION_SECRET", "")
        cookie_secure = os.environ.get("MC_ADMIN_WEB_COOKIE_SECURE", "false").lower() == "true"
        job_history = int(os.environ.get("MC_ADMIN_WEB_JOB_HISTORY", "100"))
        return cls(
            repo_root=repo_root,
            password=password,
            session_secret=session_secret,
            cookie_secure=cookie_secure,
            job_history=job_history,
        )


def utcnow_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def get_docker_client() -> docker.DockerClient:
    try:
        return docker.from_env()
    except DockerException as exc:
        raise ActionError(f"Docker client unavailable: {exc}") from exc


def get_container(client: docker.DockerClient, name: str = "cobblemon"):
    try:
        container = client.containers.get(name)
        container.reload()
        return container
    except NotFound as exc:
        raise ActionError(
            "Container 'cobblemon' is missing. Start the stack from the server CLI with ./infra/start.sh."
        ) from exc
    except DockerException as exc:
        raise ActionError(f"Failed to inspect Docker container: {exc}") from exc


def _safe_decode(data: object) -> str:
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return str(data)


def _truncate(text: str) -> str:
    if len(text) <= _STDOUT_TAIL_LIMIT:
        return text
    return text[-_STDOUT_TAIL_LIMIT:]


def _run_script(repo_root: Path, *args: str, timeout: int) -> tuple[str, str]:
    command = ["bash", *args]
    try:
        proc = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ActionError(f"Missing executable for command: {' '.join(command)}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ActionError(f"Command timed out after {timeout}s: {' '.join(command)}") from exc

    stdout = _truncate(proc.stdout)
    stderr = _truncate(proc.stderr)
    if proc.returncode != 0:
        message = stderr or stdout or f"Command failed with exit code {proc.returncode}"
        raise ActionError(message)
    return stdout, stderr


def read_whitelist(repo_root: Path) -> list[str]:
    path = repo_root / "data" / "whitelist.json"
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ActionError(f"Failed to parse whitelist file: {exc}") from exc

    names = [str(entry["name"]) for entry in data if isinstance(entry, dict) and "name" in entry]
    names.sort(key=str.casefold)
    return names


def read_logs(tail: int) -> list[str]:
    client = get_docker_client()
    container = get_container(client)
    try:
        content = _safe_decode(container.logs(tail=tail))
    except DockerException as exc:
        raise ActionError(f"Failed to read container logs: {exc}") from exc

    return [line for line in content.splitlines() if line.strip()]


def get_status(repo_root: Path) -> dict[str, object]:
    client = get_docker_client()
    try:
        container = get_container(client)
    except ActionError as exc:
        if "missing" not in str(exc):
            raise
        return {
            "container_exists": False,
            "container_state": "missing",
            "health": "missing",
            "players_online": None,
            "players_max": None,
            "whitelist_count": len(read_whitelist(repo_root)),
            "last_status_line": None,
            "updated_at": utcnow_iso(),
        }

    state = str(container.attrs.get("State", {}).get("Status", "unknown"))
    health = str(container.attrs.get("State", {}).get("Health", {}).get("Status", "none"))

    try:
        lines = [line for line in _safe_decode(container.logs(tail=250)).splitlines() if line.strip()]
    except DockerException as exc:
        raise ActionError(f"Failed to read container logs: {exc}") from exc

    last_status_line = next((line for line in reversed(lines) if "There are " in line), None)
    players_online: Optional[int] = None
    players_max: Optional[int] = None
    if last_status_line:
        match = PLAYER_STATUS_RE.search(last_status_line)
        if match:
            players_online = int(match.group("online"))
            players_max = int(match.group("max"))

    return {
        "container_exists": True,
        "container_state": state,
        "health": health,
        "players_online": players_online,
        "players_max": players_max,
        "whitelist_count": len(read_whitelist(repo_root)),
        "last_status_line": last_status_line,
        "updated_at": utcnow_iso(),
    }


def start_container() -> tuple[str, str]:
    client = get_docker_client()
    container = get_container(client)
    try:
        container.start()
        container.reload()
    except DockerException as exc:
        raise ActionError(f"Failed to start container: {exc}") from exc
    return (f"Container state: {container.status}", "")


def stop_container() -> tuple[str, str]:
    client = get_docker_client()
    container = get_container(client)
    try:
        container.stop(timeout=30)
        container.reload()
    except DockerException as exc:
        raise ActionError(f"Failed to stop container: {exc}") from exc
    return (f"Container state: {container.status}", "")


def restart_container(timeout_sec: int = _DEFAULT_RESTART_TIMEOUT_SEC) -> tuple[str, str]:
    client = get_docker_client()
    container = get_container(client)
    try:
        container.restart(timeout=30)
    except DockerException as exc:
        raise ActionError(f"Failed to restart container: {exc}") from exc

    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        try:
            container.reload()
        except DockerException as exc:
            raise ActionError(f"Failed to refresh container state: {exc}") from exc

        state = container.attrs.get("State", {}).get("Status")
        health = container.attrs.get("State", {}).get("Health", {}).get("Status", "none")
        if state == "running" and health in {"healthy", "none"}:
            return (f"Container state: {state}, health: {health}", "")
        time.sleep(_POLL_INTERVAL_SEC)

    raise ActionError("Container did not become healthy within the restart timeout")


def run_backup(repo_root: Path) -> tuple[str, str]:
    return _run_script(repo_root, "infra/backup.sh", timeout=900)


def add_player(repo_root: Path, name: str, op: bool) -> tuple[str, str]:
    args = ["infra/player.sh", "add", name]
    if op:
        args.append("--op")
    return _run_script(repo_root, *args, timeout=60)


def remove_player(repo_root: Path, name: str) -> tuple[str, str]:
    return _run_script(repo_root, "infra/player.sh", "remove", name, timeout=60)


def op_player(repo_root: Path, name: str) -> tuple[str, str]:
    return _run_script(repo_root, "infra/player.sh", "op", name, timeout=60)


def deop_player(repo_root: Path, name: str) -> tuple[str, str]:
    return _run_script(repo_root, "infra/player.sh", "deop", name, timeout=60)


def run_onboard(repo_root: Path, name: str, op: bool) -> tuple[str, str]:
    args = ["infra/onboard.sh", name]
    if op:
        args.append("--op")
    return _run_script(repo_root, *args, timeout=120)
