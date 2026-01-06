from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # App
    app_name: str = "KitchenMaster API"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql+asyncpg://kitchenmaster:kitchenmaster@localhost:5432/kitchenmaster"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Google AI / Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    imagen_model: str = "imagen-3.0-generate-002"
    
    # JWT
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
