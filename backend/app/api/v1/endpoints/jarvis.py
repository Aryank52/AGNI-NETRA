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
    InvestigationWorkspaceSchema
)
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

