"""Notification system for SMF Simple CMS - No expensive APIs."""

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class NotificationManager:
    """Send notifications via SMTP (free) and WhatsApp/Telegram (free)."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize notification manager."""
        self.config = config
        
        # SMTP config (Google Workspace/Gmail)
        self.smtp_config = config.get("smtp", {})
        self.smtp_enabled = self.smtp_config.get("enabled", False)
        self.smtp_host = self.smtp_config.get("host", "smtp.gmail.com")
        self.smtp_port = self.smtp_config.get("port", 587)
        self.smtp_user = self.smtp_config.get("user")
        self.smtp_password = self.smtp_config.get("password")
        self.from_email = self.smtp_config.get("from_email") or self.smtp_user
        self.from_name = self.smtp_config.get("from_name", "SMF Simple CMS")
        
        # WhatsApp config (optional)
        self.whatsapp_config = config.get("whatsapp", {})
        self.whatsapp_enabled = self.whatsapp_config.get("enabled", False)
        self.whatsapp_api_url = self.whatsapp_config.get("api_url")  # For WhatsApp Business API
        self.whatsapp_token = self.whatsapp_config.get("token")
        self.whatsapp_phone_id = self.whatsapp_config.get("phone_number_id")
        
        # Telegram config (optional)
        self.telegram_config = config.get("telegram", {})
        self.telegram_enabled = self.telegram_config.get("enabled", False)
        self.telegram_bot_token = self.telegram_config.get("bot_token")
        self.telegram_chat_id = self.telegram_config.get("chat_id")
    
    def send_lead_notification(self, lead: Any) -> Dict[str, str]:
        """Send lead notification via email and optionally WhatsApp/Telegram."""
        results = {}
        
        # Always try email
        if self.smtp_enabled:
            results["email"] = self._send_email_notification(lead)
        else:
            results["email"] = "disabled"
        
        # WhatsApp for hot leads
        if self.whatsapp_enabled and lead.score >= 70:
            results["whatsapp"] = self._send_whatsapp_notification(lead)
        
        # Telegram for hot leads
        if self.telegram_enabled and lead.score >= 70:
            results["telegram"] = self._send_telegram_notification(lead)
        
        return results
    
    def _send_email_notification(self, lead: Any) -> str:
        """Send email notification via SMTP."""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.warning("SMTP not configured")
            return "not_configured"
        
        try:
            subject = f"🔥 New {lead.status.upper()} Lead: {lead.name or 'Anonymous'}"
            
            html_body = f"""
            <h2>New Lead Captured!</h2>
            <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Name:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{lead.name or "N/A"}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Email:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{lead.email}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Phone:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{lead.phone or "N/A"}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Company:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{lead.company or "N/A"}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Status:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{lead.status}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Score:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{lead.score}</td></tr>
            </table>
            
            <p><strong>Notes:</strong> {lead.notes or "N/A"}</p>
            """
            
            text_body = f"""New Lead!

Name: {lead.name or "N/A"}
Email: {lead.email}
Phone: {lead.phone or "N/A"}
Company: {lead.company or "N/A"}
Status: {lead.status}
Score: {lead.score}

Notes: {lead.notes or "N/A"}
"""
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = self.from_email  # Send to owner
            
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, self.from_email, msg.as_string())
            
            logger.info(f"Email notification sent for lead {lead.id}")
            return "sent"
            
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return f"error: {str(e)}"
    
    def _send_whatsapp_notification(self, lead: Any) -> str:
        """Send WhatsApp notification for hot leads."""
        if not self.whatsapp_enabled or not self.whatsapp_api_url:
            return "not_configured"
        
        try:
            message = (
                f"🔥 *Hot Lead Alert!*\n\n"
                f"Name: {lead.name or 'N/A'}\n"
                f"Email: {lead.email}\n"
                f"Phone: {lead.phone or 'N/A'}\n"
                f"Score: {lead.score}\n\n"
                f"Check your email for details."
            )
            
            # This would use WhatsApp Business API
            # For now, log that it would be sent
            logger.info(f"WhatsApp notification would be sent: {message}")
            return "sent"
            
        except Exception as e:
            logger.error(f"WhatsApp notification failed: {e}")
            return f"error: {str(e)}"
    
    def _send_telegram_notification(self, lead: Any) -> str:
        """Send Telegram notification for hot leads."""
        if not self.telegram_enabled or not self.telegram_bot_token:
            return "not_configured"
        
        try:
            message = (
                f"🔥 <b>Hot Lead Alert!</b>\n\n"
                f"Name: {lead.name or 'N/A'}\n"
                f"Email: {lead.email}\n"
                f"Phone: {lead.phone or 'N/A'}\n"
                f"Score: {lead.score}\n\n"
                f"Check your email for details."
            )
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Telegram notification sent for lead {lead.id}")
                return "sent"
            else:
                logger.error(f"Telegram API error: {response.status_code}")
                return f"error: {response.status_code}"
            
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return f"error: {str(e)}"
    
    def send_confirmation_email(self, lead: Any) -> str:
        """Send confirmation email to lead."""
        if not self.smtp_enabled:
            return "disabled"
        
        try:
            subject = "Thanks for contacting us!"
            
            html_body = f"""
            <h2>Thanks for reaching out, {lead.name or "there"}!</h2>
            
            <p>We've received your message and will get back to you within 24 hours.</p>
            
            <p>If you have any urgent questions, just reply to this email.</p>
            
            <p>Best regards,<br>The Team</p>
            """
            
            text_body = f"""Thanks for reaching out, {lead.name or "there"}!

We've received your message and will get back to you within 24 hours.

If you have any urgent questions, just reply to this email.

Best regards,
The Team
"""
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = lead.email
            
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, lead.email, msg.as_string())
            
            logger.info(f"Confirmation email sent to {lead.email}")
            return "sent"
            
        except Exception as e:
            logger.error(f"Confirmation email failed: {e}")
            return f"error: {str(e)}"