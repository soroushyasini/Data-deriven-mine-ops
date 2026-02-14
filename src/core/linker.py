"""
Data linking engine - traces lab results back to bunker loads and truck shipments.
This is the core feature that connects the entire supply chain.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class SampleCodeParser:
    """Parse sample codes to extract metadata."""
    
    @staticmethod
    def parse(sample_code: str) -> Optional[Dict[str, Any]]:
        """
        Parse sample code to extract facility, date, and sample type.
        
        Formats supported:
        - Spaced: C 1404 10 14 K2
                  │  │    │  │  │
                  │  │    │  │  └─ Sample type + number
                  │  │    │  └──── Day
                  │  │    └─────── Month
                  │  └──────────── Year (Jalali)
                  └─────────────── Facility (A/B/C)
        - Concatenated: A1404105L, C14041014K, RC14041010, 14041017CR3
        
        Args:
            sample_code: Sample code string
            
        Returns:
            Dictionary with parsed fields or None if invalid
        """
        if not sample_code:
            return None
        
        sample_code = sample_code.strip()
        
        # Special codes
        special_codes = {
            "F2(T3)": {"facility": None, "date": None, "sample_type": "F", "is_special": True},
            "SR2": {"facility": None, "date": None, "sample_type": "SR", "is_special": True}
        }
        if sample_code in special_codes:
            return special_codes[sample_code]
        
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
                "sample_type": sample_type,
                "sample_number": sample_num if sample_num else None,
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
                "sample_type": sample_type,
                "sample_number": None,
                "is_special": False
            }
        
        # Fallback - couldn't parse
        return None


class DataLinker:
    """Links lab samples to bunker loads and truck shipments."""
    
    def __init__(self, facilities_config: Dict[str, Any]):
        """
        Initialize with facilities configuration.
        
        Args:
            facilities_config: Facility mapping (code -> names)
        """
        self.facilities = facilities_config
        self.parser = SampleCodeParser()
    
    def link_sample_to_bunker(
        self,
        sample: Dict[str, Any],
        bunker_loads: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Link a lab sample to its source bunker load.
        
        Args:
            sample: Lab sample dictionary with sample_code
            bunker_loads: List of bunker load records
            
        Returns:
            Matching bunker load or None
        """
        sample_code = sample.get("sample_code", "")
        parsed = self.parser.parse(sample_code)
        
        if not parsed or parsed.get("is_special"):
            return None
        
        facility = parsed.get("facility")
        sample_date = parsed.get("date")
        
        # Find bunker loads from same facility on same date
        matches = []
        for load in bunker_loads:
            load_facility = load.get("facility_code")
            load_date = load.get("date")
            
            if load_facility == facility and load_date == sample_date:
                matches.append(load)
        
        # If multiple matches, return the first (could be improved with time matching)
        return matches[0] if matches else None
    
    def link_bunker_to_shipment(
        self,
        bunker_load: Dict[str, Any],
        shipments: List[Dict[str, Any]],
        date_tolerance_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Link a bunker load to source truck shipment(s).
        
        Since bunker loads aggregate multiple truck shipments,
        this returns all shipments within date range to the same facility.
        
        Args:
            bunker_load: Bunker load dictionary
            shipments: List of truck shipment records
            date_tolerance_days: Days before bunker load to search for shipments
            
        Returns:
            List of matching shipments (may be multiple)
        """
        facility_code = bunker_load.get("facility_code")
        bunker_date = bunker_load.get("date")
        
        if not facility_code or not bunker_date:
            return []
        
        # Get facility destination name from config
        facility_info = self.facilities.get(facility_code, {})
        truck_dest = facility_info.get("truck_dest")
        
        if not truck_dest:
            return []
        
        # Find shipments to this destination within date range
        matches = []
        
        for shipment in shipments:
            shipment_dest = shipment.get("destination")
            shipment_date = shipment.get("date")
            
            if shipment_dest == truck_dest:
                # Check if shipment is within tolerance before bunker date
                if self._is_within_date_range(
                    shipment_date, bunker_date, date_tolerance_days
                ):
                    matches.append(shipment)
        
        return matches
    
    def link_sample_to_source(
        self,
        sample: Dict[str, Any],
        bunker_loads: List[Dict[str, Any]],
        shipments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Complete trace: Lab sample → Bunker load → Truck shipment(s) → Mine.
        
        Args:
            sample: Lab sample dictionary
            bunker_loads: List of bunker loads
            shipments: List of truck shipments
            
        Returns:
            Dictionary with linked records
        """
        result = {
            "sample": sample,
            "bunker_load": None,
            "shipments": [],
            "trace_complete": False
        }
        
        # Step 1: Link to bunker
        bunker = self.link_sample_to_bunker(sample, bunker_loads)
        if not bunker:
            return result
        
        result["bunker_load"] = bunker
        
        # Step 2: Link bunker to shipments
        linked_shipments = self.link_bunker_to_shipment(bunker, shipments)
        result["shipments"] = linked_shipments
        
        # Trace is complete if we found at least one shipment
        result["trace_complete"] = len(linked_shipments) > 0
        
        return result
    
    @staticmethod
    def _is_within_date_range(
        shipment_date: str,
        bunker_date: str,
        tolerance_days: int
    ) -> bool:
        """
        Check if shipment date is within tolerance days before bunker date.
        
        Args:
            shipment_date: Shipment date (YYYY/MM/DD)
            bunker_date: Bunker date (YYYY/MM/DD)
            tolerance_days: Days of tolerance
            
        Returns:
            True if within range
        """
        try:
            # For Jalali dates, we do simple string comparison
            # A more robust solution would use jdatetime for actual date math
            # For now, check if dates are close (same or shipment before bunker)
            return shipment_date <= bunker_date
        except Exception:
            return False
    
    def generate_trace_report(
        self,
        samples: List[Dict[str, Any]],
        bunker_loads: List[Dict[str, Any]],
        shipments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive trace report for all samples.
        
        Args:
            samples: List of lab samples
            bunker_loads: List of bunker loads
            shipments: List of shipments
            
        Returns:
            Report with statistics and linked records
        """
        linked_samples = []
        unlinked_samples = []
        
        for sample in samples:
            trace = self.link_sample_to_source(sample, bunker_loads, shipments)
            
            if trace["trace_complete"]:
                linked_samples.append(trace)
            else:
                unlinked_samples.append(trace)
        
        return {
            "total_samples": len(samples),
            "linked_count": len(linked_samples),
            "unlinked_count": len(unlinked_samples),
            "link_rate": len(linked_samples) / len(samples) if samples else 0,
            "linked_samples": linked_samples,
            "unlinked_samples": unlinked_samples
        }
