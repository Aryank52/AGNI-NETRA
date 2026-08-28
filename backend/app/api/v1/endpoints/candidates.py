from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import require_analyst
from backend.app.models.domain import CandidateFacility, IndustrialFacility, User
from backend.app.models.schemas import CandidateFacilityOut
from backend.app.services.candidate_service import promote_candidate_to_verified_facility

router = APIRouter()


class CandidatePromotionRequest(BaseModel):
    verified_name: Optional[str] = None
    facility_type: Optional[str] = "REFINERY"
    notes: Optional[str] = None


@router.get("", response_model=List[CandidateFacilityOut])
def get_candidate_facilities(
    db: Session = Depends(get_db),
    state: Optional[str] = None,
    status_filter: Optional[str] = None
):
    """
    Retrieves discovered Candidate Industrial Facilities (USP: Unknown Thermal Source Discovery).
    """
    query = db.query(CandidateFacility)
    if state and state != "ALL":
        query = query.filter(CandidateFacility.state.ilike(f"%{state}%"))
    if status_filter and status_filter != "ALL":
        query = query.filter(CandidateFacility.status == status_filter)

    return query.order_by(CandidateFacility.industrial_context_score.desc()).all()


@router.post("/{candidate_id}/promote")
def promote_candidate_to_known(
    candidate_id: str,
    payload: Optional[CandidatePromotionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Promotes a candidate facility to the official Known & Verified Industrial Registry.
    Requires ANALYST or ADMIN role.
    """
    cand = db.query(CandidateFacility).filter(CandidateFacility.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate facility not found")

    v_name = (payload.verified_name if payload and payload.verified_name else f"Verified: {cand.name_label}")
    f_type = (payload.facility_type if payload and payload.facility_type else "REFINERY")
    notes = (payload.notes if payload else "Promoted via analyst HITL console")

    res = promote_candidate_to_verified_facility(
        db=db,
        candidate_id=candidate_id,
        verified_name=v_name,
        facility_type=f_type,
        analyst_id=current_user.id,
        notes=notes
    )

    return {"status": "SUCCESS", "result": res}
