from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from backend.app.core.config import settings
from backend.app.core.database import get_db, get_database_mode, check_postgis_available, get_database_diagnostics
from backend.app.api.v1.api import api_router
from backend.app.core.storage import storage_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    description="AGNI-NETRA — AI-Powered Industrial Fire & Persistent Thermal Intelligence Platform"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Master API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def health_check():
    mode = get_database_mode()
    return {
        "status": "HEALTHY",
        "service": "AGNI-NETRA",
        "database_mode": mode,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


@app.get("/health/db", tags=["Health"])
def database_health_check(db: Session = Depends(get_db)):
    """
    Validates live database connection, response latency, and engine dialect.
    """
    start_time = time.time()
    try:
        db.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start_time) * 1000, 2)
        dialect = db.bind.dialect.name if db.bind else "sqlite"
        
        if dialect == "postgresql":
            has_postgis, postgis_ver = check_postgis_available(db)
            return {
                "status": "HEALTHY",
                "database": "CONNECTED",
                "engine": "PostgreSQL",
                "spatial": "PostGIS" if has_postgis else "UNAVAILABLE",
                "mode": "POSTGRESQL",
                "postgis_version": postgis_ver,
                "latency_ms": latency_ms
            }
        else:
            return {
                "status": "HEALTHY",
                "database": "CONNECTED",
                "engine": "SQLite",
                "spatial": "SHAPELY_FALLBACK",
                "mode": "TEST/DEMO",
                "latency_ms": latency_ms
            }
    except Exception as e:
        return {
            "status": "UNHEALTHY",
            "database": "FAILED",
            "mode": get_database_mode(),
            "detail": str(e)
        }


@app.get("/health/storage", tags=["Health"])
def storage_health_check():
    return storage_service.check_health()
