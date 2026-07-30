from fastapi import FastAPI

from app.core.config import get_settings
from app.routers.auth import router as auth_router
from app.routers.onboarding import router as onboarding_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.include_router(auth_router)
app.include_router(onboarding_router)
