from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class CurrentUserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    display_name: str | None
    roles: list[str]


class AdminStatusResponse(BaseModel):
    status: Literal["ok", "degraded"]
    services: dict[str, Literal["online", "unavailable"]]
