from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.session import database_is_ready
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse | JSONResponse:
    if not database_is_ready():
        payload = HealthResponse(status="unavailable", database="error")
        return JSONResponse(status_code=503, content=payload.model_dump())
    return HealthResponse(status="ok", database="ok")
