"""
AGNI-NETRA — PostGIS Set-Based FIRMS Thermal Spatial Association & Power Profiler
Associates NASA FIRMS thermal detections with power facility geometries at 500m, 1km, and 2km.
Computes empirical thermal baselines (Mean, Median, P75, P90, P99 FRP, Recurrence, Diurnal persistence).
"""

import os
import sys
import json
import time
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from backend.app.core.database import engine


def run_firms_power_profiling():
    print("=" * 80, flush=True)
    print("   AGNI-NETRA — POSTGIS FIRMS SPATIAL ASSOCIATION & THERMAL PROFILER   ", flush=True)
    print("=" * 80, flush=True)

    start_time = time.time()

    with engine.connect() as conn:
        total_pwr = conn.execute(text("""
            SELECT count(*) FROM industrial_facilities
            WHERE geom IS NOT NULL
              AND (facility_type = 'POWER_PLANT' OR source = 'CEA+OSM' OR cea_project_name IS NOT NULL);
        """)).scalar()
        print(f"[AGNI-NETRA] Target power facilities with PostGIS geometry: {total_pwr:,}", flush=True)

        print("[AGNI-NETRA] Executing high-performance spatial join against 1.77M FIRMS thermal history...", flush=True)
        spatial_profile_query = text("""
            SELECT 
                f.id,
                f.name,
                f.cea_project_name,
                f.plant_capacity,
                f.prime_mover,
                f.state,
                COUNT(CASE WHEN ST_DWithin(f.geom::geography, ST_SetSRID(ST_MakePoint(th.longitude, th.latitude), 4326)::geography, 500) THEN 1 END) AS count_500m,
                COUNT(CASE WHEN ST_DWithin(f.geom::geography, ST_SetSRID(ST_MakePoint(th.longitude, th.latitude), 4326)::geography, 1000) THEN 1 END) AS count_1km,
                COUNT(*) AS count_2km,
                AVG(th.frp) AS avg_frp,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY th.frp) AS median_frp,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY th.frp) AS p75_frp,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY th.frp) AS p90_frp,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY th.frp) AS p99_frp,
                MAX(th.frp) AS max_frp,
                VARIANCE(th.frp) AS var_frp,
                MIN(th.acq_timestamp) AS first_seen,
                MAX(th.acq_timestamp) AS last_seen,
                COUNT(DISTINCT DATE(th.acq_timestamp)) AS active_days,
                COUNT(CASE WHEN th.day_night = 'N' THEN 1 END) AS night_count,
                COUNT(CASE WHEN th.day_night = 'D' THEN 1 END) AS day_count
            FROM industrial_facilities f
            JOIN thermal_history th
              ON th.latitude BETWEEN f.latitude - 0.025 AND f.latitude + 0.025
             AND th.longitude BETWEEN f.longitude - 0.025 AND f.longitude + 0.025
             AND ST_DWithin(f.geom::geography, ST_SetSRID(ST_MakePoint(th.longitude, th.latitude), 4326)::geography, 2000)
            WHERE f.geom IS NOT NULL
              AND (f.facility_type = 'POWER_PLANT' OR f.source = 'CEA+OSM' OR f.cea_project_name IS NOT NULL)
            GROUP BY f.id, f.name, f.cea_project_name, f.plant_capacity, f.prime_mover, f.state;
        """)

        matched_results = conn.execute(spatial_profile_query).fetchall()

    print(f"[AGNI-NETRA] Spatial association identified {len(matched_results):,} power facilities with FIRMS thermal detections within 2km.", flush=True)

    total_500m = 0
    total_1km = 0
    total_2km = 0
    active_thermal_facilities = 0

    facility_updates = []
    baseline_inserts = []

    for r in matched_results:
        f_id, f_name, cea_proj, cap, pm, f_state, cnt_500m, cnt_1km, cnt_2km, avg_frp, med_frp, p75, p90, p99, max_frp, var_frp, first_s, last_s, act_days, night_cnt, day_cnt = r

        total_500m += cnt_500m
        total_1km += cnt_1km
        total_2km += cnt_2km

        dn_ratio = (night_cnt / day_cnt) if (day_cnt and day_cnt > 0) else (float(night_cnt) if night_cnt else 1.0)
        status_band = "ACTIVE_THERMAL_SOURCE" if cnt_1km >= 10 else ("MODERATE_INTERMITTENT" if cnt_2km >= 3 else "LOW_OBSERVATIONS")

        if cnt_2km >= 3:
            active_thermal_facilities += 1

        distrib = {
            "mean_frp": round(float(avg_frp or 0), 2),
            "median_frp": round(float(med_frp or 0), 2),
            "max_frp": round(float(max_frp or 0), 2),
            "p75_frp": round(float(p75 or 0), 2),
            "p90_frp": round(float(p90 or 0), 2),
            "p99_frp": round(float(p99 or 0), 2),
            "count_500m": cnt_500m,
            "count_1km": cnt_1km,
            "count_2km": cnt_2km,
            "day_night_ratio": round(dn_ratio, 2),
            "first_observed": first_s.isoformat() if first_s else None,
            "last_observed": last_s.isoformat() if last_s else None
        }

        baseline_inserts.append({
            "id": f"BL-{f_id[:32]}",
            "facility_id": f_id,
            "mean_frp": round(float(avg_frp or 0), 2),
            "median_frp": round(float(med_frp or 0), 2),
            "variance_frp": round(float(var_frp or 0), 2),
            "max_historical_frp": round(float(max_frp or 0), 2),
            "frp_distribution": json.dumps(distrib),
            "frequency_days": act_days or 0,
            "day_night_ratio": round(dn_ratio, 2),
            "status_band": status_band,
            "notes": f"Empirical FIRMS Baseline: {cnt_2km} detections within 2km ({cnt_1km} within 1km), {act_days} active days."
        })

        facility_updates.append({
            "facility_id": f_id,
            "det_500m": cnt_500m,
            "det_1km": cnt_1km,
            "det_2km": cnt_2km,
            "status": status_band
        })

    # Update industrial_facilities
    print(f"\n[AGNI-NETRA] Updating {len(facility_updates):,} facility records in DB...", flush=True)
    update_fac_query = text("""
        UPDATE industrial_facilities
        SET firms_detections_500m = :det_500m,
            firms_detections_1km = :det_1km,
            firms_detections_2km = :det_2km,
            thermal_activity_status = :status
        WHERE id = :facility_id;
    """)

    with engine.begin() as conn:
        for i in range(0, len(facility_updates), 500):
            batch = facility_updates[i : i + 500]
            conn.execute(update_fac_query, batch)

    # Insert facility_baselines
    if baseline_inserts:
        print(f"[AGNI-NETRA] Registering {len(baseline_inserts):,} empirical power facility baselines...", flush=True)
        baseline_query = text("""
            INSERT INTO facility_baselines (
                id, facility_id, mean_frp, median_frp, variance_frp,
                max_historical_frp, frp_distribution, frequency_days,
                day_night_ratio, status_band, notes, updated_at
            ) VALUES (
                :id, :facility_id, :mean_frp, :median_frp, :variance_frp,
                :max_historical_frp, CAST(:frp_distribution AS JSON), :frequency_days,
                :day_night_ratio, :status_band, :notes, NOW() AT TIME ZONE 'UTC'
            )
            ON CONFLICT (facility_id) DO UPDATE SET
                mean_frp = EXCLUDED.mean_frp,
                median_frp = EXCLUDED.median_frp,
                variance_frp = EXCLUDED.variance_frp,
                max_historical_frp = EXCLUDED.max_historical_frp,
                frp_distribution = EXCLUDED.frp_distribution,
                frequency_days = EXCLUDED.frequency_days,
                day_night_ratio = EXCLUDED.day_night_ratio,
                status_band = EXCLUDED.status_band,
                notes = EXCLUDED.notes,
                updated_at = NOW() AT TIME ZONE 'UTC';
        """)

        with engine.begin() as conn:
            for i in range(0, len(baseline_inserts), 500):
                batch = baseline_inserts[i : i + 500]
                conn.execute(baseline_query, batch)

    elapsed = time.time() - start_time
    print(f"\n[AGNI-NETRA] FIRMS Spatial Association Completed in {elapsed:.2f} seconds.", flush=True)
    print(f"   • Total Power Facilities Analyzed : {total_pwr:,}", flush=True)
    print(f"   • Facilities with Thermal Activity: {len(matched_results):,}", flush=True)
    print(f"   • Active/Moderate Thermal Plants  : {active_thermal_facilities:,}", flush=True)
    print(f"   • FIRMS Detections within 500m   : {total_500m:,}", flush=True)
    print(f"   • FIRMS Detections within 1km    : {total_1km:,}", flush=True)
    print(f"   • FIRMS Detections within 2km    : {total_2km:,}", flush=True)


if __name__ == "__main__":
    run_firms_power_profiling()
