from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BirdDog API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://birddog:birddog@db:5432/birddog"
    schedule_cron: str = "0 17 * * *"
    timezone: str = "Europe/Berlin"
    log_level: str = "INFO"
    keycloak_issuer: str = "http://auth.localhost:22080/realms/birddog"
    keycloak_jwks_url: str = (
        "http://keycloak:22080/realms/birddog/protocol/openid-connect/certs"
    )
    keycloak_audience: str = "birddog-api"
    keycloak_health_url: str = "http://keycloak:9000/health/ready"
    mailpit_api_url: str = "http://mailpit:8025"
    cv_storage_path: str = "/data/cvs"
    cv_max_bytes: int = Field(default=25 * 1024 * 1024, ge=1)
    cv_max_pages: int = Field(default=50, ge=1, le=500)
    cv_ocr_timeout_seconds: int = Field(default=120, ge=5, le=900)
    cv_ocr_dpi: int = Field(default=200, ge=100, le=400)
    cv_worker_interval_seconds: int = Field(default=2, ge=1, le=300)
    cv_facts_worker_interval_seconds: int = Field(default=5, ge=1, le=300)

    ki_connect_base_url: str = "https://chat.kiconnect.nrw/api/v1"
    ki_connect_api_key: str = ""
    ki_connect_model: str = "ki.inferenz.nrw-mistralai-mistral-small-4-119b-2603"
    ki_connect_timeout_seconds: int = Field(default=120, ge=5, le=600)

    model_config = SettingsConfigDict(extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
