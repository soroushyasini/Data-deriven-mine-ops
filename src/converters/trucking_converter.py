"""
Trucking converter - converts mine to grinding facility truck shipment data.
Handles driver name canonicalization and cost calculation fixes.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.base_converter import BaseConverter


class TruckingConverter(BaseConverter):
    """Converts truck shipment data to standardized format."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize trucking converter."""
        super().__init__(config_dir)
    
    def convert(self, input_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert truck shipment data.
        
        Args:
            input_data: List of raw shipment records
            
        Returns:
            Standardized trucking data with metadata
        """
        shipments = []
        statistics = {
            "total_shipments": 0,
            "by_destination": {},
            "total_tonnage_kg": 0,
            "total_cost_rial": 0,
            "unique_trucks": set(),
            "unique_drivers": set()
        }
        
        for record in input_data:
            # Skip summary and null rows
            if self.is_summary_row(record) or self.is_null_row(record):
                continue
            
            shipment = self._convert_shipment_record(record)
            if shipment:
                shipments.append(shipment)
                
                # Update statistics
                destination = shipment.get("destination", "Unknown")
                if destination not in statistics["by_destination"]:
                    statistics["by_destination"][destination] = {
                        "shipment_count": 0,
                        "total_tonnage_kg": 0,
                        "total_cost_rial": 0
                    }
                
                dest_stats = statistics["by_destination"][destination]
                dest_stats["shipment_count"] += 1
                dest_stats["total_tonnage_kg"] += shipment.get("tonnage_kg", 0)
                dest_stats["total_cost_rial"] += shipment.get("total_cost_rial", 0)
                
                statistics["total_tonnage_kg"] += shipment.get("tonnage_kg", 0)
                statistics["total_cost_rial"] += shipment.get("total_cost_rial", 0)
                
                if shipment.get("truck_number"):
                    statistics["unique_trucks"].add(shipment["truck_number"])
                
                driver_canonical = shipment.get("driver_info", {}).get("canonical")
                if driver_canonical:
                    statistics["unique_drivers"].add(driver_canonical)
        
        statistics["total_shipments"] = len(shipments)
        statistics["unique_trucks"] = list(statistics["unique_trucks"])
        statistics["unique_drivers"] = list(statistics["unique_drivers"])
        
        return {
            "shipments": shipments,
            "statistics": statistics,
            "metadata": {
                "source": "mine_to_grinding_transport"
            }
        }
    
    def _convert_shipment_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a single shipment record.
        
        Args:
            record: Raw shipment record
            
        Returns:
            Standardized shipment dictionary or None
        """
        # Extract fields (support both English and Persian column names)
        date_raw = record.get("date") or record.get("تاریخ")
        truck_raw = record.get("truck_number") or record.get("شماره کامیون")
        receipt_raw = record.get("receipt_number") or record.get("شماره رسید")
        tonnage_raw = record.get("tonnage_kg") or record.get("tonnage") or record.get("تناژ")
        destination_raw = record.get("destination") or record.get("مقصد")
        cost_per_ton_raw = record.get("cost_per_ton") or record.get("هزینه به ازای هر تن")
        driver_raw = record.get("driver_name") or record.get("نام راننده")
        notes_raw = record.get("notes") or record.get("توضیحات")
        row_num = record.get("row_number") or record.get("ردیف")
        
        # Clean and process
        date = self.normalize_date(str(date_raw)) if date_raw else ""
        truck_number = self.clean_truck_number(truck_raw) if truck_raw else ""
        receipt_number = str(receipt_raw) if receipt_raw and str(receipt_raw).strip() != "" else None
        
        tonnage_kg = 0
        if tonnage_raw:
            try:
                tonnage_kg = float(self.clean_persian_number(tonnage_raw))
            except (ValueError, TypeError):
                tonnage_kg = 0
        
        cost_per_ton = 0
        if cost_per_ton_raw:
            try:
                cost_per_ton = float(self.clean_persian_number(cost_per_ton_raw))
            except (ValueError, TypeError):
                cost_per_ton = 0
        
        destination = str(destination_raw).strip() if destination_raw else ""
        notes = str(notes_raw).strip() if notes_raw else ""
        
        # Canonicalize driver name
        driver_info = self.canonicalize_driver_name(str(driver_raw)) if driver_raw else {
            "original": "",
            "canonical": "",
            "is_known": False,
            "status": "pending_review"
        }
        
        # Calculate total cost (FIXED: cost_per_ton is per TON, not per kg)
        total_cost_rial = self.calculate_cost(tonnage_kg, cost_per_ton)
        
        # Map destination to facility
        facility_code = self._destination_to_facility(destination)
        
        shipment = {
            "row_number": row_num,
            "date": date,
            "truck_number": truck_number,
            "receipt_number": receipt_number,
            "tonnage_kg": tonnage_kg,
            "destination": destination,
            "facility_code": facility_code,
            "cost_per_ton_rial": cost_per_ton,
            "total_cost_rial": total_cost_rial,
            "total_cost_toman": total_cost_rial / 10,
            "driver_info": driver_info,
            "notes": notes
        }
        
        return shipment
    
    def _destination_to_facility(self, destination: str) -> Optional[str]:
        """
        Map destination name to facility code.
        
        Args:
            destination: Destination name
            
        Returns:
            Facility code (A/B/C) or None
        """
        for code, facility_info in self.facilities.items():
            truck_dest = facility_info.get("truck_dest", "")
            if truck_dest and truck_dest in destination:
                return code
        
        return None


def main():
    """Example usage."""
    import json
    
    converter = TruckingConverter()
    
    # Example: Load from JSON file
    input_file = "data/samples/trucking_data_for_llm.json"
    if Path(input_file).exists():
        with open(input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        result = converter.convert(input_data)
        
        # Write output
        output_file = "data/processed/truck_shipments_standardized.json"
        converter.write_json(result, output_file)
        print(f"Converted {result['statistics']['total_shipments']} truck shipments")
        print(f"Total tonnage: {result['statistics']['total_tonnage_kg']:,.0f} kg")
        print(f"Total cost: {result['statistics']['total_cost_rial']:,.0f} Rial")
        print(f"Output written to: {output_file}")


if __name__ == "__main__":
    main()
