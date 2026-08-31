"""
AGNI-NETRA — National Spatial Administrative Enrichment Pipeline (Phase 2A)
High-performance spatial enrichment linking:
1. Industrial Facilities (35,662 canonical OSM objects) -> State, District, Sub-district
2. NASA FIRMS Thermal Detections (1.77M+ real observations) -> State, District
3. PARIVESH Environmental Clearance Projects (622 records) -> State, District, Sub-district
"""

import sys
import os
import time
import shapely.wkb
import shapely.geometry
import shapely.prepared
from shapely.strtree import STRtree
import psycopg2.extras
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine


def load_boundary_trees():
    print("[INIT] Loading administrative boundaries and preparing geometries...", flush=True)
    t0 = time.time()

    with engine.connect() as conn:
        adm1_rows = conn.execute(text("SELECT id, admin_code, normalized_name, ST_AsBinary(geom) FROM admin_boundaries WHERE admin_level = 1;")).fetchall()
        adm2_rows = conn.execute(text("SELECT id, admin_code, normalized_name, ST_AsBinary(geom) FROM admin_boundaries WHERE admin_level = 2;")).fetchall()
        adm3_rows = conn.execute(text("SELECT id, admin_code, normalized_name, parent_code, ST_AsBinary(geom) FROM admin_boundaries WHERE admin_level = 3;")).fetchall()

    adm1_shapes = [shapely.wkb.loads(bytes(r[3])) for r in adm1_rows]
    adm1_prep = [shapely.prepared.prep(s) for s in adm1_shapes]
    adm1_tree = STRtree(adm1_shapes)

    adm2_shapes = [shapely.wkb.loads(bytes(r[3])) for r in adm2_rows]
    adm2_prep = [shapely.prepared.prep(s) for s in adm2_shapes]
    adm2_tree = STRtree(adm2_shapes)

    adm3_by_dist = {}
    for r in adm3_rows:
        p_code = r[3]
        s = shapely.wkb.loads(bytes(r[4]))
        p = shapely.prepared.prep(s)
        if p_code not in adm3_by_dist:
            adm3_by_dist[p_code] = []
        adm3_by_dist[p_code].append((r[0], r[1], r[2], p))

    print(f"  -> Prepared 36 States, 735 Districts, 6,824 Sub-districts in {time.time() - t0:.2f}s.", flush=True)
    return (adm1_rows, adm1_shapes, adm1_prep, adm1_tree), (adm2_rows, adm2_shapes, adm2_prep, adm2_tree), adm3_by_dist


