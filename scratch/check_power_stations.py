import sqlite3
import sys

conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()
rows = cur.execute("""
    SELECT id, name, facility_type, master_sector, state, district, latitude, longitude
    FROM industrial_facilities
    WHERE (cea_project_name IS NOT NULL OR LOWER(facility_type) LIKE '%power%' OR LOWER(master_sector) LIKE '%power%')
    ORDER BY 
        COALESCE(firms_detections_1km, 0) DESC,
        CASE 
            WHEN length(id) = 36 THEN 1
            WHEN source = 'CEA' THEN 2
            WHEN cea_project_name IS NOT NULL THEN 3
            WHEN plant_capacity IS NOT NULL THEN 4
            WHEN id LIKE 'osm_relation_%' THEN 5
            WHEN id LIKE 'osm_way_%' THEN 6
            ELSE 7
        END ASC,
        id ASC
    LIMIT 200
""").fetchall()

sys.stdout.buffer.write(f"Top 200 power stations states:\n".encode('utf-8'))
from collections import Counter
counts = Counter([r[4] for r in rows])
for s, c in counts.most_common(15):
    sys.stdout.buffer.write(f"  {s}: {c}\n".encode('utf-8'))

types = Counter([r[2] for r in rows])
sys.stdout.buffer.write(f"\nFacility types in power stations query:\n".encode('utf-8'))
for t, c in types.most_common(10):
    sys.stdout.buffer.write(f"  {t}: {c}\n".encode('utf-8'))
