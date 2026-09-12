"""
AGNI-NETRA Phase 6: Intelligence Providers & Coverage API Endpoints
Provides machine-readable discovery, metadata, health status, and geographic reach
for all intelligence providers with RBAC masking for PUBLIC users.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_optional_current_user
from backend.app.models.domain import User, InvestigationWorkspace
from backend.app.services.intelligence.provider_registry import provider_registry
from backend.app.services.intelligence.profiles import IndiaIntelligenceProfile, GlobalIntelligenceProfile, GlobalContextProfile
from backend.app.services.intelligence.context_engine import context_engine
from backend.app.services.intelligence.temporal_engine import temporal_baseline_engine
from backend.app.services.intelligence.environmental_engine import environmental_discovery_engine
from backend.app.services.intelligence.cross_modal_engine import cross_modal_verification_engine
from backend.app.services.intelligence.evidence_graph_engine import evidence_graph_engine
from backend.app.services.intelligence.multi_event_correlation import multi_event_correlation_engine
from backend.app.services.intelligence.global_intelligence_synthesis import global_intelligence_synthesis_engine
from backend.app.services.intelligence.next_best_evidence import next_best_evidence_engine
from backend.app.models.canonical import DecisionSupportMode

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


# ==============================================================================
# Phase 11 Evidence Graph & Explainable Intelligence Endpoints
# ==============================================================================

@router.get("/events/{event_id}/evidence-graph")
def get_event_evidence_graph_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves full canonical evidence graph for an event with support profiles and epistemic nature breakdown."""
    user_role = current_user.role if current_user else "PUBLIC"
    graph_obj = evidence_graph_engine.build_event_evidence_graph(db=db, event_ref=event_id)
    graph_dict = graph_obj.model_dump()
    if user_role == "PUBLIC":
        # RBAC masking for public: retain full explainability while sanitizing internal debug flags
        graph_dict["internal_audit"] = False
    return {
        "status": "SUCCESS",
        "data": graph_dict
    }


@router.get("/events/{event_id}/evidence")
def get_event_evidence_nodes_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves all evidence nodes for an event with nature and uncertainty."""
    graph_obj = evidence_graph_engine.build_event_evidence_graph(db=db, event_ref=event_id)
    return {
        "status": "SUCCESS",
        "total_nodes": len(graph_obj.nodes),
        "evidence_nature_counts": graph_obj.evidence_nature_counts,
        "nodes": [n.model_dump() for n in graph_obj.nodes]
    }


@router.get("/events/{event_id}/evidence/supporting")
def get_event_supporting_evidence_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves supporting evidence items directly substantiating the operational assessment."""
    supp = evidence_graph_engine.get_supporting_evidence(db=db, event_id=event_id)
    return {
        "status": "SUCCESS",
        "total_supporting": len(supp),
        "supporting_evidence": supp
    }


@router.get("/events/{event_id}/evidence/conflicting")
def get_event_conflicting_evidence_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves contradicting/limiting evidence items and conflicting hypotheses."""
    conf = evidence_graph_engine.get_conflicting_evidence(db=db, event_id=event_id)
    return {
        "status": "SUCCESS",
        "total_conflicting": len(conf),
        "conflicting_evidence": conf
    }


@router.get("/events/{event_id}/hypotheses")
def get_event_hypotheses_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves standardized candidate hypotheses (A through G) with support profiles."""
    hyps = evidence_graph_engine.get_hypotheses(db=db, event_id=event_id)
    return {
        "status": "SUCCESS",
        "total_hypotheses": len(hyps),
        "hypotheses": hyps
    }


@router.get("/events/{event_id}/assessment-lineage")
def get_event_assessment_lineage_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves assessment lineage tracing conclusion from root observations to final synthesis."""
    lineage = evidence_graph_engine.get_assessment_lineage(db=db, event_id=event_id)
    return {
        "status": "SUCCESS",
        "assessment_lineage": lineage
    }


@router.get("/events/{event_id}/data-gaps")
def get_event_data_gaps_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves identified missing evidence, unconfigured feeds, and recommendations to reduce uncertainty."""
    gaps = evidence_graph_engine.get_data_gaps(db=db, event_id=event_id)
    return {
        "status": "SUCCESS",
        "data_gaps": gaps
    }


