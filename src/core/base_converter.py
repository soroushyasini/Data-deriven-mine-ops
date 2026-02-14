"""
Base converter with shared utilities for data processing.
Handles Persian text, date normalization, and common data cleaning tasks.
"""

import json
import re
from typing import Any, Dict, List, Optional
from pathlib import Path


class BaseConverter:
    """Base class for all data converters with shared utilities."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize with configuration directory."""
        self.config_dir = Path(config_dir)
        self.facilities = self._load_json_config("facilities.json")
        self.drivers = self._load_json_config("drivers.json")
        self.trucks = self._load_json_config("trucks.json")
    
    def _load_json_config(self, filename: str) -> Dict[str, Any]:
        """Load JSON configuration file with UTF-8 encoding."""
        config_path = self.config_dir / filename
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def clean_persian_number(value: Any) -> str:
        """
        Clean Persian numbers - remove commas, convert / to . for decimals.
        
        Args:
            value: Number as string, float, or int
            
        Returns:
            Cleaned string representation
        """
        if value is None or value == "":
            return ""
        
        # Convert to string
        value_str = str(value)
        
        # Remove commas (thousands separator)
        value_str = value_str.replace(',', '')
        
        # Convert forward slash to decimal point
        value_str = value_str.replace('/', '.')
        
        return value_str.strip()
    
    @staticmethod
    def normalize_date(date_str: str) -> str:
        """
        Normalize Jalali date format to YYYY/MM/DD.
        Handles both "1404/9/09" and "1404/09/09" formats.
        
        Args:
            date_str: Date string in Jalali calendar
            
        Returns:
            Normalized date string YYYY/MM/DD
        """
        if not date_str or date_str == "":
            return ""
        
        # Split by /
        parts = str(date_str).split('/')
        if len(parts) != 3:
            return date_str
        
        # Pad month and day with leading zeros if needed
        year, month, day = parts
        return f"{year}/{month.zfill(2)}/{day.zfill(2)}"
    
    @staticmethod
    def clean_truck_number(truck_num: Any) -> str:
        """
        Clean truck number - remove .0 suffix from floats.
        
        Args:
            truck_num: Truck number as string or float
            
        Returns:
            Cleaned truck number string
        """
        if truck_num is None or truck_num == "":
            return ""
        
        # Convert to string
        truck_str = str(truck_num)
        
        # Remove .0 suffix if present
        if truck_str.endswith('.0'):
            truck_str = truck_str[:-2]
        
        return truck_str
    
    def canonicalize_driver_name(self, driver_name: str) -> Dict[str, Any]:
        """
        Canonicalize driver name using the driver registry.
        
        Args:
            driver_name: Driver name as it appears in data
            
        Returns:
            Dict with canonical_name, is_known, and status
        """
        if not driver_name or driver_name.strip() == "":
            return {
                "original": driver_name,
                "canonical": "",
                "is_known": False,
                "status": "pending_review"
            }
        
        driver_name = driver_name.strip()
        
        # Check if driver is in canonical list
        canonical_drivers = self.drivers.get("canonical_drivers", {})
        
        for canonical_name, driver_info in canonical_drivers.items():
            aliases = driver_info.get("aliases", [])
            if driver_name in aliases or driver_name == canonical_name:
                return {
                    "original": driver_name,
                    "canonical": canonical_name,
                    "is_known": True,
                    "status": driver_info.get("status", "active")
                }
        
        # Unknown driver
        return {
            "original": driver_name,
            "canonical": driver_name,
            "is_known": False,
            "status": "pending_review"
        }
    
    @staticmethod
    def fix_column_typos(columns: List[str]) -> List[str]:
        """
        Fix known column name typos in Persian text.
        
        Args:
            columns: List of column names
            
        Returns:
            List of corrected column names
        """
        typo_map = {
            "تاربخ": "تاریخ",  # Date typo
            "جمع نتاژ": "جمع تناژ",  # Tonnage typo
            "Samole": "Sample"  # English typo
        }
        
        corrected = []
        for col in columns:
            corrected.append(typo_map.get(col, col))
        
        return corrected
    
    @staticmethod
    def is_summary_row(row_data: Dict[str, Any]) -> bool:
        """
        Check if row is a summary row (contains "جمع" - meaning "total").
        
        Args:
            row_data: Dictionary of row data
            
        Returns:
            True if row appears to be a summary row
        """
        for value in row_data.values():
            if isinstance(value, str) and "جمع" in value:
                return True
        return False
    
    @staticmethod
    def is_null_row(row_data: Dict[str, Any]) -> bool:
        """
        Check if row is completely null/empty.
        
        Args:
            row_data: Dictionary of row data
            
        Returns:
            True if all values are None or empty strings
        """
        for value in row_data.values():
            if value is not None and str(value).strip() != "":
                return False
        return True
    
    def write_json(self, data: Any, output_path: str) -> None:
        """
        Write data to JSON file with UTF-8 encoding and proper formatting.
        
        Args:
            data: Data to write
            output_path: Output file path
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def calculate_cost(tonnage_kg: float, cost_per_ton: float) -> float:
        """
        Calculate transport cost.
        IMPORTANT: cost_per_ton is per TON, so must divide kg by 1000.
        
        Args:
            tonnage_kg: Weight in kilograms
            cost_per_ton: Cost per ton in Rial
            
        Returns:
            Total cost in Rial
        """
        if tonnage_kg is None or cost_per_ton is None:
            return 0.0
        
        tonnage_tons = tonnage_kg / 1000.0
        return tonnage_tons * cost_per_ton
