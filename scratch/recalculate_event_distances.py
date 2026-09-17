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

updates = []
for ev in events:
    eid, code, elat, elon, old_dist, old_status = ev
    min_d = float('inf')
    best_fac = None
    for f in facs:
        d = haversine(elat, elon, f[2], f[3])
        if d < min_d:
            min_d = d
            best_fac = f
    
    new_dist = round(min_d, 1)
    if new_dist <= 500.0:
        new_status = 'ON_SITE'
    elif new_dist <= 2500.0:
        new_status = 'PROXIMATE'
    else:
        new_status = 'REMOTE'
    
    updates.append((new_dist, new_status, eid, code, old_dist, old_status, best_fac[1]))

print(f"Total events to update: {len(updates)}")
for u in updates[:15]:
    name = str(u[6]).encode('ascii', 'replace').decode('ascii')
    print(f"  {u[3]}: dist {u[4]}m -> {u[0]}m | status {u[5]} -> {u[1]} | Nearest: {name}")

# Perform update
for u in updates:
    cur.execute("UPDATE thermal_events SET nearest_facility_distance_m = ?, facility_status = ? WHERE id = ?", (u[0], u[1], u[2]))

conn.commit()
print("Successfully committed updated nearest_facility_distance_m and facility_status to thermal_events!")
