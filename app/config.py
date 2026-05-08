from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Job API"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobs"
    redis_url: str = "redis://localhost:6379/0"

    redis_max_connections: int = 10
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5

    rate_limit_enabled: bool = True


settings = Settings()
