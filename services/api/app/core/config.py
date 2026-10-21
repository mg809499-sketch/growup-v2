from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la API, cargada desde variables GROWUP_* y .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GROWUP_",
        extra="ignore",
    )

    app_name: str = "Growup API"
    environment: str = "local"
    debug: bool = False
    database_url: str = ""
    redis_url: str = ""
    supabase_url: str = ""
    supabase_jwt_audience: str = "authenticated"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
