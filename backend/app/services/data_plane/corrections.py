"""
AGNI-NETRA JARVIS Phase 16: Record Corrections & Retraction Engine
Maintains lifecycle state transitions (ORIGINAL -> CORRECTED -> RETRACTED)
without physically erasing historical source records.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.domain import IngestionRecordModel
from backend.app.services.data_plane.models import RecordLifecycleState


class CorrectionsManager:
    """
    Manages non-destructive provider corrections and retractions.
    """

    @classmethod
    def apply_correction(
        cls,
        db: Session,
        ingestion_id: str,
        updated_fields: Dict[str, Any],
        reason: str,
        actor_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        """
        Marks record as CORRECTED and stores previous state in normalized payload.
        """
        rec = db.query(IngestionRecordModel).filter(IngestionRecordModel.ingestion_id == ingestion_id).first()
        if not rec:
            return {"status": "ERROR", "message": f"Record '{ingestion_id}' not found"}

        now_utc = datetime.now(timezone.utc)
        prev_state = {
            "latitude": rec.latitude,
            "longitude": rec.longitude,
            "lifecycle_state": rec.lifecycle_state,
            "normalized_payload": dict(rec.normalized_payload or {})
        }

        # Update fields
        for k, v in updated_fields.items():
            if hasattr(rec, k):
                setattr(rec, k, v)

        rec.lifecycle_state = RecordLifecycleState.CORRECTED.value
        norm = dict(rec.normalized_payload or {})
        norm["correction_audit"] = {
            "corrected_at": now_utc.isoformat(),
            "corrected_by": actor_id,
            "reason": reason,
            "previous_state": prev_state
        }
        rec.normalized_payload = norm
        db.commit()

        return {
            "status": "SUCCESS",
            "ingestion_id": ingestion_id,
            "lifecycle_state": RecordLifecycleState.CORRECTED.value,
            "reason": reason,
            "corrected_at": now_utc.isoformat()
        }

    @classmethod
    def apply_retraction(
        cls,
        db: Session,
        ingestion_id: str,
        reason: str,
        actor_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        """
        Marks record as RETRACTED without physical deletion.
        """
        rec = db.query(IngestionRecordModel).filter(IngestionRecordModel.ingestion_id == ingestion_id).first()
        if not rec:
            return {"status": "ERROR", "message": f"Record '{ingestion_id}' not found"}

        now_utc = datetime.now(timezone.utc)
        rec.lifecycle_state = RecordLifecycleState.RETRACTED.value
        norm = dict(rec.normalized_payload or {})
        norm["retraction_audit"] = {
            "retracted_at": now_utc.isoformat(),
            "retracted_by": actor_id,
            "reason": reason
        }
        rec.normalized_payload = norm
        db.commit()

        return {
            "status": "SUCCESS",
            "ingestion_id": ingestion_id,
            "lifecycle_state": RecordLifecycleState.RETRACTED.value,
            "reason": reason,
            "retracted_at": now_utc.isoformat(),
            "preserved": "Record retained in database with RETRACTED status"
        }


corrections_manager = CorrectionsManager()
