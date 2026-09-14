"""
AGNI-NETRA — JARVIS API Router
REST API endpoints for the Autonomous Intelligence & Command Layer.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.api.deps import get_current_active_user, get_optional_current_user
from backend.app.models.domain import User, InvestigationWorkspace
from backend.app.models.jarvis_schemas import (
    JarvisCommandRequest, JarvisResponse, ExecutionTrace, JarvisToolInfo, SessionContext,
    InvestigationWorkspaceSchema, JarvisMission, JarvisMissionRequest,
    SituationalSnapshot, SituationalChange, AttentionItem, IndiaSituationBrief, SixtySecondBrief,
    TimelineEvent, SituationalBriefRequest
)
from backend.app.services.jarvis.jarvis_situational_service import jarvis_situational_service
from backend.app.services.jarvis.jarvis_orchestrator import (
    master_orchestrator, WORKING_MEMORY_CACHE
)
from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
from backend.app.services.jarvis.jarvis_memory import session_memory
from backend.app.services.jarvis.jarvis_workspace import workspace_manager

router = APIRouter()


@router.post("/command", response_model=JarvisResponse)
def execute_jarvis_command(
    req: JarvisCommandRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> JarvisResponse:
    """
    Executes an autonomous agentic command through the JARVIS Master Orchestrator.
    Parses intent, generates declarative execution plan, coordinates specialist agents,
    fuses evidence, and enforces safety gates.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None
    response = master_orchestrator.execute_command(db, req, user_role=user_role, user_id=user_id)
    return response


