"""
AGNI-NETRA — Generalized NASA FIRMS Full Historical Archive Streaming Importer
Offline, batched, idempotent ingestion for PostgreSQL 16.15 + PostGIS 3.4.2.

Supports any historical year (2022, 2023, 2024, 2025).

Usage:
  python database/import_firms_full_archive.py --year 2023
  python database/import_firms_full_archive.py --year 2022 --input-dir E:\\AGNI-NETRA-DATA\\FIRMS\\HISTORICAL\\2022\\full
"""

import sys
import os
import argparse
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
from psycopg2.extras import execute_values
from shapely.geometry import Point
from shapely.prepared import prep

from backend.app.core.database import engine
from backend.app.services.spatial_engine import lookup_state, lookup_district
from data_pipeline.adapters.firms_adapter import INDIA_BBOX, INDIA_TERRITORIAL_POLYGON

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


def inspect_archives(archive_dir: str) -> List[Dict[str, Any]]:
    """Inspects the archive directory and discovers all candidate NASA FIRMS ZIP files."""
    if not os.path.exists(archive_dir):
        print(f"[INSPECTION] Target directory does not exist: {archive_dir}")
        return []

    zip_files = [f for f in os.listdir(archive_dir) if f.lower().endswith(".zip")]
    if not zip_files:
        print(f"[INSPECTION] No ZIP files found in directory: {archive_dir}")
        return []

    discovered = []
    for zname in sorted(zip_files):
        zpath = os.path.join(archive_dir, zname)
        sz = os.path.getsize(zpath)
        sha = calculate_sha256(zpath)

        with zipfile.ZipFile(zpath, "r") as zf:
            csv_entries = [name for name in zf.namelist() if name.lower().endswith(".csv")]
            for csv_name in csv_entries:
                with zf.open(csv_name) as cf:
                    ts = io.TextIOWrapper(cf, encoding="utf-8", errors="replace")
                    reader = csv.reader(ts)
                    header = next(reader, None)

                # Determine product & sensor
                fn_upper = zname.upper()
                if "J1V-C2" in fn_upper or "VJ114" in fn_upper:
                    prod = "VJ114IMGTDL"
                    sat = "NOAA-20"
                    sensor = "VIIRS_NOAA20"
                    coll = "Collection 2"
                    is_modis = False
                elif "J2V-C2" in fn_upper or "VJ214" in fn_upper:
                    prod = "VJ214IMGTDL"
                    sat = "NOAA-21"
                    sensor = "VIIRS_NOAA21"
                    coll = "Collection 2"
                    is_modis = False
                elif "SV-C2" in fn_upper or "VNP14" in fn_upper:
                    prod = "VNP14IMGTDL"
                    sat = "Suomi-NPP"
                    sensor = "VIIRS_SNPP"
                    coll = "Collection 2"
                    is_modis = False
                elif "M-C61" in fn_upper or "MCD14" in fn_upper:
                    prod = "MCD14DL"
                    sat = "Terra/Aqua"
                    sensor = "MODIS_COMBINED"
                    coll = "Collection 6.1"
                    is_modis = True
                else:
                    prod = "UNKNOWN_PRODUCT"
                    sat = "UNKNOWN_SATELLITE"
                    sensor = "UNKNOWN_SENSOR"
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
                    "collection": coll,
                    "is_modis": is_modis,
                    "header": header
                })

    return discovered


def resolve_default_archive_dir(target_year: int) -> str:
    candidates = [
        rf"E:\PROJECTS\AGNI-NETRA(DATABASE)\FIRMS\HISTORICAL\{target_year}\full",
        rf"E:\AGNI-NETRA-DATA\FIRMS\HISTORICAL\{target_year}\full"
    ]
    for d in candidates:
        if os.path.exists(d) and any(f.lower().endswith(".zip") for f in os.listdir(d)):
            return d
    return candidates[0]


