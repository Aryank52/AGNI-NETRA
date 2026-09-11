"""
AGNI-NETRA Phase 6: Intelligence Providers & Coverage API Endpoints
Provides machine-readable discovery, metadata, health status, and geographic reach
for all intelligence providers with RBAC masking for PUBLIC users.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_optional_current_user
from backend.app.models.domain import User
from backend.app.services.intelligence.provider_registry import provider_registry
from backend.app.services.intelligence.profiles import IndiaIntelligenceProfile, GlobalIntelligenceProfile

router = APIRouter()


@router.get("/providers", response_model=List[Dict[str, Any]])
def list_intelligence_providers(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Lists registered provider adapters and their capabilities.
    Restricts internal diagnostic metadata for PUBLIC users.
    """
    user_role = current_user.role if current_user else "PUBLIC"
    providers = provider_registry.list_providers(role=user_role)
    return providers


@router.get("/providers/{provider_name}")
def get_provider_details(
    provider_name: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves detailed metadata for a specific intelligence provider adapter.
    """
    user_role = current_user.role if current_user else "PUBLIC"
    provider = provider_registry.get_provider(provider_name)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intelligence provider '{provider_name}' is not registered."
        )

    meta = provider.get_metadata().model_dump()
    if user_role == "PUBLIC":
        meta["source_provenance"] = "Authoritative Satellite / Official Public Catalog"

    health = provider.get_health(db)
    meta["current_health"] = health.value
    return meta


@router.get("/coverage")
def get_geographic_coverage_summary(
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns factual geographic intelligence coverage across profiles.
    Does NOT claim global coverage that does not exist.
    """
    summary = provider_registry.get_coverage_summary()
    summary["india_profile"] = IndiaIntelligenceProfile.get_profile().model_dump()
    summary["global_profile_scaffolding"] = GlobalIntelligenceProfile.get_profile().model_dump()
    return summary


@router.get("/health")
def get_providers_health(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Lightweight operational status check across all registered provider adapters.
    """
    return provider_registry.get_provider_health_summary(db)
