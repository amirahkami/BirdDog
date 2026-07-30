from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.auth import CurrentUser, get_current_user
from app.main import app

client = TestClient(app)


def test_protected_routes_reject_anonymous_requests() -> None:
    assert client.get("/me").status_code == 401
    assert client.get("/admin/status").status_code == 401
    assert client.get("/onboarding").status_code == 401


def test_current_user_response() -> None:
    app.dependency_overrides[get_current_user] = lambda: _user({"jobseeker"})
    try:
        response = client.get("/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["username"] == "jobseeker"
    assert response.json()["roles"] == ["jobseeker"]


def test_admin_status_requires_admin_role() -> None:
    app.dependency_overrides[get_current_user] = lambda: _user({"jobseeker"})
    try:
        response = client.get("/admin/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_admin_status_reports_services(monkeypatch) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user({"admin"})
    monkeypatch.setattr("app.routers.auth.database_is_ready", lambda: True)
    monkeypatch.setattr("app.routers.auth._http_service_is_ready", lambda _: True)
    try:
        response = client.get("/admin/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "services": {
            "api": "online",
            "postgresql": "online",
            "keycloak": "online",
            "mailpit": "online",
        },
    }


def _user(roles: set[str]) -> CurrentUser:
    username = "birddog" if "admin" in roles else "jobseeker"
    return CurrentUser(
        id=uuid4(),
        subject=f"subject-{username}",
        username=username,
        email=f"{username}@birddog.local",
        display_name=username,
        roles=frozenset(roles),
    )
