"""
Tests for Telegram notification system.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.alerts.telegram_notifier import TelegramNotifier
from src.core.validator import ValidationAlert, AlertLevel


class TestTelegramNotifier:
    """Test Telegram notifier functionality."""
    
    def test_notifier_disabled_without_credentials(self):
        """Test that notifier is disabled when credentials are missing."""
        notifier = TelegramNotifier(bot_token=None, chat_id=None)
        assert notifier.enabled is False
    
    def test_notifier_enabled_with_credentials(self):
        """Test that notifier is enabled when credentials are provided."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat_id")
        assert notifier.enabled is True
        assert notifier.api_url == "https://api.telegram.org/bottest_token/sendMessage"
    
    def test_send_alert_buffers_alert(self):
        """Test that send_alert buffers alerts."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat_id")
        
        alert = ValidationAlert(
            level=AlertLevel.CRITICAL,
            rule="test_rule",
            message="Test alert message",
            data={"key": "value"}
        )
        
        notifier.send_alert(alert)
        assert len(notifier.alerts_buffer) == 1
        assert notifier.alerts_buffer[0] == alert
    
    def test_send_alert_does_nothing_when_disabled(self):
        """Test that send_alert does nothing when notifier is disabled."""
        notifier = TelegramNotifier(bot_token=None, chat_id=None)
        
        alert = ValidationAlert(
            level=AlertLevel.CRITICAL,
            rule="test_rule",
            message="Test alert message",
            data={}
        )
        
        notifier.send_alert(alert)
        assert len(notifier.alerts_buffer) == 0
    
    @patch('src.alerts.telegram_notifier.requests.post')
    def test_send_summary_sends_message(self, mock_post):
        """Test that send_summary sends a message via HTTP."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat_id")
        
        # Add some alerts
        notifier.send_alert(ValidationAlert(
            level=AlertLevel.CRITICAL,
            rule="rule1",
            message="Critical alert 1",
            data={}
        ))
        notifier.send_alert(ValidationAlert(
            level=AlertLevel.WARNING,
            rule="rule2",
            message="Warning alert",
            data={}
        ))
        notifier.send_alert(ValidationAlert(
            level=AlertLevel.CRITICAL,
            rule="rule3",
            message="Critical alert 2",
            data={}
        ))
        
        # Send summary
        notifier.send_summary()
        
        # Verify HTTP call was made
        assert mock_post.called
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.telegram.org/bottest_token/sendMessage"
        
        # Verify message content
        json_data = call_args[1]['json']
        assert json_data['chat_id'] == "test_chat_id"
        assert json_data['parse_mode'] == "Markdown"
        message_text = json_data['text']
        assert "Total alerts: *3*" in message_text
        assert "🚨 Critical: *2*" in message_text
        assert "⚠️ Warning: *1*" in message_text
        assert "Critical alert 1" in message_text
        assert "Critical alert 2" in message_text
        
        # Verify buffer was cleared
        assert len(notifier.alerts_buffer) == 0
    
    @patch('src.alerts.telegram_notifier.requests.post')
    def test_send_summary_limits_critical_alerts(self, mock_post):
        """Test that send_summary limits critical alerts to top 5."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat_id")
        
        # Add 10 critical alerts
        for i in range(10):
            notifier.send_alert(ValidationAlert(
                level=AlertLevel.CRITICAL,
                rule=f"rule{i}",
                message=f"Critical alert {i}",
                data={}
            ))
        
        # Send summary
        notifier.send_summary()
        
        # Verify message includes "...and 5 more"
        json_data = mock_post.call_args[1]['json']
        message_text = json_data['text']
        assert "_...and 5 more_" in message_text
    
    def test_send_summary_does_nothing_when_disabled(self):
        """Test that send_summary does nothing when notifier is disabled."""
        notifier = TelegramNotifier(bot_token=None, chat_id=None)
        notifier.send_summary()  # Should not raise any exceptions
    
    def test_send_summary_does_nothing_with_empty_buffer(self):
        """Test that send_summary does nothing when buffer is empty."""
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat_id")
        notifier.send_summary()  # Should not raise any exceptions
    
    @patch('src.alerts.telegram_notifier.requests.post')
    def test_send_summary_handles_request_errors(self, mock_post):
        """Test that send_summary handles request errors gracefully."""
        mock_post.side_effect = Exception("Network error")
        
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat_id")
        notifier.send_alert(ValidationAlert(
            level=AlertLevel.CRITICAL,
            rule="test_rule",
            message="Test alert",
            data={}
        ))
        
        # Should not raise exception
        notifier.send_summary()
        
        # Buffer should still be cleared
        assert len(notifier.alerts_buffer) == 0
    
    @patch('src.alerts.telegram_notifier.requests.post')
    def test_send_summary_handles_http_errors(self, mock_post):
        """Test that send_summary handles HTTP-level errors (non-200 status codes)."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request: invalid chat_id"
        mock_post.return_value = mock_response
        
        notifier = TelegramNotifier(bot_token="test_token", chat_id="test_chat_id")
        notifier.send_alert(ValidationAlert(
            level=AlertLevel.CRITICAL,
            rule="test_rule",
            message="Test alert",
            data={}
        ))
        
        # Should not raise exception
        notifier.send_summary()
        
        # Verify HTTP call was made
        assert mock_post.called
        
        # Buffer should still be cleared even with error
        assert len(notifier.alerts_buffer) == 0
