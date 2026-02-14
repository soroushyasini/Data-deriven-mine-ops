"""
Grade report - Au ppm analysis per facility.
"""

from typing import Any, Dict, List
from statistics import mean, stdev

from src.reports.base_report import BaseReport


class GradeReport(BaseReport):
    """Gold grade analysis report generator."""
    
    def generate_data(
        self,
        facility_code: str,
        lab_samples: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate grade report data for a facility.
        
        Args:
            facility_code: Facility code (A/B/C)
            lab_samples: List of lab samples
            
        Returns:
            Report data dictionary
        """
        lab_samples = lab_samples or []
        
        # Filter to facility
        facility_samples = [s for s in lab_samples if s.get('facility_code') == facility_code]
        
        # Group by sample type
        by_type = {}
        for sample_type in ['K', 'L', 'T', 'CR', 'RC']:
            type_samples = [s for s in facility_samples if s.get('sample_type') == sample_type]
            
            # Extract Au values (only detected)
            au_values = [
                s.get('au_ppm', 0)
                for s in type_samples
                if s.get('au_detected') and s.get('au_ppm') is not None
            ]
            
            if au_values:
                by_type[sample_type] = {
                    'count': len(type_samples),
                    'detected': len(au_values),
                    'average': mean(au_values),
                    'min': min(au_values),
                    'max': max(au_values),
                    'stdev': stdev(au_values) if len(au_values) > 1 else 0,
                    'samples': type_samples
                }
        
        # Identify outliers (values > 2 std dev from mean)
        outliers = []
        for sample_type, type_data in by_type.items():
            if type_data['stdev'] > 0:
                threshold = type_data['average'] + 2 * type_data['stdev']
                for sample in type_data['samples']:
                    au = sample.get('au_ppm', 0)
                    if sample.get('au_detected') and au > threshold:
                        outliers.append({
                            'sample_code': sample.get('sample_code'),
                            'sample_type': sample_type,
                            'au_ppm': au,
                            'threshold': threshold
                        })
        
        facility_names = {'A': 'Hejazian', 'B': 'Shen Beton', 'C': 'Kavian'}
        
        return {
            'title': f'Grade Report - {facility_names.get(facility_code, facility_code)}',
            'facility_code': facility_code,
            'facility_name': facility_names.get(facility_code, facility_code),
            'by_type': by_type,
            'outliers': outliers
        }
    
    def format_markdown(self, data: Dict[str, Any]) -> str:
        """Format grade report as Markdown."""
        md = f"# {data['title']}\n\n"
        md += f"**Facility:** {data['facility_name']} ({data['facility_code']})\n\n"
        
        # Sample type definitions
        type_names = {
            'K': 'Ore Input',
            'L': 'Solution',
            'T': 'Tailings',
            'CR': 'Carbon',
            'RC': 'Return Water'
        }
        
        # Statistics by type
        md += "## Gold Content by Sample Type\n\n"
        
        if not data['by_type']:
            md += "*No data available.*\n\n"
        else:
            md += "| Type | Description | Samples | Avg (ppm) | Min (ppm) | Max (ppm) | Std Dev |\n"
            md += "|------|-------------|---------|-----------|-----------|-----------|----------|\n"
            
            for sample_type in ['K', 'L', 'T', 'CR', 'RC']:
                if sample_type in data['by_type']:
                    type_data = data['by_type'][sample_type]
                    md += f"| {sample_type} | {type_names.get(sample_type, '')} | "
                    md += f"{type_data['detected']}/{type_data['count']} | "
                    md += f"{type_data['average']:.3f} | "
                    md += f"{type_data['min']:.3f} | "
                    md += f"{type_data['max']:.3f} | "
                    md += f"{type_data['stdev']:.3f} |\n"
            
            md += "\n"
        
        # Outliers
        md += "## Outliers (> 2σ from mean)\n\n"
        if data['outliers']:
            md += "| Sample Code | Type | Au (ppm) | Threshold |\n"
            md += "|-------------|------|----------|------------|\n"
            for outlier in data['outliers']:
                md += f"| {outlier['sample_code']} | {outlier['sample_type']} | "
                md += f"{outlier['au_ppm']:.3f} | {outlier['threshold']:.3f} |\n"
        else:
            md += "*No outliers detected.*\n"
        
        md += "\n"
        
        # Recommendations
        md += "## Recommendations\n\n"
        
        # Check ore input
        if 'K' in data['by_type']:
            ore_avg = data['by_type']['K']['average']
            if ore_avg > 5:
                md += "- ⚠️ **High ore grade detected** - Consider optimization of processing parameters\n"
            elif ore_avg < 0.5:
                md += "- ⚠️ **Low ore grade** - Review mining operations\n"
        
        # Check tailings
        if 'T' in data['by_type']:
            tailings_avg = data['by_type']['T']['average']
            if tailings_avg > 0.2:
                md += "- 🚨 **High gold loss in tailings** - Process optimization required\n"
        
        # Check return water
        if 'RC' in data['by_type']:
            rc_avg = data['by_type']['RC']['average']
            if rc_avg > 0.05:
                md += "- 🚨 **Gold in return water** - Circuit leak suspected\n"
        
        # Check carbon
        if 'CR' in data['by_type']:
            carbon_avg = data['by_type']['CR']['average']
            if carbon_avg < 200:
                md += "- ⚠️ **Low carbon loading** - Carbon may need replacement\n"
        
        return md
