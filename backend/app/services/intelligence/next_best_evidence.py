"""
AGNI-NETRA Phase 13: Next-Best-Evidence Engine
Recommends targeted information acquisitions and sensor observations to reduce epistemic uncertainty
across competing operational intelligence hypotheses.

Strict Operating Principle:
Decision support only. NOT autonomous action.
Never claims a recommendation will definitely resolve uncertainty.
"""

from typing import Dict, Any, List, Optional
from backend.app.models.canonical import (
    NextBestEvidenceRecommendation, InformationValueCategory
)


class NextBestEvidenceEngine:
    """
    Deterministic decision-support engine identifying the highest information-gain observations
    to resolve competing operational hypotheses and reduce epistemic uncertainty.
    """

    AVAILABLE_RECOMMENDATION_TYPES = [
        "HIGH_RES_OPTICAL",
        "ADDITIONAL_THERMAL_PASS",
        "GROUND_SENSOR",
        "SCADA_TELEMETRY",
        "WEATHER_OBSERVATION",
        "AIR_QUALITY_OBSERVATION",
        "ADDITIONAL_SAR",
        "MORE_HISTORY",
        "FACILITY_REGISTRY_CHECK"
    ]

    @classmethod
    def recommend_next_best_evidence(
        cls,
        event_data: Dict[str, Any],
        competing_hypotheses: Optional[List[Dict[str, Any]]] = None,
        data_gaps: Optional[List[Dict[str, Any]]] = None,
        epistemic_uncertainty: Optional[Dict[str, Any]] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> List[NextBestEvidenceRecommendation]:
        """
        Evaluates current evidence state, missing providers, and competing hypotheses
        to generate structured, prioritized evidence recommendations.
        """
        recs: List[NextBestEvidenceRecommendation] = []
        competing_hyps = competing_hypotheses or []
        gaps = data_gaps or []
        uncertainty = epistemic_uncertainty or {}

        facility_name = event_data.get("facility_name") or (context_data.get("facility_name") if context_data else None)
        facility_type = event_data.get("facility_type") or (context_data.get("facility_type") if context_data else None)
        cloud_cover = float(event_data.get("cloud_cover", 20.0))

        # Check dominant and viable hypotheses
        hyp_ids = [h.get("hypothesis_id", "") for h in competing_hyps]
        is_industrial = any("INDUSTRIAL" in h_id or "FLARING" in h_id or "RECURRING" in h_id for h_id in hyp_ids) or bool(facility_name)
        has_wildfire_comp = any("FOREST" in h_id or "VEGETATION" in h_id or "AGRICULTURAL" in h_id for h_id in hyp_ids)

        # 1. SCADA Telemetry (High Value for Industrial Facilities)
        if is_industrial:
            recs.append(NextBestEvidenceRecommendation(
                target_source="SCADA_TELEMETRY",
                reason="Query facility distributed control system (DCS) / SCADA flare header mass flow rate and relief valve status.",
                uncertainty_addressed="Differentiates routine operational flaring from emergency process upset or equipment failure.",
                evidence_gap="Direct internal facility process flow data is currently unconfigured or restricted.",
                expected_information_value=InformationValueCategory.HIGH.value,
                provider_status="UNCONFIGURED",
                availability="ON_DEMAND_ANALYST_REQUEST",
                action_steps=[
                    "Request plant operational telemetry log for relief header system.",
                    "Verify flare gas mass flow rate against baseline operational thresholds.",
                    "Correlate steam assist injection rate with observed radiative power."
                ]
            ))

        # 2. High-Resolution Optical Overpass (PlanetScope / Sentinel-2 MSI)
        recs.append(NextBestEvidenceRecommendation(
            target_source="HIGH_RES_OPTICAL",
            reason="Acquire cloud-free sub-meter or 10m VNIR/SWIR imagery at next daylight orbital pass.",
            uncertainty_addressed="Confirms physical flame footprint, structural integrity of surrounding tanks, and presence of smoke plume.",
            evidence_gap="Current VIIRS passes provide 375m coarse resolution without structural micro-detail.",
            expected_information_value=InformationValueCategory.HIGH.value if cloud_cover < 50.0 else InformationValueCategory.MEDIUM.value,
            provider_status="AVAILABLE",
            availability="NEXT_ORBITAL_PASS",
            action_steps=[
                "Task upcoming Sentinel-2 or commercial high-res optical constellation pass.",
                "Inspect Band 12 (SWIR 2.2µm) for localized high-temperature flame centroid.",
                "Verify presence or absence of structural roof deformation on nearby storage units."
            ]
        ))

        # 3. Synthetic Aperture Radar (SAR) Coherence / Backscatter (Sentinel-1 C-band)
        if cloud_cover >= 30.0 or is_industrial:
            recs.append(NextBestEvidenceRecommendation(
                target_source="ADDITIONAL_SAR",
                reason="Acquire Sentinel-1 or NISAR dual-polarization (VV/VH) radar backscatter over the coordinates.",
                uncertainty_addressed="Penetrates atmospheric smoke and cloud cover; detects localized metallic structural collapse or tank damage.",
                evidence_gap="Optical passes may be hindered by night or heavy overcast.",
                expected_information_value=InformationValueCategory.HIGH.value if cloud_cover >= 50.0 else InformationValueCategory.MEDIUM.value,
                provider_status="AVAILABLE",
                availability="SCHEDULED_REVISIT",
                action_steps=[
                    "Process Sentinel-1 interferometric coherence map against pre-event baseline.",
                    "Check cross-polarization ratio (VH/VV) for anomalous volume scattering anomalies.",
                    "Flag structural deformation zones within 500m of thermal centroid."
                ]
            ))

        # 4. Additional Thermal Pass (NOAA-20 / NOAA-21 / ISRO INSAT-3D)
        recs.append(NextBestEvidenceRecommendation(
            target_source="ADDITIONAL_THERMAL_PASS",
            reason="Cross-correlate with next polar-orbiting VIIRS pass or 15-minute INSAT-3D/3DR geostationary TIR observation.",
            uncertainty_addressed="Evaluates thermal decay curve and persistence duration across consecutive satellite revisits.",
            evidence_gap="Sub-hourly temporal evolution between 12-hour polar revisits.",
            expected_information_value=InformationValueCategory.MEDIUM.value,
            provider_status="AVAILABLE",
            availability="IMMEDIATE_ORBITAL",
            action_steps=[
                "Monitor upcoming NOAA-21 VIIRS overpass for persistent radiative emission.",
                "Extract INSAT-3D TIR thermal anomaly time series at 15-minute intervals.",
                "Update persistence coefficient if detection persists across 3 consecutive cycles."
            ]
        ))

        # 5. Local Surface Weather & Air Quality Observations
        recs.append(NextBestEvidenceRecommendation(
            target_source="WEATHER_OBSERVATION",
            reason="Correlate local automatic weather station (AWS) surface anemometer wind measurements with ERA5 reanalysis.",
            uncertainty_addressed="Refines boundary-layer plume transport vector and downwind hazard corridor projection.",
            evidence_gap="ERA5 reanalysis operates on ~31km spatial grid; localized terrain channeling may cause micro-scale shifts.",
            expected_information_value=InformationValueCategory.MEDIUM.value,
            provider_status="AVAILABLE",
            availability="CONTINUOUS_TELEMETERED",
            action_steps=[
                "Retrieve closest IMD / State AWS 10m wind velocity and direction.",
                "Re-compute plume dispersion cone using verified surface anemometer vectors.",
                "Disclose any angular variance between ERA5 model and local weather station."
            ]
        ))

        # 6. Facility Registry & Environmental Clearance Cadastral Check
        if not facility_name or event_data.get("facility_status") == "CANDIDATE":
            recs.append(NextBestEvidenceRecommendation(
                target_source="FACILITY_REGISTRY_CHECK",
                reason="Cross-reference coordinates against Ministry of Environment (PARIVESH) and State Pollution Control Board registries.",
                uncertainty_addressed="Validates official licensed operational boundaries and authorized emission discharge stacks.",
                evidence_gap="Unregistered or unindexed industrial asset.",
                expected_information_value=InformationValueCategory.HIGH.value,
                provider_status="AVAILABLE",
                availability="IMMEDIATE_DB_LOOKUP",
                action_steps=[
                    "Query PARIVESH database for environmental clearance compliance filings.",
                    "Inspect state industrial development corporation (SIDC) cadastral parcel maps.",
                    "Update facility known status upon operator verification."
                ]
            ))

        return recs


next_best_evidence_engine = NextBestEvidenceEngine()
