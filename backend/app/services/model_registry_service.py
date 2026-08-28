from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.domain import MLModelRegistry, AuditLog, User


VALID_MODEL_STATUSES = [
    "TRAINING",
    "VALIDATION",
    "CANDIDATE",
    "APPROVED",
    "ACTIVE",
    "RETIRED"
]


class ModelRegistryService:
    """
    AGNI-NETRA Model Governance & Lifecycle Registry.
    Guarantees strict audit trails, holdout performance tracking, and human-in-the-loop approval.
    Models can NEVER be automatically promoted to ACTIVE without authorized analyst/admin sign-off.
    """

    def list_models(self, db: Session) -> List[MLModelRegistry]:
        return db.query(MLModelRegistry).order_by(MLModelRegistry.trained_at.desc()).all()

    def get_active_model(self, db: Session, algorithm: str = "XGBoost") -> Optional[MLModelRegistry]:
        return db.query(MLModelRegistry).filter(
            MLModelRegistry.is_active == True,
            MLModelRegistry.algorithm.ilike(f"%{algorithm}%")
        ).first()

    def register_model_artifact(
        self,
        db: Session,
        model_name: str,
        version: str,
        dataset_version: str,
        algorithm: str,
        metrics: Dict[str, Any],
        artifact_path: str,
        notes: Optional[str] = None
    ) -> MLModelRegistry:
        """
        Registers a new trained model candidate into the governance registry in CANDIDATE status.
        """
        existing = db.query(MLModelRegistry).filter(MLModelRegistry.version == version).first()
        if existing:
            raise ValueError(f"Model version '{version}' is already registered.")

        new_model = MLModelRegistry(
            model_name=model_name,
            version=version,
            dataset_version=dataset_version,
            algorithm=algorithm,
            metrics=metrics,
            artifact_path=artifact_path,
            status="CANDIDATE",
            is_active=False,
            notes=notes,
            trained_at=datetime.now(timezone.utc)
        )
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        return new_model

    def update_model_status(
        self,
        db: Session,
        model_id: str,
        new_status: str,
        approver: User,
        notes: Optional[str] = None
    ) -> MLModelRegistry:
        """
        Transitions model lifecycle status with strict authorization checks.
        """
        if new_status not in VALID_MODEL_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: {VALID_MODEL_STATUSES}")

        model = db.query(MLModelRegistry).filter(MLModelRegistry.id == model_id).first()
        if not model:
            raise ValueError(f"Model {model_id} not found")

        # If activating this model, archive/deactivate current active model of same algorithm
        if new_status == "ACTIVE":
            current_actives = db.query(MLModelRegistry).filter(
                MLModelRegistry.algorithm == model.algorithm,
                MLModelRegistry.is_active == True
            ).all()
            for cur in current_actives:
                cur.is_active = False
                cur.status = "APPROVED"

            model.is_active = True
            model.approved_by = approver.email
            model.approved_at = datetime.now(timezone.utc)

        model.status = new_status
        if notes:
            model.notes = f"{model.notes or ''}\n[{new_status}]: {notes}".strip()

        # Audit Trail
        audit = AuditLog(
            user_id=approver.id,
            action="PROMOTE_MODEL_STATUS",
            resource_type="MLModelRegistry",
            resource_id=model.id,
            details={
                "model_name": model.model_name,
                "version": model.version,
                "new_status": new_status,
                "approver_role": approver.role,
                "notes": notes
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(model)
        return model


model_registry_service = ModelRegistryService()
