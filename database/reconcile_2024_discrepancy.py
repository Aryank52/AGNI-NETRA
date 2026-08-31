"""
AGNI-NETRA — PHASE 5D-R: 2024 NASA FIRMS Reconciliation & Discrepancy Analysis
"""

import sys
import os
import io
import zipfile
import csv
import uuid
import hashlib
from datetime import datetime
from shapely.geometry import Point
from shapely.prepared import prep
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(line_buffering=True)
from sqlalchemy import text
from backend.app.core.database import engine
from data_pipeline.adapters.firms_adapter import INDIA_BBOX, INDIA_TERRITORIAL_POLYGON

print("=" * 85)
print("  AGNI-NETRA — PHASE 5D-R: 2024 NASA FIRMS DISCREPANCY RECONCILIATION")
print("=" * 85)

ARCHIVE_DIR = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FIRMS\HISTORICAL\2024\full"
PREPARED_INDIA = prep(INDIA_TERRITORIAL_POLYGON)
min_lat, min_lon, max_lat, max_lon = INDIA_BBOX

ARCHIVES = [
    {"zip": "DL_FIRE_J1V-C2_795861.zip", "sat": "NOAA-20", "sensor": "VIIRS_NOAA20", "product": "VJ114IMGTDL"},
    {"zip": "DL_FIRE_SV-C2_795862.zip", "sat": "Suomi-NPP", "sensor": "VIIRS_SNPP", "product": "VNP14IMGTDL"},
    {"zip": "DL_FIRE_J2V-C2_795893.zip", "sat": "NOAA-21", "sensor": "VIIRS_NOAA21", "product": "VJ214IMGTDL"},
    {"zip": "DL_FIRE_M-C61_795860.zip", "sat": "Terra/Aqua", "sensor": "MODIS_COMBINED", "product": "MCD14DL"},
]

# Step 1: Process archives and gather source record IDs
total_source_rows = 0
accepted_inside_india = 0
outside_india = 0

source_id_counts = {}  # source_record_id -> count
source_id_to_record = {}  # source_record_id -> sample row data
archive_details = {}

for arc in ARCHIVES:
    zip_path = os.path.join(ARCHIVE_DIR, arc["zip"])
    print(f"\nInspecting Archive: {arc['zip']} ({arc['sat']})")
    
    # Calculate SHA256
    with open(zip_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    print(f"  SHA-256: {sha}")
    
    with zipfile.ZipFile(zip_path, "r") as z:
        for fname in z.namelist():
            if not fname.endswith(".csv"):
                continue
            with z.open(fname) as f_csv:
                reader = csv.DictReader(io.TextIOWrapper(f_csv, encoding="utf-8"))
                arc_rows = 0
                arc_accepted = 0
                arc_dups = 0
                for row in reader:
                    arc_rows += 1
                    total_source_rows += 1
                    try:
                        lat = float(row["latitude"])
                        lon = float(row["longitude"])
                    except Exception:
                        continue
                    
                    if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
                        outside_india += 1
                        continue
                    if not PREPARED_INDIA.contains(Point(lon, lat)):
                        outside_india += 1
                        continue
                    
                    accepted_inside_india += 1
                    arc_accepted += 1
                    
                    # Specific satellite mapping
                    sat = arc["sat"]
                    sensor = arc["sensor"]
                    if arc["product"] == "MCD14DL":
                        sat_code = row.get("satellite", "").strip().upper()
                        sat = "Terra" if sat_code == "T" else ("Aqua" if sat_code == "A" else "Terra/Aqua")
                        sensor = "MODIS_TERRA" if sat_code == "T" else ("MODIS_AQUA" if sat_code == "A" else "MODIS_COMBINED")
                    
                    acq_time = row["acq_time"].strip().zfill(4)
                    source_record_id = f"FIRMS_{sat}_{sensor}_{row['acq_date']}_{acq_time}_{row['latitude']}_{row['longitude']}"
                    rec_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, source_record_id))
                    
                    if source_record_id in source_id_counts:
                        source_id_counts[source_record_id] += 1
                        arc_dups += 1
                    else:
                        source_id_counts[source_record_id] = 1
                        source_id_to_record[source_record_id] = {
                            "uuid": rec_id,
                            "sat": sat,
                            "sensor": sensor,
                            "acq_date": row["acq_date"],
                            "acq_time": acq_time,
                            "lat": lat,
                            "lon": lon,
                            "product": arc["product"]
                        }
                print(f"  Rows read: {arc_rows:,} | Inside India: {arc_accepted:,} | Duplicates in source: {arc_dups:,}")
                archive_details[arc["zip"]] = {
                    "rows": arc_rows,
                    "accepted": arc_accepted,
                    "duplicates": arc_dups,
                    "sha256": sha
                }

