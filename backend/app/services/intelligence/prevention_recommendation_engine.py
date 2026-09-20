"""
AGNI-NETRA — Proactive Fire Prevention Recommendation Engine
Phase: Proactive Prevention & Root-Cause Intelligence Extension

Generates structured, evidence-linked preventive recommendations for verified authorities
and facility safety operators.
Strict Invariant: Recommends non-guaranteed risk mitigations using "MAY REDUCE RECURRENCE RISK".
Never guarantees outcome ("WILL PREVENT FUTURE FIRES" is forbidden).
"""

from typing import List, Dict, Any, Optional


class PreventionRecommendationEngine:
    """
    Deterministic rule engine that maps identified contributing factors and root-cause hypotheses
    to evidence-linked actionable recommendations.
    """

    @classmethod
    def generate_recommendations(
        cls,
        case_id: str,
        facility_name: Optional[str],
        facility_type: Optional[str],
        hypotheses: List[Dict[str, Any]],
        recurrence_rate: float,
        persistence_score: float,
        baseline_deviation_ratio: float,
        is_protected_area_nearby: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes preventive actions grounded in supported and plausible hypotheses.
        """
        recommendations = []

        # Find supported or plausible hypotheses
        supported_or_plausible = [
            h for h in hypotheses
            if h.get("status") in ["SUPPORTED", "PLAUSIBLE"]
        ]

        # 1. Industrial Process / Flare Optimization
        if any(h.get("category") == "INDUSTRIAL_PROCESS" for h in supported_or_plausible):
            recommendations.append({
                "case_id": case_id,
                "hypothesis_category": "INDUSTRIAL_PROCESS",
                "recommendation": (
                    f"Conduct technical audit of elevated flare operating headers, gas recovery compressors, "
                    f"and purge gas flows at {facility_name or 'the facility'} to identify uncombusted hydrocarbon slip."
                ),
                "reason": (
                    f"Continuous thermal baseline deviation ({baseline_deviation_ratio:.1f}x) and high recurrence ({recurrence_rate:.1f} episodes/yr) "
                    f"indicate cyclical process flaring or off-gas pressure fluctuations."
                ),
                "supporting_evidence": [
                    f"Baseline deviation ratio: {baseline_deviation_ratio:.1f}x",
                    f"Historical recurrence rate: {recurrence_rate:.1f} episodes/yr"
                ],
                "risk_relevance": "Process flaring intensity and unexpected off-gas thermal excursions",
                "responsible_authority_category": "FACILITY_OPERATOR",
                "urgency": "HIGH" if baseline_deviation_ratio > 2.0 else "MEDIUM",
                "expected_prevention_objective": "MAY REDUCE RECURRENCE RISK of unplanned high-volume emergency flaring excursions.",
                "status": "PROPOSED"
            })

            recommendations.append({
                "case_id": case_id,
                "hypothesis_category": "INDUSTRIAL_PROCESS",
                "recommendation": (
                    "Schedule joint regulatory inspection with Directorate of Industrial Safety & Health (DISH) "
                    "for high-temperature process unit relief valves and emergency blowdown drums."
                ),
                "reason": "Persistent high-temperature thermal signatures indicate recurrent relief system activation.",
                "supporting_evidence": [
                    f"Persistence score: {persistence_score:.2f}",
                    "Industrial facility registered under major hazard installations"
                ],
                "risk_relevance": "Regulatory compliance and pressure relief containment",
                "responsible_authority_category": "INDUSTRIAL_SAFETY_AUTHORITY",
                "urgency": "MEDIUM",
                "expected_prevention_objective": "MAY REDUCE RECURRENCE RISK by verifying mechanical integrity of overpressure protection.",
                "status": "PROPOSED"
            })

        # 2. Equipment Failure / Mechanical Integrity
        if any(h.get("category") == "EQUIPMENT_FAILURE" for h in supported_or_plausible):
            recommendations.append({
                "case_id": case_id,
                "hypothesis_category": "EQUIPMENT_FAILURE",
                "recommendation": (
                    "Implement acoustic and infrared thermography scans of high-pressure rotating pumps, compressor seals, "
                    "and furnace transfer lines across the process perimeter."
                ),
                "reason": "Anomalous thermal spikes may correlate with frictional heating or mechanical seal degradation.",
                "supporting_evidence": [
                    "Thermal intensity baseline deviation",
                    "Persistent localized hotspot concentration"
                ],
                "risk_relevance": "Mechanical breakdown leading to volatile fluid ignition",
                "responsible_authority_category": "FACILITY_OPERATOR",
                "urgency": "HIGH",
                "expected_prevention_objective": "MAY REDUCE RECURRENCE RISK of catastrophic seal blowout and pressurized containment loss.",
                "status": "PROPOSED"
            })

        # 3. Fuel or Hydrocarbon / Storage & Handling
        if any(h.get("category") in ["FUEL_OR_HYDROCARBON", "STORAGE_OR_HANDLING"] for h in supported_or_plausible):
            recommendations.append({
                "case_id": case_id,
                "hypothesis_category": "STORAGE_OR_HANDLING",
                "recommendation": (
                    "Review primary and secondary rim seal integrity on floating-roof hydrocarbon storage tanks "
                    "and test foam deluge suppression systems in coordination with local fire authorities."
                ),
                "reason": "Petrochemical bulk liquid storage facilities present chronic vapor loss and rim seal ignition hazards.",
                "supporting_evidence": [
                    "Nearby bulk hydrocarbon storage inventory",
                    "High thermal radiant flux density in facility buffer"
                ],
                "risk_relevance": "Atmospheric storage tank rim fires and vapor ignition",
                "responsible_authority_category": "LOCAL_FIRE_SERVICE",
                "urgency": "HIGH",
                "expected_prevention_objective": "MAY REDUCE RECURRENCE RISK of vapor rim ignition through proactive seal replacement and fire water readiness.",
                "status": "PROPOSED"
            })

        # 4. Environmental & Ecological Buffer Protection
        if is_protected_area_nearby:
            recommendations.append({
                "case_id": case_id,
                "hypothesis_category": "FOREST_OR_VEGETATION",
                "recommendation": (
                    "Establish a 100-meter cleared firebreak barrier between the industrial facility boundary wall "
                    "and adjoining protected scrub/forest buffer zones, accompanied by seasonal dry fuel clearance."
                ),
                "reason": "Proximity to protected ecological reserves creates secondary ignition risks from industrial perimeter heat sources.",
                "supporting_evidence": [
                    "Protected ecological reserve or forest boundary within 5.0 km buffer"
                ],
                "risk_relevance": "Secondary ecological wildfire propagation across boundary interface",
                "responsible_authority_category": "ENVIRONMENTAL_AUTHORITY",
                "urgency": "MEDIUM",
                "expected_prevention_objective": "MAY REDUCE RECURRENCE RISK of industrial radiant heat igniting surrounding scrub vegetation.",
                "status": "PROPOSED"
            })

        # 5. Continuous Thermal Surveillance & Air Quality Monitoring
        recommendations.append({
            "case_id": case_id,
            "hypothesis_category": "INDUSTRIAL_PROCESS",
            "recommendation": (
                "Install automated ground-level optical/thermal CCTV surveillance linked to state pollution control "
                "continuous emission monitoring systems (CEMS) for 24x7 flare stack smoke opacity tracking."
            ),
            "reason": "Real-time ground validation bridges the revisit interval between polar-orbiting satellite overpasses.",
            "supporting_evidence": [
                f"Multi-year satellite thermal recurrence record ({recurrence_rate:.1f} episodes/yr)"
            ],
            "risk_relevance": "Surveillance coverage gaps between satellite passes",
            "responsible_authority_category": "POLLUTION_CONTROL_AUTHORITY",
            "urgency": "MEDIUM",
            "expected_prevention_objective": "MAY REDUCE RECURRENCE RISK through early detection of uncombusted smoke emissions before thermal escalation.",
            "status": "PROPOSED"
        })

        # 6. District Administration Emergency Coordination
        recommendations.append({
            "case_id": case_id,
            "hypothesis_category": "INDUSTRIAL_PROCESS",
            "recommendation": (
                "Update District Off-Site Emergency Management Plan (DM Plan) with recent thermal recurrence patterns "
                "and conduct triennial mock drills involving JMC Fire Brigade, DISH, and facility safety teams."
            ),
            "reason": "Ensures mutual aid coordination across municipal fire services and specialized industrial responders.",
            "supporting_evidence": [
                f"District jurisdictional responsibility: {facility_name or 'Industrial Zone'}"
            ],
            "risk_relevance": "Inter-agency command coordination and community off-site safety",
            "responsible_authority_category": "DISTRICT_ADMINISTRATION",
            "urgency": "LOW",
            "expected_prevention_objective": "MAY REDUCE RECURRENCE RISK of containment failure escalating beyond facility boundaries into public domains.",
            "status": "PROPOSED"
        })

        return recommendations


prevention_recommendation_engine = PreventionRecommendationEngine()
