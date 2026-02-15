"""
Telegram notification system for alerts.
Uses direct HTTP API calls for reliability (no async complexity).
"""

import os
import requests
from typing import List, Optional

from src.core.validator import ValidationAlert, AlertLevel


class TelegramNotifier:
    """Sends alerts via Telegram bot using HTTP API."""
    
    TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.alerts_buffer: List[ValidationAlert] = []
        
        if not self.bot_token or not self.chat_id:
            print("Warning: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Telegram notifications disabled.")
            self.enabled = False
            return
        
        self.enabled = True
        self.api_url = self.TELEGRAM_API_URL.format(token=self.bot_token)
    
    def send_alert(self, alert: ValidationAlert):
        """Buffer an alert for the summary message."""
        if not self.enabled:
            return
        self.alerts_buffer.append(alert)
    
    def send_summary(self):
        """Send a single summary message to Telegram with all buffered alerts."""
        if not self.enabled or not self.alerts_buffer:
            return
        
        # Count by level
        critical_count = sum(1 for a in self.alerts_buffer if a.level == AlertLevel.CRITICAL)
        warning_count = sum(1 for a in self.alerts_buffer if a.level == AlertLevel.WARNING)
        info_count = len(self.alerts_buffer) - critical_count - warning_count
        
        # Build summary message
        message = "📊 *Mining Ops — Alert Summary*\n\n"
        message += f"Total alerts: *{len(self.alerts_buffer)}*\n"
        if critical_count:
            message += f"🚨 Critical: *{critical_count}*\n"
        if warning_count:
            message += f"⚠️ Warning: *{warning_count}*\n"
        if info_count:
            message += f"ℹ️ Info: *{info_count}*\n"
        
        # Add top 5 critical alerts as details
        critical_alerts = [a for a in self.alerts_buffer if a.level == AlertLevel.CRITICAL]
        if critical_alerts:
            message += "\n*Top Critical Alerts:*\n"
            for alert in critical_alerts[:5]:
                message += f"• {alert.message}\n"
            if len(critical_alerts) > 5:
                message += f"_...and {len(critical_alerts) - 5} more_\n"
        
        # Send via HTTP
        self._send_message(message)
        
        # Clear buffer
        self.alerts_buffer.clear()
    
    def _send_message(self, text: str):
        """Send a message to Telegram via HTTP POST."""
        if not self.enabled:
            return
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            if response.status_code == 200:
                print("✓ Telegram summary sent successfully")
            else:
                print(f"Warning: Telegram API returned status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Warning: Failed to send Telegram message: {e}")
    
    @staticmethod
    def _get_emoji(level: AlertLevel) -> str:
        if level == AlertLevel.CRITICAL:
            return "🚨"
        elif level == AlertLevel.WARNING:
            return "⚠️"
        return "ℹ️"
    
    @staticmethod
    def _format_message(alert: ValidationAlert, emoji: str) -> str:
        message = f"{emoji} *{alert.level.value.upper()}*\n\n"
        message += f"*Rule:* {alert.rule}\n"
        message += f"*Message:* {alert.message}\n"
        if alert.data:
            message += "\n*Details:*\n"
            for key, value in alert.data.items():
                message += f"• {key}: {value}\n"
        return message
