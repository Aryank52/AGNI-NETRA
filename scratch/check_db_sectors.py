import sqlite3
from collections import Counter

conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()

rows = cur.execute("SELECT facility_type, master_sector FROM industrial_facilities").fetchall()
print(f"Total facilities in DB: {len(rows)}")
types = Counter([r[0] for r in rows])
print("\nAll facility types in DB:")
for t, c in types.most_common(15):
    print(f"  {t}: {c}")

sectors = Counter([r[1] for r in rows])
print("\nAll sectors in DB:")
for s, c in sectors.most_common(15):
    print(f"  {s}: {c}")
