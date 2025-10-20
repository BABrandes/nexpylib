
from nexpy import XSet

from test_base import ObservableTestCase
import pytest

class TestXSet(ObservableTestCase):
    """Test cases for XSet"""
    
    def setup_method(self):
        super().setup_method()
        self.observable = XSet({1, 2, 3})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        assert self.observable.set == {1, 2, 3}
    
    def test_add(self):
        """Test adding a new value"""
        self.observable.add(4)
        assert self.observable.set == {1, 2, 3, 4}
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listener(self.notification_callback)
        self.observable.add(7)
        assert self.notification_count == 1
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listener(self.notification_callback)
        self.observable.add(1)  # Same value
        assert self.notification_count == 0
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listener(self.notification_callback)
        self.observable.remove_listener(self.notification_callback)
        self.observable.add(10)
        assert self.notification_count == 0
    
    def test_multiple_listeners(self):
        """Test multiple listeners"""
        count1, count2 = 0, 0
        
        def callback1():
            nonlocal count1
            count1 += 1
        
        def callback2():
            nonlocal count2
            count2 += 1
        
        self.observable.add_listener(callback1)
        self.observable.add_listener(callback2)
        self.observable.add(13)
        
        assert count1 == 1
        assert count2 == 1
    
    def test_initialization_with_carries_bindable_set(self):
        """Test initialization with CarriesBindableSet"""
        # Create a source observable set
        source = XSet({1, 2, 3})
        
        # Create a new observable set initialized with the source
        target = XSet(source.set_hook)
        
        # Check that the target has the same initial value
        assert target.set == {1, 2, 3}
        
        # Check that they are bound together
        source.add(4)
        assert target.set == {1, 2, 3, 4}
        
        # Check bidirectional binding
        target.add(5)
        assert source.set == {1, 2, 3, 4, 5}
    
    def test_initialization_with_carries_bindable_set_chain(self):
        """Test initialization with CarriesBindableSet in a chain"""
        # Create a chain of observable sets
        obs1 = XSet({10})
        obs2 = XSet(obs1.set_hook)
        obs3 = XSet(obs2.set_hook)
        
        # Check initial values
        assert obs1.set == {10}
        assert obs2.set == {10}
        assert obs3.set == {10}
        
        # Change the first observable
        obs1.add(20)
        assert obs1.set == {10, 20}
        assert obs2.set == {10, 20}
        assert obs3.set == {10, 20}
        
        # Change the middle observable
        obs2.add(30)
        assert obs1.set == {10, 20, 30}
        assert obs2.set == {10, 20, 30}
        assert obs3.set == {10, 20, 30}
    
    def test_initialization_with_carries_bindable_set_unbinding(self):
        """Test that initialization with CarriesBindableSet can be unbound"""
        source = XSet({100})
        target = XSet(source.set_hook)
        
        # Verify they are bound
        assert target.set == {100}
        source.add(200)
        assert target.set == {100, 200}
        
        # Unbind them
        target.isolate_by_key("value")
        
        # Change source, target should not update
        source.add(300)
        assert target.set == {100, 200}  # Should remain unchanged
        
        # Change target, source should not update
        target.add(400)
        assert source.set == {100, 200, 300}  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_set_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = XSet({100})
        target1 = XSet(source.set_hook)
        target2 = XSet(source.set_hook)
        target3 = XSet(source.set_hook)
        
        # Check initial values
        assert target1.set == {100}
        assert target2.set == {100}
        assert target3.set == {100}
        
        # Change source, all targets should update
        source.add(200)
        assert target1.set == {100, 200}
        assert target2.set == {100, 200}
        assert target3.set == {100, 200}
        
        # Change one target, source and other targets should update
        target1.add(300)
        assert source.set == {100, 200, 300}
        assert target2.set == {100, 200, 300}
        assert target3.set == {100, 200, 300}
    
    def test_initialization_with_carries_bindable_set_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableSet"""
        # Test with empty set in source
        source_empty: XSet[int] = XSet(set())
        target_empty = XSet(source_empty.set_hook)
        assert target_empty.set == set()
        
        # Test with None in source
        source_none: XSet[int] = XSet(None)
        target_none = XSet(source_none.set_hook)
        assert target_none.set == set()
        
        # Test with single item
        source_single = XSet({42})
        target_single = XSet(source_single.set_hook)
        assert target_single.set == {42}
    
    def test_initialization_with_carries_bindable_set_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableSet"""
        source = XSet({100})
        target = XSet(source.set_hook)
        
        # Check binding consistency
        
        # Check that they are properly bound
        assert target.set_hook.is_joined_with(source.set_hook)
        assert source.set_hook.is_joined_with(target.set_hook)
    
    def test_initialization_with_carries_bindable_set_performance(self):
        """Test performance of initialization with CarriesBindableSet"""
        import time
        
        # Create source
        source = XSet({100})
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = XSet(source.set_hook)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 6 seconds)
        assert end_time - start_time < 6.0, "Initialization should be fast"
        
        # Verify the last target is properly bound
        target = XSet(source.set_hook)
        source.add(200)
        assert target.set == {100, 200}
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = XSet({10})
        obs2 = XSet({20})
        
        # Bind obs1 to obs2
        obs1.join_by_key("value", obs2.set_hook, "use_caller_value")  # type: ignore
        
        # Change obs1, obs2 should update to include obs1's elements
        obs1.add(30)
        assert obs2.set == {10, 30}
        
        # Change obs2, obs1 should also update (bidirectional)
        obs2.add(40)
        assert obs1.set == {10, 30, 40}
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = XSet({100})
        obs2 = XSet({200})
        
        # USE_CALLER_VALUE: target (obs2) gets caller's value
        obs1.join_by_key("value", obs2.set_hook, "use_caller_value")  # type: ignore
        assert obs2.set == {100}
        
        # Test update_observable_from_self mode
        obs3 = XSet({300})
        obs4 = XSet({400})
        obs3.join_by_key("value", obs4.set_hook, "use_target_value")  # type: ignore
        # USE_TARGET_VALUE means caller gets target's value
        assert obs3.set == {400}
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = XSet({10})
        obs2 = XSet({20})
        
        obs1.join_by_key("value", obs2.set_hook, "use_caller_value")  # type: ignore
        obs1.isolate_by_key("value")
        
        # Changes should no longer propagate
        obs1.add(50)
        assert obs1.set == {10, 50}
        assert obs2.set == {10}
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = XSet({10})
        with pytest.raises(ValueError):
            obs.join_by_key("value", obs.set_hook, "use_caller_value")  # type: ignore
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = XSet({10})
        obs2 = XSet({20})
        obs3 = XSet({30})
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.join_by_key("value", obs2.set_hook, "use_caller_value")  # type: ignore
        obs2.join_by_key("value", obs3.set_hook, "use_caller_value")  # type: ignore
        
        # Verify chain works
        obs1.add(100)
        assert obs2.set == {10, 100}
        assert obs3.set == {10, 100}
        
        # Break the chain by unbinding obs2 from obs3
        obs2.isolate_by_key("value")
        
        # Change obs1, obs2 should NOT update but obs3 should (obs1 and obs3 remain bound)
        obs1.add(200)
        assert obs2.set == {10, 100}  # obs2 is isolated
        assert obs3.set == {10, 100, 200}  # obs3 gets updated since obs1 and obs3 remain bound
        
        # Change obs3, obs1 should update since obs1 and obs3 remain bound after obs2.disconnect()
        obs3.add(300)
        assert obs1.set == {10, 100, 200, 300}
        assert obs2.set == {10, 100}
    
    def test_string_representation(self):
        """Test string and repr methods"""
        assert "XSet(options={1, 2, 3})" == str(self.observable)
        assert "XSet({1, 2, 3})" == repr(self.observable)
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = XSet({10})
        
        # Test is_listening_to
        assert not obs.is_listening_to(self.notification_callback)
        
        obs.add_listener(self.notification_callback)
        assert obs.is_listening_to(self.notification_callback)
        
        obs.remove_listener(self.notification_callback)
        assert not obs.is_listening_to(self.notification_callback)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = XSet({10})
        obs2 = XSet({20})
        obs3 = XSet({30})
        
        # Bind obs2 and obs3 to obs1
        obs2.join_by_key("value", obs1.set_hook, "use_caller_value")  # type: ignore
        obs3.join_by_key("value", obs1.set_hook, "use_caller_value")  # type: ignore
        
        # Change obs1, both should update to obs1's value
        obs1.add(100)
        assert obs2.set == {30, 100}
        assert obs3.set == {30, 100}
        
        # Change obs2, obs1 should also update (bidirectional), obs3 should also update
        obs2.add(200)
        assert obs1.set == {30, 100, 200}
        assert obs3.set == {30, 100, 200}
    
    def test_set_methods(self):
        """Test standard set methods"""
        obs = XSet({1, 2, 3})
        
        # Test add
        obs.add(4)
        assert obs.set == {1, 2, 3, 4}
        
        # Test remove
        obs.remove(2)
        assert obs.set == {1, 3, 4}
        
        # Test discard
        obs.discard(5)  # Non-existent item
        assert obs.set == {1, 3, 4}
        
        # Test clear
        obs.clear()
        assert obs.set == set()
    
    def test_set_copy_behavior(self):
        """Test that value returns immutable frozenset"""
        obs = XSet({1, 2, 3})
        
        # Get the set value
        set_value = obs.set
        
        # Verify it's a set (mutable - no immutability conversion)
        assert isinstance(set_value, set)
        assert set_value == {1, 2, 3}
        
        # Modifying the returned set doesn't affect the observable
        # (it should be a copy or the observable handles updates internally)
        set_value.add(4)
        # The observable's value shouldn't change
        assert obs.set == {1, 2, 3}
    
    def test_set_validation(self):
        """Test set validation"""
        # Test with valid set
        obs = XSet({1, 2, 3})
        assert obs.set == {1, 2, 3}
        
        # Test with None (should create empty set)
        obs_none: XSet[int] = XSet(None)
        assert obs_none.set == set()
        
        # Test with empty set
        obs_empty: XSet[int] = XSet(set())
        assert obs_empty.set == set()
    
    def test_set_binding_edge_cases(self):
        """Test edge cases for set binding"""
        # Test binding empty sets
        obs1: XSet[int] = XSet(set())
        obs2: XSet[int] = XSet(set())
        obs1.join_by_key("value", obs2.set_hook, "use_caller_value")  # type: ignore
        
        obs1.add(1)
        assert obs2.set == {1}
        
        # Test binding sets with same initial values
        obs3 = XSet({42})
        obs4 = XSet({42})
        obs3.join_by_key("value", obs4.set_hook, "use_caller_value")  # type: ignore
        
        obs3.add(100)
        assert obs4.set == {42, 100}
    
    def test_set_performance(self):
        """Test set performance characteristics"""
        import time
        
        # Test add performance
        obs: XSet[int] = XSet(set())
        start_time = time.time()
        
        for i in range(1000):
            obs.add(i)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 1.0, "Add operations should be fast"
        assert len(obs.set) == 1000
        
        # Test binding performance
        source = XSet({1, 2, 3})
        start_time = time.time()
        
        for _ in range(100):
            XSet(source.set_hook)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 1.0, "Binding operations should be fast"
    
    def test_set_error_handling(self):
        """Test set error handling"""
        obs = XSet({1, 2, 3})
        
        # Test remove non-existent item
        with pytest.raises(KeyError):
            obs.remove(99)
        
        # Test discard non-existent item (should not raise error)
        obs.discard(99)
        assert obs.set == {1, 2, 3}
    
    def test_set_binding_consistency(self):
        """Test binding system consistency"""
        source = XSet({100})
        target = XSet(source.set_hook)
        
        # Check binding consistency
        
        # Check that they are properly bound
        assert target.set_hook.is_joined_with(source.set_hook)
        assert source.set_hook.is_joined_with(target.set_hook)
    
    def test_set_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = XSet({10})
        with pytest.raises(ValueError):
            obs.join_by_key("value", None, "use_caller_value")  # type: ignore
    
    def test_set_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = XSet({42})
        obs2 = XSet({42})
        
        obs1.join_by_key("value", obs2.set_hook, "use_caller_value")  # type: ignore
        # Both should still have the same value
        assert obs1.set == {42}
        assert obs2.set == {42}
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = XSet({10})
        callback = lambda: None
        
        obs.add_listener(callback)
        assert len(obs.listeners) == 1
        
        obs.add_listener(callback)
        assert len(obs.listeners) == 1
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = XSet({10})
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listener(callback)
        assert len(obs.listeners) == 0

    def test_serialization(self):
        """Test the complete serialization and deserialization cycle."""
        # Step 1: Create an XSet instance
        obs = XSet({1, 2, 3})
        
        # Step 2: Fill it (modify the set)
        obs.add(4)
        obs.add(5)
        obs.remove(2)
        
        # Store the expected state after step 2
        expected_set = obs.set
        
        # Step 3: Serialize it and get a dict from "get_value_references_for_serialization"
        serialized_data = obs.get_values_for_serialization()
        
        # Verify serialized data contains expected keys
        assert "value" in serialized_data
        # Serialized data may be frozenset internally
        assert frozenset(serialized_data["value"]) == frozenset(expected_set) # type: ignore
        
        # Step 4: Delete the object
        del obs
        
        # Step 5: Create a fresh XSet instance
        obs_restored = XSet[int](set())
        
        # Verify it starts empty
        assert obs_restored.set == set()
        
        # Step 6: Use "set_value_references_from_serialization"
        obs_restored.set_values_from_serialization(serialized_data)
        
        # Step 7: Check if the object is the same as after step 2
        assert obs_restored.set == expected_set