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
        """Test parsing standard sample code with spaces."""
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
    
    def test_concatenated_sample_code_with_prefix(self):
        """Test parsing concatenated sample code with single letter prefix."""
        parser = SampleCodeParser()
        # A1404105L → facility=A, year=1404, month=10, day=5, suffix=L
        result = parser.parse("A1404105L")
        
        assert result is not None
        assert result['facility'] == 'A'
        assert result['year'] == '1404'
        assert result['month'] == '10'
        assert result['day'] == '05'
        assert result['date'] == '1404/10/05'
        assert result['sample_type'] == 'L'
    
    def test_concatenated_sample_code_two_letter_prefix(self):
        """Test parsing concatenated sample code with two-letter prefix."""
        parser = SampleCodeParser()
        # RC14041010 → prefix=RC, year=1404, month=10, day=10
        result = parser.parse("RC14041010")
        
        assert result is not None
        assert result.get('prefix') == 'RC'
        assert result['year'] == '1404'
        assert result['month'] == '10'
        assert result['day'] == '10'
    
    def test_concatenated_sample_code_no_prefix(self):
        """Test parsing concatenated sample code with no prefix."""
        parser = SampleCodeParser()
        # 14041017CR3 → no prefix, year=1404, month=10, day=17, suffix=CR3
        result = parser.parse("14041017CR3")
        
        assert result is not None
        assert result['facility'] is None
        assert result['year'] == '1404'
        assert result['month'] == '10'
        assert result['day'] == '17'
        assert result['sample_type'] == 'CR3'
    
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
    
    def test_parse_sample_code_spaced(self):
        """Test parsing spaced sample code (backward compatibility)."""
        result = AssayConverter._parse_sample_code("C 1404 10 14 K2")
        assert result['facility'] == 'C'
        assert result['year'] == '1404'
        assert result['month'] == '10'
        assert result['day'] == '14'
        assert result['date'] == '1404/10/14'
        assert result['sample_type'] == 'K'
        assert result['sample_number'] == '2'
        assert result['is_special'] is False
    
    def test_parse_sample_code_concatenated_with_prefix(self):
        """Test parsing concatenated sample code with single letter prefix."""
        # A1404105L → facility=A, year=1404, month=10, day=5, suffix=L
        result = AssayConverter._parse_sample_code("A1404105L")
        assert result['facility'] == 'A'
        assert result['year'] == '1404'
        assert result['month'] == '10'
        assert result['day'] == '05'
        assert result['date'] == '1404/10/05'
        assert result['sample_type'] == 'L'
        assert result['is_special'] is False
    
    def test_parse_sample_code_concatenated_with_suffix(self):
        """Test parsing concatenated sample code with multi-char suffix."""
        # C14041014K → facility=C, year=1404, month=10, day=14, suffix=K
        result = AssayConverter._parse_sample_code("C14041014K")
        assert result['facility'] == 'C'
        assert result['year'] == '1404'
        assert result['month'] == '10'
        assert result['day'] == '14'
        assert result['date'] == '1404/10/14'
        assert result['sample_type'] == 'K'
    
    def test_parse_sample_code_concatenated_two_letter_prefix(self):
        """Test parsing concatenated sample code with two-letter prefix."""
        # RC14041010 → prefix=RC, year=1404, month=10, day=10
        result = AssayConverter._parse_sample_code("RC14041010")
        assert result.get('prefix') == 'RC'
        assert result['year'] == '1404'
        assert result['month'] == '10'
        assert result['day'] == '10'
        assert result['date'] == '1404/10/10'
    
    def test_parse_sample_code_concatenated_no_prefix(self):
        """Test parsing concatenated sample code with no prefix."""
        # 14041017CR3 → no prefix, year=1404, month=10, day=17, suffix=CR3
        result = AssayConverter._parse_sample_code("14041017CR3")
        assert result['facility'] is None
        assert result['year'] == '1404'
        assert result['month'] == '10'
        assert result['day'] == '17'
        assert result['date'] == '1404/10/17'
        assert result['sample_type'] == 'CR3'
    
    def test_parse_sample_code_concatenated_with_number_suffix(self):
        """Test parsing concatenated sample code with suffix containing number."""
        # C14041027K2 → facility=C, year=1404, month=10, day=27, suffix=K2
        result = AssayConverter._parse_sample_code("C14041027K2")
        assert result['facility'] == 'C'
        assert result['year'] == '1404'
        assert result['month'] == '10'
        assert result['day'] == '27'
        assert result['sample_type'] == 'K2'
    
    def test_parse_sample_code_special_codes(self):
        """Test parsing special sample codes."""
        result = AssayConverter._parse_sample_code("F2(T3)")
        assert result['is_special'] is True
        assert result['sample_type'] == 'F2(T3)'
        
        result = AssayConverter._parse_sample_code("SR2")
        assert result['is_special'] is True
        assert result['sample_type'] == 'SR2'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
