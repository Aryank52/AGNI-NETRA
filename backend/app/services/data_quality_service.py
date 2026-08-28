from datetime import datetime, timezone
from typing import Dict, Any, List


class DataQualityService:
    """
    Geospatial & Remote Sensing Data Quality Evaluation Engine.
    Computes transparent, reproducible data quality metrics without artificial fabrication.
    """

    def evaluate_observation_quality(
        self,
        confidence: float,
        brightness_k: float,
        frp_mw: float,
        scan_angle: float = 0.0,
        acq_time: datetime = None
    ) -> Dict[str, Any]:
        """
        Evaluates physical observation telemetry against remote sensing calibration bounds.
        """
        # 1. Sensor Confidence Weight (40%)
        conf_score = min(1.0, max(0.0, confidence / 100.0))

        # 2. Radiative Intensity Validity (30%)
        # Normal physical combustion FRP ranges between 0.5 MW and 10,000 MW
        if frp_mw >= 5.0 and brightness_k >= 310.0:
            intensity_validity = 1.0
        elif frp_mw >= 1.0:
            intensity_validity = 0.85
        else:
            intensity_validity = 0.60

        # 3. Geometric Scan Degradation (15%)
        # Edge-of-scan pixels have larger ground footprint (bow-tie effect)
        scan_quality = 1.0 - (min(60.0, abs(scan_angle)) / 120.0)

        # 4. Temporal Latency (15%)
        latency_score = 1.0
        if acq_time:
            now = datetime.now(timezone.utc)
            if acq_time.tzinfo is None:
                acq_time = acq_time.replace(tzinfo=timezone.utc)
            latency_hours = max(0.0, (now - acq_time).total_seconds() / 3600.0)
            if latency_hours > 72.0:
                latency_score = 0.70
            elif latency_hours > 24.0:
                latency_score = 0.85
            else:
                latency_score = 1.0

        composite_score = (
            (conf_score * 0.40) +
            (intensity_validity * 0.30) +
            (scan_quality * 0.15) +
            (latency_score * 0.15)
        )

        grade = "EXCELLENT" if composite_score >= 0.88 else "GOOD" if composite_score >= 0.72 else "MODERATE"

        return {
            "composite_quality_score": round(composite_score, 3),
            "quality_grade": grade,
            "confidence_factor": round(conf_score, 2),
            "intensity_validity": round(intensity_validity, 2),
            "geometric_quality": round(scan_quality, 2),
            "latency_factor": round(latency_score, 2)
        }


data_quality_service = DataQualityService()
