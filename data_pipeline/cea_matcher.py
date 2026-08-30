"""
AGNI-NETRA — Multi-Signal Entity Resolution & CEA Power Station Matcher
Matches aggregated CEA power projects against the OSM Industrial Facility Registry.
Enriches matched OSM power facilities with CEA capacity, prime mover, and unit details,
and registers unmatched CEA facilities as non-geolocated canonical entries.
"""

import os
import sys
import re
import json
import uuid
import time
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from backend.app.core.database import engine
from data_pipeline.osm_classifier import normalize_name, normalize_state


# Organization Acronym mappings
ORG_EXPANSIONS = {
    "NTPC": ["ntpc", "national thermal power corporation"],
    "NHPC": ["nhpc", "national hydroelectric power corporation"],
    "NPCIL": ["npcil", "nuclear power corporation of india"],
    "NEEPCO": ["neepco", "north eastern electric power corporation"],
    "SJVNL": ["sjvn", "satluj jal vidyut nigam"],
    "THDC": ["thdc", "tehri hydro development corporation"],
    "DVC": ["dvc", "damodar valley corporation"],
    "BBMB": ["bbmb", "bhakra beas management board"],
    "RRVUNL": ["rrvunl", "rajasthan rajya vidyut utpadan nigam", "rvunl"],
    "MAHAGENCO": ["mahagenco", "maharashtra state power generation", "mspgcl"],
    "GSECL": ["gsecl", "gujarat state electricity corporation"],
    "KPCL": ["kpcl", "karnataka power corporation"],
    "APGENCO": ["apgenco", "andhra pradesh power generation"],
    "TSGENCO": ["tsgenco", "telangana state power generation"],
    "TANGEDCO": ["tangedco", "tamil nadu generation and distribution", "tneb"],
    "UPRVUNL": ["uprvunl", "uttar pradesh rajya vidyut utpadan nigam"],
    "PSPCL": ["pspcl", "punjab state power corporation", "pseb"],
    "HPGCL": ["hpgcl", "haryana power generation"],
    "WBPDCL": ["wbpdcl", "west bengal power development corporation"],
    "OPGC": ["opgc", "odisha power generation corporation"],
    "OHPC": ["ohpc", "odisha hydro power corporation"],
    "CSPGCL": ["cspgcl", "chhattisgarh state power generation"],
    "MPPGCL": ["mppgcl", "madhya pradesh power generating company"],
    "APL": ["adani", "adani power"],
    "TPC": ["tata power", "tata"],
    "JSWEL": ["jsw", "jsw energy"],
    "BEPL": ["bajaj energy", "bepl"]
}


STOP_WORDS = {
    "tps", "stps", "stpp", "tpp", "ccpp", "hps", "hep", "aps", "npp", "dpp",
    "power", "station", "plant", "project", "limited", "ltd", "pvt", "corp",
    "thermal", "hydro", "atomic", "electric", "house", "stage", "phase",
    "i", "ii", "iii", "iv", "v", "vi", "1", "2", "3", "4", "5", "unit", "units",
    "extension", "extn", "combined", "cycle", "gas", "steam", "solar"
}


def extract_core_keywords(name: str) -> List[str]:
    """
    Extracts informative keywords from a power station project name.
    """
    if not name:
        return []
    clean = re.sub(r"[^a-zA-Z0-9\s]+", " ", name.lower())
    tokens = [t.strip() for t in clean.split() if len(t.strip()) >= 3 and t.strip() not in STOP_WORDS]
    return tokens


