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

CSV_FILE = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FIRMS\Extracted files\fire_archive_J1V-C2_794935.csv"
BATCH_SIZE = 10000

TYPE_DESCRIPTIONS = {
    0: "presumed vegetation fire",
    1: "active volcano",
    2: "other static land source",
    3: "offshore"
}


def normalize_confidence(conf_val: str) -> float:
    c = str(conf_val).strip().lower()
    if c == "l" or c == "low":
        return 30.0
    elif c == "n" or c == "nominal":
        return 65.0
    elif c == "h" or c == "high":
        return 95.0
    try:
        val = float(conf_val)
        return min(max(val, 0.0), 100.0)
    except Exception:
        return 65.0


def import_dataset():
    start_time = time.time()
    filename = os.path.basename(CSV_FILE)
    
    print("=" * 70)
    print(f"AGNI-NETRA — NASA FIRMS ARCHIVE IMPORTER")
    print(f"Target Dataset: {filename}")
    print("=" * 70)
    
    # 1. Check Pre-import counts
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_detections;")
            count_det_before = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_history;")
            count_hist_before = cur.fetchone()[0]
            
    print(f"Database counts before import:")
    print(f"  - thermal_detections : {count_det_before:,}")
    print(f"  - thermal_history    : {count_hist_before:,}")
    print()
    
    total_rows_read = 0
    inside_india_count = 0
    outside_india_count = 0
    rejected_count = 0
    
    batch_detections = []
    batch_history = []
    
    min_timestamp = None
    max_timestamp = None
    
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
        with open(CSV_FILE, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows_read += 1
                
                try:
                    lat = float(row["latitude"])
                    lon = float(row["longitude"])
                    acq_date = row["acq_date"].strip()
                    acq_time_raw = row["acq_time"].strip().zfill(4)
                    
                    # Timestamp construction
                    dt_str = f"{acq_date} {acq_time_raw}"
                    acq_dt = datetime.strptime(dt_str, "%Y-%m-%d %H%M")
                    
                    # Radiometric fields
                    brightness = float(row["brightness"]) if row.get("brightness") else None
                    bright_t31 = float(row["bright_t31"]) if row.get("bright_t31") else None
                    frp = float(row["frp"]) if row.get("frp") else 0.0
                    confidence = normalize_confidence(row.get("confidence", "n"))
                    day_night = row.get("daynight", "D").strip().upper()
                    if day_night not in ["D", "N"]:
                        day_night = "D"
                    
                    type_int = int(row.get("type", 0)) if row.get("type") else 0
                    scan = float(row.get("scan", 0.0))
                    track = float(row.get("track", 0.0))
                    version = row.get("version", "2")
                    instrument = row.get("instrument", "VIIRS")
                    satellite_raw = row.get("satellite", "N20")
                    
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
                
                # Track timestamp bounds
                if min_timestamp is None or acq_dt < min_timestamp:
                    min_timestamp = acq_dt
                if max_timestamp is None or acq_dt > max_timestamp:
                    max_timestamp = acq_dt
                
                # Deterministic Identifiers
                source_record_id = f"FIRMS_J1V-C2_{acq_date}_{acq_time_raw}_{lat:.5f}_{lon:.5f}"
                record_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, source_record_id))
                
                metadata = {
                    "source_file": filename,
                    "satellite_raw": satellite_raw,
                    "instrument": instrument,
                    "version": version,
                    "scan": scan,
                    "track": track,
                    "type": type_int,
                    "type_description": TYPE_DESCRIPTIONS.get(type_int, "other"),
                    "confidence_raw": row.get("confidence", "n"),
                    "source_record_id": source_record_id
                }
                metadata_json = json.dumps(metadata)
                
                state = lookup_state(lat, lon)
                district = lookup_district(lat, lon)
                
                # Tuple for thermal_detections
                det_tuple = (
                    record_id,
                    "NASA_FIRMS_VIIRS",
                    "VIIRS_NOAA20",
                    "NOAA-20",
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
                    "NASA_FIRMS_VIIRS",
                    "VIIRS_NOAA20",
                    "NOAA-20",
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
                    False,  # is_demo
                    now_utc
                )
                batch_history.append(hist_tuple)
                
                # Batch execution
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
    
    # 2. Check Post-import counts & PostGIS Spatial queries
    with engine.raw_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_detections;")
            count_det_after = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM thermal_history;")
            count_hist_after = cur.fetchone()[0]
            
            # Timestamp range & group by sensor/satellite
            cur.execute("""
                SELECT sensor, satellite, COUNT(*), MIN(acq_timestamp), MAX(acq_timestamp)
                FROM thermal_detections
                GROUP BY sensor, satellite;
            """)
            sensor_stats = cur.fetchall()
            
            # PostGIS Geometry check
            cur.execute("""
                SELECT 
                    COUNT(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)) AS valid_geom_count,
                    COUNT(*) FILTER (WHERE latitude IS NULL OR longitude IS NULL) AS null_geom_count
                FROM thermal_detections;
            """)
            geom_stats = cur.fetchone()
            
    inserted_det = count_det_after - count_det_before
    duplicates = inside_india_count - inserted_det
    
    print("\n" + "=" * 70)
    print("IMPORT COMPLETE — FACTUAL SUMMARY REPORT")
    print("=" * 70)
    print(f"Source file              : {filename}")
    print(f"FIRMS Product            : Standard Science Quality Archive (Collection 2)")
    print(f"Satellite                : NOAA-20 (JPSS-1)")
    print(f"Sensor                   : VIIRS (375m)")
    print(f"Rows read                : {total_rows_read:,}")
    print(f"Rows inside India        : {inside_india_count:,}")
    print(f"Rows outside India       : {outside_india_count:,}")
    print(f"Rows rejected            : {rejected_count:,}")
    print(f"Rows inserted (net new)  : {inserted_det:,}")
    print(f"Duplicate/Retried records: {duplicates:,}")
    print(f"Date range               : {min_timestamp} -> {max_timestamp}")
    print(f"Database count before    : {count_det_before:,}")
    print(f"Database count after     : {count_det_after:,}")
    print(f"Import duration          : {duration} seconds")
    print("\nSensor / Satellite Breakdown in thermal_detections:")
    for s in sensor_stats:
        print(f"  • Sensor: {s[0]} | Satellite: {s[1]} | Count: {s[2]:,} | Earliest: {s[3]} | Latest: {s[4]}")
    print(f"\nPostGIS Geometries:")
    print(f"  • Valid PostGIS geometries (SRID 4326): {geom_stats[0]:,}")
    print(f"  • Null/invalid geometries             : {geom_stats[1]:,}")
    print("=" * 70)


if __name__ == "__main__":
    import_dataset()
