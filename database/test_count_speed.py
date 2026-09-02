import time
import psycopg2

conn = psycopg2.connect('postgresql://postgres:projectdatabase_2026@localhost:5432/agni_netra')
cur = conn.cursor()
t0 = time.perf_counter()
cur.execute("""
    SELECT 
        COUNT(*) FILTER (WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = false) as c_2022_off,
        COUNT(*) FILTER (WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = true) as c_2022_pil,
        COUNT(*) FILTER (WHERE acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = false) as c_2023_off,
        COUNT(*) FILTER (WHERE acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01') as c_2024_rec,
        COUNT(*) FILTER (WHERE acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01') as c_2025_off,
        COUNT(*) FILTER (WHERE acq_timestamp >= '2026-01-01') as c_2026_off
    FROM thermal_detections;
""")
res = cur.fetchone()
dt = round((time.perf_counter() - t0) * 1000, 2)
print(f"All 6 counts combined in ONE single scan: {res} in {dt} ms ({dt/1000:.2f} s)")
conn.close()
