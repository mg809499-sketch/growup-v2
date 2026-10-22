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
    db_pool_min: int = 1
    db_pool_max: int = 10
    tenant_cache_ttl_seconds: int = 300
    root_domain: str = "growup.com"
    inventory_reservation_ttl_seconds: int = 900
    redis_url: str = ""
    r2_endpoint_url: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_catalog_bucket: str = "growup-catalog-local"
    r2_public_base_url: str = ""
    media_upload_url_ttl_seconds: int = 900
    media_max_image_bytes: int = 10 * 1024 * 1024
    media_stale_upload_seconds: int = 3600
    supabase_url: str = ""
    supabase_jwt_audience: str = "authenticated"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def supabase_jwks_url(self) -> str:
        base = self.supabase_url.rstrip("/")
        return f"{base}/auth/v1/.well-known/jwks.json"

    @property
    def supabase_issuer(self) -> str:
        base = self.supabase_url.rstrip("/")
        return f"{base}/auth/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