unique_accepted_source_ids = len(source_id_counts)
duplicate_source_records = accepted_inside_india - unique_accepted_source_ids

print("\n" + "=" * 85)
print("SOURCE LEVEL RECONCILIATION TOTALS:")
print(f"  Total Source Rows Read      : {total_source_rows:,}")
print(f"  Total Rows Inside India     : {accepted_inside_india:,}")
print(f"  Total Rows Outside India    : {outside_india:,}")
print(f"  Unique Source Record IDs    : {unique_accepted_source_ids:,}")
print(f"  Duplicate Source Records    : {duplicate_source_records:,}")

# Step 2: Compare against live PostgreSQL database
print("\n" + "=" * 85)
print("QUERYING DATABASE FOR 2024 RECORDS...")

with engine.connect() as conn:
    # Get all 2024 detection IDs from DB
    db_2024_rows = conn.execute(text("""
        SELECT id::text, source_record_id 
        FROM thermal_history 
        WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024;
    """)).fetchall()
    
    db_det_count = conn.execute(text("""
        SELECT COUNT(*) 
        FROM thermal_detections 
        WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = false;
    """)).scalar()

db_history_ids = {r[0] for r in db_2024_rows}
db_source_ids = {r[1] for r in db_2024_rows if r[1]}

print(f"  Database 2024 thermal_detections (real): {db_det_count:,}")
print(f"  Database 2024 thermal_history rows     : {len(db_2024_rows):,}")

# Step 3: Detailed set analysis
source_uuids = {v["uuid"]: k for k, v in source_id_to_record.items()}

already_in_db = 0
missing_from_db = []

for u, s_id in source_uuids.items():
    if u in db_history_ids or s_id in db_source_ids:
        already_in_db += 1
    else:
        missing_from_db.append(s_id)

db_not_in_source = 0
for u in db_history_ids:
    if u not in source_uuids:
        db_not_in_source += 1

print("\n" + "=" * 85)
print("EXACT DISCREPANCY CLASSIFICATION:")
print(f"  Accepted Inside India (Total Streamed) : {accepted_inside_india:,}")
print(f"  Unique Source Records                  : {unique_accepted_source_ids:,}")
print(f"  Exact Source Duplicate Rows (DUPLICATE): {duplicate_source_records:,}")
print(f"  Source Records Already in DB           : {already_in_db:,}")
print(f"  Source Records Missing from DB         : {len(missing_from_db):,}")
print(f"  DB Records Not in Current Source       : {db_not_in_source:,}")
print(f"  Current DB 2024 Detection Count        : {db_det_count:,}")
print(f"  Difference (Accepted - DB Detections)  : {accepted_inside_india - db_det_count:,}")

# Let's inspect duplicates in detail
if duplicate_source_records > 0:
    print(f"\nDUPLICATE BREAKDOWN ({duplicate_source_records} records):")
    dup_samples = [k for k, v in source_id_counts.items() if v > 1]
    print(f"  Total distinct keys with >1 occurrence: {len(dup_samples)}")
    for s_id in dup_samples[:10]:
        print(f"  - Count: {source_id_counts[s_id]}x | ID: {s_id}")

# Let's check missing records in detail
if missing_from_db:
    print(f"\nMISSING FROM DATABASE BREAKDOWN ({len(missing_from_db)} records):")
    for s_id in missing_from_db[:10]:
        print(f"  - Missing: {s_id} | Data: {source_id_to_record[s_id]}")

print("=" * 85)
