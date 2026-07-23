from functools import lru_cache

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

    model_config = SettingsConfigDict(extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
