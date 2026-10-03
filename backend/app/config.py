from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    database_url: str = "postgresql+asyncpg://watchme:watchme@localhost:5432/watchme"
    tmdb_api_key: str = ""
    tmdb_base_url: str = "https://api.tmdb.org/3"
    tmdb_image_base_url: str = "https://image.tmdb.org/t/p/w500"
    
    groq_api_key: Optional[str] = None
    groq_model: str = "qwen/qwen3.8-27b"
    
    fcm_credentials_path: Optional[str] = None
    
    notification_interval_seconds: int = 3600
    debug: bool = False
    
    app_name: str = "WatchMe"
    cors_origins: list[str] = ["http://localhost:4200", "http://localhost:8100", "capacitor://localhost", "ionic://localhost"]

@lru_cache
def get_settings() -> Settings:
    return Settings()
