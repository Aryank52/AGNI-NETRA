import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.domain import User, ThermalEvent, Alert, VerificationRecord, AuditLog
from backend.app.core.security import get_password_hash, create_access_token

client = TestClient(app)


def test_complete_e2e_decision_support_journey():
    """
    Complete End-to-End Acceptance Test Workflow:
    Login → Dashboard → Map → Event → Intelligence → Verification → Alert → Report → Portals → Admin/Audit
    """
    db = SessionLocal()
    try:
        # =========================================================================
        # 1. LOGIN
        # =========================================================================
        # Ensure analyst user exists
        analyst = db.query(User).filter(User.email == "analyst@agni.in").first()
        if not analyst:
            analyst = User(
                email="analyst@agni.in",
                hashed_password=get_password_hash("Analyst@123"),
                full_name="Senior Remote Sensing Analyst",
                organization="CPCB / ISRO Monitoring Cell",
                role="ANALYST",
                is_active=True
            )
            db.add(analyst)
            db.commit()
            db.refresh(analyst)

        # Execute Login API with form data (OAuth2 standard)
        login_resp = client.post("/api/v1/auth/login", data={
            "username": "analyst@agni.in",
            "password": "Analyst@123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        auth_data = login_resp.json()
        assert "access_token" in auth_data
        token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert auth_data["user"]["role"] == "ANALYST"

        # =========================================================================
        # 2. DASHBOARD & KPIS
        # =========================================================================
        kpi_resp = client.get("/api/v1/analytics/kpis")
        assert kpi_resp.status_code == 200
        kpis = kpi_resp.json()
        assert "active_events_count" in kpis
        assert "industrial_candidates_count" in kpis
        assert "persistent_sources_count" in kpis

        # State filter query (Gujarat)
        events_resp = client.get("/api/v1/events?state=Gujarat&limit=10")
        assert events_resp.status_code == 200
        raw_events = events_resp.json()
        events_list = raw_events["items"] if isinstance(raw_events, dict) and "items" in raw_events else raw_events
        assert len(events_list) > 0

        # =========================================================================
        # 3. TACTICAL MAP & GEOJSON
        # =========================================================================
        geo_resp = client.get("/api/v1/events/geojson")
        assert geo_resp.status_code == 200
        geo = geo_resp.json()
        assert geo["type"] == "FeatureCollection"
        assert len(geo["features"]) > 0

        # =========================================================================
        # 4. EVENT INTELLIGENCE DOSSIER & SHAP
        # =========================================================================
        target_event = events_list[0]
        event_id = target_event["id"]

        dossier_resp = client.get(f"/api/v1/events/{event_id}")
        assert dossier_resp.status_code == 200
        dossier = dossier_resp.json()
        assert "event_code" in dossier
        assert "latitude" in dossier
        assert "longitude" in dossier
        assert "max_frp" in dossier
        assert "facility_status" in dossier
        assert "prediction" in dossier
        assert "risk" in dossier

        # Verify SHAP attributions and uncertainty
        pred = dossier["prediction"]
        assert pred["predicted_class"] in [
            "Industrial Fire", "Gas Flare", "Forest Fire",
            "Agricultural Burning", "Mining Activity", "Other Thermal Source", "Uncertain"
        ]
        assert 0.0 <= pred["confidence"] <= 1.0

        # =========================================================================
        # 5. HUMAN-IN-THE-LOOP (HITL) VERIFICATION
        # =========================================================================
        verif_queue_resp = client.get("/api/v1/verification/queue")
        assert verif_queue_resp.status_code == 200

        submit_verif_resp = client.post("/api/v1/verification", json={
            "event_id": event_id,
            "verified_label": "Industrial Fire",
            "verification_action": "CONFIRM",
            "notes": "E2E Acceptance Test: Confirmed via Sentinel-2 SWIR reflection and CPCB station telemetry"
        }, headers=headers)
        assert submit_verif_resp.status_code == 200
        verif_rec = submit_verif_resp.json()
        assert verif_rec["verification_action"] == "CONFIRM"

        # =========================================================================
        # 6. INCIDENT ALERTS & ACKNOWLEDGMENT
        # =========================================================================
        # Ensure at least one alert exists
        alert = db.query(Alert).first()
        if not alert:
            alert = Alert(
                event_id=event_id,
                alert_level="CRITICAL",
                title="Critical Thermal Intensity Breach",
                message="High radiative power (>150MW) detected near industrial installation",
                status="NEW",
                dispatched_to={"agencies": ["NDRF", "CPCB"]}
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)

        ack_resp = client.patch(f"/api/v1/alerts/{alert.id}", json={
            "status": "ACKNOWLEDGED"
        }, headers=headers)
        assert ack_resp.status_code == 200
        assert ack_resp.json()["status"] == "ACKNOWLEDGED"

        # =========================================================================
        # 7. AUTOMATED PDF REPORT GENERATION
        # =========================================================================
        pdf_resp = client.get(f"/api/v1/reports/event/{event_id}/download")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert pdf_resp.content.startswith(b"%PDF-")

        # =========================================================================
        # 8. SPECIALIZED PORTALS (RESEARCH, INDUSTRY, PUBLIC)
        # =========================================================================
        # Research Portal
        res_resp = client.get("/api/v1/portals/research/overview")
        assert res_resp.status_code == 200
        assert res_resp.json()["feature_dimensions"] == 18

        # Industry Portal
        ind_resp = client.get("/api/v1/portals/industry/facilities")
        assert ind_resp.status_code == 200

        # Public Portal
        pub_resp = client.get("/api/v1/portals/public/advisories")
        assert pub_resp.status_code == 200

        # Thermal Baselines Grid
        base_resp = client.get("/api/v1/baselines/grid-cells")
        assert base_resp.status_code == 200
        assert len(base_resp.json()) >= 5

        # =========================================================================
        # 9. ADMIN & AUDIT TRAIL LOGGING
        # =========================================================================
        admin_user = db.query(User).filter(User.role == "ADMIN").first()
        if not admin_user:
            admin_user = User(
                email="admin@agni.in",
                hashed_password=get_password_hash("Admin@123"),
                full_name="System Administrator",
                role="ADMIN",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        admin_token = create_access_token(subject=str(admin_user.id), role="ADMIN")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        audit_resp = client.get("/api/v1/admin/audit-logs", headers=admin_headers)
        assert audit_resp.status_code == 200
        logs = audit_resp.json()
        assert len(logs) > 0

        # Verify system health
        health_resp = client.get("/api/v1/admin/system-health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "HEALTHY"

    finally:
        db.close()
