"""
Tests for ingestion pipeline functions.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.ingest import extract_sheets
from src.core.base_converter import BaseConverter


class TestExtractSheets:
    """Test extract_sheets function."""
    
    def test_nested_format_multiple_sheets(self):
        """Test extraction from nested format with multiple sheets."""
        nested_data = {
            "metadata": {"version": "1.0"},
            "sheets": [
                {
                    "sheet_name": "Sheet1",
                    "data": [{"id": 1}, {"id": 2}]
                },
                {
                    "sheet_name": "Sheet2",
                    "data": [{"id": 3}, {"id": 4}]
                }
            ],
            "summary": {}
        }
        
        result = extract_sheets(nested_data)
        assert isinstance(result, dict)
        assert "Sheet1" in result
        assert "Sheet2" in result
        assert len(result["Sheet1"]) == 2
        assert len(result["Sheet2"]) == 2
    
    def test_nested_format_single_sheet(self):
        """Test extraction from nested format with single sheet (trucking case)."""
        nested_data = {
            "metadata": {"version": "1.0"},
            "sheets": [
                {
                    "sheet_name": "Trucking",
                    "data": [{"id": 1}, {"id": 2}, {"id": 3}]
                }
            ],
            "summary": {}
        }
        
        result = extract_sheets(nested_data)
        # Single sheet should return just the data list
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["id"] == 1
    
    def test_flat_format_dict(self):
        """Test with already flat dictionary format."""
        flat_data = {
            "Sheet1": [{"id": 1}, {"id": 2}],
            "Sheet2": [{"id": 3}]
        }
        
        result = extract_sheets(flat_data)
        assert result == flat_data
    
    def test_flat_format_list(self):
        """Test with already flat list format."""
        flat_data = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        result = extract_sheets(flat_data)
        assert result == flat_data


class TestBaseConverterTypeSafety:
    """Test type safety fixes in BaseConverter."""
    
    def test_is_summary_row_with_dict(self):
        """Test is_summary_row with valid dict."""
        row = {"field1": "جمع", "field2": "value"}
        assert BaseConverter.is_summary_row(row) is True
        
        row = {"field1": "normal", "field2": "value"}
        assert BaseConverter.is_summary_row(row) is False
    
    def test_is_summary_row_with_non_dict(self):
        """Test is_summary_row with non-dict (should not crash)."""
        assert BaseConverter.is_summary_row("string") is False
        assert BaseConverter.is_summary_row(123) is False
        assert BaseConverter.is_summary_row(None) is False
        assert BaseConverter.is_summary_row([1, 2, 3]) is False
    
    def test_is_null_row_with_dict(self):
        """Test is_null_row with valid dict."""
        row = {"field1": None, "field2": "", "field3": "  "}
        assert BaseConverter.is_null_row(row) is True
        
        row = {"field1": "value", "field2": None}
        assert BaseConverter.is_null_row(row) is False
    
    def test_is_null_row_with_non_dict(self):
        """Test is_null_row with non-dict (should not crash)."""
        assert BaseConverter.is_null_row(None) is True
        assert BaseConverter.is_null_row("string") is False
        assert BaseConverter.is_null_row(123) is False
        assert BaseConverter.is_null_row([]) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
