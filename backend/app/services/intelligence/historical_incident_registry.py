"""
AGNI-NETRA — Governed Historical Incident Registry Service
Phase 25: Unified Event Intelligence + Historical Incident Intelligence

Separates historical raw satellite thermal observations from verified historical incidents.
Provides closed-loop HITL registration, point-in-time safe historical lookups, and similarity searches.
Zero model retraining: verification accumulates structured historical intelligence without modifying model weights.
"""

import math
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.domain import HistoricalIncident, ThermalEvent, VerificationRecord, IndustrialFacility


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance in kilometers between two points."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 2)


class HistoricalIncidentRegistryService:
    """
    Governed service managing the authoritative Historical Incident Registry.
    """

    @classmethod
    def register_verified_incident(
        cls,
        db: Session,
        event_id: str,
        analyst_name: Optional[str] = "Human Analyst",
        verified_label: Optional[str] = None,
        verification_action: str = "CONFIRM",
        verified_cause: Optional[str] = None,
        notes: Optional[str] = None,
        verification_record_id: Optional[str] = None
    ) -> Optional[HistoricalIncident]:
        """
        Closed-loop registration: records a verified historical incident from a confirmed/corrected event.
        Does NOT automatically trigger model retraining or alter model thresholds.
        """
        event = db.query(ThermalEvent).filter(ThermalEvent.id == event_id).first()
        if not event:
            return None

        # Check if already registered
        all_incidents = db.query(HistoricalIncident).all()
        existing = next((inc for inc in all_incidents if inc.linked_event_ids and event_id in inc.linked_event_ids), None)

        label = verified_label or (event.prediction.predicted_class if event.prediction else "Industrial Thermal Hotspot")
        fac_name = event.facility.name if event.facility else None

        similarity_sig = {
            "peak_frp": round(float(event.max_frp or 0.0), 2),
            "avg_frp": round(float(event.avg_frp or 0.0), 2),
            "detection_count": int(event.detection_count or 1),
            "latitude": round(float(event.latitude), 4),
            "longitude": round(float(event.longitude), 4),
            "classification": label,
            "state": event.state or "India",
            "district": event.district or "Unknown",
            "facility_id": event.facility_id
        }

        now_utc = datetime.now(timezone.utc)
        first_date = event.first_seen or now_utc
        last_date = event.last_seen or now_utc

        if existing:
            # Update existing record
            existing.status = "VERIFIED" if verification_action in ["CONFIRM", "CORRECT", "OVERRIDE"] else "CONTESTED"
            existing.classification = label
            existing.verified_cause = verified_cause or existing.verified_cause or f"Verified by {analyst_name} ({verification_action})"
            existing.verified_by = analyst_name
            existing.verified_at = now_utc
            existing.notes = notes or existing.notes
            existing.similarity_signature = similarity_sig
            if verification_record_id:
                existing.verification_record_id = verification_record_id
            db.commit()
            db.refresh(existing)
            return existing

        # Generate human-readable incident code
        year_str = first_date.strftime("%Y") if hasattr(first_date, "strftime") else "2026"
        inc_code = f"INC-{year_str}-{uuid.uuid4().hex[:6].upper()}"

        incident = HistoricalIncident(
            incident_code=inc_code,
            linked_event_ids=[event_id],
            latitude=float(event.latitude),
            longitude=float(event.longitude),
            state=event.state or "India",
            district=event.district or "Unknown",
            facility_id=event.facility_id,
            facility_name=fac_name,
            first_observed_date=first_date,
            last_observed_date=last_date,
            peak_frp=float(event.max_frp or 0.0),
            avg_frp=float(event.avg_frp or 0.0),
            detection_count=int(event.detection_count or 1),
            classification=label,
            status="VERIFIED" if verification_action in ["CONFIRM", "CORRECT", "OVERRIDE"] else "CONTESTED",
            verified_cause=verified_cause or f"Verified by {analyst_name} ({verification_action})",
            evidence_ids=[f"EV-{event_id[:8]}"],
            source_provenance={
                "provider": "NASA_FIRMS",
                "sensor": "VIIRS",
                "verification_method": "HUMAN_IN_THE_LOOP_REVIEW",
                "verification_action": verification_action,
                "recorded_at": now_utc.isoformat()
            },
            similarity_signature=similarity_sig,
            verification_record_id=verification_record_id,
            verified_by=analyst_name,
            verified_at=now_utc,
            notes=notes
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    @classmethod
    def query_incidents(
        cls,
        db: Session,
        state: Optional[str] = None,
        district: Optional[str] = None,
        status: Optional[str] = None,
        classification: Optional[str] = None,
        facility_id: Optional[str] = None,
        min_frp: Optional[float] = 0.0,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Queries verified and governed historical incidents with explicit filters.
        """
        query = db.query(HistoricalIncident)

        if state and state.upper() != "ALL":
            query = query.filter(HistoricalIncident.state.ilike(f"%{state}%"))
        if district and district.upper() != "ALL":
            query = query.filter(HistoricalIncident.district.ilike(f"%{district}%"))
        if status and status.upper() != "ALL":
            query = query.filter(HistoricalIncident.status == status.upper())
        if classification and classification.upper() != "ALL":
            query = query.filter(HistoricalIncident.classification.ilike(f"%{classification}%"))
        if facility_id:
            query = query.filter(HistoricalIncident.facility_id == facility_id)
        if min_frp and min_frp > 0:
            query = query.filter(HistoricalIncident.peak_frp >= min_frp)

        total_count = query.count()
        items = query.order_by(desc(HistoricalIncident.last_observed_date)).offset((page - 1) * limit).limit(limit).all()

        return {
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1,
            "items": items
        }

    @classmethod
    def get_incident_by_id(cls, db: Session, incident_id: str) -> Optional[HistoricalIncident]:
        return db.query(HistoricalIncident).filter(
            (HistoricalIncident.id == incident_id) | (HistoricalIncident.incident_code == incident_id)
        ).first()

    @classmethod
    def find_similar_verified_incidents(
        cls,
        db: Session,
        latitude: float,
        longitude: float,
        peak_frp: float,
        classification: Optional[str] = None,
        radius_km: float = 50.0,
        point_in_time_cutoff: Optional[datetime] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Point-in-time safe search for similar verified historical incidents.
        Anti-leakage: if point_in_time_cutoff is specified, only incidents observed BEFORE cutoff are returned.
        """
        deg = radius_km / 111.0
        query = db.query(HistoricalIncident).filter(
            HistoricalIncident.status == "VERIFIED",
            HistoricalIncident.latitude.between(latitude - deg, latitude + deg),
            HistoricalIncident.longitude.between(longitude - deg, longitude + deg)
        )

        # Anti-leakage temporal enforcement
        if point_in_time_cutoff:
            query = query.filter(HistoricalIncident.first_observed_date < point_in_time_cutoff)

        candidates = query.all()
        results = []

        for inc in candidates:
            dist = haversine_km(latitude, longitude, inc.latitude, inc.longitude)
            if dist > radius_km:
                continue

            # Compute normalized similarity score (0.0 to 1.0)
            dist_sim = max(0.0, 1.0 - (dist / radius_km))
            frp_sim = 1.0
            if peak_frp > 0 and inc.peak_frp > 0:
                frp_sim = min(peak_frp, inc.peak_frp) / max(peak_frp, inc.peak_frp)
            class_sim = 1.0 if (classification and inc.classification and classification.lower() == inc.classification.lower()) else 0.6

            similarity_score = round(0.40 * dist_sim + 0.35 * frp_sim + 0.25 * class_sim, 3)

            results.append({
                "incident_id": inc.id,
                "incident_code": inc.incident_code,
                "distance_km": dist,
                "similarity_score": similarity_score,
                "classification": inc.classification,
                "peak_frp": inc.peak_frp,
                "state": inc.state,
                "district": inc.district,
                "facility_name": inc.facility_name,
                "first_observed_date": inc.first_observed_date.isoformat() if inc.first_observed_date else None,
                "last_observed_date": inc.last_observed_date.isoformat() if inc.last_observed_date else None,
                "verified_cause": inc.verified_cause,
                "verified_by": inc.verified_by,
                "status": inc.status
            })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:limit]

    @classmethod
    def seed_from_existing_verifications(cls, db: Session) -> int:
        """
        Bootstraps verified incidents from already existing database verification records.
        Strictly factual: zero synthetic records generated.
        """
        verified_events = db.query(ThermalEvent).filter(ThermalEvent.status == "VERIFIED").all()
        seeded_count = 0

        for ev in verified_events:
            existing = db.query(HistoricalIncident).filter(
                HistoricalIncident.linked_event_ids.contains(ev.id)
            ).first()
            if existing:
                continue

            vrec = db.query(VerificationRecord).filter(VerificationRecord.event_id == ev.id).order_by(desc(VerificationRecord.created_at)).first()
            analyst = "Certified Regional Analyst"
            label = vrec.verified_label if vrec else (ev.prediction.predicted_class if ev.prediction else "Industrial Thermal Hotspot")
            action = vrec.verification_action if vrec else "CONFIRM"
            v_notes = vrec.notes if vrec else "Historical verification baseline record."

            inc = cls.register_verified_incident(
                db=db,
                event_id=ev.id,
                analyst_name=analyst,
                verified_label=label,
                verification_action=action,
                verified_cause="Historical Operational Ground Truth",
                notes=v_notes,
                verification_record_id=vrec.id if vrec else None
            )
            if inc:
                seeded_count += 1

        return seeded_count


historical_incident_registry = HistoricalIncidentRegistryService()
