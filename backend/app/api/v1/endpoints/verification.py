from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.core.database import get_db
from backend.app.api.deps import require_analyst, get_current_active_user
from backend.app.models.domain import ThermalEvent, VerificationRecord, ModelPrediction, User, AuditLog
from backend.app.models.schemas import VerificationCreate, VerificationRecordOut, ThermalEventOut

router = APIRouter()


@router.get("/queue", response_model=List[ThermalEventOut])
def get_verification_queue(db: Session = Depends(get_db)):
    """
    Retrieves list of thermal events pending human analyst verification.
    Prioritizes low confidence predictions, abnormal baseline spikes, and candidate industrial sources.
    """
    events = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.prediction),
        joinedload(ThermalEvent.risk),
        joinedload(ThermalEvent.features)
    ).filter(ThermalEvent.status == "ACTIVE").all()

    # Filter events needing verification (Uncertain or low confidence < 0.65 or candidate or abnormal)
    queue = []
    for e in events:
        is_uncertain = e.prediction and (e.prediction.predicted_class == "Uncertain" or e.prediction.confidence < 0.65)
        is_candidate = e.facility_status == "CANDIDATE"
        is_critical = e.risk and e.risk.risk_level == "CRITICAL"
        
        if is_uncertain or is_candidate or is_critical:
            queue.append(e)

    return queue[:30]


@router.post("", response_model=VerificationRecordOut)
def submit_verification(
    verif_in: VerificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Records human-in-the-loop analyst verification / label correction.
    Feeds back into active learning ground-truth dataset.
    """
    event = db.query(ThermalEvent).filter(ThermalEvent.id == verif_in.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Thermal event not found")

    pred = db.query(ModelPrediction).filter(ModelPrediction.event_id == verif_in.event_id).first()
    orig_label = pred.predicted_class if pred else "Uncertain"

    record = VerificationRecord(
        event_id=verif_in.event_id,
        analyst_id=current_user.id,
        original_prediction=orig_label,
        verified_label=verif_in.verified_label,
        verification_action=verif_in.verification_action,
        notes=verif_in.notes,
        evidence_reviewed=verif_in.evidence_reviewed or {}
    )
    db.add(record)

    # If analyst corrected the prediction, update event status
    if verif_in.verification_action == "CORRECT" and pred:
        pred.predicted_class = verif_in.verified_label
        pred.confidence = 1.0
        pred.explanation_summary = f"Human verified and corrected by Analyst ({current_user.full_name}). Notes: {verif_in.notes or 'No notes'}."

    audit = AuditLog(
        user_id=current_user.id,
        action="VERIFY_EVENT",
        resource_type="ThermalEvent",
        resource_id=verif_in.event_id,
        details={
            "action": verif_in.verification_action,
            "orig": orig_label,
            "verified": verif_in.verified_label
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(record)

    return record
