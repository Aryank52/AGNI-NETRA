import pytest
from datetime import timedelta
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.services.spatial_engine import haversine_distance_m, lookup_state


def test_password_hashing():
    pwd = "AgniNetraSecurePassword123"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_creation():
    user_id = "test-user-uuid-123"
    role = "ANALYST"
    token = create_access_token(subject=user_id, role=role, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)
    assert len(token.split(".")) == 3  # Header.Payload.Signature


def test_spatial_calculations():
    # Mumbai to Delhi distance (~1150 km)
    mumbai = (19.0760, 72.8777)
    delhi = (28.7041, 77.1025)
    dist_m = haversine_distance_m(mumbai[0], mumbai[1], delhi[0], delhi[1])
    assert 1100000 < dist_m < 1200000

    # State containment lookup
    state_gj = lookup_state(22.35, 69.86)  # Jamnagar
    assert state_gj == "Gujarat"

    state_pb = lookup_state(30.24, 75.84)  # Sangrur
    assert state_pb == "Punjab"
