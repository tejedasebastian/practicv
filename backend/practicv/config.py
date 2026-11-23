from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the PractiCV API."""

    app_name: str = "PractiCV"
    environment: str = "local"
    version: str = "0.2.1"
    database_url: str = "postgresql+psycopg://practicv:practicv@localhost:5434/practicv"
    frontend_origin: str = "http://localhost:3000"
    mcp_enabled: bool = True
    mcp_server_path: str | None = None
    mcp_fixture_dir: str | None = None
    url_capture_user_agent: str = "PractiCV/0.1.0 (+https://github.com/kuki236/practicv)"
    practilizate_enabled: bool = False
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/api/v1/email/oauth/google/callback"
    google_oauth_scopes: str = "https://www.googleapis.com/auth/gmail.readonly"

    model_config = SettingsConfigDict(
        env_prefix="PRACTICV_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
