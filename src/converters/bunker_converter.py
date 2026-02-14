"""
Bunker converter - converts bunker load data from Excel/JSON to standardized format.
Handles grinding facility → factory transport data.
"""

from typing import Any, Dict, List
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.base_converter import BaseConverter


class BunkerConverter(BaseConverter):
    """Converts bunker transport data to standardized format."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize bunker converter."""
        super().__init__(config_dir)
        
        # Sheet name to facility code mapping
        self.sheet_to_facility = {
            "رباط سفید": "A",
            "شن بتن": "B",
            "مس کاویان": "C"
        }
    
    def convert(self, input_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Convert bunker load data from multiple sheets.
        
        Args:
            input_data: Dictionary with sheet names as keys, list of records as values
            
        Returns:
            Standardized bunker data with metadata
        """
        all_loads = []
        statistics = {
            "total_loads": 0,
            "by_facility": {},
            "total_tonnage_kg": 0
        }
        
        for sheet_name, records in input_data.items():
            facility_code = self.sheet_to_facility.get(sheet_name)
            
            if not facility_code:
                # Try to match partial names
                for known_sheet, code in self.sheet_to_facility.items():
                    if known_sheet in sheet_name:
                        facility_code = code
                        break
            
            if not facility_code:
                print(f"Warning: Unknown sheet name: {sheet_name}")
                continue
            
            facility_loads = self._convert_facility_records(records, facility_code, sheet_name)
            all_loads.extend(facility_loads)
            
            # Update statistics
            facility_tonnage = sum(load.get("tonnage_kg", 0) for load in facility_loads)
            statistics["by_facility"][facility_code] = {
                "facility_name": self.facilities.get(facility_code, {}).get("name_en", "Unknown"),
                "load_count": len(facility_loads),
                "total_tonnage_kg": facility_tonnage
            }
            statistics["total_tonnage_kg"] += facility_tonnage
        
        statistics["total_loads"] = len(all_loads)
        
        return {
            "loads": all_loads,
            "statistics": statistics,
            "metadata": {
                "source": "bunker_transport",
                "transport_cost_per_ton_rial": 3200000,
                "transport_cost_per_ton_toman": 320000
            }
        }
    
    def _convert_facility_records(
        self,
        records: List[Dict[str, Any]],
        facility_code: str,
        sheet_name: str
    ) -> List[Dict[str, Any]]:
        """
        Convert records from a single facility sheet.
        
        Args:
            records: List of raw records
            facility_code: Facility code (A/B/C)
            sheet_name: Original sheet name
            
        Returns:
            List of standardized load records
        """
        loads = []
        
        for record in records:
            # Skip summary and null rows
            if self.is_summary_row(record) or self.is_null_row(record):
                continue
            
            # Fix column name typos before processing
            normalized_record = self._normalize_column_names(record)
            
            # Extract and clean fields
            row_number = normalized_record.get("row_number") or normalized_record.get("ردیف")
            date_raw = normalized_record.get("date") or normalized_record.get("تاریخ")
            tonnage_raw = normalized_record.get("tonnage_kg") or normalized_record.get("تناژ") or normalized_record.get("tonnage")
            cumulative_raw = normalized_record.get("cumulative_tonnage") or normalized_record.get("جمع تناژ")
            driver_raw = normalized_record.get("driver") or normalized_record.get("راننده")
            
            # Clean and process
            date = self.normalize_date(str(date_raw)) if date_raw else ""
            tonnage_kg = float(self.clean_persian_number(tonnage_raw)) if tonnage_raw else 0
            cumulative_tonnage = float(self.clean_persian_number(cumulative_raw)) if cumulative_raw else 0
            
            driver_info = self.canonicalize_driver_name(str(driver_raw)) if driver_raw else {
                "original": "",
                "canonical": "",
                "is_known": False,
                "status": "pending_review"
            }
            
            # Calculate transport cost
            transport_cost_rial = self.calculate_cost(tonnage_kg, 3200000)
            
            load = {
                "row_number": row_number,
                "date": date,
                "facility_code": facility_code,
                "facility_name": self.facilities.get(facility_code, {}).get("name_en", "Unknown"),
                "facility_name_fa": self.facilities.get(facility_code, {}).get("name_fa", ""),
                "sheet_name": sheet_name,
                "tonnage_kg": tonnage_kg,
                "cumulative_tonnage_kg": cumulative_tonnage,
                "driver_info": driver_info,
                "transport_cost_rial": transport_cost_rial,
                "transport_cost_toman": transport_cost_rial / 10
            }
            
            loads.append(load)
        
        return loads
    
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
            "تاربخ": "تاریخ",  # Date typo
            "جمع نتاژ": "جمع تناژ",  # Cumulative tonnage typo
        }
        
        for key, value in record.items():
            # Check if key has a known typo
            normalized_key = typo_map.get(key, key)
            normalized[normalized_key] = value
        
        return normalized


def main():
    """Example usage."""
    import json
    
    converter = BunkerConverter()
    
    # Example: Load from JSON file
    input_file = "data/samples/data_for_llm_enhanced.json"
    if Path(input_file).exists():
        with open(input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        result = converter.convert(input_data)
        
        # Write output
        output_file = "data/processed/bunker_loads_standardized.json"
        converter.write_json(result, output_file)
        print(f"Converted {result['statistics']['total_loads']} bunker loads")
        print(f"Output written to: {output_file}")


if __name__ == "__main__":
    main()
