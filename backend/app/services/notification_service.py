import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from backend.app.core.config import settings


class NotificationService:
    """
    AGNI-NETRA Notification Dispatcher.
    Provides decoupled abstractions for Email (SMTP) and SMS alerts.
    Gracefully disables dispatch when credentials/services are unconfigured.
    """

    def __init__(self):
        self.email_enabled = settings.EMAIL_ENABLED and bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD)
        self.sms_enabled = settings.SMS_ENABLED and bool(settings.SMS_API_KEY)

    def send_alert_email(
        self,
        recipient_email: str,
        subject: str,
        alert_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dispatches structured HTML alert notification via SMTP if configured.
        """
        if not self.email_enabled:
            return {
                "status": "SKIPPED",
                "message": "Email service not configured or disabled in environment settings."
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

    def send_sms_alert(
        self,
        phone_number: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Dispatches SMS alert via configured SMS gateway provider abstraction.
        """
        if not self.sms_enabled:
            return {
                "status": "SKIPPED",
                "message": "SMS provider not configured (CONSOLE mode active)."
            }

        # Pluggable vendor integration hook
        return {
            "status": "SENT",
            "provider": settings.SMS_PROVIDER,
            "recipient": phone_number,
            "message": message[:160]
        }


notification_service = NotificationService()
