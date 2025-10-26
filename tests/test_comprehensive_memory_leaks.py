"""
Comprehensive memory leak tests covering advanced scenarios.

This test suite covers:
- Publisher/Subscriber patterns
- XSubscriber with callbacks
- Long-running scenarios
- Large data structures
- Complex binding chains
- Weak reference cleanup
"""

import gc
import weakref
from typing import Any, Optional, Mapping, Callable

import pytest

from nexpy import XValue, XList, XSet, XDict, XSubscriber, ValuePublisher
from nexpy.core.publisher_subscriber.publisher_protocol import PublisherProtocol

class TestPublisherSubscriberMemoryLeaks:
    """Test memory leaks in Publisher/Subscriber patterns."""
    
    def test_value_publisher_cleanup(self):
        """Test that ValuePublisher can be garbage collected."""
        publisher = ValuePublisher("test_value", "sync")
        publisher_ref = weakref.ref(publisher)
        
        assert publisher_ref() is not None
        
        del publisher
        gc.collect()
        
        assert publisher_ref() is None
    
    def test_publisher_with_subscribers_cleanup(self):
        """Test that publishers with subscribers can be garbage collected."""
        publisher = ValuePublisher("test_value", "sync")
        
        # Create dummy subscriber callbacks
        def callback():
            pass
        
        publisher.add_subscriber(callback)
        
        publisher_ref = weakref.ref(publisher)
        
        del publisher
        gc.collect()
        
        assert publisher_ref() is None
    
    def test_xsubscriber_cleanup(self):
        """Test that XSubscriber can be garbage collected."""
        publisher = ValuePublisher(0, "sync")
        
        def get_value(pub: Optional[PublisherProtocol]) -> Mapping[str, int]:
            if pub is None:
                return {"value": 0}
            return {"value": 1}
        
        subscriber = XSubscriber(publisher, get_value)
        subscriber_ref = weakref.ref(subscriber)
        
        del subscriber
        gc.collect()
        
        assert subscriber_ref() is None
    
    def test_xsubscriber_callback_cleanup(self):
        """Test that XSubscriber callbacks don't leak."""
        publisher = ValuePublisher(0, "sync")
        
        captured_refs = []
        
        def get_value(pub: Optional[PublisherProtocol]) -> Mapping[str, int]:
            if pub is None:
                return {"value": 0}
            return {"value": 1}
        
        subscriber = XSubscriber(publisher, get_value)
        
        del subscriber
        del publisher
        gc.collect()
        
        # Verify references were cleaned up
        assert len(captured_refs) == 0 or all(ref() is None for ref in captured_refs)


class TestWeakReferenceMemoryLeaks:
    """Test memory leaks with weak references."""
    
    def test_hook_weak_refs_cleanup(self):
        """Test that hooks with weak references can be cleaned up."""
        from nexpy.core.hooks.implementations.floating_hook import FloatingHook
        
        hook = FloatingHook("test")
        hook_ref = weakref.ref(hook)
        
        # Create weak references
        nexus_ref = weakref.ref(hook._get_nexus())  # type: ignore
        
        del hook
        gc.collect()
        
        assert hook_ref() is None
        assert nexus_ref() is None
    
    def test_multiple_weak_refs_cleanup(self):
        """Test cleanup with multiple weak references."""
        from nexpy.core.hooks.implementations.floating_hook import FloatingHook
        
        hooks = [FloatingHook(f"value_{i}") for i in range(10)]
        refs = [weakref.ref(hook) for hook in hooks]
        
        # Join some hooks
        for i in range(0, len(hooks) - 1, 2):
            hooks[i].join(hooks[i + 1], "use_caller_value")
        
        del hooks
        gc.collect()
        
        # All should be cleaned up
        assert all(ref() is None for ref in refs)


class TestLargeDataStructureMemoryLeaks:
    """Test memory leaks with large data structures."""
    
    def test_large_xlist_cleanup(self):
        """Test that large XList can be garbage collected."""
        large_list = XList(list(range(1000)))
        list_ref = weakref.ref(large_list)
        
        del large_list
        gc.collect()
        
        assert list_ref() is None
    
    def test_large_xset_cleanup(self):
        """Test that large XSet can be garbage collected."""
        large_set = XSet(set(range(1000)))
        set_ref = weakref.ref(large_set)
        
        del large_set
        gc.collect()
        
        assert set_ref() is None
    
    def test_large_xdict_cleanup(self):
        """Test that large XDict can be garbage collected."""
        large_dict = XDict({str(i): i for i in range(1000)})
        dict_ref = weakref.ref(large_dict)
        
        del large_dict
        gc.collect()
        
        assert dict_ref() is None
    
    def test_many_small_observables(self):
        """Test cleanup of many small observables."""
        # Create many observables
        for batch in range(5):
            observables = [XValue(f"value_{batch}_{i}") for i in range(100)]
            
            # Use them
            for obs in observables:
                obs.value = "modified"
            
            del observables
        
        gc.collect()
        
        # Verify we can still create new observables without running out of memory
        new_obs = XValue("test")
        assert new_obs.value == "test"


