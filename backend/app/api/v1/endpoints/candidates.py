from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import require_analyst
from backend.app.models.domain import CandidateFacility, IndustrialFacility, User, AuditLog
from backend.app.models.schemas import CandidateFacilityOut

router = APIRouter()


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

    # Create canonical facility record
    new_fac = IndustrialFacility(
        name=f"Verified: {cand.name_label}",
        facility_type="OTHER",
        status="VERIFIED",
        source="PROMOTED_CANDIDATE",
        source_id=cand.id,
        state=cand.state,
        district=cand.district,
        latitude=cand.latitude,
        longitude=cand.longitude,
        confidence_score=0.92,
        operating_hours="24x7",
        contact_info={"promoted_by": current_user.email}
    )
    db.add(new_fac)
    cand.status = "PROMOTED"

    audit = AuditLog(
        user_id=current_user.id,
        action="PROMOTE_CANDIDATE",
        resource_type="CandidateFacility",
        resource_id=candidate_id,
        details={"candidate_label": cand.name_label}
    )
    db.add(audit)
    db.commit()

    return {"status": "SUCCESS", "message": f"Candidate promoted to Industrial Facility ID: {new_fac.id}"}
