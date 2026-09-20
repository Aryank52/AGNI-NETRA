"""
AGNI-NETRA — WP3 Dead-Letter & Quarantine Service
Ensures zero silent data loss by capturing rejected, malformed, or transiently failed
records into a durable, recoverable quarantine ledger with sanitized debug payloads.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.domain import IngestionQuarantineModel
from backend.app.services.ingestion.failure_taxonomy import (
    IngestionFailureCategory, sanitize_error_message
)


SENSITIVE_KEYS = {
    "api_key", "map_key", "password", "token", "secret",
    "authorization", "auth", "key", "access_token"
}


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redacts secrets and authentication credentials from payloads."""
    clean: Dict[str, Any] = {}
    for k, v in payload.items():
        if str(k).lower() in SENSITIVE_KEYS:
            clean[k] = "[REDACTED]"
        elif isinstance(v, dict):
            clean[k] = sanitize_payload(v)
        elif isinstance(v, list):
            clean[k] = [sanitize_payload(item) if isinstance(item, dict) else item for item in v]
        else:
            clean[k] = v
    return clean


class DeadLetterService:
    """
    Manages quarantine capture, inspection, and recovery.
    """

    def record_quarantine(
        self,
        db: Session,
        provider: str,
        dataset: str,
        reason: str,
        error_category: IngestionFailureCategory = IngestionFailureCategory.UNKNOWN_FAILURE,
        source_record_id: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
        batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Durable capture of a rejected/failed record into `ingestion_quarantine`.
        """
        quarantine_id = f"QRN-{uuid.uuid4().hex[:8].upper()}"
        safe_payload = sanitize_payload(raw_payload or {})
        safe_reason = sanitize_error_message(reason)
        now_utc = datetime.now(timezone.utc)

        db_entry = IngestionQuarantineModel(
            id=str(uuid.uuid4()),
            quarantine_id=quarantine_id,
            batch_id=batch_id,
            provider=provider.upper(),
            dataset=dataset.upper(),
            source_record_id=source_record_id,
            reason=safe_reason,
            error_code=error_category.value,
            raw_safe_reference=safe_payload,
            detected_at=now_utc,
            resolution="UNRESOLVED"
        )
        db.add(db_entry)
        db.flush()

        return {
            "quarantine_id": quarantine_id,
            "batch_id": batch_id,
            "provider": provider.upper(),
            "dataset": dataset.upper(),
            "source_record_id": source_record_id,
            "reason": safe_reason,
            "error_code": error_category.value,
            "detected_at": now_utc.isoformat(),
            "status": "QUARANTINED"
        }

    def list_quarantined_records(
        self,
        db: Session,
        limit: int = 50,
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lists recent quarantined records for administrative inspection.
        """
        q = db.query(IngestionQuarantineModel)
        if provider:
            q = q.filter(IngestionQuarantineModel.provider == provider.upper())

        rows = q.order_by(IngestionQuarantineModel.detected_at.desc()).limit(limit).all()
        return [
            {
                "quarantine_id": r.quarantine_id,
                "batch_id": r.batch_id,
                "provider": r.provider,
                "dataset": r.dataset,
                "source_record_id": r.source_record_id,
                "reason": r.reason,
                "error_code": r.error_code,
                "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                "resolution": r.resolution,
                "payload_preview": r.raw_safe_reference
            }
            for r in rows
        ]


dead_letter_service = DeadLetterService()
