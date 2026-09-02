import psycopg2

conn = psycopg2.connect('postgresql://postgres:projectdatabase_2026@localhost:5432/agni_netra')
cur = conn.cursor()
cur.execute("""
    SELECT indexname, indexdef 
    FROM pg_indexes 
    WHERE tablename = 'thermal_detections';
""")
rows = cur.fetchall()
print(f"Indexes on thermal_detections: {len(rows)}")
for r in rows:
    print(f"  {r[0]}: {r[1]}")
conn.close()
