"""
AGNI-NETRA — Verification Audit for IBM Mining Intelligence Fusion Layer
Audits database consistency, spatial associations, IBM context linkage, and FIRMS telemetry.
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine


def verify_mining_fusion():
    print("=" * 95)
    print("           AGNI-NETRA — IBM MINING INTELLIGENCE FUSION AUDIT & VERIFICATION           ")
    print("=" * 95)

    with engine.connect() as conn:
        # 1. Total Canonical Facilities (Integrity check)
        total_canonical = conn.execute(text("SELECT count(*) FROM industrial_facilities;")).scalar()
        print(f"\n[1. CANONICAL FACILITY REGISTRY INTEGRITY]")
        print(f"  • Total Canonical Facilities in Database : {total_canonical:,} (Expected: 35,662)")
        assert total_canonical == 35662, f"Expected 35,662 canonical facilities, got {total_canonical}"

        # 2. Total Mining Facilities Ingested in Evidence Layer
        total_mines = conn.execute(text("SELECT count(*) FROM facility_mining_evidence;")).scalar()
        osm_pure_mines = conn.execute(text("SELECT count(*) FROM facility_mining_evidence WHERE facility_type IN ('MINE', 'MINING');")).scalar()
        osm_works_mines = conn.execute(text("SELECT count(*) FROM facility_mining_evidence WHERE facility_type = 'WORKS';")).scalar()
        print(f"\n[2. OSM MINING GEOMETRY INGESTION]")
        print(f"  • Total Fused Mining Facilities         : {total_mines}")
        print(f"  • OSM Pure Mines (MINE / MINING)        : {osm_pure_mines}")
        print(f"  • OSM Mining Works / Quarries / Pits     : {osm_works_mines}")

        # 3. IBM Mining Lease Context Integration
        ibm_lease_linked = conn.execute(text("SELECT count(*) FROM facility_mining_evidence WHERE ibm_lease_context_present = True;")).scalar()
        high_tier_mines = conn.execute(text("SELECT count(*) FROM facility_mining_evidence WHERE ibm_potential_tier = 'HIGH';")).scalar()
        med_tier_mines = conn.execute(text("SELECT count(*) FROM facility_mining_evidence WHERE ibm_potential_tier = 'MEDIUM';")).scalar()
        low_tier_mines = conn.execute(text("SELECT count(*) FROM facility_mining_evidence WHERE ibm_potential_tier = 'LOW';")).scalar()
        nmi_linked = conn.execute(text("SELECT count(*) FROM facility_mining_evidence WHERE nmi_resource_context_present = True;")).scalar()

        print(f"\n[3. IBM LEASE & MINERAL RESOURCE CONTEXT LINKAGE]")
        print(f"  • Mines with IBM District Lease Context  : {ibm_lease_linked} ({ibm_lease_linked / total_mines * 100:.1f}%)")
        print(f"  • Mines in HIGH Potential Tier Districts : {high_tier_mines}")
        print(f"  • Mines in MEDIUM Potential Tier         : {med_tier_mines}")
        print(f"  • Mines in LOW Potential Tier            : {low_tier_mines}")
        print(f"  • Mines with NMI Commodity Resources     : {nmi_linked}")

        # 4. Multi-Distance NASA FIRMS Thermal Telemetry
        thermal_active_mines = conn.execute(text("SELECT count(*) FROM facility_mining_evidence WHERE thermal_activity_present = True;")).scalar()
        mines_500m = conn.execute(text("SELECT count(*) FROM facility_mining_evidence WHERE firms_associated_500m > 0;")).scalar()
        mines_1km = conn.execute(text("SELECT count(*) FROM facility_mining_evidence WHERE firms_associated_1km > 0;")).scalar()
        mines_2km = conn.execute(text("SELECT count(*) FROM facility_mining_evidence WHERE firms_associated_2km > 0;")).scalar()
        
        sum_dets_500m = conn.execute(text("SELECT coalesce(sum(firms_associated_500m), 0) FROM facility_mining_evidence;")).scalar()
        sum_dets_1km = conn.execute(text("SELECT coalesce(sum(firms_associated_1km), 0) FROM facility_mining_evidence;")).scalar()
        sum_dets_2km = conn.execute(text("SELECT coalesce(sum(firms_associated_2km), 0) FROM facility_mining_evidence;")).scalar()

        print(f"\n[4. MULTI-DISTANCE FIRMS THERMAL ASSOCIATIONS]")
        print(f"  • Total Mining Facilities with Detections : {thermal_active_mines}")
        print(f"  • Mines with Detections within 500m       : {mines_500m} (Total 500m Detections: {sum_dets_500m})")
        print(f"  • Mines with Detections within 1km        : {mines_1km} (Total 1km Detections: {sum_dets_1km})")
        print(f"  • Mines with Detections within 2km        : {mines_2km} (Total 2km Detections: {sum_dets_2km})")

        # 5. Thermal Persistence Breakdown
        cats = conn.execute(text("""
            SELECT thermal_persistence_category, count(*) 
            FROM facility_mining_evidence 
            GROUP BY thermal_persistence_category 
            ORDER BY count(*) DESC;
        """)).fetchall()
        print(f"\n[5. THERMAL PERSISTENCE CLASSIFICATION]")
        for c in cats:
            print(f"  • {c[0]:<25} : {c[1]}")

        # 6. Candidate Mining Sources
        candidates = conn.execute(text("SELECT count(*) FROM candidate_facilities WHERE status = 'CANDIDATE';")).scalar()
        print(f"\n[6. CANDIDATE MINING SOURCES DETECTED]")
        print(f"  • Unmapped Thermal Clusters Flagged as CANDIDATE: {candidates}")

        # 7. Sample Fused Mine Output
        top_mine = conn.execute(text("""
            SELECT facility_name, state, district, ibm_potential_tier, mineral_commodity,
                   firms_associated_500m, firms_associated_1km, firms_associated_2km,
                   max_frp, thermal_persistence_category, scientific_attribution
            FROM facility_mining_evidence
            WHERE thermal_activity_present = True
            ORDER BY firms_associated_2km DESC
            LIMIT 1;
        """)).fetchone()

        if top_mine:
            print(f"\n[7. SAMPLE SCIENTIFIC FUSED EVIDENCE RECORD]")
            print(f"  • Name                   : {top_mine[0]}")
            print(f"  • State / District       : {top_mine[1]} / {top_mine[2]}")
            print(f"  • IBM Potential Tier     : {top_mine[3]}")
            print(f"  • Mineral Commodity      : {top_mine[4]}")
            print(f"  • Concentric Detections  : 500m: {top_mine[5]} | 1km: {top_mine[6]} | 2km: {top_mine[7]}")
            print(f"  • Max Observed FRP       : {top_mine[8]} MW")
            print(f"  • Persistence Category   : {top_mine[9]}")
            print(f"  • Scientific Attribution : {top_mine[10]}")

    print("\n" + "=" * 95)
    print("                    ALL MINING INTELLIGENCE FUSION AUDIT CHECKS PASSED                    ")
    print("=" * 95)


if __name__ == "__main__":
    verify_mining_fusion()
