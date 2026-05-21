from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="report-service", min_length=1)
    app_env: str = Field(default="development", min_length=1)
    host: str = Field(default="0.0.0.0", min_length=1)
    port: int = Field(default=8003, gt=0)
    auth_service_url: str = Field(default="http://127.0.0.1:8000", min_length=1)
    http_timeout_seconds: float = Field(default=5, gt=0)
    database_url: str = Field(
        default=(
            "postgresql+asyncpg://report_service_user:report_service_password"
            "@127.0.0.1:6434/report_service_db?prepared_statement_cache_size=0"
        ),
        min_length=1,
    )
    database_echo: bool = False
    database_pool_size: int = Field(default=5, gt=0)
    database_max_overflow: int = Field(default=10, ge=0)
    cors_allowed_origins: str = ""
    rate_limit_requests: int = Field(default=120, gt=0)
    rate_limit_window_seconds: int = Field(default=60, gt=0)
    grpc_shared_secret: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.auth_service_url = str(settings.auth_service_url).rstrip("/")
    return settings
