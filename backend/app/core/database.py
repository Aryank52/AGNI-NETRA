import os
import re
from typing import Dict, Any, Tuple, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings


# 1. Determine Database Engine and Operational Mode
raw_db_url = (settings.DATABASE_URL or "").strip()

if not raw_db_url:
    # Explicit fallback only when DATABASE_URL is completely unset
    DATABASE_URL = "sqlite:///./agni_netra.db"
    DATABASE_MODE = "SQLITE_TEST"
elif raw_db_url.startswith("postgresql://") or raw_db_url.startswith("postgres://") or raw_db_url.startswith("postgresql+"):
    DATABASE_URL = raw_db_url
    DATABASE_MODE = "POSTGRESQL"
elif raw_db_url.startswith("sqlite://"):
    DATABASE_URL = raw_db_url
    DATABASE_MODE = "SQLITE_TEST"
else:
    # Any other configured URL
    DATABASE_URL = raw_db_url
    DATABASE_MODE = "POSTGRESQL" if "postgres" in raw_db_url else "SQLITE_TEST"

IS_POSTGRESQL = (DATABASE_MODE == "POSTGRESQL")
IS_SQLITE_TEST = (DATABASE_MODE == "SQLITE_TEST")


# 2. Configure Engine with Strict Operational Parameters
connect_args = {}
engine_kwargs: Dict[str, Any] = {"pool_pre_ping": True}

if IS_SQLITE_TEST:
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
else:
    # Production PostgreSQL + PostGIS connection pooling
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 1800


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


# 3. Helper Utilities for Sanitization & Diagnostics

def sanitize_db_url(url: str) -> str:
    """Removes sensitive passwords from connection strings for safe logging."""
    if not url:
        return ""
    return re.sub(r":([^@/]+)@", r":****@", url)


def get_database_mode() -> str:
    """Returns the authoritative active database mode: POSTGRESQL or SQLITE_TEST."""
    return DATABASE_MODE


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
        "connection_error": None
    }

    try:
        with SessionLocal() as session:
            version_row = session.execute(text("SELECT version();" if IS_POSTGRESQL else "SELECT sqlite_version();")).scalar()
            diag["database_version"] = str(version_row)
            diag["status"] = "CONNECTED"

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


# 4. FastAPI Dependency Injection
def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