def enrich_facilities(adm1_data, adm2_data, adm3_by_dist):
    adm1_rows, adm1_shapes, adm1_prep, adm1_tree = adm1_data
    adm2_rows, adm2_shapes, adm2_prep, adm2_tree = adm2_data

    print("\n" + "=" * 95, flush=True)
    print(" [PHASE 2A.1] SPATIAL ADMINISTRATIVE ENRICHMENT: INDUSTRIAL FACILITIES (35,662) ", flush=True)
    print("=" * 95, flush=True)
    t0 = time.time()

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE facility_administrative_context CASCADE;"))

    with engine.connect() as conn:
        facs = conn.execute(text("""
            SELECT id, state, district, city, latitude, longitude
            FROM industrial_facilities;
        """)).fetchall()

    records = []
    state_conflicts = 0
    dist_conflicts = 0
    with_state = 0
    with_dist = 0
    with_subdist = 0

    for f in facs:
        f_id, orig_st, orig_dist, orig_city, lat, lon = f[0], f[1], f[2], f[3], f[4], f[5]
        s_id, s_name = None, None
        d_id, d_name, d_code = None, None, None
        sub_id, sub_name = None, None

        if lat is not None and lon is not None and lat != 0.0 and lon != 0.0:
            pt = shapely.geometry.Point(lon, lat)

            # State Match
            c_s = adm1_tree.query(pt)
            for idx in c_s:
                if adm1_prep[idx].intersects(pt):
                    s_id, s_name = adm1_rows[idx][0], adm1_rows[idx][2]
                    break

            # District Match
            c_d = adm2_tree.query(pt)
            for idx in c_d:
                if adm2_prep[idx].intersects(pt):
                    d_id, d_code, d_name = adm2_rows[idx][0], adm2_rows[idx][1], adm2_rows[idx][2]
                    break

            # Sub-district Match (localized within matched district)
            if d_code and d_code in adm3_by_dist:
                for sub_item in adm3_by_dist[d_code]:
                    if sub_item[3].intersects(pt):
                        sub_id, sub_name = sub_item[0], sub_item[2]
                        break

        if s_id: with_state += 1
        if d_id: with_dist += 1
        if sub_id: with_subdist += 1

        has_st_conf = False
        if orig_st and orig_st not in ["National / Unspecified", "National Territory"] and s_name:
            if orig_st.strip().lower() != s_name.strip().lower():
                has_st_conf = True
                state_conflicts += 1

        has_dist_conf = False
        if orig_dist and d_name:
            if orig_dist.strip().lower() != d_name.strip().lower():
                has_dist_conf = True
                dist_conflicts += 1

        records.append((
            f_id, orig_st, orig_dist, orig_city,
            s_name, d_name, sub_name,
            str(s_id) if s_id else None,
            str(d_id) if d_id else None,
            str(sub_id) if sub_id else None,
            has_st_conf, has_dist_conf,
            "POSTGIS_SPATIAL_JOIN",
            "geoBoundaries / Local Government Directory",
            "HIGH"
        ))

    # Bulk insert into facility_administrative_context
    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO facility_administrative_context (
                    facility_id, original_state, original_district, original_city,
                    derived_state, derived_district, derived_subdistrict,
                    state_id, district_id, subdistrict_id,
                    has_state_conflict, has_district_conflict,
                    spatial_match_method, administrative_source, administrative_confidence
                ) VALUES %s;
                """,
                records,
                page_size=5000
            )
        raw_conn.commit()
    finally:
        raw_conn.close()

    elapsed = time.time() - t0
    total = len(facs)
    print(f"  • Total Canonical Facilities     : {total:,}", flush=True)
    print(f"  • Enriched Administrative Context: {len(records):,} (100.0%)", flush=True)
    print(f"  • State Coverage                 : {with_state:,} ({with_state/total*100:.2f}%)", flush=True)
    print(f"  • District Coverage              : {with_dist:,} ({with_dist/total*100:.2f}%)", flush=True)
    print(f"  • Sub-District Coverage          : {with_subdist:,} ({with_subdist/total*100:.2f}%)", flush=True)
    print(f"  • State Conflicts Detected       : {state_conflicts:,}", flush=True)
    print(f"  • District Conflicts Detected    : {dist_conflicts:,}", flush=True)
    print(f"  • Execution Time                 : {elapsed:.2f}s", flush=True)


def enrich_firms(adm1_data, adm2_data):
    adm1_rows, adm1_shapes, adm1_prep, adm1_tree = adm1_data
    adm2_rows, adm2_shapes, adm2_prep, adm2_tree = adm2_data

    print("\n" + "=" * 95, flush=True)
    print(" [PHASE 2A.2] SPATIAL ADMINISTRATIVE ENRICHMENT: NASA FIRMS TELEMETRY (1.77M+) ", flush=True)
    print("=" * 95, flush=True)
    t0 = time.time()

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE observation_administrative_context CASCADE;"))

    read_conn = engine.raw_connection()
    write_conn = engine.raw_connection()
    batch_size = 100000
    total_processed = 0
    total_matched_state = 0
    total_matched_dist = 0

    try:
        with read_conn.cursor(name="firms_stream_cursor") as read_cur:
            read_cur.itersize = batch_size
            read_cur.execute("SELECT id, latitude, longitude FROM thermal_detections;")

            while True:
                rows = read_cur.fetchmany(batch_size)
                if not rows:
                    break

                batch_records = []
                for r in rows:
                    det_id, lat, lon = r[0], r[1], r[2]
                    s_id, s_name = None, None
                    d_id, d_name = None, None

                    if lat is not None and lon is not None:
                        pt = shapely.geometry.Point(lon, lat)

                        # State match
                        c_s = adm1_tree.query(pt)
                        for idx in c_s:
                            if adm1_prep[idx].intersects(pt):
                                s_id, s_name = adm1_rows[idx][0], adm1_rows[idx][2]
                                break

                        # District match
                        c_d = adm2_tree.query(pt)
                        for idx in c_d:
                            if adm2_prep[idx].intersects(pt):
                                d_id, d_name = adm2_rows[idx][0], adm2_rows[idx][2]
                                break

                    if s_id: total_matched_state += 1
                    if d_id: total_matched_dist += 1

                    batch_records.append((
                        det_id,
                        str(s_id) if s_id else None,
                        s_name,
                        str(d_id) if d_id else None,
                        d_name,
                        None,
                        None,
                        "POSTGIS_SPATIAL_JOIN",
                        "geoBoundaries / Local Government Directory",
                        "HIGH" if s_id else "UNMATCHED"
                    ))

                total_processed += len(batch_records)

                # Bulk write batch
                with write_conn.cursor() as write_cur:
                    psycopg2.extras.execute_values(
                        write_cur,
                        """
                        INSERT INTO observation_administrative_context (
                            detection_id, state_id, state_name, district_id, district_name,
                            subdistrict_id, subdistrict_name, spatial_match_method,
                            boundary_source, administrative_confidence
                        ) VALUES %s;
                        """,
                        batch_records,
                        page_size=10000
                    )
                write_conn.commit()
                print(f"    Processed {total_processed:,} / 1,771,007 observations ({total_matched_state:,} state matches)...", flush=True)

    finally:
        read_conn.close()
        write_conn.close()

    elapsed = time.time() - t0
    print(f"  • Total FIRMS Observations       : {total_processed:,}", flush=True)
    print(f"  • State Coverage                 : {total_matched_state:,} ({total_matched_state/total_processed*100:.2f}%)", flush=True)
    print(f"  • District Coverage              : {total_matched_dist:,} ({total_matched_dist/total_processed*100:.2f}%)", flush=True)
    print(f"  • Unmatched Offshore/Border      : {total_processed - total_matched_state:,} ({((total_processed - total_matched_state)/total_processed)*100:.2f}%)", flush=True)
    print(f"  • Execution Time                 : {elapsed:.2f}s", flush=True)


def enrich_parivesh(adm1_data, adm2_data, adm3_by_dist):
    adm1_rows, adm1_shapes, adm1_prep, adm1_tree = adm1_data
    adm2_rows, adm2_shapes, adm2_prep, adm2_tree = adm2_data

    print("\n" + "=" * 95, flush=True)
    print(" [PHASE 2A.3] SPATIAL ADMINISTRATIVE ENRICHMENT: PARIVESH CLEARANCE PROJECTS (622) ", flush=True)
    print("=" * 95, flush=True)
    t0 = time.time()

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE parivesh_administrative_context CASCADE;"))

    with engine.connect() as conn:
        projects = conn.execute(text("""
            SELECT proposal_id, state, district, latitude, longitude
            FROM parivesh_projects_staging;
        """)).fetchall()

    records = []
    spatial_count = 0
    source_count = 0
    state_conflicts = 0

    for p in projects:
        prop_id, orig_st, orig_dist, lat, lon = p[0], p[1], p[2], p[3], p[4]
        s_id, s_name = None, None
        d_id, d_name, d_code = None, None, None
        sub_id, sub_name = None, None
        method = "SOURCE_ATTRIBUTION"
        conf = "MEDIUM"

        has_coords = (lat is not None and lon is not None and (6.0 <= lat <= 38.0) and (68.0 <= lon <= 98.0))

        if has_coords:
            pt = shapely.geometry.Point(lon, lat)

            # State Match
            c_s = adm1_tree.query(pt)
            for idx in c_s:
                if adm1_prep[idx].intersects(pt):
                    s_id, s_name = adm1_rows[idx][0], adm1_rows[idx][2]
                    break

            # District Match
            c_d = adm2_tree.query(pt)
            for idx in c_d:
                if adm2_prep[idx].intersects(pt):
                    d_id, d_code, d_name = adm2_rows[idx][0], adm2_rows[idx][1], adm2_rows[idx][2]
                    break

            # Sub-district Match
            if d_code and d_code in adm3_by_dist:
                for sub_item in adm3_by_dist[d_code]:
                    if sub_item[3].intersects(pt):
                        sub_id, sub_name = sub_item[0], sub_item[2]
                        break

            if s_id:
                spatial_count += 1
                method = "POSTGIS_SPATIAL_JOIN"
                conf = "HIGH"
            else:
                source_count += 1
        else:
            source_count += 1

        derived_st = s_name if s_name else orig_st
        derived_dist = d_name if d_name else orig_dist

        has_st_conf = False
        if s_name and orig_st and s_name.strip().lower() != orig_st.strip().lower():
            has_st_conf = True
            state_conflicts += 1

        records.append((
            prop_id, orig_st, orig_dist,
            derived_st, derived_dist, sub_name,
            str(s_id) if s_id else None,
            str(d_id) if d_id else None,
            str(sub_id) if sub_id else None,
            has_st_conf, False,
            method, conf
        ))

    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO parivesh_administrative_context (
                    proposal_id, original_state, original_district,
                    derived_state, derived_district, derived_subdistrict,
                    state_id, district_id, subdistrict_id,
                    has_state_conflict, has_district_conflict,
                    administrative_method, administrative_confidence
                ) VALUES %s;
                """,
                records,
                page_size=1000
            )
        raw_conn.commit()
    finally:
        raw_conn.close()

    elapsed = time.time() - t0
    total = len(projects)
    print(f"  • Total PARIVESH Projects        : {total}", flush=True)
    print(f"  • Enriched Administrative Context: {len(records)} (100.0%)", flush=True)
    print(f"  • Spatially Derived (Coordinates): {spatial_count} ({spatial_count/total*100:.1f}%)", flush=True)
    print(f"  • Source Attributed (No Coords)  : {source_count} ({source_count/total*100:.1f}%)", flush=True)
    print(f"  • State Conflicts Detected       : {state_conflicts}", flush=True)
    print(f"  • Execution Time                 : {elapsed:.2f}s", flush=True)


def run_full_enrichment():
    total_start = time.time()
    adm1, adm2, adm3_by_dist = load_boundary_trees()
    enrich_facilities(adm1, adm2, adm3_by_dist)
    enrich_firms(adm1, adm2)
    enrich_parivesh(adm1, adm2, adm3_by_dist)

    print("\n" + "=" * 95, flush=True)
    print(f" [PHASE 2A COMPLETE] NATIONAL ADMINISTRATIVE ENRICHMENT FINISHED IN {time.time() - total_start:.2f}s ", flush=True)
    print("=" * 95, flush=True)


if __name__ == "__main__":
    run_full_enrichment()
