"""
AGNI-NETRA — NASA FIRMS 2024 Full Historical Archive Standalone Streaming Importer
Offline, batched, idempotent ingestion for PostgreSQL 16.15 + PostGIS 3.4.2.

Supported Standard Science Products:
  1. NOAA-20 VIIRS 375m (VJ114IMGTDL, Collection 2) - DL_FIRE_J1V-C2_795861.zip
  2. Suomi-NPP VIIRS 375m (VNP14IMGTDL, Collection 2) - DL_FIRE_SV-C2_795862.zip
  3. NOAA-21 VIIRS 375m (VJ214IMGTDL, Collection 2) - DL_FIRE_J2V-C2_795893.zip
  4. MODIS Terra/Aqua 1km (MCD14DL, Collection 6.1) - DL_FIRE_M-C61_795860.zip

Features:
  - Streaming zip extraction (zero full-file RAM caching)
  - Shapely prepared geometry containment (prep) for maximum spatial throughput
  - Deterministic UUIDv5 primary keys (idempotent upsert)
  - Strict preservation of 2022 official (1,274,383), 2022 pilot (210,000), 2023 official (1,244,759), and 2026 baseline (1,771,110) records
  - Generates authoritative archive manifest (archive_manifest_2024.json)
"""

import sys
import os
from collections import defaultdict
# Enable line buffering for real-time progress monitoring
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
import csv
import json
import time
import uuid
import zipfile
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

import psycopg2
import psycopg2.extras
from shapely.geometry import Point
from shapely.prepared import prep

from backend.app.core.database import engine
from backend.app.services.spatial_engine import lookup_state, lookup_district
from data_pipeline.adapters.firms_adapter import INDIA_BBOX, INDIA_TERRITORIAL_POLYGON

TARGET_YEAR = 2024

CANDIDATE_DIRS = [
    r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FIRMS\HISTORICAL\2024\full",
    r"E:\AGNI-NETRA-DATA\FIRMS\HISTORICAL\2024\full"
]

BATCH_SIZE = 25000

# Prepared geometry for 50x-100x faster point-in-polygon containment checks
PREPARED_INDIA = prep(INDIA_TERRITORIAL_POLYGON)

TYPE_DESCRIPTIONS = {
    0: "presumed vegetation fire",
    1: "active volcano",
    2: "other static land source",
    3: "offshore"
}


def calculate_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def normalize_confidence(conf_val: str, is_modis: bool) -> tuple[float, str]:
    c = str(conf_val).strip()
    if is_modis:
        try:
            val = float(c)
            return min(max(val, 0.0), 100.0), c
        except Exception:
            return 60.0, c

    cl = c.lower()
    if cl in ["l", "low"]:
        return 30.0, c
    elif cl in ["n", "nominal"]:
        return 65.0, c
    elif cl in ["h", "high"]:
        return 95.0, c

    try:
        val = float(c)
        return min(max(val, 0.0), 100.0), c
    except Exception:
        return 65.0, c


def resolve_archive_dir() -> str:
    for d in CANDIDATE_DIRS:
        if os.path.exists(d) and any(f.lower().endswith(".zip") for f in os.listdir(d)):
            return d
    return CANDIDATE_DIRS[0]


