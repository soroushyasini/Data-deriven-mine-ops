"""
Alert engine - processes validation alerts and triggers notifications.
"""

import json
from typing import Any, Dict, List
from pathlib import Path

from src.core.validator import DataValidator, ValidationAlert


class AlertEngine:
    """Processes alerts and routes them to appropriate notifiers."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize alert engine."""
        self.config_dir = Path(config_dir)
        self.validator = DataValidator(config_dir)
        self.notifiers = []
    
    def add_notifier(self, notifier):
        """
        Add a notifier to the engine.
        
        Args:
            notifier: Notifier instance (must have send_alert method)
        """
        self.notifiers.append(notifier)
    
    def process_shipments(self, shipments: List[Dict[str, Any]]) -> List[ValidationAlert]:
        """
        Process shipments and generate alerts.
        
        Args:
            shipments: List of shipment records
            
        Returns:
            List of validation alerts
        """
        all_alerts = []
        
        for shipment in shipments:
            alerts = self.validator.validate_shipment(shipment)
            all_alerts.extend(alerts)
        
        return all_alerts
    
    def process_lab_samples(self, samples: List[Dict[str, Any]]) -> List[ValidationAlert]:
        """
        Process lab samples and generate alerts.
        
        Args:
            samples: List of lab sample records
            
        Returns:
            List of validation alerts
        """
        all_alerts = []
        
        for sample in samples:
            alerts = self.validator.validate_lab_sample(sample)
            all_alerts.extend(alerts)
        
        return all_alerts
    
    def send_alerts(self, alerts: List[ValidationAlert]):
        """
        Send alerts through all registered notifiers.
        
        Args:
            alerts: List of validation alerts
        """
        for alert in alerts:
            for notifier in self.notifiers:
                try:
                    notifier.send_alert(alert)
                except Exception as e:
                    print(f"Error sending alert via {notifier.__class__.__name__}: {e}")
    
    def process_and_send(
        self,
        shipments: List[Dict[str, Any]] = None,
        samples: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process data and send all alerts.
        
        Args:
            shipments: Optional list of shipments
            samples: Optional list of samples
            
        Returns:
            Summary of alerts generated
        """
        all_alerts = []
        
        if shipments:
            shipment_alerts = self.process_shipments(shipments)
            all_alerts.extend(shipment_alerts)
        
        if samples:
            sample_alerts = self.process_lab_samples(samples)
            all_alerts.extend(sample_alerts)
        
        # Send all alerts
        self.send_alerts(all_alerts)
        
        # Send summary for notifiers that support it
        for notifier in self.notifiers:
            if hasattr(notifier, 'send_summary'):
                notifier.send_summary()
        
        # Generate summary
        summary = {
            "total_alerts": len(all_alerts),
            "by_level": {},
            "by_rule": {}
        }
        
        for alert in all_alerts:
            level = alert.level.value
            rule = alert.rule
            
            summary["by_level"][level] = summary["by_level"].get(level, 0) + 1
            summary["by_rule"][rule] = summary["by_rule"].get(rule, 0) + 1
        
        return summary
