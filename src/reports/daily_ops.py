"""
Daily operations report - trucks, bunkers, samples for the day.
"""

from typing import Any, Dict, List
from datetime import datetime

from src.reports.base_report import BaseReport


class DailyOpsReport(BaseReport):
    """Daily operations report generator."""
    
    def generate_data(
        self,
        date: str,
        shipments: List[Dict[str, Any]] = None,
        bunker_loads: List[Dict[str, Any]] = None,
        lab_samples: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate daily operations data.
        
        Args:
            date: Target date (Jalali YYYY/MM/DD)
            shipments: List of shipments
            bunker_loads: List of bunker loads
            lab_samples: List of lab samples
            
        Returns:
            Report data dictionary
        """
        shipments = shipments or []
        bunker_loads = bunker_loads or []
        lab_samples = lab_samples or []
        
        # Filter to target date
        day_shipments = [s for s in shipments if s.get('date') == date]
        day_loads = [b for b in bunker_loads if b.get('date') == date]
        day_samples = [s for s in lab_samples if s.get('date') == date]
        
        # Calculate statistics
        total_shipped_kg = sum(s.get('tonnage_kg', 0) for s in day_shipments)
        total_loaded_kg = sum(b.get('tonnage_kg', 0) for b in day_loads)
        
        # By facility
        by_facility = {}
        for code in ['A', 'B', 'C']:
            facility_shipments = [s for s in day_shipments if s.get('facility_code') == code]
            facility_loads = [b for b in day_loads if b.get('facility_code') == code]
            
            by_facility[code] = {
                'shipments': len(facility_shipments),
                'shipped_kg': sum(s.get('tonnage_kg', 0) for s in facility_shipments),
                'loads': len(facility_loads),
                'loaded_kg': sum(b.get('tonnage_kg', 0) for b in facility_loads)
            }
        
        return {
            'title': f'Daily Operations Report - {date}',
            'date': date,
            'shipments': {
                'count': len(day_shipments),
                'total_kg': total_shipped_kg,
                'records': day_shipments
            },
            'bunker_loads': {
                'count': len(day_loads),
                'total_kg': total_loaded_kg,
                'records': day_loads
            },
            'lab_samples': {
                'count': len(day_samples),
                'records': day_samples
            },
            'by_facility': by_facility
        }
    
    def format_markdown(self, data: Dict[str, Any]) -> str:
        """Format daily operations report as Markdown."""
        md = f"# {data['title']}\n\n"
        md += f"**Date:** {data['date']}\n\n"
        
        # Summary
        md += "## Summary\n\n"
        md += f"- **Truck Shipments:** {data['shipments']['count']} ({data['shipments']['total_kg']:,.0f} kg)\n"
        md += f"- **Bunker Loads:** {data['bunker_loads']['count']} ({data['bunker_loads']['total_kg']:,.0f} kg)\n"
        md += f"- **Lab Samples:** {data['lab_samples']['count']}\n\n"
        
        # By Facility
        md += "## By Facility\n\n"
        facility_names = {'A': 'Hejazian', 'B': 'Shen Beton', 'C': 'Kavian'}
        
        for code, name in facility_names.items():
            facility_data = data['by_facility'][code]
            md += f"### {name} (Facility {code})\n\n"
            md += f"- Shipments: {facility_data['shipments']} ({facility_data['shipped_kg']:,.0f} kg)\n"
            md += f"- Bunker Loads: {facility_data['loads']} ({facility_data['loaded_kg']:,.0f} kg)\n\n"
        
        # Detailed Tables
        md += "## Truck Shipments\n\n"
        if data['shipments']['records']:
            md += "| Truck | Destination | Tonnage (kg) | Cost (Rial) |\n"
            md += "|-------|-------------|--------------|-------------|\n"
            for s in data['shipments']['records']:
                md += f"| {s.get('truck_number', 'N/A')} | {s.get('destination', 'N/A')} | "
                md += f"{s.get('tonnage_kg', 0):,.0f} | {s.get('total_cost_rial', 0):,.0f} |\n"
        else:
            md += "*No shipments on this date.*\n"
        
        md += "\n## Bunker Loads\n\n"
        if data['bunker_loads']['records']:
            md += "| Facility | Tonnage (kg) | Driver |\n"
            md += "|----------|--------------|--------|\n"
            for b in data['bunker_loads']['records']:
                driver = b.get('driver_info', {}).get('canonical', 'N/A')
                md += f"| {b.get('facility_code', 'N/A')} | {b.get('tonnage_kg', 0):,.0f} | {driver} |\n"
        else:
            md += "*No bunker loads on this date.*\n"
        
        md += "\n## Lab Samples\n\n"
        if data['lab_samples']['records']:
            md += "| Sample Code | Type | Au (ppm) |\n"
            md += "|-------------|------|----------|\n"
            for s in data['lab_samples']['records']:
                au_str = f"{s.get('au_ppm', 0):.3f}" if s.get('au_detected') else "< DL"
                md += f"| {s.get('sample_code', 'N/A')} | {s.get('sample_type', 'N/A')} | {au_str} |\n"
        else:
            md += "*No samples on this date.*\n"
        
        return md
