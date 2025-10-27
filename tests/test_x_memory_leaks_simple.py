"""
Simplified memory leak test for observables.
"""

from typing import Any
import gc
import weakref

from nexpy import XValue, XDictSelect


def test_simple_observable_gc():
    """Test that simple observables can be garbage collected."""
    # Create an observable
    obs = XValue("test_value")
    obs_ref = weakref.ref(obs)
    
    # Verify it exists
    assert obs_ref() is not None
    
    # Delete the observable
    del obs
    
    # Force garbage collection
    gc.collect()
    
    # Verify it was garbage collected
    assert obs_ref() is None


def test_complex_observable_gc():
    """Test that complex observables can be garbage collected."""
    # Create a complex observable
    obs = XDictSelect(
        dict_hook={"a": 1, "b": 2},
        key_hook="a",
        value_hook=None
    )
    obs_ref = weakref.ref(obs)
    
    # Verify it exists
    assert obs_ref() is not None
    
    # Delete the observable
    del obs
    
    # Force garbage collection
    gc.collect()
    
    # Verify it was garbage collected
    assert obs_ref() is None


def test_observable_with_listeners_gc():
    """Test that observables with listeners can be garbage collected."""
    # Create an observable
    obs = XValue("test_value")
    obs_ref = weakref.ref(obs)
    
    # Add a listener
    def listener():
        pass
    
    obs.add_listener(listener)
    
    # Delete the observable
    del obs
    
    # Force garbage collection
    gc.collect()
    
    # Verify it was garbage collected
    assert obs_ref() is None


def test_observable_with_validator_gc():
    """Test that observables with validators can be garbage collected."""
    def validator(value: Any) -> tuple[bool, str]:
        return True, "Valid"
    
    # Create an observable with validator
    obs = XValue("test_value", validate_value_callback=validator)
    obs_ref = weakref.ref(obs)
    
    # Delete the observable
    del obs
    
    # Force garbage collection
    gc.collect()
    
    # Verify it was garbage collected
    assert obs_ref() is None
