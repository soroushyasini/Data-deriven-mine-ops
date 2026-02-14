"""
Tests for lab sample ingestion with duplicate handling.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.models import LabSample, Facility
from src.database.connection import DatabaseConnection
from src.database.ingestion import DataIngestion


class TestLabSampleDuplicateHandling:
    """Test lab sample ingestion with duplicate sample codes."""
    
    @pytest.fixture
    def test_db(self):
        """Create a test database connection."""
        # Use in-memory SQLite for testing
        db = DatabaseConnection(db_url='sqlite:///:memory:')
        db.create_tables()
        return db
    
    @pytest.fixture
    def test_facility(self, test_db):
        """Create a test facility."""
        with test_db.get_session() as session:
            facility = Facility(
                code='A',
                name_fa='آسیاب الف',
                name_en='Grinding A',
                bunker_sheet_name='A',
                truck_destination='Factory'
            )
            session.add(facility)
            session.commit()
            session.refresh(facility)
            return facility.id
    
    def test_same_sample_code_different_sheets(self, test_db, test_facility):
        """Test that same sample code can exist in different sheets."""
        ingestion = DataIngestion(test_db)
        
        samples = [
            {
                'sample_code': 'A1404101L',
                'sheet_name': 'Solutions',
                'au_ppm': 0.5,
                'facility_code': 'A',
                'sample_type': 'L',
                'date': '1404/10/01',
                'year': '1404',
                'month': '10',
                'day': '01',
                'sample_number': '1'
            },
            {
                'sample_code': 'A1404101L',
                'sheet_name': 'Solids',
                'au_ppm': 1.2,
                'facility_code': 'A',
                'sample_type': 'L',
                'date': '1404/10/01',
                'year': '1404',
                'month': '10',
                'day': '01',
                'sample_number': '1'
            }
        ]
        
        count = ingestion.ingest_lab_samples(samples)
        
        # Both samples should be inserted (different sheets)
        assert count == 2
        
        with test_db.get_session() as session:
            all_samples = session.query(LabSample).all()
            assert len(all_samples) == 2
            assert all_samples[0].sheet_name != all_samples[1].sheet_name
    
    def test_duplicate_sample_code_same_sheet_skipped(self, test_db, test_facility):
        """Test that duplicate sample in the same sheet is skipped."""
        ingestion = DataIngestion(test_db)
        
        samples = [
            {
                'sample_code': 'A1404101K',
                'sheet_name': 'Solids',
                'au_ppm': 0.5,
                'facility_code': 'A',
                'sample_type': 'K',
                'date': '1404/10/01',
                'year': '1404',
                'month': '10',
                'day': '01',
                'sample_number': '1'
            },
            {
                'sample_code': 'A1404101K',
                'sheet_name': 'Solids',
                'au_ppm': 0.6,  # Different value but same sheet
                'facility_code': 'A',
                'sample_type': 'K',
                'date': '1404/10/01',
                'year': '1404',
                'month': '10',
                'day': '01',
                'sample_number': '1'
            }
        ]
        
        count = ingestion.ingest_lab_samples(samples)
        
        # Only first sample should be inserted, second is duplicate
        assert count == 1
        
        with test_db.get_session() as session:
            all_samples = session.query(LabSample).all()
            assert len(all_samples) == 1
            assert all_samples[0].au_ppm == 0.5  # First value retained
    
    def test_multiple_samples_different_codes(self, test_db, test_facility):
        """Test that different sample codes all get inserted."""
        ingestion = DataIngestion(test_db)
        
        samples = [
            {
                'sample_code': 'A1404101K',
                'sheet_name': 'Solids',
                'au_ppm': 0.5,
                'facility_code': 'A',
                'sample_type': 'K',
                'date': '1404/10/01',
                'year': '1404',
                'month': '10',
                'day': '01',
                'sample_number': '1'
            },
            {
                'sample_code': 'A1404102K',
                'sheet_name': 'Solids',
                'au_ppm': 0.6,
                'facility_code': 'A',
                'sample_type': 'K',
                'date': '1404/10/02',
                'year': '1404',
                'month': '10',
                'day': '02',
                'sample_number': '2'
            },
            {
                'sample_code': 'A1404103L',
                'sheet_name': 'Solutions',
                'au_ppm': 0.3,
                'facility_code': 'A',
                'sample_type': 'L',
                'date': '1404/10/01',
                'year': '1404',
                'month': '10',
                'day': '01',
                'sample_number': '3'
            }
        ]
        
        count = ingestion.ingest_lab_samples(samples)
        
        # All three samples should be inserted
        assert count == 3
        
        with test_db.get_session() as session:
            all_samples = session.query(LabSample).all()
            assert len(all_samples) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
