from __future__ import annotations

import time


def wait_for_job(client, job_id: str, timeout: float = 2.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/api/jobs/{job_id}")
        payload = response.json()
        if payload["status"] in {"succeeded", "failed"}:
            return payload
        time.sleep(0.05)
    raise AssertionError(f"Job {job_id} did not finish in time")


def test_status_endpoint_returns_payload(client, app_module, monkeypatch):
    login = client.post("/login", data={"password": "test-password"})
    assert login.status_code == 200 or login.status_code == 303

    monkeypatch.setattr(
        app_module,
        "get_status",
        lambda repo_root: {
            "container_exists": True,
            "container_state": "running",
            "health": "healthy",
            "players_online": 1,
            "players_max": 20,
            "whitelist_count": 1,
            "last_status_line": "There are 1 of a max of 20 players online",
            "updated_at": "2026-02-28T00:00:00+00:00",
        },
    )

    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["container_state"] == "running"


def test_player_add_enqueues_job(client, app_module, monkeypatch, csrf_token):
    seen = {}

    def fake_add(repo_root, name, op):
        seen["args"] = (str(repo_root), name, op)
        return ("added", "")

    monkeypatch.setattr(app_module, "add_player", fake_add)

    response = client.post(
        "/api/players/add",
        headers={"X-CSRF-Token": csrf_token},
        json={"name": "Brock", "op": True},
    )
    assert response.status_code == 200
    payload = response.json()
    job = wait_for_job(client, payload["job_id"])
    assert job["status"] == "succeeded"
    assert seen["args"][1:] == ("Brock", True)


def test_onboard_requires_csrf(client):
    client.post("/login", data={"password": "test-password"})
    response = client.post("/api/onboard", json={"name": "Misty", "op": False})
    assert response.status_code == 403


def test_backup_enqueues_job(client, app_module, monkeypatch, csrf_token):
    monkeypatch.setattr(app_module, "run_backup", lambda repo_root: ("backup ok", ""))

    response = client.post("/api/actions/backup", headers={"X-CSRF-Token": csrf_token})
    assert response.status_code == 200
    payload = response.json()
    job = wait_for_job(client, payload["job_id"])
    assert job["status"] == "succeeded"
    assert job["stdout_tail"] == "backup ok"
