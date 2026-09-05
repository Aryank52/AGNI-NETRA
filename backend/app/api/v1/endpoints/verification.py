from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.core.database import get_db
from backend.app.api.deps import require_analyst, get_current_active_user
from backend.app.models.domain import ThermalEvent, VerificationRecord, ModelPrediction, User, AuditLog
from backend.app.models.schemas import VerificationCreate, VerificationRecordOut, ThermalEventOut

router = APIRouter()


@router.get("", response_model=List[ThermalEventOut])
@router.get("/queue", response_model=List[ThermalEventOut])
def get_verification_queue(
    db: Session = Depends(get_db),
    priority_filter: Optional[str] = None,
    current_user: User = Depends(require_analyst)
):
    """
    Retrieves prioritized list of thermal events pending human analyst verification.
    Prioritizes low confidence predictions, high uncertainty, critical risk, and candidate industrial sources.
    """
    events = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.prediction),
        joinedload(ThermalEvent.risk),
        joinedload(ThermalEvent.features),
        joinedload(ThermalEvent.verifications)
    ).filter(ThermalEvent.status == "ACTIVE").all()

    queue = []
    for e in events:
        is_verified = len(e.verifications) > 0
        is_uncertain = e.prediction and (e.prediction.predicted_class == "Uncertain" or e.prediction.confidence < 0.70)
        is_candidate = e.facility_status == "CANDIDATE"
        is_critical = e.risk and e.risk.risk_level == "CRITICAL"

        if priority_filter == "HIGH_UNCERTAINTY" and not is_uncertain:
            continue
        if priority_filter == "CRITICAL_RISK" and not is_critical:
            continue
        if priority_filter == "CANDIDATES" and not is_candidate:
            continue

        if not is_verified or is_uncertain or is_candidate or is_critical:
            queue.append(e)

    return queue[:40]


@router.get("/history", response_model=List[VerificationRecordOut])
def get_verification_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Retrieves recent audit log of human-in-the-loop analyst decisions and label corrections.
    """
    records = db.query(VerificationRecord).order_by(VerificationRecord.created_at.desc()).limit(limit).all()
    return records


@router.post("", response_model=VerificationRecordOut)
def submit_verification(
    verif_in: VerificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Records human-in-the-loop analyst verification / label correction.
    Feeds back into active learning ground-truth dataset and compliance audit trail.
    """
    event = db.query(ThermalEvent).filter(ThermalEvent.id == verif_in.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Thermal event not found")

    pred = db.query(ModelPrediction).filter(ModelPrediction.event_id == verif_in.event_id).first()
    orig_label = pred.predicted_class if pred else "Uncertain"

    action = verif_in.verification_action.upper()

    record = VerificationRecord(
        event_id=verif_in.event_id,
        analyst_id=current_user.id,
        original_prediction=orig_label,
        verified_label=verif_in.verified_label,
        verification_action=action,
        notes=verif_in.notes,
        evidence_reviewed=verif_in.evidence_reviewed or {}
    )
    db.add(record)

    # If analyst confirmed or overridden the prediction, update event & prediction status
    if action in ["CORRECT", "OVERRIDE"] and pred:
        pred.predicted_class = verif_in.verified_label
        pred.confidence = 1.0
        pred.explanation_summary = f"Human verified and corrected to '{verif_in.verified_label}' by Analyst ({current_user.full_name}). Notes: {verif_in.notes or 'None'}."
        event.status = "VERIFIED"
    elif action == "CONFIRM" and pred:
        pred.confidence = max(0.95, pred.confidence)
        pred.explanation_summary = f"Human analyst ({current_user.full_name}) confirmed '{pred.predicted_class}'. Notes: {verif_in.notes or 'None'}."
        event.status = "VERIFIED"
    elif action == "REJECT":
        event.status = "DISMISSED"

    audit = AuditLog(
        user_id=current_user.id,
        action=f"VERIFY_EVENT_{action}",
        resource_type="ThermalEvent",
        resource_id=verif_in.event_id,
        details={
            "action": action,
            "original_class": orig_label,
            "verified_class": verif_in.verified_label,
            "analyst": current_user.email
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(record)

    return record
