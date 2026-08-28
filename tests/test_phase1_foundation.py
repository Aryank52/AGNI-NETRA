import os
import sys
import pytest
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.core.database import SessionLocal, engine
from backend.app.core.storage import storage_service
from backend.app.tasks.maintenance_tasks import system_heartbeat
from backend.app.models.domain import User, ThermalEvent
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_phase1_config_and_env():
    """Verify settings loaded properly from environment"""
    assert settings.PROJECT_NAME == "AGNI-NETRA"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.SECRET_KEY is not None


def test_phase1_database_connectivity():
    """Verify database connection and schema access"""
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        assert user_count >= 0
    finally:
        db.close()


def test_phase1_health_endpoints():
    """Verify all health endpoints return 200 and healthy status"""
    r_api = client.get("/health")
    assert r_api.status_code == 200
    assert r_api.json()["status"] == "HEALTHY"

    r_db = client.get("/health/db")
    assert r_db.status_code == 200
    assert r_db.json()["status"] == "HEALTHY"

    r_store = client.get("/health/storage")
    assert r_store.status_code == 200
    assert r_store.json()["status"] == "HEALTHY"


def test_phase1_security_jwt_rbac():
    """Verify password hashing, token encoding, and role payload preservation"""
    raw_pwd = "P1SecurePassword2026!"
    hashed = get_password_hash(raw_pwd)
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

    for role in ["PUBLIC", "RESEARCHER", "INDUSTRY", "ANALYST", "AGENCY", "ADMIN"]:
        token = create_access_token(subject="user_123", role=role)
        assert token is not None
        assert len(token.split(".")) == 3


def test_phase1_celery_task_execution():
    """Verify Celery task executes and returns worker health status"""
    res = system_heartbeat()
    assert res["status"] == "HEALTHY"
    assert res["worker"] == "agni_netra_celery_worker"


def test_phase1_minio_storage():
    """Verify MinIO object storage service client"""
    health = storage_service.check_health()
    assert health["status"] == "HEALTHY"
    assert health["service"] == "MinIO S3 Object Storage"
    url = storage_service.save_file("test/doc.pdf", b"%PDF-1.4 test")
    assert url is not None
    assert "doc.pdf" in url


def test_phase1_auth_api_flow():
    """Verify user registration, login, and profile retrieval via REST API"""
    test_email = f"phase1_test_{int(datetime.now(timezone.utc).timestamp())}@agni.gov.in"
    reg_payload = {
        "email": test_email,
        "password": "Phase1TestPassword123!",
        "full_name": "Test Inspector",
        "organization": "Pollution Control Board",
        "role": "ANALYST"
    }
    
    # 1. Register
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 200
    user_data = reg_resp.json()
    assert user_data["email"] == test_email
    assert user_data["role"] == "ANALYST"

    # 2. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": test_email, "password": "Phase1TestPassword123!"}
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Get profile (/auth/me)
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == test_email
