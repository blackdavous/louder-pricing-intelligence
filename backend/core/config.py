"""
Core Configuration
Loads and validates environment variables
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # App
    APP_NAME: str = "Louder Pricing Intelligence"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-secret-key-in-production"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]
    
    # Database
    DATABASE_URL: str = "postgresql://louder_user:louder_password@localhost:5432/louder_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Mercado Libre API
    ML_CLIENT_ID: str = ""
    ML_CLIENT_SECRET: str = ""
    ML_REDIRECT_URI: str = "http://localhost:8000/api/auth/ml/callback"
    ML_COUNTRY: str = "MX"
    ML_RATE_LIMIT_PER_HOUR: int = 5000
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_ORG_ID: str = ""
    OPENAI_MODEL_MINI: str = "gpt-4o-mini"
    OPENAI_MODEL_FULL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Scans Configuration
    MAX_COMPETITORS_PER_PRODUCT: int = 50
    MIN_SIMILARITY_SCORE: float = 0.65
    DEFAULT_TARGET_PERCENTILE: int = 50
    
    # Pricing Rules
    MIN_MARGIN_PERCENT: float = 20.0
    MAX_AUTO_PRICE_CHANGE_PERCENT: float = 10.0
    MIN_CONFIDENCE_AUTO_APPLY: int = 85
    
    # Notifications
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@louder.com"
    EMAIL_ALERTS_TO: str = ""
    SLACK_WEBHOOK_URL: str = ""
    
    # Monitoring
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
