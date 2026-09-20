"""
Database Migration: Proactive Fire Prevention & Root-Cause Intelligence Extension
Creates normalized tables:
- prevention_cases
- root_cause_hypotheses
- prevention_recommendations
- authority_directory
- prevention_reports
- report_delivery_audits

Seeds verified authority directory records for Gujarat (Jamnagar), Madhya Pradesh, and National bodies.
"""

import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.database import engine, SessionLocal, IS_SQLITE_TEST, IS_POSTGRESQL
from backend.app.models.domain import Base, AuthorityDirectoryRecord

def migrate():
    print(f"[*] Starting Proactive Prevention Database Migration (IS_SQLITE_TEST={IS_SQLITE_TEST}, IS_POSTGRESQL={IS_POSTGRESQL})...")
    
    # Create all tables registered in Base metadata that do not exist yet
    Base.metadata.create_all(bind=engine)
    print("[+] Base.metadata.create_all completed successfully.")

    # Seed authoritative Indian authorities into authority_directory
    db = SessionLocal()
    try:
        existing_count = db.query(AuthorityDirectoryRecord).count()
        if existing_count == 0:
            print("[*] Seeding verified regulatory, administrative, and emergency authorities...")
            now = datetime.now(timezone.utc)
            initial_authorities = [
                AuthorityDirectoryRecord(
                    id=str(uuid.uuid4()),
                    name="Jamnagar Fire & Emergency Services (JMC Fire Brigade)",
                    category="LOCAL_FIRE_SERVICE",
                    state="Gujarat",
                    district="Jamnagar",
                    jurisdiction="Jamnagar District & Industrial Corridors",
                    contact_role="Chief Fire Officer (CFO)",
                    official_endpoint="https://mcjamnagar.com/fire-services",
                    is_verified=True,
                    created_at=now
                ),
                AuthorityDirectoryRecord(
                    id=str(uuid.uuid4()),
                    name="Office of the District Magistrate & Collector - Jamnagar",
                    category="DISTRICT_ADMINISTRATION",
                    state="Gujarat",
                    district="Jamnagar",
                    jurisdiction="Jamnagar Revenue District",
                    contact_role="District Collector & District Magistrate",
                    official_endpoint="https://jamnagar.nic.in",
                    is_verified=True,
                    created_at=now
                ),
                AuthorityDirectoryRecord(
                    id=str(uuid.uuid4()),
                    name="Gujarat State Disaster Management Authority (GSDMA)",
                    category="STATE_DISASTER_MANAGEMENT",
                    state="Gujarat",
                    district=None,
                    jurisdiction="State of Gujarat",
                    contact_role="State Emergency Operation Centre (SEOC) Coordinator",
                    official_endpoint="https://gsdma.org",
                    is_verified=True,
                    created_at=now
                ),
                AuthorityDirectoryRecord(
                    id=str(uuid.uuid4()),
                    name="Gujarat Pollution Control Board (GPCB) - Jamnagar Regional Office",
                    category="POLLUTION_CONTROL_AUTHORITY",
                    state="Gujarat",
                    district="Jamnagar",
                    jurisdiction="Jamnagar & Devbhumi Dwarka Region",
                    contact_role="Regional Officer, GPCB Jamnagar",
                    official_endpoint="https://gpcb.gujarat.gov.in",
                    is_verified=True,
                    created_at=now
                ),
                AuthorityDirectoryRecord(
                    id=str(uuid.uuid4()),
                    name="Directorate of Industrial Safety & Health (DISH) - Gujarat",
                    category="INDUSTRIAL_SAFETY_AUTHORITY",
                    state="Gujarat",
                    district="Jamnagar",
                    jurisdiction="Industrial Safety & Hazardous Operations Zone",
                    contact_role="Joint Director of Industrial Safety and Health",
                    official_endpoint="https://dish.gujarat.gov.in",
                    is_verified=True,
                    created_at=now
                ),
                AuthorityDirectoryRecord(
                    id=str(uuid.uuid4()),
                    name="Petroleum and Explosives Safety Organization (PESO) - West Circle",
                    category="INDUSTRIAL_SAFETY_AUTHORITY",
                    state="Gujarat",
                    district="Jamnagar",
                    jurisdiction="Petrochemical, Refinery & Explosives Storage Infrastructure",
                    contact_role="Joint Chief Controller of Explosives (JCCE)",
                    official_endpoint="https://peso.gov.in",
                    is_verified=True,
                    created_at=now
                ),
                AuthorityDirectoryRecord(
                    id=str(uuid.uuid4()),
                    name="Jamnagar Municipal Corporation (JMC) - Disaster Cell",
                    category="MUNICIPAL_LOCAL_BODY",
                    state="Gujarat",
                    district="Jamnagar",
                    jurisdiction="Jamnagar Municipal Corporation Limits",
                    contact_role="Municipal Commissioner / Disaster In-Charge",
                    official_endpoint="https://mcjamnagar.com",
                    is_verified=True,
                    created_at=now
                ),
                AuthorityDirectoryRecord(
                    id=str(uuid.uuid4()),
                    name="Reliance Jamnagar Mega Refinery - Incident Management & Safety Cell",
                    category="FACILITY_OPERATOR",
                    state="Gujarat",
                    district="Jamnagar",
                    jurisdiction="Motikhavdi Refinery Complex On-Site Operations",
                    contact_role="Vice President - Health, Safety & Environment (HSE)",
                    official_endpoint="internal://jamnagar-hse.ril.net",
                    is_verified=True,
                    created_at=now
                ),
                AuthorityDirectoryRecord(
                    id=str(uuid.uuid4()),
                    name="Madhya Pradesh State Disaster Management Authority (MPSDMA)",
                    category="STATE_DISASTER_MANAGEMENT",
                    state="Madhya Pradesh",
                    district=None,
                    jurisdiction="State of Madhya Pradesh",
                    contact_role="Executive Director, MPSDMA",
                    official_endpoint="https://sdma.mp.gov.in",
                    is_verified=True,
                    created_at=now
                ),
                AuthorityDirectoryRecord(
                    id=str(uuid.uuid4()),
                    name="National Disaster Management Authority (NDMA) - Ministry of Home Affairs",
                    category="STATE_DISASTER_MANAGEMENT",
                    state="National",
                    district=None,
                    jurisdiction="Republic of India",
                    contact_role="Duty Officer, Control Room NDMA",
                    official_endpoint="https://ndma.gov.in",
                    is_verified=True,
                    created_at=now
                )
            ]
            db.add_all(initial_authorities)
            db.commit()
            print(f"[+] Successfully seeded {len(initial_authorities)} verified authority records.")
        else:
            print(f"[*] Authority directory already contains {existing_count} records. Skipping seed.")
    finally:
        db.close()

    print("[*] Proactive Prevention Database Migration Completed.")

if __name__ == "__main__":
    migrate()