@router.get("/events/{event_id}/provenance-chain")
def get_event_provenance_chain_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves complete provenance chain for all evidence nodes in the graph."""
    prov = evidence_graph_engine.get_provenance_chain(db=db, event_id=event_id)
    return {
        "status": "SUCCESS",
        "provenance_chain": prov
    }


# =====================================================================
# Phase 12: Multi-Event Incident Correlation Endpoints (Section 21)
# =====================================================================

@router.get("/events/{event_id}/related")
def get_event_related_events_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves related event IDs discovered via multi-event correlation."""
    res = multi_event_correlation_engine.correlate_incident(db, event_id=event_id)
    return {
        "status": "SUCCESS",
        "primary_event_id": event_id,
        "related_event_ids": res.related_event_ids,
        "total_related": len(res.related_event_ids),
        "cohort_count": res.cohort_count
    }


@router.get("/events/{event_id}/relationships")
def get_event_relationships_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves pairwise typed relationships between primary event and related events."""
    res = multi_event_correlation_engine.correlate_incident(db, event_id=event_id)
    return {
        "status": "SUCCESS",
        "primary_event_id": event_id,
        "total_relationships": len(res.relationships),
        "relationships": [r.model_dump() for r in res.relationships]
    }


@router.get("/events/{event_id}/cluster")
def get_event_cluster_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves spatial-temporal DBSCAN clusters formed around event."""
    res = multi_event_correlation_engine.correlate_incident(db, event_id=event_id)
    return {
        "status": "SUCCESS",
        "primary_event_id": event_id,
        "total_clusters": len(res.clusters),
        "clusters": [c.model_dump() for c in res.clusters],
        "primary_cluster": res.clusters[0].model_dump() if res.clusters else None
    }


@router.get("/events/{event_id}/incident")
def get_event_incident_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves complete multi-event incident correlation result for event."""
    res = multi_event_correlation_engine.correlate_incident(db, event_id=event_id)
    return {
        "status": "SUCCESS",
        "primary_event_id": event_id,
        "correlation_result": res.model_dump()
    }


@router.get("/incidents/{incident_id}")
def get_incident_by_id_endpoint(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves incident assessment and impact profile by incident ID."""
    primary_event_id = incident_id.replace("INC-", "")
    res = multi_event_correlation_engine.correlate_incident(db, event_id=primary_event_id)
    return {
        "status": "SUCCESS",
        "incident_id": incident_id,
        "primary_event_id": res.primary_event_id,
        "incident_assessment": res.incident_assessment.model_dump() if res.incident_assessment else None,
        "impact_profile": res.impact_profile.model_dump() if res.impact_profile else None,
        "correlation_strength": res.incident_assessment.correlation_strength if res.incident_assessment else "UNKNOWN"
    }


