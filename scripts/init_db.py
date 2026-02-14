#!/usr/bin/env python3
"""
Initialize database schema and load configuration data.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import init_database
from src.database.ingestion import DataIngestion


def main():
    """Initialize database and load initial configuration."""
    print("Initializing database...")
    
    # Initialize database (create tables)
    db = init_database()
    print("✓ Database tables created")
    
    # Load configuration data
    config_dir = Path(__file__).parent.parent / "config"
    
    # Initialize ingestion
    ingestion = DataIngestion(db)
    
    # Load facilities
    facilities_file = config_dir / "facilities.json"
    if facilities_file.exists():
        with open(facilities_file, 'r', encoding='utf-8') as f:
            facilities = json.load(f)
        count = ingestion.ingest_facilities(facilities)
        print(f"✓ Loaded {count} facilities")
    
    # Load drivers
    drivers_file = config_dir / "drivers.json"
    if drivers_file.exists():
        with open(drivers_file, 'r', encoding='utf-8') as f:
            drivers = json.load(f)
        count = ingestion.ingest_drivers(drivers)
        print(f"✓ Loaded {count} drivers")
    
    print("\n✓ Database initialization complete!")
    print("\nNext steps:")
    print("1. Place data files in data/incoming/")
    print("2. Run: python scripts/ingest.py")


if __name__ == "__main__":
    main()
