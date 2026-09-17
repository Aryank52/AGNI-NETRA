import sqlite3, math

conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

cur.execute("SELECT id, name, latitude, longitude FROM industrial_facilities WHERE LOWER(district) = 'jamnagar'")
rows = cur.fetchall()
print(f"Total Jamnagar facilities: {len(rows)}")
for r in rows:
    d = haversine(22.3542, 69.8644, r[2], r[3])
    print(f"  {r[1]} at ({r[2]}, {r[3]}): {d:.1f} m (id={r[0]})")
