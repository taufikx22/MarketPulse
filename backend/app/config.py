from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://marketpulse:marketpulse@localhost:5432/marketpulse"
    database_url_sync: str = "postgresql://marketpulse:marketpulse@localhost:5432/marketpulse"

    clerk_publishable_key: str = ""
    clerk_secret_key: str = ""
    clerk_jwks_url: str = ""
    clerk_webhook_secret: str = ""

    chromadb_host: str = "localhost"
    chromadb_port: int = 8000

    cors_origins: list[str] = ["http://localhost:3000"]

    staging_dir: str = "staging"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
