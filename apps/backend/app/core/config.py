from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BirdDog API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://birddog:birddog@db:5432/birddog"
    schedule_cron: str = "0 17 * * *"
    timezone: str = "Europe/Berlin"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
