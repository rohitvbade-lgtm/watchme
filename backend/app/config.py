from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field, AliasChoices
from functools import lru_cache
from typing import Optional, Union

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
    cors_origins: list[str] = ["http://localhost:4200", "http://localhost:8100", "https://localhost", "capacitor://localhost", "ionic://localhost"]

    # Security & Protection settings (accepts either API_SECRET_KEY or API_SECRET)
    api_secret_key: Optional[str] = Field(None, validation_alias=AliasChoices("api_secret_key", "api_secret"))
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 120
    rate_limit_search_per_minute: int = 40

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def async_database_url(self) -> str:
        """
        Normalize database URL for asyncpg and Supabase compatibility:
        - Replaces postgres:// or postgresql:// with postgresql+asyncpg://
        - Converts sslmode= to ssl= (asyncpg requirement)
        - Ensures ssl=require is applied for Supabase hosts
        """
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        
        # asyncpg expects 'ssl=require' rather than 'sslmode=require'
        if "sslmode=" in url:
            url = url.replace("sslmode=", "ssl=")
            
        # If Supabase connection and ssl param is missing, append it
        if ("supabase.co" in url or "supabase.com" in url) and "ssl=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}ssl=require"

        return url

@lru_cache
def get_settings() -> Settings:
    return Settings()

