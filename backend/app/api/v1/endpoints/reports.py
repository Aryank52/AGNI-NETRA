from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload

from backend.app.core.database import get_db
from backend.app.models.domain import ThermalEvent, IndustrialFacility, Report, User
from backend.app.services.report_service import generate_event_pdf_report
from backend.app.api.deps import get_current_active_user, require_researcher

router = APIRouter()


@router.get("/event/{event_id}/download")
def download_event_pdf_report(
    event_id: str,
    db: Session = Depends(get_db)
):
    """
    Generates and downloads a formal AGNI-NETRA Intelligence Dossier PDF for a thermal event.
    """
    event = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.prediction),
        joinedload(ThermalEvent.risk),
        joinedload(ThermalEvent.features),
        joinedload(ThermalEvent.facility)
    ).filter(ThermalEvent.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Thermal event not found")

    event_data = {
        "event_code": event.event_code,
        "state": event.state,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "status": event.status,
        "detection_count": event.detection_count,
        "max_frp": event.max_frp,
        "avg_frp": event.avg_frp,
        "first_seen": event.first_seen,
        "last_seen": event.last_seen,
        "facility_status": event.facility_status,
        "landcover_class": event.landcover_class,
        "nearest_facility_distance_m": event.nearest_facility_distance_m
    }

    pred_data = None
    if event.prediction:
        pred_data = {
            "predicted_class": event.prediction.predicted_class,
            "confidence": event.prediction.confidence,
            "shap_values": event.prediction.shap_values,
            "explanation_summary": event.prediction.explanation_summary
        }

    risk_data = None
    if event.risk:
        risk_data = {
            "risk_level": event.risk.risk_level,
            "risk_score": event.risk.risk_score,
            "risk_reasons": event.risk.risk_reasons
        }

    fac_data = None
    if event.facility:
        fac_data = {
            "name": event.facility.name,
            "facility_type": event.facility.facility_type
        }

    pdf_bytes = generate_event_pdf_report(
        event_data=event_data,
        prediction_data=pred_data,
        risk_data=risk_data,
        facility_data=fac_data
    )

    filename = f"AGNI_NETRA_Report_{event.event_code}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
