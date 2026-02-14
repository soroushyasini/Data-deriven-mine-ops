"""
Finance converter - handles financial records and driver payment tracking.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.base_converter import BaseConverter


class FinanceConverter(BaseConverter):
    """Converts financial records to standardized format."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize finance converter."""
        super().__init__(config_dir)
    
    def convert_payment_records(
        self,
        payment_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Convert driver payment records.
        
        Args:
            payment_records: List of payment records
            
        Returns:
            Standardized payment data
        """
        payments = []
        driver_balances = {}
        
        for record in payment_records:
            if self.is_null_row(record):
                continue
            
            payment = self._convert_payment_record(record)
            if payment:
                payments.append(payment)
                
                # Update driver balance
                driver_canonical = payment.get("driver_info", {}).get("canonical")
                if driver_canonical:
                    if driver_canonical not in driver_balances:
                        driver_balances[driver_canonical] = {
                            "total_owed": 0,
                            "total_paid": 0,
                            "balance": 0
                        }
                    
                    balance = driver_balances[driver_canonical]
                    amount = payment.get("amount_rial", 0)
                    
                    if payment.get("type") == "owed":
                        balance["total_owed"] += amount
                    elif payment.get("type") == "paid":
                        balance["total_paid"] += amount
                    
                    balance["balance"] = balance["total_owed"] - balance["total_paid"]
        
        return {
            "payments": payments,
            "driver_balances": driver_balances,
            "statistics": {
                "total_payments": len(payments),
                "total_owed_rial": sum(p.get("amount_rial", 0) for p in payments if p.get("type") == "owed"),
                "total_paid_rial": sum(p.get("amount_rial", 0) for p in payments if p.get("type") == "paid")
            }
        }
    
    def _convert_payment_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a single payment record.
        
        Args:
            record: Raw payment record
            
        Returns:
            Standardized payment dictionary
        """
        date_raw = record.get("date") or record.get("تاریخ")
        driver_raw = record.get("driver") or record.get("راننده")
        amount_raw = record.get("amount") or record.get("مبلغ")
        payment_type_raw = record.get("type") or record.get("نوع")
        notes_raw = record.get("notes") or record.get("توضیحات")
        
        date = self.normalize_date(str(date_raw)) if date_raw else ""
        
        driver_info = self.canonicalize_driver_name(str(driver_raw)) if driver_raw else {
            "original": "",
            "canonical": "",
            "is_known": False,
            "status": "pending_review"
        }
        
        amount_rial = 0
        if amount_raw:
            try:
                amount_rial = float(self.clean_persian_number(amount_raw))
            except (ValueError, TypeError):
                amount_rial = 0
        
        payment_type = str(payment_type_raw).lower() if payment_type_raw else "owed"
        notes = str(notes_raw).strip() if notes_raw else ""
        
        return {
            "date": date,
            "driver_info": driver_info,
            "amount_rial": amount_rial,
            "amount_toman": amount_rial / 10,
            "type": payment_type,
            "notes": notes
        }
    
    def aggregate_transport_costs(
        self,
        shipments: List[Dict[str, Any]],
        bunker_loads: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate transport costs from shipments and bunker loads.
        
        Args:
            shipments: List of truck shipments (mine → grinding)
            bunker_loads: List of bunker loads (grinding → factory)
            
        Returns:
            Aggregated cost data
        """
        # Mine to grinding costs
        mine_to_grinding = {
            "total_cost_rial": sum(s.get("total_cost_rial", 0) for s in shipments),
            "by_facility": {}
        }
        
        for shipment in shipments:
            facility = shipment.get("facility_code")
            if facility:
                if facility not in mine_to_grinding["by_facility"]:
                    mine_to_grinding["by_facility"][facility] = {
                        "shipment_count": 0,
                        "total_cost_rial": 0
                    }
                mine_to_grinding["by_facility"][facility]["shipment_count"] += 1
                mine_to_grinding["by_facility"][facility]["total_cost_rial"] += shipment.get("total_cost_rial", 0)
        
        # Grinding to factory costs
        grinding_to_factory = {
            "total_cost_rial": sum(b.get("transport_cost_rial", 0) for b in bunker_loads),
            "by_facility": {}
        }
        
        for load in bunker_loads:
            facility = load.get("facility_code")
            if facility:
                if facility not in grinding_to_factory["by_facility"]:
                    grinding_to_factory["by_facility"][facility] = {
                        "load_count": 0,
                        "total_cost_rial": 0
                    }
                grinding_to_factory["by_facility"][facility]["load_count"] += 1
                grinding_to_factory["by_facility"][facility]["total_cost_rial"] += load.get("transport_cost_rial", 0)
        
        total_transport_cost = mine_to_grinding["total_cost_rial"] + grinding_to_factory["total_cost_rial"]
        
        return {
            "mine_to_grinding": mine_to_grinding,
            "grinding_to_factory": grinding_to_factory,
            "total_transport_cost_rial": total_transport_cost,
            "total_transport_cost_toman": total_transport_cost / 10
        }


def main():
    """Example usage."""
    print("Finance converter - use via ingestion pipeline")


if __name__ == "__main__":
    main()
