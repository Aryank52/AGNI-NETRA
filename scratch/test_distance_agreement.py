import sqlite3
import math

conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()

# Find EVT-GUJ-20260916-150D
cur.execute("SELECT id, event_code, latitude, longitude, nearest_facility_distance_m, facility_status FROM thermal_events WHERE event_code = 'EVT-GUJ-20260916-150D'")
evt = cur.fetchone()
print("Event from DB:", evt)

if evt:
    evt_id, code, e_lat, e_lon, db_dist, fac_status = evt
    
    # Haversine formula
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000.0 # meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    # Find closest facility in industrial_facilities
    cur.execute("SELECT id, name, latitude, longitude FROM industrial_facilities WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    facs = cur.fetchall()
    min_dist = float('inf')
    best_fac = None
    for f in facs:
        fid, fname, flat, flon = f
        d = haversine(e_lat, e_lon, flat, flon)
        if d < min_dist:
            min_dist = d
            best_fac = (fid, fname, flat, flon)

    print(f"Nearest facility in DB: {best_fac[1]} at ({best_fac[2]}, {best_fac[3]})")
    print(f"Calculated Haversine Distance: {min_dist:.1f} m")
    print(f"Stored DB Distance: {db_dist:.1f} m")
    diff = abs(min_dist - db_dist)
    print(f"Difference: {diff:.1f} m (Agreement: {diff < 50.0})")
