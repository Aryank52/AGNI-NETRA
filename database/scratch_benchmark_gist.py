import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import text
from backend.app.core.database import engine

def benchmark_gist():
    with engine.connect() as conn:
        print("Testing GiST query performance on industrial facilities...")
        t0 = time.time()
        
        # Test sample of 100 facilities with GiST ST_DWithin
        res = conn.execute(text("""
            EXPLAIN ANALYZE
            SELECT f.id, count(td.id) as det_count
            FROM (SELECT id, geom FROM industrial_facilities WHERE geom IS NOT NULL LIMIT 100) f
            LEFT JOIN thermal_detections td 
              ON ST_DWithin(f.geom::geography, ST_SetSRID(ST_MakePoint(td.longitude, td.latitude), 4326)::geography, 2000.0)
             AND td.is_demo = false
            GROUP BY f.id;
        """)).fetchall()
        print("Explain plan:")
        for r in res:
            print(" ", r[0])
        print(f"Time taken: {time.time() - t0:.2f}s")

if __name__ == "__main__":
    benchmark_gist()