def score_project_match(
    cea_proj: Dict[str, Any],
    osm_fac: Dict[str, Any]
) -> Tuple[float, List[str]]:
    """
    Scores similarity between a CEA project and an OSM facility.
    Returns (score [0-100], match_reasons).
    """
    score = 0.0
    reasons = []

    cea_name = (cea_proj.get("project_name") or "").lower()
    osm_name = (osm_fac.get("name") or "").lower()
    osm_ind_name = (osm_fac.get("industry_name") or "").lower()
    osm_operator = (osm_fac.get("company_name") or osm_fac.get("operator") or "").lower()
    osm_metadata = osm_fac.get("source_metadata") or {}
    if isinstance(osm_metadata, str):
        try:
            osm_metadata = json.loads(osm_metadata)
        except Exception:
            osm_metadata = {}

    cea_keywords = extract_core_keywords(cea_name)
    osm_text = f"{osm_name} {osm_ind_name} {osm_operator} {osm_metadata.get('name', '')} {osm_metadata.get('operator', '')}".lower()
    osm_tokens = set(extract_core_keywords(osm_text))

    # 1. Name Core Keyword Overlap
    if cea_keywords:
        matching_kw = [k for k in cea_keywords if k in osm_text or any(k in t or t in k for t in osm_tokens)]
        kw_ratio = len(matching_kw) / len(cea_keywords)
        if kw_ratio >= 1.0:
            score += 50.0
            reasons.append(f"Complete keyword match: {matching_kw}")
        elif kw_ratio >= 0.5:
            score += 35.0
            reasons.append(f"Partial keyword match: {matching_kw}")
        elif any(len(k) >= 5 and k in osm_text for k in cea_keywords):
            score += 25.0
            reasons.append(f"Distinctive keyword match")

    # 2. State Alignment
    cea_state = (cea_proj.get("state") or "").lower()
    osm_state = (osm_fac.get("state") or "").lower()
    if cea_state and osm_state and cea_state != "national / unspecified" and osm_state != "national / unspecified":
        if cea_state == osm_state or cea_state in osm_state or osm_state in cea_state:
            score += 25.0
            reasons.append(f"State match ({cea_proj.get('state')})")
        else:
            # Penalize state mismatch
            score -= 30.0
            reasons.append("State mismatch")
    elif cea_state and cea_state != "national / unspecified":
        score += 10.0  # Mild bonus if OSM state is unassigned

    # 3. Organisation / Operator Alignment
    cea_org = (cea_proj.get("organisation") or "").upper()
    if cea_org:
        matched_org = False
        org_aliases = ORG_EXPANSIONS.get(cea_org, [cea_org.lower()])
        for alias in org_aliases:
            if alias in osm_operator or alias in osm_text:
                score += 20.0
                reasons.append(f"Operator match ({cea_org})")
                matched_org = True
                break
        if not matched_org and osm_operator and len(osm_operator) > 3:
            # Mild score if no direct conflict
            pass

    # 4. Facility Classification & Prime Mover Compatibility
    fac_type = osm_fac.get("facility_type")
    if fac_type == "POWER_PLANT":
        score += 10.0
        reasons.append("Type match (POWER_PLANT)")

    pm = (cea_proj.get("prime_mover") or "").lower()
    if "solar" in osm_text and "solar" not in pm:
        # Penalize matching a thermal CEA plant with a solar farm
        score -= 25.0

    return max(0.0, min(100.0, score)), reasons


def aggregate_cea_staging_records() -> List[Dict[str, Any]]:
    """
    Loads unit records from `cea_power_stations_staging` and aggregates them per project.
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, cea_record_id, page_number, s_no, region, state, sector,
                   organisation, project_name, prime_mover, unit_no,
                   installed_capacity_mw, year_of_commissioning, raw_row_text
            FROM cea_power_stations_staging
            ORDER BY page_number, id;
        """)).fetchall()

    projects_map = defaultdict(lambda: {
        "region": None,
        "state": None,
        "sector": None,
        "organisation": None,
        "project_name": None,
        "prime_mover": None,
        "units": [],
        "total_mw": 0.0,
        "years": []
    })

    for r in rows:
        proj_name = r[8]
        state_val = r[5]
        org_val = r[7]
        key = (proj_name, state_val, org_val)

        p = projects_map[key]
        p["region"] = r[4] or p["region"]
        p["state"] = state_val or p["state"]
        p["sector"] = r[6] or p["sector"]
        p["organisation"] = org_val or p["organisation"]
        p["project_name"] = proj_name
        p["prime_mover"] = r[9] or p["prime_mover"]

        unit_mw = r[11] or 0.0
        p["total_mw"] += unit_mw
        if r[12]:
            p["years"].append(r[12])

        p["units"].append({
            "cea_record_id": r[1],
            "page_number": r[2],
            "unit_no": r[10],
            "installed_capacity_mw": r[11],
            "year_of_commissioning": r[12]
        })

    project_list = []
    for key, p in projects_map.items():
        min_yr = min(p["years"]) if p["years"] else None
        max_yr = max(p["years"]) if p["years"] else None
        project_list.append({
            "project_name": p["project_name"],
            "state": p["state"],
            "region": p["region"],
            "sector": p["sector"],
            "organisation": p["organisation"],
            "prime_mover": p["prime_mover"],
            "unit_count": len(p["units"]),
            "total_installed_capacity_mw": round(p["total_mw"], 2),
            "commissioning_year_min": min_yr,
            "commissioning_year_max": max_yr,
            "units": p["units"]
        })

    print(f"[AGNI-NETRA] Aggregated {len(rows):,} unit rows into {len(project_list):,} unique CEA power projects.")
    return project_list


