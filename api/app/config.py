from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # postgresql://hk_api.<project-ref>:<heslo>@<pooler-host>:5432/postgres?sslmode=require
    database_url: str = ""
    cors_origins: str = "http://localhost:5173"
    public_app_url: str = "http://localhost:5173"
    calc_log_enabled: bool = True
    rate_limit: str = "300/minute"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def db_configured(self) -> bool:
        return bool(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
