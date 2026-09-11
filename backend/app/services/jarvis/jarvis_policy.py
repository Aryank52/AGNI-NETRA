"""
AGNI-NETRA — JARVIS Central Operating Policy
Authoritative governance rules enforcing operational boundaries, permission gating,
blocked mutation interception, and the non-bypassable Operational Dispatch Gate invariant.
"""

from typing import Dict, Any, List, Set, Tuple, Optional
from backend.app.models.jarvis_schemas import CommandIntent


# Authoritative Safety Invariant: Live physical/emergency dispatch is permanently locked.
ENABLE_OPERATIONAL_DISPATCH_GATE: bool = False


class JarvisOperatingPolicy:
    """
    Central Operating Policy for the JARVIS Master Agent.
    """

    ALLOWED_OPERATIONS: Set[str] = {
        "READ",
        "ANALYZE",
        "INVESTIGATE",
        "CLASSIFY",
        "EXPLAIN",
        "COMPARE",
        "RANK",
        "SUMMARIZE",
        "GENERATE_REPORT",
        "CREATE_PERMITTED_VERIFICATION_CASE",
        "STATUS",
        "LOCATE"
    }

    RESTRICTED_OPERATIONS: Set[str] = {
        "ARBITRARY_SQL",
        "DELETE",
        "SCHEMA_CHANGES",
        "MODEL_ACTIVATION",
        "MODEL_CHANGES",
        "THRESHOLD_CHANGES",
        "DISPATCH",
        "OS_CONTROL",
        "RBAC_BYPASS",
        "HITL_BYPASS",
        "UNAUTHORIZED_WRITES",
        "AUTONOMOUS_ACTION_WITHOUT_USER_COMMAND"
    }

    MUTATION_KEYWORDS: List[str] = [
        "DROP TABLE", "DELETE FROM", "TRUNCATE", "ALTER TABLE",
        "UPDATE thermal_", "INSERT INTO", "GRANT ALL", "REVOKE",
        ";--", "SHUTDOWN", "EXEC(", "EXECUTE("
    ]

    DISPATCH_KEYWORDS: List[str] = [
        "dispatch", "send drone", "deploy responders", "call fire department",
        "deploy team", "emergency dispatch", "dispatch team", "send emergency"
    ]

    @classmethod
    def evaluate_command_safety(
        cls,
        command: str,
        intent: Optional[CommandIntent] = None,
        user_role: str = "ANALYST"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Evaluates command against Central Operating Policy.
        Returns: (is_allowed: bool, violation_type: Optional[str], reason: Optional[str])
        """
        cmd_upper = command.strip().upper()

        # 1. Block Dispatch Operations unconditionally
        if (
            intent == CommandIntent.DISPATCH_REQUEST or
            any(k.upper() in cmd_upper for k in cls.DISPATCH_KEYWORDS)
        ):
            return (
                False,
                "OPERATIONAL_DISPATCH_BLOCKED",
                "Direct automated emergency dispatch is strictly prohibited by AGNI-NETRA Safety Policy (ENABLE_OPERATIONAL_DISPATCH_GATE=False). Physical dispatch requires offline dual-key authentication."
            )

        # 2. Block Arbitrary SQL mutations and DDL/DML attacks
        for kw in cls.MUTATION_KEYWORDS:
            if kw in cmd_upper:
                return (
                    False,
                    "MUTATION_BLOCKED",
                    f"Command contains prohibited mutating or administrative statement ('{kw}'). All JARVIS operations are strictly read/analyze/investigate only."
                )

        # 3. Block Model / Threshold tampering
        if any(w in cmd_upper for w in ["ACTIVATE MODEL", "CHANGE THRESHOLD", "SET THRESHOLD", "DISABLE GATE", "OVERRIDE GATE"]):
            return (
                False,
                "GOVERNANCE_TAMPER_BLOCKED",
                "Model weights, promotion gates, and risk thresholds are immutable via command console. Governance must be performed through verified offline pipelines."
            )

        # 4. RBAC checks
        role_upper = (user_role or "ANALYST").upper()
        if role_upper == "PUBLIC":
            # Public role is restricted from deep investigations, internal facility IDs, and raw SQL/telemetry
            if intent in [CommandIntent.INVESTIGATE, CommandIntent.GENERATE_REPORT]:
                return (
                    False,
                    "RBAC_RESTRICTION",
                    "Public role accounts are restricted from generating comprehensive industrial intelligence dossiers or executing targeted facility deep dives. Upgrade to Analyst or Officer."
                )

        return True, None, None


operating_policy = JarvisOperatingPolicy()
