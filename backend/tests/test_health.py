"""Scaffold check: the PreventVital app starts and reports a non-diagnostic disclaimer."""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_ok() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "preventvital"
    assert "not a diagnostic" in body["disclaimer"].lower()
