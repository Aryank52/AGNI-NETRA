"""
AGNI-NETRA — Complete Verification of 2024 Reconciliation
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(line_buffering=True)
from sqlalchemy import text
from backend.app.core.database import engine

print("=" * 85)
print("  AGNI-NETRA — 2024 RECONCILIATION EXACT DATABASE PROOF")
print("=" * 85)

with engine.connect() as conn:
    # 1. Total records with reference_year = 2024
    ref_2024 = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE raw_metadata->>'reference_year' = '2024';")).scalar()
    print(f"1. thermal_history rows with reference_year='2024': {ref_2024:,}")
    
    # 2. Total records with acq_date between 2024-01-01 and 2024-12-31
    date_2024 = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE acq_date BETWEEN '2024-01-01' AND '2024-12-31';")).scalar()
    print(f"2. thermal_history rows with acq_date in 2024 calendar year: {date_2024:,}")
    
    # 3. Monthly distribution by acq_date (Calendar Month)
    monthly_acq = conn.execute(text("""
        SELECT SUBSTRING(acq_date, 1, 7) AS month, COUNT(*) AS cnt, ROUND(AVG(frp)::numeric, 2) AS avg_frp, ROUND(MAX(frp)::numeric, 2) AS max_frp
        FROM thermal_history
        WHERE raw_metadata->>'reference_year' = '2024'
        GROUP BY SUBSTRING(acq_date, 1, 7)
        ORDER BY month;
    """)).fetchall()
    
    print("\n3. 2024 MONTHLY BREAKDOWN BY ACQUISITION DATE (CALENDAR YEAR 2024):")
    tot_monthly = 0
    for r in monthly_acq:
        tot_monthly += r[1]
        print(f"  {r[0]}: {r[1]:,} records | avg FRP: {r[2]} MW | max FRP: {r[3]} MW")
    print(f"  Sum of all 12 calendar months: {tot_monthly:,}")
    
    # 4. Satellite breakdown for 2024 archive
    sat_breakdown = conn.execute(text("""
        SELECT satellite, sensor, COUNT(*) AS cnt
        FROM thermal_history
        WHERE raw_metadata->>'reference_year' = '2024'
        GROUP BY satellite, sensor
        ORDER BY cnt DESC;
    """)).fetchall()
    
    print("\n4. 2024 SATELLITE & SENSOR BREAKDOWN:")
    for r in sat_breakdown:
        print(f"  {r[0]} ({r[1]}): {r[2]:,} records")
        
    # 5. Product breakdown for 2024 archive
    prod_breakdown = conn.execute(text("""
        SELECT raw_metadata->>'product' AS prod, COUNT(*) AS cnt
        FROM thermal_history
        WHERE raw_metadata->>'reference_year' = '2024'
        GROUP BY raw_metadata->>'product'
        ORDER BY cnt DESC;
    """)).fetchall()
    
    print("\n5. 2024 PRODUCT BREAKDOWN:")
    for r in prod_breakdown:
        print(f"  {r[0]}: {r[1]:,} records")

    # 6. Check protected baselines
    det_2026 = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;")).scalar()
    det_2023 = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023 AND is_demo = false;")).scalar()
    det_2022 = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = false;")).scalar()
    det_2022_pilot = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = true;")).scalar()
    
    print("\n6. PROTECTED DATASET IMMUTABILITY:")
    print(f"  2026 Locked Baseline : {det_2026:,} (Expected: 1,771,110, DELTA: {det_2026 - 1771110})")
    print(f"  2023 Locked Baseline : {det_2023:,} (Expected: 1,244,759, DELTA: {det_2023 - 1244759})")
    print(f"  2022 Official Locked : {det_2022:,} (Expected: 1,274,383, DELTA: {det_2022 - 1274383})")
    print(f"  2022 Pilot Isolated  : {det_2022_pilot:,} (Expected: 210,000, DELTA: {det_2022_pilot - 210000})")

print("=" * 85)
