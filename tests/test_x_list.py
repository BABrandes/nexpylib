
from test_base import ObservableTestCase
import pytest

from nexpy.x_objects.list_like.x_list import XList

class TestXList(ObservableTestCase):
    """Test cases for XList (concrete implementation)"""
    
    def setup_method(self):
        super().setup_method()
        self.observable = XList([1, 2, 3])
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        assert self.observable.list == [1, 2, 3]
    
    def test_append(self):
        """Test appending a new value"""
        self.observable.append(4)
        assert self.observable.list == [1, 2, 3, 4]
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listener(self.notification_callback)
        self.observable.append(7)
        assert self.notification_count == 1
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listener(self.notification_callback)
        self.observable.list = [1, 2, 3]  # Same value
        assert self.notification_count == 0
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listener(self.notification_callback)
        self.observable.remove_listener(self.notification_callback)
        self.observable.append(10)
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
        self.observable.append(13)
        
        assert count1 == 1
        assert count2 == 1
    
    def test_initialization_with_carries_bindable_list(self):
        """Test initialization with CarriesBindableList"""
        # Create a source observable list
        source = XList([1, 2, 3])
        
        # Create a new observable list initialized with the source
        target = XList[int](source)
        
        # Check that the target has the same initial value
        assert target.list == [1, 2, 3]
        
        # Check that they are bound together
        source.append(4)
        assert target.list == [1, 2, 3, 4]
        
        # Check bidirectional binding
        target.append(5)
        assert source.list == [1, 2, 3, 4, 5]
    
    def test_initialization_with_carries_bindable_list_chain(self):
        """Test initialization with CarriesBindableList in a chain"""
        # Create a chain of observable lists
        obs1 = XList([10])
        obs2 = XList[int](obs1)
        obs3 = XList[int](obs2)
        
        # Check initial values
        assert obs1.list == [10]
        assert obs2.list == [10]
        assert obs3.list == [10]
        
        # Change the first observable
        obs1.append(20)
        assert obs1.list == [10, 20]
        assert obs2.list == [10, 20]
        assert obs3.list == [10, 20]     
        
        # Change the middle observable
        obs2.append(30)
        assert obs1.list == [10, 20, 30]
        assert obs2.list == [10, 20, 30]
        assert obs3.list == [10, 20, 30]
    
    def test_initialization_with_carries_bindable_list_unbinding(self):
        """Test that initialization with CarriesBindableList can be unbound"""
        source = XList([100])
        target = XList[int](source)
        
        # Verify they are bound
        assert target.list == [100]
        source.append(200)
        assert target.list == [100, 200]
        
        # Unbind them
        target.isolate_by_key("value")
        
        # Change source, target should not update
        source.append(300)
        assert target.list == [100, 200]  # Should remain unchanged
        
        # Change target, source should not update
        target.append(400)
        assert source.list == [100, 200, 300]  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_list_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = XList([100])
        target1 = XList[int](source)
        target2 = XList[int](source)
        target3 = XList[int](source)
        
        # Check initial values
        assert target1.list == [100]
        assert target2.list == [100]
        assert target3.list == [100]
        
        # Change source, all targets should update
        source.append(200)
        assert target1.list == [100, 200]
        assert target2.list == [100, 200]
        assert target3.list == [100, 200]
        
        # Change one target, source and other targets should update
        target1.append(300)
        assert source.list == [100, 200, 300]
        assert target2.list == [100, 200, 300]
        assert target3.list == [100, 200, 300]
    
    def test_initialization_with_carries_bindable_list_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableList"""
        # Test with empty list in source
        source_empty: XList[int] = XList([])
        target_empty = XList[int](source_empty)
        assert target_empty.list == []
        
        # Test with None in source
        source_none: XList[int] = XList(None)
        target_none = XList[int](source_none)
        assert target_none.list == []
        
        # Test with single item
        source_single = XList([42])
        target_single = XList[int](source_single)
        assert target_single.list == [42]
    
    def test_initialization_with_carries_bindable_list_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableList"""
        source = XList([100])
        target = XList[int](source)
        
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        assert target.list_hook.is_joined_with(source.list_hook)
        assert source.list_hook.is_joined_with(target.list_hook)
    
    def test_initialization_with_carries_bindable_list_performance(self):
        """Test performance of initialization with CarriesBindableList"""
        import time
        
        # Create source
        source = XList([100])
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = XList[int](source)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 6 seconds)
        assert end_time - start_time < 6.0, "Initialization should be fast"
        
        # Verify the last target is properly bound
        target = XList[int](source)
        source.append(200)
        assert target.list == [100, 200]
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = XList([10])
        obs2 = XList([20])
        
        # Bind obs1 to obs2
        obs1.join_by_key("value", obs2.list_hook, "use_caller_value")  # type: ignore
        
        # Change obs1, obs2 should update with obs1's value appended
        obs1.append(30)
        assert obs2.list == [10, 30]
        
        # Change obs2, obs1 should also update (bidirectional)
        obs2.append(40)
        assert obs1.list == [10, 30, 40]  # obs1 took obs2's initial value [20]
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = XList([100])
        obs2 = XList([200])
        
        # Test USE_CALLER_VALUE: use caller's value → target (obs2) gets caller's value
        obs1.join_by_key("value", obs2.list_hook, "use_caller_value")  # type: ignore
        assert obs2.list == [100]
        
        # Test update_observable_from_self mode
        obs3 = XList([300])
        obs4 = XList([400])
        obs3.join_by_key("value", obs4.list_hook, "use_target_value")  # type: ignore
        # USE_TARGET_VALUE means caller gets target's value
        assert obs3.list == [400]
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = XList([10])
        obs2 = XList([20])
        
        obs1.join_by_key("value", obs2.list_hook, "use_caller_value")  # type: ignore
        obs1.isolate_by_key("value")
        
        # Changes should no longer propagate
        obs1.append(50)
        assert obs1.list == [10, 50]
        assert obs2.list == [10]
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = XList([10])
        with pytest.raises(ValueError):
            obs.join_by_key("value", obs.list_hook, "use_caller_value")  # type: ignore
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = XList([10])
        obs2 = XList([20])
        obs3 = XList([30])
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.join_by_key("value", obs2.list_hook, "use_caller_value")  # type: ignore
        obs2.join_by_key("value", obs3.list_hook, "use_caller_value")  # type: ignore
        
        # Verify chain works: values converge to caller on each bind
        obs1.append(100)
        assert obs2.list == [10, 100]
        assert obs3.list == [10, 100]
        
        # Break the chain by unbinding obs2 from obs3
        obs2.isolate_by_key("value")
        
        # Change obs1, obs2 should NOT update but obs3 should (obs1 and obs3 remain bound)
        obs1.append(200)
        assert obs2.list == [10, 100]  # obs2 is isolated, should not update
        assert obs3.list == [10, 100, 200]  # obs3 gets updated since obs1 and obs3 remain bound
        
        # Change obs3, obs1 should update since obs1 and obs3 remain bound after obs2.disconnect()
        obs3.append(300)
        assert obs1.list == [10, 100, 200, 300]
        assert obs2.list == [10, 100]
    
    def test_string_representation(self):
        """Test string and repr methods"""
        assert str(self.observable) == "OL(value=[1, 2, 3])"
        assert repr(self.observable) == "XList([1, 2, 3])"
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = XList([10])
        
        # Test is_listening_to
        assert not obs.is_listening_to(self.notification_callback)
        
        obs.add_listener(self.notification_callback)
        assert obs.is_listening_to(self.notification_callback)
        
        obs.remove_listener(self.notification_callback)
        assert not obs.is_listening_to(self.notification_callback)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = XList([10])
        obs2 = XList([20])
        obs3 = XList([30])
        
        # Bind obs2 and obs3 to obs1
        obs2.join_by_key("value", obs1.list_hook, "use_caller_value")  # type: ignore
        obs3.join_by_key("value", obs1.list_hook, "use_caller_value")  # type: ignore
        
        # Change obs1, both should update to obs1's value
        obs1.append(100)
        assert obs2.list == [30, 100]
        assert obs3.list == [30, 100]
        
        # Change obs2, obs1 should also update (bidirectional), obs3 should also update
        obs2.append(200)
        assert obs1.list == [30, 100, 200]
        assert obs3.list == [30, 100, 200]
    
    def test_list_methods(self):
        """Test standard list methods"""
        obs = XList([1, 2, 3])
        
        # Test append
        obs.append(4)
        assert obs.list == [1, 2, 3, 4]
        
        # Test extend
        obs.extend([5, 6])
        assert obs.list == [1, 2, 3, 4, 5, 6]
        
        # Test insert
        obs.insert(0, 0)
        assert obs.list == [0, 1, 2, 3, 4, 5, 6]
        
        # Test remove
        obs.remove(3)
        assert obs.list == [0, 1, 2, 4, 5, 6]
        
        # Test pop
        popped = obs.pop()
        assert popped == 6
        assert obs.list == [0, 1, 2, 4, 5]
        
        # Test clear
        obs.clear()
        assert obs.list == []
    
    def test_list_indexing(self):
        """Test list indexing operations"""
        obs = XList([10, 20, 30, 40, 50])
        
        # Test getitem
        assert obs[0] == 10
        assert obs[-1] == 50
        
        # Test setitem
        obs[2] = 35
        assert obs.list == [10, 20, 35, 40, 50]
        
        # Test delitem
        del obs[1]
        assert obs.list == [10, 35, 40, 50]
        
        # Test slice operations
        obs[1:3] = [25, 30] # type: ignore
        assert obs.list == [10, 25, 30, 50]
    
    def test_list_comparison(self):
        """Test list comparison operations"""
        obs1 = XList([1, 2, 3])
        obs2 = XList([1, 2, 3])
        obs3 = XList([1, 2, 4])
        
        # Test equality
        assert obs1 == obs2
        assert obs1 != obs3
        
        # Test comparison with regular lists (compare values)
        assert obs1.list == [1, 2, 3]
        assert obs1.list != [1, 2, 4]
    
    def test_list_iteration(self):
        """Test list iteration"""
        obs = XList([1, 2, 3, 4, 5])
        
        # Test iteration
        items = list(obs)
        assert items == [1, 2, 3, 4, 5]  # list() creates a list
        assert tuple(obs) == (1, 2, 3, 4, 5)  # tuple() creates a tuple
        
        # Test length
        assert len(obs) == 5
        
        # Test contains
        assert 3 in obs
        assert 6 not in obs
    
    def test_list_copy_behavior(self):
        """Test that value returns a list"""
        obs = XList([1, 2, 3])
        
        # Get the list value
        list_value = obs.list
        
        # Verify it's a list
        assert isinstance(list_value, list)
        assert list_value == [1, 2, 3]
        
        # Modifying the returned list should not affect the observable
        list_value.append(4)
        # Original should be unchanged (defensive copy)
        assert obs.list == [1, 2, 3]
    
    def test_list_validation(self):
        """Test list validation"""
        # Test with valid list
        obs = XList([1, 2, 3])
        assert obs.list == [1, 2, 3]
        
        # Test with None (should create empty list)
        obs_none: XList[int] = XList(None)
        assert obs_none.list == []
        
        # Test with empty list
        obs_empty: XList[int] = XList([])
        assert obs_empty.list == []
    
    def test_list_binding_edge_cases(self):
        """Test edge cases for list binding"""
        # Test binding empty lists
        obs1: XList[int] = XList([])
        obs2: XList[int] = XList([])
        obs1.join_by_key("value", obs2.list_hook, "use_caller_value")  # type: ignore
        
        obs1.append(1)
        assert obs2.list == [1]
        
        # Test binding lists with same initial values
        obs3 = XList([42])
        obs4 = XList([42])
        obs3.join_by_key("value", obs4.list_hook, "use_caller_value")  # type: ignore
        
        obs3.append(100)
        assert obs4.list == [42, 100]
    
    def test_list_performance(self):
        """Test list performance characteristics"""
        import time
        
        # Test append performance
        obs: XList[int] = XList([])
        start_time = time.time()
        
        for i in range(1000):
            obs.append(i)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 1.0, "Append operations should be fast"
        assert len(obs.list) == 1000
        
        # Test binding performance
        source = XList([1, 2, 3])
        start_time = time.time()
        
        for _ in range(100):
            XList(source)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 1.0, "Binding operations should be fast"
    
    def test_list_error_handling(self):
        """Test list error handling"""
        obs = XList([1, 2, 3])
        
        # Test index out of range
        with pytest.raises(IndexError):
            _ = obs[10]
        
        # Test remove non-existent item (should raise ValueError, matching Python list behavior)
        with pytest.raises(ValueError):
            obs.remove(99)
        
        # Test pop from empty list
        empty_obs: XList[int] = XList([])
        with pytest.raises(IndexError):
            empty_obs.pop()
    
    def test_list_binding_consistency(self):
        """Test binding system consistency"""
        source = XList([100])
        target = XList[int](source)
        
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        assert target.list_hook.is_joined_with(source.list_hook)
        assert source.list_hook.is_joined_with(target.list_hook)
    
    def test_list_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = XList([10])
        with pytest.raises(ValueError):
            obs.join_by_key(None, "value", "use_caller_value")  # type: ignore
    
    def test_list_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = XList([42])
        obs2 = XList([42])
        
        obs1.join_by_key("value", obs2.list_hook, "use_caller_value")  # type: ignore
        # Both should still have the same value
        assert obs1.list == [42]
        assert obs2.list == [42]
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = XList([10])
        callback = lambda: None
        
        obs.add_listener(callback, callback)
        assert len(obs.listeners) == 1
        
        obs.add_listener(callback)
        assert len(obs.listeners) == 1
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = XList([10])
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listener(callback)
        assert len(obs.listeners) == 0

    def test_serialization(self):
        """Test the complete serialization and deserialization cycle."""
        # Step 1: Create an XList instance
        obs = XList([1, 2, 3])
        
        # Step 2: Fill it (modify the list)
        obs.append(4)
        obs.extend([5, 6])
        obs[0] = 10
        
        # Store the expected state after step 2
        expected_list = obs.list  # Tuples are immutable, no copy needed
        
        # Step 3: Serialize it and get a dict from "get_values_for_serialization"
        serialized_data = obs.get_values_for_serialization()
        
        # Verify serialized data contains expected keys
        assert "value" in serialized_data
        # Serialized data may be tuple internally
        assert list(serialized_data["value"]) == expected_list # type: ignore
        
        # Step 4: Delete the object
        del obs
        
        # Step 5: Create a fresh XList instance
        obs_restored = XList[int]([])
        
        # Verify it starts empty
        assert obs_restored.list == []
        
        # Step 6: Use "set_values_from_serialization"
        obs_restored.set_values_from_serialization(serialized_data)
        
        # Step 7: Check if the object is the same as after step 2
        assert obs_restored.list == expected_list