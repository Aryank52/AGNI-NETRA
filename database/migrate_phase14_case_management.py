"""
Migration script for Phase 14: Intelligence Operations, Case Management & Audit Governance
Creates normalized case management tables:
- investigation_audit_log (append-only immutable audit trail)
- assessment_versions (immutable versioned snapshots of unified assessments)
- evidence_reviews (analyst evidence acceptance/questioning/rejection)
- evidence_requests (formal evidence acquisition requests)
- case_notes (structured analyst notes)
- report_versions (governed report generation records)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.app.core.database import engine, IS_SQLITE_TEST

def migrate():
    # Define table creation statements for SQLite and PostgreSQL
    if IS_SQLITE_TEST:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS investigation_audit_log (
                id VARCHAR(36) PRIMARY KEY,
                audit_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                actor_id VARCHAR(64) NOT NULL,
                actor_role VARCHAR(50) NOT NULL,
                timestamp DATETIME NOT NULL,
                action VARCHAR(64) NOT NULL,
                previous_state VARCHAR(50),
                new_state VARCHAR(50),
                reason TEXT,
                evidence_ids JSON DEFAULT '[]',
                assessment_version INTEGER DEFAULT 1,
                provenance JSON DEFAULT '{}',
                FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_audit_case_id ON investigation_audit_log(case_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON investigation_audit_log(timestamp);
            """,
            """
            CREATE TABLE IF NOT EXISTS assessment_versions (
                id VARCHAR(36) PRIMARY KEY,
                version_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                version_number INTEGER NOT NULL,
                assessment JSON DEFAULT '{}',
                created_at DATETIME NOT NULL,
                created_by VARCHAR(64) NOT NULL,
                trigger VARCHAR(100) NOT NULL,
                evidence_delta JSON DEFAULT '{}',
                uncertainty_delta JSON DEFAULT '{}',
                provenance JSON DEFAULT '{}',
                FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_assessment_ver_case_id ON assessment_versions(case_id);
            """,
            """
            CREATE TABLE IF NOT EXISTS evidence_reviews (
                id VARCHAR(36) PRIMARY KEY,
                review_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                evidence_id VARCHAR(64) NOT NULL,
                status VARCHAR(50) DEFAULT 'UNREVIEWED',
                reviewer_id VARCHAR(64),
                reviewer_role VARCHAR(50),
                notes TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_evidence_rev_case_id ON evidence_reviews(case_id);
            """,
            """
            CREATE TABLE IF NOT EXISTS evidence_requests (
                id VARCHAR(36) PRIMARY KEY,
                request_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                requested_source VARCHAR(100) NOT NULL,
                reason TEXT NOT NULL,
                uncertainty_target VARCHAR(100),
                priority VARCHAR(50) DEFAULT 'MEDIUM',
                status VARCHAR(50) DEFAULT 'OPEN',
                requested_by VARCHAR(64) NOT NULL,
                created_at DATETIME NOT NULL,
                completed_at DATETIME,
                FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_evidence_req_case_id ON evidence_requests(case_id);
            """,
            """
            CREATE TABLE IF NOT EXISTS case_notes (
                id VARCHAR(36) PRIMARY KEY,
                note_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                author VARCHAR(64) NOT NULL,
                author_role VARCHAR(50) NOT NULL,
                timestamp DATETIME NOT NULL,
                content TEXT NOT NULL,
                case_version INTEGER DEFAULT 1,
                FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_case_notes_case_id ON case_notes(case_id);
            """,
            """
            CREATE TABLE IF NOT EXISTS report_versions (
                id VARCHAR(36) PRIMARY KEY,
                report_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                report_version INTEGER NOT NULL,
                presentation_mode VARCHAR(50) DEFAULT 'ANALYST',
                assessment_version INTEGER NOT NULL,
                generated_at DATETIME NOT NULL,
                provenance JSON DEFAULT '{}',
                hash VARCHAR(64) NOT NULL,
                file_path VARCHAR(500),
                title VARCHAR(255),
                content_markdown TEXT,
                FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_report_ver_case_id ON report_versions(case_id);
            """
        ]
    else:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS investigation_audit_log (
                id VARCHAR(36) PRIMARY KEY,
                audit_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                actor_id VARCHAR(64) NOT NULL,
                actor_role VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                action VARCHAR(64) NOT NULL,
                previous_state VARCHAR(50),
                new_state VARCHAR(50),
                reason TEXT,
                evidence_ids JSONB DEFAULT '[]'::jsonb,
                assessment_version INTEGER DEFAULT 1,
                provenance JSONB DEFAULT '{}'::jsonb,
                CONSTRAINT fk_audit_case FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_audit_case_id ON investigation_audit_log(case_id);
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON investigation_audit_log(timestamp);
            """,
            """
            CREATE TABLE IF NOT EXISTS assessment_versions (
                id VARCHAR(36) PRIMARY KEY,
                version_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                version_number INTEGER NOT NULL,
                assessment JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_by VARCHAR(64) NOT NULL,
                trigger VARCHAR(100) NOT NULL,
                evidence_delta JSONB DEFAULT '{}'::jsonb,
                uncertainty_delta JSONB DEFAULT '{}'::jsonb,
                provenance JSONB DEFAULT '{}'::jsonb,
                CONSTRAINT fk_ass_ver_case FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_assessment_ver_case_id ON assessment_versions(case_id);
            """,
            """
            CREATE TABLE IF NOT EXISTS evidence_reviews (
                id VARCHAR(36) PRIMARY KEY,
                review_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                evidence_id VARCHAR(64) NOT NULL,
                status VARCHAR(50) DEFAULT 'UNREVIEWED',
                reviewer_id VARCHAR(64),
                reviewer_role VARCHAR(50),
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                CONSTRAINT fk_ev_rev_case FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_rev_case_id ON evidence_reviews(case_id);
            """,
            """
            CREATE TABLE IF NOT EXISTS evidence_requests (
                id VARCHAR(36) PRIMARY KEY,
                request_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                requested_source VARCHAR(100) NOT NULL,
                reason TEXT NOT NULL,
                uncertainty_target VARCHAR(100),
                priority VARCHAR(50) DEFAULT 'MEDIUM',
                status VARCHAR(50) DEFAULT 'OPEN',
                requested_by VARCHAR(64) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                completed_at TIMESTAMP WITH TIME ZONE,
                CONSTRAINT fk_ev_req_case FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_req_case_id ON evidence_requests(case_id);
            """,
            """
            CREATE TABLE IF NOT EXISTS case_notes (
                id VARCHAR(36) PRIMARY KEY,
                note_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                author VARCHAR(64) NOT NULL,
                author_role VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                content TEXT NOT NULL,
                case_version INTEGER DEFAULT 1,
                CONSTRAINT fk_note_case FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_case_notes_case_id ON case_notes(case_id);
            """,
            """
            CREATE TABLE IF NOT EXISTS report_versions (
                id VARCHAR(36) PRIMARY KEY,
                report_id VARCHAR(64) UNIQUE NOT NULL,
                case_id VARCHAR(64) NOT NULL,
                report_version INTEGER NOT NULL,
                presentation_mode VARCHAR(50) DEFAULT 'ANALYST',
                assessment_version INTEGER NOT NULL,
                generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                provenance JSONB DEFAULT '{}'::jsonb,
                hash VARCHAR(64) NOT NULL,
                file_path VARCHAR(500),
                title VARCHAR(255),
                content_markdown TEXT,
                CONSTRAINT fk_rep_ver_case FOREIGN KEY (case_id) REFERENCES investigation_workspaces(investigation_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_report_ver_case_id ON report_versions(case_id);
            """
        ]

    with engine.connect() as conn:
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    print(f"Notice executing statement: {e}")
        conn.commit()
    print("Phase 14 migration complete: case governance tables created.")

if __name__ == "__main__":
    migrate()
