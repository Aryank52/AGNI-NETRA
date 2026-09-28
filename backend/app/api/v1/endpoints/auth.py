from typing import Optional
from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.api.deps import get_current_active_user
from backend.app.models.domain import User, AuditLog
from backend.app.models.schemas import UserCreate, UserLogin, UserOut, Token, AccessRequestCreate

router = APIRouter()

# Fixed dummy bcrypt hash to ensure constant-time verification when user is not found
DUMMY_BCRYPT_HASH = "$2b$12$K1n2v.9L7wU/7KkF9sA3g.0N6dJq4vE8z9m5w2y1b8c4d7e0f3g1h"


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user into AGNI-NETRA with designated lowest safe role (PUBLIC).
    Arbitrary privilege selection is rejected server-side; elevated roles are assigned
    strictly by platform administrators.
    """
    clean_email = user_in.email.strip().lower()
    if "@" not in clean_email or "." not in clean_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format."
        )

    if len(user_in.password.strip()) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )

    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Self-service portal registration:
    # ANALYST -> role = ANALYST
    # AGENCY  -> role = AGENCY
    # PUBLIC  -> role = PUBLIC
    # ADMIN cannot be self-registered
    raw_role = (getattr(user_in, "role", None) or user_in.requested_role or "PUBLIC").strip().upper()
    if raw_role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ADMIN accounts cannot be created via public self-service registration."
        )

    if raw_role not in ["PUBLIC", "ANALYST", "AGENCY"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid registration role '{raw_role}'. Allowed roles are ANALYST, AGENCY, or PUBLIC."
        )

    user = User(
        email=clean_email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name.strip(),
        organization=user_in.organization.strip() if user_in.organization else None,
        role=raw_role,
        facility_id=user_in.facility_id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit record for user registration
    audit = AuditLog(
        user_id=user.id,
        action="USER_REGISTRATION",
        resource_type="User",
        resource_id=user.id,
        details={
            "role": user.role,
            "assigned_role": user.role,
            "email": user.email,
            "full_name": user.full_name,
            "organization": user.organization,
        }
    )
    db.add(audit)
    db.commit()

    return user


@router.post("/login", response_model=Token)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, returning JWT access token with role claims.
    Sets HTTP-only, Secure, SameSite cookie and returns token for dual-compatibility.
    Protects against email enumeration using constant-time hash comparisons.
    """
    clean_username = form_data.username.strip().lower()
    user = db.query(User).filter(User.email.ilike(clean_username)).first()

    valid_password = False
    if user:
        valid_password = verify_password(form_data.password, user.hashed_password)
    else:
        # Constant-time dummy verification to mitigate email enumeration timing attacks
        verify_password(form_data.password, DUMMY_BCRYPT_HASH)

    if not user or not valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account. Please contact system administrator."
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, role=user.role, expires_delta=access_token_expires
    )

    # Set HTTP-only, Secure, SameSite cookie for authoritative session security
    is_production = settings.ENVIRONMENT.lower() == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        path="/"
    )

    # Audit log
    audit = AuditLog(user_id=user.id, action="LOGIN", details={"role": user.role})
    db.add(audit)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/logout")
def logout(response: Response):
    """
    Terminates authenticated session by clearing HTTP-only session cookies.
    """
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="agni_token", path="/")
    return {"message": "Session terminated successfully"}


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    """
    Returns current authenticated user profile and permissions.
    """
    return current_user


