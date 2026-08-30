import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from backend.app.core.database import SessionLocal, engine

print("=" * 70)
print("AGNI-NETRA — POST-IMPORT DATABASE VERIFICATION")
print("=" * 70)

with SessionLocal() as session:
    # 1. Total Counts
    det_count = session.execute(text("SELECT COUNT(*) FROM thermal_detections;")).scalar()
    hist_count = session.execute(text("SELECT COUNT(*) FROM thermal_history;")).scalar()
    evt_count = session.execute(text("SELECT COUNT(*) FROM thermal_events;")).scalar()
    
    print(f"Total Database Counts:")
    print(f"  • thermal_detections : {det_count:,}")
    print(f"  • thermal_history    : {hist_count:,}")
    print(f"  • thermal_events     : {evt_count:,}")
    print()
    
    # 2. Timestamp range
    time_bounds = session.execute(text("""
        SELECT 
            MIN(acq_timestamp) as min_time,
            MAX(acq_timestamp) as max_time
        FROM thermal_detections;
    """)).fetchone()
    print(f"Canonical Timestamp Range in thermal_detections:")
    print(f"  • Earliest acquisition: {time_bounds[0]}")
    print(f"  • Latest acquisition  : {time_bounds[1]}")
    print()
    
    # 3. Group by sensor / satellite
    sensor_group = session.execute(text("""
        SELECT 
            sensor, 
            satellite, 
            COUNT(*) as record_count,
            MIN(acq_timestamp) as earliest,
            MAX(acq_timestamp) as latest,
            ROUND(AVG(frp)::numeric, 2) as avg_frp,
            ROUND(MAX(frp)::numeric, 2) as max_frp
        FROM thermal_detections
        GROUP BY sensor, satellite
        ORDER BY record_count DESC;
    """)).fetchall()
    
    print(f"Sensor & Satellite Provenance Breakdown:")
    for row in sensor_group:
        print(f"  • Sensor: {row[0]:<15} | Satellite: {row[1]:<10} | Count: {row[2]:>8,} | FRP (Avg/Max): {row[5]}/{row[6]} MW | Window: {row[3]} to {row[4]}")
    print()
    
    # 4. PostGIS Geometry Check
    geom_stats = session.execute(text("""
        SELECT 
            COUNT(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)) AS valid_geoms,
            COUNT(*) FILTER (WHERE latitude IS NULL OR longitude IS NULL) AS null_geoms,
            ST_AsText(ST_Centroid(ST_Collect(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)))) AS geographic_centroid
        FROM thermal_detections
        WHERE is_demo = false;
    """)).fetchone()
    
    print(f"PostGIS Spatial Geometry Statistics (Real FIRMS data):")
    print(f"  • Valid PostGIS geometries (SRID 4326) : {geom_stats[0]:,}")
    print(f"  • Null/invalid geometries              : {geom_stats[1]:,}")
    print(f"  • Geographic Centroid of Indian Hotspots: {geom_stats[2]}")
    print()
    
    # 5. Top Indian States by Detection Density
    state_stats = session.execute(text("""
        SELECT state, COUNT(*) as detections, ROUND(AVG(frp)::numeric, 2) as avg_frp
        FROM thermal_history
        WHERE is_demo = false
        GROUP BY state
        ORDER BY detections DESC
        LIMIT 8;
    """)).fetchall()
    
    print(f"Top Indian States by Real Hotspot Ingestion:")
    for s in state_stats:
        print(f"  • {s[0]:<20} : {s[1]:>8,} detections (Avg FRP: {s[2]} MW)")
    print()
    
    # 6. Sample Real Ingested Record
    sample = session.execute(text("""
        SELECT id, sensor, satellite, latitude, longitude, acq_timestamp, frp, confidence, day_night, raw_metadata
        FROM thermal_detections
        WHERE is_demo = false
        LIMIT 1;
    """)).fetchone()
    
    print(f"Sample Ingested Record Details:")
    print(f"  • ID            : {sample[0]}")
    print(f"  • Sensor/Sat    : {sample[1]} ({sample[2]})")
    print(f"  • Coordinates   : Lat {sample[3]}, Lon {sample[4]}")
    print(f"  • Timestamp     : {sample[5]}")
    print(f"  • Radiometrics  : FRP={sample[6]} MW, Confidence={sample[7]}%, Day/Night={sample[8]}")
    print(f"  • Metadata      : {sample[9]}")
    print("=" * 70)
