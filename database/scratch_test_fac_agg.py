import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import text
from backend.app.core.database import engine

def test_facility_aggregation():
    with engine.connect() as conn:
        print("Testing facility aggregation query...")
        t0 = time.time()
        
        # Aggregate 500 facilities
        q = text("""
            WITH sample_fac AS (
                SELECT id, name, latitude, longitude
                FROM industrial_facilities
                WHERE latitude IS NOT NULL
                LIMIT 500
            )
            SELECT 
                f.id,
                f.name,
                COUNT(td.id) as det_count_2km,
                COUNT(td.id) FILTER (WHERE td.latitude BETWEEN f.latitude - 0.009 AND f.latitude + 0.009 
                                       AND td.longitude BETWEEN f.longitude - 0.009 AND f.longitude + 0.009) as det_count_1km,
                COUNT(td.id) FILTER (WHERE td.latitude BETWEEN f.latitude - 0.0045 AND f.latitude + 0.0045 
                                       AND td.longitude BETWEEN f.longitude - 0.0045 AND f.longitude + 0.0045) as det_count_500m,
                COUNT(DISTINCT DATE(td.acq_timestamp)) as active_days,
                COALESCE(AVG(td.frp), 0.0) as mean_frp,
                COALESCE(MAX(td.frp), 0.0) as max_frp,
                COALESCE(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY td.frp), 0.0) as median_frp,
                COALESCE(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY td.frp), 0.0) as p90_frp,
                COUNT(td.id) FILTER (WHERE td.day_night = 'D') as day_count,
                COUNT(td.id) FILTER (WHERE td.day_night = 'N') as night_count,
                MIN(td.acq_timestamp) as first_seen,
                MAX(td.acq_timestamp) as last_seen
            FROM sample_fac f
            LEFT JOIN thermal_detections td
              ON td.latitude BETWEEN f.latitude - 0.018 AND f.latitude + 0.018
             AND td.longitude BETWEEN f.longitude - 0.018 AND f.longitude + 0.018
             AND td.is_demo = false
            GROUP BY f.id, f.name;
        """)
        res = conn.execute(q).fetchall()
        print(f"Aggregated {len(res)} facilities in {time.time() - t0:.2f}s")
        active = [r for r in res if r[2] > 0]
        print(f"Facilities with thermal activity in sample: {len(active)}")
        if active:
            print("Sample active facility result:")
            print(" ", active[0])

if __name__ == "__main__":
    test_facility_aggregation()
