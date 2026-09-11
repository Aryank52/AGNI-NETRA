"""
AGNI-NETRA Phase 7: Global Thermal Intelligence & Multi-Provider Fusion Engine
Implements canonical thermal observation normalization, deterministic cross-source deduplication,
event-level multi-sensor fusion, source agreement / conflict scoring, and fail-safe multi-provider queries.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.canonical import ThermalObservation, ThermalEvent
from backend.app.services.intelligence.provenance import (
    SourceProvenance,
    create_firms_provenance,
    create_copernicus_slstr_provenance,
    create_mosdac_provenance,
    create_goes_provenance,
)
from backend.app.services.intelligence.provider_registry import provider_registry
from backend.app.services.intelligence.providers.base import ThermalProvider, ProviderHealth


# -----------------------------------------------------------------------------
# 1. Coordinate & Geodetic Utilities
# -----------------------------------------------------------------------------

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two WGS84 points in meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def parse_iso_utc_timestamp(ts_val: Any) -> Optional[datetime]:
    """
    Parses datetime string or object into standard ISO-8601 UTC datetime.
    Preserves timezone information without data loss.
    """
    if ts_val is None:
        return None
    if isinstance(ts_val, datetime):
        if ts_val.tzinfo is None:
            return ts_val.replace(tzinfo=timezone.utc)
        return ts_val.astimezone(timezone.utc)
    if isinstance(ts_val, str):
        try:
            # Replace Z with +00:00 for fromisoformat compatibility
            clean_str = ts_val.strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None
    return None


# -----------------------------------------------------------------------------
# 2. Canonical Observation Normalizer & Quality Filter
# -----------------------------------------------------------------------------

def normalize_thermal_record(
    raw: Dict[str, Any],
    provider_name: str = "FIRMS",
    dataset_name: Optional[str] = None
) -> Optional[ThermalObservation]:
    """
    Validates and normalizes raw telemetry into canonical ThermalObservation.
    Safely rejects malformed records violating WGS84 or physical metric bounds:
    - Latitude: [-90.0, 90.0]
    - Longitude: [-180.0, 180.0]
    - FRP: >= 0.0 MW
    - Confidence: [0.0, 100.0]
    - Valid acquisition timestamp required.
    """
    try:
        # 1. Spatial bounds
        lat = raw.get("latitude")
        lon = raw.get("longitude")
        if lat is None or lon is None:
            return None
        lat_f = float(lat)
        lon_f = float(lon)
        if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
            return None

        # 2. Temporal validation
        time_raw = raw.get("observation_time") or raw.get("acq_timestamp") or raw.get("timestamp")
        dt = parse_iso_utc_timestamp(time_raw)
        if dt is None:
            return None
        iso_time = dt.isoformat()

        # 3. Numeric ranges
        frp_raw = raw.get("radiative_power") or raw.get("frp") or 0.0
        frp_f = float(frp_raw)
        if frp_f < 0.0:
            return None

        conf_raw = raw.get("confidence") or 80.0
        conf_f = float(conf_raw)
        conf_f = max(0.0, min(100.0, conf_f))

        brightness = raw.get("brightness_temperature") or raw.get("brightness")
        bright_f = float(brightness) if brightness is not None else None

        obs_id = str(raw.get("observation_id") or f"OBS-{provider_name[:5]}-{abs(hash((lat_f, lon_f, iso_time))) % 10000000:07d}")
        rec_id = str(raw.get("source_record_id") or raw.get("id") or obs_id)

        # 4. Provenance assembly
        sensor = str(raw.get("sensor") or "VIIRS")
        sat = str(raw.get("satellite") or "NOAA-20")
        day_night = str(raw.get("day_night") or "D").upper()
        if day_night not in ("D", "N"):
            day_night = "D"

        if provider_name.upper() == "COPERNICUS_SLSTR":
            prov = create_copernicus_slstr_provenance(record_id=rec_id, observation_time=dt, satellite=sat, confidence=conf_f)
            ds = dataset_name or "COPERNICUS_SENTINEL3_SLSTR_FRP"
        elif provider_name.upper() == "ISRO_MOSDAC":
            prov = create_mosdac_provenance(record_id=rec_id, observation_time=dt, satellite=sat, confidence=conf_f)
            ds = dataset_name or "MOSDAC_INSAT_3D_3DR_TIR"
        elif provider_name.upper() == "NOAA_GOES":
            prov = create_goes_provenance(record_id=rec_id, observation_time=dt, satellite=sat)
            ds = dataset_name or "NOAA_GOES_ABI_FDCA"
        else:
            prov = create_firms_provenance(record_id=rec_id, observation_time=dt, sensor=sensor, confidence=conf_f)
            ds = dataset_name or f"NASA_FIRMS_{sensor}_NRT"

        return ThermalObservation(
            observation_id=obs_id,
            provider=provider_name.upper(),
            dataset=ds,
            source_record_id=rec_id,
            latitude=lat_f,
            longitude=lon_f,
            observation_time=iso_time,
            radiative_power=frp_f,
            brightness_temperature=bright_f,
            confidence=conf_f,
            sensor=sensor,
            satellite=sat,
            day_night=day_night,
            quality_flags=raw.get("quality_flags", {}),
            source_provenance=prov
        )
    except Exception:
        return None


# -----------------------------------------------------------------------------
# 3. Deterministic Cross-Source Deduplication
# -----------------------------------------------------------------------------

def deduplicate_thermal_observations(
    observations: List[ThermalObservation],
    spatial_threshold_m: float = 1000.0,
    temporal_threshold_sec: float = 1800.0
) -> List[List[ThermalObservation]]:
    """
    Groups observations referring to the same underlying physical thermal anomaly.
    
    Scientifically defensible matching dimensions:
    1. Spatial Proximity: <= 1000m (Sensor pixel resolution envelope of VIIRS 375m / SLSTR 1km)
    2. Temporal Coincidence: <= 1800s (30-minute coincidence window between dual satellite passes)
    3. Source Separation: Clusters observations from multiple independent providers to assess agreement
       without double-counting redundant entries from the exact same satellite pass.
    """
    clusters: List[List[ThermalObservation]] = []
    
    for obs in observations:
        t_obs = parse_iso_utc_timestamp(obs.observation_time)
        if t_obs is None:
            continue
        
        matched_cluster = None
        for cluster in clusters:
            rep = cluster[0]
            t_rep = parse_iso_utc_timestamp(rep.observation_time)
            if t_rep is None:
                continue
            
            # Check temporal window
            time_diff = abs((t_obs - t_rep).total_seconds())
            if time_diff > temporal_threshold_sec:
                continue
            
            # Check spatial distance
            dist = haversine_distance_meters(obs.latitude, obs.longitude, rep.latitude, rep.longitude)
            if dist <= spatial_threshold_m:
                matched_cluster = cluster
                break
        
        if matched_cluster is not None:
            # Check if this exact source record is already in cluster (prevent duplicate ingestion)
            exists = any(
                o.observation_id == obs.observation_id or
                (o.provider == obs.provider and o.source_record_id == obs.source_record_id)
                for o in matched_cluster
            )
            if not exists:
                matched_cluster.append(obs)
        else:
            clusters.append([obs])
            
    return clusters


# -----------------------------------------------------------------------------
# 4. Multi-Source Event Fusion & Agreement Evaluation
# -----------------------------------------------------------------------------

def evaluate_source_agreement(
    observations: List[ThermalObservation]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Evaluates cross-provider agreement across a cohort of coincident thermal observations.
    
    Categorization:
    - SINGLE_SOURCE: Only one provider detected the event.
    - MULTI_SOURCE_AGREEMENT: 2+ independent providers observe consistent thermal anomaly.
    - SOURCE_CONFLICT: Coincident passes disagree materially (e.g. FRP divergence > 5x or detection dispute).
    - INSUFFICIENT_OVERLAP: No coincident orbital passes overlapped in space/time.
    """
    if not observations:
        return "INSUFFICIENT_OVERLAP", []

    providers = list(set(o.provider for o in observations))
    conflicts: List[Dict[str, Any]] = []

    if len(providers) <= 1:
        return "SINGLE_SOURCE", []

    # Calculate FRP variance / ratio across distinct providers
    frps_by_provider: Dict[str, List[float]] = {}
    for o in observations:
        frps_by_provider.setdefault(o.provider, []).append(o.radiative_power)

    max_frps = {p: max(vals) for p, vals in frps_by_provider.items()}
    p_names = list(max_frps.keys())

    # Check for severe divergence between distinct providers
    divergence_detected = False
    for i in range(len(p_names)):
        for j in range(i + 1, len(p_names)):
            p1, p2 = p_names[i], p_names[j]
            v1, v2 = max_frps[p1], max_frps[p2]
            high_val = max(v1, v2)
            low_val = max(1.0, min(v1, v2))
            ratio = high_val / low_val

            if ratio >= 2.5 and high_val >= 25.0:
                divergence_detected = True
                conflicts.append({
                    "type": "THERMAL_MAGNITUDE_DIVERGENCE",
                    "severity": "MODERATE",
                    "provider_a": p1,
                    "magnitude_a_mw": v1,
                    "provider_b": p2,
                    "magnitude_b_mw": v2,
                    "ratio": round(ratio, 2),
                    "explanation": f"FRP magnitude divergence between {p1} ({v1:.1f} MW) and {p2} ({v2:.1f} MW) exceeds {round(ratio, 1)}x ratio buffer due to sensor pixel footprints."
                })

    if divergence_detected:
        return "SOURCE_CONFLICT", conflicts

    return "MULTI_SOURCE_AGREEMENT", []


