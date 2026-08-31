"""
AGNI-NETRA — IBM Mining Intelligence Fusion Pipeline
Synthesizes OSM mining geometry, IBM lease context, IBM mineral resources, and NASA FIRMS thermal telemetry.
"""

import sys
import os
import json
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine

COMMODITY_MAP = {
    "coal": "Coal",
    "iron": "Iron Ore",
    "iron ore": "Iron Ore",
    "hematite": "Iron Ore (Heamatite)",
    "magnetite": "Iron Ore (Magnetite)",
    "limestone": "Limestone",
    "lime": "Limestone",
    "bauxite": "Bauxite",
    "manganese": "Manganese Ore",
    "gold": "Gold",
    "copper": "Copper",
    "lead": "Lead-Zinc",
    "zinc": "Lead-Zinc",
    "silver": "Silver",
    "diamond": "Diamond",
    "chromite": "Chromite",
    "vermiculite": "Vermiculite",
    "kyanite": "Kyanite",
    "graphite": "Graphite",
    "dolomite": "Dolomite",
    "quartz": "Quartz",
    "granite": "Granite",
    "sand": "Moulding Sand"
}


STATE_CLEAN_MAP = {
    "chhattisgar": "Chhattisgarh",
    "chhattisgarh": "Chhattisgarh",
    "maharasht": "Maharashtra",
    "maharashtra": "Maharashtra",
    "andhra pra": "Andhra Pradesh",
    "andhra pradesh": "Andhra Pradesh",
    "madhya pr": "Madhya Pradesh",
    "madhya pradesh": "Madhya Pradesh",
    "west beng": "West Bengal",
    "west bengal": "West Bengal",
    "uttar prad": "Uttar Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "karnataka": "Karnataka",
    "tamil nadu": "Tamil Nadu",
    "kerala": "Kerala",
    "delhi": "Delhi",
    "gujarat": "Gujarat",
    "odisha": "Odisha",
    "rajasthan": "Rajasthan",
    "punjab": "Punjab",
    "himachal pradesh": "Himachal Pradesh",
    "uttarakhand": "Uttarakhand",
    "bihar": "Bihar",
    "jharkhand": "Jharkhand",
    "telangana": "Telangana",
    "assam": "Assam",
    "jammu & kashmir": "Jammu & Kashmir",
    "jammu & k": "Jammu & Kashmir",
    "goa": "Goa",
    "meghalaya": "Meghalaya",
    "sikkim": "Sikkim",
    "tripura": "Tripura",
    "manipur": "Manipur",
    "puducherry": "Puducherry",
    "lakshadwe": "Lakshadweep",
}


def normalize_state_name(st: Optional[str]) -> Optional[str]:
    if not st:
        return None
    key = st.strip().lower()
    return STATE_CLEAN_MAP.get(key, st.strip().title())


def detect_commodity_from_name_and_tags(name: str, meta: Dict[str, Any]) -> Optional[str]:
    text_to_search = f"{name or ''} {meta.get('resource', '')} {meta.get('substance', '')} {meta.get('mineral', '')} {meta.get('operator', '')}".lower()
    for kw, comm in COMMODITY_MAP.items():
        if kw in text_to_search:
            return comm
    return None


