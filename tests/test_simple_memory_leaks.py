"""
Simple memory leak test to isolate the issue.
"""

import gc
import weakref

from nexpy import FloatingHook
from nexpy.core.nexus_system.nexus import Nexus


def test_simple_hook_gc():
    """Test simple hook garbage collection."""
    # Create a hook
    hook = FloatingHook("test_value")
    hook_ref = weakref.ref(hook)
    
    # Verify the hook exists
    assert hook_ref() is not None
    
    # Delete the hook
    del hook
    
    # Force garbage collection
    gc.collect()
    
    # Verify the hook was garbage collected
    assert hook_ref() is None


def test_hook_with_callback_gc():
    """Test hook with callback garbage collection."""
    # Create a callback that might hold a reference
    def callback(value: str) -> tuple[bool, str]:
        return True, "Successfully validated"
    
    # Create a hook with callback
    hook = FloatingHook("test_value", isolated_validation_callback=callback)
    hook_ref = weakref.ref(hook)
    
    # Verify the hook exists
    assert hook_ref() is not None
    
    # Delete the hook
    del hook
    
    # Force garbage collection
    gc.collect()
    
    # Verify the hook was garbage collected
    assert hook_ref() is None


def test_nexus_gc():
    """Test nexus garbage collection."""
    # Create a nexus
    nexus = Nexus("test_value")
    nexus_ref = weakref.ref(nexus)
    
    # Verify the nexus exists
    assert nexus_ref() is not None
    
    # Delete the nexus
    del nexus
    
    # Force garbage collection
    gc.collect()
    
    # Verify the nexus was garbage collected
    assert nexus_ref() is None