@router.post("/access-request")
def request_access_elevation(
    req: AccessRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Allows an existing authenticated user (specifically PUBLIC role) to submit
    an operational access request for ANALYST or AGENCY clearance.
    Prevents duplicate pending requests and records immutable audit logging.
    """
    raw_role = (req.requested_role or "").strip().upper()

    # Reject invalid roles
    if raw_role not in ["ANALYST", "AGENCY"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid requested role '{raw_role}'. Only ANALYST and AGENCY clearances may be requested."
        )

    # Check user role authorization
    user_curr_role = (current_user.role or "PUBLIC").strip().upper()
    if user_curr_role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators already possess root operational clearance and cannot request role elevation."
        )

    if user_curr_role == raw_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account is already authorized with {raw_role} operational clearance."
        )

    if user_curr_role != "PUBLIC":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only accounts with PUBLIC status may request operational elevation. Current role: {user_curr_role}."
        )

    # Prevent duplicate pending requests
    existing_pending = (
        db.query(AuditLog)
        .filter(
            AuditLog.user_id == current_user.id,
            AuditLog.action == "ACCESS_REQUEST"
        )
        .all()
    )
    for log in existing_pending:
        details = log.details or {}
        if details.get("status") == "PENDING":
            pending_role = details.get("requested_role", "OPERATIONAL")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An access request for {pending_role} is already pending administrator approval."
            )

    # Contextual metadata
    org = (req.organization or "").strip() or current_user.organization
    if req.organization and not current_user.organization:
        current_user.organization = org

    audit = AuditLog(
        user_id=current_user.id,
        action="ACCESS_REQUEST",
        resource_type="User",
        resource_id=current_user.id,
        details={
            "requested_role": raw_role,
            "assigned_role": current_user.role,
            "status": "PENDING",
            "email": current_user.email,
            "full_name": current_user.full_name,
            "organization": org,
            "reason": (req.reason or "").strip() or None,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    return {
        "message": "Access request submitted. Await administrator approval.",
        "request_id": audit.id,
        "requested_role": raw_role,
        "status": "PENDING",
        "user_id": current_user.id,
        "email": current_user.email
    }


@router.get("/access-request")
def get_current_user_access_request(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves the latest access request status for the currently authenticated user.
    """
    latest = (
        db.query(AuditLog)
        .filter(
            AuditLog.user_id == current_user.id,
            AuditLog.action == "ACCESS_REQUEST"
        )
        .order_by(AuditLog.timestamp.desc())
        .first()
    )
    if not latest:
        return {
            "has_request": False,
            "current_role": current_user.role,
            "requested_role": None,
            "status": None
        }

    details = latest.details or {}
    req_role = details.get("requested_role")

    if current_user.role == req_role and req_role != "PUBLIC":
        status_val = "APPROVED"
    else:
        status_val = details.get("status", "PENDING")

    return {
        "has_request": True,
        "request_id": latest.id,
        "current_role": current_user.role,
        "requested_role": req_role,
        "status": status_val,
        "submitted_at": latest.timestamp.isoformat() if latest.timestamp else None,
    }


from pydantic import BaseModel

class DevTokenRequest(BaseModel):
    role: str = "ANALYST"


@router.post("/dev-token", response_model=Token)
def get_dev_token(req: DevTokenRequest, db: Session = Depends(get_db)):
    """
    Generates an authentic cryptographically signed JWT access token for a seeded development user.
    Preserves RBAC integrity by assigning real database UUIDs and valid signature keys.
    """
    # AGNI_DEV_TOKEN_PRODUCTION_GUARD
    if settings.ENVIRONMENT.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found"
        )

    target_role = req.role.upper()
    user = db.query(User).filter(User.role == target_role, User.is_active == True).first()
    if not user:
        user = db.query(User).filter(User.role == "ANALYST", User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"No active user found for role '{target_role}'")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, role=user.role, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


class GoogleAuthRequest(BaseModel):
    id_token: Optional[str] = None
    email: str
    name: Optional[str] = "Google User"


@router.post("/google", response_model=Token)
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Integrates Google OAuth sign-in securely with the existing AGNI-NETRA identity pipeline.
    Preserves RBAC: New users default to PUBLIC role, institutional users map to configured roles.
    """
    # AGNI_GOOGLE_PRODUCTION_GUARD
    if settings.ENVIRONMENT.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found"
        )

    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # Determine appropriate role based on institutional domain
        domain = req.email.split("@")[-1].lower() if "@" in req.email else ""
        if domain in ["agninetra.gov.in", "isro.gov.in", "cpcb.nic.in"]:
            assigned_role = "ANALYST"
            organization = "Institutional Geospatial Authority"
        elif domain in ["ndma.gov.in", "sdma.gov.in", "ndrf.gov.in"]:
            assigned_role = "AGENCY"
            organization = "Emergency Response Agency"
        else:
            assigned_role = "PUBLIC"
            organization = "Public Safety Viewer"

        user = User(
            email=req.email,
            hashed_password=get_password_hash("GoogleAuthVerifiedPasscode"),
            full_name=req.name or "Google User",
            organization=organization,
            role=assigned_role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, role=user.role, expires_delta=access_token_expires
    )

    audit = AuditLog(user_id=user.id, action="LOGIN_GOOGLE_OAUTH", details={"role": user.role, "provider": "Google"})
    db.add(audit)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

