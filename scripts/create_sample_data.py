"""
Create sample data files for testing the system.
"""

import json
from pathlib import Path


def create_sample_trucking_data():
    """Create sample trucking data."""
    data = [
        {
            "row_number": 1,
            "date": "1404/10/14",
            "truck_number": "14978",
            "receipt_number": "RCP-001",
            "tonnage_kg": 25000,
            "destination": "رباط سفید",
            "cost_per_ton": 7000000,
            "driver_name": "محمد احمدآبادی",
            "notes": ""
        },
        {
            "row_number": 2,
            "date": "1404/10/14",
            "truck_number": "14979",
            "receipt_number": "RCP-002",
            "tonnage_kg": 28000,
            "destination": "شن بتن مشهد",
            "cost_per_ton": 8500000,
            "driver_name": "محمدرضا احمد آبادی",
            "notes": ""
        },
        {
            "row_number": 3,
            "date": "1404/10/15",
            "truck_number": "14978",
            "receipt_number": "RCP-003",
            "tonnage_kg": 26500,
            "destination": "شهرک کاویان",
            "cost_per_ton": 8500000,
            "driver_name": "کریم ابادی",
            "notes": ""
        }
    ]
    return data


def create_sample_bunker_data():
    """Create sample bunker data."""
    data = {
        "رباط سفید": [
            {
                "row_number": 1,
                "تاریخ": "1404/10/14",
                "tonnage_kg": 24500,
                "cumulative_tonnage": 24500,
                "driver": "محمد احمدآبادی"
            }
        ],
        "شن بتن": [
            {
                "row_number": 1,
                "تاریخ": "1404/10/14",
                "tonnage_kg": 27800,
                "cumulative_tonnage": 27800,
                "driver": "محمدرضا احمدآبادی"
            }
        ],
        "مس کاویان": [
            {
                "row_number": 1,
                "تاریخ": "1404/10/15",
                "tonnage_kg": 26000,
                "cumulative_tonnage": 26000,
                "driver": "ابوالفضل کریم آبادی"
            }
        ]
    }
    return data


def create_sample_lab_data():
    """Create sample lab data."""
    data = {
        "Solutions": [
            {
                "sample_code": "A 1404 10 14 L1",
                "au_ppm": 0.285
            },
            {
                "sample_code": "B 1404 10 14 L1",
                "au_ppm": 0.312
            }
        ],
        "Solids": [
            {
                "sample_code": "A 1404 10 14 K1",
                "au_ppm": 1.234
            },
            {
                "sample_code": "A 1404 10 14 T1",
                "au_ppm": 0.087
            },
            {
                "sample_code": "C 1404 10 15 K1",
                "au_ppm": 2.156
            },
            {
                "sample_code": "C 1404 10 15 T1",
                "au_ppm": 0.125
            }
        ],
        "Carbon": [
            {
                "sample_code": "A 1404 10 14 CR1",
                "au_ppm": 425.5
            }
        ]
    }
    return data


def main():
    """Generate sample data files."""
    samples_dir = Path("data/samples")
    samples_dir.mkdir(parents=True, exist_ok=True)
    
    # Trucking data
    trucking_file = samples_dir / "trucking_data_for_llm.json"
    trucking_data = create_sample_trucking_data()
    with open(trucking_file, 'w', encoding='utf-8') as f:
        json.dump(trucking_data, f, ensure_ascii=False, indent=2)
    print(f"✓ Created: {trucking_file}")
    
    # Bunker data
    bunker_file = samples_dir / "data_for_llm_enhanced.json"
    bunker_data = create_sample_bunker_data()
    with open(bunker_file, 'w', encoding='utf-8') as f:
        json.dump(bunker_data, f, ensure_ascii=False, indent=2)
    print(f"✓ Created: {bunker_file}")
    
    # Lab data
    lab_file = samples_dir / "lab_data_for_llm.json"
    lab_data = create_sample_lab_data()
    with open(lab_file, 'w', encoding='utf-8') as f:
        json.dump(lab_data, f, ensure_ascii=False, indent=2)
    print(f"✓ Created: {lab_file}")
    
    print("\n✓ Sample data files created successfully!")
    print("You can now test the ingestion pipeline with these files.")


if __name__ == "__main__":
    main()
