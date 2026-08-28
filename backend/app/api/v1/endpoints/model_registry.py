from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import require_analyst, require_admin
from backend.app.models.domain import MLModelRegistry, DatasetRegistry, User
from backend.app.models.schemas import MLModelRegistryOut, MLModelStatusUpdate, DatasetRegistryOut
from backend.app.services.model_registry_service import model_registry_service

router = APIRouter()


@router.get("/models", response_model=List[MLModelRegistryOut])
def get_registered_models(db: Session = Depends(get_db)):
    """
    Retrieves all machine learning models in the governance registry with evaluation metrics and lifecycle statuses.
    """
    return model_registry_service.list_models(db)


@router.post("/models/{model_id}/status", response_model=MLModelRegistryOut)
def update_model_lifecycle_status(
    model_id: str,
    payload: MLModelStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Updates the lifecycle status of a model (e.g. CANDIDATE -> APPROVED -> ACTIVE).
    Requires ANALYST or ADMIN role with full audit logging.
    """
    try:
        updated = model_registry_service.update_model_status(
            db=db,
            model_id=model_id,
            new_status=payload.status,
            approver=current_user,
            notes=payload.notes
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/datasets", response_model=List[DatasetRegistryOut])
def get_registered_datasets(db: Session = Depends(get_db)):
    """
    Retrieves all partitioned training and validation datasets with provenance metadata.
    """
    return db.query(DatasetRegistry).order_by(DatasetRegistry.created_at.desc()).all()
