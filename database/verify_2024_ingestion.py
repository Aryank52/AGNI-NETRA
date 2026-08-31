"""
AGNI-NETRA — Live PostgreSQL & PostGIS Verification for 2024 Historical Data Ingestion
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(line_buffering=True)
from sqlalchemy import text
from backend.app.core.database import engine

print("=" * 85)
print("  AGNI-NETRA — PHASE 5D POST-INGESTION POSTGRESQL & POSTGIS AUDIT")
print("=" * 85)

with engine.connect() as conn:
    # 1. Overall counts & immutability
    td_total = conn.execute(text("SELECT COUNT(*) FROM thermal_detections;")).scalar()
    th_total = conn.execute(text("SELECT COUNT(*) FROM thermal_history;")).scalar()
    det_2026 = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;")).scalar()
    det_2022_real = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = false;")).scalar()
    det_2022_pilot = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = true;")).scalar()
    det_2023_real = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023 AND is_demo = false;")).scalar()
    det_2024_real = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = false;")).scalar()
    hist_2024_real = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = false;")).scalar()
    det_2025 = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025;")).scalar()

    print("\n1. DATABASE RECORD TOTALS & BASELINE INTEGRITY:")
    print(f"  thermal_detections Total : {td_total:,}")
    print(f"  thermal_history Total    : {th_total:,}")
    print(f"  2026 Detections (Locked) : {det_2026:,} (Expected: 1,771,110, DELTA: {det_2026 - 1771110})")
    print(f"  2023 Official (Protected): {det_2023_real:,} (Expected: 1,244,759, DELTA: {det_2023_real - 1244759})")
    print(f"  2022 Official (Locked)   : {det_2022_real:,} (Expected: 1,274,383, DELTA: {det_2022_real - 1274383})")
    print(f"  2022 Pilot (Isolated)    : {det_2022_pilot:,} (Expected: 210,000, DELTA: {det_2022_pilot - 210000})")
    print(f"  2024 Official Detections : {det_2024_real:,} (is_demo=False)")
    print(f"  2024 Official History    : {hist_2024_real:,} (is_demo=False)")
    print(f"  2025 Detections          : {det_2025:,} (Expected: 0)")

    # 2. PostGIS Geometry Validation
    geom_stats = conn.execute(text("""
        SELECT 
            COUNT(*) AS total_2024,
            COUNT(latitude) AS non_null_lat,
            COUNT(longitude) AS non_null_lon,
            COUNT(acq_timestamp) AS non_null_ts,
            SUM(CASE WHEN ST_IsValid(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)) THEN 1 ELSE 0 END) AS valid_geom,
            SUM(CASE WHEN ST_SRID(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)) = 4326 THEN 1 ELSE 0 END) AS srid_4326,
            MIN(latitude) AS min_lat,
            MAX(latitude) AS max_lat,
            MIN(longitude) AS min_lon,
            MAX(longitude) AS max_lon
        FROM thermal_detections
        WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = false;
    """)).mappings().first()

    print("\n2. POSTGIS GEOMETRY & SPATIAL VALIDITY (2024 DATA):")
    print(f"  Total 2024 Rows : {geom_stats['total_2024']:,}")
    print(f"  Non-Null Lat/Lon: {geom_stats['non_null_lat']:,} / {geom_stats['total_2024']:,} ({geom_stats['non_null_lat']/geom_stats['total_2024']*100:.1f}%)")
    print(f"  Valid Geom      : {geom_stats['valid_geom']:,} ({geom_stats['valid_geom']/geom_stats['total_2024']*100:.1f}%)")
    print(f"  SRID = 4326     : {geom_stats['srid_4326']:,} ({geom_stats['srid_4326']/geom_stats['total_2024']*100:.1f}%)")
    print(f"  Lat Range       : [{geom_stats['min_lat']:.4f} .. {geom_stats['max_lat']:.4f}]")
    print(f"  Lon Range       : [{geom_stats['min_lon']:.4f} .. {geom_stats['max_lon']:.4f}]")

    # 3. Monthly distribution
    monthly_rows = conn.execute(text("""
        SELECT 
            TO_CHAR(acq_timestamp, 'YYYY-MM') AS month,
            COUNT(*) AS cnt,
            ROUND(AVG(frp)::numeric, 2) AS avg_frp,
            ROUND(MAX(frp)::numeric, 2) AS max_frp
        FROM thermal_detections
        WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = false
        GROUP BY TO_CHAR(acq_timestamp, 'YYYY-MM')
        ORDER BY month;
    """)).fetchall()

    print("\n3. 2024 TEMPORAL MONTHLY DISTRIBUTION:")
    for r in monthly_rows:
        print(f"  {r[0]}: {r[1]:,} detections | avg FRP: {r[2]} MW | max FRP: {r[3]} MW")

    # 4. Satellite distribution
    sat_rows = conn.execute(text("""
        SELECT satellite, sensor, COUNT(*) AS cnt
        FROM thermal_detections
        WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = false
        GROUP BY satellite, sensor
        ORDER BY cnt DESC;
    """)).fetchall()

    print("\n4. 2024 SATELLITE & SENSOR DISTRIBUTION:")
    for r in sat_rows:
        print(f"  {r[0]} ({r[1]}): {r[2]:,} detections")

    # 5. Top 10 States
    state_rows = conn.execute(text("""
        SELECT state, COUNT(*) AS cnt
        FROM thermal_history
        WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = false
        GROUP BY state
        ORDER BY cnt DESC
        LIMIT 10;
    """)).fetchall()

    print("\n5. 2024 TOP 10 STATES BY OBSERVATIONS:")
    for r in state_rows:
        print(f"  {r[0] or 'UNASSIGNED'}: {r[1]:,} observations")

    # 6. Top 10 Districts
    dist_rows = conn.execute(text("""
        SELECT district, state, COUNT(*) AS cnt
        FROM thermal_history
        WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = false
        GROUP BY district, state
        ORDER BY cnt DESC
        LIMIT 10;
    """)).fetchall()

    print("\n6. 2024 TOP 10 DISTRICTS BY OBSERVATIONS:")
    for r in dist_rows:
        print(f"  {r[0] or 'UNASSIGNED'} ({r[1] or 'National'}): {r[2]:,} observations")

print("=" * 85)
