"""
Tests for data converters.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.base_converter import BaseConverter
from src.converters.assay_converter import AssayConverter
from src.core.linker import SampleCodeParser


class TestBaseConverter:
    """Test base converter utilities."""
    
    def test_clean_persian_number(self):
        """Test Persian number cleaning."""
        assert BaseConverter.clean_persian_number("1,234.56") == "1234.56"
        assert BaseConverter.clean_persian_number("1234/56") == "1234.56"
        assert BaseConverter.clean_persian_number("1,234,567") == "1234567"
    
    def test_normalize_date(self):
        """Test date normalization."""
        assert BaseConverter.normalize_date("1404/9/09") == "1404/09/09"
        assert BaseConverter.normalize_date("1404/10/1") == "1404/10/01"
        assert BaseConverter.normalize_date("1404/09/09") == "1404/09/09"
    
    def test_clean_truck_number(self):
        """Test truck number cleaning."""
        assert BaseConverter.clean_truck_number("14978.0") == "14978"
        assert BaseConverter.clean_truck_number("14978") == "14978"
        assert BaseConverter.clean_truck_number(14978.0) == "14978"
    
    def test_calculate_cost(self):
        """Test cost calculation (per ton, not per kg)."""
        # 25,000 kg = 25 tons
        # 25 tons * 7,000,000 Rial/ton = 175,000,000 Rial
        assert BaseConverter.calculate_cost(25000, 7000000) == 175000000


class TestSampleCodeParser:
    """Test sample code parsing."""
    
    def test_standard_sample_code(self):
        """Test parsing standard sample code."""
        parser = SampleCodeParser()
        result = parser.parse("C 1404 10 14 K2")
        
        assert result is not None
        assert result['facility'] == 'C'
        assert result['year'] == '1404'
        assert result['month'] == '10'
        assert result['day'] == '14'
        assert result['date'] == '1404/10/14'
        assert result['sample_type'] == 'K'
        assert result['sample_number'] == '2'
        assert result['is_special'] is False
    
    def test_sample_code_with_two_letter_type(self):
        """Test parsing sample code with two-letter type (CR, RC)."""
        parser = SampleCodeParser()
        result = parser.parse("A 1404 09 05 CR1")
        
        assert result is not None
        assert result['facility'] == 'A'
        assert result['sample_type'] == 'CR'
        assert result['sample_number'] == '1'
    
    def test_special_sample_code(self):
        """Test parsing special sample codes."""
        parser = SampleCodeParser()
        
        result = parser.parse("F2(T3)")
        assert result is not None
        assert result['is_special'] is True
        
        result = parser.parse("SR2")
        assert result is not None
        assert result['is_special'] is True
    
    def test_invalid_sample_code(self):
        """Test parsing invalid sample code."""
        parser = SampleCodeParser()
        result = parser.parse("INVALID")
        assert result is None


class TestAssayConverter:
    """Test assay converter."""
    
    def test_parse_au_value_normal(self):
        """Test parsing normal Au value."""
        result = AssayConverter._parse_au_value("1.234")
        assert result['value'] == 1.234
        assert result['detected'] is True
        assert result['below_limit'] is False
    
    def test_parse_au_value_below_limit(self):
        """Test parsing below detection limit."""
        result = AssayConverter._parse_au_value("<0.05")
        assert result['value'] == 0.05
        assert result['detected'] is False
        assert result['below_limit'] is True
    
    def test_parse_au_value_none(self):
        """Test parsing None value."""
        result = AssayConverter._parse_au_value(None)
        assert result['value'] is None
        assert result['detected'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
