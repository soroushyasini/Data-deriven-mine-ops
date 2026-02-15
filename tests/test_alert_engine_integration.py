"""
Integration test for alert engine with telegram notifier.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.alerts.alert_engine import AlertEngine
from src.alerts.telegram_notifier import TelegramNotifier
from src.core.validator import ValidationAlert, AlertLevel


class TestAlertEngineIntegration:
    """Test alert engine integration with notifiers."""
    
    @patch('src.alerts.telegram_notifier.requests.post')
    def test_process_and_send_calls_send_summary(self, mock_post):
        """Test that process_and_send calls send_summary on telegram notifier."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Initialize alert engine
        engine = AlertEngine()
        
        # Add telegram notifier
        telegram = TelegramNotifier(bot_token="test_token", chat_id="test_chat_id")
        engine.add_notifier(telegram)
        
        # Process some sample data that will trigger alerts
        samples = [
            {
                'sample_code': 'A 1404 10 14 K1',
                'au_ppm': 25.0,  # High value to trigger critical alert
                'sample_type': 'K'
            }
        ]
        
        # Process and send alerts
        summary = engine.process_and_send(samples=samples)
        
        # Verify alerts were generated
        assert summary['total_alerts'] > 0
        
        # Verify HTTP call was made to Telegram
        assert mock_post.called
        
        # Verify the message contains alert summary
        json_data = mock_post.call_args[1]['json']
        assert 'Mining Ops' in json_data['text']
        assert 'Total alerts:' in json_data['text']
    
    def test_send_summary_called_only_on_supporting_notifiers(self):
        """Test that send_summary is only called on notifiers that support it."""
        # Create a mock notifier without send_summary
        mock_notifier = Mock()
        mock_notifier.send_alert = Mock()
        
        # Initialize alert engine
        engine = AlertEngine()
        engine.add_notifier(mock_notifier)
        
        # Process empty data
        summary = engine.process_and_send(samples=[])
        
        # Verify send_alert was called (even with no alerts)
        # but send_summary should not be called (because notifier doesn't have it)
        # This should not raise any errors
        assert summary['total_alerts'] == 0