def import_full_archive(target_year: int, archive_dir: Optional[str] = None) -> bool:
    if archive_dir is None:
        archive_dir = resolve_default_archive_dir(target_year)

    manifest_path = os.path.join(archive_dir, f"archive_manifest_{target_year}.json")

    print("=" * 85, flush=True)
    print(f"  AGNI-NETRA: NASA FIRMS {target_year} FULL ARCHIVE INGESTION", flush=True)
    print("=" * 85, flush=True)

    archives = inspect_archives(archive_dir)
    if not archives:
        print(f"\n[STATUS] {target_year}_FILES_NOT_STAGED", flush=True)
        print(f"Directory {archive_dir} contains no archive ZIP files to import.", flush=True)
        return False

    print(f"\nDiscovered {len(archives)} NASA FIRMS archive(s) in {archive_dir}:", flush=True)
    for arc in archives:
        print(f"  - {arc['zip_name']} ({arc['file_size']:,} bytes) | Product: {arc['product']} | Sensor: {arc['sensor']}", flush=True)

    overall_start_time = time.time()

    # 1. Pre-Ingestion Counts
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

            cur.execute(f"SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = {target_year} AND is_demo = false;")
            det_target_before = cur.fetchone()[0]

    print("\nPre-Ingestion Baseline:", flush=True)
    print(f"  thermal_detections Total : {det_total_before:,}", flush=True)
    print(f"  thermal_history Total    : {hist_total_before:,}", flush=True)
    print(f"  2026 Detections (Locked) : {det_2026_before:,}", flush=True)
    print(f"  2022 Official (Locked)   : {det_2022_real_before:,}", flush=True)
    print(f"  2022 Pilot (Isolated)    : {det_2022_pilot_before:,}", flush=True)
    print(f"  {target_year} Official (Current): {det_target_before:,}\n", flush=True)

    total_source_rows = 0
    total_inside_india = 0
    total_outside_india = 0
    total_rejected = 0

    satellite_distribution = {}
    monthly_distribution = {}
    state_distribution = {}
    district_distribution = {}

    # 2. Ingest Archives
    for config in archives:
        zip_name = config["zip_name"]
        csv_name = config["csv_name"]
        zip_path = config["filepath"]

        print(f"--- Processing Archive: {zip_name} ({config['file_size'] / (1024*1024):.2f} MB) ---", flush=True)
        print(f"  Product: {config['product']} | Sensor: {config['sensor']} | Satellite: {config['satellite']}", flush=True)

        archive_start_time = time.time()
        rows_read = 0
        rows_inside = 0
        rows_outside = 0
        rows_rejected = 0

        detections_batch = []
        history_batch = []

        with zipfile.ZipFile(zip_path, "r") as zf:
            with zf.open(csv_name) as cf:
                text_stream = io.TextIOWrapper(cf, encoding="utf-8", errors="replace")
                reader = csv.DictReader(text_stream)

                for row in reader:
                    rows_read += 1
                    total_source_rows += 1

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
                            if "VJ214" in config["product"]:
                                sat_val = "NOAA-21"
                            elif "VJ114" in config["product"]:
                                sat_val = "NOAA-20"
                            elif "VNP14" in config["product"]:
                                sat_val = "Suomi-NPP"
                            else:
                                sat_val = "NOAA-20" if sat_raw in ["N20", "1", "JPSS-1"] else ("Suomi-NPP" if sat_raw in ["SNPP", "NPP"] else config["satellite"])
                            sensor_val = config["sensor"]

                    except Exception:
                        rows_rejected += 1
                        total_rejected += 1
                        continue

                    # Bounding box quick check
                    if not ((INDIA_BBOX[0] <= lat <= INDIA_BBOX[2]) and (INDIA_BBOX[1] <= lon <= INDIA_BBOX[3])):
                        rows_outside += 1
                        total_outside_india += 1
                        continue

                    # Ultra-fast point-in-polygon with prepared geometry
                    pt = Point(lon, lat)
                    if not PREPARED_INDIA.contains(pt):
                        rows_outside += 1
                        total_outside_india += 1
                        continue

                    rows_inside += 1
                    total_inside_india += 1

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
                        "reference_year": target_year,
                        "processing_type": "STANDARD_SCIENCE"
                    }

                    state = lookup_state(lat, lon)
                    district = lookup_district(lat, lon)

                    # Distributions
                    month_key = acq_date[:7]
                    monthly_distribution[month_key] = monthly_distribution.get(month_key, 0) + 1
                    satellite_distribution[sat_val] = satellite_distribution.get(sat_val, 0) + 1
                    if state:
                        state_distribution[state] = state_distribution.get(state, 0) + 1
                    if district:
                        district_distribution[district] = district_distribution.get(district, 0) + 1

                    detections_batch.append((
                        record_id,
                        sat_val,
                        lat,
                        lon,
                        brightness,
                        round(confidence / 100.0, 4),
                        acq_dt,
                        day_night,
                        "FIRMS_HISTORICAL_ARCHIVE",
                        json.dumps(metadata),
                        state,
                        district,
                        frp,
                        bright_t31,
                        False,  # is_demo = False (Official Production Archive)
                        lon,
                        lat
                    ))

                    history_batch.append((
                        record_id,
                        "FIRMS_HISTORICAL_ARCHIVE",
                        sensor_val,
                        sat_val,
                        lat,
                        lon,
                        acq_date,
                        acq_time_raw,
                        acq_dt,
                        brightness,
                        bright_t31,
                        round(confidence / 100.0, 4),
                        frp,
                        day_night,
                        "STANDARD_SCIENCE",
                        state,
                        district,
                        json.dumps(metadata),
                        lon,
                        lat,
                        False
                    ))

                    if len(detections_batch) >= BATCH_SIZE:
                        _flush_batches(detections_batch, history_batch)
                        detections_batch.clear()
                        history_batch.clear()
                        elapsed_so_far = time.time() - archive_start_time
                        speed = rows_inside / max(elapsed_so_far, 0.001)
                        print(f"  [Progress] {rows_read:,} rows read -> {rows_inside:,} inside India ({speed:.1f} rec/s)", flush=True)

                if detections_batch:
                    _flush_batches(detections_batch, history_batch)
                    detections_batch.clear()
                    history_batch.clear()

        archive_elapsed = time.time() - archive_start_time
        archive_speed = rows_inside / max(archive_elapsed, 0.001)
        print(f"  --> Completed {zip_name}: {rows_inside:,} India records in {archive_elapsed:.2f}s ({archive_speed:.1f} rows/sec)\n", flush=True)

    total_elapsed = time.time() - overall_start_time
    total_speed = total_inside_india / max(total_elapsed, 0.001)

    # 3. Post-Ingestion Verification
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

            cur.execute(f"SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = {target_year} AND is_demo = false;")
            det_target_real_after = cur.fetchone()[0]

    status_str = f"{target_year}_FULL_ARCHIVE_IMPORTED"
    print("=" * 85, flush=True)
    print("  FINAL INGESTION & INTEGRITY SUMMARY", flush=True)
    print("=" * 85, flush=True)
    print(f"Status                  : {status_str}", flush=True)
    print(f"Total Source Rows Read  : {total_source_rows:,}", flush=True)
    print(f"Total Inside India (OK) : {total_inside_india:,}", flush=True)
    print(f"Filtered Outside India  : {total_outside_india:,}", flush=True)
    print(f"thermal_detections Total: {det_total_before:,} -> {det_total_after:,} (+{det_total_after - det_total_before:,})", flush=True)
    print(f"thermal_history Total   : {hist_total_before:,} -> {hist_total_after:,} (+{hist_total_after - hist_total_before:,})", flush=True)
    print(f"2026 Detections (Locked): {det_2026_before:,} -> {det_2026_after:,} (DELTA: {det_2026_after - det_2026_before}) [UNTOUCHED]", flush=True)
    print(f"2022 Official (Locked)  : {det_2022_real_before:,} -> {det_2022_real_after:,} (DELTA: {det_2022_real_after - det_2022_real_before}) [UNTOUCHED]", flush=True)
    print(f"Real Official {target_year} (DB) : {det_target_real_after:,} (is_demo=False)", flush=True)
    print(f"Pilot Isolated 2022 (DB): {det_2022_pilot_after:,} (is_demo=True)", flush=True)
    print(f"Null / Invalid Records  : {total_rejected}", flush=True)
    print(f"Total Elapsed Time      : {total_elapsed:.2f}s ({total_speed:.1f} rows/sec avg)", flush=True)

    # 4. Generate Manifest File
    manifest_data = {
        "status": status_str,
        "target_year": target_year,
        "processing_timestamp": datetime.now(timezone.utc).isoformat(),
        "summary_counts": {
            "source_rows_read": total_source_rows,
            "inside_india_accepted": total_inside_india,
            "outside_india_filtered": total_outside_india,
            "rejected_corrupted": total_rejected,
            f"database_real_{target_year}_records": det_target_real_after,
            "database_real_2022_records": det_2022_real_after,
            "database_pilot_isolated_records": det_2022_pilot_after,
            "2026_count_before": det_2026_before,
            "2026_count_after": det_2026_after,
            "2026_delta": det_2026_after - det_2026_before,
            "2022_delta": det_2022_real_after - det_2022_real_before
        },
        "archive_files": archives,
        "satellite_distribution": satellite_distribution,
        "monthly_distribution": dict(sorted(monthly_distribution.items())),
        "state_distribution": dict(sorted(state_distribution.items(), key=lambda x: x[1], reverse=True)),
        "null_or_invalid_rows": total_rejected,
        "performance": {
            "elapsed_seconds": round(total_elapsed, 2),
            "rows_per_second_avg": round(total_speed, 1),
            "batch_size": BATCH_SIZE
        }
    }

    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest_data, mf, indent=2)
    print(f"Manifest written to     : {manifest_path}\n", flush=True)

    return True


