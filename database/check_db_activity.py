import psycopg2

conn = psycopg2.connect('postgresql://postgres:projectdatabase_2026@localhost:5432/agni_netra')
cur = conn.cursor()
cur.execute("SELECT pid, state, wait_event_type, wait_event, query_start, query FROM pg_stat_activity WHERE datname = 'agni_netra' AND pid != pg_backend_pid();")
rows = cur.fetchall()
print(f"Active connections: {len(rows)}")
for r in rows:
    print(f"PID: {r[0]}, State: {r[1]}, Wait: {r[2]}:{r[3]}, Started: {r[4]}\nQuery: {r[5][:100]}\n")

# If any idle in transaction or stuck query exists, terminate them
for r in rows:
    if r[1] in ('idle in transaction', 'active'):
        print(f"Terminating PID {r[0]}...")
        cur.execute("SELECT pg_terminate_backend(%s);", (r[0],))
conn.commit()
conn.close()
print("Cleaned up stale connections.")
