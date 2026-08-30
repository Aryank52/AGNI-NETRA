import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "AGNI-NETRA"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "agni_netra_secret_key_change_in_production_2026_super_secure_key_12345"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database: Primary = PostgreSQL + PostGIS; Fallback = SQLite (TEST/DEMO)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/agninetra"
    
    # Redis & Async
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # MinIO / S3
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_USE_SSL: bool = False
    S3_BUCKET_NAME: str = "agni-netra"
    S3_BUCKET_IMAGERY: str = "agni-netra-imagery"
    S3_BUCKET_REPORTS: str = "agni-netra-reports"
    
    # Remote Sensing APIs
    FIRMS_MAP_KEY: str = ""
    FIRMS_API_URL: str = "https://firms.modaps.eosdis.nasa.gov/api/country/csv"
    
    # Machine Learning
    MODEL_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "ml", "models")
    DEFAULT_MODEL_VERSION: str = "v1.0.0"
    
    # Notifications (Optional Configurable Services)
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_FROM_EMAIL: str = "alerts@agni-netra.gov.in"
    
    SMS_ENABLED: bool = False
    SMS_PROVIDER: str = "CONSOLE"
    SMS_API_KEY: str = ""

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )


settings = Settings()
