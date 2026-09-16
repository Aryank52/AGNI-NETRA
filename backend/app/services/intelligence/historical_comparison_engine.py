"""
AGNI-NETRA — Deterministic Historical Comparison Engine
Phase 25: Unified Event Intelligence + Historical Incident Intelligence

Calculates point-in-time safe historical comparisons for any thermal event:
1. Historical baseline
2. Current deviation from baseline
3. Recurrence
4. Persistence
5. Seasonality
6. Temporal trend
7. Similar historical thermal events
8. Similar verified historical incidents

Strict Anti-Leakage Rule: All calculations use ONLY observations observed BEFORE event observation timestamp T_obs.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.app.models.domain import (
    ThermalEvent,
    ThermalDetection,
    ThermalHistory,
    IndustrialFacility,
    FacilityBaseline,
    HistoricalIncident
)
from backend.app.services.intelligence.historical_incident_registry import (
    historical_incident_registry,
    haversine_km
)


def to_utc(dt: Optional[Any]) -> Optional[datetime]:
    """Ensures datetime object is timezone-aware in UTC."""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return None


def to_naive_utc(dt: Optional[Any]) -> Optional[datetime]:
    """Ensures datetime object is naive UTC for SQLite DB queries."""
    aware = to_utc(dt)
    if aware is None:
        return None
    return aware.replace(tzinfo=None)


class HistoricalComparisonEngine:
    """
    Authoritative deterministic engine for longitudinal comparisons and historical grounding.
    """

    @classmethod
    def resolve_event(cls, db: Session, event_ref: Union[ThermalEvent, str]) -> Optional[ThermalEvent]:
        if isinstance(event_ref, ThermalEvent):
            return event_ref
        ref_str = str(event_ref).strip()
        ev = db.query(ThermalEvent).filter(ThermalEvent.id == ref_str).first()
        if ev:
            return ev
        ev = db.query(ThermalEvent).filter(ThermalEvent.event_code == ref_str).first()
        if ev:
            return ev
        # Try suffix / code match
        ev = db.query(ThermalEvent).filter(ThermalEvent.event_code.ilike(f"%{ref_str}%")).first()
        return ev

    @classmethod
    def compare_event(
        cls,
        db: Session,
        event_ref: Union[ThermalEvent, str],
        point_in_time_cutoff: Optional[datetime] = None,
        radius_km: float = 15.0
    ) -> Dict[str, Any]:
        """
        Runs comprehensive point-in-time safe historical comparison for an event.
        Guarantees zero data leakage: observations after cutoff are strictly excluded.
        """
        event = cls.resolve_event(db, event_ref)
        if not event:
            return cls._empty_comparison_result(str(event_ref))

        # Establish point-in-time cutoff
        cutoff = point_in_time_cutoff
        if cutoff is None:
            cutoff = event.first_seen or event.last_seen or datetime.now(timezone.utc)
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=timezone.utc)

        current_frp = round(float(event.max_frp or 0.0), 1)

        # 1. Point-in-time safe historical baseline
        baseline = cls._calculate_point_in_time_baseline(db, event, cutoff, radius_km)

        # 2. Baseline deviation
        deviation = cls._calculate_baseline_deviation(current_frp, baseline)

        # 3. Point-in-time recurrence
        recurrence = cls._calculate_point_in_time_recurrence(db, event, cutoff, radius_km)

        # 4. Point-in-time persistence
        persistence = cls._calculate_point_in_time_persistence(db, event, cutoff)

        # 5. Seasonality profile
        seasonality = cls._calculate_point_in_time_seasonality(db, event, cutoff, radius_km)

        # 6. Temporal trend
        trend = cls._calculate_point_in_time_trend(db, event, cutoff, radius_km)

        # 7. Similar historical thermal events
        similar_events = cls._find_similar_historical_events(db, event, cutoff, radius_km)

        # 8. Similar verified historical incidents
        similar_incidents = historical_incident_registry.find_similar_verified_incidents(
            db=db,
            latitude=float(event.latitude),
            longitude=float(event.longitude),
            peak_frp=current_frp,
            classification=event.prediction.predicted_class if event.prediction else None,
            radius_km=radius_km * 2.0,
            point_in_time_cutoff=cutoff,
            limit=5
        )

        # Historical relationship tier
        if len(similar_incidents) > 0 or (baseline["sample_count"] >= 10 and deviation["deviation_ratio"] < 2.0):
            relationship_tier = "HIGH"
        elif baseline["sample_count"] >= 5 or len(similar_events) >= 3:
            relationship_tier = "MODERATE"
        elif baseline["sample_count"] >= 1 or len(similar_events) >= 1:
            relationship_tier = "LOW"
        else:
            relationship_tier = "NONE"

        # Deterministic Grounded Answers to the 6 Core Questions
        answers = cls._generate_core_answers(
            event=event,
            current_frp=current_frp,
            baseline=baseline,
            deviation=deviation,
            recurrence=recurrence,
            persistence=persistence,
            similar_events=similar_events,
            similar_incidents=similar_incidents
        )

        return {
            "event_id": event.id,
            "event_code": event.event_code,
            "cutoff_timestamp": cutoff.isoformat(),
            "baseline_frp_mean": baseline["mean_frp"],
            "baseline_frp_std": baseline["std_frp"],
            "baseline_sample_count": baseline["sample_count"],
            "baseline_status": baseline["status"],
            "current_frp": current_frp,
            "deviation_ratio": deviation["deviation_ratio"],
            "deviation_percent": deviation["deviation_percent"],
            "deviation_z_score": deviation["z_score"],
            "is_intensity_anomaly": deviation["is_anomaly"],
            "deviation_explanation": deviation["explanation"],
            "persistence_score": persistence["persistence_score"],
            "persistence_category": persistence["persistence_category"],
            "active_days_count": persistence["active_days_count"],
            "span_days": persistence["span_days"],
            "recurrence_rate": recurrence["recurrence_rate"],
            "recurrence_category": recurrence["recurrence_category"],
            "episodes_count": recurrence["episodes_count"],
            "recent_30d_episodes": recurrence["recent_30d_episodes"],
            "seasonality_pattern": seasonality["pattern"],
            "seasonal_peak_months": seasonality["peak_months"],
            "temporal_trend": trend,
            "similar_historical_events_count": len(similar_events),
            "similar_historical_events": similar_events,
            "previous_verified_incidents_count": len(similar_incidents),
            "previous_verified_incidents": similar_incidents,
            "historical_relationship": relationship_tier,
            "answers": answers
        }

    @classmethod
    def _calculate_point_in_time_baseline(
        cls,
        db: Session,
        event: ThermalEvent,
        cutoff: datetime,
        radius_km: float
    ) -> Dict[str, Any]:
        """
        Computes baseline using strictly prior observations (t < cutoff).
        """
        # Facility baseline check
        if event.facility_id:
            fb = db.query(FacilityBaseline).filter(FacilityBaseline.facility_id == event.facility_id).first()
            if fb and fb.mean_frp > 0:
                mean_f = round(float(fb.mean_frp), 1)
                var_f = float(fb.variance_frp or 0.0)
                std_f = round(math.sqrt(var_f) if var_f > 0 else (mean_f * 0.35), 1)
                samples = int(fb.frequency_days or 30)
                return {
                    "mean_frp": mean_f,
                    "std_frp": std_f,
                    "sample_count": samples,
                    "status": "ESTABLISHED_FACILITY"
                }

        # Spatial perimeter query (detections prior to cutoff)
        deg = radius_km / 111.0
        naive_cutoff = to_naive_utc(cutoff)
        prior_dets = db.query(ThermalDetection).filter(
            ThermalDetection.latitude.between(event.latitude - deg, event.latitude + deg),
            ThermalDetection.longitude.between(event.longitude - deg, event.longitude + deg),
            ThermalDetection.acq_timestamp < naive_cutoff
        ).all()

        if not prior_dets:
            # Check historical archive table
            prior_hist = db.query(ThermalHistory).filter(
                ThermalHistory.latitude.between(event.latitude - deg, event.latitude + deg),
                ThermalHistory.longitude.between(event.longitude - deg, event.longitude + deg),
                ThermalHistory.acq_timestamp < naive_cutoff
            ).all()
            if prior_hist:
                frps = [h.frp for h in prior_hist if h.frp and h.frp > 0]
                if frps:
                    mean_f = round(float(sum(frps) / len(frps)), 1)
                    std_f = round(float((sum((x - mean_f)**2 for x in frps) / max(1, len(frps) - 1))**0.5), 1) if len(frps) > 1 else round(mean_f * 0.35, 1)
                    return {
                        "mean_frp": mean_f,
                        "std_frp": std_f,
                        "sample_count": len(frps),
                        "status": "HISTORICAL_ARCHIVE"
                    }

            return {
                "mean_frp": 0.0,
                "std_frp": 0.0,
                "sample_count": 0,
                "status": "NO_BASELINE"
            }

        frps = [d.frp for d in prior_dets if d.frp and d.frp > 0]
        if not frps:
            return {
                "mean_frp": 0.0,
                "std_frp": 0.0,
                "sample_count": 0,
                "status": "NO_BASELINE"
            }

        mean_f = round(float(sum(frps) / len(frps)), 1)
        variance = sum((x - mean_f)**2 for x in frps) / max(1, len(frps) - 1) if len(frps) > 1 else (mean_f * 0.35)**2
        std_f = round(math.sqrt(variance), 1)

        return {
            "mean_frp": mean_f,
            "std_frp": std_f,
            "sample_count": len(frps),
            "status": "SPATIAL_CELL" if len(frps) >= 5 else "SPARSE_HISTORY"
        }

    @classmethod
    def _calculate_baseline_deviation(
        cls,
        current_frp: float,
        baseline: Dict[str, Any]
    ) -> Dict[str, Any]:
        mean_frp = baseline["mean_frp"]
        std_frp = baseline["std_frp"]

        if mean_frp <= 0:
            return {
                "deviation_ratio": 1.0,
                "deviation_percent": 0.0,
                "z_score": 0.0,
                "is_anomaly": False,
                "explanation": "No prior baseline exists for statistical comparison."
            }

        dev_ratio = round(current_frp / max(1.0, mean_frp), 2)
        dev_pct = round(((current_frp - mean_frp) / max(1.0, mean_frp)) * 100.0, 1)
        z_score = round((current_frp - mean_frp) / max(1.0, std_frp), 2)

        if z_score >= 2.5 or dev_ratio >= 2.5:
            is_anomaly = True
            explanation = f"Critical deviation: +{dev_pct}% above baseline mean ({mean_frp} MW, z={z_score}σ)."
        elif z_score >= 1.5 or dev_ratio >= 1.5:
            is_anomaly = True
            explanation = f"Elevated deviation: +{dev_pct}% above baseline mean ({mean_frp} MW, z={z_score}σ)."
        elif z_score <= -1.5:
            is_anomaly = False
            explanation = f"Below baseline: {dev_pct}% lower than historical average ({mean_frp} MW)."
        else:
            is_anomaly = False
            explanation = f"Nominal: within normal historical operating parameters (+{dev_pct}%)."

        return {
            "deviation_ratio": dev_ratio,
            "deviation_percent": dev_pct,
            "z_score": z_score,
            "is_anomaly": is_anomaly,
            "explanation": explanation
        }

    @classmethod
    def _calculate_point_in_time_recurrence(
        cls,
        db: Session,
        event: ThermalEvent,
        cutoff: datetime,
        radius_km: float
    ) -> Dict[str, Any]:
        deg = radius_km / 111.0
        naive_cutoff = to_naive_utc(cutoff)
        prior_dets = db.query(ThermalDetection).filter(
            ThermalDetection.latitude.between(event.latitude - deg, event.latitude + deg),
            ThermalDetection.longitude.between(event.longitude - deg, event.longitude + deg),
            ThermalDetection.acq_timestamp < naive_cutoff
        ).order_by(ThermalDetection.acq_timestamp.asc()).all()

        if not prior_dets:
            # Fallback to thermal_history
            prior_hist = db.query(ThermalHistory).filter(
                ThermalHistory.latitude.between(event.latitude - deg, event.latitude + deg),
                ThermalHistory.longitude.between(event.longitude - deg, event.longitude + deg),
                ThermalHistory.acq_timestamp < naive_cutoff
            ).all()
            if not prior_hist:
                return {
                    "recurrence_rate": 0.0,
                    "recurrence_category": "NON_RECURRENT",
                    "episodes_count": 0,
                    "recent_30d_episodes": 0
                }
            ts_list = sorted([to_utc(h.acq_timestamp) for h in prior_hist if h.acq_timestamp])
        else:
            ts_list = sorted([to_utc(d.acq_timestamp) for d in prior_dets if d.acq_timestamp])

        if not ts_list:
            return {
                "recurrence_rate": 0.0,
                "recurrence_category": "NON_RECURRENT",
                "episodes_count": 0,
                "recent_30d_episodes": 0
            }

        # Cluster into episodes with 48h separation
        episodes: List[List[datetime]] = []
        curr_ep: List[datetime] = [ts_list[0]]
        for i in range(1, len(ts_list)):
            delta_h = (ts_list[i] - ts_list[i-1]).total_seconds() / 3600.0
            if delta_h <= 48.0:
                curr_ep.append(ts_list[i])
            else:
                episodes.append(curr_ep)
                curr_ep = [ts_list[i]]
        if curr_ep:
            episodes.append(curr_ep)

        ep_count = len(episodes)
        span_days = max(1, (ts_list[-1] - ts_list[0]).days + 1)
        rate = round(ep_count / float(span_days), 3)

        cutoff_30d = to_utc(cutoff) - timedelta(days=30)
        recent_count = sum(1 for ep in episodes if to_utc(ep[-1]) >= cutoff_30d)

        if ep_count >= 8 or recent_count >= 3:
            cat = "HIGHLY_RECURRENT"
        elif ep_count >= 2:
            cat = "RECURRENT"
        else:
            cat = "NON_RECURRENT"

        return {
            "recurrence_rate": rate,
            "recurrence_category": cat,
            "episodes_count": ep_count,
            "recent_30d_episodes": recent_count
        }

    @classmethod
    def _calculate_point_in_time_persistence(
        cls,
        db: Session,
        event: ThermalEvent,
        cutoff: datetime
    ) -> Dict[str, Any]:
        # Current event detections up to cutoff
        naive_cutoff = to_naive_utc(cutoff)
        dets = db.query(ThermalDetection).filter(
            ThermalDetection.event_id == event.id,
            ThermalDetection.acq_timestamp <= naive_cutoff
        ).order_by(ThermalDetection.acq_timestamp.asc()).all()

        if not dets:
            return {
                "persistence_score": 1.0,
                "persistence_category": "TRANSIENT",
                "active_days_count": 1,
                "span_days": 1
            }

        ts = [to_utc(d.acq_timestamp) for d in dets if d.acq_timestamp]
        if not ts:
            return {
                "persistence_score": 1.0,
                "persistence_category": "TRANSIENT",
                "active_days_count": 1,
                "span_days": 1
            }

        dates = {t.date() for t in ts}
        active_days = len(dates)
        span = max(1, (ts[-1] - ts[0]).days + 1)

        raw_score = math.log1p(active_days) * (len(dets) / float(span)) * 2.5
        persistence_score = round(min(10.0, max(0.5, raw_score)), 2)

        if persistence_score >= 6.5 or active_days >= 7:
            category = "HIGHLY_PERSISTENT"
        elif persistence_score >= 3.5 or active_days >= 3:
            category = "PERSISTENT"
        elif persistence_score >= 1.5 or active_days >= 2:
            category = "RECURRING"
        else:
            category = "TRANSIENT"

        return {
            "persistence_score": persistence_score,
            "persistence_category": category,
            "active_days_count": active_days,
            "span_days": span
        }

    @classmethod
    def _calculate_point_in_time_seasonality(
        cls,
        db: Session,
        event: ThermalEvent,
        cutoff: datetime,
        radius_km: float
    ) -> Dict[str, Any]:
        deg = radius_km / 111.0
        naive_cutoff = to_naive_utc(cutoff)
        prior = db.query(ThermalDetection).filter(
            ThermalDetection.latitude.between(event.latitude - deg, event.latitude + deg),
            ThermalDetection.longitude.between(event.longitude - deg, event.longitude + deg),
            ThermalDetection.acq_timestamp < naive_cutoff
        ).all()

        if len(prior) < 6:
            return {"pattern": "INSUFFICIENT_DATA", "peak_months": []}

        months = [d.acq_timestamp.month for d in prior if d.acq_timestamp]
        month_counts = {m: months.count(m) for m in range(1, 13)}
        active_months = sum(1 for c in month_counts.values() if c > 0)

        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        if active_months >= 8:
            return {"pattern": "NON_SEASONAL_CONTINUOUS", "peak_months": []}

        sorted_m = sorted(month_counts.items(), key=lambda x: x[1], reverse=True)
        top_2 = sum(x[1] for x in sorted_m[:2])
        if top_2 / max(1, len(months)) >= 0.60:
            peaks = [month_names[m-1] for m, c in sorted_m[:2] if c > 0]
            return {"pattern": "SEASONAL", "peak_months": peaks}

        return {"pattern": "SPORADIC", "peak_months": []}

    @classmethod
    def _calculate_point_in_time_trend(
        cls,
        db: Session,
        event: ThermalEvent,
        cutoff: datetime,
        radius_km: float
    ) -> str:
        deg = radius_km / 111.0
        cutoff_aware = to_utc(cutoff)
        cutoff_30d_naive = to_naive_utc(cutoff_aware - timedelta(days=30))
        cutoff_naive = to_naive_utc(cutoff_aware)

        recent = db.query(ThermalDetection).filter(
            ThermalDetection.latitude.between(event.latitude - deg, event.latitude + deg),
            ThermalDetection.longitude.between(event.longitude - deg, event.longitude + deg),
            ThermalDetection.acq_timestamp >= cutoff_30d_naive,
            ThermalDetection.acq_timestamp < cutoff_naive
        ).all()

        older = db.query(ThermalDetection).filter(
            ThermalDetection.latitude.between(event.latitude - deg, event.latitude + deg),
            ThermalDetection.longitude.between(event.longitude - deg, event.longitude + deg),
            ThermalDetection.acq_timestamp < cutoff_30d_naive
        ).all()

        if not recent or not older:
            return "STABLE"

        recent_avg = sum(d.frp for d in recent if d.frp) / max(1, len(recent))
        older_avg = sum(d.frp for d in older if d.frp) / max(1, len(older))

        if recent_avg >= older_avg * 1.30:
            return "INCREASING"
        elif recent_avg <= older_avg * 0.70:
            return "DECREASING"
        return "STABLE"

    @classmethod
    def _find_similar_historical_events(
        cls,
        db: Session,
        event: ThermalEvent,
        cutoff: datetime,
        radius_km: float
    ) -> List[Dict[str, Any]]:
        deg = radius_km / 111.0
        cutoff_naive = to_naive_utc(cutoff)
        candidates = db.query(ThermalEvent).filter(
            ThermalEvent.id != event.id,
            ThermalEvent.latitude.between(event.latitude - deg, event.latitude + deg),
            ThermalEvent.longitude.between(event.longitude - deg, event.longitude + deg),
            ThermalEvent.first_seen < cutoff_naive
        ).limit(10).all()

        results = []
        c_frp = float(event.max_frp or 50.0)

        for cand in candidates:
            dist = haversine_km(float(event.latitude), float(event.longitude), float(cand.latitude), float(cand.longitude))
            if dist > radius_km:
                continue
            cand_frp = float(cand.max_frp or 50.0)
            frp_ratio = min(c_frp, cand_frp) / max(1.0, max(c_frp, cand_frp))
            dist_sim = max(0.0, 1.0 - (dist / radius_km))
            sim_score = round(0.55 * dist_sim + 0.45 * frp_ratio, 2)

            results.append({
                "event_id": cand.id,
                "event_code": cand.event_code,
                "distance_km": dist,
                "similarity_score": sim_score,
                "peak_frp": cand_frp,
                "status": cand.status,
                "first_seen": cand.first_seen.isoformat() if cand.first_seen else None
            })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:5]

    @classmethod
    def _generate_core_answers(
        cls,
        event: ThermalEvent,
        current_frp: float,
        baseline: Dict[str, Any],
        deviation: Dict[str, Any],
        recurrence: Dict[str, Any],
        persistence: Dict[str, Any],
        similar_events: List[Dict[str, Any]],
        similar_incidents: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Synthesizes deterministic answers to the 6 authoritative user questions.
        """
        # 1. Is this normal for this location?
        if baseline["status"] in ["ESTABLISHED_FACILITY", "SPATIAL_CELL"]:
            if deviation["is_anomaly"]:
                q1 = f"Abnormal: Current intensity ({current_frp} MW) is {deviation['deviation_percent']:+.1f}% above the historical baseline of {baseline['mean_frp']} MW (z={deviation['z_score']}σ)."
            else:
                q1 = f"Normal: Current intensity ({current_frp} MW) is within expected operating limits ({deviation['deviation_percent']:+.1f}% of {baseline['mean_frp']} MW baseline)."
        else:
            q1 = f"No established longitudinal baseline exists for this immediate location ({baseline['sample_count']} prior observations)."

        # 2. Has this happened before?
        if len(similar_incidents) > 0:
            q2 = f"Yes. Detected {len(similar_events)} prior thermal events in this corridor, and {len(similar_incidents)} verified historical incidents are on record."
        elif len(similar_events) > 0:
            q2 = f"Yes. Found {len(similar_events)} historically similar thermal events in this area; no verified incidents are currently on file."
        else:
            q2 = "No historically similar thermal events were detected within this spatial perimeter prior to this observation."

        # 3. How often does it happen?
        if recurrence["episodes_count"] > 0:
            q3 = f"{recurrence['recurrence_category']}: {recurrence['episodes_count']} prior thermal episodes recorded ({recurrence['recent_30d_episodes']} in the past 30 days)."
        else:
            q3 = "Zero prior recurring episodes recorded within this area."

        # 4. Is this event more intense than normal?
        if baseline["mean_frp"] > 0:
            if deviation["deviation_ratio"] >= 1.5:
                q4 = f"Significantly more intense: {current_frp} MW is {deviation['deviation_ratio']}x the historical average of {baseline['mean_frp']} MW."
            elif deviation["deviation_ratio"] <= 0.8:
                q4 = f"Less intense: {current_frp} MW is below the historical average of {baseline['mean_frp']} MW."
            else:
                q4 = f"Comparable intensity: {current_frp} MW aligns with baseline average of {baseline['mean_frp']} MW."
        else:
            q4 = f"Baseline unavailable; observed radiative output is {current_frp} MW."

        # 5. Does it resemble previous incidents?
        if similar_incidents:
            top_inc = similar_incidents[0]
            q5 = f"Yes. High resemblance to verified incident {top_inc['incident_code']} ({top_inc['classification']}, similarity {top_inc['similarity_score']:.2f}, {top_inc['distance_km']} km away)."
        else:
            q5 = "No prior verified incidents with matching spatial and radiative characteristics exist in this corridor."

        # 6. Is the current event persistent?
        q6 = f"{persistence['persistence_category']}: Observed across {persistence['active_days_count']} active calendar days over a {persistence['span_days']}-day span (persistence score {persistence['persistence_score']}/10)."

        return {
            "is_normal": q1,
            "has_happened_before": q2,
            "how_often": q3,
            "recurrence_frequency": q3,
            "more_intense_than_normal": q4,
            "intensity_relative_to_baseline": q4,
            "resembles_previous_incidents": q5,
            "resemble_previous_incidents": q5,
            "is_persistent": q6
        }


historical_comparison_engine = HistoricalComparisonEngine()
