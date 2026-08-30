import os
import sys
import csv
import json
import time
import uuid
import psycopg2.extras
from datetime import datetime, timezone
from shapely.geometry import Point, Polygon

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine
from backend.app.services.spatial_engine import lookup_state, lookup_district
from data_pipeline.adapters.firms_adapter import INDIA_BBOX, INDIA_TERRITORIAL_POLYGON

FIRMS_DIR = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FIRMS\Extracted files"
BATCH_SIZE = 10000

# Strict Phase 9 Import Order for the 7 remaining datasets
DATASETS_TO_IMPORT = [
    "fire_archive_SV-C2_794937.csv",
    "fire_archive_M-C61_794933.csv",
    "fire_nrt_SV-C2_794937.csv",
    "fire_nrt_M-C61_794933.csv",
    "fire_nrt_J1V-C2_794935.csv",
    "fire_nrt_J2V-C2_794936.csv",
    "fire_nrt_LS_794934.csv"
]

TYPE_DESCRIPTIONS = {
    0: "presumed vegetation fire",
    1: "active volcano",
    2: "other static land source",
    3: "offshore"
}


def resolve_sensor_and_satellite(filename: str, row: dict):
    sat_raw = str(row.get("satellite", "")).strip()
    fn = filename.lower()
    
    if "sv-c2" in fn:
        return "NASA_FIRMS_VIIRS", "VIIRS_SNPP", "Suomi-NPP"
    elif "m-c61" in fn:
        if "aqua" in sat_raw.lower():
            return "NASA_FIRMS_MODIS", "MODIS_AQUA", "Aqua"
        elif "terra" in sat_raw.lower():
            return "NASA_FIRMS_MODIS", "MODIS_TERRA", "Terra"
        else:
            return "NASA_FIRMS_MODIS", "MODIS_COMBINED", "Terra/Aqua"
    elif "j1v-c2" in fn:
        return "NASA_FIRMS_VIIRS", "VIIRS_NOAA20", "NOAA-20"
    elif "j2v-c2" in fn:
        return "NASA_FIRMS_VIIRS", "VIIRS_NOAA21", "NOAA-21"
    elif "ls_" in fn:
        if sat_raw in ["L8", "8"]:
            return "NASA_FIRMS_LANDSAT", "LANDSAT_OLI", "Landsat-8"
        elif sat_raw in ["L9", "9"]:
            return "NASA_FIRMS_LANDSAT", "LANDSAT_OLI_2", "Landsat-9"
        else:
            return "NASA_FIRMS_LANDSAT", "LANDSAT_OLI", "Landsat"
    else:
        return "NASA_FIRMS_GENERIC", "GENERIC_THERMAL", sat_raw or "Satellite"


def normalize_confidence(conf_val: str, filename: str) -> float:
    c = str(conf_val).strip()
    fn = filename.lower()
    
    # MODIS numeric percentage
    if "m-c61" in fn:
        try:
            return min(max(float(c), 0.0), 100.0)
        except Exception:
            return 60.0
            
    # Landsat categorical (L/M/H)
    if "ls_" in fn:
        cu = c.upper()
        if cu == "L":
            return 35.0
        elif cu == "M":
            return 70.0
        elif cu == "H":
            return 95.0
        return 65.0
        
    # VIIRS categorical (l/n/h)
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


