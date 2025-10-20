"""
Unit tests for the nexpy package.

This module contains tests for the core functionality of nexpy.
"""

import pytest
import sys
import os

# Add the src directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import nexpy


class TestNexPy:
    """Test class for nexpy core functionality."""
    
    def test_version(self):
        """Test that version is properly defined."""
        assert hasattr(nexpy, '__version__')
        assert isinstance(nexpy.__version__, str)
        assert len(nexpy.__version__) > 0
    
    def test_author(self):
        """Test that author information is properly defined."""
        assert hasattr(nexpy, '__author__')
        assert isinstance(nexpy.__author__, str)
        assert len(nexpy.__author__) > 0
    
    def test_email(self):
        """Test that email information is properly defined."""
        assert hasattr(nexpy, '__email__')
        assert isinstance(nexpy.__email__, str)
        assert len(nexpy.__email__) > 0
    
    def test_all_exports(self):
        """Test that __all__ is properly defined."""
        assert hasattr(nexpy, '__all__')
        assert isinstance(nexpy.__all__, list)
        
        # Check that all exported items exist
        for item in nexpy.__all__:
            assert hasattr(nexpy, item)


if __name__ == "__main__":
    pytest.main([__file__])
