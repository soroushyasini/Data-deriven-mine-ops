#!/usr/bin/env python3
"""
System validation script - verifies all components are working.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def check_imports():
    """Check all critical imports work."""
    print("=" * 60)
    print("1. Checking Imports...")
    print("=" * 60)
    
    try:
        from src.core.base_converter import BaseConverter
        print("✓ BaseConverter")
        
        from src.core.validator import DataValidator
        print("✓ DataValidator")
        
        from src.core.linker import DataLinker
        print("✓ DataLinker")
        
        from src.converters.bunker_converter import BunkerConverter
        print("✓ BunkerConverter")
        
        from src.converters.assay_converter import AssayConverter
        print("✓ AssayConverter")
        
        from src.converters.trucking_converter import TruckingConverter
        print("✓ TruckingConverter")
        
        from src.converters.finance_converter import FinanceConverter
        print("✓ FinanceConverter")
        
        from src.database.models import Base
        print("✓ Database Models")
        
        from src.database.connection import DatabaseConnection
        print("✓ DatabaseConnection")
        
        from src.database.ingestion import DataIngestion
        print("✓ DataIngestion")
        
        from src.alerts.alert_engine import AlertEngine
        print("✓ AlertEngine")
        
        from src.reports.daily_ops import DailyOpsReport
        print("✓ DailyOpsReport")
        
        from src.reports.grade_report import GradeReport
        print("✓ GradeReport")
        
        print("\n✓ All imports successful!")
        return True
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        return False


def check_configs():
    """Check configuration files exist and are valid."""
    print("\n" + "=" * 60)
    print("2. Checking Configuration Files...")
    print("=" * 60)
    
    import json
    
    config_files = [
        "config/facilities.json",
        "config/drivers.json",
        "config/trucks.json",
        "config/sample_types.json",
        "config/validation_rules.json"
    ]
    
    all_valid = True
    for config_file in config_files:
        path = Path(config_file)
        if not path.exists():
            print(f"✗ Missing: {config_file}")
            all_valid = False
        else:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"✓ {config_file}")
            except Exception as e:
                print(f"✗ Invalid JSON in {config_file}: {e}")
                all_valid = False
    
    if all_valid:
        print("\n✓ All configuration files valid!")
    return all_valid


def check_sample_data():
    """Check sample data files exist."""
    print("\n" + "=" * 60)
    print("3. Checking Sample Data...")
    print("=" * 60)
    
    sample_files = [
        "data/samples/trucking_data_for_llm.json",
        "data/samples/data_for_llm_enhanced.json",
        "data/samples/lab_data_for_llm.json"
    ]
    
    all_exist = True
    for sample_file in sample_files:
        path = Path(sample_file)
        if not path.exists():
            print(f"✗ Missing: {sample_file}")
            all_exist = False
        else:
            print(f"✓ {sample_file}")
    
    if all_exist:
        print("\n✓ All sample data files present!")
    return all_exist


def test_converters():
    """Test all converters with sample data."""
    print("\n" + "=" * 60)
    print("4. Testing Converters...")
    print("=" * 60)
    
    import json
    from src.converters.trucking_converter import TruckingConverter
    from src.converters.bunker_converter import BunkerConverter
    from src.converters.assay_converter import AssayConverter
    
    try:
        # Test trucking converter
        with open('data/samples/trucking_data_for_llm.json', 'r', encoding='utf-8') as f:
            trucking_data = json.load(f)
        
        trucking_conv = TruckingConverter()
        trucking_result = trucking_conv.convert(trucking_data)
        print(f"✓ Trucking: {trucking_result['statistics']['total_shipments']} shipments")
        
        # Test bunker converter
        with open('data/samples/data_for_llm_enhanced.json', 'r', encoding='utf-8') as f:
            bunker_data = json.load(f)
        
        bunker_conv = BunkerConverter()
        bunker_result = bunker_conv.convert(bunker_data)
        print(f"✓ Bunker: {bunker_result['statistics']['total_loads']} loads")
        
        # Test assay converter
        with open('data/samples/lab_data_for_llm.json', 'r', encoding='utf-8') as f:
            lab_data = json.load(f)
        
        assay_conv = AssayConverter()
        assay_result = assay_conv.convert(lab_data)
        print(f"✓ Assay: {assay_result['statistics']['total_samples']} samples")
        
        print("\n✓ All converters working!")
        return True
    except Exception as e:
        print(f"\n✗ Converter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation():
    """Test validation and alerts."""
    print("\n" + "=" * 60)
    print("5. Testing Validation & Alerts...")
    print("=" * 60)
    
    from src.core.validator import DataValidator
    
    try:
        validator = DataValidator()
        
        # Test high grade ore
        sample = {
            'sample_code': 'A 1404 10 14 K1',
            'au_ppm': 25.0,
            'sample_type': 'K'
        }
        alerts = validator.validate_lab_sample(sample)
        print(f"✓ Ore input validation: {len(alerts)} alerts generated")
        
        # Test tonnage
        alerts = validator.validate_tonnage(35000, {'test': True})
        print(f"✓ Tonnage validation: {len(alerts)} alerts generated")
        
        print("\n✓ Validation system working!")
        return True
    except Exception as e:
        print(f"\n✗ Validation test failed: {e}")
        return False


def test_linking():
    """Test data linking."""
    print("\n" + "=" * 60)
    print("6. Testing Data Linking...")
    print("=" * 60)
    
    from src.core.linker import DataLinker
    
    try:
        facilities = {
            'A': {'name_en': 'Hejazian', 'truck_dest': 'رباط سفید'}
        }
        
        linker = DataLinker(facilities)
        
        sample = {
            'sample_code': 'A 1404 10 14 K1',
            'facility_code': 'A',
            'date': '1404/10/14'
        }
        
        bunker_loads = [
            {'facility_code': 'A', 'date': '1404/10/14', 'tonnage_kg': 25000}
        ]
        
        result = linker.link_sample_to_bunker(sample, bunker_loads)
        
        if result:
            print("✓ Sample → Bunker linking works")
        else:
            print("✗ Sample → Bunker linking failed")
            return False
        
        print("\n✓ Data linking working!")
        return True
    except Exception as e:
        print(f"\n✗ Linking test failed: {e}")
        return False


def run_pytest():
    """Run pytest suite."""
    print("\n" + "=" * 60)
    print("7. Running Test Suite...")
    print("=" * 60)
    
    import subprocess
    
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("\n✓ All tests passed!")
            return True
        else:
            print("\n✗ Some tests failed")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"\n✗ Could not run pytest: {e}")
        return False


def main():
    """Run all validation checks."""
    print("\n" + "=" * 60)
    print("GOLD MINING OPERATIONS PLATFORM - SYSTEM VALIDATION")
    print("=" * 60 + "\n")
    
    results = {}
    
    results['imports'] = check_imports()
    results['configs'] = check_configs()
    results['sample_data'] = check_sample_data()
    results['converters'] = test_converters()
    results['validation'] = test_validation()
    results['linking'] = test_linking()
    results['tests'] = run_pytest()
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check.upper():.<40} {status}")
    
    all_passed = all(results.values())
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 SUCCESS! All validation checks passed!")
        print("\nThe system is ready for production use.")
        print("\nNext steps:")
        print("1. docker-compose up -d")
        print("2. docker-compose exec pipeline python scripts/init_db.py")
        print("3. Place real data in data/incoming/")
        print("4. docker-compose exec pipeline python scripts/ingest.py")
        return 0
    else:
        print("\n⚠️  WARNING! Some validation checks failed.")
        print("Please review the errors above and fix them.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
