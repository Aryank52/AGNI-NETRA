"""
AGNI-NETRA — JARVIS Session Memory
Provides scoped, session-aware context memory allowing natural pronoun resolution
and conversational continuity across multi-step operational commands.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from backend.app.models.jarvis_schemas import SessionContext


class JarvisSessionMemory:
    """
    In-memory session context manager for conversational command continuity.
    Scoped by session_id, ensuring no unrestricted cross-user state leakage.
    """

    def __init__(self, session_ttl_minutes: int = 120):
        self._sessions: Dict[str, SessionContext] = {}
        self.session_ttl = timedelta(minutes=session_ttl_minutes)

    def get_or_create_session(self, session_id: Optional[str] = None) -> SessionContext:
        """
        Retrieves active session or initializes a new scoped session.
        """
        now = datetime.now(timezone.utc)
        if not session_id or session_id not in self._sessions:
            new_id = session_id or f"sess-{uuid.uuid4().hex[:8]}"
            session = SessionContext(
                session_id=new_id,
                created_at=now,
                updated_at=now
            )
            self._sessions[new_id] = session
            return session

        session = self._sessions[session_id]
        # Check TTL expiration
        if now - session.updated_at > self.session_ttl:
            # Expired session; reset context
            session.current_event_ref = None
            session.current_region = None
            session.command_history = []
        session.updated_at = now
        return session

    def update_session(
        self,
        session_id: str,
        command: str,
        intent: Optional[str] = None,
        event_ref: Optional[str] = None,
        region: Optional[str] = None,
        candidate_set: Optional[List[Dict[str, Any]]] = None,
        selected_candidate_ref: Optional[str] = None,
        comparison_set: Optional[List[str]] = None,
        last_winner_reason: Optional[str] = None,
        active_investigation_id: Optional[str] = None
    ) -> SessionContext:
        """
        Updates session context with latest entity, comparison set, and command history.
        """
        session = self.get_or_create_session(session_id)
        if event_ref:
            session.current_event_ref = event_ref
        if region:
            session.current_region = region
        if intent:
            session.last_intent = intent
        if candidate_set is not None:
            session.candidate_set = candidate_set
        if selected_candidate_ref:
            session.selected_candidate_ref = selected_candidate_ref
            session.current_event_ref = selected_candidate_ref
        if comparison_set is not None:
            session.comparison_set = comparison_set
        if last_winner_reason:
            session.last_winner_reason = last_winner_reason
        if active_investigation_id:
            session.active_investigation_id = active_investigation_id

        session.command_history.append(command)
        if len(session.command_history) > 20:
            session.command_history.pop(0)

        session.updated_at = datetime.now(timezone.utc)
        return session

    def get_context_dict(self, session_id: Optional[str]) -> Dict[str, Any]:
        """
        Returns flat context dictionary suitable for entity resolution in the Command Interpreter.
        """
        if not session_id or session_id not in self._sessions:
            return {}
        session = self._sessions[session_id]
        candidate_codes = []
        for c in (session.candidate_set or []):
            if isinstance(c, dict) and c.get("event_code"):
                candidate_codes.append(c["event_code"])
            elif isinstance(c, str):
                candidate_codes.append(c)

        return {
            "current_event_ref": session.current_event_ref,
            "current_region": session.current_region,
            "active_investigation_id": session.active_investigation_id,
            "last_intent": session.last_intent,
            "selected_candidate_ref": session.selected_candidate_ref,
            "comparison_set": session.comparison_set or [],
            "candidate_set_codes": candidate_codes,
            "candidate_set": candidate_codes,
            "last_winner_reason": session.last_winner_reason,
            "history_count": len(session.command_history)
        }


session_memory = JarvisSessionMemory()
