"""
Test for memory leaks in the hook-based architecture.

This test verifies that hooks and hook nexuses can be properly garbage collected
when they are no longer referenced.
"""

import gc
import weakref

from nexpy import XValue, XDictSelect, FloatingHook

from nexpy.core.nexus_system.nexus import Nexus


class TestMemoryLeaks:
    """Test for memory leaks in the hook-based architecture."""

    def test_hook_garbage_collection(self):
        """Test that standalone hooks can be garbage collected."""
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

    def test_hook_nexus_garbage_collection(self):
        """Test that hook nexuses can be garbage collected when empty."""
        # Create a hook nexus
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

    def test_hook_with_nexus_garbage_collection(self):
        """Test that hooks and their nexuses can be garbage collected together."""
        # Create a hook (which creates its own nexus)
        hook = FloatingHook("test_value")
        hook_ref = weakref.ref(hook)
        nexus_ref = weakref.ref(hook._get_nexus())  # type: ignore
        
        # Verify both exist
        assert hook_ref() is not None
        assert nexus_ref() is not None
        
        # Delete the hook
        del hook
        
        # Force garbage collection
        gc.collect()
        
        # Verify both were garbage collected
        assert hook_ref() is None
        assert nexus_ref() is None

    def test_connected_hooks_garbage_collection(self):
        """Test that connected hooks can be garbage collected when disconnected."""
        # Create two hooks
        hook1 = FloatingHook("value1")
        hook2 = FloatingHook("value2")
        
        hook1_ref = weakref.ref(hook1)
        hook2_ref = weakref.ref(hook2)
        
        # Connect them
        success, _ = hook1.join(hook2, "use_caller_value")
        assert success
        
        # Verify they're connected (same nexus)
        assert hook1._get_nexus() == hook2._get_nexus()  # type: ignore
        
        # Disconnect hook1
        hook1.isolate()
        
        # Verify they're now disconnected (different nexuses)
        assert hook1._get_nexus() != hook2._get_nexus()  # type: ignore
        
        # Delete hook1
        del hook1
        
        # Force garbage collection
        gc.collect()
        
        # Verify hook1 was garbage collected but hook2 still exists
        assert hook1_ref() is None
        assert hook2_ref() is not None
        
        # Delete hook2
        del hook2
        
        # Force garbage collection
        gc.collect()
        
        # Verify hook2 was also garbage collected
        assert hook2_ref() is None

    def test_observable_garbage_collection(self):
        """Test that observables and their hooks can be garbage collected."""
        # Create an observable
        obs = XValue("test_value")
        obs_ref = weakref.ref(obs)
        
        # Verify the observable exists
        assert obs_ref() is not None
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Verify the observable was garbage collected
        assert obs_ref() is None

    def test_complex_observable_garbage_collection(self):
        """Test that complex observables can be garbage collected."""
        # Create a complex observable
        obs = XDictSelect(
            dict_hook={"a": 1, "b": 2},
            key_hook="a",
            value_hook=None
        )
        obs_ref = weakref.ref(obs)
        
        # Verify the observable exists
        assert obs_ref() is not None
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Verify the observable was garbage collected
        assert obs_ref() is None

    def test_nexus_manager_no_memory_leaks(self):
        """Test that NexusManager doesn't hold references to hooks."""
        # Create hooks
        hook1 = FloatingHook("value1")
        hook2 = FloatingHook("value2")
        
        hook1_ref = weakref.ref(hook1)
        hook2_ref = weakref.ref(hook2)
        
        # Connect them through NexusManager
        success, _ = hook1.join(hook2, "use_caller_value")
        assert success
        
        # Delete the hooks
        del hook1
        del hook2
        
        # Force garbage collection
        gc.collect()
        
        # Verify hooks were garbage collected despite NexusManager still existing
        assert hook1_ref() is None
        assert hook2_ref() is None

    def test_circular_reference_prevention(self):
        """Test that circular references don't prevent garbage collection."""
        # Create hooks that reference each other through nexuses
        hook1 = FloatingHook("value1")
        hook2 = FloatingHook("value2")
        
        # Connect them (creates circular references through nexus)
        success, _ = hook1.join(hook2, "use_caller_value")
        assert success
        
        # Create weak references
        hook1_ref = weakref.ref(hook1)
        hook2_ref = weakref.ref(hook2)
        nexus_ref = weakref.ref(hook1._get_nexus())  # type: ignore
        
        # Delete both hooks
        del hook1
        del hook2
        
        # Force garbage collection
        gc.collect()
        
        # Verify everything was garbage collected despite circular references
        assert hook1_ref() is None
        assert hook2_ref() is None
        assert nexus_ref() is None

    def test_listener_memory_leaks(self):
        """Test that listeners don't prevent garbage collection."""
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
        
        # Verify the observable was garbage collected
        assert obs_ref() is None

    def test_callback_memory_leaks(self):
        """Test that callbacks don't prevent garbage collection."""
        # Create an observable with callbacks
        
        obs = XValue("test_value")
        obs_ref = weakref.ref(obs)
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Verify the observable was garbage collected
        assert obs_ref() is None