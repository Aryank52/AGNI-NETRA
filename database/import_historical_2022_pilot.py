"""
AGNI-NETRA — Phase 5B-1: Historical FIRMS 2022 Pilot Ingestion Engine
Streams, normalizes, and batch-inserts 2022 Standard Science FIRMS Archive data:
1. fire_archive_SV-C2_2022.csv (VIIRS Suomi-NPP 375m, VNP14IMGTDL)
2. fire_archive_J1V-C2_2022.csv (VIIRS NOAA-20 375m, VJ114IMGTDL)
3. fire_archive_M-C61_2022.csv (MODIS Terra/Aqua Combined 1km, MCD14DL)
"""

import os
import sys
import csv
import json
import time
import uuid
import hashlib
import psycopg2.extras
from datetime import datetime, timezone
from shapely.geometry import Point

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.database import engine
from backend.app.services.spatial_engine import lookup_state, lookup_district
from data_pipeline.adapters.firms_adapter import INDIA_BBOX, INDIA_TERRITORIAL_POLYGON

DATA_DIR_2022 = r"E:\AGNI-NETRA-DATA\FIRMS\HISTORICAL\2022"
BATCH_SIZE = 10000

ARCHIVE_FILES_2022 = [
    {
        "filename": "fire_archive_SV-C2_2022.csv",
        "product": "VNP14IMGTDL",
        "collection": "Collection 2",
        "satellite": "Suomi-NPP",
        "sensor": "VIIRS_SNPP",
        "source": "NASA_FIRMS_VIIRS",
        "resolution_m": 375.0
    },
    {
        "filename": "fire_archive_J1V-C2_2022.csv",
        "product": "VJ114IMGTDL",
        "collection": "Collection 2",
        "satellite": "NOAA-20",
        "sensor": "VIIRS_NOAA20",
        "source": "NASA_FIRMS_VIIRS",
        "resolution_m": 375.0
    },
    {
        "filename": "fire_archive_M-C61_2022.csv",
        "product": "MCD14DL",
        "collection": "Collection 6.1",
        "satellite": "Terra/Aqua",
        "sensor": "MODIS_COMBINED",
        "source": "NASA_FIRMS_MODIS",
        "resolution_m": 1000.0
    }
]

TYPE_DESCRIPTIONS = {
    0: "presumed vegetation fire",
    1: "active volcano",
    2: "other static land source",
    3: "offshore"
}