@router.get("/incidents/{incident_id}/events")
def get_incident_events_endpoint(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves member events associated with the correlated incident."""
    primary_event_id = incident_id.replace("INC-", "")
    res = multi_event_correlation_engine.correlate_incident(db, event_id=primary_event_id)
    all_events = [res.primary_event_id] + [eid for eid in res.related_event_ids if eid != res.primary_event_id]
    return {
        "status": "SUCCESS",
        "incident_id": incident_id,
        "primary_event_id": res.primary_event_id,
        "total_events": len(all_events),
        "events": all_events,
        "related_event_ids": res.related_event_ids,
        "cohort_count": res.cohort_count
    }


@router.get("/incidents/{incident_id}/evidence")
def get_incident_evidence_endpoint(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves evidence nodes, uncertainty, and data gaps for the incident."""
    primary_event_id = incident_id.replace("INC-", "")
    res = multi_event_correlation_engine.correlate_incident(db, event_id=primary_event_id)
    return {
        "status": "SUCCESS",
        "incident_id": incident_id,
        "total_evidence_nodes": len(res.incident_evidence),
        "evidence_nodes": res.incident_evidence,
        "uncertainty": res.incident_uncertainty,
        "data_gaps": res.incident_data_gaps
    }


@router.get("/incidents/{incident_id}/hypotheses")
def get_incident_hypotheses_endpoint(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves the 9 standardized incident hypotheses (H1-H9) for the incident."""
    primary_event_id = incident_id.replace("INC-", "")
    res = multi_event_correlation_engine.correlate_incident(db, event_id=primary_event_id)
    return {
        "status": "SUCCESS",
        "incident_id": incident_id,
        "favored_hypothesis": res.incident_assessment.favored_hypothesis if res.incident_assessment else None,
        "total_hypotheses": len(res.hypotheses),
        "hypotheses": [h.model_dump() for h in res.hypotheses]
    }


@router.get("/incidents/{incident_id}/provenance")
def get_incident_provenance_endpoint(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Retrieves provenance and audit trail for the incident correlation."""
    primary_event_id = incident_id.replace("INC-", "")
    res = multi_event_correlation_engine.correlate_incident(db, event_id=primary_event_id)
    return {
        "status": "SUCCESS",
        "incident_id": incident_id,
        "provenance": res.provenance,
        "model_id": res.model_id,
        "correlation_timestamp": res.correlation_timestamp
    }


# ------------------------------------------------------------------------------
# Phase 13: Global Intelligence Fusion & Decision-Support Synthesis Endpoints
# ------------------------------------------------------------------------------

def _resolve_decision_support_mode(mode_str: str, current_user: Optional[User]) -> DecisionSupportMode:
    """Helper to parse mode with RBAC fallback to PUBLIC_SAFE for unauthorized or public requests."""
    user_role = current_user.role if current_user else "PUBLIC"
    cleaned = str(mode_str or "ANALYST").strip().upper().replace("-", "_")
    if user_role == "PUBLIC" or cleaned in ("PUBLIC_SAFE", "PUBLIC"):
        return DecisionSupportMode.PUBLIC_SAFE
    if cleaned == "AGENCY":
        return DecisionSupportMode.AGENCY
    if cleaned == "EXECUTIVE":
        return DecisionSupportMode.EXECUTIVE
    return DecisionSupportMode.ANALYST


@router.get("/events/{event_id}/assessment")
def get_event_intelligence_assessment(
    event_id: str,
    mode: str = Query("ANALYST", description="Decision support mode: ANALYST, AGENCY, EXECUTIVE, PUBLIC_SAFE"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Synthesizes and retrieves the comprehensive UnifiedIntelligenceAssessment for an event
    with strict separation of observation, classification, risk, evidence, and uncertainty.
    """
    mode_enum = _resolve_decision_support_mode(mode, current_user)
    assessment = global_intelligence_synthesis_engine.synthesize_assessment(
        db=db,
        target_ref=event_id,
        mode=mode_enum.value
    )
    return {
        "status": "SUCCESS",
        "event_id": event_id,
        "mode": mode_enum.value,
        "assessment": assessment.model_dump()
    }


@router.get("/events/{event_id}/assessment/history")
def get_event_assessment_history(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves chronological assessment evolution history and delta changes for an event workspace.
    """
    ws = db.query(InvestigationWorkspace).filter(
        (InvestigationWorkspace.primary_event_id == event_id) |
        (InvestigationWorkspace.title.ilike(f"%{event_id}%"))
    ).order_by(InvestigationWorkspace.updated_at.desc()).first()

    history = ws.assessment_history if (ws and ws.assessment_history) else []
    changes = ws.assessment_changes if (ws and ws.assessment_changes) else None
    return {
        "status": "SUCCESS",
        "event_id": event_id,
        "history": history,
        "changes": changes
    }


@router.get("/events/{event_id}/decision-support")
def get_event_decision_support(
    event_id: str,
    mode: str = Query("ANALYST", description="Decision support mode: ANALYST, AGENCY, EXECUTIVE, PUBLIC_SAFE"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves tailored decision-support package for the requested stakeholder presentation mode.
    """
    mode_enum = _resolve_decision_support_mode(mode, current_user)
    assessment = global_intelligence_synthesis_engine.synthesize_assessment(
        db=db,
        target_ref=event_id,
        mode=mode_enum.value
    )
    pkg = assessment.decision_support_packages.get(mode_enum.value) or assessment.decision_support_packages.get("ANALYST")
    return {
        "status": "SUCCESS",
        "event_id": event_id,
        "mode": mode_enum.value,
        "decision_support": pkg
    }


@router.get("/events/{event_id}/next-best-evidence")
def get_event_next_best_evidence(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves prioritized Next-Best-Evidence recommendations to reduce epistemic uncertainty.
    """
    assessment = global_intelligence_synthesis_engine.synthesize_assessment(
        db=db,
        target_ref=event_id,
        mode="ANALYST"
    )
    return {
        "status": "SUCCESS",
        "event_id": event_id,
        "recommendations": [rec.model_dump() for rec in assessment.next_best_evidence]
    }


@router.get("/events/{event_id}/assessment/provenance")
def get_event_assessment_provenance(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves auditable provenance and source integrity trail for the synthesized intelligence assessment.
    """
    assessment = global_intelligence_synthesis_engine.synthesize_assessment(
        db=db,
        target_ref=event_id,
        mode="ANALYST"
    )
    return {
        "status": "SUCCESS",
        "event_id": event_id,
        "provenance": assessment.provenance,
        "evidence_ids": assessment.evidence_ids,
        "synthesis_pipeline_version": assessment.synthesis_pipeline_version,
        "synthesis_timestamp": assessment.synthesis_timestamp
    }


@router.get("/incidents/{incident_id}/assessment")
def get_incident_intelligence_assessment(
    incident_id: str,
    mode: str = Query("ANALYST", description="Decision support mode: ANALYST, AGENCY, EXECUTIVE, PUBLIC_SAFE"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Synthesizes and retrieves multi-event incident-level intelligence assessment.
    """
    mode_enum = _resolve_decision_support_mode(mode, current_user)
    assessment = global_intelligence_synthesis_engine.synthesize_incident_assessment(
        db=db,
        incident_id=incident_id,
        mode=mode_enum.value
    )
    return {
        "status": "SUCCESS",
        "incident_id": incident_id,
        "mode": mode_enum.value,
        "assessment": assessment.model_dump()
    }


@router.get("/incidents/{incident_id}/decision-support")
def get_incident_decision_support(
    incident_id: str,
    mode: str = Query("ANALYST", description="Decision support mode: ANALYST, AGENCY, EXECUTIVE, PUBLIC_SAFE"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves incident-level decision-support package for the requested stakeholder presentation mode.
    """
    mode_enum = _resolve_decision_support_mode(mode, current_user)
    assessment = global_intelligence_synthesis_engine.synthesize_incident_assessment(
        db=db,
        incident_id=incident_id,
        mode=mode_enum.value
    )
    pkg = assessment.decision_support_packages.get(mode_enum.value) or assessment.decision_support_packages.get("ANALYST")
    return {
        "status": "SUCCESS",
        "incident_id": incident_id,
        "mode": mode_enum.value,
        "decision_support": pkg
    }


@router.get("/incidents/{incident_id}/next-best-evidence")
def get_incident_next_best_evidence(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves incident-level Next-Best-Evidence recommendations.
    """
    assessment = global_intelligence_synthesis_engine.synthesize_incident_assessment(
        db=db,
        incident_id=incident_id,
        mode="ANALYST"
    )
    return {
        "status": "SUCCESS",
        "incident_id": incident_id,
        "recommendations": [rec.model_dump() for rec in assessment.next_best_evidence]
    }





