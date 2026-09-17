import sqlite3
import sys

conn = sqlite3.connect('agni_netra.db')
cur = conn.cursor()
rows = cur.execute("SELECT state, count(1) FROM industrial_facilities WHERE id LIKE 'osm_relation_%' GROUP BY state ORDER BY count(1) DESC LIMIT 15").fetchall()
for r in rows:
    sys.stdout.buffer.write(f"  {r[0]}: {r[1]}\n".encode('utf-8'))