def run_mining_intelligence_fusion():
    print("=" * 90, flush=True)
    print("      AGNI-NETRA — EXECUTING MINING INTELLIGENCE FUSION PIPELINE      ", flush=True)
    print("=" * 90, flush=True)

    with engine.connect() as conn:
        # Step 1: Identify all OSM mines and mining-related objects
        print("\n[STEP 1: IDENTIFYING OSM MINING OBJECTS]...", flush=True)
        facilities = conn.execute(text("""
            SELECT 
                id, name, facility_type, source, source_id,
                state, district, latitude, longitude, source_metadata,
                ST_AsGeoJSON(geom) as geojson
            FROM industrial_facilities
            WHERE facility_type IN ('MINE', 'MINING')
               OR (facility_type = 'WORKS' AND (
                   lower(name) LIKE '%mine%' OR lower(name) LIKE '%quarry%' OR lower(name) LIKE '%colliery%' 
                   OR lower(source_metadata::text) LIKE '%mine%' OR lower(source_metadata::text) LIKE '%quarry%'
               ))
            ORDER BY facility_type ASC, name ASC;
        """)).fetchall()

        print(f"  -> Identified {len(facilities)} target mining facilities for intelligence fusion.", flush=True)

        # Step 2: Load Reference IBM Context & NMI Resources for fast in-memory lookup
        print("\n[STEP 2: LOADING IBM LEASE & NMI CONTEXT DICTIONARIES]...", flush=True)
        ibm_dist_rows = conn.execute(text("""
            SELECT state, district, sum(lease_count) as total_leases, sum(lease_area_ha) as total_area,
                   json_agg(json_build_object('mineral', mineral, 'leases', lease_count, 'area_ha', lease_area_ha)) as minerals
            FROM ibm_mining_lease_context
            WHERE table_number = 'Table-3' AND district IS NOT NULL
            GROUP BY state, district;
        """)).fetchall()

        ibm_district_map = {}
        for r in ibm_dist_rows:
            st = normalize_state_name(r[0]).lower() if r[0] else ""
            dist = (r[1] or "").strip().lower()
            ibm_district_map[(st, dist)] = {
                "leases": r[2],
                "area_ha": r[3],
                "minerals": r[4]
            }

        # Load state-level summary from Table 1 / Table 2
        ibm_state_rows = conn.execute(text("""
            SELECT state, sum(lease_count) as total_leases, sum(lease_area_ha) as total_area
            FROM ibm_mining_lease_context
            WHERE table_number IN ('Table-1', 'Table-2', 'Table-3') AND state IS NOT NULL AND state != 'All India'
            GROUP BY state;
        """)).fetchall()

        ibm_state_map = {}
        for r in ibm_state_rows:
            st = normalize_state_name(r[0]).lower() if r[0] else ""
            ibm_state_map[st] = {
                "leases": r[1],
                "area_ha": r[2]
            }

        ibm_tiers = conn.execute(text("""
            SELECT state, district, potential_category, lease_count, lease_area_ha
            FROM ibm_mining_lease_context
            WHERE table_number IN ('Table-4', 'Table-5', 'Table-6') AND potential_category IS NOT NULL;
        """)).fetchall()

        tier_map = {}
        for r in ibm_tiers:
            st = normalize_state_name(r[0]).lower() if r[0] else ""
            dist = (r[1] or "").strip().lower() if r[1] else None
            tier_map[(st, dist)] = r[2]

        nmi_rows = conn.execute(text("""
            SELECT commodity, mineral, unit, reserves, remaining_resources, total_resources
            FROM ibm_mineral_resources;
        """)).fetchall()

        nmi_map = {}
        for r in nmi_rows:
            comm_key = (r[0] or "").strip().lower()
            nmi_map[comm_key] = {
                "commodity": r[0],
                "mineral": r[1],
                "unit": r[2],
                "reserves": r[3],
                "resources": r[5]
            }

        # Step 3: Clear existing evidence tables for clean rebuild
        print("\n[STEP 3: REBUILDING EVIDENCE TABLES]...", flush=True)
        with engine.begin() as wconn:
            wconn.execute(text("TRUNCATE TABLE facility_mining_evidence CASCADE;"))
            wconn.execute(text("TRUNCATE TABLE mining_thermal_associations CASCADE;"))

        # Step 4: Process each mining facility with spatial join against thermal_detections
        print("\n[STEP 4: FUSING SPATIAL GEOMETRY, IBM CONTEXT, AND FIRMS DETECTIONS]...", flush=True)
        evidence_records = []
        association_records = []
        candidate_count = 0

        for idx, fac in enumerate(facilities):
            fac_id = fac[0]
            fac_name = fac[1]
            fac_type = fac[2]
            source_id = fac[4]
            state_val = normalize_state_name(fac[5])
            dist_val = fac[6]
            lat = fac[7]
            lon = fac[8]
            meta = fac[9] or {}

            # Administrative spatial enrichment if missing or unspecified
            admin_source = "OSM_ORIGINAL"
            if not state_val or state_val == "National / Unspecified" or state_val == "National":
                # KNN spatial lookup against known geocoded facilities in DB
                admin_nn = conn.execute(text("""
                    SELECT state, district
                    FROM industrial_facilities
                    WHERE state IS NOT NULL AND state != 'National / Unspecified'
                    ORDER BY ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) <-> ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                    LIMIT 1;
                """), {"lon": lon, "lat": lat}).fetchone()

                if admin_nn:
                    state_val = normalize_state_name(admin_nn[0])
                    dist_val = admin_nn[1]
                    admin_source = "SPATIAL_PROXIMITY_ENRICHMENT"
                else:
                    state_val = "National Territory"
                    admin_source = "NATIONAL_UNSPECIFIED"

            # Commodity detection
            detected_comm = detect_commodity_from_name_and_tags(fac_name, meta)

            # IBM Mining Lease Context Lookup
            st_key = (state_val or "").strip().lower()
            dist_key = (dist_val or "").strip().lower() if dist_val else ""
            
            ibm_data = ibm_district_map.get((st_key, dist_key))
            ibm_tier = tier_map.get((st_key, dist_key)) or tier_map.get((st_key, None)) or "LOW"
            
            if ibm_data:
                ibm_present = True
                ibm_leases = ibm_data["leases"]
                ibm_area = ibm_data["area_ha"]
                ibm_minerals = ibm_data["minerals"]
            elif st_key in ibm_state_map:
                ibm_present = True
                ibm_leases = ibm_state_map[st_key]["leases"]
                ibm_area = ibm_state_map[st_key]["area_ha"]
                ibm_minerals = []
            else:
                ibm_present = False
                ibm_leases = None
                ibm_area = None
                ibm_minerals = []

            # NMI Resource Context Lookup
            nmi_data = None
            if detected_comm:
                nmi_data = nmi_map.get(detected_comm.lower())
            
            nmi_present = nmi_data is not None
            nmi_reserves = nmi_data["reserves"] if nmi_data else None
            nmi_resources = nmi_data["resources"] if nmi_data else None
            nmi_unit = nmi_data["unit"] if nmi_data else None

            # Multi-distance FIRMS thermal observations query using B-Tree index bounding box pre-filter + exact geography calculation
            deg_buffer = 0.022  # ~2.4 km bounding box buffer
            detections_query = text("""
                SELECT 
                    acq_timestamp, frp, confidence, day_night,
                    ST_Distance(
                        ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                    ) as dist_m
                FROM thermal_detections
                WHERE latitude BETWEEN :min_lat AND :max_lat
                  AND longitude BETWEEN :min_lon AND :max_lon
                  AND ST_DWithin(
                      ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                      ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                      2000
                  )
                ORDER BY acq_timestamp ASC;
            """)
            
            dets = conn.execute(detections_query, {
                "lon": lon, "lat": lat,
                "min_lat": lat - deg_buffer, "max_lat": lat + deg_buffer,
                "min_lon": lon - deg_buffer, "max_lon": lon + deg_buffer
            }).fetchall()

            # Partition into 500m, 1km, 2km
            dets_500m = [d for d in dets if d[4] <= 500]
            dets_1km = [d for d in dets if d[4] <= 1000]
            dets_2km = dets

            cnt_500m = len(dets_500m)
            cnt_1km = len(dets_1km)
            cnt_2km = len(dets_2km)

            first_seen = dets_2km[0][0] if dets_2km else None
            last_seen = dets_2km[-1][0] if dets_2km else None
            
            frps_2km = [float(d[1]) for d in dets_2km if d[1] is not None]
            confs_2km = [float(d[2]) for d in dets_2km if d[2] is not None]
            
            mean_frp = float(np.mean(frps_2km)) if frps_2km else None
            med_frp = float(np.median(frps_2km)) if frps_2km else None
            p90_frp = float(np.percentile(frps_2km, 90)) if frps_2km else None
            p99_frp = float(np.percentile(frps_2km, 99)) if frps_2km else None
            max_frp = float(np.max(frps_2km)) if frps_2km else None

            # Calculate active dates recurrence
            active_dates = set(d[0].date() for d in dets_2km if d[0])
            active_days_count = len(active_dates)

            # Thermal persistence category
            if active_days_count >= 5 and cnt_2km >= 10:
                persistence_cat = "HIGH_PERSISTENCE"
            elif cnt_2km >= 3:
                persistence_cat = "MODERATE_PERSISTENCE"
            elif cnt_2km >= 1:
                persistence_cat = "EPISODIC_ACTIVITY"
            else:
                persistence_cat = "NO_THERMAL_ACTIVITY"

            # Scientific explainable attribution statement
            has_thermal = cnt_2km > 0
            comm_desc = f"{detected_comm}" if detected_comm else "Unspecified mineral"
            district_desc = f"{dist_val}, {state_val}" if dist_val and state_val != 'National / Unspecified' else "National Territory"
            
            if has_thermal:
                attr_statement = (
                    f"Thermal activity ({cnt_2km} detections within 2km, {active_days_count} active dates) is spatially "
                    f"associated with a mining context supported by OSM facility '{fac_name}' and IBM {district_desc} "
                    f"records (Potential Tier: {ibm_tier})."
                )
                if nmi_present and nmi_resources:
                    attr_statement += f" National Mineral Inventory (NMI) resources for {comm_desc}: {nmi_resources:,.2f} {nmi_unit}."
            else:
                attr_statement = (
                    f"OSM mining facility '{fac_name}' located in {district_desc} (IBM Potential Tier: {ibm_tier}). "
                    f"No active FIRMS thermal detections observed within 2km."
                )

            evidence_summary = {
                "osm_mining_geometry": "PRESENT",
                "ibm_lease_context": "PRESENT" if ibm_present else "ABSENT",
                "ibm_potential_tier": ibm_tier,
                "mineral_detected": detected_comm,
                "nmi_resource_context": "PRESENT" if nmi_present else "ABSENT",
                "thermal_detections_500m": cnt_500m,
                "thermal_detections_1km": cnt_1km,
                "thermal_detections_2km": cnt_2km,
                "active_days_recurrence": active_days_count,
                "persistence_status": persistence_cat,
                "mean_frp_mw": round(mean_frp, 2) if mean_frp else None,
                "max_frp_mw": round(max_frp, 2) if max_frp else None,
                "scientific_interpretation": attr_statement
            }

            # Confidence score calculation
            conf = 0.50
            if ibm_present: conf += 0.15
            if detected_comm: conf += 0.10
            if cnt_500m > 0: conf += 0.15
            elif cnt_1km > 0: conf += 0.10
            elif cnt_2km > 0: conf += 0.05
            if active_days_count >= 5: conf += 0.10

            evidence_records.append({
                "facility_id": fac_id,
                "facility_name": fac_name,
                "facility_type": fac_type,
                "osm_object_id": source_id,
                "osm_object_type": meta.get("type", "way"),
                "operator": meta.get("operator"),
                "mineral_commodity": detected_comm,
                "state": state_val,
                "district": dist_val,
                "administrative_source": admin_source,
                "latitude": lat,
                "longitude": lon,
                "ibm_lease_context_present": ibm_present,
                "ibm_district_lease_count": ibm_leases,
                "ibm_district_lease_area_ha": ibm_area,
                "ibm_potential_tier": ibm_tier,
                "ibm_district_minerals": json.dumps(ibm_minerals),
                "nmi_resource_context_present": nmi_present,
                "nmi_commodity_reserves": nmi_reserves,
                "nmi_commodity_resources": nmi_resources,
                "nmi_commodity_unit": nmi_unit,
                "firms_associated_500m": cnt_500m,
                "firms_associated_1km": cnt_1km,
                "firms_associated_2km": cnt_2km,
                "first_thermal_seen": first_seen,
                "last_thermal_seen": last_seen,
                "active_days_count": active_days_count,
                "mean_frp": mean_frp,
                "median_frp": med_frp,
                "p90_frp": p90_frp,
                "p99_frp": p99_frp,
                "max_frp": max_frp,
                "mining_context_present": True,
                "mining_geometry_present": True,
                "thermal_activity_present": has_thermal,
                "thermal_persistence_category": persistence_cat,
                "confidence_score": round(min(conf, 0.99), 2),
                "scientific_attribution": attr_statement,
                "evidence_summary": json.dumps(evidence_summary)
            })

            # Record detailed distance bands
            for band_name, band_dets in [("500m", dets_500m), ("1km", dets_1km), ("2km", dets_2km)]:
                if band_dets:
                    b_frps = [float(d[1]) for d in band_dets if d[1] is not None]
                    b_confs = [float(d[2]) for d in band_dets if d[2] is not None]
                    b_active = len(set(d[0].date() for d in band_dets if d[0]))
                    b_first = band_dets[0][0]
                    b_last = band_dets[-1][0]
                    p_days = (b_last - b_first).days if b_first and b_last else 0
                    day_c = sum(1 for d in band_dets if d[3] == 'D')
                    night_c = sum(1 for d in band_dets if d[3] == 'N')

                    association_records.append({
                        "facility_id": fac_id,
                        "distance_band": band_name,
                        "detection_count": len(band_dets),
                        "first_seen": b_first,
                        "last_seen": b_last,
                        "active_days_count": b_active,
                        "mean_frp": float(np.mean(b_frps)) if b_frps else None,
                        "median_frp": float(np.median(b_frps)) if b_frps else None,
                        "p90_frp": float(np.percentile(b_frps, 90)) if b_frps else None,
                        "p99_frp": float(np.percentile(b_frps, 99)) if b_frps else None,
                        "max_frp": float(np.max(b_frps)) if b_frps else None,
                        "mean_confidence": float(np.mean(b_confs)) if b_confs else None,
                        "day_detection_count": day_c,
                        "night_detection_count": night_c,
                        "recurrence_rate": round(b_active / len(band_dets), 4) if band_dets else 0,
                        "persistence_days": p_days
                    })

            # Step 5: Candidate Mining Source Generation
            # If persistent cluster (>= 5 detections across >= 3 dates) exists near mining geometry without an explicit named facility
            if has_thermal and active_days_count >= 3 and cnt_1km >= 5 and "n.e.c." in fac_name.lower():
                candidate_label = f"Candidate-Mining-Source-{state_val[:3].upper()}-{idx+1:03d}"
                cand_p_days = (last_seen - first_seen).days if first_seen and last_seen else 1
                with engine.begin() as wconn:
                    wconn.execute(text("""
                        INSERT INTO candidate_facilities (
                            id, name_label, status, latitude, longitude,
                            state, district, industrial_context_score,
                            persistence_days, detection_count,
                            first_detected_at, last_detected_at,
                            evidence_summary
                        ) VALUES (
                            gen_random_uuid()::text, :name_label, 'CANDIDATE', :lat, :lon,
                            :state, :district, :context_score,
                            :persistence_days, :detection_count,
                            :first_detected_at, :last_detected_at,
                            CAST(:evidence_summary AS json)
                        )
                        ON CONFLICT DO NOTHING;
                    """), {
                        "name_label": candidate_label,
                        "lat": lat,
                        "lon": lon,
                        "state": state_val or "National Territory",
                        "district": dist_val,
                        "context_score": 0.85,
                        "persistence_days": max(1, cand_p_days),
                        "detection_count": cnt_1km,
                        "first_detected_at": first_seen,
                        "last_detected_at": last_seen,
                        "evidence_summary": json.dumps({
                            "evidence": "Persistent thermal cluster near unnamed OSM mining geometry",
                            "observation_count_1km": cnt_1km,
                            "active_days_count": active_days_count,
                            "ibm_potential_tier": ibm_tier,
                            "status": "CANDIDATE_UNVERIFIED"
                        })
                    })
                candidate_count += 1

        # Step 6: Write to facility_mining_evidence and mining_thermal_associations
        print(f"\n[STEP 5: INSERTING {len(evidence_records)} EVIDENCE RECORDS & {len(association_records)} ASSOCIATION RECORDS]...", flush=True)
        insert_ev_sql = text("""
            INSERT INTO facility_mining_evidence (
                facility_id, facility_name, facility_type, osm_object_id, osm_object_type,
                operator, mineral_commodity, state, district, administrative_source,
                latitude, longitude,
                ibm_lease_context_present, ibm_district_lease_count, ibm_district_lease_area_ha,
                ibm_potential_tier, ibm_district_minerals,
                nmi_resource_context_present, nmi_commodity_reserves, nmi_commodity_resources,
                nmi_commodity_unit,
                firms_associated_500m, firms_associated_1km, firms_associated_2km,
                first_thermal_seen, last_thermal_seen, active_days_count,
                mean_frp, median_frp, p90_frp, p99_frp, max_frp,
                mining_context_present, mining_geometry_present, thermal_activity_present,
                thermal_persistence_category, confidence_score, scientific_attribution,
                evidence_summary
            ) VALUES (
                :facility_id, :facility_name, :facility_type, :osm_object_id, :osm_object_type,
                :operator, :mineral_commodity, :state, :district, :administrative_source,
                :latitude, :longitude,
                :ibm_lease_context_present, :ibm_district_lease_count, :ibm_district_lease_area_ha,
                :ibm_potential_tier, CAST(:ibm_district_minerals AS jsonb),
                :nmi_resource_context_present, :nmi_commodity_reserves, :nmi_commodity_resources,
                :nmi_commodity_unit,
                :firms_associated_500m, :firms_associated_1km, :firms_associated_2km,
                :first_thermal_seen, :last_thermal_seen, :active_days_count,
                :mean_frp, :median_frp, :p90_frp, :p99_frp, :max_frp,
                :mining_context_present, :mining_geometry_present, :thermal_activity_present,
                :thermal_persistence_category, :confidence_score, :scientific_attribution,
                CAST(:evidence_summary AS jsonb)
            );
        """)

        insert_assoc_sql = text("""
            INSERT INTO mining_thermal_associations (
                facility_id, distance_band, detection_count, first_seen, last_seen,
                active_days_count, mean_frp, median_frp, p90_frp, p99_frp, max_frp,
                mean_confidence, day_detection_count, night_detection_count,
                recurrence_rate, persistence_days
            ) VALUES (
                :facility_id, :distance_band, :detection_count, :first_seen, :last_seen,
                :active_days_count, :mean_frp, :median_frp, :p90_frp, :p99_frp, :max_frp,
                :mean_confidence, :day_detection_count, :night_detection_count,
                :recurrence_rate, :persistence_days
            );
        """)

        with engine.begin() as wconn:
            for ev in evidence_records:
                wconn.execute(insert_ev_sql, ev)
            for assoc in association_records:
                wconn.execute(insert_assoc_sql, assoc)

            # Update industrial_facilities multi-distance counts
            wconn.execute(text("""
                UPDATE industrial_facilities f
                SET 
                    firms_detections_500m = e.firms_associated_500m,
                    firms_detections_1km = e.firms_associated_1km,
                    firms_detections_2km = e.firms_associated_2km
                FROM facility_mining_evidence e
                WHERE f.id = e.facility_id;
            """))

        print(f"\n[AGNI-NETRA] Mining Intelligence Fusion Complete!", flush=True)
        print(f"  • Total Mining Facilities Processed    : {len(evidence_records)}", flush=True)
        print(f"  • Multi-Distance Associations Ingested : {len(association_records)}", flush=True)
        print(f"  • Candidate Mining Sources Created    : {candidate_count}", flush=True)


if __name__ == "__main__":
    run_mining_intelligence_fusion()
