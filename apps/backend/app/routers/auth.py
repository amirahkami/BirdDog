from urllib.error import URLError
from urllib.request import urlopen

from fastapi import APIRouter

from app.core.auth import AdminUser, AuthenticatedUser
from app.core.config import get_settings
from app.db.session import database_is_ready
from app.schemas.auth import AdminStatusResponse, CurrentUserResponse

router = APIRouter(tags=["authentication"])
settings = get_settings()


@router.get("/me", response_model=CurrentUserResponse)
def me(user: AuthenticatedUser) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        roles=sorted(user.roles),
    )


@router.get("/admin/status", response_model=AdminStatusResponse)
def admin_status(_: AdminUser) -> AdminStatusResponse:
    services = {
        "api": "online",
        "postgresql": "online" if database_is_ready() else "unavailable",
        "keycloak": (
            "online" if _http_service_is_ready(settings.keycloak_health_url) else "unavailable"
        ),
        "mailpit": (
            "online"
            if _http_service_is_ready(f"{settings.mailpit_api_url}/readyz")
            else "unavailable"
        ),
    }
    overall = "ok" if all(value == "online" for value in services.values()) else "degraded"
    return AdminStatusResponse(status=overall, services=services)


def _http_service_is_ready(url: str) -> bool:
    try:
        with urlopen(url, timeout=2) as response:
            return response.status == 200
    except (OSError, URLError):
        return False
