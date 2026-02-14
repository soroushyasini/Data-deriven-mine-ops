"""
Email notification system for alerts.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

from src.core.validator import ValidationAlert, AlertLevel


class EmailNotifier:
    """Sends alerts via email."""
    
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        username: str = None,
        password: str = None,
        from_addr: str = None,
        to_addrs: List[str] = None
    ):
        """
        Initialize email notifier.
        
        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_addr: From email address
            to_addrs: List of recipient addresses
        """
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.username = username or os.getenv('SMTP_USERNAME')
        self.password = password or os.getenv('SMTP_PASSWORD')
        self.from_addr = from_addr or os.getenv('EMAIL_FROM')
        self.to_addrs = to_addrs or os.getenv('EMAIL_TO', '').split(',')
        
        # Check if configured
        if not all([self.username, self.password, self.from_addr, self.to_addrs[0]]):
            print("Warning: Email not fully configured. Email notifications disabled.")
            self.enabled = False
        else:
            self.enabled = True
    
    def send_alert(self, alert: ValidationAlert):
        """
        Send an alert via email.
        
        Args:
            alert: ValidationAlert instance
        """
        if not self.enabled:
            return
        
        # Only send critical alerts individually
        # Warnings can be batched in daily digest
        if alert.level != AlertLevel.CRITICAL:
            return
        
        subject = f"[{alert.level.value.upper()}] Mining Operations Alert - {alert.rule}"
        body = self._format_message(alert)
        
        self._send_email(subject, body)
    
    def send_digest(self, alerts: List[ValidationAlert]):
        """
        Send a digest of multiple alerts.
        
        Args:
            alerts: List of validation alerts
        """
        if not self.enabled or not alerts:
            return
        
        subject = f"Mining Operations Daily Digest - {len(alerts)} alerts"
        body = self._format_digest(alerts)
        
        self._send_email(subject, body)
    
    def _send_email(self, subject: str, body: str):
        """
        Send an email.
        
        Args:
            subject: Email subject
            body: Email body (HTML)
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_addr
        msg['To'] = ', '.join(self.to_addrs)
        
        # Attach HTML body
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
        except Exception as e:
            print(f"Error sending email: {e}")
    
    @staticmethod
    def _format_message(alert: ValidationAlert) -> str:
        """
        Format alert as HTML email.
        
        Args:
            alert: ValidationAlert instance
            
        Returns:
            HTML formatted message
        """
        color = {
            AlertLevel.CRITICAL: '#dc3545',
            AlertLevel.WARNING: '#ffc107',
            AlertLevel.INFO: '#17a2b8'
        }.get(alert.level, '#6c757d')
        
        html = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif;">
                <h2 style="color: {color};">{alert.level.value.upper()} Alert</h2>
                <p><strong>Rule:</strong> {alert.rule}</p>
                <p><strong>Message:</strong> {alert.message}</p>
                
                <h3>Details:</h3>
                <ul>
        """
        
        for key, value in alert.data.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        
        html += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def _format_digest(alerts: List[ValidationAlert]) -> str:
        """
        Format multiple alerts as HTML digest.
        
        Args:
            alerts: List of validation alerts
            
        Returns:
            HTML formatted digest
        """
        html = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h1>Mining Operations Daily Digest</h1>
        """
        
        # Group by level
        by_level = {}
        for alert in alerts:
            level = alert.level.value
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(alert)
        
        for level, level_alerts in by_level.items():
            html += f"<h2>{level.upper()} ({len(level_alerts)})</h2><ul>"
            for alert in level_alerts:
                html += f"<li><strong>{alert.rule}:</strong> {alert.message}</li>"
            html += "</ul>"
        
        html += """
        </body>
        </html>
        """
        
        return html
