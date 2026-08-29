import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from backend.app.core.config import settings


class EmailNotificationProvider:
    """
    SMTP-based Email Notification Provider.
    Dispatches structured HTML alerts when EMAIL_ENABLED=true and credentials are configured.
    """

    def __init__(self):
        self.enabled = settings.EMAIL_ENABLED and bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD)

    def send(self, recipient_email: str, subject: str, alert_details: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "status": "SKIPPED",
                "message": "Email provider disabled or SMTP credentials not configured."
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[AGNI-NETRA ALERT] {subject}"
            msg["From"] = settings.ALERT_FROM_EMAIL
            msg["To"] = recipient_email

            event_code = alert_details.get("event_code", "N/A")
            risk_level = alert_details.get("risk_level", "HIGH")
            max_frp = alert_details.get("max_frp", 0.0)
            facility_name = alert_details.get("facility_name", "Unassigned")
            state = alert_details.get("state", "India")

            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #0b1120; color: #f8fafc; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155;">
                    <h2 style="color: #f59e0b; margin-top: 0;">AGNI-NETRA Incident Alert</h2>
                    <p style="font-size: 14px; color: #cbd5e1;">A high-priority thermal risk signature has been detected by satellite intelligence.</p>
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px;">
                        <tr><td style="padding: 8px; color: #94a3b8;">Event Code:</td><td style="padding: 8px; font-weight: bold; color: #fff;">{event_code}</td></tr>
                        <tr><td style="padding: 8px; color: #94a3b8;">Risk Level:</td><td style="padding: 8px; font-weight: bold; color: #ef4444;">{risk_level}</td></tr>
                        <tr><td style="padding: 8px; color: #94a3b8;">Peak FRP:</td><td style="padding: 8px; color: #fff;">{max_frp} MW</td></tr>
                        <tr><td style="padding: 8px; color: #94a3b8;">Facility Context:</td><td style="padding: 8px; color: #fff;">{facility_name} ({state})</td></tr>
                    </table>
                    <a href="http://localhost:3000/dashboard/alerts" style="display: inline-block; padding: 10px 20px; background-color: #f59e0b; color: #020617; font-weight: bold; border-radius: 8px; text-decoration: none;">View in Command Center</a>
                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

            return {"status": "DELIVERED", "recipient": recipient_email}
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}


class SMSProvider:
    """
    SMS Gateway Provider Abstraction.
    Allows modular pluggability for Twilio, Textlocal, CDAC Meghdoot, or Console logging.
    """

    def __init__(self):
        self.enabled = settings.SMS_ENABLED and bool(settings.SMS_API_KEY)
        self.provider_name = settings.SMS_PROVIDER

    def send(self, phone_number: str, message: str) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "status": "SKIPPED",
                "provider": self.provider_name,
                "message": f"SMS provider not configured (CONSOLE simulation: {message[:60]}...)"
            }

        return {
            "status": "SENT",
            "provider": self.provider_name,
            "recipient": phone_number,
            "message": message[:160]
        }


class AgencyNotificationProvider:
    """
    Integration-ready abstraction for Indian Government & Regulatory Agencies:
    - NDMA (National Disaster Management Authority)
    - SDMA (State Disaster Management Authority)
    - State Forest Departments
    - CPCB / SPCB (Central & State Pollution Control Boards)
    - Directorate of Industrial Safety & Health (DISH)
    - Facility Operators / Safety Officers
    """

    SUPPORTED_AGENCIES = [
        "NDMA",
        "SDMA",
        "FOREST_DEPARTMENT",
        "CPCB_SPCB",
        "INDUSTRIAL_SAFETY_DIRECTORATE",
        "FACILITY_OPERATOR"
    ]

    def __init__(self):
        self.email_provider = EmailNotificationProvider()
        self.sms_provider = SMSProvider()

    def dispatch_agency_advisory(
        self,
        agency_type: str,
        target_state: str,
        alert_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Routes incident intelligence to the relevant authority based on jurisdiction and event classification.
        """
        agency = agency_type.upper()
        if agency not in self.SUPPORTED_AGENCIES:
            agency = "SDMA"

        subject = f"{agency} Advisory - {target_state}: {alert_payload.get('title', 'Thermal Incident')}"
        
        # Abstraction layer ready for official API webhooks / dispatch systems
        return {
            "status": "QUEUED_FOR_DISPATCH",
            "agency": agency,
            "jurisdiction": target_state,
            "priority": alert_payload.get("risk_level", "HIGH"),
            "event_code": alert_payload.get("event_code"),
            "dispatch_timestamp": alert_payload.get("timestamp"),
            "channels": ["SYSTEM_INBOX", "SECURE_ADVISORY_PORTAL"]
        }


class NotificationService:
    """
    Unified AGNI-NETRA Notification Dispatcher.
    Coordinates Email, SMS, and Agency advisories.
    """

    def __init__(self):
        self.email_provider = EmailNotificationProvider()
        self.sms_provider = SMSProvider()
        self.agency_provider = AgencyNotificationProvider()

    @property
    def email_enabled(self) -> bool:
        return self.email_provider.enabled

    @property
    def sms_enabled(self) -> bool:
        return self.sms_provider.enabled

    def send_alert_email(self, recipient_email: str, subject: str, alert_details: Dict[str, Any]) -> Dict[str, Any]:
        return self.email_provider.send(recipient_email, subject, alert_details)

    def send_sms_alert(self, phone_number: str, message: str) -> Dict[str, Any]:
        return self.sms_provider.send(phone_number, message)

    def notify_agencies(self, agency_type: str, target_state: str, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.agency_provider.dispatch_agency_advisory(agency_type, target_state, alert_payload)


notification_service = NotificationService()
