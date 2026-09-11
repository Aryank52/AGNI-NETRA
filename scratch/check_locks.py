import psycopg2

conn = psycopg2.connect("postgresql://postgres:projectdatabase_2026@127.0.0.1:5432/agni_netra")
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
    SELECT pid, state, wait_event_type, wait_event, query_start, query
    FROM pg_stat_activity
    WHERE datname = 'agni_netra' AND pid <> pg_backend_pid();
""")
rows = cur.fetchall()
print(f"Active connections: {len(rows)}")
for r in rows:
    print(f"PID {r[0]} | State: {r[1]} | Wait: {r[2]}:{r[3]} | Started: {r[4]} | Query: {r[5][:80] if r[5] else 'None'}")

cur.close()
conn.close()
