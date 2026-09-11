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
from backend.app.services.intelligence.profiles import IndiaIntelligenceProfile, GlobalIntelligenceProfile, GlobalContextProfile
from backend.app.services.intelligence.context_engine import context_engine

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


@router.get("/context/providers")
def get_context_providers(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Lists registered contextual intelligence providers across all 7 domains:
    Facilities, Power, Mining, Land Cover, Protected Areas, Administrative, Environmental.
    """
    providers = provider_registry.get_context_providers()
    results = []
    for p in providers:
        meta = p.get_metadata().model_dump()
        meta["current_health"] = p.get_health(db).value
        results.append(meta)
    return results


@router.get("/context/coverage")
def get_context_coverage(
    region: Optional[str] = "GLOBAL",
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns multi-domain contextual intelligence coverage breakdown across the 7 domains.
    Truthfully reports AVAILABLE, PARTIAL, and NOT_CONFIGURED without fabricating global sources.
    """
    return provider_registry.get_context_coverage_summary(region=region or "GLOBAL")


@router.get("/context/health")
def get_context_health(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns operational health status across registered contextual intelligence providers.
    """
    context_providers = provider_registry.get_context_providers()
    statuses = {}
    for p in context_providers:
        meta = p.get_metadata()
        statuses[meta.provider_name.upper()] = {
            "health": p.get_health(db).value,
            "availability": meta.availability.value,
            "dataset": meta.dataset_name,
            "domain": getattr(meta, "category", "CONTEXT"),
            "geographic_reach": getattr(meta, "geographic_reach", "India Operational")
        }
    return {
        "status": "OPERATIONAL",
        "total_context_providers": len(context_providers),
        "context_providers": statuses
    }


@router.get("/events/{event_id}/context")
def get_event_context(
    event_id: str,
    buffer_meters: Optional[int] = 5000,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Discovers and correlates multi-domain contextual intelligence around a specific thermal event.
    Returns observations across 7 domains, spatial relationships, supporting/conflicting evidence,
    strongest explanation, and remaining uncertainty.
    """
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

    raw_event = JarvisToolRegistry.tool_get_event(db, event_id)
    if not raw_event or not raw_event.get("found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    lat = float(raw_event.get("latitude", 22.3039))
    lon = float(raw_event.get("longitude", 70.8022))

    correlation = context_engine.discover_and_correlate(
        db=db,
        event_ref_or_obj=raw_event,
        thermal_data=None
    )

    return {
        "event_id": event_id,
        "event_code": raw_event.get("event_code", event_id),
        "coordinates": [lat, lon],
        "state": raw_event.get("state"),
        "correlation": correlation
    }


@router.get("/events/{event_id}/context/provenance")
def get_event_context_provenance(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves full contextual provenance records and uncertainty analysis for a specific event.
    """
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

    raw_event = JarvisToolRegistry.tool_get_event(db, event_id)
    if not raw_event or not raw_event.get("found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    lat = float(raw_event.get("latitude", 22.3039))
    lon = float(raw_event.get("longitude", 70.8022))

    correlation = context_engine.discover_and_correlate(
        db=db,
        event_ref_or_obj=raw_event,
        thermal_data=None
    )

    return {
        "event_id": event_id,
        "event_code": raw_event.get("event_code", event_id),
        "coordinates": [lat, lon],
        "context_sources": correlation.get("context_sources", []),
        "context_provenance": correlation.get("context_provenance", []),
        "context_coverage": correlation.get("context_coverage", {}),
        "context_uncertainty": correlation.get("context_uncertainty", "KNOWN"),
        "evidence_strength": correlation.get("evidence_strength", "LIMITED"),
        "missing_sources": correlation.get("missing_sources", []),
        "conflicting_evidence": correlation.get("conflicting_evidence", [])
    }

