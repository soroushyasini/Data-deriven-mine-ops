"""
Log file notifier for persistent alert records.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.validator import ValidationAlert


class LogNotifier:
    """Writes alerts to a log file."""
    
    def __init__(self, log_file: str = "logs/alerts.log"):
        """
        Initialize log notifier.
        
        Args:
            log_file: Path to log file
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.enabled = True
    
    def send_alert(self, alert: ValidationAlert):
        """
        Write alert to log file.
        
        Args:
            alert: ValidationAlert instance
        """
        if not self.enabled:
            return
        
        # Format as JSON line
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": alert.level.value,
            "rule": alert.rule,
            "message": alert.message,
            "data": alert.data
        }
        
        # Append to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def read_alerts(self, limit: Optional[int] = None) -> list:
        """
        Read alerts from log file.
        
        Args:
            limit: Maximum number of alerts to read (from end)
            
        Returns:
            List of alert dictionaries
        """
        if not self.log_file.exists():
            return []
        
        alerts = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    alert = json.loads(line)
                    alerts.append(alert)
                except json.JSONDecodeError:
                    continue
        
        if limit:
            alerts = alerts[-limit:]
        
        return alerts
