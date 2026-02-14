"""
Telegram notification system for alerts.
"""

import os
from typing import Optional

try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

from src.core.validator import ValidationAlert, AlertLevel


class TelegramNotifier:
    """Sends alerts via Telegram bot."""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token (default from environment)
            chat_id: Telegram chat ID (default from environment)
        """
        if not TELEGRAM_AVAILABLE:
            print("Warning: python-telegram-bot not installed. Telegram notifications disabled.")
            self.enabled = False
            return
        
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            print("Warning: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Telegram notifications disabled.")
            self.enabled = False
            return
        
        try:
            self.bot = Bot(token=self.bot_token)
            self.enabled = True
        except Exception as e:
            print(f"Error initializing Telegram bot: {e}")
            self.enabled = False
    
    def send_alert(self, alert: ValidationAlert):
        """
        Send an alert via Telegram.
        
        Args:
            alert: ValidationAlert instance
        """
        if not self.enabled:
            return
        
        # Format message
        emoji = self._get_emoji(alert.level)
        message = self._format_message(alert, emoji)
        
        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except TelegramError as e:
            print(f"Error sending Telegram message: {e}")
    
    @staticmethod
    def _get_emoji(level: AlertLevel) -> str:
        """Get emoji for alert level."""
        if level == AlertLevel.CRITICAL:
            return "🚨"
        elif level == AlertLevel.WARNING:
            return "⚠️"
        else:
            return "ℹ️"
    
    @staticmethod
    def _format_message(alert: ValidationAlert, emoji: str) -> str:
        """
        Format alert message for Telegram.
        
        Args:
            alert: ValidationAlert instance
            emoji: Emoji to use
            
        Returns:
            Formatted message
        """
        message = f"{emoji} *{alert.level.value.upper()}*\n\n"
        message += f"*Rule:* {alert.rule}\n"
        message += f"*Message:* {alert.message}\n"
        
        # Add relevant data
        if alert.data:
            message += "\n*Details:*\n"
            for key, value in alert.data.items():
                message += f"• {key}: {value}\n"
        
        return message