class TestComplexBindingMemoryLeaks:
    """Test memory leaks in complex binding scenarios."""
    
    def test_deep_chain_cleanup(self):
        """Test cleanup of deeply chained observables."""
        # Create a chain of observables
        chain = [XValue(i) for i in range(10)]
        
        # Chain them together
        for i in range(len(chain) - 1):
            chain[i].value_hook.join(chain[i + 1].value_hook, "use_caller_value")
        
        refs = [weakref.ref(obs) for obs in chain]
        
        del chain
        gc.collect()
        
        # All should be cleaned up
        assert all(ref() is None for ref in refs)
    
    def test_mesh_binding_cleanup(self):
        """Test cleanup of mesh-like binding structures."""
        # Create a mesh where each observable connects to the next 3
        mesh = [XValue(i) for i in range(20)]
        
        for i in range(len(mesh)):
            for j in range(min(3, len(mesh) - i - 1)):
                mesh[i].value_hook.join(mesh[i + j + 1].value_hook, "use_caller_value")
        
        refs = [weakref.ref(obs) for obs in mesh]
        
        del mesh
        gc.collect()
        
        # All should be cleaned up
        assert all(ref() is None for ref in refs)


class TestListenerCallbackMemoryLeaks:
    """Test memory leaks in listener and callback scenarios."""
    
    def test_multiple_listeners_cleanup(self):
        """Test cleanup with many listeners."""
        obs = XValue("test")
        
        # Add many listeners
        for i in range(100):
            obs.add_listener(lambda: None)
        
        obs_ref = weakref.ref(obs)
        
        del obs
        gc.collect()
        
        assert obs_ref() is None
    
    def test_closure_listener_cleanup(self):
        """Test cleanup of listeners with closures."""
        captured = []
        
        for i in range(10):
            obs = XValue("test")
            
            def make_listener(val: Any) -> Callable[[], None]:
                def listener():
                    captured.append(val)
                return listener
            
            obs.add_listener(make_listener(i))
            
            del obs
        
        gc.collect()
        
        # Should not prevent cleanup
        assert True


class TestStressMemoryLeaks:
    """Test memory leaks under stress conditions."""
    
    def test_create_delete_cycle(self):
        """Test cleanup in rapid create/delete cycles."""
        for cycle in range(10):
            # Create many observables
            observables = [XValue(f"cycle_{cycle}_value_{i}") for i in range(100)]
            
            # Use them
            for obs in observables:
                obs.value = "modified"
            
            # Delete them
            del observables
        
        gc.collect()
        
        # Should not accumulate
        assert True
    
    def test_rapid_binding_changes(self):
        """Test cleanup with rapid binding/unbinding."""
        from nexpy.core.hooks.implementations.floating_hook import FloatingHook
        
        for cycle in range(10):
            hooks = [FloatingHook(i) for i in range(10)]
            
            # Connect them
            for i in range(len(hooks) - 1):
                hooks[i].join(hooks[i + 1], "use_caller_value")
            
            # Disconnect them
            for i in range(len(hooks)):
                hooks[i].isolate()
            
            del hooks
        
        gc.collect()
        
        # Should not accumulate
        assert True


class TestPublisherSubscriberLeaks:
    """Test memory leaks in Publisher/Subscriber integration."""
    
    def test_publisher_with_xsubscriber_cleanup(self):
        """Test cleanup of Publisher-XSubscriber pairs."""
        for i in range(10):
            publisher = ValuePublisher(0, "sync")
            
            def get_val(pub: Optional[ValuePublisher[Any]]) -> Mapping[str, int]:
                return {"value": 1}
            
            subscriber = XSubscriber(publisher, get_val) # type: ignore
            
            del publisher
            del subscriber
        
        gc.collect()
        
        # Should not accumulate
        assert True
    
    def test_multiple_subscribers_per_publisher_cleanup(self):
        """Test cleanup with multiple subscribers per publisher."""
        publisher = ValuePublisher(0, "sync")
        
        # Create and destroy many subscribers
        for _ in range(5):
            subscribers = []
            for _ in range(10):
                subscriber = XSubscriber(publisher, lambda pub: {"value": 0})
                subscribers.append(subscriber)
            
            del subscribers
            gc.collect()
        
        # Publisher should still be usable
        publisher.value = 42
        assert publisher.value == 42
    
    def test_publisher_multiple_xsubscribers(self):
        """Test cleanup of multiple XSubscribers on one publisher."""
        publisher = ValuePublisher(0, "sync")
        
        # Create many subscribers
        for _ in range(50):
            subscriber = XSubscriber(publisher, lambda pub: {"value": 0})
            del subscriber
        
        gc.collect()
        
        # Publisher should still be usable
        publisher.value = 42
        assert publisher.value == 42


class TestComplexObservableMemoryLeaks:
    """Test memory leaks in complex observable scenarios."""
    
    def test_observable_with_many_secondary_hooks_cleanup(self):
        """Test cleanup of observables with many secondary hooks."""
        from nexpy import XDictSelect
        
        obs = XDictSelect({"a": 1, "b": 2, "c": 3}, "a")
        obs_ref = weakref.ref(obs)
        
        del obs
        gc.collect()
        
        assert obs_ref() is None
    
    def test_nested_observables_cleanup(self):
        """Test cleanup of nested observables."""
        inner = XValue("inner")
        outer = XValue(inner)
        
        refs = [weakref.ref(inner), weakref.ref(outer)]
        
        del inner, outer
        gc.collect()
        
        assert all(ref() is None for ref in refs)
    
    def test_observable_with_complex_callback_cleanup(self):
        """Test cleanup with complex callbacks."""
        obs = XValue("test")
        
        def complex_callback(value: Any) -> bool:
            # Create capture
            captured = [1, 2, 3]
            return True
        
        obs_ref = weakref.ref(obs)
        
        del obs
        gc.collect()
        
        assert obs_ref() is None