def import_single_dataset(csv_filename: str):
    csv_path = os.path.join(FIRMS_DIR, csv_filename)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found: {csv_path}")
        
    start_time = time.time()
    proc_type = "STANDARD_SCIENCE" if "fire_archive" in csv_filename.lower() else "NRT"
    
    print("\n" + "=" * 75)
    print(f"PROCESSING DATASET: {csv_filename}")
    print(f"Processing Type   : {proc_type}")
    print("=" * 75)
    
    # 1. Pre-import database count
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_detections;")
            count_det_before = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_history;")
            count_hist_before = cur.fetchone()[0]
            
    total_rows_read = 0
    inside_india_count = 0
    outside_india_count = 0
    rejected_count = 0
    
    batch_detections = []
    batch_history = []
    
    min_timestamp = None
    max_timestamp = None
    
    sensor_name_sample = None
    sat_name_sample = None
    
    raw_conn = engine.raw_connection()
    cur = raw_conn.cursor()
    
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
    
    try:
        with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
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
                    
                    # Radiometrics & fields (graceful for Landsat with no FRP/brightness)
                    brightness = float(row["brightness"]) if row.get("brightness") and row["brightness"].strip() else None
                    bright_t31 = float(row["bright_t31"]) if row.get("bright_t31") and row["bright_t31"].strip() else None
                    frp = float(row["frp"]) if row.get("frp") and row["frp"].strip() else 0.0
                    
                    conf_raw = row.get("confidence", "")
                    confidence = normalize_confidence(conf_raw, csv_filename)
                    
                    day_night = row.get("daynight", "D").strip().upper()
                    if day_night not in ["D", "N"]:
                        day_night = "D"
                    
                    scan = float(row.get("scan", 0.0)) if row.get("scan") else 0.0
                    track = float(row.get("track", 0.0)) if row.get("track") else 0.0
                    type_int = int(row.get("type", 0)) if row.get("type") and row["type"].strip().isdigit() else None
                    version = row.get("version", "NRT" if proc_type == "NRT" else "2")
                    instrument = row.get("instrument", "")
                    
                    source, sensor, satellite = resolve_sensor_and_satellite(csv_filename, row)
                    if sensor_name_sample is None:
                        sensor_name_sample = sensor
                        sat_name_sample = satellite
                    
                except Exception as ex:
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
                
                # Deterministic Idempotent ID
                source_record_id = f"FIRMS_{sensor}_{acq_date}_{acq_time_raw}_{lat:.5f}_{lon:.5f}"
                record_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, source_record_id))
                
                metadata = {
                    "source_file": csv_filename,
                    "satellite_raw": row.get("satellite", ""),
                    "instrument": instrument,
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
                
                # Tuple for thermal_detections
                det_tuple = (
                    record_id,
                    source,
                    sensor,
                    satellite,
                    lat,
                    lon,
                    acq_dt,
                    brightness,
                    bright_t31,
                    frp,
                    confidence,
                    day_night,
                    None,  # event_id
                    metadata_json,
                    False   # is_demo
                )
                batch_detections.append(det_tuple)
                
                # Tuple for thermal_history
                now_utc = datetime.now(timezone.utc)
                hist_tuple = (
                    record_id,
                    source,
                    sensor,
                    satellite,
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
                    proc_type,
                    state,
                    district,
                    source_record_id,
                    metadata_json,
                    False,  # is_demo
                    now_utc
                )
                batch_history.append(hist_tuple)
                
                if len(batch_detections) >= BATCH_SIZE:
                    psycopg2.extras.execute_values(cur, insert_det_sql, batch_detections, page_size=BATCH_SIZE)
                    psycopg2.extras.execute_values(cur, insert_hist_sql, batch_history, page_size=BATCH_SIZE)
                    raw_conn.commit()
                    batch_detections.clear()
                    batch_history.clear()
                    print(f"  Ingested {inside_india_count:,} Indian records so far (Processed {total_rows_read:,} lines)...")
        
        # Flush remaining
        if batch_detections:
            psycopg2.extras.execute_values(cur, insert_det_sql, batch_detections, page_size=BATCH_SIZE)
            psycopg2.extras.execute_values(cur, insert_hist_sql, batch_history, page_size=BATCH_SIZE)
            raw_conn.commit()
            batch_detections.clear()
            batch_history.clear()
            
    finally:
        cur.close()
        raw_conn.close()
        
    duration = round(time.time() - start_time, 2)
    
    # 2. Post-import verification
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_detections;")
            count_det_after = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_history;")
            count_hist_after = cur.fetchone()[0]
            
    inserted_det = count_det_after - count_det_before
    duplicates = inside_india_count - inserted_det
    
    print("\n--- DATASET MILESTONE REPORT ---")
    print(f"Filename             : {csv_filename}")
    print(f"Processing Type      : {proc_type}")
    print(f"Satellite / Sensor   : {sat_name_sample} / {sensor_name_sample}")
    print(f"Source rows          : {total_rows_read:,}")
    print(f"Rows inside India    : {inside_india_count:,}")
    print(f"Rows outside India   : {outside_india_count:,}")
    print(f"Rows rejected        : {rejected_count:,}")
    print(f"Rows inserted (net)  : {inserted_det:,}")
    print(f"Duplicates / Overlap : {duplicates:,}")
    print(f"Min acq_timestamp    : {min_timestamp}")
    print(f"Max acq_timestamp    : {max_timestamp}")
    print(f"DB count before      : {count_det_before:,}")
    print(f"DB count after       : {count_det_after:,}")
    print(f"Elapsed time         : {duration} s")
    print("--------------------------------\n")
    
    return {
        "filename": csv_filename,
        "processing_type": proc_type,
        "satellite": sat_name_sample,
        "sensor": sensor_name_sample,
        "source_rows": total_rows_read,
        "inside_india": inside_india_count,
        "outside_india": outside_india_count,
        "rejected": rejected_count,
        "inserted": inserted_det,
        "duplicates": duplicates,
        "min_timestamp": str(min_timestamp),
        "max_timestamp": str(max_timestamp),
        "count_before": count_det_before,
        "count_after": count_det_after,
        "duration_s": duration
    }


def run_full_pipeline():
    overall_start = time.time()
    summary_results = []
    
    print("=" * 80)
    print("AGNI-NETRA — BATCH INGESTION OF REMAINING 7 NASA FIRMS ARCHIVES")
    print("=" * 80)
    
    for idx, fname in enumerate(DATASETS_TO_IMPORT, 1):
        print(f"\n>>> [{idx}/{len(DATASETS_TO_IMPORT)}] INGESTING {fname} ...")
        res = import_single_dataset(fname)
        summary_results.append(res)
        
    overall_duration = round(time.time() - overall_start, 2)
    
    # Final National Check (Phase 11)
    print("\n" + "=" * 80)
    print("PHASE 11 — FINAL NATIONAL FIRMS DATA CHECK")
    print("=" * 80)
    
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            # 1. Total counts
            cur.execute("SELECT COUNT(*) FROM thermal_detections;")
            total_det = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_history;")
            total_hist = cur.fetchone()[0]
            
            # 2. Satellite breakdown
            cur.execute("""
                SELECT satellite, COUNT(*) as cnt, MIN(acq_timestamp), MAX(acq_timestamp)
                FROM thermal_detections
                WHERE is_demo = false
                GROUP BY satellite
                ORDER BY cnt DESC;
            """)
            sat_stats = cur.fetchall()
            
            # 3. Sensor breakdown
            cur.execute("""
                SELECT sensor, COUNT(*) as cnt, ROUND(AVG(frp)::numeric, 2), ROUND(MAX(frp)::numeric, 2)
                FROM thermal_detections
                WHERE is_demo = false
                GROUP BY sensor
                ORDER BY cnt DESC;
            """)
            sensor_stats = cur.fetchall()
            
            # 4. Processing type breakdown
            cur.execute("""
                SELECT processing_type, COUNT(*) as cnt
                FROM thermal_history
                WHERE is_demo = false
                GROUP BY processing_type
                ORDER BY cnt DESC;
            """)
            proc_stats = cur.fetchall()
            
            # 5. Year / Month breakdown
            cur.execute("""
                SELECT 
                    EXTRACT(YEAR FROM acq_timestamp)::int as yr,
                    EXTRACT(MONTH FROM acq_timestamp)::int as mo,
                    COUNT(*) as monthly_detections
                FROM thermal_detections
                WHERE is_demo = false
                GROUP BY yr, mo
                ORDER BY yr, mo;
            """)
            monthly_stats = cur.fetchall()
            
            # 6. Null coordinate & spatial validity
            cur.execute("""
                SELECT 
                    COUNT(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)) AS valid_geoms,
                    COUNT(*) FILTER (WHERE latitude IS NULL OR longitude IS NULL) AS null_coords,
                    COUNT(*) FILTER (WHERE acq_timestamp IS NULL) AS null_timestamps
                FROM thermal_detections;
            """)
            geom_stats = cur.fetchone()
            
    print(f"Total National Detections in thermal_detections : {total_det:,}")
    print(f"Total Observations in thermal_history          : {total_hist:,}")
    print(f"Total Real PostGIS Geometries (SRID 4326)      : {geom_stats[0]:,}")
    print(f"Null Coordinate Count                          : {geom_stats[1]}")
    print(f"Null Timestamp Count                           : {geom_stats[2]}")
    print(f"Total Batch Pipeline Ingestion Duration        : {overall_duration} s\n")
    
    print("Breakdown by Satellite:")
    for s in sat_stats:
        print(f"  • {s[0]:<15} : {s[1]:>9,} observations | {s[2]} to {s[3]}")
        
    print("\nBreakdown by Sensor:")
    for s in sensor_stats:
        print(f"  • {s[0]:<16} : {s[1]:>9,} observations | Avg FRP: {s[2]} MW | Max FRP: {s[3]} MW")
        
    print("\nBreakdown by Processing Type:")
    for p in proc_stats:
        print(f"  • {p[0]:<18} : {p[1]:>9,} observations")
        
    print("\nTemporal Distribution (Month-by-Month across India 2026):")
    for m in monthly_stats:
        print(f"  • {m[0]}-{str(m[1]).zfill(2)} : {m[2]:>9,} detections")
        
    print("=" * 80)


if __name__ == "__main__":
    run_full_pipeline()