@router.get("/trace/{trace_id}", response_model=ExecutionTrace)
def get_execution_trace(
    trace_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> ExecutionTrace:
    """
    Retrieves the complete step-by-step execution trace for an audited JARVIS command.
    """
    trace = WORKING_MEMORY_CACHE.get(trace_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution trace '{trace_id}' not found in active working memory."
        )
    return trace


@router.get("/tools", response_model=List[JarvisToolInfo])
def list_jarvis_tools(
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[JarvisToolInfo]:
    """
    Returns the catalog of registered, typed, and permission-controlled tools.
    """
    return JarvisToolRegistry.get_registered_tools()


@router.get("/status")
def get_jarvis_system_status(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns operational health, FIRMS ingestion telemetry, database stats, and safety configuration.
    """
    return JarvisToolRegistry.tool_get_system_status(db)


@router.get("/session/{session_id}", response_model=SessionContext)
def get_session_context(
    session_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> SessionContext:
    """
    Retrieves the scoped session memory and recent command history for an active operator.
    """
    return session_memory.get_or_create_session(session_id)


@router.post("/investigate", response_model=JarvisResponse)
def investigate_event_shortcut(
    event_ref: str = Query(..., description="Event code or UUID to investigate"),
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> JarvisResponse:
    """
    Direct structured investigation shortcut mapping to a full JARVIS investigation plan.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None
    req = JarvisCommandRequest(
        command=f"JARVIS, investigate Event {event_ref}",
        session_id=session_id
    )
    return master_orchestrator.execute_command(db, req, user_role=user_role, user_id=user_id)


# =================================================================================
# INVESTIGATION WORKSPACE ENDPOINTS (JARVIS PHASE 3)
# =================================================================================

@router.get("/investigations", response_model=List[InvestigationWorkspaceSchema])
def list_investigations(
    status_filter: Optional[str] = Query(None, description="Optional status filter"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[InvestigationWorkspace]:
    """
    Lists intelligence investigations with RBAC enforcement.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None

    if user_role == "PUBLIC":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role 'PUBLIC' is not authorized to access internal investigations."
        )

    query = db.query(InvestigationWorkspace)
    if user_role not in ["ADMIN", "AGENCY"]:
        query = query.filter(
            (InvestigationWorkspace.created_by == user_id) | (InvestigationWorkspace.created_by == None)
        )

    if status_filter:
        query = query.filter(InvestigationWorkspace.status == status_filter.upper())

    return query.order_by(InvestigationWorkspace.updated_at.desc()).offset(offset).limit(limit).all()


@router.post("/investigations", response_model=InvestigationWorkspaceSchema)
def create_investigation_workspace(
    session_id: str = Query(..., description="Session identifier"),
    target_event_id: Optional[str] = Query(None, description="Optional initial target event ID"),
    primary_objective: Optional[str] = Query(None, description="Optional investigation objective"),
    target_region: Optional[str] = Query(None, description="Optional target geographic state/region"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> InvestigationWorkspace:
    """
    Explicitly initializes and persists a new Investigation Workspace.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None

    if user_role == "PUBLIC":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role 'PUBLIC' is not authorized to create intelligence investigations."
        )

    return workspace_manager.create_workspace(
        db=db,
        session_id=session_id,
        user_role=user_role,
        user_id=user_id,
        primary_objective=primary_objective,
        target_event_id=target_event_id,
        target_region=target_region
    )


@router.get("/investigations/{investigation_id}", response_model=InvestigationWorkspaceSchema)
def get_investigation_workspace(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> InvestigationWorkspace:
    """
    Retrieves full details of a specific investigation workspace.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None

    workspace, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if err:
        if "Access Denied" in err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)

    return workspace


@router.get("/investigations/{investigation_id}/evidence")
def get_investigation_evidence(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves structured epistemic evidence for an investigation workspace.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None

    workspace, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if err:
        if "Access Denied" in err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)

    return {
        "investigation_id": workspace.investigation_id,
        "target_event_id": workspace.target_event_id,
        "evidence_summary": workspace.evidence_summary,
        "classification_summary": workspace.classification_summary,
        "risk_summary": workspace.risk_summary,
        "anomaly_summary": workspace.anomaly_summary,
        "spatial_summary": workspace.spatial_summary,
        "structured_evidence": workspace.structured_evidence,
        "open_questions": workspace.open_questions,
        "resolved_questions": workspace.resolved_questions
    }


@router.get("/investigations/{investigation_id}/history")
def get_investigation_history(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves the ordered command and execution trace history for an investigation workspace.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None

    workspace, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if err:
        if "Access Denied" in err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)

    return {
        "investigation_id": workspace.investigation_id,
        "command_history": workspace.command_history,
        "execution_ids": workspace.execution_ids
    }


@router.post("/investigations/{investigation_id}/command", response_model=JarvisResponse)
def execute_investigation_scoped_command(
    investigation_id: str,
    req: JarvisCommandRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> JarvisResponse:
    """
    Executes a command scoped strictly to the specified active investigation workspace.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None

    workspace, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if err:
        if "Access Denied" in err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)

    req.investigation_id = investigation_id
    req.session_id = workspace.session_id
    return master_orchestrator.execute_command(db, req, user_role=user_role, user_id=user_id)


@router.post("/investigations/{investigation_id}/refresh", response_model=JarvisResponse)
def refresh_investigation_evidence(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> JarvisResponse:
    """
    Forces full re-execution and freshness update for an active investigation workspace.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None

    workspace, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if err:
        if "Access Denied" in err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)

    target = workspace.target_event_id or "EVT-827"
    cmd_str = f"JARVIS, refresh the investigation for Event {target}"
    req = JarvisCommandRequest(
        command=cmd_str,
        session_id=workspace.session_id,
        investigation_id=investigation_id
    )
    return master_orchestrator.execute_command(db, req, user_role=user_role, user_id=user_id)


@router.post("/investigations/{investigation_id}/close")
def close_investigation_workspace(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Transitions workspace status to CLOSED while preserving audit trails and reporting any unresolved actions.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None

    workspace, err, warnings = workspace_manager.close_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if err:
        if "Access Denied" in err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)

    return {
        "investigation_id": workspace.investigation_id,
        "status": workspace.status,
        "warnings": warnings,
        "message": f"Investigation Case {workspace.investigation_id} closed successfully. Historical audit preserved."
    }


@router.get("/investigations/{investigation_id}/sources")
def get_investigation_sources(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves sources used, geographic coverage profile, missing sources, and provenance records for a specific investigation.
    Enforces RBAC access control.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None

    workspace, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if err:
        if "Access Denied" in err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)

    return {
        "investigation_id": workspace.investigation_id,
        "coverage_profile": workspace.coverage_profile or "INDIA",
        "sources_used": workspace.sources_used or ["FIRMS", "OSM", "CEA", "PARIVESH", "IBM_MINING", "ISRO_BHUVAN", "FSI", "ADMIN_BOUNDARIES"],
        "missing_sources": workspace.missing_sources or ["WEATHER_INTELLIGENCE", "HIGH_RES_OPTICAL"],
        "partial_sources": workspace.partial_sources or ["PARIVESH"],
        "source_availability_matrix": workspace.source_availability_matrix or {},
        "provenance_records": workspace.provenance_records or []
    }


# =========================================================================
# Phase 22: Mission Mode & Governed Intelligence Endpoints
# =========================================================================

@router.post("/mission", response_model=JarvisMission)
def execute_intelligence_mission(
    req: JarvisMissionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> JarvisMission:
    """
    Phase 22 Governed Intelligence Mission Orchestration Endpoint.
    Executes controlled, evidence-grounded intelligence missions for sovereign India.
    """
    from backend.app.services.jarvis.jarvis_mission_service import jarvis_mission_service
    user_role = current_user.role if current_user else req.user_role
    user_id = current_user.id if current_user else (req.user_id or "ANALYST")
    return jarvis_mission_service.execute_mission(
        db=db,
        request=req,
        user_id=user_id,
        user_role=user_role,
        session_id=req.session_id
    )


@router.get("/governed-tools")
def list_governed_mission_tools(
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Returns the Phase 22 catalog of registered, typed, governed intelligence tools.
    """
    from backend.app.services.jarvis.jarvis_mission_service import JarvisGovernedToolRegistry
    return JarvisGovernedToolRegistry.list_tools()


@router.get("/mission/active")
def get_active_mission(
    session_id: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Optional[Dict[str, Any]]:
    """
    Retrieves the most recent mission executed in the current session.
    """
    from backend.app.services.jarvis.jarvis_mission_service import mission_memory
    m = mission_memory.get_current_mission()
    return m.model_dump() if m else None


# =========================================================================
# Phase 23: Situational Awareness & Command Center Endpoints
# =========================================================================

@router.get("/situational/snapshot", response_model=SituationalSnapshot)
def get_situational_snapshot(
    time_window: str = Query("LAST_30_DAYS"),
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> SituationalSnapshot:
    """
    Returns the canonical SituationalSnapshot across Sovereign India.
    Derives all counts and attention queues from real database state.
    """
    user_role = current_user.role if current_user else "ANALYST"
    snap = jarvis_situational_service.generate_snapshot(db=db, time_window=time_window, state=state)
    if user_role == "PUBLIC":
        snap.major_uncertainties = [u for u in snap.major_uncertainties if "unverified" not in u.lower()]
        for item in snap.attention_items:
            item.coordinates = None
    return snap


@router.get("/situational/changes", response_model=List[SituationalChange])
def get_situational_changes(
    state: Optional[str] = Query(None),
    entity_ref: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[SituationalChange]:
    """
    Evaluates what changed across sovereign Indian thermal clusters with deterministic significance.
    """
    return jarvis_situational_service.detect_changes(db=db, state=state, entity_ref=entity_ref)


@router.get("/situational/attention", response_model=List[AttentionItem])
def get_situational_attention_queue(
    limit: int = Query(20, ge=1, le=100),
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[AttentionItem]:
    """
    Returns the ranked Analyst Attention Queue ordered by the governed priority score.
    """
    user_role = current_user.role if current_user else "ANALYST"
    items = jarvis_situational_service.build_attention_queue(db=db, limit=limit, state=state)
    if user_role == "PUBLIC":
        for it in items:
            it.coordinates = None
    return items


@router.post("/situational/brief")
def generate_situational_brief(
    req: SituationalBriefRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Generates situational briefs (60-second, India national, regional, industrial, trend, executive, or analyst).
    """
    user_role = current_user.role if current_user else req.user_role
    b_type = req.brief_type.upper()

    if b_type in ("SIXTY_SECOND", "60_SECOND", "60S"):
        res = jarvis_situational_service.generate_60s_brief(db=db)
        return res.model_dump()
    elif b_type == "REGIONAL" and req.state:
        res = jarvis_situational_service.generate_regional_brief(db=db, state_name=req.state)
        return res.model_dump()
    elif b_type == "INDUSTRIAL":
        res = jarvis_situational_service.generate_industrial_brief(db=db, corridor_or_facility=req.corridor or req.state)
        return res.model_dump()
    elif b_type == "TREND":
        return jarvis_situational_service.generate_trend_summary(db=db, time_window=req.time_window or "30d")
    elif b_type == "EXECUTIVE":
        res = jarvis_situational_service.generate_executive_brief(db=db)
        return res.model_dump()
    elif b_type == "ANALYST":
        if user_role == "PUBLIC":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role 'PUBLIC' is not authorized to access analyst-depth briefings."
            )
        res = jarvis_situational_service.generate_analyst_brief(db=db)
        return res.model_dump()
    else:  # INDIA
        res = jarvis_situational_service.generate_india_brief(db=db, state=req.state)
        return res.model_dump()


@router.get("/situational/timeline", response_model=List[TimelineEvent])
def get_situational_timeline(
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[TimelineEvent]:
    """
    Retrieves chronological timeline of events, escalations, assessment revisions, and verifications.
    """
    return jarvis_situational_service.get_situational_timeline(db=db, limit=limit)


@router.post("/situational/investigate-top", response_model=JarvisMission)
def investigate_top_attention_item(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> JarvisMission:
    """
    Transition endpoint: Identifies highest-priority item in the attention queue and launches Phase 22 mission mode.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else "ANALYST"

    top_items = jarvis_situational_service.build_attention_queue(db=db, limit=1)
    target_ref = top_items[0].event_code if top_items else "EVT-GJ-2025-001"

    from backend.app.services.jarvis.jarvis_mission_service import jarvis_mission_service
    mission_cmd = f"MISSION: Investigate event {target_ref} and assess industrial risk drivers"
    return jarvis_mission_service.execute_mission(
        db=db,
        request=mission_cmd,
        user_id=user_id,
        user_role=user_role
    )


# =========================================================================
# JARVIS Autonomous Intelligence, World State & Voice Re-Architecture
# =========================================================================

from pydantic import BaseModel
from backend.app.services.autonomous_intelligence_service import autonomous_intelligence_core
from backend.app.services.jarvis.jarvis_world_state import jarvis_world_state
from backend.app.services.jarvis.jarvis_agentic_orchestrator import jarvis_agentic_orchestrator
from backend.app.services.jarvis.jarvis_voice_service import jarvis_voice_service


class VoiceInteractRequest(BaseModel):
    transcript: str
    session_id: Optional[str] = None


class VoiceSettingsRequest(BaseModel):
    is_muted: Optional[bool] = None
    proactive_notifications_enabled: Optional[bool] = None
    min_risk_threshold: Optional[float] = None


class AutonomousTriggerRequest(BaseModel):
    observations: Optional[List[Dict[str, Any]]] = None
    source: Optional[str] = "NASA FIRMS VIIRS"


@router.get("/world-state")
def get_jarvis_world_state(
    state: Optional[str] = Query(None, description="Optional state filter"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns live operational situation summary, active incidents, changed events,
    and attention queues across sovereign India.
    """
    return jarvis_world_state.get_world_state_summary(db=db, state_filter=state)


@router.post("/autonomous/trigger")
def trigger_autonomous_pipeline(
    req: AutonomousTriggerRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Triggers Path A autonomous intelligence pipeline across observations.
    Executes detection, clustering, context fusion, classification, risk, priority,
    evidence assembly, and notifies JARVIS orchestrator without analyst intervention.
    """
    user_role = current_user.role if current_user else "ANALYST"
    if user_role == "PUBLIC":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role 'PUBLIC' is not authorized to trigger autonomous pipeline runs."
        )

    observations = req.observations
    if not observations:
        # Default sample observation in Gujarat industrial corridor
        observations = [
            {
                "latitude": 22.4707,
                "longitude": 70.0577,
                "brightness": 355.0,
                "frp": 125.4,
                "confidence": 92.0,
                "sensor": "VIIRS",
                "satellite": "NOAA-20",
                "acq_timestamp": datetime.now(timezone.utc).isoformat(),
                "day_night": "N"
            },
            {
                "latitude": 22.4720,
                "longitude": 70.0590,
                "brightness": 348.0,
                "frp": 85.2,
                "confidence": 88.0,
                "sensor": "VIIRS",
                "satellite": "NOAA-20",
                "acq_timestamp": datetime.now(timezone.utc).isoformat(),
                "day_night": "N"
            }
        ]

    outcomes = autonomous_intelligence_core.process_observations_autonomous(
        db=db,
        raw_observations=observations,
        source_name=req.source or "NASA FIRMS VIIRS"
    )

    return {
        "status": "SUCCESS",
        "events_processed": len(outcomes),
        "outcomes": [o.model_dump() for o in outcomes]
    }


@router.get("/autonomous/lifecycle/{event_code}")
def get_event_lifecycle_history(
    event_code: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves the chronological, audited 12-state lifecycle transition history for an event.
    """
    transitions = autonomous_intelligence_core.get_lifecycle_history(event_code)
    return {
        "event_code": event_code,
        "total_transitions": len(transitions),
        "transitions": [t.model_dump() for t in transitions]
    }


@router.post("/voice/interact")
def process_voice_interaction(
    req: VoiceInteractRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Unified voice and conversational console endpoint.
    Processes transcribed speech, queries world state or initiates governed investigation,
    and returns grounded structured reasoning with spoken response text.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else "ANALYST"

    return jarvis_voice_service.process_voice_transcript(
        db=db,
        transcript=req.transcript,
        user_role=user_role,
        user_id=user_id
    )


@router.get("/voice/proactive")
def get_proactive_voice_notifications(
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Retrieves queued proactive spoken notifications that exceed the significance threshold.
    """
    user_role = current_user.role if current_user else "ANALYST"
    notifications = jarvis_voice_service.get_proactive_notifications(user_role=user_role)
    return {
        "notifications": notifications,
        "count": len(notifications)
    }


@router.post("/voice/settings")
def update_voice_settings(
    req: VoiceSettingsRequest,
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Updates voice preferences (mute, proactive threshold, auto-speak).
    """
    return jarvis_voice_service.update_settings(req.model_dump(exclude_unset=True))


@router.get("/voice/settings")
def get_voice_settings(
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    return jarvis_voice_service.get_settings()


@router.get("/mission/orchestrated")
def get_orchestrated_mission(
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Optional[Dict[str, Any]]:
    """
    Returns the latest governed multi-capability investigation executed by the JARVIS Agentic Orchestrator.
    """
    return jarvis_agentic_orchestrator.get_active_mission()
