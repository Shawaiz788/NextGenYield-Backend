from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    PROJECT_NAME: str = "NextGenYield Backend"
    API_V1_STR: str = "/api/v1"
    
    # Database URL: Direct PostgreSQL (e.g. Supabase) or local fallback SQLite
    DATABASE_URL: str = "sqlite:///./nextgenyield.db"
    
    # Supabase Settings (for Storage and client operations)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_BUCKET_NAME: str = "field-observations"
    
    # Authentication & Security
    SECRET_KEY: str = "nextgenyield_super_secure_jwt_secret_change_in_production_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days for mobile farmer convenience
    
    # CORS Origins (Allow Expo development client, Web, and mobile emulators)
    CORS_ORIGINS: List[str] = ["*"]
    
    # Model Inference Service Gateway (Dedicated PyTorch FoMo4Wheat ViT-B/14 service)
    AI_INFERENCE_SERVICE_URL: Optional[str] = "https://duykd-202-1-27-175.run.pinggy-free.link"

settings = Settings()
