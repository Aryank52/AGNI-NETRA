import sqlite3

conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()

cur.execute("""
    SELECT state, count(*), min(latitude), max(latitude), min(longitude), max(longitude)
    FROM industrial_facilities
    GROUP BY state
    ORDER BY count(*) DESC
""")
rows = cur.fetchall()
print("Facilities by state:")
for r in rows:
    safe_state = str(r[0]).encode('ascii', 'replace').decode('ascii')
    print(f"  {safe_state}: {r[1]} facilities (lat: {r[2]} to {r[3]}, lon: {r[4]} to {r[5]})")

# Check facilities near southern tip / Sri Lanka
cur.execute("""
    SELECT id, name, facility_type, state, district, latitude, longitude
    FROM industrial_facilities
    WHERE latitude < 10.0
    LIMIT 10
""")
southern = cur.fetchall()
print("\nRepresentative southern tip facilities (lat < 10.0):")
for s in southern:
    safe_name = str(s[1]).encode('ascii', 'replace').decode('ascii')
    safe_state = str(s[3]).encode('ascii', 'replace').decode('ascii')
    print(f"  {safe_name} | {safe_state} - {s[4]} | lat={s[5]}, lon={s[6]}")
