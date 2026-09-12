"""
JARVIS Phase 14: Case Management, Audit Governance & Intelligence Operations Engine
Implements:
- Deterministic investigation case lifecycle state machine
- RBAC policy enforcement and action authorization
- Write safety guard (PROPOSE ACTION -> Human APPROVE -> System EXECUTE)
- Append-only immutable audit trail logger
- Material assessment versioning with delta comparison
- Separate evidence review tracking (without modifying underlying observations)
- Formal evidence requests lifecycle
- Structured analyst notes (preventing JARVIS human impersonation)
- Reproducible report versioning
- Deterministic chronological case timeline synthesizer
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.domain import (
    InvestigationWorkspace,
    InvestigationAuditLog,
    AssessmentVersion,
    EvidenceReview,
    EvidenceRequest,
    CaseNote,
    ReportVersion,
    generate_uuid,
)
from backend.app.models.canonical import (
    CaseState,
    CaseActionType,
    EvidenceReviewStatus,
    HumanVerificationDecision,
    EvidenceRequestStatus,
    EvidenceRequestPriority,
    CaseTimelineEventType,
    CaseTimelineItem,
    AssessmentVersionRecord,
    EvidenceReviewRecord,
    EvidenceRequestRecord,
    CaseNoteRecord,
    ReportVersionRecord,
    InvestigationAuditRecord,
    CaseActionProposal,
)
from backend.app.models.jarvis_schemas import InvestigationStatus


class CaseStateTransitionError(ValueError):
    """Raised when an invalid case state transition is attempted."""
    pass


class CaseAuthorizationError(PermissionError):
    """Raised when an actor lacks permission for a governed case action."""
    pass


class WriteSafetyViolationError(RuntimeError):
    """Raised when an autonomous agent attempts to execute a protected write action directly."""
    pass


def _normalize_ts(dt: Any) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)
    if hasattr(dt, "tzinfo") and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class CaseManagementEngine:

    """
    Authoritative Case Lifecycle & Audit Governance Engine for AGNI-NETRA.
    Singleton service enforcing immutable records, valid state transitions,
    and human-in-the-loop verification invariants.
    """

    # 1. Deterministic State Transition Matrix
    ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
        CaseState.CREATED.value: [
            CaseState.ACTIVE.value,
            CaseState.INVESTIGATING.value,
            CaseState.CLOSED.value,
            InvestigationStatus.ACTIVE.value,
            InvestigationStatus.ANALYZING.value,
            InvestigationStatus.CLOSED.value,
        ],
        CaseState.ACTIVE.value: [
            CaseState.INVESTIGATING.value,
            CaseState.REQUIRES_REVIEW.value,
            CaseState.CLOSED.value,
            InvestigationStatus.ANALYZING.value,
            InvestigationStatus.REQUIRES_HUMAN_REVIEW.value,
            InvestigationStatus.CLOSED.value,
        ],
        CaseState.INVESTIGATING.value: [
            CaseState.REQUIRES_REVIEW.value,
            CaseState.CONTESTED.value,
            CaseState.RESOLVED.value,
            CaseState.CLOSED.value,
            InvestigationStatus.REQUIRES_HUMAN_REVIEW.value,
            InvestigationStatus.COMPLETED.value,
            InvestigationStatus.CLOSED.value,
        ],
        InvestigationStatus.ANALYZING.value: [
            CaseState.REQUIRES_REVIEW.value,
            CaseState.CONTESTED.value,
            CaseState.RESOLVED.value,
            CaseState.CLOSED.value,
            InvestigationStatus.REQUIRES_HUMAN_REVIEW.value,
            InvestigationStatus.COMPLETED.value,
            InvestigationStatus.CLOSED.value,
        ],
        CaseState.REQUIRES_REVIEW.value: [
            CaseState.VERIFIED.value,
            CaseState.CONTESTED.value,
            CaseState.INVESTIGATING.value,
            CaseState.RESOLVED.value,
            CaseState.CLOSED.value,
            InvestigationStatus.ANALYZING.value,
            InvestigationStatus.COMPLETED.value,
            InvestigationStatus.CLOSED.value,
        ],
        InvestigationStatus.REQUIRES_HUMAN_REVIEW.value: [
            CaseState.VERIFIED.value,
            CaseState.CONTESTED.value,
            CaseState.INVESTIGATING.value,
            CaseState.RESOLVED.value,
            CaseState.CLOSED.value,
            InvestigationStatus.ANALYZING.value,
            InvestigationStatus.COMPLETED.value,
            InvestigationStatus.CLOSED.value,
        ],
        CaseState.VERIFIED.value: [
            CaseState.RESOLVED.value,
            CaseState.CONTESTED.value,
            CaseState.CLOSED.value,
            InvestigationStatus.COMPLETED.value,
            InvestigationStatus.CLOSED.value,
        ],
        CaseState.CONTESTED.value: [
            CaseState.INVESTIGATING.value,
            CaseState.REQUIRES_REVIEW.value,
            CaseState.RESOLVED.value,
            CaseState.CLOSED.value,
            InvestigationStatus.ANALYZING.value,
            InvestigationStatus.REQUIRES_HUMAN_REVIEW.value,
            InvestigationStatus.COMPLETED.value,
            InvestigationStatus.CLOSED.value,
        ],
        CaseState.RESOLVED.value: [
            CaseState.CLOSED.value,
            CaseState.ACTIVE.value,
            CaseState.INVESTIGATING.value,
            InvestigationStatus.CLOSED.value,
            InvestigationStatus.ACTIVE.value,
        ],
        InvestigationStatus.COMPLETED.value: [
            CaseState.CLOSED.value,
            CaseState.ACTIVE.value,
            CaseState.INVESTIGATING.value,
            InvestigationStatus.CLOSED.value,
            InvestigationStatus.ACTIVE.value,
        ],
        CaseState.CLOSED.value: [
            CaseState.ACTIVE.value,
            CaseState.INVESTIGATING.value,
            InvestigationStatus.ACTIVE.value,
        ],
    }

    # 2. RBAC Policy Matrix
    ACTION_PERMISSIONS: Dict[str, List[str]] = {
        CaseActionType.OPEN_CASE.value: ["ADMIN", "ANALYST", "AGENCY"],
        CaseActionType.START_INVESTIGATION.value: ["ADMIN", "ANALYST", "AGENCY"],
        CaseActionType.REQUEST_REVIEW.value: ["ADMIN", "ANALYST", "AGENCY"],
        CaseActionType.VERIFY.value: ["ADMIN", "ANALYST"],
        CaseActionType.REJECT.value: ["ADMIN", "ANALYST"],
        CaseActionType.MARK_INCONCLUSIVE.value: ["ADMIN", "ANALYST"],
        CaseActionType.REQUEST_MORE_EVIDENCE.value: ["ADMIN", "ANALYST", "AGENCY", "RESEARCHER"],
        CaseActionType.ADD_NOTE.value: ["ADMIN", "ANALYST", "AGENCY", "RESEARCHER"],
        CaseActionType.ADD_EVIDENCE_REFERENCE.value: ["ADMIN", "ANALYST", "AGENCY"],
        CaseActionType.ESCALATE.value: ["ADMIN", "ANALYST", "AGENCY"],
        CaseActionType.RESOLVE.value: ["ADMIN", "ANALYST"],
        CaseActionType.CLOSE.value: ["ADMIN", "ANALYST"],
        CaseActionType.REOPEN.value: ["ADMIN", "ANALYST", "AGENCY"],
        "REVIEW_EVIDENCE": ["ADMIN", "ANALYST"],
        "GENERATE_REPORT": ["ADMIN", "ANALYST", "AGENCY", "RESEARCHER", "INDUSTRY"],
        "VIEW_PUBLIC_CASE": ["ADMIN", "ANALYST", "AGENCY", "RESEARCHER", "INDUSTRY", "PUBLIC"],
    }

    # 3. Protected Actions Requiring Human Confirmation (Write Safety)
    PROTECTED_ACTIONS = {
        CaseActionType.CLOSE.value,
        CaseActionType.VERIFY.value,
        CaseActionType.REJECT.value,
        CaseActionType.RESOLVE.value,
    }

    @classmethod
    def validate_transition(cls, current_state: str, new_state: str) -> bool:
        """
        Validates whether transitioning from current_state to new_state is permitted.
        Raises CaseStateTransitionError if illegal.
        """
        curr = current_state.upper()
        target = new_state.upper()

        if curr == target:
            return True  # Idempotent re-affirmation

        allowed = cls.ALLOWED_TRANSITIONS.get(curr, [])
        if target not in allowed:
            raise CaseStateTransitionError(
                f"Invalid case state transition from '{curr}' to '{target}'. "
                f"Permitted transitions from '{curr}' are: {allowed}"
            )
        return True

    @classmethod
    def check_authorization(cls, actor_role: str, action: str) -> bool:
        """
        Checks if actor_role is authorized to execute action.
        Raises CaseAuthorizationError if denied.
        """
        role = (actor_role or "PUBLIC").upper()
        act = action.upper()
        permitted_roles = cls.ACTION_PERMISSIONS.get(act, ["ADMIN"])

        if role not in permitted_roles:
            raise CaseAuthorizationError(
                f"Actor role '{role}' is not authorized to execute case action '{act}'. "
                f"Requires one of: {permitted_roles}"
            )
        return True

    @classmethod
    def create_audit_entry(
        cls,
        db: Session,
        case_id: str,
        actor_id: str,
        actor_role: str,
        action: str,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        reason: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
        assessment_version: int = 1,
        provenance_metadata: Optional[Dict[str, Any]] = None,
    ) -> InvestigationAuditLog:
        """
        Appends an immutable audit log entry.
        Never allows in-place mutation of prior entries.
        """
        now = datetime.now(timezone.utc)
        audit_uuid = f"AUD-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        audit_payload = {
            "audit_id": audit_uuid,
            "case_id": case_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "timestamp": now.isoformat(),
            "action": action,
            "previous_state": previous_state,
            "new_state": new_state,
            "reason": reason,
            "evidence_ids": evidence_ids or [],
            "assessment_version": assessment_version,
        }

        # Cryptographic hash of the audit entry content
        content_hash = hashlib.sha256(
            json.dumps(audit_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        provenance = {
            "checksum_sha256": content_hash,
            "tamper_evident": True,
            "logged_at": now.isoformat(),
            **(provenance_metadata or {}),
        }

        entry = InvestigationAuditLog(
            id=generate_uuid(),
            audit_id=audit_uuid,
            case_id=case_id,
            actor_id=actor_id,
            actor_role=actor_role,
            timestamp=now,
            action=action,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason,
            evidence_ids=evidence_ids or [],
            assessment_version=assessment_version,
            provenance=provenance,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @classmethod
    def propose_or_execute_action(
        cls,
        db: Session,
        workspace: InvestigationWorkspace,
        action: str,
        actor_id: str,
        actor_role: str,
        reason: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
        supporting_evidence: Optional[List[str]] = None,
        verifier: Optional[str] = None,
        confirm_governed_action: bool = False,
        is_autonomous_call: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluates write safety and state transitions for governed actions:
        - If action is protected AND called autonomously or without human confirmation:
          returns a structured PROPOSAL without executing the state transition.
        - If authorized and confirmed:
          executes the state transition and logs an immutable audit entry.
        """
        act = action.upper()
        cls.check_authorization(actor_role, act)

        # Map action to target state
        target_state_map = {
            CaseActionType.OPEN_CASE.value: CaseState.ACTIVE.value,
            CaseActionType.START_INVESTIGATION.value: CaseState.INVESTIGATING.value,
            CaseActionType.REQUEST_REVIEW.value: CaseState.REQUIRES_REVIEW.value,
            CaseActionType.VERIFY.value: CaseState.VERIFIED.value,
            CaseActionType.REJECT.value: CaseState.CONTESTED.value,
            CaseActionType.MARK_INCONCLUSIVE.value: CaseState.REQUIRES_REVIEW.value,
            CaseActionType.REQUEST_MORE_EVIDENCE.value: CaseState.INVESTIGATING.value,
            CaseActionType.RESOLVE.value: CaseState.RESOLVED.value,
            CaseActionType.CLOSE.value: CaseState.CLOSED.value,
            CaseActionType.REOPEN.value: CaseState.ACTIVE.value,
        }
        target_state = target_state_map.get(act, workspace.status)

        # Check write safety for protected actions
        if act in cls.PROTECTED_ACTIONS:
            if is_autonomous_call or not confirm_governed_action:
                # Return Action Proposal requiring human confirmation
                proposal = CaseActionProposal(
                    proposal_id=f"PROP-{uuid.uuid4().hex[:8].upper()}",
                    case_id=workspace.investigation_id,
                    recommended_action=CaseActionType(act),
                    target_state=CaseState(target_state) if target_state in CaseState.__members__ else CaseState.ACTIVE,
                    reason=reason or f"Action {act} proposed by system/analyst awaiting explicit human confirmation.",
                    requires_human_approval=True,
                    authorized_roles=cls.ACTION_PERMISSIONS.get(act, ["ADMIN", "ANALYST"]),
                    created_at=datetime.now(timezone.utc),
                )
                return {
                    "status": "PROPOSED",
                    "action": act,
                    "proposal": proposal.model_dump(),
                    "message": f"Action '{act}' requires explicit human approval. Action proposal generated.",
                    "requires_confirmation": True,
                    "workspace_status": workspace.status,
                }

        # If state change is required, validate transition
        prev_state = workspace.status
        if target_state != prev_state:
            cls.validate_transition(prev_state, target_state)
            workspace.status = target_state
            workspace.updated_at = datetime.now(timezone.utc)

        # Handle specific verification actions
        if act == CaseActionType.VERIFY.value:
            if not verifier or verifier.upper() == "JARVIS":
                raise ValueError("Verification requires an explicit human verifier; JARVIS cannot verify.")
            workspace.verification_status = HumanVerificationDecision.VERIFIED.value
        elif act == CaseActionType.REJECT.value:
            workspace.verification_status = HumanVerificationDecision.REJECTED.value
        elif act == CaseActionType.MARK_INCONCLUSIVE.value:
            workspace.verification_status = HumanVerificationDecision.INCONCLUSIVE.value
        elif act == CaseActionType.REQUEST_MORE_EVIDENCE.value:
            workspace.verification_status = HumanVerificationDecision.NEEDS_MORE_EVIDENCE.value

        db.add(workspace)
        db.commit()
        db.refresh(workspace)

        # Retrieve current assessment version
        curr_ver = (
            db.query(AssessmentVersion)
            .filter(AssessmentVersion.case_id == workspace.investigation_id)
            .count()
        ) or 1

        # Create immutable audit record
        audit_entry = cls.create_audit_entry(
            db=db,
            case_id=workspace.investigation_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action=act,
            previous_state=prev_state,
            new_state=workspace.status,
            reason=reason,
            evidence_ids=evidence_ids or [],
            assessment_version=curr_ver,
            provenance_metadata={"supporting_evidence": supporting_evidence or []},
        )

        return {
            "status": "EXECUTED",
            "action": act,
            "previous_state": prev_state,
            "new_state": workspace.status,
            "audit_id": audit_entry.audit_id,
            "verification_status": workspace.verification_status,
            "message": f"Action '{act}' successfully executed and logged to audit trail.",
        }

    @classmethod
    def record_assessment_version(
        cls,
        db: Session,
        case_id: str,
        assessment_dict: Dict[str, Any],
        created_by: str,
        trigger: str,
    ) -> AssessmentVersion:
        """
        Creates an immutable snapshot of an assessment.
        Calculates evidence_delta and uncertainty_delta compared to prior version.
        Never overwrites previous versions.
        """
        # Find latest version
        prior_ver = (
            db.query(AssessmentVersion)
            .filter(AssessmentVersion.case_id == case_id)
            .order_by(desc(AssessmentVersion.version_number))
            .first()
        )

        next_ver_num = (prior_ver.version_number + 1) if prior_ver else 1
        version_id = f"VER-{case_id}-{next_ver_num:03d}"

        # Calculate deltas
        evidence_delta: Dict[str, Any] = {"added_evidence": [], "removed_evidence": [], "total_evidence_count": 0}
        uncertainty_delta: Dict[str, Any] = {"prior_level": None, "current_level": None, "score_delta": 0.0}

        curr_ev_ids = set(assessment_dict.get("structured_statements", {}).keys()) or set()
        if "next_best_evidence" in assessment_dict:
            curr_ev_ids.update([f"REC-{i}" for i in range(len(assessment_dict["next_best_evidence"]))])

        if prior_ver and prior_ver.assessment:
            prior_assessment = prior_ver.assessment
            prior_ev_ids = set(prior_assessment.get("structured_statements", {}).keys()) or set()
            if "next_best_evidence" in prior_assessment:
                prior_ev_ids.update([f"REC-{i}" for i in range(len(prior_assessment["next_best_evidence"]))])

            evidence_delta["added_evidence"] = list(curr_ev_ids - prior_ev_ids)
            evidence_delta["removed_evidence"] = list(prior_ev_ids - curr_ev_ids)
            evidence_delta["total_evidence_count"] = len(curr_ev_ids)

            prior_unc = prior_assessment.get("uncertainty_summary", {}).get("level", "KNOWN")
            curr_unc = assessment_dict.get("uncertainty_summary", {}).get("level", "KNOWN")
            uncertainty_delta["prior_level"] = prior_unc
            uncertainty_delta["current_level"] = curr_unc

            prior_score = prior_assessment.get("evidence_support_score", 0.0)
            curr_score = assessment_dict.get("evidence_support_score", 0.0)
            uncertainty_delta["score_delta"] = round(curr_score - prior_score, 2)
        else:
            evidence_delta["added_evidence"] = list(curr_ev_ids)
            evidence_delta["total_evidence_count"] = len(curr_ev_ids)
            uncertainty_delta["current_level"] = assessment_dict.get("uncertainty_summary", {}).get("level", "KNOWN")
            uncertainty_delta["score_delta"] = round(assessment_dict.get("evidence_support_score", 0.0), 2)

        now = datetime.now(timezone.utc)
        payload_bytes = json.dumps(assessment_dict, sort_keys=True, default=str).encode("utf-8")
        ver_hash = hashlib.sha256(payload_bytes).hexdigest()

        provenance = {
            "sha256": ver_hash,
            "algorithm": "sha256",
            "timestamp": now.isoformat(),
            "created_by": created_by,
            "trigger": trigger,
        }

        new_version = AssessmentVersion(
            id=generate_uuid(),
            version_id=version_id,
            case_id=case_id,
            version_number=next_ver_num,
            assessment=assessment_dict,
            created_at=now,
            created_by=created_by,
            trigger=trigger,
            evidence_delta=evidence_delta,
            uncertainty_delta=uncertainty_delta,
            provenance=provenance,
        )
        db.add(new_version)
        db.commit()
        db.refresh(new_version)

        # Log audit record for assessment creation
        cls.create_audit_entry(
            db=db,
            case_id=case_id,
            actor_id=created_by,
            actor_role="SYSTEM" if created_by.upper().startswith("JARVIS") else "ANALYST",
            action="CREATE_ASSESSMENT_VERSION",
            previous_state=None,
            new_state=None,
            reason=f"Assessment version {next_ver_num} triggered by {trigger}.",
            assessment_version=next_ver_num,
            provenance_metadata={"version_id": version_id, "hash": ver_hash},
        )

        return new_version

    @classmethod
    def review_evidence_item(
        cls,
        db: Session,
        case_id: str,
        evidence_id: str,
        status: str,
        reviewer_id: str,
        reviewer_role: str,
        notes: Optional[str] = None,
    ) -> EvidenceReview:
        """
        Records an analyst's review decision for an evidence item.
        Does NOT alter the underlying raw observation.
        """
        cls.check_authorization(reviewer_role, "REVIEW_EVIDENCE")
        stat = status.upper()
        if stat not in EvidenceReviewStatus.__members__:
            raise ValueError(f"Invalid EvidenceReviewStatus '{stat}'. Permitted: {list(EvidenceReviewStatus.__members__.keys())}")

        review = (
            db.query(EvidenceReview)
            .filter(EvidenceReview.case_id == case_id, EvidenceReview.evidence_id == evidence_id)
            .first()
        )
        now = datetime.now(timezone.utc)
        if review:
            review.status = stat
            review.reviewer_id = reviewer_id
            review.reviewer_role = reviewer_role
            review.notes = notes
            review.updated_at = now
        else:
            review = EvidenceReview(
                id=generate_uuid(),
                review_id=f"REV-{uuid.uuid4().hex[:8].upper()}",
                case_id=case_id,
                evidence_id=evidence_id,
                status=stat,
                reviewer_id=reviewer_id,
                reviewer_role=reviewer_role,
                notes=notes,
                created_at=now,
                updated_at=now,
            )
            db.add(review)

        db.commit()
        db.refresh(review)

        # Log audit entry
        cls.create_audit_entry(
            db=db,
            case_id=case_id,
            actor_id=reviewer_id,
            actor_role=reviewer_role,
            action="REVIEW_EVIDENCE",
            reason=f"Evidence {evidence_id} marked as {stat}. Notes: {notes or 'None'}",
            evidence_ids=[evidence_id],
        )
        return review

    @classmethod
    def create_evidence_request(
        cls,
        db: Session,
        case_id: str,
        requested_source: str,
        reason: str,
        uncertainty_target: Optional[str],
        priority: str,
        requested_by: str,
        actor_role: str = "ANALYST",
    ) -> EvidenceRequest:
        """
        Creates a formal evidence request.
        Does NOT automatically trigger external data acquisition.
        """
        cls.check_authorization(actor_role, CaseActionType.REQUEST_MORE_EVIDENCE.value)
        prio = priority.upper()
        if prio not in EvidenceRequestPriority.__members__:
            prio = EvidenceRequestPriority.MEDIUM.value

        now = datetime.now(timezone.utc)
        req = EvidenceRequest(
            id=generate_uuid(),
            request_id=f"REQ-{uuid.uuid4().hex[:8].upper()}",
            case_id=case_id,
            requested_source=requested_source,
            reason=reason,
            uncertainty_target=uncertainty_target,
            priority=prio,
            status=EvidenceRequestStatus.OPEN.value,
            requested_by=requested_by,
            created_at=now,
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        # Log audit entry
        cls.create_audit_entry(
            db=db,
            case_id=case_id,
            actor_id=requested_by,
            actor_role=actor_role,
            action=CaseActionType.REQUEST_MORE_EVIDENCE.value,
            reason=f"Evidence request created for {requested_source}. Rationale: {reason}",
            provenance_metadata={"request_id": req.request_id, "priority": prio},
        )
        return req

    @classmethod
    def add_case_note(
        cls,
        db: Session,
        case_id: str,
        author: str,
        author_role: str,
        content: str,
        case_version: Optional[int] = None,
    ) -> CaseNote:
        """
        Adds a structured analyst note.
        Prohibits JARVIS from impersonating human analysts.
        """
        cls.check_authorization(author_role, CaseActionType.ADD_NOTE.value)
        if not author or author.strip().upper() == "JARVIS":
            raise ValueError("Case notes must be authored by a human user; JARVIS cannot author case notes.")

        now = datetime.now(timezone.utc)
        note = CaseNote(
            id=generate_uuid(),
            note_id=f"NOTE-{uuid.uuid4().hex[:8].upper()}",
            case_id=case_id,
            author=author,
            author_role=author_role,
            timestamp=now,
            content=content,
            case_version=case_version or 1,
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        cls.create_audit_entry(
            db=db,
            case_id=case_id,
            actor_id=author,
            actor_role=author_role,
            action=CaseActionType.ADD_NOTE.value,
            reason=f"Added case note: {content[:80]}...",
            assessment_version=case_version or 1,
        )
        return note

    @classmethod
    def record_report_version(
        cls,
        db: Session,
        case_id: str,
        presentation_mode: str,
        assessment_version: int,
        content_markdown: str,
        title: Optional[str] = None,
        file_path: Optional[str] = None,
        generated_by: str = "SYSTEM",
    ) -> ReportVersion:
        """
        Records a generated report for reproducible auditability.
        """
        prior_reports = (
            db.query(ReportVersion)
            .filter(ReportVersion.case_id == case_id)
            .order_by(desc(ReportVersion.report_version))
            .first()
        )
        next_rep_num = (prior_reports.report_version + 1) if prior_reports else 1
        now = datetime.now(timezone.utc)
        content_hash = hashlib.sha256(content_markdown.encode("utf-8")).hexdigest()

        rep = ReportVersion(
            id=generate_uuid(),
            report_id=f"REP-{case_id}-{next_rep_num:03d}",
            case_id=case_id,
            report_version=next_rep_num,
            presentation_mode=presentation_mode,
            assessment_version=assessment_version,
            generated_at=now,
            provenance={
                "hash": content_hash,
                "generated_by": generated_by,
                "assessment_version": assessment_version,
                "timestamp": now.isoformat(),
            },
            hash=content_hash,
            file_path=file_path,
            title=title or f"Intelligence Dossier {case_id} v{next_rep_num}",
            content_markdown=content_markdown,
        )
        db.add(rep)
        db.commit()
        db.refresh(rep)

        cls.create_audit_entry(
            db=db,
            case_id=case_id,
            actor_id=generated_by,
            actor_role="SYSTEM" if generated_by.upper().startswith("JARVIS") else "ANALYST",
            action="GENERATE_REPORT",
            reason=f"Generated report version {next_rep_num} (mode={presentation_mode})",
            assessment_version=assessment_version,
            provenance_metadata={"report_id": rep.report_id, "hash": content_hash},
        )
        return rep

    @classmethod
    def get_case_timeline(cls, db: Session, case_id: str) -> List[CaseTimelineItem]:
        """
        Synthesizes a deterministic chronological case timeline across:
        EVENT -> INVESTIGATION -> EVIDENCE -> ASSESSMENT -> CHANGE -> REVIEW -> VERIFICATION -> REPORT -> CLOSURE
        """
        items: List[CaseTimelineItem] = []

        workspace = (
            db.query(InvestigationWorkspace)
            .filter(InvestigationWorkspace.investigation_id == case_id)
            .first()
        )
        if not workspace:
            return []

        # 1. EVENT & INVESTIGATION creation
        created_time = _normalize_ts(workspace.created_at)
        items.append(
            CaseTimelineItem(
                timeline_id=f"TL-INV-{case_id[:8]}",
                case_id=case_id,
                event_type=CaseTimelineEventType.INVESTIGATION,
                timestamp=created_time,
                summary=f"Investigation workspace {case_id} initialized for target {workspace.target_event_id or 'unknown'}",
                actor_id=workspace.created_by or "JARVIS_ORCHESTRATOR",
                actor_role=workspace.user_role or "ANALYST",
                details={"status": workspace.status, "target_event_id": workspace.target_event_id},
            )
        )

        # 2. EVIDENCE items
        for ev in (workspace.structured_evidence or []):
            ev_ts = _normalize_ts(ev.get("timestamp") or created_time)

            items.append(
                CaseTimelineItem(
                    timeline_id=f"TL-EV-{ev.get('evidence_id', uuid.uuid4().hex[:6])}",
                    case_id=case_id,
                    event_type=CaseTimelineEventType.EVIDENCE,
                    timestamp=ev_ts,
                    summary=f"Evidence ingested: {ev.get('type', 'data')} from {ev.get('source', 'sensor')}",
                    actor_id="SYSTEM",
                    actor_role="SYSTEM",
                    details=ev,
                )
            )

        # 3. EVIDENCE REVIEWS
        reviews = db.query(EvidenceReview).filter(EvidenceReview.case_id == case_id).all()
        for rev in reviews:
            items.append(
                CaseTimelineItem(
                    timeline_id=f"TL-REV-{rev.review_id}",
                    case_id=case_id,
                    event_type=CaseTimelineEventType.REVIEW,
                    timestamp=_normalize_ts(rev.updated_at or rev.created_at),
                    summary=f"Evidence {rev.evidence_id} reviewed and marked {rev.status}",
                    actor_id=rev.reviewer_id or "ANALYST",
                    actor_role=rev.reviewer_role or "ANALYST",
                    details={"evidence_id": rev.evidence_id, "status": rev.status, "notes": rev.notes},
                )
            )

        # 4. ASSESSMENTS & CHANGES
        versions = (
            db.query(AssessmentVersion)
            .filter(AssessmentVersion.case_id == case_id)
            .order_by(AssessmentVersion.version_number)
            .all()
        )
        for ver in versions:
            items.append(
                CaseTimelineItem(
                    timeline_id=f"TL-ASS-{ver.version_id}",
                    case_id=case_id,
                    event_type=CaseTimelineEventType.ASSESSMENT,
                    timestamp=_normalize_ts(ver.created_at),
                    summary=f"Unified Assessment v{ver.version_number} synthesized ({ver.trigger})",
                    actor_id=ver.created_by,
                    actor_role="ANALYST",
                    details={
                        "version_number": ver.version_number,
                        "trigger": ver.trigger,
                        "uncertainty_delta": ver.uncertainty_delta,
                        "evidence_delta": ver.evidence_delta,
                    },
                )
            )

        # 5. AUDIT LOGS (Actions, Verifications, Closures)
        audits = (
            db.query(InvestigationAuditLog)
            .filter(InvestigationAuditLog.case_id == case_id)
            .order_by(InvestigationAuditLog.timestamp)
            .all()
        )
        for aud in audits:
            if aud.action in [CaseActionType.VERIFY.value, CaseActionType.REJECT.value, CaseActionType.MARK_INCONCLUSIVE.value]:
                items.append(
                    CaseTimelineItem(
                        timeline_id=f"TL-VER-{aud.audit_id}",
                        case_id=case_id,
                        event_type=CaseTimelineEventType.VERIFICATION,
                        timestamp=_normalize_ts(aud.timestamp),
                        summary=f"Human Verification Decision: {aud.action} by {aud.actor_id}",
                        actor_id=aud.actor_id,
                        actor_role=aud.actor_role,
                        details={"action": aud.action, "reason": aud.reason, "state": aud.new_state},
                    )
                )
            elif aud.action in [CaseActionType.CLOSE.value, CaseActionType.RESOLVE.value]:
                items.append(
                    CaseTimelineItem(
                        timeline_id=f"TL-CLS-{aud.audit_id}",
                        case_id=case_id,
                        event_type=CaseTimelineEventType.CLOSURE,
                        timestamp=_normalize_ts(aud.timestamp),
                        summary=f"Case closed/resolved ({aud.action}) by {aud.actor_id}",
                        actor_id=aud.actor_id,
                        actor_role=aud.actor_role,
                        details={"action": aud.action, "reason": aud.reason, "new_state": aud.new_state},
                    )
                )

        # 6. REPORTS
        reports = db.query(ReportVersion).filter(ReportVersion.case_id == case_id).all()
        for rep in reports:
            items.append(
                CaseTimelineItem(
                    timeline_id=f"TL-REP-{rep.report_id}",
                    case_id=case_id,
                    event_type=CaseTimelineEventType.REPORT,
                    timestamp=_normalize_ts(rep.generated_at),
                    summary=f"Report v{rep.report_version} generated ({rep.presentation_mode} mode)",
                    actor_id=rep.provenance.get("generated_by", "SYSTEM"),
                    actor_role="SYSTEM",
                    details={"report_version": rep.report_version, "mode": rep.presentation_mode, "hash": rep.hash},
                )
            )

        # Sort chronologically
        items.sort(key=lambda x: _normalize_ts(x.timestamp))
        return items



case_management_engine = CaseManagementEngine()
