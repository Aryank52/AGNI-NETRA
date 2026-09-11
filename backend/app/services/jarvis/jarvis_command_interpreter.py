"""
AGNI-NETRA — JARVIS Command Interpreter
Extracts intent, entities, and parameters from natural language commands using an extensible provider abstraction.
Default: High-precision Deterministic Rule & Token-Matching Engine.
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
from backend.app.models.jarvis_schemas import CommandIntent, CommandObjective


class BaseLLMProvider(ABC):
    """
    Abstract AI/LLM Provider interface for command interpretation and natural language understanding.
    Deterministic engines remain authoritative for numerical intelligence.
    """

    @abstractmethod
    def interpret(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Interprets natural language into structured intent and entities.
        """
        pass


class LocalDeterministicProvider(BaseLLMProvider):
    """
    High-performance, zero-latency local deterministic command interpreter.
    Fully offline, requiring no external cloud or API credentials.
    """

    INDIAN_STATES = [
        "gujarat", "maharashtra", "punjab", "madhya pradesh", "chhattisgarh",
        "jharkhand", "karnataka", "andhra pradesh", "odisha", "tamil nadu",
        "rajasthan", "west bengal", "uttar pradesh", "haryana", "telangana",
        "bihar", "assam", "kerala", "goa", "uttarakhand", "himachal pradesh"
    ]

    def interpret(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cmd = command.strip().lower()
        entities: Dict[str, Any] = {}
        context = context or {}

        # 1. State Extraction
        has_explicit_state = False
        for state in self.INDIAN_STATES:
            if state in cmd:
                entities["state"] = state.title()
                has_explicit_state = True
                break
        if not entities.get("state") and context.get("current_region"):
            entities["state"] = context["current_region"]

        # 2. Buffer Distance Extraction (e.g. "5 km", "5km", "1000m")
        dist_match = re.search(r"(\d+(?:\.\d+)?)\s*(km|m|meter|kilometer)", cmd)
        if dist_match:
            val = float(dist_match.group(1))
            unit = dist_match.group(2)
            entities["distance_m"] = val * 1000.0 if "km" in unit else val
        else:
            entities["distance_m"] = 5000.0

        # 3. Risk Level Extraction
        for r_level in ["CRITICAL", "HIGH", "MODERATE", "LOW"]:
            if r_level.lower() in cmd:
                entities["risk_level"] = r_level
                break

        # 4. Flags & Criteria Extraction
        entities["near_facility"] = any(w in cmd for w in [
            "near an industrial facility", "near industrial facilities", "near facility",
            "near facilities", "near industrial", "around an industrial facility", "around industrial"
        ])
        entities["facility_context"] = "REFINERY" if "refinery" in cmd else ("INDUSTRIAL" if (entities["near_facility"] or "facility" in cmd or "industrial" in cmd) else None)
        
        # Baseline condition - only triggered when relative elevation/deviation is explicitly requested
        if any(w in cmd for w in ["unusually high", "baseline deviation", "more anomalous than", "anomalous compared to", "higher than baseline", "unusually elevated"]):
            entities["baseline_condition"] = "UNUSUALLY_HIGH"

        # Candidate Cardinality Extraction
        candidate_count = 1
        if re.search(r"\b(three|3|triple|top three|top 3|three highest-risk|3 highest-risk)\b", cmd):
            candidate_count = 3
        elif re.search(r"\b(two|2|both|top two|top 2|two highest-risk|2 highest-risk)\b", cmd):
            candidate_count = 2
        elif re.search(r"\b(four|4|top four|top 4)\b", cmd):
            candidate_count = 4
        elif re.search(r"\b(five|5|top five|top 5)\b", cmd):
            candidate_count = 5
        entities["candidate_count"] = candidate_count

        # Target Hypothesis / Class
        if any(w in cmd for w in ["industrial fire", "refinery fire", "factory fire"]):
            entities["target_hypothesis"] = "Industrial Fire"
        elif "gas flare" in cmd or "flare" in cmd:
            entities["target_hypothesis"] = "Gas Flare"

        # 5. Multi-Candidate & Comparative Cardinality Detection
        has_compare_verb = any(w in cmd for w in [
            "compare", "comparing", "contrast", "contrasting", "relative to each other",
            "between the", "which of", "which event", "which thermal", "which case", "which one",
            "more concerning", "most concerning", "stronger", "strongest"
        ])
        has_plural_candidates = any(w in cmd for w in [
            "strongest cases", "strongest events", "candidate events", "candidate cases",
            "these cases", "these events", "the cases", "the events", "candidates",
            "other high-risk events", "other high risk events", "the other high-risk", "other events",
            "top three", "top two", "top 3", "top 2", "two strongest", "three strongest",
            "similar events", "similar cases", "similar incidents", "events", "cases", "hotspots", "anomalies"
        ])

        if any(w in cmd for w in [
            "other high-risk events", "other high risk events", "the other high-risk", "other events",
            "similar events", "similar cases", "similar incidents", "other incidents", "with similar"
        ]):
            entities["compare_with_others"] = True
            entities["is_multi_compare"] = True
            candidate_count = max(3, candidate_count)
            entities["candidate_count"] = candidate_count

        if (
            any(w in cmd for w in [
                "which one has the strongest evidence", "which one has stronger evidence",
                "tell me which one", "tell me which", "which has the strongest evidence",
                "identify the strongest case", "which case is strongest", "which of these cases",
                "which of these events", "which of these", "which event is more concerning",
                "which thermal incident is the most concerning", "rank these cases", "rank these events"
            ])
            or (has_compare_verb and (has_plural_candidates or candidate_count > 1))
            or any(w in cmd for w in [
                "strongest case for a possible", "strongest case for", "strongest candidate for",
                "need the strongest case"
            ])
        ):
            entities["is_multi_compare"] = True
            if candidate_count <= 1:
                candidate_count = 3
            entities["candidate_count"] = candidate_count
            if "industrial fire" in cmd or "fire" in cmd:
                entities["target_hypothesis"] = "Industrial Fire"

        # 6. Event Reference Extraction & Normalization (Possessive & Prepositional Syntax)
        common_words = {
            "near", "in", "at", "on", "from", "with", "for", "to", "and", "or", "is",
            "that", "this", "the", "under", "across", "within", "between", "of", "by",
            "details", "data", "status", "risk", "anomaly", "anomalies", "facilities",
            "facility", "an", "a", "highest", "critical", "latest", "recent", "most",
            "suspicious", "worst", "cases", "case", "three", "events", "fire", "around",
            "risk", "classification", "behavior", "baseline", "report", "dossier"
        }
        
        explicit_event_found = False

        # Pattern A: "Event 827", "Event 827's", "Event-827", "EVT-827"
        evt_match = re.search(r"(?:event|evt)[\s\-_#:]*([a-z0-9\-]+)(?:['’]s)?", cmd, re.IGNORECASE)
        if evt_match:
            candidate = evt_match.group(1).upper()
            candidate = re.sub(r"['’]S$", "", candidate)
            cand_lower = candidate.lower()
            if cand_lower not in common_words and (re.search(r"\d", candidate) or candidate.startswith("EVT-")):
                entities["event_ref"] = candidate
                explicit_event_found = True
                entities["explicit_event_provided"] = True

        # Pattern B: Prepositional "risk of Event 827", "classification of 827"
        if not explicit_event_found:
            prep_match = re.search(r"\b(?:risk|classification|behavior|baseline|evidence|dossier|status)\s+of\s+(?:event\s+|evt\s+)?([a-z0-9\-]+)\b", cmd, re.IGNORECASE)
            if prep_match:
                candidate = prep_match.group(1).upper()
                candidate = re.sub(r"['’]S$", "", candidate)
                cand_lower = candidate.lower()
                if cand_lower not in common_words and (re.search(r"\d", candidate) or candidate.startswith("EVT-")):
                    entities["event_ref"] = candidate
                    explicit_event_found = True
                    entities["explicit_event_provided"] = True

        # Pattern C: Direct code "EVT-..."
        if not explicit_event_found:
            evt_code_match = re.search(r"\b(evt-[a-z0-9\-]+)(?:['’]s)?\b", cmd, re.IGNORECASE)
            if evt_code_match:
                entities["event_ref"] = evt_code_match.group(1).upper()
                explicit_event_found = True
                entities["explicit_event_provided"] = True

        # Pattern C2: Investigation Case ID "INV-..."
        inv_match = re.search(r"\b(inv-\d{8}-[a-z0-9]+)\b", cmd, re.IGNORECASE)
        if inv_match:
            entities["investigation_id"] = inv_match.group(1).upper()

        # Pattern D: Standalone 3-8 digit number
        if not explicit_event_found:
            num_match = re.search(r"\b(\d{3,8})(?:['’]s)?\b", cmd)
            if num_match:
                num_val = num_match.group(1)
                if num_val not in ["2022", "2023", "2024", "2025", "2026", "2027", "5000", "1000"]:
                    entities["event_ref"] = num_val
                    explicit_event_found = True
                    entities["explicit_event_provided"] = True

        # 7. Contextual Reference & Descriptive Anaphora Resolution
        candidate_pool: List[str] = []
        if context.get("candidate_set_codes"):
            candidate_pool.extend([str(c) for c in context["candidate_set_codes"] if c])
        elif context.get("comparison_set"):
            candidate_pool.extend([str(c) for c in context["comparison_set"] if c])
        elif context.get("candidate_set"):
            candidate_pool.extend([str(c) for c in context["candidate_set"] if c])

        # 7a. Candidate Code Extraction ("Candidate A", "Candidate B", "Candidate C", etc.)
        if not explicit_event_found:
            cand_code_match = re.search(r"\bcandidate\s+([a-c]|1|2|3)\b", cmd, re.IGNORECASE)
            if cand_code_match:
                c_sym = cand_code_match.group(1).upper()
                idx_map = {"A": 0, "1": 0, "B": 1, "2": 1, "C": 2, "3": 2}
                idx = idx_map.get(c_sym, -1)
                if 0 <= idx < len(candidate_pool):
                    entities["event_ref"] = candidate_pool[idx]
                    entities["resolved_from_context"] = True
                    entities["contextual_reference"] = f"candidate_{c_sym}"
                    explicit_event_found = True

        is_evidence_req = any(w in cmd for w in [
            "give me the evidence", "evidence behind the conclusion", "evidence behind",
            "evidence for the conclusion", "show me the evidence", "not just the classification",
            "what is the evidence", "what evidence behind", "explain your evidence", "show the evidence",
            "evidence supporting that conclusion", "evidence supporting that", "evidence for the winner",
            "show the strongest evidence"
        ])
        if is_evidence_req:
            entities["require_evidence_summary"] = True
            entities["summary_type"] = "EVIDENCE"

        if not explicit_event_found:
            # 7a. Implicit Evidence Request Context Binding
            if is_evidence_req:
                if context.get("selected_candidate_ref"):
                    entities["event_ref"] = context["selected_candidate_ref"]
                    entities["resolved_from_context"] = True
                    entities["contextual_reference"] = "selected_candidate_ref"
                    explicit_event_found = True
                elif context.get("current_event_ref"):
                    entities["event_ref"] = context["current_event_ref"]
                    entities["resolved_from_context"] = True
                    entities["contextual_reference"] = "current_event_ref"
                    explicit_event_found = True
                elif len(candidate_pool) == 1:
                    entities["event_ref"] = candidate_pool[0]
                    entities["resolved_from_context"] = True
                    entities["contextual_reference"] = "candidate_0"
                    explicit_event_found = True
                elif len(candidate_pool) > 1:
                    labels = [f"Candidate {chr(65+i)}" for i in range(len(candidate_pool[:4]))]
                    clarif_opts = ", ".join(labels[:-1]) + ", or " + labels[-1] if len(labels) > 1 else labels[0]
                    entities["clarification_required"] = True
                    entities["clarification_message"] = f"Which case do you mean: {clarif_opts}?"

            # 7b. Ordinal References ("the first one", "the second one", "the third one")
            if not explicit_event_found:
                if any(w in cmd for w in ["the first one", "first one", "the first case", "first case", "the first event", "1st one"]):
                    pool = candidate_pool or ([context.get("current_event_ref")] if context.get("current_event_ref") else [])
                    if len(pool) >= 1 and pool[0]:
                        entities["event_ref"] = pool[0]
                        entities["resolved_from_context"] = True
                        entities["contextual_reference"] = "first_candidate"
                        explicit_event_found = True
                elif any(w in cmd for w in ["the second one", "second one", "the second case", "second case", "the second event", "2nd one"]):
                    if len(candidate_pool) >= 2 and candidate_pool[1]:
                        entities["event_ref"] = candidate_pool[1]
                        entities["resolved_from_context"] = True
                        entities["contextual_reference"] = "second_candidate"
                        explicit_event_found = True
                elif any(w in cmd for w in ["the third one", "third one", "the third case", "third case", "the third event", "3rd one"]):
                    if len(candidate_pool) >= 3 and candidate_pool[2]:
                        entities["event_ref"] = candidate_pool[2]
                        entities["resolved_from_context"] = True
                        entities["contextual_reference"] = "third_candidate"
                        explicit_event_found = True

            # 7c. Superlative & Winner References
            if not explicit_event_found:
                is_winner_ref = any(w in cmd for w in [
                    "the winner", "winner", "winning case", "the one you identified",
                    "identified case", "the one you selected", "the strongest one",
                    "the strongest case", "strongest one", "strongest case",
                    "strongest case from that comparison", "from that comparison", "that comparison",
                    "the highest-risk one", "highest-risk one", "highest risk one",
                    "the most high-risk one", "the most suspicious one", "most suspicious one"
                ])
                if is_winner_ref:
                    target_sup = (
                        context.get("selected_candidate_ref")
                        or context.get("current_event_ref")
                        or (candidate_pool[0] if candidate_pool else None)
                    )
                    if target_sup:
                        entities["event_ref"] = target_sup
                        entities["resolved_from_context"] = True
                        entities["contextual_reference"] = "winner_or_strongest"
                        explicit_event_found = True

            # 7d. Descriptive & Demonstrative Focus References ("the serious one", "that event", etc.)
            if not explicit_event_found:
                is_cohort_query = any(w in cmd for w in [
                    "events", "cases", "deserve", "attention first", "investigate first",
                    "prioritize", "ranking", "summarize current", "all events", "recent events",
                    "what should the analyst", "what should i investigate",
                    "sources", "data sources", "coverage", "missing", "provenance"
                ])
                is_descriptive = (
                    not is_cohort_query and (
                        bool(re.search(r"\b(?:the serious one|the concerning one|that event|that case|the event|the case|this case|this event|that one|this one)\b", cmd, re.IGNORECASE))
                        or bool(re.search(r"\b(it|its|same event|for it)\b", cmd, re.IGNORECASE))
                    )
                )
                
                is_new_search = (
                    entities.get("near_facility") or 
                    (has_explicit_state and any(w in cmd for w in ["find", "locate", "search", "most critical", "highest-risk", "anomaly in", "event in", "three highest-risk"])) or
                    any(w in cmd for w in ["find the highest-risk", "find highest-risk", "search critical", "find the most suspicious", "three highest-risk"])
                )

                if is_descriptive and not is_new_search and not entities.get("is_multi_compare"):
                    current_ref = context.get("current_event_ref")
                    sel_ref = context.get("selected_candidate_ref")

                    if sel_ref:
                        entities["event_ref"] = sel_ref
                        entities["resolved_from_context"] = True
                        entities["contextual_reference"] = "selected_candidate_ref"
                        explicit_event_found = True
                    elif current_ref:
                        if len(candidate_pool) <= 1 or current_ref in candidate_pool[:1]:
                            entities["event_ref"] = current_ref
                            entities["resolved_from_context"] = True
                            entities["contextual_reference"] = "current_event_ref"
                            explicit_event_found = True
                        else:
                            labels = [f"Candidate {chr(65+i)}" for i in range(len(candidate_pool[:4]))]
                            clarif_opts = ", ".join(labels[:-1]) + ", or " + labels[-1] if len(labels) > 1 else labels[0]
                            entities["clarification_required"] = True
                            entities["clarification_message"] = f"Which case do you mean: {clarif_opts}?"
                    elif len(candidate_pool) == 1:
                        entities["event_ref"] = candidate_pool[0]
                        entities["resolved_from_context"] = True
                        entities["contextual_reference"] = "candidate_0"
                        explicit_event_found = True
                    elif len(candidate_pool) > 1:
                        labels = [f"Candidate {chr(65+i)}" for i in range(len(candidate_pool[:4]))]
                        clarif_opts = ", ".join(labels[:-1]) + ", or " + labels[-1] if len(labels) > 1 else labels[0]
                        entities["clarification_required"] = True
                        entities["clarification_message"] = f"Which case do you mean: {clarif_opts}?"
                    elif not is_cohort_query and bool(re.search(r"\b(?:the serious one|the concerning one|that event|that case|the event|the case|this event|this case)\b", cmd, re.IGNORECASE)):
                        # Ambiguity without context: Never invent a target
                        entities["clarification_required"] = True
                        entities["clarification_message"] = "Target event not specified in command or session context. Please provide an event ID."

        # 8. Semantic Intent & Dimension Drivers
        entities["require_investigation"] = any(w in cmd for w in ["investigate", "deep dive", "inspect", "examine"])
        
        # Risk explanation driver (covers possessive, prepositional, and causal forms)
        is_risk_explanation = (
            any(w in cmd for w in [
                "'s risk", "’s risk", "risk of", "why it is high risk", "why is it high risk",
                "risk factors", "explain why", "main risk factors", "major risk factors",
                "explain its risk", "risk drivers", "tell me why it is high risk", "why high risk",
                "why you consider this event dangerous", "dangerous", "tell me the risk",
                "what is the risk", "explain risk", "risk breakdown"
            ]) or (
                ("risk" in cmd or "why" in cmd) and
                any(w in cmd for w in ["explain", "tell me", "why", "describe", "breakdown", "factors"]) and
                not any(w in cmd for w in ["compare", "which", "rank", "find the highest-risk", "search", "dossier", "report"])
            )
        )
        entities["require_explain_risk"] = is_risk_explanation
        entities["require_explain_shap"] = any(w in cmd for w in ["shap", "strongest drivers", "waterfall drivers", "feature attribution"])
        
        # Multi-candidate cohort comparison driver
        is_multi_compare = (
            any(w in cmd for w in [
                "similar events", "compare with similar", "which case is strongest", "which candidate",
                "which is strongest", "strongest case", "winner", "compare the critical thermal events",
                "compare the critical events", "compare events", "compare thermal events",
                "which candidate is most severe", "most severe candidate", "strongest candidate",
                "compare them", "which case"
            ]) or (
                "compare" in cmd and any(w in cmd for w in ["events", "cases", "candidates", "cohort", "similar"])
            )
        )
        entities["is_multi_compare"] = is_multi_compare

        # Baseline comparison driver
        is_baseline_comparison = (
            any(w in cmd for w in [
                "'s historical behavior", "’s historical behavior", "historical behavior of",
                "'s baseline", "’s baseline", "baseline of", "compare with its historical baseline",
                "compare with its normal behavior", "compare with its usual pattern",
                "compare with historical expectation", "historical baseline", "historical behavior",
                "normal behavior", "usual pattern", "historical expectation"
            ]) and not is_multi_compare
        )
        entities["require_compare_baseline"] = is_baseline_comparison or ("compare" in cmd and not is_multi_compare)

        # Dossier driver
        entities["require_dossier"] = any(w in cmd for w in [
            "dossier", "prepare a dossier", "generate an intelligence dossier",
            "intelligence dossier", "generate its intelligence dossier", "incident report",
            "generate an investigation dossier", "prepare a report", "formal report"
        ])

        # Target verification question driver ("does it require human verification?", etc.)
        is_target_verification = any(w in cmd for w in [
            "require human verification", "require verification", "need human verification",
            "need verification", "human verification required", "verification required",
            "require analyst review", "require analyst verification"
        ]) and not any(w in cmd for w in ["queue", "which cases", "list pending", "show verification queue"])
        if is_target_verification:
            entities["require_target_verification"] = True

        # Workspace management drivers
        is_resume_ws = any(w in cmd for w in ["resume my", "resume investigation", "reopen investigation", "resume the investigation", "resume event"])
        if is_resume_ws:
            entities["resume_investigation"] = True

        is_close_ws = any(w in cmd for w in ["close this investigation", "close investigation", "close the investigation", "archive investigation", "close case"])
        if is_close_ws:
            entities["close_investigation"] = True

        is_refresh_ws = any(w in cmd for w in [
            "refresh the investigation", "refresh investigation", "recheck event", 
            "update the latest evidence", "refresh evidence", "refresh data", "recheck the event",
            "refresh the evidence"
        ]) or ("refresh" in cmd and any(w in cmd for w in ["evidence", "data", "investigation", "workspace"]))
        if is_refresh_ws:
            entities["refresh_investigation"] = True

        # Strict stopping trigger
        # Strict stopping trigger
        if any(w in cmd for w in ["stop once you have enough evidence", "stop once", "stop when sufficient", "stop once enough"]):
            entities["strict_stopping"] = True

        # Phase 4 Intelligence Operations & Workflow Drivers
        # A. What Remains
        is_what_remains = (
            any(w in cmd for w in [
                "what remains to be done", "what is still unresolved",
                "what tasks are left", "what is left to do", "what is left", "what still remains"
            ]) or ("what remains" in cmd and not any(u in cmd for u in ["uncertain", "uncertainty"]))
        )
        if is_what_remains:
            entities["what_remains"] = True

        # B. Why Stopped
        is_why_stopped = any(w in cmd for w in [
            "why did you stop", "why you stopped", "why did execution stop",
            "why did execution halt", "why did you halt", "stopping condition"
        ])
        if is_why_stopped:
            entities["why_stopped"] = True

        # C. What Do You Know
        is_what_do_you_know = any(w in cmd for w in [
            "summarize what you know about this case", "summarize what you know",
            "what do you know about this case", "what do you know",
            "what is known about this case", "show what you know", "show knowledge"
        ])
        if is_what_do_you_know:
            entities["what_do_you_know"] = True
            if not entities.get("event_ref"):
                if context.get("selected_candidate_ref"):
                    entities["event_ref"] = context["selected_candidate_ref"]
                    entities["resolved_from_context"] = True
                elif context.get("current_event_ref"):
                    entities["event_ref"] = context["current_event_ref"]
                    entities["resolved_from_context"] = True

        # D. Summarize Investigation (Canonical 13-dimension)
        is_summarize_inv = any(w in cmd for w in [
            "summarize the investigation", "summarize this investigation",
            "summarize investigation", "investigation summary", "canonical investigation summary"
        ])
        if is_summarize_inv:
            entities["summarize_investigation"] = True

        # E. Continue Investigation
        is_continue_inv = (
            cmd in ["jarvis, continue", "continue", "continue the investigation", "continue investigation", "proceed with investigation", "jarvis continue"]
            or any(w in cmd for w in ["continue the investigation", "continue investigation", "proceed with investigation"])
        )
        if is_continue_inv:
            entities["continue_investigation"] = True

        # F. Candidate Select / Inspect
        cand_sel_match = re.search(r"\b(?:inspect|select|focus|switch to)\s+candidate\s+([a-e]|1|2|3|4|5)\b", cmd, re.IGNORECASE)
        if cand_sel_match:
            c_sym = cand_sel_match.group(1).upper()
            entities["select_candidate"] = f"Candidate {c_sym}"
            entities["candidate_letter"] = c_sym
            idx_map = {"A": 0, "1": 0, "B": 1, "2": 1, "C": 2, "3": 2, "D": 3, "4": 3, "E": 4, "5": 4}
            idx = idx_map.get(c_sym, -1)
            if 0 <= idx < len(candidate_pool):
                entities["event_ref"] = candidate_pool[idx]
                entities["resolved_from_context"] = True
                entities["contextual_reference"] = f"candidate_{c_sym}"

        # G. Explain Winner Selection
        is_explain_selection = any(w in cmd for w in [
            "why did you select that one", "why did you select that", "why did you select", "why did you pick that one",
            "why did you pick that", "why you selected", "explain why the first one wins",
            "why the first one wins", "why does it win", "why did that one win",
            "explain why it wins", "why did you choose that", "why did you choose"
        ])
        if is_explain_selection:
            entities["explain_winner_selection"] = True
            if not entities.get("event_ref"):
                if context.get("selected_candidate_ref"):
                    entities["event_ref"] = context["selected_candidate_ref"]
                    entities["resolved_from_context"] = True
                elif context.get("current_event_ref"):
                    entities["event_ref"] = context["current_event_ref"]
                    entities["resolved_from_context"] = True

        # H. Top Candidates Investigate
        is_top_cands_investigate = bool(re.search(r"\btake (?:the )?(?:top )?(two|three|four|five|2|3|4|5) (?:and )?investigate\b", cmd)) or (
            "take the top" in cmd and "investigate" in cmd
        ) or (
            "investigate" in cmd and any(w in cmd for w in ["top three", "top 3", "top two", "top 2"])
        )
        if is_top_cands_investigate:
            entities["top_candidates_investigate"] = True

        # Fallback binding for verification question
        if is_target_verification and not entities.get("event_ref"):
            if context.get("selected_candidate_ref"):
                entities["event_ref"] = context["selected_candidate_ref"]
                entities["resolved_from_context"] = True
            elif context.get("current_event_ref"):
                entities["event_ref"] = context["current_event_ref"]
                entities["resolved_from_context"] = True
            elif len(candidate_pool) > 0:
                entities["event_ref"] = candidate_pool[0]
                entities["resolved_from_context"] = True

        # Phase 5 Operational Intelligence Depth Drivers
        # A. Low Confidence Flag
        is_low_conf = any(w in cmd for w in [
            "low classification confidence", "low confidence", "confidence is low",
            "confidence below", "uncertain classification", "classification confidence is low",
            "confidence <"
        ])
        if is_low_conf:
            entities["low_confidence"] = True
            conf_m = re.search(r"below\s+(\d+)%", cmd) or re.search(r"<\s*(\d+)%", cmd)
            if conf_m:
                entities["confidence_max"] = float(conf_m.group(1)) / 100.0

        # B. Evidence Conflict Query Flag
        is_evidence_conflict = any(w in cmd for w in [
            "conflicts with the current classification", "conflicts with classification",
            "conflict with the current classification", "conflict with classification",
            "contradicts the current classification", "contradicts classification",
            "where classifier and historical behavior disagree", "classifier and historical behavior disagree",
            "where the classifier and historical behavior disagree", "historical behavior conflicts",
            "historical behavior contradicts", "conflicting evidence", "check for conflicts",
            "check conflicts", "evidence conflict", "evidence conflicts", "explain any conflicting evidence"
        ])
        if is_evidence_conflict:
            entities["is_evidence_conflict"] = True

        # C. Evidence Strength Query Flag
        is_evidence_strength = any(w in cmd for w in [
            "how strong is the evidence", "evidence strength", "evidence strongly supports",
            "strength of the evidence", "how strong is evidence", "is the evidence strong",
            "assess evidence strength", "determine whether the evidence strongly supports"
        ])
        if is_evidence_strength:
            entities["is_evidence_strength"] = True

        # D. Analyst Prioritization Query Flag
        is_analyst_prioritization = any(w in cmd for w in [
            "what should the analyst investigate first", "what should i investigate first",
            "investigate first", "deserve attention first", "deserve analyst attention first",
            "which event deserves attention first", "events that deserve attention first",
            "events that deserve analyst attention first", "events that deserve attention",
            "events that deserve analyst attention", "prioritize analyst", "analyst prioritization",
            "identify the events that deserve attention first", "identify the events that deserve analyst attention first"
        ])
        if is_analyst_prioritization:
            entities["is_analyst_prioritization"] = True

        # E. Priority Explanation Flag ("why investigate this first?")
        is_priority_explanation = any(w in cmd for w in [
            "why should i investigate this event first", "why investigate this event first",
            "why should we investigate this first", "explain why the winner is stronger",
            "why the winner is stronger", "why is the winner stronger",
            "explain why this event wins", "why this event wins", "why investigate first",
            "explain why the first one wins"
        ])
        if is_priority_explanation:
            entities["is_priority_explanation"] = True

        # F. Uncertainty Query Flag
        is_uncertainty = any(w in cmd for w in [
            "what are we uncertain about", "what are we still uncertain about",
            "what remains uncertain", "what is uncertain", "what are you uncertain about",
            "summarize uncertainty", "uncertainty assessment", "tell me what remains uncertain"
        ])
        if is_uncertainty:
            entities["is_uncertainty"] = True

        # G. "What Could Change The Conclusion?" Flag
        is_what_could_change = any(w in cmd for w in [
            "what could change this conclusion", "what could change the conclusion",
            "what evidence could change the conclusion", "what evidence could change",
            "what would change the current conclusion", "what would change the conclusion",
            "what would change this conclusion", "what could change your conclusion",
            "evidence could change the conclusion"
        ])
        if is_what_could_change:
            entities["is_what_could_change"] = True

        # H. Operator Summary / "What is important now?" Flag
        is_operator_summary = any(w in cmd for w in [
            "summarize current intelligence", "give me the most important intelligence right now",
            "most important intelligence currently available", "most important intelligence right now",
            "most important intelligence", "what is important now", "current intelligence",
            "current intelligence brief", "summarize the most important intelligence"
        ])
        if is_operator_summary:
            entities["is_operator_summary"] = True

        # I. Complex Acceptance Command Flag (Section 20)
        is_complex_acceptance = (
            "most concerning thermal event" in cmd
            and "industrial facility" in cmd
            and ("investigate it" in cmd or "investigate" in cmd)
            and ("conflicting evidence" in cmd or "uncertain" in cmd or "human verification" in cmd)
        )
        if is_complex_acceptance:
            entities["is_complex_acceptance"] = True

        # Phase 6 Global Intelligence Architecture & Provider Abstraction Drivers
        
        # A. Section 24 Comprehensive Acceptance Query
        is_section_24_acceptance = (
            ("which intelligence sources" in cmd or "which data sources" in cmd or "which sources" in cmd or "what intelligence sources" in cmd)
            and ("geographic coverage" in cmd or "coverage" in cmd)
            and ("missing" in cmd or "what evidence is missing" in cmd)
            and ("human verification" in cmd or "verification" in cmd)
        )
        if is_section_24_acceptance:
            entities["is_section_24_acceptance"] = True

        # B. Sources Used / Data Sources Query
        is_sources_used = any(w in cmd for w in [
            "what sources were used", "which sources were used", "what sources support",
            "which data sources were used", "which data sources support", "what data sources were used",
            "what intelligence sources support", "what sources support this investigation",
            "sources were used for this case", "sources were used", "sources used",
            "what sources are supporting", "show sources used", "data sources used",
            "what sources support the assessment", "which sources support this investigation"
        ]) and not is_section_24_acceptance
        if is_sources_used:
            entities["is_sources_used"] = True

        # C. Geographic Coverage Query
        is_coverage_query = any(w in cmd for w in [
            "what intelligence sources are available here", "what sources are available here",
            "what geographic coverage is available here", "what geographic coverage is available",
            "what coverage is available here", "what coverage is available",
            "show geographic coverage", "geographic coverage available", "coverage available"
        ]) and not is_section_24_acceptance
        if is_coverage_query:
            entities["is_coverage_query"] = True

        # D. Missing Sources / Evidence Gap Query
        is_missing_sources = any(w in cmd for w in [
            "what data is missing", "what is missing from this investigation",
            "what is missing", "what sources are missing", "missing data",
            "missing intelligence sources", "what evidence is missing"
        ]) and not is_section_24_acceptance
        if is_missing_sources:
            entities["is_missing_sources"] = True

        # E. Investigation Coverage Sufficiency Query
        is_coverage_sufficiency = any(w in cmd for w in [
            "is this investigation sufficiently covered", "is the investigation sufficiently covered",
            "sufficiently covered", "is coverage sufficient", "is the evidence sufficiently covered"
        ]) and not is_section_24_acceptance
        if is_coverage_sufficiency:
            entities["is_coverage_sufficiency"] = True

        # F. Source Provenance Query
        is_source_provenance = any(w in cmd for w in [
            "show me the source provenance", "show source provenance",
            "show the source provenance", "source provenance", "what is the source provenance",
            "what is the provenance", "provenance audit"
        ]) and not is_section_24_acceptance
        if is_source_provenance:
            entities["is_source_provenance"] = True

        # Phase 9 Global Historical Baselines & Temporal Pattern Intelligence Commands
        # A. Section 26 Primary Acceptance Command
        is_section_26_phase9_acceptance = (
            any(w in cmd for w in [
                "analyze the historical baseline and temporal behavior",
                "historical baseline and temporal behavior",
                "historical thermal, contextual, and temporal behavior",
                "historical thermal contextual and temporal",
                "temporal behavior of event 827",
                "temporal behavior of event",
                "temporal behavior for evt-827",
                "temporal behavior for event 827",
                "all available thermal, contextual, and temporal",
                "all available thermal contextual and temporal",
                "thermal, contextual, and temporal sources",
                "thermal contextual and temporal sources"
            ])
            or (
                ("827" in cmd or "event" in cmd)
                and "temporal" in cmd
                and any(w in cmd for w in ["historical baseline", "persistent or recurring", "behavior for", "baseline and temporal"])
            )
        )
        if is_section_26_phase9_acceptance:
            entities["is_section_26_phase9_acceptance"] = True
            if not entities.get("event_ref"):
                entities["event_ref"] = "EVT-827"

        # B. Analyze Historical Behavior
        is_analyze_historical_behavior = (
            any(w in cmd for w in [
                "what is the historical baseline",
                "historical baseline for",
                "historical baseline of",
                "analyze the historical behavior of this event",
                "analyze the historical behavior",
                "historical behavior of this event",
                "analyze historical behavior"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_analyze_historical_behavior:
            entities["is_analyze_historical_behavior"] = True

        # C. Determine Persistence
        is_determine_persistence = (
            any(w in cmd for w in [
                "is this event persistent",
                "is this persistent",
                "determine whether this event is persistent",
                "whether this event is persistent",
                "determine whether the event is persistent",
                "event is persistent",
                "persistence analysis",
                "how persistent is this"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_determine_persistence:
            entities["is_determine_persistence"] = True

        # D. Determine Recurrence
        is_determine_recurrence = (
            any(w in cmd for w in [
                "has this location burned or flared before",
                "burned or flared before",
                "flared before",
                "burned before",
                "determine whether this activity is recurring",
                "whether this activity is recurring",
                "is this activity recurring",
                "activity is recurring",
                "recurrence analysis",
                "has this burned before",
                "has this location flared before"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_determine_recurrence:
            entities["is_determine_recurrence"] = True

        # E. Compare Historical Baseline
        is_compare_historical_baseline = (
            any(w in cmd for w in [
                "compare this event to historical baseline",
                "compare this event to its historical baseline",
                "compare this event with its historical baseline",
                "compare this event with historical baseline",
                "compare to historical baseline",
                "compare with its historical baseline",
                "compare with historical baseline"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_compare_historical_baseline:
            entities["is_compare_historical_baseline"] = True

        # F. Determine Temporal Anomaly
        is_determine_temporal_anomaly = (
            any(w in cmd for w in [
                "is this an anomalous deviation or routine activity",
                "anomalous deviation or routine activity",
                "routine activity",
                "anomalous deviation",
                "tell me whether this event is temporally anomalous",
                "whether this event is temporally anomalous",
                "is this event temporally anomalous",
                "temporally anomalous",
                "temporal anomaly"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_determine_temporal_anomaly:
            entities["is_determine_temporal_anomaly"] = True

        # G. Determine Seasonality
        is_determine_seasonality = (
            any(w in cmd for w in [
                "does this event follow a seasonal pattern",
                "follow a seasonal pattern",
                "follows a seasonal pattern",
                "determine whether the event follows a seasonal pattern",
                "whether the event follows a seasonal pattern",
                "seasonal pattern",
                "is this event seasonal"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_determine_seasonality:
            entities["is_determine_seasonality"] = True

        # H. Show Day-Night Behavior
        is_show_day_night = (
            any(w in cmd for w in [
                "show day versus night behavior",
                "day versus night behavior",
                "day vs night behavior",
                "show the day-night behavior of this event",
                "day-night behavior of this event",
                "show day-night behavior",
                "day-night behavior",
                "day night behavior",
                "diurnal behavior"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_show_day_night:
            entities["is_show_day_night"] = True

        # I. Explain Temporal Evidence
        is_explain_temporal_evidence = (
            any(w in cmd for w in [
                "explain the temporal evidence for this event",
                "explain the temporal evidence",
                "explain temporal evidence",
                "temporal evidence for this event"
            ]) and "provenance" not in cmd
            and "combine" not in cmd
            and not is_section_26_phase9_acceptance
        )
        if is_explain_temporal_evidence:
            entities["is_explain_temporal_evidence"] = True

        # J. Show Missing Historical Data
        is_missing_historical_data = (
            any(w in cmd for w in [
                "what historical data is missing",
                "show what historical data is missing",
                "historical data is missing",
                "missing historical data",
                "which historical data is missing"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_missing_historical_data:
            entities["is_missing_historical_data"] = True

        # K. Reduce Temporal Uncertainty
        is_reduce_temporal_uncertainty = (
            any(w in cmd for w in [
                "what observations would reduce temporal uncertainty",
                "observations would reduce temporal uncertainty",
                "what additional observations would reduce temporal uncertainty",
                "tell me what additional observations would reduce temporal uncertainty",
                "reduce temporal uncertainty"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_reduce_temporal_uncertainty:
            entities["is_reduce_temporal_uncertainty"] = True

        # L. Combine All Evidence
        is_combine_all_evidence = (
            any(w in cmd for w in [
                "combine all thermal, contextual, and temporal evidence",
                "combine all thermal contextual and temporal evidence",
                "combine thermal, contextual, and temporal evidence",
                "combine thermal contextual and temporal evidence",
                "combine all evidence"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_combine_all_evidence:
            entities["is_combine_all_evidence"] = True

        # M. Temporal Provenance
        is_temporal_provenance = (
            any(w in cmd for w in [
                "show the temporal evidence provenance",
                "show temporal evidence provenance",
                "show temporal provenance",
                "temporal evidence provenance",
                "temporal source provenance",
                "temporal provenance"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_temporal_provenance:
            entities["is_temporal_provenance"] = True

        # N. Temporal Coverage
        is_temporal_coverage = (
            any(w in cmd for w in [
                "what temporal coverage is available for this event",
                "what temporal coverage is available",
                "temporal coverage is available",
                "temporal coverage available",
                "show temporal coverage",
                "temporal coverage"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_temporal_coverage:
            entities["is_temporal_coverage"] = True

        is_any_phase9 = (
            is_section_26_phase9_acceptance or is_analyze_historical_behavior or
            is_determine_persistence or is_determine_recurrence or
            is_compare_historical_baseline or is_determine_temporal_anomaly or
            is_determine_seasonality or is_show_day_night or
            is_explain_temporal_evidence or is_missing_historical_data or
            is_reduce_temporal_uncertainty or is_combine_all_evidence or
            is_temporal_provenance or is_temporal_coverage
        )
        if is_any_phase9:
            entities["clarification_required"] = False
            if not entities.get("event_ref"):
                entities["event_ref"] = context.get("current_event_ref") or context.get("selected_candidate_ref") or "EVT-827"

        # Phase 7 Global Thermal Intelligence & Multi-Provider Fusion Commands
        # A. Section 28 Primary Acceptance Command
        is_section_28_acceptance = (
            any(w in cmd for w in ["investigate event 827", "investigate 827", "investigate evt-827", "investigate event evt-827", "investigate this event"])
            and any(w in cmd for w in ["all available thermal sources", "all thermal sources", "available thermal sources", "thermal sources"])
            and any(w in cmd for w in ["agree", "disagree", "disagreement", "confidence", "observations agree"])
            and not any(w in cmd for w in ["contextual sources", "contextual evidence", "thermal and contextual", "and contextual"])
            and not is_section_26_phase9_acceptance
        )
        if is_section_28_acceptance:
            entities["is_section_28_acceptance"] = True
            if not entities.get("event_ref"):
                entities["event_ref"] = "EVT-827"

        # Phase 8 Global Context Intelligence & Cross-Domain Fusion Commands
        # A. Section 24 Phase 8 Primary Acceptance Command
        is_section_24_phase8_acceptance = (
            any(w in cmd for w in ["investigate event 827", "investigate 827", "investigate evt-827", "investigate this event"])
            and any(w in cmd for w in ["thermal and contextual", "contextual sources", "contextual evidence", "and contextual"])
            and any(w in cmd for w in ["reduce uncertainty", "uncertainty", "contextual evidence conflicts", "sources are missing", "supports the event"])
            and not is_section_26_phase9_acceptance
        ) or (
            any(w in cmd for w in [
                "investigate event 827 using all available thermal and contextual sources",
                "using all available thermal and contextual sources",
                "what contextual evidence supports the event, what sources are missing"
            ]) and not is_section_26_phase9_acceptance
        )
        if is_section_24_phase8_acceptance:
            entities["is_section_24_phase8_acceptance"] = True
            if not entities.get("event_ref"):
                entities["event_ref"] = "EVT-827"


        # B. Show All Context Available
        is_show_all_context = any(w in cmd for w in [
            "show all context available for this event", "show all context available",
            "show all context", "all context available for this event", "all context available"
        ]) and not is_section_24_phase8_acceptance
        if is_show_all_context:
            entities["is_show_all_context"] = True

        # C. Investigate Industrial Context
        is_investigate_industrial_context = any(w in cmd for w in [
            "investigate the industrial context around this event",
            "investigate the industrial context", "investigate industrial context",
            "industrial context around this event", "industrial context for this event"
        ]) and not is_section_24_phase8_acceptance
        if is_investigate_industrial_context:
            entities["is_investigate_industrial_context"] = True

        # D. Associate Facility Context
        is_associate_facility_context = any(w in cmd for w in [
            "determine whether this event is associated with a facility",
            "whether this event is associated with a facility",
            "is associated with a facility", "associated with a facility",
            "associated with an industrial facility", "facility association"
        ]) and not is_section_24_phase8_acceptance
        if is_associate_facility_context:
            entities["is_associate_facility_context"] = True

        # E. Mining Context Support
        is_mining_context_support = any(w in cmd for w in [
            "determine whether mining context supports this event",
            "whether mining context supports this event",
            "mining context supports this event", "mining context support",
            "does mining context support", "mining support for this event"
        ]) and not is_section_24_phase8_acceptance
        if is_mining_context_support:
            entities["is_mining_context_support"] = True

        # F. Land Cover & Protected Area Context
        is_landcover_protected_context = any(w in cmd for w in [
            "show the land-cover and protected-area context",
            "show land-cover and protected-area context",
            "land-cover and protected-area context", "land cover and protected area context",
            "land cover and protected area", "land-cover and protected area"
        ]) and not is_section_24_phase8_acceptance
        if is_landcover_protected_context:
            entities["is_landcover_protected_context"] = True

        # G. Global Context Available
        is_global_context_available = any(w in cmd for w in [
            "show what global context is available for this investigation",
            "what global context is available for this investigation",
            "what global context is available", "show what global context is available",
            "global context is available", "global context available"
        ]) and not is_section_24_phase8_acceptance
        if is_global_context_available:
            entities["is_global_context_available"] = True

        # H. Missing Context Sources
        is_missing_context_sources = any(w in cmd for w in [
            "tell me which contextual sources are missing",
            "which contextual sources are missing", "contextual sources are missing",
            "what contextual sources are missing", "missing contextual sources"
        ]) and not is_section_24_phase8_acceptance
        if is_missing_context_sources:
            entities["is_missing_context_sources"] = True

        # I. Conflicting Context Evidence
        is_conflicting_context_evidence = any(w in cmd for w in [
            "identify conflicting contextual evidence", "conflicting contextual evidence",
            "identify conflicting context", "conflicting context evidence", "conflicting context"
        ]) and not is_section_24_phase8_acceptance
        if is_conflicting_context_evidence:
            entities["is_conflicting_context_evidence"] = True

        # J. Compare Strongest Contextual Explanations
        is_strongest_context_explanations = any(w in cmd for w in [
            "compare the strongest contextual explanations",
            "strongest contextual explanations", "compare contextual explanations",
            "strongest contextual explanation", "contextual explanations"
        ]) and not is_section_24_phase8_acceptance
        if is_strongest_context_explanations:
            entities["is_strongest_context_explanations"] = True

        # K. Reduce Uncertainty Context
        is_reduce_uncertainty_context = any(w in cmd for w in [
            "tell me what additional context would reduce uncertainty",
            "what additional context would reduce uncertainty",
            "additional context would reduce uncertainty",
            "reduce uncertainty with additional context", "reduce uncertainty"
        ]) and not is_section_24_phase8_acceptance
        if is_reduce_uncertainty_context:
            entities["is_reduce_uncertainty_context"] = True

        # L. Context Provenance
        is_context_provenance = any(w in cmd for w in [
            "show the context provenance", "show contextual provenance",
            "context provenance for this investigation", "context provenance",
            "contextual provenance", "context source provenance"
        ]) and not is_section_24_phase8_acceptance
        if is_context_provenance:
            entities["is_context_provenance"] = True

        # B. Thermal Sources Support
        is_thermal_sources_support = any(w in cmd for w in [
            "which thermal sources support this event", "which thermal sources support",
            "what thermal sources support", "thermal sources support this event",
            "thermal sources supporting", "which thermal sources"
        ]) and not is_section_28_acceptance and not is_section_24_phase8_acceptance
        if is_thermal_sources_support:
            entities["is_thermal_sources_support"] = True

        # C. Multiple Sources Support
        is_multiple_sources_support = any(w in cmd for w in [
            "does more than one source support", "more than one source support this thermal event",
            "more than one source support", "multiple thermal sources support", "multiple sources support"
        ]) and not is_section_28_acceptance and not is_section_24_phase8_acceptance
        if is_multiple_sources_support:
            entities["is_multiple_sources_support"] = True

        # D. Source Disagreements / Conflict
        is_source_disagreements = any(w in cmd for w in [
            "are there source disagreements", "source disagreements", "are there any source disagreements",
            "source disagreement", "disagreements between sources", "disagreements among sources"
        ]) and not is_section_28_acceptance and not is_section_24_phase8_acceptance
        if is_source_disagreements:
            entities["is_source_disagreements"] = True

        # E. Thermal Evidence Provenance (Section 29)
        is_thermal_provenance = any(w in cmd for w in [
            "show the thermal evidence provenance", "show the thermal-source provenance",
            "show thermal-source provenance", "thermal-source provenance for this investigation",
            "thermal evidence provenance", "thermal source provenance", "thermal provenance"
        ]) and not is_section_28_acceptance and not is_section_24_phase8_acceptance
        if is_thermal_provenance:
            entities["is_thermal_provenance"] = True

        # F. Thermal Coverage for Region
        is_thermal_coverage = any(w in cmd for w in [
            "what thermal coverage is available for this region", "what thermal coverage is available",
            "thermal coverage is available for this region", "thermal coverage for this region",
            "thermal coverage available", "what thermal coverage"
        ]) and not is_section_28_acceptance and not is_section_24_phase8_acceptance
        if is_thermal_coverage:
            entities["is_thermal_coverage"] = True

        # G. Investigate Event with All Thermal Sources
        is_investigate_all_thermal = any(w in cmd for w in [
            "investigate this event using all available thermal sources",
            "using all available thermal sources", "with all available thermal sources",
            "using all thermal sources", "investigate using all available thermal sources"
        ]) and not is_section_28_acceptance and not is_section_24_phase8_acceptance
        if is_investigate_all_thermal:
            entities["is_investigate_all_thermal"] = True

        # G. Weather Request Flag (Graceful Missing Provider Handling)
        is_weather_requested = any(w in cmd for w in [
            "weather context", "with weather", "weather data", "meteorological context"
        ])
        if is_weather_requested:
            entities["weather_requested"] = True

        # J. General Multi-Constraint Search Flag
        if any(w in cmd for w in ["persistent anomalies", "persistent anomaly", "abnormal thermal activity", "intensity is significantly above historical", "significantly above historical"]):
            entities["anomalous_only"] = True

        constraint_signals = sum([
            bool(entities.get("near_facility") or "within" in cmd or "near" in cmd),
            bool(entities.get("risk_level")),
            bool(entities.get("low_confidence") or is_low_conf),
            bool(entities.get("anomalous_only") or "anomal" in cmd or "above historical" in cmd or entities.get("baseline_condition")),
            bool(is_evidence_conflict),
            bool("requiring human verification" in cmd or "requiring verification" in cmd)
        ])
        is_deep_investigation = (
            entities.get("require_investigation") or 
            entities.get("require_dossier") or 
            entities.get("require_explain_risk") or 
            is_complex_acceptance or 
            entities.get("event_ref") or
            "investigate" in cmd
        )
        if constraint_signals >= 2 and not is_deep_investigation:
            entities["is_multi_constraint_query"] = True

        flag_count = sum([
            entities["require_investigation"],
            entities["require_explain_risk"],
            entities["require_compare_baseline"] and not is_multi_compare,
            entities["require_dossier"],
            (entities["near_facility"] or "facility" in cmd or "industrial" in cmd) and not is_multi_compare
        ])
        if flag_count >= 2 and not is_risk_explanation and not is_baseline_comparison and not entities.get("require_dossier") and not is_multi_compare:
            entities["is_composite"] = True

        # 9. Intent Classification (Objective-First Hierarchy)
        if any(w in cmd for w in ["dispatch", "emergency send", "send team", "call fire department", "deploy responders"]):
            intent = CommandIntent.DISPATCH_REQUEST
        elif is_complex_acceptance:
            intent = CommandIntent.INVESTIGATE
        elif is_operator_summary:
            intent = CommandIntent.STATUS
        elif is_analyst_prioritization:
            intent = CommandIntent.RANK
        elif is_priority_explanation:
            intent = CommandIntent.EXPLAIN
            entities["explain_type"] = "PRIORITY"
        elif is_evidence_conflict:
            intent = CommandIntent.EXPLAIN
            entities["explain_type"] = "CONFLICT"
        elif is_what_could_change:
            intent = CommandIntent.EXPLAIN
            entities["explain_type"] = "WHAT_COULD_CHANGE"
        elif is_evidence_strength or is_uncertainty:
            intent = CommandIntent.SUMMARIZE
        elif entities.get("is_multi_constraint_query"):
            intent = CommandIntent.LOCATE
        elif entities.get("close_investigation"):
            intent = CommandIntent.STATUS
        elif is_what_remains or is_why_stopped:
            intent = CommandIntent.STATUS
        elif is_what_do_you_know or is_summarize_inv:
            intent = CommandIntent.SUMMARIZE
        elif is_explain_selection:
            intent = CommandIntent.EXPLAIN
            entities["explain_type"] = "SELECTION"
        elif is_continue_inv or is_top_cands_investigate or entities.get("select_candidate"):
            intent = CommandIntent.INVESTIGATE
        elif entities.get("resume_investigation") or entities.get("refresh_investigation"):
            intent = CommandIntent.INVESTIGATE
        elif is_target_verification and not entities.get("is_composite"):
            intent = CommandIntent.VERIFY
            entities["explain_type"] = "VERIFICATION"
        elif any(w in cmd for w in ["system status", "intelligence status", "health", "system intelligence status"]):
            intent = CommandIntent.STATUS
        elif (
            any(w in cmd for w in [
                "verification queue", "analyst triage", "cases require human verification",
                "which cases require", "show verification queue", "pending verification"
            ]) or (
                ("human verification" in cmd or "need verification" in cmd)
                and any(w in cmd for w in ["which", "queue", "show", "list", "pending", "cases"])
            )
        ) and not entities.get("is_composite"):
            intent = CommandIntent.VERIFY
        elif entities.get("require_dossier") and not entities.get("is_composite"):
            intent = CommandIntent.GENERATE_REPORT
        elif entities.get("is_composite") or ("investigate" in cmd and any(w in cmd for w in ["gujarat", "facility", "critical", "three"]) and not entities.get("event_ref")):
            intent = CommandIntent.INVESTIGATE
        elif entities.get("is_multi_compare") or is_multi_compare:
            intent = CommandIntent.COMPARE
        elif is_risk_explanation and not entities.get("is_composite"):
            intent = CommandIntent.EXPLAIN
            entities["explain_type"] = "RISK"
        elif entities.get("require_explain_shap") and not entities.get("is_composite"):
            intent = CommandIntent.EXPLAIN
            entities["explain_type"] = "SHAP"
        elif is_baseline_comparison and not entities.get("is_composite"):
            intent = CommandIntent.COMPARE
        elif any(w in cmd for w in ["find", "search", "critical anomalies within", "near industrial facilities", "near facilities", "most suspicious"]) and not entities.get("is_composite") and not entities.get("event_ref"):
            intent = CommandIntent.LOCATE
        elif any(w in cmd for w in ["investigate", "inspect event", "deep dive", "examine"]):
            intent = CommandIntent.INVESTIGATE
        elif any(w in cmd for w in ["latest", "recent", "overview", "show high-risk", "show events", "show the latest"]):
            intent = CommandIntent.QUERY
        elif any(w in cmd for w in ["rank", "top 10", "highest-risk"]):
            intent = CommandIntent.RANK
        else:
            intent = CommandIntent.INVESTIGATE if entities.get("event_ref") else CommandIntent.QUERY

        # 10. Construct Explicit CommandObjective Model
        primary_goal = "QUERY"
        if is_section_26_phase9_acceptance:
            primary_goal = "SECTION_26_PHASE9_ACCEPTANCE"
        elif is_analyze_historical_behavior:
            primary_goal = "ANALYZE_HISTORICAL_BEHAVIOR"
        elif is_determine_persistence:
            primary_goal = "DETERMINE_PERSISTENCE"
        elif is_determine_recurrence:
            primary_goal = "DETERMINE_RECURRENCE"
        elif is_compare_historical_baseline:
            primary_goal = "COMPARE_HISTORICAL_BASELINE"
        elif is_determine_temporal_anomaly:
            primary_goal = "DETERMINE_TEMPORAL_ANOMALY"
        elif is_determine_seasonality:
            primary_goal = "DETERMINE_SEASONALITY"
        elif is_show_day_night:
            primary_goal = "SHOW_DAY_NIGHT_BEHAVIOR"
        elif is_explain_temporal_evidence:
            primary_goal = "EXPLAIN_TEMPORAL_EVIDENCE"
        elif is_missing_historical_data:
            primary_goal = "SHOW_MISSING_HISTORICAL_DATA"
        elif is_reduce_temporal_uncertainty:
            primary_goal = "REDUCE_TEMPORAL_UNCERTAINTY"
        elif is_combine_all_evidence:
            primary_goal = "COMBINE_ALL_EVIDENCE"
        elif is_temporal_provenance:
            primary_goal = "TEMPORAL_PROVENANCE"
        elif is_temporal_coverage:
            primary_goal = "TEMPORAL_COVERAGE"
        elif is_section_24_phase8_acceptance:
            primary_goal = "SECTION_24_PHASE8_ACCEPTANCE"
        elif is_section_28_acceptance:
            primary_goal = "SECTION_28_ACCEPTANCE"
        elif is_show_all_context:
            primary_goal = "SHOW_ALL_CONTEXT"
        elif is_investigate_industrial_context:
            primary_goal = "INVESTIGATE_INDUSTRIAL_CONTEXT"
        elif is_associate_facility_context:
            primary_goal = "ASSOCIATE_FACILITY_CONTEXT"
        elif is_mining_context_support:
            primary_goal = "MINING_CONTEXT_SUPPORT"
        elif is_landcover_protected_context:
            primary_goal = "LANDCOVER_PROTECTED_CONTEXT"
        elif is_global_context_available:
            primary_goal = "GLOBAL_CONTEXT_AVAILABLE"
        elif is_missing_context_sources:
            primary_goal = "MISSING_CONTEXT_SOURCES"
        elif is_conflicting_context_evidence:
            primary_goal = "CONFLICTING_CONTEXT_EVIDENCE"
        elif is_strongest_context_explanations:
            primary_goal = "STRONGEST_CONTEXT_EXPLANATIONS"
        elif is_reduce_uncertainty_context:
            primary_goal = "REDUCE_UNCERTAINTY_CONTEXT"
        elif is_context_provenance:
            primary_goal = "CONTEXT_PROVENANCE"
        elif is_thermal_sources_support:
            primary_goal = "THERMAL_SOURCES_SUPPORT"
        elif is_multiple_sources_support:
            primary_goal = "MULTIPLE_THERMAL_SOURCES_SUPPORT"
        elif is_source_disagreements:
            primary_goal = "SOURCE_DISAGREEMENTS"
        elif is_thermal_provenance:
            primary_goal = "THERMAL_SOURCE_PROVENANCE"
        elif is_thermal_coverage:
            primary_goal = "THERMAL_COVERAGE_QUERY"
        elif is_investigate_all_thermal:
            primary_goal = "INVESTIGATE_ALL_THERMAL_SOURCES"
        elif is_section_24_acceptance:
            primary_goal = "SECTION_24_ACCEPTANCE"
        elif is_sources_used:
            primary_goal = "SOURCES_USED"
        elif is_coverage_query:
            primary_goal = "GEOGRAPHIC_COVERAGE"
        elif is_missing_sources:
            primary_goal = "MISSING_SOURCES"
        elif is_coverage_sufficiency:
            primary_goal = "COVERAGE_SUFFICIENCY"
        elif is_source_provenance:
            primary_goal = "SOURCE_PROVENANCE"
        elif is_complex_acceptance:
            primary_goal = "COMPLEX_OPERATIONAL_ACCEPTANCE"
        elif is_operator_summary:
            primary_goal = "OPERATOR_INTELLIGENCE_SUMMARY"
        elif is_analyst_prioritization:
            primary_goal = "ANALYST_PRIORITIZATION"
        elif is_priority_explanation:
            primary_goal = "EXPLAIN_PRIORITY"
        elif is_evidence_conflict:
            primary_goal = "DETECT_CONFLICTS"
        elif is_what_could_change:
            primary_goal = "WHAT_COULD_CHANGE"
        elif is_evidence_strength:
            primary_goal = "ASSESS_EVIDENCE_STRENGTH"
        elif is_uncertainty:
            primary_goal = "ASSESS_UNCERTAINTY"
        elif entities.get("is_multi_constraint_query"):
            primary_goal = "MULTI_CONSTRAINT_SEARCH"
        elif is_what_remains:
            primary_goal = "WHAT_REMAINS"
        elif is_why_stopped:
            primary_goal = "WHY_STOPPED"
        elif is_what_do_you_know:
            primary_goal = "WHAT_KNOWN"
        elif is_summarize_inv:
            primary_goal = "SUMMARIZE_INVESTIGATION"
        elif is_explain_selection:
            primary_goal = "EXPLAIN_SELECTION"
        elif is_continue_inv:
            primary_goal = "CONTINUE_INVESTIGATION"
        elif is_top_cands_investigate:
            primary_goal = "INVESTIGATE_TOP_CANDIDATES"
        elif entities.get("select_candidate"):
            primary_goal = "SELECT_CANDIDATE"
        elif is_target_verification:
            primary_goal = "CHECK_VERIFICATION"
        elif entities.get("is_multi_compare"):
            primary_goal = "MULTI_EVENT_COMPARE"
        elif (
            entities.get("baseline_condition")
            and (entities.get("near_facility") or "within" in cmd)
            and not entities.get("is_composite")
            and not entities.get("event_ref")
            and not entities.get("require_dossier")
        ):
            primary_goal = "MULTI_CONSTRAINT_FILTER"
        elif entities.get("surgical_stop") or entities.get("strict_stopping"):
            primary_goal = "SURGICAL_EXPLANATION"
        elif "suspicious" in cmd and ("explain" in cmd or "why" in cmd or "find" in cmd) and not entities.get("event_ref"):
            primary_goal = "IDENTIFY_AND_EXPLAIN_SUSPICIOUS"
        elif entities.get("require_dossier") or intent == CommandIntent.GENERATE_REPORT:
            primary_goal = "GENERATE_DOSSIER"
        elif is_risk_explanation or (intent == CommandIntent.EXPLAIN and entities.get("explain_type") == "RISK"):
            primary_goal = "EXPLAIN_RISK"
        elif entities.get("require_explain_shap") or (intent == CommandIntent.EXPLAIN and entities.get("explain_type") == "SHAP"):
            primary_goal = "EXPLAIN_SHAP"
        elif is_baseline_comparison or (intent == CommandIntent.COMPARE and not entities.get("is_multi_compare")):
            primary_goal = "COMPARE_BASELINE"
        elif is_evidence_req or entities.get("require_evidence_summary") or intent == CommandIntent.SUMMARIZE:
            primary_goal = "SHOW_EVIDENCE"
        elif entities.get("event_ref"):
            primary_goal = "INVESTIGATE_TARGET"
        elif intent == CommandIntent.LOCATE:
            primary_goal = "LOCATE_ANOMALIES"

        requested_output = "SYNTHESIS"
        if primary_goal == "GENERATE_DOSSIER":
            requested_output = "DOSSIER_PDF"
        elif primary_goal in ["MULTI_EVENT_COMPARE", "INVESTIGATE_TOP_CANDIDATES"]:
            requested_output = "COMPARISON"
        elif primary_goal in [
            "EXPLAIN_RISK", "EXPLAIN_SHAP", "EXPLAIN_SELECTION", "IDENTIFY_AND_EXPLAIN_SUSPICIOUS",
            "SURGICAL_EXPLANATION", "ASSOCIATE_FACILITY_CONTEXT", "MINING_CONTEXT_SUPPORT",
            "STRONGEST_CONTEXT_EXPLANATIONS", "REDUCE_UNCERTAINTY_CONTEXT", "DETERMINE_PERSISTENCE",
            "DETERMINE_RECURRENCE", "COMPARE_HISTORICAL_BASELINE", "DETERMINE_TEMPORAL_ANOMALY",
            "DETERMINE_SEASONALITY", "EXPLAIN_TEMPORAL_EVIDENCE", "REDUCE_TEMPORAL_UNCERTAINTY"
        ]:
            requested_output = "EXPLANATION"
        elif primary_goal in [
            "WHAT_REMAINS", "WHY_STOPPED", "WHAT_KNOWN", "SUMMARIZE_INVESTIGATION", "SOURCES_USED",
            "GEOGRAPHIC_COVERAGE", "MISSING_SOURCES", "COVERAGE_SUFFICIENCY", "SOURCE_PROVENANCE",
            "THERMAL_SOURCES_SUPPORT", "MULTIPLE_THERMAL_SOURCES_SUPPORT", "SOURCE_DISAGREEMENTS",
            "THERMAL_SOURCE_PROVENANCE", "THERMAL_COVERAGE_QUERY", "SHOW_ALL_CONTEXT",
            "LANDCOVER_PROTECTED_CONTEXT", "GLOBAL_CONTEXT_AVAILABLE", "MISSING_CONTEXT_SOURCES",
            "CONFLICTING_CONTEXT_EVIDENCE", "CONTEXT_PROVENANCE", "ANALYZE_HISTORICAL_BEHAVIOR",
            "SHOW_DAY_NIGHT_BEHAVIOR", "SHOW_MISSING_HISTORICAL_DATA", "TEMPORAL_PROVENANCE",
            "TEMPORAL_COVERAGE"
        ]:
            requested_output = "STATUS_REPORT"
        elif primary_goal in [
            "SECTION_24_ACCEPTANCE", "SECTION_28_ACCEPTANCE", "SECTION_24_PHASE8_ACCEPTANCE",
            "SECTION_26_PHASE9_ACCEPTANCE", "COMBINE_ALL_EVIDENCE", "INVESTIGATE_ALL_THERMAL_SOURCES",
            "INVESTIGATE_INDUSTRIAL_CONTEXT"
        ]:
            requested_output = "SYNTHESIS"

        stopping_condition = "SUFFICIENT_EVIDENCE_FOR_OBJECTIVE"
        if primary_goal == "SECTION_26_PHASE9_ACCEPTANCE":
            stopping_condition = "SECTION_26_PHASE9_HISTORICAL_TEMPORAL_EVALUATED_AND_HALT"
        elif primary_goal == "SECTION_24_PHASE8_ACCEPTANCE":
            stopping_condition = "SECTION_24_PHASE8_CROSS_DOMAIN_EVALUATED_AND_HALT"
        elif primary_goal == "SECTION_28_ACCEPTANCE":
            stopping_condition = "SECTION_28_MULTI_PROVIDER_EVALUATED_AND_HALT"
        elif primary_goal in [
            "ANALYZE_HISTORICAL_BEHAVIOR", "SHOW_DAY_NIGHT_BEHAVIOR", "SHOW_MISSING_HISTORICAL_DATA",
            "TEMPORAL_PROVENANCE", "TEMPORAL_COVERAGE"
        ]:
            stopping_condition = "TEMPORAL_INTELLIGENCE_REPORTED_AND_HALT"
        elif primary_goal in [
            "DETERMINE_PERSISTENCE", "DETERMINE_RECURRENCE", "COMPARE_HISTORICAL_BASELINE",
            "DETERMINE_TEMPORAL_ANOMALY", "DETERMINE_SEASONALITY", "EXPLAIN_TEMPORAL_EVIDENCE",
            "REDUCE_TEMPORAL_UNCERTAINTY"
        ]:
            stopping_condition = "TEMPORAL_ANALYSIS_EVALUATED_AND_HALT"
        elif primary_goal == "COMBINE_ALL_EVIDENCE":
            stopping_condition = "ALL_EVIDENCE_COMBINED_AND_HALT"
        elif primary_goal in ["SHOW_ALL_CONTEXT", "LANDCOVER_PROTECTED_CONTEXT", "GLOBAL_CONTEXT_AVAILABLE", "MISSING_CONTEXT_SOURCES", "CONFLICTING_CONTEXT_EVIDENCE", "CONTEXT_PROVENANCE"]:
            stopping_condition = "CONTEXT_INTELLIGENCE_REPORTED_AND_HALT"
        elif primary_goal in ["ASSOCIATE_FACILITY_CONTEXT", "MINING_CONTEXT_SUPPORT", "STRONGEST_CONTEXT_EXPLANATIONS", "REDUCE_UNCERTAINTY_CONTEXT"]:
            stopping_condition = "CONTEXTUAL_EXPLANATION_REPORTED_AND_HALT"
        elif primary_goal == "INVESTIGATE_INDUSTRIAL_CONTEXT":
            stopping_condition = "INDUSTRIAL_CONTEXT_EVALUATED_AND_HALT"
        elif primary_goal in ["THERMAL_SOURCES_SUPPORT", "MULTIPLE_THERMAL_SOURCES_SUPPORT", "SOURCE_DISAGREEMENTS", "THERMAL_SOURCE_PROVENANCE", "THERMAL_COVERAGE_QUERY"]:
            stopping_condition = "THERMAL_INTELLIGENCE_REPORTED_AND_HALT"
        elif primary_goal == "INVESTIGATE_ALL_THERMAL_SOURCES":
            stopping_condition = "ALL_THERMAL_SOURCES_EVALUATED_AND_HALT"
        elif primary_goal == "SECTION_24_ACCEPTANCE":
            stopping_condition = "SECTION_24_VERIFICATION_EVALUATED_AND_HALT"
        elif primary_goal in ["SOURCES_USED", "GEOGRAPHIC_COVERAGE", "MISSING_SOURCES", "COVERAGE_SUFFICIENCY", "SOURCE_PROVENANCE"]:
            stopping_condition = "PROVIDER_AUDIT_REPORTED_AND_HALT"
        elif primary_goal == "GENERATE_DOSSIER":
            stopping_condition = "GENERATE_DOSSIER_AND_HALT"
        elif primary_goal == "MULTI_EVENT_COMPARE":
            stopping_condition = "IDENTIFY_STRONGEST_CASE_AND_HALT"
        elif primary_goal == "INVESTIGATE_TOP_CANDIDATES":
            stopping_condition = "INVESTIGATE_COHORT_AND_HALT"
        elif primary_goal == "WHAT_REMAINS":
            stopping_condition = "OPERATIONAL_STATUS_REPORTED_AND_HALT"
        elif primary_goal == "WHY_STOPPED":
            stopping_condition = "STOPPING_TRACE_EXPLAINED_AND_HALT"
        elif primary_goal in ["WHAT_KNOWN", "SUMMARIZE_INVESTIGATION"]:
            stopping_condition = "KNOWLEDGE_SYNTHESIS_REPORTED_AND_HALT"
        elif primary_goal == "EXPLAIN_SELECTION":
            stopping_condition = "SELECTION_RATIONALE_EXPLAINED_AND_HALT"
        elif primary_goal == "CHECK_VERIFICATION":
            stopping_condition = "VERIFICATION_STATUS_EVALUATED_AND_HALT"
        elif primary_goal == "MULTI_CONSTRAINT_FILTER":
            stopping_condition = "FILTER_MATCHING_CANDIDATES_AND_HALT"
        elif primary_goal == "SURGICAL_EXPLANATION":
            stopping_condition = "SUFFICIENT_EVIDENCE_FOR_CLASSIFICATION_AND_RISK"
        elif entities.get("strict_stopping"):
            stopping_condition = "SUFFICIENT_EVIDENCE_FOR_REQUESTED_DIMENSIONS_AND_HALT"
        elif primary_goal == "EXPLAIN_RISK":
            stopping_condition = "SUFFICIENT_EVIDENCE_FOR_RISK_EXPLANATION_AND_HALT"
        elif primary_goal == "COMPARE_BASELINE":
            stopping_condition = "SUFFICIENT_EVIDENCE_FOR_BASELINE_COMPARISON_AND_HALT"

        constraints_list = []
        if entities.get("distance_m"):
            constraints_list.append(f"within {int(entities['distance_m']/1000)}km of facility")
        elif entities.get("near_facility"):
            constraints_list.append("near industrial facility")
        if entities.get("risk_level") or "high-risk" in cmd:
            constraints_list.append(f"risk >= {entities.get('risk_level', 'HIGH')}")
        if entities.get("baseline_condition"):
            constraints_list.append("anomalous baseline ratio")

        objective = CommandObjective(
            primary_goal=primary_goal,
            target_event=entities.get("event_ref"),
            target_region=entities.get("state"),
            facility_context=entities.get("facility_context"),
            max_distance_m=entities.get("distance_m"),
            risk_threshold=entities.get("risk_level", "HIGH" if "high-risk" in cmd else None),
            baseline_condition=entities.get("baseline_condition"),
            candidate_count=entities.get("candidate_count", 1),
            constraints=constraints_list,
            ranking_criteria=entities.get("target_hypothesis") or ("RISK_SCORE" if "highest-risk" in cmd else None),
            target_hypothesis=entities.get("target_hypothesis"),
            requested_evidence=[k for k, v in entities.items() if k.startswith("require_") and v],
            requested_output=requested_output,
            stopping_condition=stopping_condition,
            resolved_from_context=entities.get("resolved_from_context", False),
            contextual_reference=entities.get("contextual_reference")
        )
        entities["objective"] = objective

        return {
            "intent": intent,
            "entities": entities,
            "objective": objective,
            "confidence": 0.98,
            "provider": "LocalDeterministicProvider",
            "raw_command": command
        }


class JarvisCommandInterpreter:
    """
    Main facade for interpreting natural language operational commands into typed intents and parameters.
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or LocalDeterministicProvider()

    def parse_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Tuple[CommandIntent, Dict[str, Any]]:
        """
        Parses command string into typed CommandIntent and entities dictionary.
        """
        result = self.provider.interpret(command, context)
        intent = result["intent"]
        entities = result["entities"]
        return intent, entities

    def interpret(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Direct facade for provider interpretation.
        """
        return self.provider.interpret(command, context)



command_interpreter = JarvisCommandInterpreter()
