from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user
from backend.app.models.domain import User, EvidenceRecord, ThermalEvent
from backend.app.models.schemas import EvidenceRecordCreate, EvidenceRecordOut

router = APIRouter()


@router.get("/event/{event_id}")
def get_event_evidence(
    event_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves all attached multimodal evidence records (satellite, GIS, field notes, photos, documents) for an event.
    """
    records = db.query(EvidenceRecord).filter(EvidenceRecord.event_id == event_id).order_by(EvidenceRecord.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "event_id": r.event_id,
            "evidence_type": r.evidence_type,
            "evidence_source": r.evidence_source,
            "title": r.title,
            "notes": r.notes,
            "evidence_data": r.evidence_data,
            "verified": r.verified,
            "verified_by": r.verified_by,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in records
    ]


@router.post("/", response_model=EvidenceRecordOut)
def add_evidence_record(
    payload: EvidenceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Attaches a new multimodal evidence item to a thermal event dossier.
    """
    event = db.query(ThermalEvent).filter(ThermalEvent.id == payload.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Thermal event not found")

    record = EvidenceRecord(
        event_id=payload.event_id,
        evidence_type=payload.evidence_type,
        evidence_source=payload.evidence_source,
        title=payload.title,
        notes=payload.notes,
        evidence_data=payload.evidence_data,
        verified=False,
        verified_by=None
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/{evidence_id}/verify")
def verify_evidence_record(
    evidence_id: str,
    verified: bool = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Allows authorized analysts or inspectors to corroborate or invalidate an evidence record.
    """
    record = db.query(EvidenceRecord).filter(EvidenceRecord.id == evidence_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Evidence record not found")

    record.verified = verified
    record.verified_by = current_user.email
    db.commit()
    db.refresh(record)
    return {
        "status": "UPDATED",
        "evidence_id": record.id,
        "verified": record.verified,
        "verified_by": record.verified_by
    }
