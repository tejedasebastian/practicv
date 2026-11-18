from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the PractiCV API."""

    app_name: str = "PractiCV"
    environment: str = "local"
    version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://practicv:practicv@localhost:5434/practicv"
    frontend_origin: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_prefix="PRACTICV_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
