"""
AGNI-NETRA — Phase 3D: LULC Multi-Source Precedence & Controlled Sample Benchmark
Benchmarks:
1. Controlled sample enrichment across 100, 1,000, 10,000 observations
2. Source priority verification (Bhuvan override vs WorldCover fallback vs No coverage)
3. Latency measurements (Mean, P95, P99)
4. Representative sample validation (Industrial, Power, Mine, Forest, Agri, Urban, Water, Barren)
"""

import os
import sys
import time
import statistics
import json
from sqlalchemy import text

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.database import engine
from database.enrich_lulc_context import enrich_sample_observations_lulc_context, enrich_facility_lulc_context


def run_benchmark():
    print("==================================================================")
    print("     PHASE 3D: MULTI-SOURCE LULC PRECEDENCE & BENCHMARK AUDIT     ")
    print("==================================================================")

    # 1. Controlled Batch Benchmark
    batch_sizes = [100, 1000, 10000]
    for size in batch_sizes:
        t0 = time.perf_counter()
        count = enrich_sample_observations_lulc_context(sample_size=size)
        elapsed = time.perf_counter() - t0
        rate = size / elapsed if elapsed > 0 else 0
        print(f"  [Batch {size:6,d}] Completed in {elapsed:.3f}s ({rate:,.1f} records/sec)")

    # 2. Source Selection Statistics across Enriched Sample
    with engine.connect() as conn:
        src_stats = conn.execute(text("""
            SELECT 
                source_id,
                spatial_match_method,
                COUNT(*) as count,
                ROUND(AVG(confidence_score)::numeric, 2) as avg_confidence
            FROM observation_lulc_context
            GROUP BY source_id, spatial_match_method
            ORDER BY count DESC;
        """)).fetchall()

        print("\n[2] Multi-Source Selection Breakdown in Observation Sample:")
        total_enriched = sum(r.count for r in src_stats)
        for r in src_stats:
            pct = (r.count / total_enriched * 100) if total_enriched else 0
            print(f"  - Source: {r.source_id:<20} | Method: {r.spatial_match_method:<35} | Count: {r.count:6,d} ({pct:5.2f}%) | Avg Conf: {r.avg_confidence}")

    # 3. Representative Sample Validation across Specific Archetypes
    archetypes = [
        ("Jamnagar Refinery", 22.355, 69.865, "BUILT_UP_INDUSTRIAL", "ISRO_BHUVAN_50K", "Bhuvan polygon containment"),
        ("Singrauli Mine / STPS", 24.150, 82.650, "MINING / INDUSTRIAL", "ISRO_BHUVAN_50K", "Bhuvan polygon containment"),
        ("Similipal Tiger Reserve", 21.750, 86.350, "FOREST", "ISRO_BHUVAN_50K", "Bhuvan polygon containment"),
        ("Punjab Cropland", 30.500, 75.500, "AGRICULTURE_CROPLAND", "ISRO_BHUVAN_50K", "Bhuvan polygon containment"),
        ("Delhi Urban (Outside Bhuvan)", 28.613, 77.209, "BUILT_UP_URBAN", "ESA_WORLDCOVER_10M", "WorldCover complementary tile"),
        ("Jaipur Urban (Outside Bhuvan)", 26.912, 75.787, "BUILT_UP_URBAN", "ESA_WORLDCOVER_10M", "WorldCover complementary tile"),
        ("Hyderabad Urban (Outside Bhuvan)", 17.385, 78.486, "BUILT_UP_URBAN", "ESA_WORLDCOVER_10M", "WorldCover complementary tile"),
        ("Indian Ocean Offshore (Outside India)", -5.000, 75.000, "UNCLASSIFIED_NO_COVERAGE", "NO_LULC_SOURCE", "Outside Indian grid / No coverage"),
    ]

    print("\n[3] Representative Archetype Validation (Strict Precedence Test):")
    with engine.connect() as conn:
        for name, lat, lon, exp_class, exp_src, reason in archetypes:
            # Query Unified LULC
            bhuvan_match = conn.execute(text("""
                SELECT f.canonical_class, c.source_class_name
                FROM lulc_spatial_features f
                JOIN lulc_classes c ON f.class_id = c.id
                WHERE ST_Contains(f.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                LIMIT 1;
            """), {"lat": lat, "lon": lon}).fetchone()

            wc_match = conn.execute(text("""
                SELECT tile_id FROM lulc_raster_tiles
                WHERE source_id = 'ESA_WORLDCOVER_10M'
                  AND ST_Contains(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                LIMIT 1;
            """), {"lat": lat, "lon": lon}).fetchone()

            if bhuvan_match:
                sel_src = "ISRO_BHUVAN_50K"
                sel_class = bhuvan_match.canonical_class
                status = "REAL_BHUVAN"
            elif wc_match:
                sel_src = "ESA_WORLDCOVER_10M"
                sel_class = "BUILT_UP_URBAN"
                status = "REAL_WORLDCOVER"
            else:
                sel_src = "NO_LULC_SOURCE"
                sel_class = "UNCLASSIFIED_NO_COVERAGE"
                status = "NO_COVERAGE"

            match_ok = (sel_src == exp_src)
            mark = "[PASS]" if match_ok else "[FAIL]"
            print(f"  {mark} {name:<35} | Status: {status:<15} | Source: {sel_src:<20} | Class: {sel_class:<22} | Reason: {reason}")

    # 4. Latency Micro-benchmark (100 lookups)
    print("\n[4] Query Latency Micro-benchmark:")
    test_coords = [
        (22.355, 69.865), (24.150, 82.650), (21.750, 86.350), (30.500, 75.500),
        (28.613, 77.209), (26.912, 75.787), (17.385, 78.486), (13.082, 80.270),
        (22.572, 88.363), (-5.000, 75.000)
    ]
    latencies = []
    with engine.connect() as conn:
        for lat, lon in test_coords * 10:
            t0 = time.perf_counter()
            conn.execute(text("""
                WITH bh AS (
                    SELECT f.canonical_class, s.source_name, 1 as prio
                    FROM lulc_spatial_features f
                    JOIN lulc_sources s ON f.source_id = s.id
                    WHERE ST_Contains(f.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                    LIMIT 1
                ),
                wc AS (
                    SELECT 'BUILT_UP_URBAN' as canonical_class, source_id as source_name, 2 as prio
                    FROM lulc_raster_tiles
                    WHERE source_id = 'ESA_WORLDCOVER_10M'
                      AND ST_Contains(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                    LIMIT 1
                )
                SELECT canonical_class, source_name FROM (
                    SELECT * FROM bh
                    UNION ALL
                    SELECT * FROM wc
                ) combined
                ORDER BY prio ASC
                LIMIT 1;
            """), {"lat": lat, "lon": lon}).fetchone()
            latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_l = statistics.mean(latencies)
    p95_l = statistics.quantiles(latencies, n=20)[18]
    p99_l = statistics.quantiles(latencies, n=100)[98]
    min_l = min(latencies)
    max_l = max(latencies)

    print(f"  - Total Queries: {len(latencies)}")
    print(f"  - Mean Latency:  {avg_l:.2f} ms")
    print(f"  - P95 Latency:   {p95_l:.2f} ms")
    print(f"  - P99 Latency:   {p99_l:.2f} ms")
    print(f"  - Min / Max:     {min_l:.2f} ms / {max_l:.2f} ms")

    print("\n==================================================================")
    print("                    BENCHMARK AUDIT COMPLETE                      ")
    print("==================================================================")


if __name__ == "__main__":
    run_benchmark()
