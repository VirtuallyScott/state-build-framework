"""
Configuration settings for the Build State API service.

Database Configuration:
- DATABASE_TYPE: 'auto' (default), 'sqlite', or 'postgresql'
- DATABASE_URL: Connection string for the database

When DATABASE_TYPE='auto', the type is detected from DATABASE_URL:
- postgresql://... → PostgreSQL
- postgres://... → PostgreSQL  
- sqlite:///... → SQLite
- *.db → SQLite (fallback)
"""
import os
import secrets
from typing import List


class Settings:
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///builds.db")
    database_type: str = os.getenv("DATABASE_TYPE", "auto")  # auto, sqlite, postgresql

    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # API Keys
    api_keys: List[str] = os.getenv("API_KEYS", "dev-key-12345").split(",")

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


# Global settings instance
settings = Settings()