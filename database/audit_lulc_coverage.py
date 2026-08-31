"""
AGNI-NETRA — Phase 3C: Rigorous LULC Spatial Coverage, Traceability, & Performance Audit
Calculates exact measured statistics:
1. Spatial bounding box and total area covered
2. Administrative intersection with admin_boundaries (States, Districts, Sub-districts)
3. FIRMS point-in-polygon containment across all 1.77M+ observations
4. Industrial facilities point-in-polygon containment across all 35.6K+ facilities
5. Micro-benchmarks for lookup latency and query execution plans
"""

import os
import sys
import time
import json
import statistics
from sqlalchemy import text

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.database import engine


def audit_lulc():
    results = {}
    with engine.connect() as conn:
        print("==================================================================")
        print("          AGNI-NETRA LULC RIGOROUS SPATIAL AUDIT (PHASE 3C)       ")
        print("==================================================================")

        # 1. Spatial Features Stats
        feat_stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total_features,
                COALESCE(SUM(area_sqkm), 0) as total_area_sqkm,
                MIN(ST_YMin(geom)) as min_lat,
                MAX(ST_YMax(geom)) as max_lat,
                MIN(ST_XMin(geom)) as min_lon,
                MAX(ST_XMax(geom)) as max_lon
            FROM lulc_spatial_features;
        """)).fetchone()
        results["spatial_features"] = dict(feat_stats._mapping)
        print("\n[1] LULC Spatial Feature Audit:")
        print(f"  - Total Features: {feat_stats.total_features}")
        print(f"  - Total Area Represented: {feat_stats.total_area_sqkm:,.2f} sq km")
        print(f"  - Geographic Extent: Lat [{feat_stats.min_lat:.4f}, {feat_stats.max_lat:.4f}], Lon [{feat_stats.min_lon:.4f}, {feat_stats.max_lon:.4f}]")

        # 2. Source Metadata
        sources = conn.execute(text("SELECT id, source_name, organization, dataset_name, resolution_m, reference_year, product_version, access_type FROM lulc_sources;")).fetchall()
        print("\n[2] Registered LULC Sources:")
        for s in sources:
            print(f"  - ID: {s.id} | Name: {s.source_name} | Dataset: {s.dataset_name} | Res: {s.resolution_m}m | Year: {s.reference_year} | Ver: {s.product_version}")

        # 3. Administrative Boundary Coverage
        # States (admin_level = 1)
        st_cov = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT a.id) as covered_states,
                (SELECT COUNT(*) FROM admin_boundaries WHERE admin_level = 1) as total_states
            FROM admin_boundaries a
            JOIN lulc_spatial_features f ON ST_Intersects(a.geom, f.geom)
            WHERE a.admin_level = 1;
        """)).fetchone()

        # Districts (admin_level = 2)
        dt_cov = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT a.id) as covered_districts,
                (SELECT COUNT(*) FROM admin_boundaries WHERE admin_level = 2) as total_districts
            FROM admin_boundaries a
            JOIN lulc_spatial_features f ON ST_Intersects(a.geom, f.geom)
            WHERE a.admin_level = 2;
        """)).fetchone()

        # Subdistricts (admin_level = 3)
        sdt_cov = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT a.id) as covered_subdistricts,
                (SELECT COUNT(*) FROM admin_boundaries WHERE admin_level = 3) as total_subdistricts
            FROM admin_boundaries a
            JOIN lulc_spatial_features f ON ST_Intersects(a.geom, f.geom)
            WHERE a.admin_level = 3;
        """)).fetchone()

        st_pct = (st_cov.covered_states / st_cov.total_states) * 100.0 if st_cov.total_states else 0.0
        dt_pct = (dt_cov.covered_districts / dt_cov.total_districts) * 100.0 if dt_cov.total_districts else 0.0
        sdt_pct = (sdt_cov.covered_subdistricts / sdt_cov.total_subdistricts) * 100.0 if sdt_cov.total_subdistricts else 0.0

        results["admin_coverage"] = {
            "states": {"covered": st_cov.covered_states, "total": st_cov.total_states, "pct": round(st_pct, 2)},
            "districts": {"covered": dt_cov.covered_districts, "total": dt_cov.total_districts, "pct": round(dt_pct, 2)},
            "subdistricts": {"covered": sdt_cov.covered_subdistricts, "total": sdt_cov.total_subdistricts, "pct": round(sdt_pct, 2)},
        }

        print("\n[3] Administrative Coverage (Spatial Intersect):")
        print(f"  - States/UTs: {st_cov.covered_states} / {st_cov.total_states} ({st_pct:.2f}%)")
        print(f"  - Districts: {dt_cov.covered_districts} / {dt_cov.total_districts} ({dt_pct:.2f}%)")
        print(f"  - Subdistricts: {sdt_cov.covered_subdistricts} / {sdt_cov.total_subdistricts} ({sdt_pct:.2f}%)")

        # 4. NASA FIRMS Coverage Test (All 1.77M observations)
        print("\n[4] NASA FIRMS Spatial Point-in-Polygon Coverage Test...")
        firms_stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total_firms,
                COUNT(f.id) as covered_firms
            FROM thermal_detections d
            LEFT JOIN LATERAL (
                SELECT sf.id
                FROM lulc_spatial_features sf
                WHERE ST_Contains(sf.geom, ST_SetSRID(ST_MakePoint(d.longitude, d.latitude), 4326))
                LIMIT 1
            ) f ON TRUE;
        """)).fetchone()

        total_firms = firms_stats.total_firms
        covered_firms = firms_stats.covered_firms
        uncovered_firms = total_firms - covered_firms
        firms_pct = (covered_firms / total_firms * 100.0) if total_firms else 0.0

        results["firms_coverage"] = {
            "total": total_firms,
            "covered": covered_firms,
            "uncovered": uncovered_firms,
            "pct": round(firms_pct, 2)
        }
        print(f"  - Total FIRMS Observations: {total_firms:,}")
        print(f"  - Observations within Real Bhuvan LULC Polygons: {covered_firms:,} ({firms_pct:.2f}%)")
        print(f"  - Observations Outside Pilot LULC Polygons: {uncovered_firms:,} ({100.0 - firms_pct:.2f}%)")

        # 5. Industrial Facilities Coverage Test (All 35.6K facilities)
        print("\n[5] Industrial Facility Registry Coverage Test...")
        fac_stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total_facilities,
                COUNT(f.id) as covered_facilities
            FROM industrial_facilities ifac
            LEFT JOIN LATERAL (
                SELECT sf.id
                FROM lulc_spatial_features sf
                WHERE ST_Contains(sf.geom, ST_SetSRID(ST_MakePoint(ifac.longitude, ifac.latitude), 4326))
                LIMIT 1
            ) f ON TRUE;
        """)).fetchone()

        total_fac = fac_stats.total_facilities
        covered_fac = fac_stats.covered_facilities
        uncovered_fac = total_fac - covered_fac
        fac_pct = (covered_fac / total_fac * 100.0) if total_fac else 0.0

        results["facility_coverage"] = {
            "total": total_fac,
            "covered": covered_fac,
            "uncovered": uncovered_fac,
            "pct": round(fac_pct, 2)
        }
        print(f"  - Total Facilities: {total_fac:,}")
        print(f"  - Facilities within Real Bhuvan LULC Polygons: {covered_fac:,} ({fac_pct:.2f}%)")
        print(f"  - Facilities Outside Pilot LULC Polygons: {uncovered_fac:,} ({100.0 - fac_pct:.2f}%)")

        # 6. Performance Benchmark (100 sample lookups across India)
        print("\n[6] Real-time PostGIS Query Performance Benchmark...")
        test_points = [
            (22.355, 69.865),  # Jamnagar
            (21.720, 72.900),  # Dahej
            (24.150, 82.650),  # Singrauli
            (22.380, 82.720),  # Korba
            (20.950, 85.100),  # Angul
            (21.750, 86.350),  # Similipal
            (30.500, 75.500),  # Punjab
            (19.076, 72.877),  # Mumbai
            (12.971, 77.594),  # Bengaluru
            (28.613, 77.209),  # Delhi (outside pilot)
        ]
        
        latencies = []
        for lat, lon in test_points * 10:  # 100 iterations
            t0 = time.perf_counter()
            conn.execute(text("""
                SELECT f.id, f.canonical_class, c.source_class_code, c.source_class_name
                FROM lulc_spatial_features f
                JOIN lulc_classes c ON f.class_id = c.id
                WHERE ST_Contains(f.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                LIMIT 1;
            """), {"lat": lat, "lon": lon}).fetchone()
            latencies.append((time.perf_counter() - t0) * 1000.0)

        avg_lat = statistics.mean(latencies)
        p95_lat = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        min_lat = min(latencies)
        max_lat = max(latencies)

        results["performance"] = {
            "avg_ms": round(avg_lat, 2),
            "p95_ms": round(p95_lat, 2),
            "min_ms": round(min_lat, 2),
            "max_ms": round(max_lat, 2),
        }
        print(f"  - Iterations: {len(latencies)}")
        print(f"  - Mean Latency: {avg_lat:.2f} ms")
        print(f"  - P95 Latency: {p95_lat:.2f} ms")
        print(f"  - Min / Max: {min_lat:.2f} ms / {max_lat:.2f} ms")

        # 7. PostGIS Query Plan Explain
        print("\n[7] Query Execution Plan (EXPLAIN ANALYZE):")
        plan_rows = conn.execute(text("""
            EXPLAIN ANALYZE
            SELECT f.id, f.canonical_class, c.source_class_code, c.source_class_name
            FROM lulc_spatial_features f
            JOIN lulc_classes c ON f.class_id = c.id
            WHERE ST_Contains(f.geom, ST_SetSRID(ST_MakePoint(69.85, 22.35), 4326))
            LIMIT 1;
        """)).fetchall()
        for r in plan_rows:
            print(f"    {r[0]}")

        print("\n==================================================================")
        print("          AUDIT COMPLETE — GROUND TRUTH SUMMARY                   ")
        print("==================================================================")
        return results


if __name__ == "__main__":
    audit_lulc()
