from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from backend.app.core.database import get_db
from backend.app.models.domain import ThermalEvent
from backend.app.models.schemas import ThermalEventOut

router = APIRouter()


@router.get("", response_model=List[ThermalEventOut])
def get_anomalies(db: Session = Depends(get_db)):
    """
    Retrieves events exhibiting abnormal baseline spikes or behavioral anomalies.
    """
    events = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.prediction),
        joinedload(ThermalEvent.risk),
        joinedload(ThermalEvent.features)
    ).all()

    anomalies = []
    for e in events:
        is_abnormal = False
        if e.features and e.features.baseline_deviation_ratio >= 1.8:
            is_abnormal = True
        if e.risk and e.risk.abnormality_subscore >= 40.0:
            is_abnormal = True
        
        if is_abnormal:
            anomalies.append(e)

    return anomalies
