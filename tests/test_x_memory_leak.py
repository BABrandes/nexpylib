"""
Test to identify what's preventing garbage collection of observables.
"""

from typing import Any
import gc
import weakref

from nexpy import XValue


def test_observable_without_validator():
    """Test observable without validator."""
    # Create an observable without validator
    obs = XValue("test_value")
    obs_ref = weakref.ref(obs)
    
    # Verify it exists
    assert obs_ref() is not None
    
    # Delete the observable
    del obs
    
    # Force garbage collection
    gc.collect()
    
    # Check if it was garbage collected
    # This should be None if garbage collection worked properly
    assert obs_ref() is None


def test_observable_with_validator():
    """Test observable with validator."""
    def validator(value: Any) -> tuple[bool, str]:
        return True, "Valid"
    
    # Create an observable with validator
    obs = XValue("test_value", validate_value_callback=validator)
    obs_ref = weakref.ref(obs)
    
    # Verify it exists
    assert obs_ref() is not None
    
    # Delete the observable
    del obs
    
    # Force garbage collection
    gc.collect()
    
    # Check if it was garbage collected
    # This should be None if garbage collection worked properly
    assert obs_ref() is None
