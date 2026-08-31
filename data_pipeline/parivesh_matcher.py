"""
AGNI-NETRA — Batch-Optimized Inverted Index Entity Resolution Engine for PARIVESH
Sub-second matching with batch database updates and strict mutually exclusive category accounting.
"""

import os
import sys
import re
import json
import time
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple, Set

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from backend.app.core.database import engine


PROPONENT_EXPANSIONS = {
    "RELIANCE": ["reliance", "ril"],
    "NTPC": ["ntpc"],
    "TATA STEEL": ["tata steel"],
    "TATA POWER": ["tata power"],
    "JSW": ["jsw"],
    "JSPL": ["jspl", "jindal steel"],
    "SAIL": ["sail"],
    "IOCL": ["iocl", "indian oil"],
    "BPCL": ["bpcl"],
    "HPCL": ["hpcl"],
    "ONGC": ["ongc"],
    "SECL": ["secl", "south eastern coalfields"],
    "NCL": ["ncl", "northern coalfields"],
    "NMDC": ["nmdc"],
    "GFL": ["gfl", "fluorochemicals"],
    "UPL": ["upl"],
    "ESSAR": ["essar", "gsegl"],
    "BHUSHAN": ["bhushan"]
}

STOP_WORDS = {
    "project", "limited", "ltd", "pvt", "corp", "corporation", "india", "complex",
    "expansion", "unit", "plant", "works", "phase", "stage", "mod", "modernization",
    "installation", "upgrade", "operation", "compliance", "environmental", "captive",
    "integrated", "enterprise", "industrial", "synthetic", "organic", "chemicals",
    "industries", "industry", "estate", "manufacturing", "ferrous", "non"
}


def extract_tokens(text_val: Optional[str]) -> Set[str]:
    if not text_val:
        return set()
    clean = re.sub(r"[^a-zA-Z0-9\s]+", " ", str(text_val).lower())
    return {t.strip() for t in clean.split() if len(t.strip()) >= 3 and t.strip() not in STOP_WORDS}


