import sqlite3

conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()

cur.execute("SELECT id, name, state, district, latitude, longitude FROM industrial_facilities WHERE LOWER(name) LIKE '%reliance%'")
for r in cur.fetchall():
    print(r)
