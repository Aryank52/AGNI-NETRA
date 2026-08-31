"""
AGNI-NETRA — Phase 5B-3: Ultra-Fast Authoritative NASA FIRMS 2022 Full Archive Ingestion Engine
Optimized with Shapely Prepared Geometries (prep), high-throughput batching, ON CONFLICT DO NOTHING, and real-time progress logging.
"""

import os
import sys
import io
import csv
import json
import time
import uuid
import zipfile
import hashlib
import psycopg2.extras
from datetime import datetime, timezone
from collections import defaultdict
from shapely.geometry import Point
from shapely.prepared import prep

# Ensure unbuffered standard output for real-time terminal monitoring
sys.stdout.reconfigure(line_buffering=True)

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.database import engine
from backend.app.services.spatial_engine import lookup_state, lookup_district
from data_pipeline.adapters.firms_adapter import INDIA_BBOX, INDIA_TERRITORIAL_POLYGON

# Prepared geometry for 50x-100x faster point-in-polygon containment checks
PREPARED_INDIA = prep(INDIA_TERRITORIAL_POLYGON)

ARCHIVE_DIR = r"E:\AGNI-NETRA-DATA\FIRMS\HISTORICAL\2022\full"
BATCH_SIZE = 25000

ARCHIVE_CONFIGS = [
    {
        "zip_name": "DL_FIRE_J1V-C2_795685.zip",
        "product": "VJ114IMGTDL",
        "collection": "Collection 2",
        "satellite": "NOAA-20",
        "sensor": "VIIRS_NOAA20",
        "source": "NASA_FIRMS_VIIRS",
        "resolution_m": 375.0,
        "is_modis": False
    },
    {
        "zip_name": "DL_FIRE_SV-C2_795686.zip",
        "product": "VNP14IMGTDL",
        "collection": "Collection 2",
        "satellite": "Suomi-NPP",
        "sensor": "VIIRS_SNPP",
        "source": "NASA_FIRMS_VIIRS",
        "resolution_m": 375.0,
        "is_modis": False
    },
    {
        "zip_name": "DL_FIRE_M-C61_795684.zip",
        "product": "MCD14DL",
        "collection": "Collection 6.1",
        "satellite": "Terra/Aqua",
        "sensor": "MODIS_COMBINED",
        "source": "NASA_FIRMS_MODIS",
        "resolution_m": 1000.0,
        "is_modis": True
    }
]

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