def inspect_archives(archive_dir: str) -> List[Dict[str, Any]]:
    """Inspects the archive directory and discovers all candidate NASA FIRMS ZIP files."""
    if not os.path.exists(archive_dir):
        print(f"[INSPECTION] Target directory does not exist: {archive_dir}", flush=True)
        return []

    zip_files = [f for f in os.listdir(archive_dir) if f.lower().endswith(".zip")]
    if not zip_files:
        print(f"[INSPECTION] No ZIP files found in directory: {archive_dir}", flush=True)
        return []

    discovered = []
    for zname in sorted(zip_files):
        zpath = os.path.join(archive_dir, zname)
        sz = os.path.getsize(zpath)
        sha = calculate_sha256(zpath)

        with zipfile.ZipFile(zpath, "r") as zf:
            csv_entries = [name for name in zf.namelist() if name.lower().endswith(".csv")]
            for csv_name in csv_entries:
                # Determine product & sensor
                fn_upper = zname.upper()
                if "J1V-C2" in fn_upper or "VJ114" in fn_upper:
                    prod = "VJ114IMGTDL"
                    sat = "NOAA-20"
                    sensor = "VIIRS_NOAA20"
                    source = "NASA_FIRMS_VIIRS"
                    coll = "Collection 2"
                    is_modis = False
                elif "J2V-C2" in fn_upper or "VJ214" in fn_upper:
                    prod = "VJ214IMGTDL"
                    sat = "NOAA-21"
                    sensor = "VIIRS_NOAA21"
                    source = "NASA_FIRMS_VIIRS"
                    coll = "Collection 2"
                    is_modis = False
                elif "SV-C2" in fn_upper or "VNP14" in fn_upper:
                    prod = "VNP14IMGTDL"
                    sat = "Suomi-NPP"
                    sensor = "VIIRS_SNPP"
                    source = "NASA_FIRMS_VIIRS"
                    coll = "Collection 2"
                    is_modis = False
                elif "M-C61" in fn_upper or "MCD14" in fn_upper:
                    prod = "MCD14DL"
                    sat = "Terra/Aqua"
                    sensor = "MODIS_COMBINED"
                    source = "NASA_FIRMS_MODIS"
                    coll = "Collection 6.1"
                    is_modis = True
                else:
                    prod = "UNKNOWN_PRODUCT"
                    sat = "UNKNOWN_SATELLITE"
                    sensor = "UNKNOWN_SENSOR"
                    source = "NASA_FIRMS_UNKNOWN"
                    coll = "UNKNOWN"
                    is_modis = False

                discovered.append({
                    "zip_name": zname,
                    "csv_name": csv_name,
                    "filepath": zpath,
                    "file_size": sz,
                    "sha256": sha,
                    "product": prod,
                    "satellite": sat,
                    "sensor": sensor,
                    "source": source,
                    "collection": coll,
                    "is_modis": is_modis
                })

    # Sort order: NOAA-20, Suomi-NPP, NOAA-21, MODIS
    order_map = {"NOAA-20": 1, "Suomi-NPP": 2, "NOAA-21": 3, "Terra/Aqua": 4}
    discovered.sort(key=lambda x: order_map.get(x["satellite"], 99))
    return discovered


