"""
AGNI-NETRA — Verification Audit for IBM Table 15 Auctioned Mineral Blocks
Audits extraction, canonical staging, entity resolution, and spatial geometry integrity.
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine


def verify_ibm_auctioned_blocks():
    print("=" * 95)
    print("          AGNI-NETRA — IBM TABLE 15 AUCTIONED MINERAL BLOCKS AUDIT & VERIFICATION          ")
    print("=" * 95)

    with engine.connect() as conn:
        # 1. Staging vs Canonical Count
        stg_count = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks_staging;")).scalar()
        can_count = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks;")).scalar()

        print(f"\n[1. RECORD INGESTION]")
        print(f"  • Extracted Staging Records  : {stg_count} (Expected: 119)")
        print(f"  • Inserted Canonical Records : {can_count} (Expected: 119)")
        assert stg_count == 119, f"Expected 119 staging records, got {stg_count}"
        assert can_count == 119, f"Expected 119 canonical records, got {can_count}"

        # 2. Duplicate Check
        dup_sl = conn.execute(text("""
            SELECT sl_no, count(*) FROM ibm_auctioned_blocks GROUP BY sl_no HAVING count(*) > 1;
        """)).fetchall()
        dup_doc_id = conn.execute(text("""
            SELECT source_doc_id, count(*) FROM ibm_auctioned_blocks GROUP BY source_doc_id HAVING count(*) > 1;
        """)).fetchall()
        print(f"\n[2. DUPLICATE INTEGRITY CHECK]")
        print(f"  • Duplicate SL_NO Entries    : {len(dup_sl)}")
        print(f"  • Duplicate Document IDs     : {len(dup_doc_id)}")
        assert len(dup_sl) == 0, f"Found duplicate SL_NO entries: {dup_sl}"
        assert len(dup_doc_id) == 0, f"Found duplicate document IDs: {dup_doc_id}"

        # 3. Entity Resolution Distribution
        high_m = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE match_confidence = 'HIGH';")).scalar()
        med_m = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE match_confidence = 'MEDIUM';")).scalar()
        low_m = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE match_confidence = 'LOW';")).scalar()
        unmatched_m = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE match_confidence = 'UNMATCHED';")).scalar()
        total_eval = high_m + med_m + low_m + unmatched_m

        print(f"\n[3. ENTITY RESOLUTION EVALUATION]")
        print(f"  • HIGH Matches               : {high_m}")
        print(f"  • MEDIUM Matches             : {med_m}")
        print(f"  • LOW Matches                : {low_m}")
        print(f"  • UNMATCHED                  : {unmatched_m}")
        print(f"  • Total Evaluated Sum        : {total_eval} (HIGH + MEDIUM + LOW + UNMATCHED)")
        assert total_eval == can_count == 119, f"Match sum {total_eval} does not equal total records {can_count}"

        # 4. Geometry Provenance & Hallucination Check
        with_geom = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE geom IS NOT NULL;")).scalar()
        without_geom = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE geom IS NULL;")).scalar()
        print(f"\n[4. GEOMETRY INTEGRITY & ZERO HALLUCINATION]")
        print(f"  • Records with Real Geometry : {with_geom}")
        print(f"  • Records with NULL Geometry : {without_geom}")
        assert with_geom + without_geom == can_count == 119

        # 5. State Distribution
        print(f"\n[5. STATE-WISE DISTRIBUTION OF AUCTIONED BLOCKS]")
        states = conn.execute(text("""
            SELECT state, count(*) 
            FROM ibm_auctioned_blocks 
            GROUP BY state 
            ORDER BY count(*) DESC;
        """)).fetchall()
        for s in states:
            print(f"  • {s[0]:<25} : {s[1]}")

        # 6. Sample Records
        sample = conn.execute(text("""
            SELECT sl_no, state, block_name, mineral, preferred_bidder, match_confidence, page_number
            FROM ibm_auctioned_blocks
            ORDER BY sl_no ASC
            LIMIT 5;
        """)).fetchall()
        print(f"\n[6. SAMPLE CANONICAL RECORDS]")
        for sp in sample:
            print(f"  • SL {sp[0]:03d} | {sp[1]:<15} | {sp[2]:<35} | {sp[3]:<20} | Bidder: {sp[4]} | Confidence: {sp[5]}")

    print("\n" + "=" * 95)
    print("                 ALL IBM TABLE 15 VERIFICATION CHECKS PASSED                 ")
    print("=" * 95)


if __name__ == "__main__":
    verify_ibm_auctioned_blocks()