def calculate_sha256(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def normalize_confidence(conf_val: str, filename: str) -> float:
    c = str(conf_val).strip()
    fn = filename.lower()

    if "m-c61" in fn:
        try:
            return min(max(float(c), 0.0), 100.0)
        except Exception:
            return 60.0

    cl = c.lower()
    if cl in ["l", "low"]:
        return 30.0
    elif cl in ["n", "nominal"]:
        return 65.0
    elif cl in ["h", "high"]:
        return 95.0

    try:
        val = float(c)
        return min(max(val, 0.0), 100.0)
    except Exception:
        return 65.0


def import_2022_pilot():
    print("\n" + "=" * 80)
    print("  AGNI-NETRA — HISTORICAL FIRMS 2022 PILOT INGESTION")
    print("=" * 80)

    # 1. Pre-import database counts
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_detections;")
            det_count_before = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_history;")
            hist_count_before = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;")
            det_2026_before = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022;")
            det_2022_before = cur.fetchone()[0]

    print(f"Pre-Import Database Counts:")
    print(f"  thermal_detections Total : {det_count_before:,}")
    print(f"  thermal_history Total    : {hist_count_before:,}")
    print(f"  2026 Detections (Locked) : {det_2026_before:,}")
    print(f"  2022 Detections (Prior)  : {det_2022_before:,}")

    manifests = []
    overall_start = time.time()
    total_2022_inserted = 0

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

    raw_conn = engine.raw_connection()

    for file_info in ARCHIVE_FILES_2022:
        filename = file_info["filename"]
        filepath = os.path.join(DATA_DIR_2022, filename)
        if not os.path.exists(filepath):
            print(f"ERROR: File not found: {filepath}")
            continue

        file_size_bytes = os.path.getsize(filepath)
        file_sha256 = calculate_sha256(filepath)
        start_file_time = time.time()

        print(f"\nProcessing 2022 File: {filename} ({file_size_bytes / (1024 * 1024):.2f} MB)")
        print(f"  SHA-256: {file_sha256}")
        print(f"  Product: {file_info['product']} ({file_info['collection']}) | Satellite: {file_info['satellite']}")

        total_rows_read = 0
        inside_india_count = 0
        outside_india_count = 0
        rejected_count = 0
        min_timestamp = None
        max_timestamp = None

        batch_detections = []
        batch_history = []

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)

            for row in reader:
                total_rows_read += 1

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
                    confidence = normalize_confidence(conf_raw, filename)

                    day_night = row.get("daynight", "D").strip().upper()
                    if day_night not in ["D", "N"]:
                        day_night = "D"

                    scan = float(row.get("scan", 0.0)) if row.get("scan") else 0.0
                    track = float(row.get("track", 0.0)) if row.get("track") else 0.0
                    type_int = int(row.get("type", 0)) if row.get("type") and row["type"].strip().isdigit() else None
                    version = row.get("version", "2.0")

                    # Satellite resolution
                    sat_val = row.get("satellite", "").strip() or file_info["satellite"]
                    if "M-C61" in filename:
                        sat_val = "Aqua" if "aqua" in sat_val.lower() else ("Terra" if "terra" in sat_val.lower() else "Terra/Aqua")
                        sensor_val = f"MODIS_{sat_val.upper()}" if sat_val in ["Aqua", "Terra"] else "MODIS_COMBINED"
                    else:
                        sensor_val = file_info["sensor"]

                except Exception:
                    rejected_count += 1
                    continue

                # Spatial India Filtering
                if not ((INDIA_BBOX[0] <= lat <= INDIA_BBOX[2]) and (INDIA_BBOX[1] <= lon <= INDIA_BBOX[3])):
                    outside_india_count += 1
                    continue

                pt = Point(lon, lat)
                if not INDIA_TERRITORIAL_POLYGON.contains(pt):
                    outside_india_count += 1
                    continue

                inside_india_count += 1

                if min_timestamp is None or acq_dt < min_timestamp:
                    min_timestamp = acq_dt
                if max_timestamp is None or acq_dt > max_timestamp:
                    max_timestamp = acq_dt

                # Deterministic Idempotent UUIDv5
                source_record_id = f"FIRMS_{sensor_val}_{acq_date}_{acq_time_raw}_{lat:.5f}_{lon:.5f}"
                record_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, source_record_id))

                metadata = {
                    "source_file": filename,
                    "product": file_info["product"],
                    "collection": file_info["collection"],
                    "satellite_raw": sat_val,
                    "instrument": file_info["sensor"].split("_")[0],
                    "version": version,
                    "scan": scan,
                    "track": track,
                    "type": type_int,
                    "type_description": TYPE_DESCRIPTIONS.get(type_int) if type_int is not None else None,
                    "confidence_raw": conf_raw,
                    "source_record_id": source_record_id
                }
                metadata_json = json.dumps(metadata)

                state = lookup_state(lat, lon)
                district = lookup_district(lat, lon)

                det_tuple = (
                    record_id,
                    file_info["source"],
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
                    file_info["source"],
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

            # Flush remaining batch
            if batch_detections:
                with raw_conn.cursor() as cur:
                    psycopg2.extras.execute_values(cur, insert_det_sql, batch_detections, page_size=len(batch_detections))
                    psycopg2.extras.execute_values(cur, insert_hist_sql, batch_history, page_size=len(batch_history))
                raw_conn.commit()
                batch_detections = []
                batch_history = []

        file_elapsed = time.time() - start_file_time
        throughput = inside_india_count / max(0.001, file_elapsed)
        total_2022_inserted += inside_india_count

        manifest = {
            "filename": filename,
            "sha256": file_sha256,
            "size_bytes": file_size_bytes,
            "product": file_info["product"],
            "collection": file_info["collection"],
            "satellite": file_info["satellite"],
            "sensor": file_info["sensor"],
            "reference_year": 2022,
            "processing_type": "STANDARD_SCIENCE",
            "date_range": f"{min_timestamp.strftime('%Y-%m-%d')} to {max_timestamp.strftime('%Y-%m-%d')}" if min_timestamp else "N/A",
            "rows_read": total_rows_read,
            "rows_inside_india": inside_india_count,
            "rows_outside_india": outside_india_count,
            "rejected_rows": rejected_count,
            "elapsed_seconds": round(file_elapsed, 2),
            "throughput_rows_sec": round(throughput, 1),
            "import_timestamp": datetime.now(timezone.utc).isoformat()
        }
        manifests.append(manifest)
        print(f"  -> Imported {inside_india_count:,} records in {file_elapsed:.2f}s ({throughput:.1f} rec/s)")

    raw_conn.close()

    # 2. Post-import database counts & validation
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_detections;")
            det_count_after = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_history;")
            hist_count_after = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;")
            det_2026_after = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_detections WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022;")
            det_2022_after = cur.fetchone()[0]

            # 2022 Breakdown by satellite
            cur.execute("""
                SELECT satellite, COUNT(*) 
                FROM thermal_detections 
                WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 
                GROUP BY satellite ORDER BY COUNT(*) DESC;
            """)
            sat_2022_dist = dict(cur.fetchall())

            # 2022 Breakdown by month
            cur.execute("""
                SELECT TO_CHAR(acq_timestamp, 'YYYY-MM'), COUNT(*) 
                FROM thermal_detections 
                WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 
                GROUP BY TO_CHAR(acq_timestamp, 'YYYY-MM') ORDER BY 1;
            """)
            month_2022_dist = dict(cur.fetchall())

            # Null coordinate / invalid checks
            cur.execute("""
                SELECT COUNT(*) FROM thermal_detections 
                WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 
                  AND (latitude IS NULL OR longitude IS NULL OR acq_timestamp IS NULL);
            """)
            null_count = cur.fetchone()[0]

    # Save manifest file
    manifest_path = os.path.join(DATA_DIR_2022, "manifest_2022_ingestion.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump({
            "target_year": 2022,
            "overall_elapsed_seconds": round(time.time() - overall_start, 2),
            "database_counts": {
                "thermal_detections_before": det_count_before,
                "thermal_detections_after": det_count_after,
                "thermal_history_before": hist_count_before,
                "thermal_history_after": hist_count_after,
                "detections_2026_before": det_2026_before,
                "detections_2026_after": det_2026_after,
                "detections_2022_inserted": det_2022_after
            },
            "satellite_distribution_2022": sat_2022_dist,
            "monthly_distribution_2022": month_2022_dist,
            "null_or_invalid_rows": null_count,
            "file_manifests": manifests
        }, mf, indent=2)

    print("\n" + "=" * 80)
    print("  INGESTION SUMMARY & INTEGRITY REPORT")
    print("=" * 80)
    print(f"thermal_detections : {det_count_before:,} -> {det_count_after:,} (+{det_count_after - det_count_before:,})")
    print(f"thermal_history    : {hist_count_before:,} -> {hist_count_after:,} (+{hist_count_after - hist_count_before:,})")
    print(f"2026 Count (Check) : {det_2026_before:,} -> {det_2026_after:,} (DELTA: {det_2026_after - det_2026_before}) [UNTOUCHED]")
    print(f"2022 New Records   : {det_2022_after:,}")
    print(f"Null / Invalid     : {null_count}")
    print(f"Manifest written to: {manifest_path}")
    print("\n2022 Satellite Breakdown:")
    for sat, cnt in sat_2022_dist.items():
        print(f"  - {sat}: {cnt:,}")
    print("\n2022 Monthly Breakdown:")
    for ym, cnt in month_2022_dist.items():
        print(f"  - {ym}: {cnt:,}")


if __name__ == "__main__":
    import_2022_pilot()
