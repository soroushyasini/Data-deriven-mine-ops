"""
Assay converter - converts lab analysis data to standardized format.
Handles sample code parsing and detection limit processing.
"""

import re
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.base_converter import BaseConverter


class AssayConverter(BaseConverter):
    """Converts lab assay data to standardized format."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize assay converter."""
        super().__init__(config_dir)
        
        # Load sample types
        self.sample_types = self._load_json_config("sample_types.json")
    
    def convert(self, input_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Convert lab assay data from multiple sheets (Solutions, Solids, Carbon).
        
        Args:
            input_data: Dictionary with sheet names as keys, list of records as values
            
        Returns:
            Standardized assay data with metadata
        """
        all_samples = []
        statistics = {
            "total_samples": 0,
            "by_type": {},
            "detection_rate": 0,
            "average_au_ppm": {}
        }
        
        for sheet_name, records in input_data.items():
            sheet_samples = self._convert_sheet_records(records, sheet_name)
            all_samples.extend(sheet_samples)
        
        # Calculate statistics
        statistics["total_samples"] = len(all_samples)
        
        # Group by sample type
        type_groups = {}
        for sample in all_samples:
            sample_type = sample.get("sample_type", "Unknown")
            if sample_type not in type_groups:
                type_groups[sample_type] = []
            type_groups[sample_type].append(sample)
        
        # Calculate stats per type
        detected_count = 0
        for sample_type, samples in type_groups.items():
            au_values = [s["au_ppm"] for s in samples if s.get("au_detected") and s.get("au_ppm") is not None]
            detected = sum(1 for s in samples if s.get("au_detected"))
            
            statistics["by_type"][sample_type] = {
                "count": len(samples),
                "detected": detected,
                "detection_rate": detected / len(samples) if samples else 0,
                "average_au_ppm": sum(au_values) / len(au_values) if au_values else 0,
                "max_au_ppm": max(au_values) if au_values else 0,
                "min_au_ppm": min(au_values) if au_values else 0
            }
            
            detected_count += detected
        
        statistics["detection_rate"] = detected_count / len(all_samples) if all_samples else 0
        
        return {
            "samples": all_samples,
            "statistics": statistics,
            "metadata": {
                "source": "lab_analysis",
                "detection_limit_ppm": 0.05
            }
        }
    
    def _convert_sheet_records(
        self,
        records: List[Dict[str, Any]],
        sheet_name: str
    ) -> List[Dict[str, Any]]:
        """
        Convert records from a single sheet.
        
        Args:
            records: List of raw records
            sheet_name: Sheet name (Solutions, Solids, Carbon)
            
        Returns:
            List of standardized sample records
        """
        samples = []
        
        for record in records:
            # Skip null rows
            if self.is_null_row(record):
                continue
            
            # Fix column name typos
            normalized_record = self._normalize_column_names(record)
            
            # Extract fields
            sample_code = normalized_record.get("sample_code") or normalized_record.get("Sample")
            au_raw = normalized_record.get("au_ppm") or normalized_record.get("Au (ppm)")
            
            # Parse sample code
            parsed_code = self._parse_sample_code(str(sample_code)) if sample_code else {}
            
            # Handle detection limit
            au_result = self._parse_au_value(au_raw)
            
            sample = {
                "sample_code": str(sample_code) if sample_code else "",
                "sheet_name": sheet_name,
                "au_ppm": au_result["value"],
                "au_detected": au_result["detected"],
                "below_detection_limit": au_result["below_limit"],
                "sample_type": parsed_code.get("sample_type", ""),
                "facility_code": parsed_code.get("facility", ""),
                "date": parsed_code.get("date", ""),
                "year": parsed_code.get("year", ""),
                "month": parsed_code.get("month", ""),
                "day": parsed_code.get("day", ""),
                "sample_number": parsed_code.get("sample_number", ""),
                "is_special": parsed_code.get("is_special", False)
            }
            
            samples.append(sample)
        
        return samples
    
    @staticmethod
    def _parse_sample_code(sample_code: str) -> Dict[str, Any]:
        """
        Parse sample code to extract metadata.
        
        Formats supported:
        - Spaced: C 1404 10 14 K2
        - Concatenated: A1404105L, C14041014K, RC14041010, 14041017CR3
        
        Args:
            sample_code: Sample code string
            
        Returns:
            Dictionary with parsed fields
        """
        if not sample_code or sample_code.strip() == "":
            return {}
        
        sample_code = sample_code.strip()
        
        # Special codes
        special_codes = {"F2(T3)", "SR2"}
        if sample_code in special_codes:
            return {
                "facility": None,
                "date": None,
                "sample_type": sample_code[:50],
                "is_special": True,
                "year": "",
                "month": "",
                "day": "",
                "sample_number": ""
            }
        
        # Try spaced pattern first (backward compatibility)
        pattern_spaced = r'^([A-C])\s+(\d{4})\s+(\d{1,2})\s+(\d{1,2})\s+([A-Z]{1,2})(\d*)$'
        match = re.match(pattern_spaced, sample_code)
        
        if match:
            facility, year, month, day, sample_type, sample_num = match.groups()
            date_str = f"{year}/{month.zfill(2)}/{day.zfill(2)}"
            
            return {
                "facility": facility,
                "year": year,
                "month": month.zfill(2),
                "day": day.zfill(2),
                "date": date_str,
                "sample_type": sample_type[:50],
                "sample_number": sample_num if sample_num else "",
                "is_special": False
            }
        
        # Try concatenated pattern: optional prefix letters + 1404 + month(2 digits) + day(1-2 digits) + optional suffix
        pattern_concat = r'^([A-Z]{0,2}?)(\d{4})(\d{2})(\d{1,2})([A-Z]+\d*)?$'
        match = re.match(pattern_concat, sample_code)
        
        if match:
            prefix, year, month, day, suffix = match.groups()
            suffix = suffix or ""
            
            # Determine sample type from suffix
            sample_type = suffix if suffix else "unknown"
            
            # Determine facility from prefix
            facility = prefix if prefix in ("A", "B", "C") else None
            
            # Normalize date
            date_str = f"{year}/{month}/{day.zfill(2)}"
            
            return {
                "facility": facility,
                "prefix": prefix,
                "year": year,
                "month": month,
                "day": day.zfill(2),
                "date": date_str,
                "sample_type": sample_type[:50],
                "sample_number": "",
                "is_special": False
            }
        
        # Fallback - couldn't parse
        return {
            "sample_type": sample_code[:50],
            "is_special": False,
            "parse_error": True,
            "year": "",
            "month": "",
            "day": "",
            "sample_number": ""
        }
    
    @staticmethod
    def _parse_au_value(au_raw: Any) -> Dict[str, Any]:
        """
        Parse Au value, handling detection limits like "<0.05".
        
        Args:
            au_raw: Raw Au value (string, float, or None)
            
        Returns:
            Dictionary with value, detected flag, and below_limit flag
        """
        if au_raw is None or au_raw == "":
            return {
                "value": None,
                "detected": False,
                "below_limit": False
            }
        
        # Check if it's a string with < prefix
        au_str = str(au_raw).strip()
        
        if au_str.startswith("<"):
            # Below detection limit
            limit_str = au_str[1:].strip()
            try:
                limit_value = float(limit_str)
                return {
                    "value": limit_value,
                    "detected": False,
                    "below_limit": True
                }
            except ValueError:
                return {
                    "value": None,
                    "detected": False,
                    "below_limit": True
                }
        
        # Normal numeric value
        try:
            value = float(au_str)
            return {
                "value": value,
                "detected": True,
                "below_limit": False
            }
        except ValueError:
            return {
                "value": None,
                "detected": False,
                "below_limit": False
            }
    
    @staticmethod
    def _normalize_column_names(record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize column names - fix typos.
        
        Args:
            record: Raw record dictionary
            
        Returns:
            Record with normalized column names
        """
        normalized = {}
        
        typo_map = {
            "Samole": "Sample",  # English typo
        }
        
        for key, value in record.items():
            normalized_key = typo_map.get(key, key)
            normalized[normalized_key] = value
        
        return normalized


def main():
    """Example usage."""
    import json
    
    converter = AssayConverter()
    
    # Example: Load from JSON file
    input_file = "data/samples/lab_data_for_llm.json"
    if Path(input_file).exists():
        with open(input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        result = converter.convert(input_data)
        
        # Write output
        output_file = "data/processed/lab_samples_standardized.json"
        converter.write_json(result, output_file)
        print(f"Converted {result['statistics']['total_samples']} lab samples")
        print(f"Detection rate: {result['statistics']['detection_rate']:.1%}")
        print(f"Output written to: {output_file}")


if __name__ == "__main__":
    main()
