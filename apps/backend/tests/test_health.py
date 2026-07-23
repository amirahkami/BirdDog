from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_when_database_is_ready(monkeypatch) -> None:
    monkeypatch.setattr("app.routers.health.database_is_ready", lambda: True)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_when_database_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr("app.routers.health.database_is_ready", lambda: False)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "error"}
