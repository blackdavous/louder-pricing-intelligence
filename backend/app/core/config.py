from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Configuración de la aplicación.
    Lee variables de entorno del archivo .env
    """
    
    # Application
    PROJECT_NAME: str = "Louder Price Intelligence"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "louder-secret-key-change-in-production"
    INIT_DB_ON_STARTUP: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./louder_pricing.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False
    
    # Mercado Libre
    ML_CLIENT_ID: str = ""
    ML_CLIENT_SECRET: str = ""
    ML_REDIRECT_URI: str = "https://example.com/callback"
    ML_COUNTRY: str = "MX"
    ML_RATE_LIMIT_PER_HOUR: int = 5000
    ML_API_ENABLED: bool = False  # Enable when new API credentials are ready
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL_MINI: str = "gpt-4o-mini"
    OPENAI_MODEL_FULL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # MLflow
    MLFLOW_TRACKING_URI: str = "sqlite:///mlflow.db"
    MLFLOW_EXPERIMENT_NAME: str = "louder-pricing"
    
    # Monitoring
    ENABLE_METRICS: bool = True
    SENTRY_DSN: str = ""
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8501",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()