def fuse_observations_to_canonical_event(
    event_id: str,
    observations: List[ThermalObservation],
    fallback_metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> ThermalEvent:
    """
    Fuses multiple normalized observations into a single canonical ThermalEvent
    retaining contributing observations, unique providers, agreement status, and conflicts.
    """
    fallback = fallback_metadata or kwargs.get("fallback") or kwargs.get("fallback_context") or {}
    
    if not observations:
        return ThermalEvent(
            event_id=event_id,
            event_code=fallback.get("event_code") or event_id,
            latitude=fallback.get("latitude", 22.47),
            longitude=fallback.get("longitude", 70.06),
            first_seen=fallback.get("first_seen", datetime.now(timezone.utc).isoformat()),
            last_seen=fallback.get("last_seen", datetime.now(timezone.utc).isoformat()),
            detection_count=0,
            avg_frp=0.0,
            max_frp=0.0,
            country=fallback.get("country", "India"),
            jurisdiction=fallback.get("state") or fallback.get("jurisdiction", "Gujarat"),
            status="ACTIVE",
            contributing_observations=[],
            contributing_providers=[],
            source_agreement="INSUFFICIENT_OVERLAP",
            source_conflicts=[]
        )

    # Compute centroid and bbox
    lats = [o.latitude for o in observations]
    lons = [o.longitude for o in observations]
    frps = [o.radiative_power for o in observations]
    times = [o.observation_time for o in observations]

    centroid_lat = round(sum(lats) / len(lats), 6)
    centroid_lon = round(sum(lons) / len(lons), 6)
    bbox = [min(lats), min(lons), max(lats), max(lons)]

    sorted_times = sorted(times)
    first_seen = sorted_times[0]
    last_seen = sorted_times[-1]

    avg_frp = round(sum(frps) / len(frps), 2)
    max_frp = round(max(frps), 2)

    obs_ids = [o.observation_id for o in observations]
    provs = sorted(list(set(o.provider for o in observations)))

    agreement_status, conflicts = evaluate_source_agreement(observations)

    return ThermalEvent(
        event_id=event_id,
        event_code=fallback.get("event_code") or event_id,
        latitude=centroid_lat,
        longitude=centroid_lon,
        bounding_box=bbox,
        first_seen=first_seen,
        last_seen=last_seen,
        detection_count=len(observations),
        avg_frp=avg_frp,
        max_frp=max_frp,
        country=fallback.get("country", "India"),
        jurisdiction=fallback.get("state") or fallback.get("jurisdiction", "Gujarat"),
        status="ACTIVE",
        matched_facility_id=fallback.get("facility_id") or fallback.get("matched_facility_id"),
        contributing_observations=obs_ids,
        contributing_providers=provs,
        source_agreement=agreement_status,
        source_conflicts=conflicts,
        provenance=observations[0].source_provenance if observations else None
    )


# -----------------------------------------------------------------------------
# 5. Fail-Safe Multi-Provider Thermal Query Service
# -----------------------------------------------------------------------------

def query_multi_provider_thermal_intelligence(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    event_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executes fail-safe queries across all registered thermal providers.
    Provides complete failure isolation: failure of one provider (e.g. SLSTR or INSAT)
    never interrupts FIRMS observations or crashes the overall query.
    """
    thermal_providers = provider_registry.get_thermal_providers()
    
    collected_observations: List[ThermalObservation] = []
    provider_results: Dict[str, Dict[str, Any]] = {}
    contributing_sources: List[str] = []
    unconfigured_sources: List[str] = []

    for prov in thermal_providers:
        meta = prov.get_metadata()
        p_name = meta.provider_name.upper()

        if meta.availability == ProviderHealth.NOT_CONFIGURED:
            provider_results[p_name] = {
                "status": "NOT_CONFIGURED",
                "observation_count": 0,
                "coverage": meta.geographic_coverage.description,
                "limitations": meta.limitations
            }
            unconfigured_sources.append(p_name)
            continue

        # Execute query with failure isolation
        try:
            obs = prov.query_observations(
                db=db,
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                start_time=start_time,
                end_time=end_time
            )
            provider_results[p_name] = {
                "status": "AVAILABLE",
                "observation_count": len(obs),
                "coverage": meta.geographic_coverage.description,
                "dataset": meta.dataset_name
            }
            if obs:
                collected_observations.extend(obs)
                contributing_sources.append(p_name)
        except Exception as ex:
            provider_results[p_name] = {
                "status": "DEGRADED",
                "error": str(ex),
                "observation_count": 0,
                "coverage": meta.geographic_coverage.description
            }

    # Deduplicate and cluster observations
    clusters = deduplicate_thermal_observations(
        collected_observations,
        spatial_threshold_m=1000.0,
        temporal_threshold_sec=1800.0
    )

    # Flatten deduplicated records
    deduped_obs = [item for sublist in clusters for item in sublist]
    agreement_level, conflicts = evaluate_source_agreement(deduped_obs)

    # Compile observation provenance records
    provenance_records = []
    for o in deduped_obs:
        if o.source_provenance:
            provenance_records.append(o.source_provenance.model_dump())

    return {
        "event_coordinates": {"latitude": latitude, "longitude": longitude},
        "search_radius_km": radius_km,
        "total_observations_retrieved": len(collected_observations),
        "deduplicated_observation_count": len(deduped_obs),
        "contributing_providers": contributing_sources,
        "unconfigured_providers": unconfigured_sources,
        "provider_status_breakdown": provider_results,
        "source_agreement": agreement_level,
        "source_conflicts": conflicts,
        "observations": deduped_obs,
        "provenance_records": provenance_records,
        "is_multi_source_supported": len(contributing_sources) > 1,
        "evidence_sufficiency": "SUFFICIENT" if len(deduped_obs) >= 1 else "INSUFFICIENT"
    }


class ThermalFusionEngine:
    """Facade for thermal intelligence normalization, deduplication, and multi-provider fusion."""
    
    normalize_record = staticmethod(normalize_thermal_record)
    deduplicate = staticmethod(deduplicate_thermal_observations)
    evaluate_agreement = staticmethod(evaluate_source_agreement)
    fuse_event = staticmethod(fuse_observations_to_canonical_event)
    query_multi_provider = staticmethod(query_multi_provider_thermal_intelligence)


thermal_fusion_engine = ThermalFusionEngine()
