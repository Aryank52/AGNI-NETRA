import sqlite3
import sys
from collections import Counter

conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()
rows = cur.execute("""
    SELECT id, name, facility_type, master_sector, state, district, latitude, longitude
    FROM industrial_facilities
    ORDER BY 
        COALESCE(firms_detections_1km, 0) DESC,
        CASE 
            WHEN length(id) = 36 THEN 1
            WHEN source = 'PROMOTED_CANDIDATE' THEN 2
            WHEN source = 'CEA' THEN 3
            WHEN cea_project_name IS NOT NULL THEN 4
            WHEN plant_capacity IS NOT NULL THEN 5
            WHEN environmental_clearance_present = 1 THEN 6
            WHEN id LIKE 'osm_relation_%' THEN 7
            WHEN id LIKE 'osm_way_%' THEN 8
            ELSE 9
        END ASC,
        id ASC
    LIMIT 400
""").fetchall()

sys.stdout.buffer.write(f"Top 400 facilities states:\n".encode('utf-8'))
counts = Counter([r[4] for r in rows])
for s, c in counts.most_common(15):
    sys.stdout.buffer.write(f"  {s}: {c}\n".encode('utf-8'))

types = Counter([r[2] for r in rows])
sys.stdout.buffer.write(f"\nFacility types in facilities query:\n".encode('utf-8'))
for t, c in types.most_common(10):
    sys.stdout.buffer.write(f"  {t}: {c}\n".encode('utf-8'))

sectors = Counter([r[3] for r in rows])
sys.stdout.buffer.write(f"\nSectors in facilities query:\n".encode('utf-8'))
for sec, c in sectors.most_common(10):
    sys.stdout.buffer.write(f"  {sec}: {c}\n".encode('utf-8'))
