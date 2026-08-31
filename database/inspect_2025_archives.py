"""
AGNI-NETRA — PHASE 5E: Inspect and Audit 2025 NASA FIRMS Standard Science Archives
"""

import sys
import os
import io
import zipfile
import csv
import hashlib
from datetime import datetime
from collections import defaultdict
from shapely.geometry import Point
from shapely.prepared import prep

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(line_buffering=True)
from sqlalchemy import text
from backend.app.core.database import engine
from data_pipeline.adapters.firms_adapter import INDIA_BBOX, INDIA_TERRITORIAL_POLYGON

print("=" * 85)
print("  AGNI-NETRA — PHASE 5E: INSPECT & AUDIT 2025 NASA FIRMS ARCHIVES")
print("=" * 85)

ARCHIVE_DIR = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FIRMS\HISTORICAL\2025\full"
PREPARED_INDIA = prep(INDIA_TERRITORIAL_POLYGON)

if not os.path.exists(ARCHIVE_DIR):
    print(f"ERROR: Directory does not exist: {ARCHIVE_DIR}")
    sys.exit(1)

files = os.listdir(ARCHIVE_DIR)
print(f"Files found in {ARCHIVE_DIR}:")
for f in files:
    print(f"  - {f}")

zip_files = [f for f in files if f.endswith(".zip") or not os.path.splitext(f)[1]]
print(f"\nProcessing {len(zip_files)} candidate archive files...")

archive_results = []
total_read_all = 0
total_inside_all = 0
total_outside_all = 0
total_rejected_all = 0
monthly_stats = defaultdict(int)
daily_stats = defaultdict(int)
satellite_stats = defaultdict(int)

for fname in sorted(files):
    fpath = os.path.join(ARCHIVE_DIR, fname)
    if os.path.isdir(fpath) or fname.endswith(".json"):
        continue
    
    file_size = os.path.getsize(fpath)
    print(f"\n--- Archive: {fname} ({file_size / (1024*1024):.2f} MB) ---")
    
    # Calculate SHA-256
    with open(fpath, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    print(f"  SHA-256: {sha256}")
    
    # Check ZIP integrity
    try:
        zf = zipfile.ZipFile(fpath, "r")
        bad_file = zf.testzip()
        if bad_file:
            print(f"  ZIP Integrity: FAILED (corrupt member {bad_file})")
            continue
        else:
            print(f"  ZIP Integrity: PASSED (CRC-32 Valid)")
    except Exception as e:
        print(f"  ZIP Open Error: {e}")
        continue
    
    namelist = zf.namelist()
    csv_names = [n for n in namelist if n.endswith(".csv")]
    if not csv_names:
        print(f"  ERROR: No CSV file inside ZIP!")
        continue
    
    csv_name = csv_names[0]
    print(f"  Internal CSV: {csv_name}")
    
    rows_read = 0
    rows_inside = 0
    rows_outside = 0
    rows_rejected = 0
    min_date = None
    max_date = None
    dates_set = set()
    headers = []
    
    with zf.open(csv_name) as cf:
        text_stream = io.TextIOWrapper(cf, encoding="utf-8", errors="replace")
        reader = csv.DictReader(text_stream)
        headers = reader.fieldnames
        
        for row in reader:
            rows_read += 1
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                acq_date = row["acq_date"].strip()
                acq_time = row["acq_time"].strip().zfill(4)
                sat_raw = row.get("satellite", "").strip()
            except Exception:
                rows_rejected += 1
                continue
            
            dates_set.add(acq_date)
            if min_date is None or acq_date < min_date:
                min_date = acq_date
            if max_date is None or acq_date > max_date:
                max_date = acq_date
            
            # Point in polygon
            if not ((INDIA_BBOX[0] <= lat <= INDIA_BBOX[2]) and (INDIA_BBOX[1] <= lon <= INDIA_BBOX[3])):
                rows_outside += 1
                continue
            if not PREPARED_INDIA.contains(Point(lon, lat)):
                rows_outside += 1
                continue
            
            rows_inside += 1
            monthly_stats[acq_date[:7]] += 1
            daily_stats[acq_date] += 1
            satellite_stats[sat_raw] += 1
    
    print(f"  Headers: {headers}")
    print(f"  Rows Read: {rows_read:,} | Inside India: {rows_inside:,} | Outside: {rows_outside:,} | Rejected: {rows_rejected:,}")
    print(f"  Date Range: {min_date} -> {max_date} ({len(dates_set)} distinct dates)")
    
    total_read_all += rows_read
    total_inside_all += rows_inside
    total_outside_all += rows_outside
    total_rejected_all += rows_rejected

print("\n" + "=" * 85)
print("AGGREGATE 2025 INSPECTION SUMMARY:")
print(f"  Total Source Rows Read        : {total_read_all:,}")
print(f"  Total Inside India Accepted   : {total_inside_all:,}")
print(f"  Total Outside India Filtered  : {total_outside_all:,}")
print(f"  Total Corrupted/Rejected Rows : {total_rejected_all:,}")

print("\n2025 Monthly Coverage (Inside India):")
for m in sorted(monthly_stats.keys()):
    print(f"  {m}: {monthly_stats[m]:,} records")

# Live Database Baseline
print("\n" + "=" * 85)
print("CAPTURING LIVE DATABASE BASELINE (PRE-INGESTION)...")

with engine.connect() as conn:
    tot_det = conn.execute(text("SELECT COUNT(*) FROM thermal_detections;")).scalar()
    tot_hist = conn.execute(text("SELECT COUNT(*) FROM thermal_history;")).scalar()
    
    det_2022_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = false;")).scalar()
    det_2022_pil = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = true;")).scalar()
    det_2023_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023 AND is_demo = false;")).scalar()
    det_2024_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = false;")).scalar()
    det_2025_raw = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025;")).scalar()
    det_2026_raw = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;")).scalar()
    
    hist_2022_off = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = false;")).scalar()
    hist_2022_pil = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = true;")).scalar()
    hist_2023_off = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023 AND is_demo = false;")).scalar()
    hist_2024_off = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE raw_metadata->>'reference_year' = '2024';")).scalar()
    hist_2025_raw = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025;")).scalar()
    hist_2026_raw = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;")).scalar()

print(f"  thermal_detections Total : {tot_det:,}")
print(f"  thermal_history Total    : {tot_hist:,}")
print(f"  2022 Official (Locked)   : {det_2022_off:,} (Expected: 1,274,383)")
print(f"  2022 Pilot (Isolated)    : {det_2022_pil:,} (Expected: 210,000)")
print(f"  2023 Official (Locked)   : {det_2023_off:,} (Expected: 1,244,759)")
print(f"  2024 Reconciled (Locked) : {hist_2024_off:,} in thermal_history (ref_year 2024), {det_2024_off:,} session detections")
print(f"  2025 Current in DB       : {det_2025_raw:,} detections (1,476 from 2024 late-night IST rollover)")
print(f"  2026 Baseline (Locked)   : {det_2026_raw:,} (Expected: 1,771,110)")
print("=" * 85)