def run_cea_matching():
    print("=" * 80)
    print("   AGNI-NETRA — CEA & OSM POWER STATION ENTITY RESOLUTION ENGINE   ")
    print("=" * 80)

    start_time = time.time()
    cea_projects = aggregate_cea_staging_records()

    # Load candidate OSM power facilities
    with engine.connect() as conn:
        osm_rows = conn.execute(text("""
            SELECT id, name, industry_name, company_name, facility_type,
                   state, district, city, latitude, longitude, confidence, verification_status,
                   source, source_record_id, source_metadata
            FROM industrial_facilities
            WHERE facility_type = 'POWER_PLANT' 
               OR name ILIKE '%power%' 
               OR name ILIKE '%tps%' 
               OR name ILIKE '%stps%' 
               OR name ILIKE '%thermal%'
               OR name ILIKE '%hydro%'
               OR name ILIKE '%hydel%'
               OR name ILIKE '%station%';
        """)).fetchall()

    osm_candidates = []
    for r in osm_rows:
        osm_candidates.append({
            "id": r[0],
            "name": r[1],
            "industry_name": r[2],
            "company_name": r[3],
            "operator": r[3],
            "facility_type": r[4],
            "state": r[5],
            "district": r[6],
            "city": r[7],
            "latitude": r[8],
            "longitude": r[9],
            "confidence": r[10],
            "verification_status": r[11],
            "source": r[12],
            "source_record_id": r[13],
            "source_metadata": r[14]
        })

    print(f"[AGNI-NETRA] Loaded {len(osm_candidates):,} candidate OSM power facilities for matching.")

    high_matches = []
    medium_matches = []
    low_matches = []
    unmatched_projects = []

    matched_osm_ids = set()

    for proj in cea_projects:
        best_candidate = None
        best_score = 0.0
        best_reasons = []

        for osm_fac in osm_candidates:
            # Don't match the same OSM facility multiple times if already high matched
            if osm_fac["id"] in matched_osm_ids:
                continue

            score, reasons = score_project_match(proj, osm_fac)
            if score > best_score:
                best_score = score
                best_candidate = osm_fac
                best_reasons = reasons

        if best_score >= 75.0 and best_candidate:
            high_matches.append((proj, best_candidate, best_score, best_reasons))
            matched_osm_ids.add(best_candidate["id"])
        elif best_score >= 55.0 and best_candidate:
            medium_matches.append((proj, best_candidate, best_score, best_reasons))
            matched_osm_ids.add(best_candidate["id"])
        elif best_score >= 35.0 and best_candidate:
            low_matches.append((proj, best_candidate, best_score, best_reasons))
            unmatched_projects.append(proj)
        else:
            unmatched_projects.append(proj)

    print(f"\n[AGNI-NETRA] Entity Resolution Results:")
    print(f"   • HIGH Confidence Matches   : {len(high_matches):,}")
    print(f"   • MEDIUM Confidence Matches : {len(medium_matches):,}")
    print(f"   • LOW Confidence (Filtered) : {len(low_matches):,}")
    print(f"   • UNMATCHED CEA Projects    : {len(unmatched_projects):,}")

    # 1. Update Matched Facilities in Database
    print(f"\n[AGNI-NETRA] [Step 1/2] Enriching {len(high_matches) + len(medium_matches):,} matched OSM facilities in DB...")
    
    update_matched_query = text("""
        UPDATE industrial_facilities
        SET plant_capacity = :plant_capacity,
            prime_mover = :prime_mover,
            unit_count = :unit_count,
            commissioning_year_min = :comm_min,
            commissioning_year_max = :comm_max,
            cea_project_name = :cea_project_name,
            cea_organisation = :cea_organisation,
            company_name = COALESCE(company_name, :cea_organisation),
            master_sector = 'Electricity, Gas and Water Supply',
            sub_sector = :sub_sector,
            nic_code = :nic_code,
            industry_type = :industry_type,
            source = 'CEA+OSM',
            confidence = :confidence,
            verification_status = 'VERIFIED',
            source_metadata = CAST(:combined_metadata AS JSONB),
            last_updated = NOW() AT TIME ZONE 'UTC'
        WHERE id = :facility_id;
    """)

    with engine.begin() as conn:
        for proj, osm_fac, score, reasons in (high_matches + medium_matches):
            conf = "HIGH" if score >= 75.0 else "MEDIUM"
            pm = proj["prime_mover"] or "Thermal"
            
            # NIC code mapping
            if "hydro" in pm.lower():
                nic = "35102"
                sub_sec = "Hydro-electric Power Generation"
                ind_type = "Hydro-Electric Power Generation"
            elif "nuclear" in pm.lower():
                nic = "35103"
                sub_sec = "Nuclear Power Generation"
                ind_type = "Nuclear Electric Power Generation"
            elif "gas" in pm.lower():
                nic = "35101"
                sub_sec = "Gas-based Power Generation"
                ind_type = "Gas-based Electric Power Generation"
            else:
                nic = "35101"
                sub_sec = "Thermal Power Generation"
                ind_type = "Thermal Electric Power Generation"

            existing_meta = osm_fac.get("source_metadata") or {}
            if isinstance(existing_meta, str):
                try:
                    existing_meta = json.loads(existing_meta)
                except Exception:
                    existing_meta = {}

            combined_meta = {
                **existing_meta,
                "cea_enrichment": {
                    "project_name": proj["project_name"],
                    "state": proj["state"],
                    "region": proj["region"],
                    "sector": proj["sector"],
                    "organisation": proj["organisation"],
                    "prime_mover": proj["prime_mover"],
                    "unit_count": proj["unit_count"],
                    "total_capacity_mw": proj["total_installed_capacity_mw"],
                    "commissioning_year_min": proj["commissioning_year_min"],
                    "commissioning_year_max": proj["commissioning_year_max"],
                    "match_confidence": conf,
                    "match_score": score,
                    "match_reasons": reasons,
                    "units": proj["units"],
                    "source_document": "List_of_Power_Station_as_on_31.03.2025.pdf"
                }
            }

            conn.execute(update_matched_query, {
                "facility_id": osm_fac["id"],
                "plant_capacity": f"{proj['total_installed_capacity_mw']:,.1f} MW",
                "prime_mover": pm,
                "unit_count": proj["unit_count"],
                "comm_min": proj["commissioning_year_min"],
                "comm_max": proj["commissioning_year_max"],
                "cea_project_name": proj["project_name"],
                "cea_organisation": proj["organisation"],
                "sub_sector": sub_sec,
                "nic_code": nic,
                "industry_type": ind_type,
                "confidence": conf,
                "combined_metadata": json.dumps(combined_meta)
            })

    # 2. Insert Unmatched CEA Facilities as Non-Geolocated Canonical Records
    print(f"\n[AGNI-NETRA] [Step 2/2] Registering {len(unmatched_projects):,} unmatched CEA power stations (geometry=NULL)...")

    insert_unmatched_query = text("""
        INSERT INTO industrial_facilities (
            id, industry_id, name, industry_name, facility_name, plant_name,
            facility_type, status, source, source_id,
            state, district, city, industrial_area,
            latitude, longitude, geom,
            plant_capacity, prime_mover, unit_count,
            commissioning_year_min, commissioning_year_max,
            cea_project_name, cea_organisation, company_name,
            master_sector, sub_sector, nic_code, industry_type,
            operating_status, verification_status, confidence,
            source_record_id, source_file, source_metadata,
            operating_hours, contact_info, last_updated
        ) VALUES (
            :id, :industry_id, :name, :name, :name, :name,
            'POWER_PLANT', 'PROVISIONAL', 'CEA', :source_id,
            :state, NULL, NULL, NULL,
            NULL, NULL, NULL,
            :plant_capacity, :prime_mover, :unit_count,
            :comm_min, :comm_max,
            :cea_project_name, :cea_organisation, :company_name,
            'Electricity, Gas and Water Supply', :sub_sector, :nic_code, :industry_type,
            'OPERATIONAL', 'PROVISIONAL', 'MEDIUM',
            :source_id, 'List_of_Power_Station_as_on_31.03.2025.pdf', CAST(:source_metadata AS JSONB),
            '24x7', jsonb_build_object('organisation', :cea_organisation, 'state', :state),
            NOW() AT TIME ZONE 'UTC'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    with engine.begin() as conn:
        for proj in unmatched_projects:
            fac_uuid = str(uuid.uuid4())
            safe_proj_id = re.sub(r"[^a-zA-Z0-9]+", "_", proj["project_name"]).strip("_")[:40]
            source_id = f"CEA-{safe_proj_id}"
            industry_id = f"FAC-CEA-{safe_proj_id}"

            pm = proj["prime_mover"] or "Thermal"
            if "hydro" in pm.lower():
                nic = "35102"
                sub_sec = "Hydro-electric Power Generation"
                ind_type = "Hydro-Electric Power Generation"
            elif "nuclear" in pm.lower():
                nic = "35103"
                sub_sec = "Nuclear Power Generation"
                ind_type = "Nuclear Electric Power Generation"
            elif "gas" in pm.lower():
                nic = "35101"
                sub_sec = "Gas-based Power Generation"
                ind_type = "Gas-based Electric Power Generation"
            else:
                nic = "35101"
                sub_sec = "Thermal Power Generation"
                ind_type = "Thermal Electric Power Generation"

            cea_meta = {
                "source": "CEA",
                "source_document": "List_of_Power_Station_as_on_31.03.2025.pdf",
                "source_date": "2025-03-31",
                "project_name": proj["project_name"],
                "state": proj["state"],
                "region": proj["region"],
                "sector": proj["sector"],
                "organisation": proj["organisation"],
                "prime_mover": proj["prime_mover"],
                "unit_count": proj["unit_count"],
                "total_capacity_mw": proj["total_installed_capacity_mw"],
                "commissioning_year_min": proj["commissioning_year_min"],
                "commissioning_year_max": proj["commissioning_year_max"],
                "match_status": "UNMATCHED_CEA_CANONICAL",
                "units": proj["units"]
            }

            conn.execute(insert_unmatched_query, {
                "id": fac_uuid,
                "industry_id": industry_id,
                "name": proj["project_name"],
                "source_id": source_id,
                "state": proj["state"] or "National / Unspecified",
                "plant_capacity": f"{proj['total_installed_capacity_mw']:,.1f} MW",
                "prime_mover": pm,
                "unit_count": proj["unit_count"],
                "comm_min": proj["commissioning_year_min"],
                "comm_max": proj["commissioning_year_max"],
                "cea_project_name": proj["project_name"],
                "cea_organisation": proj["organisation"],
                "company_name": proj["organisation"],
                "sub_sector": sub_sec,
                "nic_code": nic,
                "industry_type": ind_type,
                "source_metadata": json.dumps(cea_meta)
            })

    elapsed = time.time() - start_time
    print(f"\n[AGNI-NETRA] CEA Entity Resolution & Registry Update completed in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    run_cea_matching()
