from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def app_module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("MC_ADMIN_WEB_PASSWORD", "test-password")
    monkeypatch.setenv("MC_ADMIN_WEB_SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("MC_ADMIN_WEB_REPO_ROOT", str(tmp_path))
    monkeypatch.setenv("MC_ADMIN_WEB_JOB_HISTORY", "10")

    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "whitelist.json").write_text(json.dumps([{"name": "Ash"}]), encoding="utf-8")

    if "app.main" in sys.modules:
        module = importlib.reload(sys.modules["app.main"])
    else:
        module = importlib.import_module("app.main")
    return module


@pytest.fixture()
def client(app_module):
    with TestClient(app_module.app) as test_client:
        yield test_client


def login(client: TestClient, password: str = "test-password"):
    response = client.post("/login", data={"password": password}, follow_redirects=False)
    return response


def extract_csrf_token(client: TestClient) -> str:
    response = client.get("/")
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', response.text)
    assert match
    return match.group(1)


@pytest.fixture()
def csrf_token(client: TestClient) -> str:
    client.post("/login", data={"password": "test-password"})
    return extract_csrf_token(client)
