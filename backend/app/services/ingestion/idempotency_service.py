"""
AGNI-NETRA — WP3 Deterministic Idempotency & Chronological Ingestion Service
Computes canonical SHA-256 fingerprints based on authoritative source attributes.
Guarantees duplicate delivery idempotency, out-of-order timestamp safety, and replay suppression.
"""

import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.models.domain import ThermalDetection, ThermalEvent
from backend.app.services.ingestion.failure_taxonomy import IngestionFailureCategory


def compute_deterministic_fingerprint(
    provider: str,
    sensor: str,
    latitude: float,
    longitude: float,
    acq_timestamp: datetime
) -> str:
    """
    Computes a canonical SHA-256 fingerprint for deterministic deduplication.
    Based strictly on authoritative physical observation attributes:
    - Provider name (e.g. NASA_FIRMS)
    - Sensor instrument (e.g. VIIRS_NOAA20, MODIS)
    - Latitude rounded to 5 decimal places (~1.1 meter geodetic precision)
    - Longitude rounded to 5 decimal places (~1.1 meter geodetic precision)
    - UTC ISO-8601 acquisition timestamp down to minute resolution
    """
    if acq_timestamp.tzinfo is None:
        acq_utc = acq_timestamp.replace(tzinfo=timezone.utc)
    else:
        acq_utc = acq_timestamp.astimezone(timezone.utc)

    ts_iso = acq_utc.strftime("%Y-%m-%dT%H:%M:00Z")
    canon_str = f"{provider.upper()}:{sensor.upper()}:{latitude:.5f}:{longitude:.5f}:{ts_iso}"
    return hashlib.sha256(canon_str.encode("utf-8")).hexdigest()


class IdempotencyService:
    """
    Manages deduplication checks, out-of-order sequence tracking, and replay idempotency.
    """

    def __init__(self):
        # In-memory LRU fingerprint cache to accelerate high-frequency bursts
        self._recent_fingerprints: Set[str] = set()
        self._max_cache_size = 50000

    def check_and_register_fingerprint(self, fingerprint: str) -> bool:
        """
        Returns True if the fingerprint is newly seen (unique) in memory cache,
        False if it was already registered.
        """
        if fingerprint in self._recent_fingerprints:
            return False

        if len(self._recent_fingerprints) >= self._max_cache_size:
            # Simple eviction of older half
            self._recent_fingerprints = set(list(self._recent_fingerprints)[self._max_cache_size // 2:])

        self._recent_fingerprints.add(fingerprint)
        return True

    def check_database_duplicate(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        acq_timestamp: datetime,
        sensor: str,
        fingerprint: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Checks PostgreSQL / SQLite for an existing observation with the same
        spatiotemporal coordinates and sensor.
        """
        if acq_timestamp.tzinfo is None:
            acq_utc = acq_timestamp.replace(tzinfo=timezone.utc)
        else:
            acq_utc = acq_timestamp.astimezone(timezone.utc)

        # 1. First check by exact coordinate bounding window (+/- 0.0001 deg ~ 11m) and timestamp
        existing = db.query(ThermalDetection.id, ThermalDetection.event_id).filter(
            ThermalDetection.latitude.between(latitude - 0.0001, latitude + 0.0001),
            ThermalDetection.longitude.between(longitude - 0.0001, longitude + 0.0001),
            ThermalDetection.sensor == sensor,
            ThermalDetection.acq_timestamp.between(
                acq_utc.replace(second=0, microsecond=0),
                acq_utc.replace(second=59, microsecond=999999)
            )
        ).first()

        if existing:
            return True, existing.id

        return False, None

    def update_event_chronology(
        self,
        event: ThermalEvent,
        observation_timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Preserves chronological integrity when observations arrive out-of-order (T3 -> T1 -> T2).
        Guarantees that:
        - first_seen is strictly MIN(first_seen, obs_ts)
        - last_seen is strictly MAX(last_seen, obs_ts)
        - Historical calculation integrity is preserved.
        """
        if observation_timestamp.tzinfo is None:
            obs_utc = observation_timestamp.replace(tzinfo=timezone.utc)
        else:
            obs_utc = observation_timestamp.astimezone(timezone.utc)

        was_out_of_order = False
        if event.first_seen:
            evt_first = event.first_seen.replace(tzinfo=timezone.utc) if event.first_seen.tzinfo is None else event.first_seen
            if obs_utc < evt_first:
                event.first_seen = obs_utc
                was_out_of_order = True
        else:
            event.first_seen = obs_utc

        if event.last_seen:
            evt_last = event.last_seen.replace(tzinfo=timezone.utc) if event.last_seen.tzinfo is None else event.last_seen
            if obs_utc > evt_last:
                event.last_seen = obs_utc
        else:
            event.last_seen = obs_utc

        return {
            "was_out_of_order": was_out_of_order,
            "first_seen": event.first_seen.isoformat(),
            "last_seen": event.last_seen.isoformat()
        }


idempotency_service = IdempotencyService()
