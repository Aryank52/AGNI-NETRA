import sqlite3
from collections import Counter
import sys

conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()
where_sql = """
    latitude IS NOT NULL 
    AND longitude IS NOT NULL 
    AND (
        cea_project_name IS NULL 
        AND (facility_type IS NULL OR LOWER(facility_type) NOT LIKE '%power%') 
        AND (master_sector IS NULL OR LOWER(master_sector) NOT LIKE '%power%') 
        AND (master_sector IS NULL OR LOWER(master_sector) NOT LIKE '%electricity%')
    )
"""

query = f"""
    SELECT id, name, facility_type, master_sector, state, district, latitude, longitude
    FROM industrial_facilities
    WHERE {where_sql}
    ORDER BY 
        COALESCE(firms_detections_1km, 0) DESC,
        CASE 
            WHEN length(id) = 36 THEN 1
            WHEN source = 'PROMOTED_CANDIDATE' THEN 2
            WHEN environmental_clearance_present = 1 THEN 3
            ELSE 4
        END ASC,
        id ASC
    LIMIT 400
"""
rows = cur.execute(query).fetchall()
sys.stdout.buffer.write(f"Total returned: {len(rows)}\n".encode('utf-8'))
states = Counter([r[4] for r in rows])
sys.stdout.buffer.write(b"\nState breakdown of top 400 manufacturing facilities:\n")
for s, c in states.most_common(20):
    sys.stdout.buffer.write(f"  {s}: {c}\n".encode('utf-8'))

types = Counter([r[2] for r in rows])
sys.stdout.buffer.write(b"\nFacility types:\n")
for t, c in types.most_common(10):
    sys.stdout.buffer.write(f"  {t}: {c}\n".encode('utf-8'))