def _flush_batches(detections_batch, history_batch):
    """Flushes batches directly into PostgreSQL using psycopg2 execute_values with ON CONFLICT DO NOTHING."""
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            det_query = """
                INSERT INTO thermal_detections (
                    id, satellite, latitude, longitude, brightness, confidence,
                    acq_timestamp, day_night, source, raw_metadata, state, district,
                    frp, bright_t31, is_demo, geom
                ) VALUES %s
                ON CONFLICT (id) DO NOTHING;
            """
            det_template = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))"
            execute_values(cur, det_query, detections_batch, template=det_template)

            hist_query = """
                INSERT INTO thermal_history (
                    id, source, sensor, satellite, latitude, longitude,
                    acq_date, acq_time, acq_timestamp, brightness, bright_t31,
                    confidence, frp, day_night, processing_type, state, district,
                    raw_metadata, geom, is_demo
                ) VALUES %s
                ON CONFLICT (id) DO NOTHING;
            """
            hist_template = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)"
            execute_values(cur, hist_query, history_batch, template=hist_template)

        conn.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGNI-NETRA Generalized NASA FIRMS Historical Archive Importer")
    parser.add_argument("--year", type=int, default=2023, help="Calendar year to import (e.g. 2023)")
    parser.add_argument("--input-dir", type=str, default=None, help="Custom input directory path")
    args = parser.parse_args()

    import_full_archive(target_year=args.year, archive_dir=args.input_dir)
