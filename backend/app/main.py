from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.api.v1.api import api_router
from backend.app.core.storage import storage_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    description="AGNI-NETRA — AI Geospatial Network for Industrial Thermal Risk & Anomaly Analysis (SIH26162)"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Master API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "HEALTHY",
        "service": "AGNI-NETRA",
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
        return {
            "status": "HEALTHY",
            "database": "Connected",
            "dialect": db.bind.dialect.name if db.bind else "sqlite",
            "latency_ms": latency_ms
        }
    except Exception as e:
        return {
            "status": "UNHEALTHY",
            "database": "Error",
            "detail": str(e)
        }


@app.get("/health/storage", tags=["Health"])
def storage_health_check():
    return storage_service.check_health()
