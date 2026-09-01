import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import text
from backend.app.core.database import engine

def benchmark_spatial():
    with engine.connect() as conn:
        print("Testing spatial query performance on industrial facilities...")
        t0 = time.time()
        
        # Test sample of 100 facilities
        res = conn.execute(text("""
            EXPLAIN ANALYZE
            SELECT f.id, count(td.id) as det_count
            FROM (SELECT id, latitude, longitude FROM industrial_facilities WHERE latitude IS NOT NULL LIMIT 100) f
            LEFT JOIN thermal_detections td 
              ON td.latitude BETWEEN f.latitude - 0.02 AND f.latitude + 0.02
             AND td.longitude BETWEEN f.longitude - 0.02 AND f.longitude + 0.02
             AND td.is_demo = false
            GROUP BY f.id;
        """)).fetchall()
        print("Explain plan:")
        for r in res:
            print(" ", r[0])
        print(f"Time taken: {time.time() - t0:.2f}s")

if __name__ == "__main__":
    benchmark_spatial()
