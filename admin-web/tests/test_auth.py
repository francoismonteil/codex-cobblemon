from __future__ import annotations

from app import auth


def test_verify_password_accepts_correct_secret():
    assert auth.verify_password("secret", "secret") is True
    assert auth.verify_password("secret", "other") is False


def test_login_required_for_api(client):
    response = client.get("/api/status")
    assert response.status_code == 401


def test_login_success_redirects_to_dashboard(client):
    response = client.post("/login", data={"password": "test-password"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_login_failure_returns_unauthorized(client):
    response = client.post("/login", data={"password": "wrong"})
    assert response.status_code == 401
    assert "Mot de passe invalide" in response.text
