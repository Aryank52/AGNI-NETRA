import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.domain import Alert, User
from backend.app.services.notification_service import notification_service


def test_notification_service_graceful_handling():
    """Verify notification service handles unconfigured email/SMS gracefully without errors"""
    res_email = notification_service.send_alert_email(
        recipient_email="test@example.com",
        subject="Test Alert",
        alert_details={"event_code": "EVT-TEST", "risk_level": "HIGH", "max_frp": 85.0}
    )
    assert "status" in res_email
    assert res_email["status"] in ["DELIVERED", "SKIPPED", "FAILED"]

    res_sms = notification_service.send_sms_alert(
        phone_number="+919876543210",
        message="Critical thermal alert test."
    )
    assert "status" in res_sms
    assert res_sms["status"] in ["SENT", "SKIPPED"]


def test_alert_lifecycle_status():
    """Verify alert status transitions in database"""
    db = SessionLocal()
    try:
        user = db.query(User).first()
        assert user is not None

        alert = db.query(Alert).first()
        if not alert:
            alert = Alert(
                event_id="test-event-id",
                alert_level="HIGH",
                message="Elevated thermal flare detection",
                status="NEW"
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)

        # Update status
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_by = user.id
        db.commit()
        db.refresh(alert)
        assert alert.status == "ACKNOWLEDGED"

        alert.status = "UNDER REVIEW"
        db.commit()
        db.refresh(alert)
        assert alert.status == "UNDER REVIEW"

        alert.status = "RESOLVED"
        db.commit()
        db.refresh(alert)
        assert alert.status == "RESOLVED"
    finally:
        db.close()
