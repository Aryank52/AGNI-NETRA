"""
AGNI-NETRA — JARVIS Voice & Conversational Intelligence Service
Processes transcribed speech, resolves operational intents, generates grounded spoken responses,
and manages governed proactive voice notifications.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.domain import ThermalEvent
from backend.app.services.jarvis.jarvis_world_state import jarvis_world_state
from backend.app.services.jarvis.jarvis_agentic_orchestrator import jarvis_agentic_orchestrator

logger = logging.getLogger("agni_netra.jarvis_voice")


class JarvisVoiceService:
    """
    JARVIS Voice Interaction & Operational Dialogue Engine.
    Connects speech-to-text input to real-time world state and agentic orchestration.
    """

    def __init__(self):
        self._voice_enabled: bool = True
        self._is_muted: bool = False
        self._proactive_notifications_enabled: bool = True
        self._min_risk_threshold: float = 70.0

    def process_voice_transcript(
        self,
        db: Session,
        transcript: str,
        user_role: str = "ANALYST",
        user_id: str = "ANALYST"
    ) -> Dict[str, Any]:
        """
        Main voice interaction pipeline:
        VOICE INPUT -> Intent & Entity Understanding -> JARVIS Reasoning -> Spoken Response Generation
        """
        cleaned = transcript.strip()
        cmd_lower = cleaned.lower()

        # Security & Sovereign Geographic Validation (WP4 / WP6)
        from backend.app.services.jarvis.jarvis_reasoning_engine import jarvis_reasoning_engine
        is_safe, sanitized, reject_err = jarvis_reasoning_engine.validate_and_sanitize_query(cleaned)
        if not is_safe:
            spoken_err = f"Request cannot be processed. {reject_err}"
            return {
                "transcript": cleaned,
                "intent": "SECURITY_REJECTION",
                "response_text": reject_err,
                "spoken_response": spoken_err,
                "visual_state": "COMPLETED",
                "error": reject_err
            }

        # Handle 'Investigate ...' intents
        if any(w in cmd_lower for w in ["investigate", "analyze", "deep dive", "examine"]):
            # Extract state or event reference
            event_ref = None
            evt_match = re.search(r"\b(evt-[\w-]+)\b", cmd_lower)
            if evt_match:
                event_ref = evt_match.group(1).upper()
            elif "gujarat" in cmd_lower:
                ev = db.query(ThermalEvent).filter(ThermalEvent.state.ilike("%gujarat%")).order_by(desc(ThermalEvent.last_seen)).first()
                if ev:
                    event_ref = ev.event_code
            elif any(w in cmd_lower for w in ["highest priority", "top", "critical"]):
                ev = db.query(ThermalEvent).order_by(desc(ThermalEvent.last_seen)).first()
                if ev:
                    event_ref = ev.event_code

            if not event_ref:
                # Default to the most active event
                ev = db.query(ThermalEvent).order_by(desc(ThermalEvent.last_seen)).first()
                event_ref = ev.event_code if ev else "EVT-GJ-2025-001"

            # Execute manual investigation via Agentic Orchestrator (Path B)
            inv_res = jarvis_agentic_orchestrator.orchestrate_manual_investigation(
                db=db,
                event_ref=event_ref,
                user_id=user_id,
                user_role=user_role
            )

            return {
                "transcript": cleaned,
                "intent": "INVESTIGATE_EVENT",
                "target_event": event_ref,
                "response_text": inv_res.get("spoken_response", f"Investigation started for {event_ref}."),
                "spoken_response": inv_res.get("spoken_response", f"Investigation completed for {event_ref}."),
                "investigation": inv_res,
                "visual_state": "COMPLETED",
                "epistemic_breakdown": inv_res.get("epistemic_synthesis")
            }

        # Otherwise dispatch to World State Q&A
        res = jarvis_world_state.answer_operational_question(db, cleaned)
        return {
            "transcript": cleaned,
            "intent": res["intent"],
            "response_text": res["answer"],
            "spoken_response": res["spoken_response"],
            "relevant_events": res.get("relevant_events", []),
            "visual_state": "COMPLETED"
        }

    def get_proactive_notifications(self, user_role: str = "ANALYST") -> List[Dict[str, Any]]:
        """Retrieves governed proactive voice alerts if enabled and role authorized."""
        if not self._proactive_notifications_enabled or self._is_muted:
            return []

        alerts = jarvis_world_state.pop_pending_voice_alerts()
        # RBAC: filter sensitive information for PUBLIC users
        if user_role == "PUBLIC":
            for a in alerts:
                a["text"] = "A thermal observation update is available in the public catalog."
        return alerts

    def update_settings(self, settings_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Configures voice operating parameters."""
        if "is_muted" in settings_dict:
            self._is_muted = bool(settings_dict["is_muted"])
        if "proactive_notifications_enabled" in settings_dict:
            self._proactive_notifications_enabled = bool(settings_dict["proactive_notifications_enabled"])
        if "min_risk_threshold" in settings_dict:
            self._min_risk_threshold = float(settings_dict["min_risk_threshold"])

        return {
            "is_muted": self._is_muted,
            "proactive_notifications_enabled": self._proactive_notifications_enabled,
            "min_risk_threshold": self._min_risk_threshold
        }

    def get_settings(self) -> Dict[str, Any]:
        return {
            "is_muted": self._is_muted,
            "proactive_notifications_enabled": self._proactive_notifications_enabled,
            "min_risk_threshold": self._min_risk_threshold
        }


# Singleton Voice Service
jarvis_voice_service = JarvisVoiceService()
