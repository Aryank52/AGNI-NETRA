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


@router.get("/thermal/providers")
def get_thermal_providers(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Lists registered thermal observation provider adapters and their sensor characteristics.
    """
    providers = provider_registry.get_thermal_providers()
    results = []
    for p in providers:
        meta = p.get_metadata().model_dump()
        meta["current_health"] = p.get_health(db).value
        results.append(meta)
    return results


@router.get("/thermal/coverage")
def get_thermal_coverage(
    region: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns multi-constellation thermal observation coverage breakdown.
    """
    return provider_registry.get_thermal_coverage_summary(region=region)


@router.get("/thermal/health")
def get_thermal_health(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns operational health status across thermal observation provider adapters.
    """
    thermal_providers = provider_registry.get_thermal_providers()
    statuses = {}
    for p in thermal_providers:
        meta = p.get_metadata()
        statuses[meta.provider_name.upper()] = {
            "health": p.get_health(db).value,
            "availability": meta.availability.value,
            "dataset": meta.dataset_name,
            "resolution": getattr(meta, "spatial_resolution", "1km"),
            "update_frequency": getattr(meta, "update_frequency", "Orbital revisit")
        }
    return {
        "status": "OPERATIONAL",
        "thermal_providers": statuses
    }


@router.get("/events/{event_id}/sources")
def get_event_thermal_sources(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves contributing thermal observation sources and agreement metrics for a specific event.
    """
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
    from backend.app.services.intelligence.thermal_fusion import query_multi_provider_thermal_intelligence

    raw_event = JarvisToolRegistry.tool_get_event(db, event_id)
    if not raw_event or not raw_event.get("found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    lat = float(raw_event.get("latitude", 22.3039))
    lon = float(raw_event.get("longitude", 70.8022))

    fusion_res = query_multi_provider_thermal_intelligence(
        db=db,
        latitude=lat,
        longitude=lon,
        radius_km=5.0,
        event_context=raw_event
    )

    return {
        "event_id": event_id,
        "event_code": raw_event.get("event_code", event_id),
        "state": raw_event.get("state"),
        "coordinates": [lat, lon],
        "thermal_sources": fusion_res.get("contributing_providers", ["NASA_FIRMS"]),
        "source_agreement": fusion_res.get("source_agreement", "SINGLE_SOURCE"),
        "source_conflicts": fusion_res.get("source_conflicts", []),
        "observation_count": fusion_res.get("deduplicated_observation_count", 1),
        "observations": [o.model_dump() for o in fusion_res.get("observations", [])],
        "provenance_records": fusion_res.get("provenance_records", [])
    }
