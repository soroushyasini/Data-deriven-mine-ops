#!/usr/bin/env python3
"""
Generate specific reports.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import argparse

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.reports.daily_ops import DailyOpsReport
from src.reports.grade_report import GradeReport


def load_processed_data():
    """Load processed data files."""
    processed_dir = Path("data/processed")
    
    data = {
        'shipments': [],
        'bunker_loads': [],
        'lab_samples': []
    }
    
    # Load shipments
    shipments_file = processed_dir / "truck_shipments_standardized.json"
    if shipments_file.exists():
        with open(shipments_file, 'r', encoding='utf-8') as f:
            shipments_data = json.load(f)
            data['shipments'] = shipments_data.get('shipments', [])
    
    # Load bunker loads
    bunker_file = processed_dir / "bunker_loads_standardized.json"
    if bunker_file.exists():
        with open(bunker_file, 'r', encoding='utf-8') as f:
            bunker_data = json.load(f)
            data['bunker_loads'] = bunker_data.get('loads', [])
    
    # Load lab samples
    lab_file = processed_dir / "lab_samples_standardized.json"
    if lab_file.exists():
        with open(lab_file, 'r', encoding='utf-8') as f:
            lab_data = json.load(f)
            data['lab_samples'] = lab_data.get('samples', [])
    
    return data


def generate_daily_ops(date: str):
    """Generate daily operations report."""
    print(f"\nGenerating Daily Operations Report for {date}...")
    
    data = load_processed_data()
    
    report = DailyOpsReport()
    files = report.generate_both(
        f"daily_ops_{date.replace('/', '-')}",
        date=date,
        shipments=data['shipments'],
        bunker_loads=data['bunker_loads'],
        lab_samples=data['lab_samples']
    )
    
    print(f"✓ Markdown: {files['markdown']}")
    if files['pdf']:
        print(f"✓ PDF: {files['pdf']}")


def generate_grade_report(facility_code: str):
    """Generate grade report for a facility."""
    print(f"\nGenerating Grade Report for Facility {facility_code}...")
    
    data = load_processed_data()
    
    report = GradeReport()
    files = report.generate_both(
        f"grade_report_facility_{facility_code}",
        facility_code=facility_code,
        lab_samples=data['lab_samples']
    )
    
    print(f"✓ Markdown: {files['markdown']}")
    if files['pdf']:
        print(f"✓ PDF: {files['pdf']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate mining operations reports')
    parser.add_argument('report_type', choices=['daily', 'grade', 'all'],
                       help='Type of report to generate')
    parser.add_argument('--date', help='Date for daily report (YYYY/MM/DD)')
    parser.add_argument('--facility', choices=['A', 'B', 'C'],
                       help='Facility code for grade report')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Gold Mining Operations - Report Generator")
    print("=" * 60)
    
    if args.report_type == 'daily' or args.report_type == 'all':
        date = args.date or "1404/10/14"  # Default date
        generate_daily_ops(date)
    
    if args.report_type == 'grade' or args.report_type == 'all':
        if args.report_type == 'grade' and not args.facility:
            print("Error: --facility required for grade report")
            return
        
        facilities = [args.facility] if args.facility else ['A', 'B', 'C']
        for facility in facilities:
            generate_grade_report(facility)
    
    print("\n" + "=" * 60)
    print("✓ Report generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
