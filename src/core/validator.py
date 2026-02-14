"""
Data validation engine for quality checks and alert generation.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ValidationAlert:
    """Represents a validation alert."""
    
    def __init__(self, level: AlertLevel, rule: str, message: str, data: Dict[str, Any]):
        self.level = level
        self.rule = rule
        self.message = message
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "level": self.level.value,
            "rule": self.rule,
            "message": self.message,
            "data": self.data
        }


class DataValidator:
    """Validates data against configured rules."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize with configuration directory."""
        self.config_dir = Path(config_dir)
        self.rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules from JSON config."""
        rules_path = self.config_dir / "validation_rules.json"
        if rules_path.exists():
            with open(rules_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def validate_lab_sample(self, sample: Dict[str, Any]) -> List[ValidationAlert]:
        """
        Validate lab sample data against rules.
        
        Args:
            sample: Lab sample dictionary with sample_code, au_ppm, sample_type
            
        Returns:
            List of validation alerts
        """
        alerts = []
        
        sample_code = sample.get("sample_code", "")
        au_ppm = sample.get("au_ppm")
        sample_type = sample.get("sample_type", "")
        
        # Check if sample code is valid
        if not self._is_valid_sample_code(sample_code):
            alerts.append(ValidationAlert(
                level=AlertLevel.CRITICAL,
                rule="invalid_sample_code",
                message=f"Sample code doesn't match expected format: {sample_code}",
                data={"sample_code": sample_code}
            ))
        
        # Skip further checks if au_ppm is not a number or is None
        if au_ppm is None or not isinstance(au_ppm, (int, float)):
            return alerts
        
        # Check ore input (K) thresholds
        if sample_type == "K":
            ore_rules = self.rules.get("ore_input", {})
            warning_threshold = ore_rules.get("warning_threshold_ppm", 5.0)
            critical_threshold = ore_rules.get("critical_threshold_ppm", 20.0)
            
            if au_ppm > critical_threshold:
                alerts.append(ValidationAlert(
                    level=AlertLevel.CRITICAL,
                    rule="ore_input_critical",
                    message=f"Ore input Au > {critical_threshold} ppm: {au_ppm} ppm - verify immediately",
                    data={"sample_code": sample_code, "au_ppm": au_ppm}
                ))
            elif au_ppm > warning_threshold:
                alerts.append(ValidationAlert(
                    level=AlertLevel.WARNING,
                    rule="ore_input_warning",
                    message=f"Ore input Au > {warning_threshold} ppm: {au_ppm} ppm - high grade, verify",
                    data={"sample_code": sample_code, "au_ppm": au_ppm}
                ))
        
        # Check tailings (T) threshold
        elif sample_type == "T":
            tailings_rules = self.rules.get("tailings", {})
            critical_threshold = tailings_rules.get("critical_threshold_ppm", 0.2)
            
            if au_ppm > critical_threshold:
                alerts.append(ValidationAlert(
                    level=AlertLevel.CRITICAL,
                    rule="tailings_loss",
                    message=f"Tailings Au > {critical_threshold} ppm: {au_ppm} ppm - gold loss too high",
                    data={"sample_code": sample_code, "au_ppm": au_ppm}
                ))
        
        # Check return water (RC) threshold
        elif sample_type == "RC":
            rc_rules = self.rules.get("return_water", {})
            critical_threshold = rc_rules.get("critical_threshold_ppm", 0.05)
            
            if au_ppm > critical_threshold:
                alerts.append(ValidationAlert(
                    level=AlertLevel.CRITICAL,
                    rule="return_water_leak",
                    message=f"Return water Au > {critical_threshold} ppm: {au_ppm} ppm - circuit leak",
                    data={"sample_code": sample_code, "au_ppm": au_ppm}
                ))
        
        # Check carbon (CR) threshold (below threshold is a warning)
        elif sample_type == "CR":
            carbon_rules = self.rules.get("carbon", {})
            warning_threshold = carbon_rules.get("warning_threshold_ppm", 200.0)
            
            if au_ppm < warning_threshold:
                alerts.append(ValidationAlert(
                    level=AlertLevel.WARNING,
                    rule="carbon_exhausted",
                    message=f"Carbon Au < {warning_threshold} ppm: {au_ppm} ppm - carbon may be exhausted",
                    data={"sample_code": sample_code, "au_ppm": au_ppm}
                ))
        
        return alerts
    
    def validate_tonnage(self, tonnage_kg: float, context: Dict[str, Any]) -> List[ValidationAlert]:
        """
        Validate tonnage against acceptable ranges.
        
        Args:
            tonnage_kg: Tonnage in kilograms
            context: Additional context (record type, date, etc.)
            
        Returns:
            List of validation alerts
        """
        alerts = []
        
        tonnage_rules = self.rules.get("tonnage", {})
        min_kg = tonnage_rules.get("min_warning_kg", 15000)
        max_kg = tonnage_rules.get("max_warning_kg", 32000)
        
        if tonnage_kg < min_kg or tonnage_kg > max_kg:
            alerts.append(ValidationAlert(
                level=AlertLevel.WARNING,
                rule="unusual_tonnage",
                message=f"Tonnage {tonnage_kg} kg outside normal range [{min_kg}, {max_kg}]",
                data={"tonnage_kg": tonnage_kg, **context}
            ))
        
        return alerts
    
    def validate_shipment(self, shipment: Dict[str, Any]) -> List[ValidationAlert]:
        """
        Validate truck shipment data.
        
        Args:
            shipment: Shipment dictionary
            
        Returns:
            List of validation alerts
        """
        alerts = []
        
        # Check for missing receipt number
        receipt_number = shipment.get("receipt_number")
        if not receipt_number or str(receipt_number).strip() == "":
            alerts.append(ValidationAlert(
                level=AlertLevel.WARNING,
                rule="missing_receipt",
                message="Missing receipt number - data quality issue",
                data={"row": shipment.get("row_number"), "date": shipment.get("date")}
            ))
        
        # Check for unknown driver
        driver_info = shipment.get("driver_info", {})
        if not driver_info.get("is_known", False):
            alerts.append(ValidationAlert(
                level=AlertLevel.WARNING,
                rule="unknown_driver",
                message=f"Unknown driver: {driver_info.get('original')} - add to registry",
                data={"driver": driver_info.get("original")}
            ))
        
        # Validate tonnage
        tonnage_kg = shipment.get("tonnage_kg")
        if tonnage_kg:
            tonnage_alerts = self.validate_tonnage(
                tonnage_kg,
                {"record_type": "shipment", "date": shipment.get("date")}
            )
            alerts.extend(tonnage_alerts)
        
        return alerts
    
    @staticmethod
    def _is_valid_sample_code(sample_code: str) -> bool:
        """
        Check if sample code matches expected pattern.
        Pattern: C 1404 10 14 K2 (facility year month day type+number)
        
        Args:
            sample_code: Sample code string
            
        Returns:
            True if valid format
        """
        if not sample_code:
            return False
        
        # Special codes that don't follow the pattern
        special_codes = ["F2(T3)", "SR2"]
        if sample_code in special_codes:
            return True
        
        # Standard pattern: Letter Space Year Space Month Space Day Space Type+Number
        # Example: C 1404 10 14 K2
        import re
        pattern = r'^[A-C]\s+\d{4}\s+\d{1,2}\s+\d{1,2}\s+[A-Z]{1,2}\d*$'
        return bool(re.match(pattern, sample_code))
