from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(..., min_length=1)
    app_env: str = Field(..., min_length=1)
    host: str = Field(..., min_length=1)
    port: int = Field(..., gt=0)
    auth_service_url: str = Field(..., min_length=1)
    http_timeout_seconds: float = Field(..., gt=0)
    database_url: str = Field(..., min_length=1)
    database_echo: bool
    database_pool_size: int = Field(..., gt=0)
    database_max_overflow: int = Field(..., ge=0)
    cors_allowed_origins: str = ""
    rate_limit_requests: int = Field(default=120, gt=0)
    rate_limit_window_seconds: int = Field(default=60, gt=0)
    grpc_shared_secret: str | None = None
    storage_endpoint_url: str = Field(..., min_length=1)
    storage_region: str = Field(..., min_length=1)
    storage_access_key: str = Field(..., min_length=1)
    storage_secret_key: str = Field(..., min_length=1)
    storage_bucket_name: str = Field(..., min_length=1)
    storage_public_base_url: str = Field(..., min_length=1)
    storage_path_prefix: str = Field(..., min_length=1)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.auth_service_url = str(settings.auth_service_url).rstrip("/")
    settings.storage_endpoint_url = str(settings.storage_endpoint_url).rstrip("/")
    settings.storage_public_base_url = str(settings.storage_public_base_url).rstrip("/")
    settings.storage_path_prefix = str(settings.storage_path_prefix).strip("/")
    return settings
