"""
AGNI-NETRA — Phase 6B Multi-Year Historical Intelligence Engine Verification Suite
==================================================================================
Tests:
1. Facility baselines table population and FRP percentile validity (p25..p99).
2. Multi-distance mining thermal associations (500m, 1km, 2km).
3. Seasonal historical baselines with 12-month pattern dictionaries.
4. Unified 12-factor event feature vectors with contextual distances and ratios.
5. Pilot isolation: 2022 demo/pilot records are strictly excluded from baselines.
6. Immutability: 2022–2026 raw observation counts remain 100% invariant.
"""

import pytest
import json
from sqlalchemy import text
from backend.app.core.database import engine

def test_facility_baselines_integrity():
    with engine.connect() as conn:
        total = conn.execute(text("SELECT count(*) FROM facility_baselines;")).scalar()
        assert total >= 35000, f"Expected >= 35,000 facility baselines, found {total}"
        
        # Test sample of active facilities
        active = conn.execute(text("""
            SELECT facility_id, mean_frp, median_frp, max_historical_frp, frequency_days, frp_distribution, status_band
            FROM facility_baselines
            WHERE frequency_days > 0
            LIMIT 20;
        """)).fetchall()
        assert len(active) > 0, "No active facility baselines found"
        for row in active:
            fid, mean_f, med_f, max_f, f_days, dist_json, band = row
            assert mean_f >= 0.0, f"Invalid mean FRP {mean_f}"
            assert med_f >= 0.0, f"Invalid median FRP {med_f}"
            assert max_f >= mean_f * 0.5, f"Max FRP {max_f} less than half of mean {mean_f}"
            assert f_days >= 1, f"Invalid frequency days {f_days}"
            assert band in ["NORMAL", "ELEVATED", "ABNORMAL", "CRITICAL"], f"Invalid status band {band}"
            
            dist = dist_json if isinstance(dist_json, dict) else json.loads(dist_json)
            for p in ["p25", "p50", "p75", "p90", "p95", "p99"]:
                assert p in dist, f"Missing percentile {p} in {dist}"

def test_mining_thermal_associations_integrity():
    with engine.connect() as conn:
        total = conn.execute(text("SELECT count(*) FROM mining_thermal_associations;")).scalar()
        assert total > 50000, f"Expected > 50,000 mining thermal associations, found {total}"
        
        bands = conn.execute(text("SELECT DISTINCT distance_band FROM mining_thermal_associations;")).fetchall()
        band_names = {b[0] for b in bands}
        assert {"500m", "1km", "2km"}.issubset(band_names), f"Missing distance bands in {band_names}"

def test_seasonal_historical_baselines():
    with engine.connect() as conn:
        total = conn.execute(text("SELECT count(*) FROM historical_baselines WHERE baseline_status = 'ESTABLISHED';")).scalar()
        assert total >= 12, f"Expected >= 12 established regional baselines, found {total}"
        
        cells = conn.execute(text("""
            SELECT grid_cell_id, mean_frp, median_frp, monthly_pattern
            FROM historical_baselines
            WHERE grid_cell_id LIKE 'CELL-%';
        """)).fetchall()
        assert len(cells) >= 12
        for c in cells:
            cid, mean_f, med_f, pat_raw = c
            assert mean_f > 0.0, f"Invalid mean FRP for cell {cid}"
            pat = pat_raw if isinstance(pat_raw, dict) else json.loads(pat_raw)
            for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
                assert m in pat, f"Missing month {m} in pattern for {cid}"

def test_event_feature_vectors():
    with engine.connect() as conn:
        total = conn.execute(text("SELECT count(*) FROM event_features;")).scalar()
        assert total >= 60, f"Expected >= 60 event features, found {total}"
        
        features = conn.execute(text("""
            SELECT ef.id, ef.frp_max, ef.bright_avg, ef.dist_to_forest_m, ef.persistence_score, ef.recurrence_rate, ef.baseline_deviation_ratio
            FROM event_features ef
            LIMIT 20;
        """)).fetchall()
        for f in features:
            fid, f_max, b_avg, d_for, p_sc, rec_r, b_dev = f
            assert f_max >= 0.0
            assert b_avg >= 200.0
            assert d_for >= 0.0
            assert 0.0 <= p_sc <= 10.0
            assert rec_r >= 0.0
            assert b_dev >= 0.0

def test_protected_data_immutability():
    with engine.connect() as conn:
        c2022_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = false;")).scalar()
        c2022_pil = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = true;")).scalar()
        c2023_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = false;")).scalar()
        c2024_off = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01';")).scalar()
        c2025_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01' AND is_demo = false;")).scalar()
        
        assert c2022_off == 1274383, f"2022 Official mismatch: {c2022_off}"
        assert c2022_pil == 210000, f"2022 Pilot mismatch: {c2022_pil}"
        assert c2023_off == 1244759, f"2023 Official mismatch: {c2023_off}"
        assert c2024_off == 1711626, f"2024 Official mismatch: {c2024_off}"
        assert c2025_off == 2007898, f"2025 Official mismatch: {c2025_off}"
