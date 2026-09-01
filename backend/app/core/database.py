import os
import re
import time
from typing import Dict, Any, Tuple, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings


# 1. Helper Utilities (Defined First to Guarantee Availability in Exception Handlers)

def sanitize_db_url(url: str) -> str:
    """Removes sensitive passwords from connection strings for safe logging and diagnostics."""
    if not url:
        return ""
    cleaned = url
    while cleaned.startswith("DATABASE_URL="):
        cleaned = cleaned[len("DATABASE_URL="):].strip()
    return re.sub(r":([^@/]+)@", r":****@", cleaned)


def normalize_db_url(url: str) -> str:
    """Cleans up and normalizes database connection strings."""
    if not url:
        return ""
    cleaned = url.strip()
    while cleaned.startswith("DATABASE_URL="):
        cleaned = cleaned[len("DATABASE_URL="):].strip()
    return cleaned


# 2. Determine Database Engine and Operational Mode
raw_db_url = normalize_db_url(settings.DATABASE_URL or "")

if not raw_db_url:
    DATABASE_URL = "sqlite:///./agni_netra.db"
    DATABASE_MODE = "SQLITE_TEST"
elif raw_db_url.startswith("postgresql://") or raw_db_url.startswith("postgres://") or raw_db_url.startswith("postgresql+"):
    DATABASE_URL = raw_db_url
    DATABASE_MODE = "POSTGRESQL"
elif raw_db_url.startswith("sqlite://"):
    DATABASE_URL = raw_db_url
    DATABASE_MODE = "SQLITE_TEST"
else:
    DATABASE_URL = raw_db_url
    DATABASE_MODE = "POSTGRESQL" if "postgres" in raw_db_url else "SQLITE_TEST"

IS_POSTGRESQL = (DATABASE_MODE == "POSTGRESQL")
IS_SQLITE_TEST = (DATABASE_MODE == "SQLITE_TEST")


# 3. Configure Engine with Strict Production Operational Parameters
connect_args = {}
engine_kwargs: Dict[str, Any] = {"pool_pre_ping": True}

if IS_SQLITE_TEST:
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
else:
    # Production PostgreSQL + PostGIS Connection Pool
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT
    engine_kwargs["pool_recycle"] = settings.DB_POOL_RECYCLE


try:
    engine = create_engine(DATABASE_URL, **engine_kwargs)
except Exception as e:
    if IS_POSTGRESQL:
        raise RuntimeError(
            f"Database Configuration Error: Failed to initialize PostgreSQL engine with URL '{sanitize_db_url(DATABASE_URL)}'. "
            f"Error: {e}. AGNI-NETRA does not silently switch to SQLite when PostgreSQL is configured."
        ) from e
    raise e


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# 4. Diagnostics & Connection Pool Reporting

def get_database_mode() -> str:
    """Returns the authoritative active database mode: POSTGRESQL or SQLITE_TEST."""
    return DATABASE_MODE


def get_connection_pool_stats() -> Dict[str, Any]:
    """
    Returns real-time connection pool telemetry for production monitoring.
    """
    if IS_SQLITE_TEST:
        return {
            "engine": "SQLite",
            "mode": "SQLITE_TEST",
            "pool_size": 1,
            "checked_in": 1,
            "checked_out": 0,
            "overflow": 0
        }
    
    pool = engine.pool
    return {
        "engine": "PostgreSQL",
        "mode": "POSTGRESQL",
        "pool_size": pool.size(),
        "checked_in_connections": pool.checkedin(),
        "checked_out_connections": pool.checkedout(),
        "overflow_connections": pool.overflow(),
        "pool_timeout_seconds": settings.DB_POOL_TIMEOUT,
        "pool_recycle_seconds": settings.DB_POOL_RECYCLE
    }


def check_postgis_available(db_session: Optional[Session] = None) -> Tuple[bool, Optional[str]]:
    """
    Validates whether the PostGIS spatial extension is enabled and responsive.
    Returns (is_available, version_or_error_message).
    """
    if IS_SQLITE_TEST:
        return False, "Not applicable (SQLite TEST/DEMO Fallback Mode)"

    session_created = False
    if db_session is None:
        db_session = SessionLocal()
        session_created = True

    try:
        result = db_session.execute(text("SELECT PostGIS_Version();")).scalar()
        return True, str(result)
    except Exception as e:
        return False, f"PostGIS unavailable: {str(e)}"
    finally:
        if session_created:
            db_session.close()


def get_database_diagnostics() -> Dict[str, Any]:
    """
    Comprehensive diagnostic reporting without exposing secrets.
    """
    sanitized = sanitize_db_url(DATABASE_URL)
    is_configured = bool(settings.DATABASE_URL)
    db_name = "agni_netra.db" if IS_SQLITE_TEST else DATABASE_URL.split("/")[-1].split("?")[0]
    
    diag: Dict[str, Any] = {
        "database_url_configured": is_configured,
        "database_url_sanitized": sanitized,
        "database_engine": "PostgreSQL" if IS_POSTGRESQL else "SQLite",
        "database_mode": DATABASE_MODE,
        "database_name": db_name,
        "status": "UNKNOWN",
        "postgis_available": False,
        "postgis_version": None,
        "database_version": None,
        "connection_error": None,
        "pool_stats": get_connection_pool_stats()
    }

    try:
        with SessionLocal() as session:
            t0 = time.perf_counter()
            version_row = session.execute(text("SELECT version();" if IS_POSTGRESQL else "SELECT sqlite_version();")).scalar()
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            diag["database_version"] = str(version_row)
            diag["status"] = "CONNECTED"
            diag["ping_latency_ms"] = latency_ms

            if IS_POSTGRESQL:
                has_postgis, postgis_ver = check_postgis_available(session)
                diag["postgis_available"] = has_postgis
                diag["postgis_version"] = postgis_ver
    except Exception as e:
        diag["status"] = "FAILED"
        diag["connection_error"] = str(e)
        if IS_POSTGRESQL:
            diag["connection_error"] = (
                f"PostgreSQL connection failed: {e}. "
                "Ensure PostgreSQL daemon is running, PostGIS is installed, and DATABASE_URL is reachable."
            )

    return diag


# 5. FastAPI Dependency Injection
def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