def import_2022_full_archives():
    print("=" * 85, flush=True)
    print("  AGNI-NETRA — PHASE 5B-3: NASA FIRMS 2022 FULL ARCHIVE INGESTION (HIGH-SPEED)", flush=True)
    print("=" * 85, flush=True)

    overall_start_time = time.time()

    # 1. Pre-Ingestion Audit
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_detections;")
            det_total_before = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_history;")
            hist_total_before = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;")
            det_2026_before = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022;")
            det_2022_before = cur.fetchone()[0]

    print(f"Pre-Ingestion Counts:", flush=True)
    print(f"  thermal_detections Total : {det_total_before:,}", flush=True)
    print(f"  thermal_history Total    : {hist_total_before:,}", flush=True)
    print(f"  2026 Detections (Locked) : {det_2026_before:,}", flush=True)
    print(f"  2022 Detections (Current): {det_2022_before:,}", flush=True)

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
    state_stats = defaultdict(int)
    district_stats = defaultdict(int)

    raw_conn = engine.raw_connection()

    for config in ARCHIVE_CONFIGS:
        zip_name = config["zip_name"]
        zip_path = os.path.join(ARCHIVE_DIR, zip_name)
        if not os.path.exists(zip_path):
            print(f"ERROR: Archive file not found: {zip_path}", flush=True)
            continue

        file_size_bytes = os.path.getsize(zip_path)
        sha256_hash = calculate_sha256(zip_path)
        file_start_time = time.time()

        print(f"\n--- Processing Archive: {zip_name} ({file_size_bytes / (1024 * 1024):.2f} MB) ---", flush=True)
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
            csv_names = [name for name in zf.namelist() if name.endswith(".csv")]
            if not csv_names:
                print(f"  No CSV found in {zip_name}!", flush=True)
                continue
            csv_filename = csv_names[0]

            with zf.open(csv_filename) as cf:
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
                        acq_dt = datetime.strptime(dt_str, "%Y-%m-%d %H%M")

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
                            sat_val = "NOAA-20" if sat_raw in ["N20", "1", "JPSS-1"] else ("Suomi-NPP" if sat_raw in ["SNPP", "NPP"] else config["satellite"])
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
                        "source_file": csv_filename,
                        "archive_zip": zip_name,
                        "dataset_scope": "FULL_ARCHIVE",
                        "product": config["product"],
                        "collection": config["collection"],
                        "satellite_raw": sat_raw,
                        "instrument": config["sensor"].split("_")[0],
                        "version": version,
                        "scan": scan,
                        "track": track,
                        "type": type_int,
                        "type_description": TYPE_DESCRIPTIONS.get(type_int, "other"),
                        "confidence_raw": conf_str,
                        "source_record_id": source_record_id
                    }
                    metadata_json = json.dumps(metadata)

                    state = lookup_state(lat, lon)
                    district = lookup_district(lat, lon)

                    ym = acq_date[:7]
                    monthly_stats[ym] += 1
                    daily_stats[acq_date] += 1
                    satellite_stats[sat_val] += 1
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
                        False
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
                        False,
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
                        print(f"  [Progress] {rows_read:,} rows read -> {rows_inside:,} inside India ({round(rows_inside/elapsed_so_far, 1):,} rec/s)", flush=True)

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
            "csv_filename": csv_filename,
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
        print(f"  --> Completed {zip_name}: {rows_inside:,} India records in {file_elapsed:.2f}s ({throughput:.1f} rows/sec)", flush=True)

    raw_conn.close()

    overall_elapsed = time.time() - overall_start_time

    # 2. Post-Ingestion Database Verification
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_detections;")
            det_total_after = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_history;")
            hist_total_after = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;")
            det_2026_after = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022;")
            det_2022_total_after = cur.fetchone()[0]

            cur.execute("""
                SELECT is_demo, COUNT(*)
                FROM thermal_detections
                WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022
                GROUP BY is_demo;
            """)
            demo_breakdown = dict(cur.fetchall())
            real_2022_count = demo_breakdown.get(False, 0)
            pilot_isolated_count = demo_breakdown.get(True, 0)

            cur.execute("""
                SELECT COUNT(*) FROM thermal_detections 
                WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 
                  AND (latitude IS NULL OR longitude IS NULL OR acq_timestamp IS NULL);
            """)
            null_count = cur.fetchone()[0]

    manifest_path = os.path.join(ARCHIVE_DIR, "archive_manifest_2022.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump({
            "status": "2022_FULL_ARCHIVE_IMPORTED",
            "target_year": 2022,
            "overall_elapsed_seconds": round(overall_elapsed, 2),
            "overall_throughput_rows_sec": round(total_accepted_india / max(0.001, overall_elapsed), 1),
            "summary_counts": {
                "source_rows_read": total_read_all,
                "inside_india_accepted": total_accepted_india,
                "outside_india_filtered": total_outside_all,
                "rejected_corrupted": total_rejected_all,
                "database_real_2022_records": real_2022_count,
                "database_pilot_isolated_records": pilot_isolated_count,
                "thermal_detections_total_before": det_total_before,
                "thermal_detections_total_after": det_total_after,
                "2026_count_before": det_2026_before,
                "2026_count_after": det_2026_after,
                "2026_delta": det_2026_after - det_2026_before
            },
            "satellite_distribution": satellite_stats,
            "monthly_distribution": dict(sorted(monthly_stats.items())),
            "state_distribution": dict(sorted(state_stats.items(), key=lambda x: x[1], reverse=True)),
            "distinct_dates_count": len(daily_stats),
            "distinct_districts_count": len(district_stats),
            "null_or_invalid_rows": null_count,
            "archives": manifest_entries
        }, mf, indent=2)

    print("\n" + "=" * 85, flush=True)
    print("  FINAL INGESTION & INTEGRITY SUMMARY", flush=True)
    print("=" * 85, flush=True)
    print(f"Status                  : 2022_FULL_ARCHIVE_IMPORTED", flush=True)
    print(f"Total Source Rows Read  : {total_read_all:,}", flush=True)
    print(f"Total Inside India (OK) : {total_accepted_india:,}", flush=True)
    print(f"Filtered Outside India  : {total_outside_all:,}", flush=True)
    print(f"thermal_detections Total: {det_total_before:,} -> {det_total_after:,} (+{det_total_after - det_total_before:,})", flush=True)
    print(f"thermal_history Total   : {hist_total_before:,} -> {hist_total_after:,} (+{hist_total_after - hist_total_before:,})", flush=True)
    print(f"2026 Detections (Locked): {det_2026_before:,} -> {det_2026_after:,} (DELTA: {det_2026_after - det_2026_before}) [UNTOUCHED]", flush=True)
    print(f"Real Official 2022 (DB) : {real_2022_count:,} (is_demo=False)", flush=True)
    print(f"Pilot Isolated 2022 (DB): {pilot_isolated_count:,} (is_demo=True)", flush=True)
    print(f"Null / Invalid Records  : {null_count}", flush=True)
    print(f"Total Elapsed Time      : {overall_elapsed:.2f}s ({round(total_accepted_india / max(0.001, overall_elapsed), 1):,} rows/sec avg)", flush=True)
    print(f"Manifest written to     : {manifest_path}", flush=True)


if __name__ == "__main__":
    import_2022_full_archives()
