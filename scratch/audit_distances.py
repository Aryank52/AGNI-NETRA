import sqlite3, math

conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

cur.execute("SELECT id, name, latitude, longitude FROM industrial_facilities WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
facs = cur.fetchall()

cur.execute("SELECT id, event_code, latitude, longitude, nearest_facility_distance_m, facility_status FROM thermal_events")
events = cur.fetchall()

discrepancies = []
for ev in events:
    eid, code, elat, elon, stored_dist, status = ev
    min_d = float('inf')
    best_fac = None
    for f in facs:
        d = haversine(elat, elon, f[2], f[3])
        if d < min_d:
            min_d = d
            best_fac = f
    
    diff = abs(min_d - (stored_dist or 0))
    if diff > 50.0:
        discrepancies.append((code, elat, elon, stored_dist, round(min_d, 1), best_fac[1]))

print(f"Total events: {len(events)}, Discrepant distances: {len(discrepancies)}")
for d in discrepancies[:10]:
    name = str(d[5]).encode('ascii', 'replace').decode('ascii')
    print(f"  {d[0]}: stored={d[3]}m vs actual={d[4]}m (Nearest: {name})")
