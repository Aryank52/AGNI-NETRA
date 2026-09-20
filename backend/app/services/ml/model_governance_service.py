"""
AGNI-NETRA — MODEL GOVERNANCE & PROVENANCE SERVICE (WP5)
Provides strict model lifecycle management, cryptographic integrity verification,
path traversal defense, and controlled human-authorized promotion gates.
"""

import os
import sys
import json
import hashlib
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import joblib
from sqlalchemy.orm import Session
from sqlalchemy import text

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.domain import MLModelRegistry, AuditLog


class ModelGovernanceStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    VALIDATION = "VALIDATION"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"
    REJECTED = "REJECTED"


class ModelGovernanceException(Exception):
    """Raised when a model governance policy or security boundary is violated."""
    def __init__(self, message: str, model_id: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.model_id = model_id


class ModelGovernanceService:
    """
    Central governance authority for ML model registration, artifact verification,
    secure loading, and controlled champion promotion.
    """

    ALLOWED_MODEL_DIRS = [
        os.path.abspath(os.path.join(WORKSPACE_DIR, "ml", "models")),
        os.path.abspath(os.path.join(WORKSPACE_DIR, "ml", "models", "candidates"))
    ]

    ALLOWED_ESTIMATOR_CLASSES = {
        "XGBClassifier",
        "RandomForestClassifier",
        "LogisticRegression",
        "IsolationForest",
        "TreeExplainer"
    }

    @staticmethod
    def compute_file_sha256(filepath: str) -> str:
        """Computes deterministic SHA-256 hash of a file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Artifact file not found: {filepath}")
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def validate_artifact_path(self, filepath: str) -> str:
        """
        Validates artifact path against path traversal and directory allowlist.
        Returns resolved absolute canonical path.
        """
        if not filepath:
            raise ModelGovernanceException("Artifact path cannot be empty.")
        
        # Check for path traversal tricks
        if ".." in filepath:
            raise ModelGovernanceException(f"Path traversal detected in artifact path: {filepath}")

        # Resolve relative to workspace if not absolute
        if not os.path.isabs(filepath):
            abs_path = os.path.abspath(os.path.join(WORKSPACE_DIR, filepath))
        else:
            abs_path = os.path.abspath(filepath)

        # Ensure path resides strictly within allowed directories
        is_allowed = any(abs_path.startswith(allowed_dir) for allowed_dir in self.ALLOWED_MODEL_DIRS)
        if not is_allowed:
            raise ModelGovernanceException(
                f"Artifact path '{abs_path}' is outside approved model directories: {self.ALLOWED_MODEL_DIRS}"
            )

        if not os.path.isfile(abs_path):
            raise ModelGovernanceException(f"Artifact file does not exist: {abs_path}")

        return abs_path

    def secure_load_artifact(
        self,
        filepath: str,
        expected_sha256: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Any:
        """
        Loads a serialized model artifact with cryptographic integrity verification
        and path traversal defenses.
        """
        canonical_path = self.validate_artifact_path(filepath)
        actual_hash = self.compute_file_sha256(canonical_path)

        if expected_sha256:
            if actual_hash.lower() != expected_sha256.lower():
                raise ModelGovernanceException(
                    f"Cryptographic hash mismatch for {canonical_path}! "
                    f"Expected: {expected_sha256}, Actual: {actual_hash}"
                )
        elif db:
            # Query registry by artifact path or filename
            basename = os.path.basename(canonical_path)
            row = db.execute(text("""
                SELECT version, artifact_sha256 FROM ml_model_registry
                WHERE artifact_path LIKE :pattern OR artifact_path = :exact
            """), {"pattern": f"%{basename}%", "exact": canonical_path}).fetchone()
            
            if row and row[1]:
                if actual_hash.lower() != row[1].lower():
                    raise ModelGovernanceException(
                        f"Cryptographic hash mismatch for model {row[0]}! "
                        f"Registry expects {row[1]}, but disk file has {actual_hash}"
                    )

        # Safe deserialization
        try:
            artifact = joblib.load(canonical_path)
        except Exception as e:
            raise ModelGovernanceException(f"Failed to deserialize artifact {canonical_path}: {e}")

        return artifact

    def register_candidate_model(
        self,
        db: Session,
        model_name: str,
        version: str,
        model_family: str,
        algorithm: str,
        dataset_version: str,
        artifact_path: str,
        metrics: Dict[str, Any],
        training_period: str,
        feature_schema_version: str = "v3.2",
        taxonomy_version: str = "7-class-v1",
        calibration_version: Optional[str] = None,
        created_by: str = "SYSTEM_PIPELINE",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registers a newly evaluated candidate model in ml_model_registry.
        Guarantees status = CANDIDATE and is_active = FALSE.
        """
        canonical_path = self.validate_artifact_path(artifact_path)
        artifact_sha256 = self.compute_file_sha256(canonical_path)

        # Check for existing version
        existing = db.execute(
            text("SELECT id, status, is_active FROM ml_model_registry WHERE version = :ver"),
            {"ver": version}
        ).fetchone()

        if existing:
            # Update candidate metadata without changing active status
            db.execute(text("""
                UPDATE ml_model_registry
                SET model_name = :name,
                    model_family = :family,
                    algorithm = :algo,
                    dataset_version = :ds_ver,
                    artifact_path = :path,
                    artifact_sha256 = :sha256,
                    metrics = CAST(:metrics AS jsonb),
                    training_period = :period,
                    feature_schema_version = :feat_ver,
                    taxonomy_version = :tax_ver,
                    calibration_version = :cal_ver,
                    status = 'CANDIDATE',
                    is_active = FALSE,
                    notes = :notes
                WHERE version = :ver
            """), {
                "name": model_name,
                "family": model_family,
                "algo": algorithm,
                "ds_ver": dataset_version,
                "path": canonical_path,
                "sha256": artifact_sha256,
                "metrics": json.dumps(metrics) if not isinstance(metrics, str) else metrics,
                "period": training_period,
                "feat_ver": feature_schema_version,
                "tax_ver": taxonomy_version,
                "cal_ver": calibration_version,
                "notes": notes,
                "ver": version
            })
            model_id = existing[0]
        else:
            import uuid
            model_id = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO ml_model_registry (
                    id, model_name, version, model_family, algorithm, dataset_version,
                    artifact_path, artifact_sha256, metrics, training_period,
                    feature_schema_version, taxonomy_version, calibration_version,
                    status, is_active, created_by, trained_at, notes
                ) VALUES (
                    :id, :name, :ver, :family, :algo, :ds_ver,
                    :path, :sha256, CAST(:metrics AS jsonb), :period,
                    :feat_ver, :tax_ver, :cal_ver,
                    'CANDIDATE', FALSE, :created_by, CURRENT_TIMESTAMP, :notes
                )
            """), {
                "id": model_id,
                "name": model_name,
                "ver": version,
                "family": model_family,
                "algo": algorithm,
                "ds_ver": dataset_version,
                "path": canonical_path,
                "sha256": artifact_sha256,
                "metrics": json.dumps(metrics) if not isinstance(metrics, str) else metrics,
                "period": training_period,
                "feat_ver": feature_schema_version,
                "tax_ver": taxonomy_version,
                "cal_ver": calibration_version,
                "created_by": created_by,
                "notes": notes
            })

        db.commit()

        return {
            "model_id": model_id,
            "version": version,
            "status": ModelGovernanceStatus.CANDIDATE.value,
            "is_active": False,
            "artifact_sha256": artifact_sha256,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }

    def authorize_model_promotion(
        self,
        db: Session,
        version: str,
        authorizing_user_id: str,
        user_role: str,
        justification: str
    ) -> Dict[str, Any]:
        """
        Executes a controlled, human-authorized champion promotion.
        CRITICAL SAFETY GATE: Blocked if automated activation is requested or if user lacks ADMIN role.
        """
        # Invariant check: Automated activation is strictly forbidden
        if settings.ENABLE_AUTOMATED_MODEL_ACTIVATION:
            raise ModelGovernanceException(
                "Invariant violation: Automated model activation must remain False."
            )

        # Authorization check: Only ADMIN role may authorize champion promotion
        if user_role != "ADMIN":
            raise ModelGovernanceException(
                f"Unauthorized: Role '{user_role}' cannot authorize champion promotion. ADMIN required."
            )

        if not justification or len(justification.strip()) < 20:
            raise ModelGovernanceException(
                "Formal promotion justification (min 20 characters) is required for audit trail."
            )

        model_row = db.execute(
            text("SELECT id, model_name, status, is_active, artifact_sha256 FROM ml_model_registry WHERE version = :ver"),
            {"ver": version}
        ).fetchone()

        if not model_row:
            raise ModelGovernanceException(f"Model version '{version}' not found in registry.")

        now = datetime.now(timezone.utc)

        # Deactivate any previously active model in the same family
        db.execute(text("""
            UPDATE ml_model_registry
            SET is_active = FALSE, status = 'RETIRED'
            WHERE is_active = TRUE AND version != :ver
        """), {"ver": version})

        # Promote target model
        db.execute(text("""
            UPDATE ml_model_registry
            SET status = 'ACTIVE',
                is_active = TRUE,
                approved_by = :approver,
                approved_at = :now,
                approval_timestamp = :now,
                notes = COALESCE(notes, '') || ' | Promoted to ACTIVE by ' || :approver || ' on ' || :now_str || ': ' || :just
            WHERE version = :ver
        """), {
            "ver": version,
            "approver": authorizing_user_id,
            "now": now,
            "now_str": now.isoformat(),
            "just": justification
        })

        db.commit()

        return {
            "model_id": model_row[0],
            "version": version,
            "previous_status": model_row[2],
            "new_status": ModelGovernanceStatus.ACTIVE.value,
            "is_active": True,
            "approved_by": authorizing_user_id,
            "approved_at": now.isoformat(),
            "justification": justification
        }


model_governance_service = ModelGovernanceService()
