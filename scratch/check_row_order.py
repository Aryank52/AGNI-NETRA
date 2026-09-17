import sqlite3

conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()

cur.execute('SELECT rowid, id, name, state, district, latitude, longitude FROM industrial_facilities ORDER BY rowid ASC LIMIT 25')
print("First 25 rowids:")
for r in cur.fetchall():
    st = str(r[3]).encode('ascii', 'replace').decode('ascii')
    print(f"  rowid {r[0]}: {r[1][:8]} | {st} - {r[4]} | lat={r[5]}, lon={r[6]}")

cur.execute('SELECT rowid, id, name, state, district, latitude, longitude FROM industrial_facilities ORDER BY rowid DESC LIMIT 25')
print("\nLast 25 rowids:")
for r in cur.fetchall():
    st = str(r[3]).encode('ascii', 'replace').decode('ascii')
    print(f"  rowid {r[0]}: {r[1][:8]} | {st} - {r[4]} | lat={r[5]}, lon={r[6]}")
