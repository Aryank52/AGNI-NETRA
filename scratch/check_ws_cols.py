import sys
sys.path.insert(0, r"E:\PROJECTS\AGNI-NETRA")
try:
    from backend.app.core.database import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    res = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'investigation_workspaces' ORDER BY ordinal_position;"))
    for r in res:
        print(f"{r[0]}: {r[1]}")
    db.close()
except Exception as e:
    import traceback
    traceback.print_exc()
