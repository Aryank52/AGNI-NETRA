"""
AGNI-NETRA — JARVIS Guardian Agent
Enforces RBAC permissions, privacy masking for public users, mutation prevention,
and the non-negotiable operational dispatch gate invariant (ENABLE_OPERATIONAL_DISPATCH_GATE=False).
"""

from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.models.domain import AuditLog, User
from backend.app.services.jarvis.jarvis_policy import operating_policy, ENABLE_OPERATIONAL_DISPATCH_GATE


class JarvisGuardian:
    """
    Safety, Authorization, and Gatekeeper Agent for JARVIS.
    """

    ALLOWED_ROLES = ["ADMIN", "ANALYST", "AGENCY", "RESEARCHER", "INDUSTRY", "PUBLIC"]

    # Roles permitted to execute granular intelligence investigations
    INTEL_AUTHORIZED_ROLES = ["ADMIN", "ANALYST", "AGENCY", "RESEARCHER"]

    # Restricted tools for Public role
    PUBLIC_RESTRICTED_TOOLS = [
        "tool_get_event_spatial_context", "tool_get_shap_drivers",
        "tool_search_critical_anomalies_near_facilities", "tool_create_verification_case",
        "tool_generate_investigation_dossier", "tool_get_alerts"
    ]

    @staticmethod
    def authorize_action(
        user_role: str,
        action: str,
        target_tool: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates whether the user's role permits executing the specified action or tool.
        """
        role_upper = (user_role or "ANALYST").upper()
        if role_upper not in JarvisGuardian.ALLOWED_ROLES:
            return False, f"Access Denied: Unrecognized role '{user_role}'."

        # 1. Central Operating Policy Safety Check
        safe, violation, reason = operating_policy.evaluate_command_safety(
            command=action,
            user_role=role_upper
        )
        if not safe:
            return False, f"{violation}: {reason}"

        # 2. Public Role Specific Tool Restrictions
        if role_upper == "PUBLIC":
            if target_tool in JarvisGuardian.PUBLIC_RESTRICTED_TOOLS or any(w in action.lower() for w in ["dossier", "shap", "internal", "investigate", "trace"]):
                return False, f"Access Denied: Action requires authenticated Analyst or Agency clearance. Public users are limited to public advisory overviews."

        # 3. Industry Role Restrictions
        if role_upper == "INDUSTRY":
            if any(w in action.lower() for w in ["all facilities", "classified audit", "dispatch"]):
                return False, "Access Denied: Industry operators are restricted to authorized facilities."

        return True, None

    @staticmethod
    def mask_public_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strips sensitive internal coordinates, UUIDs, and proprietary facility data for PUBLIC users.
        """
        if not isinstance(data, dict):
            return data

        masked = {}
        for k, v in data.items():
            if k in ["id", "facility_id", "detection_id", "trace_id", "uuid"]:
                continue
            elif k in ["latitude", "longitude"]:
                # Round coordinates to 1 decimal place (~11km) for public privacy protection
                masked[k] = round(float(v), 1) if isinstance(v, (int, float)) else v
            elif isinstance(v, dict):
                masked[k] = JarvisGuardian.mask_public_data(v)
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                masked[k] = [JarvisGuardian.mask_public_data(item) for item in v]
            else:
                masked[k] = v
        return masked

    @staticmethod
    def log_audit_event(
        db: Session,
        user_role: str,
        command: str,
        intent: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """
        Safely records an audit entry for compliance, governance, and tracing.
        Never logs passwords, tokens, or private secrets.
        """
        try:
            audit = AuditLog(
                user_id=user_id,
                action="JARVIS_COMMAND_EXECUTION",
                resource_type="JARVIS_ORCHESTRATION_LAYER",
                resource_id=intent,
                details={
                    "command": command[:500],
                    "intent": intent,
                    "user_role": user_role,
                    "status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **(details or {})
                }
            )
            db.add(audit)
            db.commit()
        except Exception:
            db.rollback()


guardian = JarvisGuardian()
