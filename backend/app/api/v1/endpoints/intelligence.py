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
from backend.app.services.intelligence.temporal_engine import temporal_baseline_engine
from backend.app.services.intelligence.environmental_engine import environmental_discovery_engine
from backend.app.services.intelligence.cross_modal_engine import cross_modal_verification_engine

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


# =========================================================================
# Phase 9: Global Historical Baselines & Temporal Pattern Intelligence Endpoints
# =========================================================================

@router.get("/temporal/providers")
def get_temporal_providers(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Lists registered temporal observation and baseline provider adapters.
    """
    return provider_registry.get_temporal_providers()


@router.get("/temporal/coverage")
def get_temporal_coverage(
    region: Optional[str] = "GLOBAL",
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns multi-constellation temporal observation coverage breakdown across providers.
    """
    return provider_registry.get_temporal_coverage_summary(region=region or "GLOBAL")


@router.get("/temporal/health")
def get_temporal_health(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns operational health status across registered temporal intelligence provider adapters.
    """
    temporal_providers = provider_registry.get_temporal_providers()
    statuses = {}
    for p in temporal_providers:
        prov_name = p.get("provider", "UNKNOWN").upper()
        statuses[prov_name] = {
            "health": "HEALTHY" if p.get("status") == "AVAILABLE" else "DEGRADED",
            "availability": p.get("status", "AVAILABLE"),
            "dataset": p.get("dataset"),
            "temporal_depth": p.get("period_covered", "Multi-year"),
            "resolution": p.get("temporal_resolution", "12_HOURS")
        }
    return {
        "status": "OPERATIONAL",
        "total_temporal_providers": len(temporal_providers),
        "temporal_providers": statuses
    }


@router.get("/events/{event_id}/temporal")
def get_event_temporal_intelligence(
    event_id: str,
    radius_km: Optional[float] = 3.0,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Executes full longitudinal temporal intelligence analysis for a specific thermal event.
    Evaluates persistence, recurrence, seasonality, day/night ratio, baseline deviation, and uncertainty.
    """
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

    raw_event = JarvisToolRegistry.tool_get_event(db, event_id)
    if not raw_event or not raw_event.get("found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    temporal_result = temporal_baseline_engine.analyze_event_temporal(
        db=db,
        event_ref=event_id,
        radius_km=radius_km or 3.0
    )

    return {
        "event_id": event_id,
        "event_code": raw_event.get("event_code", event_id),
        "coordinates": [float(raw_event.get("latitude", 22.3542)), float(raw_event.get("longitude", 69.8644))],
        "state": raw_event.get("state"),
        "temporal_intelligence": temporal_result
    }


@router.get("/events/{event_id}/temporal/history")
def get_event_temporal_history(
    event_id: str,
    radius_km: Optional[float] = 3.0,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves historical baseline radiometric telemetry and multi-scale observation windows for an event.
    """
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

    raw_event = JarvisToolRegistry.tool_get_event(db, event_id)
    if not raw_event or not raw_event.get("found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    temporal_result = temporal_baseline_engine.analyze_event_temporal(
        db=db,
        event_ref=event_id,
        radius_km=radius_km or 3.0
    )

    return {
        "event_id": event_id,
        "event_code": raw_event.get("event_code", event_id),
        "baseline": temporal_result.get("baseline", {}),
        "multi_scale_windows": temporal_result.get("multi_scale_windows", {}),
        "observation_count": temporal_result.get("observation_count", 0),
        "provider_agreement": temporal_result.get("provider_agreement", {})
    }


@router.get("/events/{event_id}/temporal/patterns")
def get_event_temporal_patterns(
    event_id: str,
    radius_km: Optional[float] = 3.0,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves behavioral temporal patterns: persistence tiers, recurrence frequency, seasonality, and diurnal cycles.
    """
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

    raw_event = JarvisToolRegistry.tool_get_event(db, event_id)
    if not raw_event or not raw_event.get("found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    temporal_result = temporal_baseline_engine.analyze_event_temporal(
        db=db,
        event_ref=event_id,
        radius_km=radius_km or 3.0
    )

    return {
        "event_id": event_id,
        "event_code": raw_event.get("event_code", event_id),
        "persistence": temporal_result.get("persistence", {}),
        "recurrence": temporal_result.get("recurrence", {}),
        "pattern": temporal_result.get("pattern", {}),
        "anomaly": temporal_result.get("anomaly", {})
    }


@router.get("/events/{event_id}/temporal/provenance")
def get_event_temporal_provenance(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves longitudinal temporal provenance records, uncertainty factors, and uncertainty reduction guidance.
    """
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

    raw_event = JarvisToolRegistry.tool_get_event(db, event_id)
    if not raw_event or not raw_event.get("found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    temporal_result = temporal_baseline_engine.analyze_event_temporal(
        db=db,
        event_ref=event_id,
        radius_km=3.0
    )
    evid = temporal_result.get("evidence", {})

    return {
        "event_id": event_id,
        "event_code": raw_event.get("event_code", event_id),
        "evidence_strength": evid.get("evidence_strength", "STRONG"),
        "temporal_uncertainty": evid.get("temporal_uncertainty", "KNOWN"),
        "observation_count": temporal_result.get("observation_count", 0),
        "provenance": [evid.get("provenance", {})] if evid.get("provenance") else [],
        "limiting_factors": evid.get("limiting_factors", []),
        "what_could_reduce_uncertainty": evid.get("what_could_reduce_uncertainty", []),
        "missing_historical_sources": evid.get("missing_historical_sources", [])
    }


# ==============================================================================
# Phase 10 Environmental Intelligence & Cross-Modal Verification Endpoints
# ==============================================================================

@router.get("/environment/providers")
def get_environmental_providers(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Lists registered environmental, meteorological, and atmospheric providers.
    Truthfully discloses unconfigured providers (ECMWF, GFS, CAMS).
    """
    return provider_registry.get_environmental_providers()


@router.get("/environment/coverage")
def get_environmental_coverage(
    region: str = "GLOBAL",
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves environmental observation coverage and unconfigured provider disclosures.
    """
    return provider_registry.get_environmental_coverage_summary(region=region)


@router.get("/environment/health")
def get_environmental_health(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns operational health across all environmental and meteorological provider adapters.
    """
    summary = provider_registry.get_provider_health_summary(db)
    statuses = summary.get("statuses", {})
    env_statuses = {
        k: v for k, v in statuses.items()
        if "WEATHER" in k or "ATMOSPHERIC" in k or "GFS" in k or "ECMWF" in k
    }
    return {
        "environmental_providers_count": len(env_statuses),
        "statuses": env_statuses,
        "operational": True
    }


@router.get("/events/{event_id}/environment")
def get_event_environment(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves surface weather, atmospheric conditions, wind transport, precipitation persistence, and cloud observability for an event.
    """
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

    raw_event = JarvisToolRegistry.tool_get_event(db, event_id)
    if not raw_event or not raw_event.get("found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    env_result = environmental_discovery_engine.analyze_event_environment(
        db=db,
        event_ref=event_id
    )
    return env_result


@router.get("/events/{event_id}/environment/provenance")
def get_event_environmental_provenance(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves provenance records, limiting factors, and uncertainty reduction guidance for environmental data.
    """
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

    raw_event = JarvisToolRegistry.tool_get_event(db, event_id)
    if not raw_event or not raw_event.get("found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    env_result = environmental_discovery_engine.analyze_event_environment(
        db=db,
        event_ref=event_id
    )
    evid = env_result.get("evidence", {})
    return {
        "event_id": event_id,
        "event_code": raw_event.get("event_code", event_id),
        "evidence_strength": evid.get("evidence_strength", "STRONG"),
        "environmental_uncertainty": evid.get("environmental_uncertainty", "KNOWN"),
        "provenance": [evid.get("provenance")] if evid.get("provenance") else [],
        "limiting_factors": evid.get("limiting_factors", []),
        "what_could_reduce_uncertainty": evid.get("what_could_reduce_uncertainty", []),
        "missing_sources": evid.get("missing_sources", [])
    }


@router.get("/events/{event_id}/cross-modal")
def get_event_cross_modal(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Evaluates multi-modal corroboration comparing thermal telemetry against optical, SAR, land cover, and weather modalities.
    """
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

    raw_event = JarvisToolRegistry.tool_get_event(db, event_id)
    if not raw_event or not raw_event.get("found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    xm_result = cross_modal_verification_engine.verify_event_cross_modal(
        db=db,
        event_ref=event_id
    )
    return xm_result


@router.get("/events/{event_id}/cross-modal/provenance")
def get_event_cross_modal_provenance(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves cross-modal provenance, highest-value next observation recommendations, and data gaps.
    """
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

    raw_event = JarvisToolRegistry.tool_get_event(db, event_id)
    if not raw_event or not raw_event.get("found"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal event '{event_id}' not found."
        )

    xm_result = cross_modal_verification_engine.verify_event_cross_modal(
        db=db,
        event_ref=event_id
    )
    evid = xm_result.get("evidence", {})
    return {
        "event_id": event_id,
        "event_code": raw_event.get("event_code", event_id),
        "corroboration_status": xm_result.get("corroboration_status", "PARTIALLY_CORROBORATED"),
        "evidence_strength": evid.get("evidence_strength", "MODERATE"),
        "cross_modal_uncertainty": evid.get("cross_modal_uncertainty", "KNOWN"),
        "modalities_evaluated": xm_result.get("modalities_evaluated", []),
        "provenance": [evid.get("provenance")] if evid.get("provenance") else [],
        "limiting_factors": evid.get("limiting_factors", []),
        "what_could_reduce_uncertainty": evid.get("what_could_reduce_uncertainty", []),
        "missing_modalities": xm_result.get("missing_modalities", []),
        "highest_value_observation": evid.get("highest_value_observation", "")
    }


# ------------------------------------------------------------------------------
# Direct Phase 10 REST Intelligence Endpoints
# ------------------------------------------------------------------------------

@router.get("/environmental/providers/status")
def get_environmental_and_cross_modal_status(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Returns coverage and status summaries across environmental and cross-modal providers."""
    env_cov = provider_registry.get_environmental_coverage_summary()
    cm_cov = provider_registry.get_cross_modal_coverage_summary()
    return {
        "status": "SUCCESS",
        "data": {
            "environmental": env_cov,
            "cross_modal": cm_cov
        }
    }


@router.get("/environmental/{event_id}")
def get_environmental_for_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves surface weather, atmospheric conditions, and wind transport for an event."""
    env_result = environmental_discovery_engine.analyze_event_environment(
        db=db,
        event_ref=event_id
    )
    return {
        "status": "SUCCESS",
        "data": env_result
    }


@router.get("/environmental/{event_id}/weather")
def get_environmental_weather_for_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves meteorological surface observations for an event."""
    env_result = environmental_discovery_engine.analyze_event_environment(
        db=db,
        event_ref=event_id
    )
    return {
        "status": "SUCCESS",
        "data": env_result.get("weather", {})
    }


@router.get("/environmental/{event_id}/plume")
def get_environmental_plume_for_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves wind vector and plume dispersion transport direction for an event."""
    env_result = environmental_discovery_engine.analyze_event_environment(
        db=db,
        event_ref=event_id
    )
    wnd = env_result.get("wind", {})
    return {
        "status": "SUCCESS",
        "data": {
            "dispersion_direction": wnd.get("smoke_dispersion_direction", "ENE"),
            "wind_speed_ms": wnd.get("wind_speed_ms", 0.0),
            "wind_direction_deg": wnd.get("wind_direction_deg", 0.0),
            "wind_speed_category": wnd.get("transport_condition", "LIGHT_DISPERSION"),
            "evidence_nature": "DERIVED",
            "relationship_type": "DERIVED_ENVIRONMENTAL_RELATIONSHIP",
            "derivation_explanation": "Plume direction is DERIVED from observed 10m wind vector and boundary layer height, not a direct plume observation.",
            "provenance": wnd.get("provenance")
        }
    }


@router.get("/cross-modal/{event_id}")
def get_cross_modal_for_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves multi-modal corroboration across optical, SAR, land cover, and weather."""
    xm_result = cross_modal_verification_engine.verify_event_cross_modal(
        db=db,
        event_ref=event_id
    )
    return {
        "status": "SUCCESS",
        "data": xm_result
    }


@router.get("/cross-modal/{event_id}/optical")
def get_cross_modal_optical_for_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves optical observation (Sentinel-2) details and observability status."""
    xm_result = cross_modal_verification_engine.verify_event_cross_modal(
        db=db,
        event_ref=event_id
    )
    return {
        "status": "SUCCESS",
        "data": xm_result.get("optical", {})
    }


@router.get("/cross-modal/{event_id}/sar")
def get_cross_modal_sar_for_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves SAR radar backscatter observation (Sentinel-1) details and coherence."""
    xm_result = cross_modal_verification_engine.verify_event_cross_modal(
        db=db,
        event_ref=event_id
    )
    return {
        "status": "SUCCESS",
        "data": xm_result.get("sar", {})
    }


