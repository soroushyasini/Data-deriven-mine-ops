#!/usr/bin/env python3
"""
Run full data ingestion pipeline.
Converts Excel/JSON data, validates, generates alerts, and loads into database.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.converters.bunker_converter import BunkerConverter
from src.converters.assay_converter import AssayConverter
from src.converters.trucking_converter import TruckingConverter
from src.converters.finance_converter import FinanceConverter
from src.database.connection import get_db
from src.database.ingestion import DataIngestion
from src.alerts.alert_engine import AlertEngine
from src.alerts.log_notifier import LogNotifier
from src.alerts.telegram_notifier import TelegramNotifier
from src.alerts.email_notifier import EmailNotifier


def load_json_file(filepath: Path) -> Any:
    """Load JSON file with UTF-8 encoding."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(filepath: Path, data: Any):
    """Save JSON file with UTF-8 encoding."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """Run full ingestion pipeline."""
    print("=" * 60)
    print("Gold Mining Operations - Data Ingestion Pipeline")
    print("=" * 60)
    
    # Paths
    incoming_dir = Path("data/incoming")
    processed_dir = Path("data/processed")
    config_dir = Path("config")
    
    # Initialize converters
    print("\n1. Initializing converters...")
    bunker_converter = BunkerConverter(str(config_dir))
    assay_converter = AssayConverter(str(config_dir))
    trucking_converter = TruckingConverter(str(config_dir))
    finance_converter = FinanceConverter(str(config_dir))
    print("✓ Converters initialized")
    
    # Initialize alert engine
    print("\n2. Initializing alert system...")
    alert_engine = AlertEngine(str(config_dir))
    alert_engine.add_notifier(LogNotifier())
    
    # Add Telegram notifier if configured
    telegram = TelegramNotifier()
    if telegram.enabled:
        alert_engine.add_notifier(telegram)
        print("✓ Telegram notifications enabled")
    
    # Add Email notifier if configured
    email = EmailNotifier()
    if email.enabled:
        alert_engine.add_notifier(email)
        print("✓ Email notifications enabled")
    
    print("✓ Alert system initialized")
    
    # Process data files
    results = {
        'bunker_loads': None,
        'lab_samples': None,
        'truck_shipments': None
    }
    
    # Process bunker data
    bunker_file = incoming_dir / "data_for_llm_enhanced.json"
    if bunker_file.exists():
        print(f"\n3. Processing bunker data from {bunker_file}...")
        input_data = load_json_file(bunker_file)
        results['bunker_loads'] = bunker_converter.convert(input_data)
        
        output_file = processed_dir / "bunker_loads_standardized.json"
        save_json_file(output_file, results['bunker_loads'])
        print(f"✓ Converted {results['bunker_loads']['statistics']['total_loads']} bunker loads")
        print(f"✓ Output: {output_file}")
    else:
        print(f"\n3. Bunker data file not found: {bunker_file}")
    
    # Process lab data
    lab_file = incoming_dir / "lab_data_for_llm.json"
    if lab_file.exists():
        print(f"\n4. Processing lab data from {lab_file}...")
        input_data = load_json_file(lab_file)
        results['lab_samples'] = assay_converter.convert(input_data)
        
        output_file = processed_dir / "lab_samples_standardized.json"
        save_json_file(output_file, results['lab_samples'])
        print(f"✓ Converted {results['lab_samples']['statistics']['total_samples']} lab samples")
        print(f"✓ Detection rate: {results['lab_samples']['statistics']['detection_rate']:.1%}")
        print(f"✓ Output: {output_file}")
    else:
        print(f"\n4. Lab data file not found: {lab_file}")
    
    # Process trucking data
    trucking_file = incoming_dir / "trucking_data_for_llm.json"
    if trucking_file.exists():
        print(f"\n5. Processing trucking data from {trucking_file}...")
        input_data = load_json_file(trucking_file)
        results['truck_shipments'] = trucking_converter.convert(input_data)
        
        output_file = processed_dir / "truck_shipments_standardized.json"
        save_json_file(output_file, results['truck_shipments'])
        print(f"✓ Converted {results['truck_shipments']['statistics']['total_shipments']} truck shipments")
        print(f"✓ Total tonnage: {results['truck_shipments']['statistics']['total_tonnage_kg']:,.0f} kg")
        print(f"✓ Output: {output_file}")
    else:
        print(f"\n5. Trucking data file not found: {trucking_file}")
    
    # Validate and generate alerts
    print("\n6. Validating data and generating alerts...")
    shipments = results['truck_shipments']['shipments'] if results['truck_shipments'] else []
    samples = results['lab_samples']['samples'] if results['lab_samples'] else []
    
    alert_summary = alert_engine.process_and_send(
        shipments=shipments,
        samples=samples
    )
    
    print(f"✓ Generated {alert_summary['total_alerts']} alerts")
    if alert_summary['by_level']:
        for level, count in alert_summary['by_level'].items():
            print(f"  - {level}: {count}")
    
    # Load into database
    print("\n7. Loading data into database...")
    db = get_db()
    ingestion = DataIngestion(db)
    
    if results['truck_shipments']:
        count = ingestion.ingest_shipments(shipments)
        print(f"✓ Loaded {count} shipments into database")
    
    if results['bunker_loads']:
        loads = results['bunker_loads']['loads']
        count = ingestion.ingest_bunker_loads(loads)
        print(f"✓ Loaded {count} bunker loads into database")
    
    if results['lab_samples']:
        count = ingestion.ingest_lab_samples(samples)
        print(f"✓ Loaded {count} lab samples into database")
    
    # Store alerts
    if alert_summary['total_alerts'] > 0:
        # Convert ValidationAlert objects to dicts
        alert_dicts = []
        for alert in alert_engine.process_shipments(shipments) + alert_engine.process_lab_samples(samples):
            alert_dicts.append(alert.to_dict())
        
        count = ingestion.ingest_alerts(alert_dicts)
        print(f"✓ Stored {count} alerts in database")
    
    print("\n" + "=" * 60)
    print("✓ Ingestion pipeline complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Generate reports: python scripts/generate_report.py")
    print("2. View dashboard: http://localhost:3000 (Metabase)")


if __name__ == "__main__":
    main()
