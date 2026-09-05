import os
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

# Explicitly load .env from project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH, override=True)
else:
    load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "AGNI-NETRA"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "agni_netra_secret_key_change_in_production_2026_super_secure_key_12345"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Production PostgreSQL + PostGIS Connection Pooling
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/agni_netra")
    DB_POOL_SIZE: int = 15
    DB_MAX_OVERFLOW: int = 25
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
    # Redis & Celery Async Workers
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Object Storage (MinIO / AWS S3)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_USE_SSL: bool = False
    S3_BUCKET_NAME: str = "agni-netra"
    S3_BUCKET_IMAGERY: str = "agni-netra-imagery"
    S3_BUCKET_REPORTS: str = "agni-netra-reports"
    
    # Remote Sensing & Satellite Ingestion APIs
    FIRMS_MAP_KEY: str = os.getenv("FIRMS_MAP_KEY", "")
    FIRMS_API_URL: str = "https://firms.modaps.eosdis.nasa.gov/api/country/csv"
    
    # Machine Learning Governance & Models
    MODEL_DIR: str = os.path.join(ROOT_DIR, "ml", "models")
    DEFAULT_MODEL_VERSION: str = "xgb-v3.0-real-candidate"
    
    # Security, Rate Limiting & Tracing
    RATE_LIMIT_PER_MINUTE: int = 600
    CORRELATION_ID_HEADER: str = "X-Correlation-ID"
    
    # Phase 13 Controlled Dispatch Safety Gate
    # Live automated dispatches remain strictly DISABLED throughout Phase 13
    ENABLE_OPERATIONAL_DISPATCH_GATE: bool = False
    IS_OPERATIONAL_DISPATCH_DEFAULT: bool = False
    
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

    # CORS Allowed Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://agni-netra.vercel.app"
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("["):
                try:
                    import json
                    return json.loads(v_str)
                except Exception:
                    pass
            return [i.strip() for i in v_str.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        
        # Check alternate env var CORS_ORIGINS if passed
        alt = os.getenv("CORS_ORIGINS")
        if alt:
            return [i.strip() for i in alt.split(",") if i.strip()]
            
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "https://agni-netra.vercel.app"
        ]

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=ENV_PATH if os.path.exists(ENV_PATH) else ".env",
        env_file_encoding="utf-8",
        extra="allow"
    )

    def get_sanitized_dict(self) -> Dict[str, Any]:
        """
        Returns production-safe configuration parameters with all passwords,
        keys, and connection credentials masked to prevent leakage in logs/APIs.
        """
        raw = self.model_dump()
        sanitized = {}
        sensitive_keys = {"SECRET_KEY", "DATABASE_URL", "S3_ACCESS_KEY", "S3_SECRET_KEY",
                          "FIRMS_MAP_KEY", "SMTP_PASSWORD", "SMS_API_KEY"}

        for k, v in raw.items():
            if k in sensitive_keys and v:
                if k == "DATABASE_URL":
                    sanitized[k] = re.sub(r":([^@/]+)@", r":****@", str(v))
                else:
                    sanitized[k] = f"{str(v)[:4]}****" if len(str(v)) > 8 else "****"
            else:
                sanitized[k] = v
        return sanitized


settings = Settings()