def run_parivesh_matching():
    print("=" * 80, flush=True)
    print("   AGNI-NETRA — PARIVESH MULTI-SIGNAL ENTITY RESOLUTION ENGINE   ", flush=True)
    print("=" * 80, flush=True)

    start_time = time.time()

    # 1. Load all staged PARIVESH records
    with engine.connect() as conn:
        parivesh_rows = conn.execute(text("""
            SELECT id, proposal_id, project_name, project_type, proponent,
                   state, district, category, sector, clearance_type, clearance_status,
                   proposal_date, decision_date, forest_related_flag, wildlife_related_flag,
                   crz_related_flag, latitude, longitude, raw_metadata
            FROM parivesh_projects_staging
            ORDER BY id;
        """)).fetchall()

    total_parivesh = len(parivesh_rows)
    print(f"[AGNI-NETRA] Loaded {total_parivesh:,} staged PARIVESH clearance records to evaluate.", flush=True)

    # 2. Load candidate canonical industrial facilities & Pre-compute token sets
    with engine.connect() as conn:
        fac_rows = conn.execute(text("""
            SELECT id, name, industry_name, company_name, facility_type,
                   state, district, latitude, longitude, confidence, verification_status,
                   source, source_record_id, source_metadata
            FROM industrial_facilities
            ORDER BY id;
        """)).fetchall()

    facilities = []
    token_inverted_index = defaultdict(list)

    for idx, r in enumerate(fac_rows):
        fac_text = f"{r[1] or ''} {r[2] or ''} {r[3] or ''} {r[6] or ''}".lower()
        fac_tokens = extract_tokens(fac_text)
        fac_obj = {
            "id": r[0],
            "name": r[1],
            "industry_name": r[2],
            "company_name": r[3],
            "facility_type": (r[4] or "").upper(),
            "state": (r[5] or "").lower(),
            "district": (r[6] or "").lower(),
            "latitude": r[7],
            "longitude": r[8],
            "confidence": r[9],
            "verification_status": r[10],
            "source": r[11],
            "source_record_id": r[12],
            "source_metadata": r[13],
            "tokens": fac_tokens,
            "text": fac_text
        }
        facilities.append(fac_obj)

        for t in fac_tokens:
            token_inverted_index[t].append(idx)

    print(f"[AGNI-NETRA] Pre-compiled {len(facilities):,} facilities with {len(token_inverted_index):,} unique inverted tokens.", flush=True)

    high_matches = []
    medium_matches = []
    low_matches = []
    unmatched_records = []

    matched_fac_ids = set()

    for p in parivesh_rows:
        p_dict = {
            "id": p[0],
            "proposal_id": p[1],
            "project_name": p[2],
            "project_type": p[3],
            "proponent": p[4],
            "state": p[5],
            "district": p[6],
            "category": p[7],
            "sector": p[8],
            "clearance_type": p[9],
            "clearance_status": p[10],
            "proposal_date": p[11],
            "decision_date": p[12],
            "forest_related_flag": p[13],
            "wildlife_related_flag": p[14],
            "crz_related_flag": p[15],
            "latitude": p[16],
            "longitude": p[17],
            "raw_metadata": p[18]
        }

        p_name = p_dict["project_name"]
        p_prop = (p_dict["proponent"] or "").lower()
        p_st = (p_dict["state"] or "").lower()
        p_dist = (p_dict["district"] or "").lower()
        p_sec = (p_dict["sector"] or "").lower()
        p_lat = p_dict["latitude"]
        p_lon = p_dict["longitude"]

        p_tokens = extract_tokens(p_name)
        prop_tokens = extract_tokens(p_prop)
        dist_tokens = extract_tokens(p_dist)

        search_tokens = p_tokens | prop_tokens | dist_tokens

        candidate_indices: Set[int] = set()
        for t in search_tokens:
            if t in token_inverted_index:
                candidate_indices.update(token_inverted_index[t])

        # Proponent aliases
        p_prop_str = (p_dict["proponent"] or "").lower()
        for key, aliases in PROPONENT_EXPANSIONS.items():
            if any(alias in p_prop_str for alias in aliases):
                for alias in aliases:
                    for at in alias.split():
                        if at in token_inverted_index:
                            candidate_indices.update(token_inverted_index[at])

        best_fac = None
        best_score = 0.0
        best_reasons = []

        for idx in candidate_indices:
            fac = facilities[idx]
            fac_tokens = fac["tokens"]
            fac_st = fac["state"]
            fac_type = fac["facility_type"]

            score = 0.0
            reasons = []

            # 1. Token overlap
            matching_tokens = p_tokens & fac_tokens
            if p_tokens:
                ratio = len(matching_tokens) / len(p_tokens)
                if ratio >= 0.6:
                    score += 45.0
                    reasons.append(f"Strong token match: {list(matching_tokens)[:3]}")
                elif ratio >= 0.3:
                    score += 30.0
                    reasons.append(f"Moderate token match: {list(matching_tokens)[:3]}")
                elif any(len(k) >= 5 and k in fac_tokens for k in p_tokens):
                    score += 20.0
                    reasons.append("Distinctive keyword match")

            # 2. State match
            if p_st and fac_st and p_st != "national / unspecified" and fac_st != "national / unspecified":
                if p_st == fac_st or p_st in fac_st or fac_st in p_st:
                    score += 25.0
                    reasons.append("State match")
                else:
                    score -= 35.0
                    reasons.append("State mismatch")
            elif p_st and p_st != "national / unspecified":
                score += 10.0

            # 3. District match
            if p_dist and fac["district"]:
                if p_dist == fac["district"] or p_dist in fac["district"] or fac["district"] in p_dist:
                    score += 15.0
                    reasons.append("District match")

            # 4. Proponent match
            if p_prop:
                for key, aliases in PROPONENT_EXPANSIONS.items():
                    if any(alias in p_prop for alias in aliases):
                        if any(alias in fac["text"] for alias in aliases):
                            score += 20.0
                            reasons.append(f"Proponent match ({key})")
                            break

            # 5. Type match
            if "thermal" in p_sec or "power" in p_name.lower():
                if fac_type == "POWER_PLANT":
                    score += 10.0
                    reasons.append("Type match (POWER_PLANT)")
            elif "petroleum" in p_name.lower() or "refinery" in p_name.lower():
                if fac_type == "REFINERY":
                    score += 10.0
                    reasons.append("Type match (REFINERY)")
            elif "steel" in p_name.lower() or "metallurgical" in p_sec:
                if fac_type in ["STEEL_PLANT", "WORKS", "FACILITY"]:
                    score += 10.0
                    reasons.append("Type match (METALLURGY/STEEL)")
            elif "mining" in p_sec or "mine" in p_name.lower():
                if fac_type == "MINE":
                    score += 10.0
                    reasons.append("Type match (MINE)")

            # 6. Spatial proximity
            if p_lat is not None and p_lon is not None and fac["latitude"] is not None and fac["longitude"] is not None:
                if abs(p_lat - fac["latitude"]) <= 0.05 and abs(p_lon - fac["longitude"]) <= 0.05:
                    score += 20.0
                    reasons.append("Spatial proximity (<5km)")

            final_score = max(0.0, min(100.0, score))
            if final_score > best_score:
                best_score = final_score
                best_fac = fac
                best_reasons = reasons

        # Mutually exclusive categorization
        if best_score >= 75.0 and best_fac:
            high_matches.append((p_dict, best_fac, best_score, best_reasons))
            matched_fac_ids.add(best_fac["id"])
        elif best_score >= 55.0 and best_fac:
            medium_matches.append((p_dict, best_fac, best_score, best_reasons))
            matched_fac_ids.add(best_fac["id"])
        elif best_score >= 35.0 and best_fac:
            low_matches.append((p_dict, best_fac, best_score, best_reasons))
        else:
            unmatched_records.append((p_dict, None, best_score, best_reasons))

    # Verify Mutually Exclusive Sum Identity
    sum_categories = len(high_matches) + len(medium_matches) + len(low_matches) + len(unmatched_records)
    print(f"\n[AGNI-NETRA] Mutually Exclusive Matching Results:", flush=True)
    print(f"   • HIGH Confidence Matches   : {len(high_matches):,}", flush=True)
    print(f"   • MEDIUM Confidence Matches : {len(medium_matches):,}", flush=True)
    print(f"   • LOW Confidence (Filtered) : {len(low_matches):,}", flush=True)
    print(f"   • UNMATCHED Records         : {len(unmatched_records):,}", flush=True)
    print(f"   • TOTAL Evaluated           : {sum_categories:,} (Exact Match: {sum_categories == total_parivesh})", flush=True)
    assert sum_categories == total_parivesh, "Categories must sum to total evaluated records"

    # 3. Batch Update parivesh_projects_staging with match statuses
    print(f"\n[AGNI-NETRA] [Step 1/2] Batch updating match metadata in parivesh_projects_staging...", flush=True)
    update_staging_query = text("""
        UPDATE parivesh_projects_staging
        SET match_status = :status,
            matched_facility_id = :fac_id,
            match_confidence = :confidence,
            match_score = :score,
            match_reasons = CAST(:reasons AS JSONB)
        WHERE id = :staging_id;
    """)

    staging_params = []
    for p_dict, fac, score, reasons in high_matches:
        staging_params.append({
            "staging_id": p_dict["id"],
            "status": "HIGH",
            "fac_id": fac["id"],
            "confidence": "HIGH",
            "score": round(score, 2),
            "reasons": json.dumps(reasons)
        })
    for p_dict, fac, score, reasons in medium_matches:
        staging_params.append({
            "staging_id": p_dict["id"],
            "status": "MEDIUM",
            "fac_id": fac["id"],
            "confidence": "MEDIUM",
            "score": round(score, 2),
            "reasons": json.dumps(reasons)
        })
    for p_dict, fac, score, reasons in low_matches:
        staging_params.append({
            "staging_id": p_dict["id"],
            "status": "LOW",
            "fac_id": None,
            "confidence": "LOW",
            "score": round(score, 2),
            "reasons": json.dumps(reasons)
        })
    for p_dict, _, score, reasons in unmatched_records:
        staging_params.append({
            "staging_id": p_dict["id"],
            "status": "UNMATCHED",
            "fac_id": None,
            "confidence": None,
            "score": round(score, 2),
            "reasons": json.dumps(reasons)
        })

    with engine.begin() as conn:
        conn.execute(update_staging_query, staging_params)

    # 4. Batch Enrich matched facilities in industrial_facilities
    print(f"[AGNI-NETRA] [Step 2/2] Batch enriching {len(high_matches) + len(medium_matches):,} matched canonical facilities in DB...", flush=True)
    update_fac_query = text("""
        UPDATE industrial_facilities
        SET environmental_clearance_present = TRUE,
            ec_proposal_id = :proposal_id,
            ec_clearance_type = :clearance_type,
            ec_clearance_status = :clearance_status,
            ec_category = :category,
            ec_decision_date = :decision_date,
            forest_related_flag = :forest_flag,
            wildlife_related_flag = :wildlife_flag,
            crz_related_flag = :crz_flag,
            verification_status = CASE WHEN geom IS NOT NULL THEN 'VERIFIED' ELSE 'PROVISIONAL' END,
            source_metadata = CAST(:combined_metadata AS JSONB),
            last_updated = NOW() AT TIME ZONE 'UTC'
        WHERE id = :fac_id;
    """)

    fac_params = []
    for p_dict, fac, score, reasons in (high_matches + medium_matches):
        conf = "HIGH" if score >= 75.0 else "MEDIUM"
        existing_meta = fac.get("source_metadata") or {}
        if isinstance(existing_meta, str):
            try:
                existing_meta = json.loads(existing_meta)
            except Exception:
                existing_meta = {}

        combined_meta = {
            **existing_meta,
            "parivesh_enrichment": {
                "proposal_id": p_dict["proposal_id"],
                "project_name": p_dict["project_name"],
                "project_type": p_dict["project_type"],
                "proponent": p_dict["proponent"],
                "state": p_dict["state"],
                "category": p_dict["category"],
                "sector": p_dict["sector"],
                "clearance_type": p_dict["clearance_type"],
                "clearance_status": p_dict["clearance_status"],
                "decision_date": p_dict["decision_date"],
                "forest_related": p_dict["forest_related_flag"],
                "wildlife_related": p_dict["wildlife_related_flag"],
                "crz_related": p_dict["crz_related_flag"],
                "match_confidence": conf,
                "match_score": round(score, 2),
                "match_reasons": reasons,
                "source_url": "https://parivesh.nic.in"
            }
        }

        fac_params.append({
            "fac_id": fac["id"],
            "proposal_id": p_dict["proposal_id"],
            "clearance_type": p_dict["clearance_type"],
            "clearance_status": p_dict["clearance_status"],
            "category": p_dict["category"],
            "decision_date": p_dict["decision_date"],
            "forest_flag": p_dict["forest_related_flag"],
            "wildlife_flag": p_dict["wildlife_related_flag"],
            "crz_flag": p_dict["crz_related_flag"],
            "combined_metadata": json.dumps(combined_meta)
        })

    with engine.begin() as conn:
        conn.execute(update_fac_query, fac_params)

    elapsed = time.time() - start_time
    print(f"\n[AGNI-NETRA] PARIVESH Entity Resolution & Enrichment completed in {elapsed:.2f} seconds.", flush=True)


if __name__ == "__main__":
    run_parivesh_matching()
