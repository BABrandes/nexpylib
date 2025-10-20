"""
Pytest configuration and fixtures for nexpy tests.

This module provides shared fixtures and configuration for all tests.
"""

import pytest
import sys
import os

# Add the src directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def nexpy_module():
    """Fixture providing access to the nexpy module."""
    import nexpy
    return nexpy


@pytest.fixture
def sample_data():
    """Fixture providing sample data for testing."""
    return {
        'numbers': [1, 2, 3, 4, 5],
        'strings': ['hello', 'world', 'nexpy'],
        'mixed': [1, 'hello', 3.14, True]
    }
