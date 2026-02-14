"""
Tests for data validation.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.validator import DataValidator, AlertLevel


class TestDataValidator:
    """Test data validation rules."""
    
    def setup_method(self):
        """Set up test validator."""
        self.validator = DataValidator()
    
    def test_validate_ore_input_warning(self):
        """Test ore input warning threshold."""
        sample = {
            'sample_code': 'A 1404 10 14 K1',
            'au_ppm': 7.5,
            'sample_type': 'K'
        }
        
        alerts = self.validator.validate_lab_sample(sample)
        
        assert len(alerts) > 0
        assert any(a.level == AlertLevel.WARNING for a in alerts)
        assert any('ore_input' in a.rule for a in alerts)
    
    def test_validate_ore_input_critical(self):
        """Test ore input critical threshold."""
        sample = {
            'sample_code': 'A 1404 10 14 K1',
            'au_ppm': 25.0,
            'sample_type': 'K'
        }
        
        alerts = self.validator.validate_lab_sample(sample)
        
        assert len(alerts) > 0
        assert any(a.level == AlertLevel.CRITICAL for a in alerts)
    
    def test_validate_tailings_critical(self):
        """Test tailings critical threshold."""
        sample = {
            'sample_code': 'B 1404 10 14 T1',
            'au_ppm': 0.3,
            'sample_type': 'T'
        }
        
        alerts = self.validator.validate_lab_sample(sample)
        
        assert len(alerts) > 0
        assert any(a.level == AlertLevel.CRITICAL for a in alerts)
        assert any('tailings' in a.rule for a in alerts)
    
    def test_validate_carbon_warning(self):
        """Test carbon exhaustion warning."""
        sample = {
            'sample_code': 'C 1404 10 14 CR1',
            'au_ppm': 150.0,
            'sample_type': 'CR'
        }
        
        alerts = self.validator.validate_lab_sample(sample)
        
        assert len(alerts) > 0
        assert any(a.level == AlertLevel.WARNING for a in alerts)
        assert any('carbon' in a.rule for a in alerts)
    
    def test_validate_invalid_sample_code(self):
        """Test invalid sample code detection."""
        sample = {
            'sample_code': 'INVALID_CODE',
            'au_ppm': 1.0,
            'sample_type': 'K'
        }
        
        alerts = self.validator.validate_lab_sample(sample)
        
        assert len(alerts) > 0
        assert any(a.level == AlertLevel.CRITICAL for a in alerts)
        assert any('invalid_sample_code' in a.rule for a in alerts)
    
    def test_validate_tonnage(self):
        """Test tonnage validation."""
        # Below minimum
        alerts = self.validator.validate_tonnage(10000, {'record_type': 'test'})
        assert len(alerts) > 0
        
        # Above maximum
        alerts = self.validator.validate_tonnage(35000, {'record_type': 'test'})
        assert len(alerts) > 0
        
        # Normal range
        alerts = self.validator.validate_tonnage(20000, {'record_type': 'test'})
        assert len(alerts) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
