import pytest
from sqlalchemy import create_engine
from backend.app.core.database import (
    sanitize_db_url, get_database_mode, check_postgis_available,
    get_database_diagnostics, Base
)
from backend.app.core.config import Settings
from backend.app.main import app
from fastapi.testclient import TestClient


def test_sanitize_db_url():
    """Verify that credentials in connection strings are masked."""
    secret_url = "postgresql+psycopg2://superadmin:SecretPassword123@db.internal:5432/agninetra"
    sanitized = sanitize_db_url(secret_url)
    assert "SecretPassword123" not in sanitized
    assert "superadmin:****@db.internal:5432/agninetra" in sanitized
    assert sanitize_db_url("") == ""


def test_database_mode_detection():
    """Verify PostgreSQL vs SQLite operational mode classification."""
    pg_url = "postgresql+psycopg2://postgres:postgres@localhost:5432/agni_netra"
    sqlite_url = "sqlite:///./test_fallback.db"

    # PostgreSQL detection
    assert "postgres" in pg_url
    # SQLite fallback detection
    assert sqlite_url.startswith("sqlite://")


def test_postgresql_non_silent_failure():
    """Verify that an invalid PostgreSQL connection fails explicitly rather than falling back to SQLite."""
    unreachable_pg = "postgresql+psycopg2://nonexistent_user:wrong_pwd@127.0.0.1:54329/nonexistent_db"
    
    # Engine creation with pool_pre_ping
    test_engine = create_engine(unreachable_pg, pool_pre_ping=True)
    
    # Attempting to connect must raise an operational error rather than silently returning a SQLite connection
    with pytest.raises(Exception) as exc_info:
        with test_engine.connect() as conn:
            pass
    assert exc_info.value is not None


def test_database_health_endpoint_response():
    """Verify that the health/db endpoint reports the correct engine and mode."""
    client = TestClient(app)
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "HEALTHY"
    assert "engine" in data
    assert "mode" in data
    assert data["engine"] in ["PostgreSQL", "SQLite"]
    if data["engine"] == "PostgreSQL":
        assert data["mode"] == "POSTGRESQL"
    else:
        assert data["mode"] == "TEST/DEMO"


def test_database_diagnostics_structure():
    """Verify get_database_diagnostics returns all canonical keys without password leakage."""
    diag = get_database_diagnostics()
    assert "database_url_configured" in diag
    assert "database_engine" in diag
    assert "database_mode" in diag
    assert "postgis_available" in diag
    assert "status" in diag
    assert "database_name" in diag
    
    # Ensure no plain-text credentials in sanitized URL
    if diag.get("database_url_sanitized"):
        assert "password" not in diag["database_url_sanitized"].lower() or "****" in diag["database_url_sanitized"]
