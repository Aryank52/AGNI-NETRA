from backend.app.api.v1.endpoints.gis import parse_bbox
import sqlite3

box = parse_bbox('65.0,8.0,95.0,35.0')
conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()

where_sql = 'latitude BETWEEN :min_lat AND :max_lat AND longitude BETWEEN :min_lon AND :max_lon'

# 1. Industrial facilities
print("--- Industrial Facilities (ORDER BY COALESCE(firms_detections_1km, 0) DESC, id ASC) ---")
query_sql = f'''
    SELECT state, count(*), min(latitude), max(latitude) FROM (
        SELECT state, latitude, longitude FROM industrial_facilities 
        WHERE {where_sql} 
        ORDER BY COALESCE(firms_detections_1km, 0) DESC, id ASC
        LIMIT 400
    ) GROUP BY state ORDER BY count(*) DESC
'''
cur.execute(query_sql, box)
for r in cur.fetchall():
    st = str(r[0]).encode('ascii', 'replace').decode('ascii')
    print(f'  {st}: {r[1]} (lat {r[2]} to {r[3]})')

# 2. Power stations
print("\n--- Power Stations (ORDER BY COALESCE(firms_detections_1km, 0) DESC, id ASC) ---")
where_pwr = where_sql + " AND (cea_project_name IS NOT NULL OR LOWER(facility_type) LIKE '%power%' OR LOWER(master_sector) LIKE '%power%')"
query_pwr = f'''
    SELECT state, count(*), min(latitude), max(latitude) FROM (
        SELECT state, latitude, longitude FROM industrial_facilities 
        WHERE {where_pwr} 
        ORDER BY COALESCE(firms_detections_1km, 0) DESC, id ASC
        LIMIT 200
    ) GROUP BY state ORDER BY count(*) DESC
'''
cur.execute(query_pwr, box)
for r in cur.fetchall():
    st = str(r[0]).encode('ascii', 'replace').decode('ascii')
    print(f'  {st}: {r[1]} (lat {r[2]} to {r[3]})')

# 3. Mining
print("\n--- Mining (ORDER BY COALESCE(firms_detections_1km, 0) DESC, id ASC) ---")
where_min = where_sql + " AND (facility_type = 'MINING' OR LOWER(name) LIKE '%mine%' OR LOWER(master_sector) LIKE '%mining%')"
query_min = f'''
    SELECT state, count(*), min(latitude), max(latitude) FROM (
        SELECT state, latitude, longitude FROM industrial_facilities 
        WHERE {where_min} 
        ORDER BY COALESCE(firms_detections_1km, 0) DESC, id ASC
        LIMIT 200
    ) GROUP BY state ORDER BY count(*) DESC
'''
cur.execute(query_min, box)
for r in cur.fetchall():
    st = str(r[0]).encode('ascii', 'replace').decode('ascii')
    print(f'  {st}: {r[1]} (lat {r[2]} to {r[3]})')
