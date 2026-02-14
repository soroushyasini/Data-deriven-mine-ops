"""
Tests for data linking engine.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.linker import DataLinker, SampleCodeParser


class TestDataLinker:
    """Test data linking functionality."""
    
    def setup_method(self):
        """Set up test linker."""
        facilities = {
            'A': {'name_en': 'Hejazian', 'truck_dest': 'رباط سفید'},
            'B': {'name_en': 'Shen Beton', 'truck_dest': 'شن بتن مشهد'},
            'C': {'name_en': 'Kavian', 'truck_dest': 'شهرک کاویان'}
        }
        self.linker = DataLinker(facilities)
    
    def test_link_sample_to_bunker(self):
        """Test linking lab sample to bunker load."""
        sample = {
            'sample_code': 'A 1404 10 14 K1',
            'facility_code': 'A',
            'date': '1404/10/14'
        }
        
        bunker_loads = [
            {'facility_code': 'A', 'date': '1404/10/14', 'tonnage_kg': 25000},
            {'facility_code': 'B', 'date': '1404/10/14', 'tonnage_kg': 22000},
            {'facility_code': 'A', 'date': '1404/10/15', 'tonnage_kg': 23000}
        ]
        
        result = self.linker.link_sample_to_bunker(sample, bunker_loads)
        
        assert result is not None
        assert result['facility_code'] == 'A'
        assert result['date'] == '1404/10/14'
    
    def test_link_bunker_to_shipment(self):
        """Test linking bunker load to truck shipments."""
        bunker_load = {
            'facility_code': 'A',
            'date': '1404/10/14'
        }
        
        shipments = [
            {'destination': 'رباط سفید', 'date': '1404/10/13', 'tonnage_kg': 30000},
            {'destination': 'رباط سفید', 'date': '1404/10/14', 'tonnage_kg': 28000},
            {'destination': 'شن بتن مشهد', 'date': '1404/10/14', 'tonnage_kg': 25000}
        ]
        
        results = self.linker.link_bunker_to_shipment(bunker_load, shipments)
        
        assert len(results) > 0
        # Should find shipments to رباط سفید (Facility A)
        assert all(s['destination'] == 'رباط سفید' for s in results)
    
    def test_complete_trace(self):
        """Test complete sample → bunker → shipment trace."""
        sample = {
            'sample_code': 'A 1404 10 14 K1',
            'facility_code': 'A',
            'date': '1404/10/14'
        }
        
        bunker_loads = [
            {'facility_code': 'A', 'date': '1404/10/14', 'tonnage_kg': 25000}
        ]
        
        shipments = [
            {'destination': 'رباط سفید', 'date': '1404/10/13', 'tonnage_kg': 30000}
        ]
        
        trace = self.linker.link_sample_to_source(sample, bunker_loads, shipments)
        
        assert trace['bunker_load'] is not None
        assert len(trace['shipments']) > 0
        assert trace['trace_complete'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