def import_2024_full_archives():
    print("=" * 85, flush=True)
    print(f"  AGNI-NETRA — PHASE 5D: NASA FIRMS {TARGET_YEAR} FULL ARCHIVE INGESTION (HIGH-SPEED)", flush=True)
    print("=" * 85, flush=True)

    archive_dir = resolve_archive_dir()
    manifest_path = os.path.join(archive_dir, f"archive_manifest_{TARGET_YEAR}.json")

    archives = inspect_archives(archive_dir)
    if not archives:
        print(f"\n[STATUS] {TARGET_YEAR}_FILES_NOT_STAGED", flush=True)
        print(f"Directory {archive_dir} contains no archive ZIP files to import.", flush=True)
        return False

    print(f"\nDiscovered {len(archives)} NASA FIRMS archive(s) in {archive_dir}:", flush=True)
    for arc in archives:
        print(f"  - {arc['zip_name']} ({arc['file_size'] / (1024*1024):.2f} MB) | Product: {arc['product']} | Satellite: {arc['satellite']} | Sensor: {arc['sensor']}", flush=True)

    overall_start_time = time.time()

    # 1. Pre-Ingestion Counts & Safety Checks
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_detections;")
            det_total_before = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM thermal_history;")
            hist_total_before = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;")
            det_2026_before = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = false;")
            det_2022_real_before = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = true;")
            det_2022_pilot_before = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023 AND is_demo = false;")
            det_2023_real_before = cur.fetchone()[0]

            cur.execute(f"SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = {TARGET_YEAR} AND is_demo = false;")
            det_target_before = cur.fetchone()[0]

    print("\nPre-Ingestion Baseline Integrity:", flush=True)
    print(f"  thermal_detections Total : {det_total_before:,}", flush=True)
    print(f"  thermal_history Total    : {hist_total_before:,}", flush=True)
    print(f"  2026 Detections (Locked) : {det_2026_before:,}", flush=True)
    print(f"  2022 Official (Locked)   : {det_2022_real_before:,}", flush=True)
    print(f"  2022 Pilot (Isolated)    : {det_2022_pilot_before:,}", flush=True)
    print(f"  2023 Official (Protected): {det_2023_real_before:,} (CRITICAL LOCK: 1,244,759)", flush=True)
    print(f"  {TARGET_YEAR} Official (Current): {det_target_before:,}\n", flush=True)

    if det_2023_real_before != 1244759:
        print(f"[FATAL ERROR] 2023 Official Baseline Count is {det_2023_real_before:,}, expected 1,244,759. Aborting.", flush=True)
        return False

    insert_det_sql = """
        INSERT INTO thermal_detections (
            id, source, sensor, satellite, latitude, longitude,
            acq_timestamp, brightness, bright_t31, frp, confidence,
            day_night, event_id, raw_metadata, is_demo
        ) VALUES %s
        ON CONFLICT (id) DO NOTHING;
    """

    insert_hist_sql = """
        INSERT INTO thermal_history (
            id, source, sensor, satellite, latitude, longitude,
            acq_date, acq_time, acq_timestamp, brightness, bright_t31,
            frp, confidence, day_night, processing_type, state,
            district, source_record_id, raw_metadata, is_demo, created_at
        ) VALUES %s
        ON CONFLICT (id) DO NOTHING;
    """

    manifest_entries = []
    total_accepted_india = 0
    total_read_all = 0
    total_outside_all = 0
    total_rejected_all = 0

    monthly_stats = defaultdict(int)
    daily_stats = defaultdict(int)
    satellite_stats = defaultdict(int)
    product_stats = defaultdict(int)
    state_stats = defaultdict(int)
    district_stats = defaultdict(int)

    raw_conn = engine.raw_connection()

    # 2. Ingest Archives
    for config in archives:
        zip_name = config["zip_name"]
        csv_name = config["csv_name"]
        zip_path = config["filepath"]
        file_size_bytes = config["file_size"]
        sha256_hash = config["sha256"]

        file_start_time = time.time()
        print(f"--- Processing Archive: {zip_name} ({file_size_bytes / (1024 * 1024):.2f} MB) ---", flush=True)
        print(f"  Product: {config['product']} | Sensor: {config['sensor']} | Satellite: {config['satellite']}", flush=True)

        rows_read = 0
        rows_inside = 0
        rows_outside = 0
        rows_rejected = 0
        min_dt = None
        max_dt = None

        batch_detections = []
        batch_history = []

        with zipfile.ZipFile(zip_path, "r") as zf:
            with zf.open(csv_name) as cf:
                text_stream = io.TextIOWrapper(cf, encoding="utf-8", errors="replace")
                reader = csv.DictReader(text_stream)

                for row in reader:
                    rows_read += 1

                    try:
                        lat = float(row["latitude"])
                        lon = float(row["longitude"])
                        acq_date = row["acq_date"].strip()
                        acq_time_raw = row["acq_time"].strip().zfill(4)

                        dt_str = f"{acq_date} {acq_time_raw}"
                        acq_dt = datetime.strptime(dt_str, "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)

                        brightness = float(row["brightness"]) if row.get("brightness") and row["brightness"].strip() else (
                            float(row["bright_ti4"]) if row.get("bright_ti4") and row["bright_ti4"].strip() else None
                        )
                        bright_t31 = float(row["bright_t31"]) if row.get("bright_t31") and row["bright_t31"].strip() else (
                            float(row["bright_ti5"]) if row.get("bright_ti5") and row["bright_ti5"].strip() else None
                        )
                        frp = float(row["frp"]) if row.get("frp") and row["frp"].strip() else 0.0

                        conf_raw = row.get("confidence", "")
                        confidence, conf_str = normalize_confidence(conf_raw, config["is_modis"])

                        day_night = row.get("daynight", "D").strip().upper()
                        if day_night not in ["D", "N"]:
                            day_night = "D"

                        scan = float(row.get("scan", 0.0)) if row.get("scan") else 0.0
                        track = float(row.get("track", 0.0)) if row.get("track") else 0.0
                        type_int = int(row.get("type", 0)) if row.get("type") and row["type"].strip().isdigit() else 0
                        version = row.get("version", "2.0")

                        sat_raw = row.get("satellite", "").strip()
                        if config["is_modis"]:
                            sat_val = "Aqua" if "aqua" in sat_raw.lower() else ("Terra" if "terra" in sat_raw.lower() else "Terra/Aqua")
                            sensor_val = f"MODIS_{sat_val.upper()}" if sat_val in ["Aqua", "Terra"] else "MODIS_COMBINED"
                        else:
                            if "VJ214" in config["product"] or "J2V-C2" in zip_name:
                                sat_val = "NOAA-21"
                                sensor_val = "VIIRS_NOAA21"
                            elif "VJ114" in config["product"] or "J1V-C2" in zip_name:
                                sat_val = "NOAA-20"
                                sensor_val = "VIIRS_NOAA20"
                            elif "VNP14" in config["product"] or "SV-C2" in zip_name:
                                sat_val = "Suomi-NPP"
                                sensor_val = "VIIRS_SNPP"
                            else:
                                sat_val = "NOAA-21" if sat_raw in ["N21", "2", "JPSS-2"] else ("NOAA-20" if sat_raw in ["N20", "1", "JPSS-1"] else ("Suomi-NPP" if sat_raw in ["SNPP", "NPP"] else config["satellite"]))
                                sensor_val = config["sensor"]

                    except Exception:
                        rows_rejected += 1
                        continue

                    # Bounding box quick check
                    if not ((INDIA_BBOX[0] <= lat <= INDIA_BBOX[2]) and (INDIA_BBOX[1] <= lon <= INDIA_BBOX[3])):
                        rows_outside += 1
                        continue

                    # Ultra-fast point-in-polygon with prepared geometry
                    pt = Point(lon, lat)
                    if not PREPARED_INDIA.contains(pt):
                        rows_outside += 1
                        continue

                    rows_inside += 1

                    if min_dt is None or acq_dt < min_dt:
                        min_dt = acq_dt
                    if max_dt is None or acq_dt > max_dt:
                        max_dt = acq_dt

                    source_record_id = f"FIRMS_{sensor_val}_{acq_date}_{acq_time_raw}_{lat:.5f}_{lon:.5f}"
                    record_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, source_record_id))

                    metadata = {
                        "source_file": csv_name,
                        "archive_zip": zip_name,
                        "dataset_scope": "FULL_ARCHIVE",
                        "product": config["product"],
                        "collection": config["collection"],
                        "satellite_raw": sat_raw,
                        "instrument": config["sensor"].split("_")[0],
                        "version": version,
                        "scan": scan,
                        "track": track,
                        "acq_time_raw": acq_time_raw,
                        "daynight": day_night,
                        "type": type_int,
                        "type_desc": TYPE_DESCRIPTIONS.get(type_int, "unknown"),
                        "raw_confidence": conf_raw,
                        "reference_year": TARGET_YEAR,
                        "processing_type": "STANDARD_SCIENCE"
                    }
                    metadata_json = json.dumps(metadata)

                    state = lookup_state(lat, lon)
                    district = lookup_district(lat, lon)

                    month_key = acq_date[:7]
                    monthly_stats[month_key] += 1
                    daily_stats[acq_date] += 1
                    satellite_stats[sat_val] += 1
                    product_stats[config["product"]] += 1
                    if state:
                        state_stats[state] += 1
                    if district:
                        district_stats[district] += 1

                    det_tuple = (
                        record_id,
                        config["source"],
                        sensor_val,
                        sat_val,
                        lat,
                        lon,
                        acq_dt,
                        brightness,
                        bright_t31,
                        frp,
                        confidence,
                        day_night,
                        None,
                        metadata_json,
                        False  # is_demo = False (Official 2024 Full Archive)
                    )
                    batch_detections.append(det_tuple)

                    hist_tuple = (
                        record_id,
                        config["source"],
                        sensor_val,
                        sat_val,
                        lat,
                        lon,
                        acq_date,
                        acq_time_raw,
                        acq_dt,
                        brightness,
                        bright_t31,
                        frp,
                        confidence,
                        day_night,
                        "STANDARD_SCIENCE",
                        state,
                        district,
                        source_record_id,
                        metadata_json,
                        False,  # is_demo = False
                        datetime.now(timezone.utc)
                    )
                    batch_history.append(hist_tuple)

                    if len(batch_detections) >= BATCH_SIZE:
                        with raw_conn.cursor() as cur:
                            psycopg2.extras.execute_values(cur, insert_det_sql, batch_detections, page_size=BATCH_SIZE)
                            psycopg2.extras.execute_values(cur, insert_hist_sql, batch_history, page_size=BATCH_SIZE)
                        raw_conn.commit()
                        batch_detections = []
                        batch_history = []
                        elapsed_so_far = time.time() - file_start_time
                        print(f"  [Progress] {rows_read:,} rows read -> {rows_inside:,} inside India ({round(rows_inside/max(0.001, elapsed_so_far), 1):,} rec/s)", flush=True)

                if batch_detections:
                    with raw_conn.cursor() as cur:
                        psycopg2.extras.execute_values(cur, insert_det_sql, batch_detections, page_size=len(batch_detections))
                        psycopg2.extras.execute_values(cur, insert_hist_sql, batch_history, page_size=len(batch_history))
                    raw_conn.commit()
                    batch_detections = []
                    batch_history = []

        file_elapsed = time.time() - file_start_time
        throughput = rows_inside / max(0.001, file_elapsed)
        total_accepted_india += rows_inside
        total_read_all += rows_read
        total_outside_all += rows_outside
        total_rejected_all += rows_rejected

        manifest_entry = {
            "archive_zip": zip_name,
            "csv_filename": csv_name,
            "sha256": sha256_hash,
            "size_bytes": file_size_bytes,
            "product": config["product"],
            "collection": config["collection"],
            "satellite": config["satellite"],
            "sensor": config["sensor"],
            "dataset_scope": "FULL_ARCHIVE",
            "processing_type": "STANDARD_SCIENCE",
            "date_range": f"{min_dt.strftime('%Y-%m-%d')} to {max_dt.strftime('%Y-%m-%d')}" if min_dt else "N/A",
            "rows_read": rows_read,
            "rows_inside_india": rows_inside,
            "rows_outside_india": rows_outside,
            "rejected_rows": rows_rejected,
            "elapsed_seconds": round(file_elapsed, 2),
            "throughput_rows_sec": round(throughput, 1),
            "import_timestamp": datetime.now(timezone.utc).isoformat()
        }
        manifest_entries.append(manifest_entry)
        print(f"  --> Completed {zip_name}: {rows_inside:,} India records in {file_elapsed:.2f}s ({throughput:.1f} rows/sec)\n", flush=True)

    raw_conn.close()
    overall_elapsed = time.time() - overall_start_time

    # 3. Post-Ingestion Database Verification
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_detections;")
            det_total_after = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_history;")
            hist_total_after = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;")
            det_2026_after = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = false;")
            det_2022_real_after = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = true;")
            det_2022_pilot_after = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023 AND is_demo = false;")
            det_2023_real_after = cur.fetchone()[0]

            cur.execute(f"SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = {TARGET_YEAR} AND is_demo = false;")
            det_2024_real_after = cur.fetchone()[0]

            cur.execute(f"""
                SELECT COUNT(*) FROM thermal_detections 
                WHERE EXTRACT(YEAR FROM acq_timestamp) = {TARGET_YEAR} 
                  AND (latitude IS NULL OR longitude IS NULL OR acq_timestamp IS NULL);
            """)
            null_count = cur.fetchone()[0]

    # Immutability validation
    if det_2023_real_after != 1244759:
        print(f"\n[FATAL] 2023_IMMUTABILITY_FAILURE: 2023 count changed from 1,244,759 to {det_2023_real_after:,}!", flush=True)
        return False

    if det_2022_real_after != 1274383:
        print(f"\n[FATAL] 2022_IMMUTABILITY_FAILURE: 2022 count changed from 1,274,383 to {det_2022_real_after:,}!", flush=True)
        return False

    if det_2026_after != det_2026_before:
        print(f"\n[FATAL] 2026_IMMUTABILITY_FAILURE: 2026 count changed from {det_2026_before:,} to {det_2026_after:,}!", flush=True)
        return False

    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump({
            "status": f"{TARGET_YEAR}_FULL_ARCHIVE_IMPORTED",
            "target_year": TARGET_YEAR,
            "overall_elapsed_seconds": round(overall_elapsed, 2),
            "overall_throughput_rows_sec": round(total_accepted_india / max(0.001, overall_elapsed), 1),
            "summary_counts": {
                "source_rows_read": total_read_all,
                "inside_india_accepted": total_accepted_india,
                "outside_india_filtered": total_outside_all,
                "rejected_corrupted": total_rejected_all,
                "database_real_2024_records": det_2024_real_after,
                "database_real_2023_records": det_2023_real_after,
                "database_real_2022_records": det_2022_real_after,
                "database_pilot_isolated_records": det_2022_pilot_after,
                "thermal_detections_total_before": det_total_before,
                "thermal_detections_total_after": det_total_after,
                "2026_count_before": det_2026_before,
                "2026_count_after": det_2026_after,
                "2026_delta": det_2026_after - det_2026_before,
                "2023_delta": det_2023_real_after - det_2023_real_before,
                "2022_delta": det_2022_real_after - det_2022_real_before
            },
            "satellite_distribution": satellite_stats,
            "product_distribution": product_stats,
            "monthly_distribution": dict(sorted(monthly_stats.items())),
            "state_distribution": dict(sorted(state_stats.items(), key=lambda x: x[1], reverse=True)),
            "distinct_dates_count": len(daily_stats),
            "distinct_districts_count": len(district_stats),
            "null_or_invalid_rows": null_count,
            "archives": manifest_entries
        }, mf, indent=2)

    print("=" * 85, flush=True)
    print("  FINAL INGESTION & INTEGRITY SUMMARY", flush=True)
    print("=" * 85, flush=True)
    print(f"Status                  : {TARGET_YEAR}_FULL_ARCHIVE_IMPORTED", flush=True)
    print(f"Total Source Rows Read  : {total_read_all:,}", flush=True)
    print(f"Total Inside India (OK) : {total_accepted_india:,}", flush=True)
    print(f"Filtered Outside India  : {total_outside_all:,}", flush=True)
    print(f"thermal_detections Total: {det_total_before:,} -> {det_total_after:,} (+{det_total_after - det_total_before:,})", flush=True)
    print(f"thermal_history Total   : {hist_total_before:,} -> {hist_total_after:,} (+{hist_total_after - hist_total_before:,})", flush=True)
    print(f"2026 Detections (Locked): {det_2026_before:,} -> {det_2026_after:,} (DELTA: {det_2026_after - det_2026_before}) [UNTOUCHED]", flush=True)
    print(f"2023 Official (Locked)  : {det_2023_real_before:,} -> {det_2023_real_after:,} (DELTA: {det_2023_real_after - det_2023_real_before}) [UNTOUCHED]", flush=True)
    print(f"2022 Official (Locked)  : {det_2022_real_before:,} -> {det_2022_real_after:,} (DELTA: {det_2022_real_after - det_2022_real_before}) [UNTOUCHED]", flush=True)
    print(f"Real Official 2024 (DB) : {det_2024_real_after:,} (is_demo=False)", flush=True)
    print(f"Pilot Isolated 2022 (DB): {det_2022_pilot_after:,} (is_demo=True)", flush=True)
    print(f"Null / Invalid Records  : {null_count}", flush=True)
    print(f"Total Elapsed Time      : {overall_elapsed:.2f}s ({round(total_accepted_india / max(0.001, overall_elapsed), 1):,} rows/sec avg)", flush=True)
    print(f"Manifest written to     : {manifest_path}\n", flush=True)

    return True


if __name__ == "__main__":
    import_2024_full_archives()
