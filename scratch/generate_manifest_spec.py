import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
import psycopg2
from backend.app.core.config import settings

LOCAL_URL = 'postgresql://postgres:projectdatabase_2026@127.0.0.1:5432/agni_netra'
SUPA_URL = settings.DATABASE_URL.replace('+psycopg2', '')

l_conn = psycopg2.connect(LOCAL_URL)
s_conn = psycopg2.connect(SUPA_URL)
l_cur = l_conn.cursor()
s_cur = s_conn.cursor()

CORE_TABLES = [
    'admin_boundaries', 'authority_directory', 'fsi_sources', 'protected_areas',
    'lulc_sources', 'lulc_classes', 'lulc_raster_tiles', 'lulc_spatial_features',
    'industrial_facilities', 'candidate_facilities', 'facility_administrative_context',
    'facility_baselines', 'facility_lulc_context', 'facility_forest_context',
    'historical_baselines', 'historical_incidents', 'thermal_events', 'risk_scores',
    'event_features', 'model_predictions', 'alerts', 'verification_records',
    'incident_lifecycle_transitions', 'root_cause_hypotheses', 'prevention_cases',
    'prevention_recommendations', 'prevention_reports', 'mission_tasks',
    'investigation_workspaces', 'investigation_audit_log', 'case_notes',
    'evidence_requests', 'evidence_reviews', 'assessment_versions', 'report_versions',
    'data_sources', 'dataset_registry', 'governed_dataset_registry',
    'ml_model_registry', 'analyst_feedback', 'users', 'audit_logs',
    'ibm_mineral_resources', 'ibm_mining_lease_context', 'ibm_auctioned_blocks',
    'facility_mining_evidence', 'fsi_isfr_district_forest_stats'
]

mapping = {}

for t in CORE_TABLES:
    s_cur.execute('''
        SELECT column_name, data_type, udt_name, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position;
    ''', (t,))
    s_cols = [r[0] for r in s_cur.fetchall()]
    
    l_cur.execute('''
        SELECT column_name, data_type, udt_name, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position;
    ''', (t,))
    l_cols = [r[0] for r in l_cur.fetchall()]

    s_cur.execute('''
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public' AND tc.table_name = %s;
    ''', (t,))
    pks = [r[0] for r in s_cur.fetchall()]

    s_cur.execute('''
        SELECT f_geometry_column, srid, type
        FROM geometry_columns
        WHERE f_table_schema = 'public' AND f_table_name = %s;
    ''', (t,))
    geom = [r[0] for r in s_cur.fetchall()]

    projected = [c for c in s_cols if c in l_cols]
    excluded_from_source = [c for c in l_cols if c not in s_cols]
    
    mapping[t] = {
        'pks': pks,
        'projected_columns': projected,
        'excluded_source_columns': excluded_from_source,
        'spatial_columns': geom
    }

l_conn.close()
s_conn.close()

with open('scratch/manifest_spec.json', 'w', encoding='utf-8') as f:
    json.dump(mapping, f, indent=2)

print('Manifest spec generated successfully for 47 tables.')
for t, m in mapping.items():
    if m['excluded_source_columns']:
        print(f"{t}: Excluded from source: {m['excluded_source_columns']}")
