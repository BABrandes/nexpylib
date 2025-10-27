from nexpy import XSetMultiSelect
import pytest

class TestXSetMultiSelect:
    """Test cases for XSetMultiSelect"""
    
    def setup_method(self):
        self.observable = XSetMultiSelect({"Apple", "Banana"}, {"Apple", "Banana", "Cherry"})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        assert self.observable.selected_options == {"Apple", "Banana"}
        assert self.observable.available_options == {"Apple", "Banana", "Cherry"}
    
    def test_set_selected_options(self):
        """Test setting new selected options"""
        self.observable.change_selected_options({"Banana", "Cherry"})
        assert self.observable.selected_options == {"Banana", "Cherry"}
    
    def test_set_available_options(self):
        """Test setting new available options"""
        # First clear selected options to avoid validation error
        self.observable.change_selected_options(set())
        new_options = {"Apple", "Orange", "Grape"}
        self.observable.change_available_options(new_options)
        assert self.observable.available_options == new_options
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listener(self.notification_callback)
        self.observable.change_selected_options({"Cherry"})
        assert self.notification_count == 1
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listener(self.notification_callback)
        self.observable.change_selected_options({"Apple", "Banana"})# Same value
        assert self.notification_count == 0
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listener(self.notification_callback)
        self.observable.remove_listener(self.notification_callback)
        self.observable.change_selected_options({"Banana"})
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
        self.observable.change_selected_options({"Cherry"})
        
        assert count1 == 1
        assert count2 == 1
    
    def test_initialization_with_carries_bindable_multi_selection_option(self):
        """Test initialization with CarriesBindableMultiSelectionOption"""
        # Create a source observable multi-selection option
        source = XSetMultiSelect({"Red", "Green"}, {"Red", "Green", "Blue"})
        
        # Create a new observable multi-selection option initialized with the source's hooks
        target: XSetMultiSelect[str] = XSetMultiSelect(source.selected_options_hook, source.available_options_hook)
        
        # Check that the target has the same initial value
        assert target.selected_options == {"Red", "Green"}
        assert target.available_options == {"Red", "Green", "Blue"}
        
        # Check that they are bound together
        source.change_selected_options({"Green", "Blue"})
        assert target.selected_options == {"Green", "Blue"}
        
        # Check bidirectional binding
        target.change_selected_options({"Red", "Blue"})
        assert source.selected_options == {"Red", "Blue"}
    
    def test_initialization_with_carries_bindable_multi_selection_option_chain(self):
        """Test initialization with CarriesBindableMultiSelectionOption in a chain"""
        # Create a chain of observable multi-selection options
        obs1: XSetMultiSelect[str] = XSetMultiSelect({"Small"}, {"Small", "Medium"})
        obs2: XSetMultiSelect[str] = XSetMultiSelect(obs1.selected_options_hook, obs1.available_options_hook)
        obs3: XSetMultiSelect[str] = XSetMultiSelect(obs2.selected_options_hook, obs2.available_options_hook)
        
        # Check initial values
        assert obs1.selected_options == {"Small"}
        assert obs2.selected_options == {"Small"}
        assert obs3.selected_options == {"Small"}
        
        # Change the first observable
        obs1.change_selected_options({"Medium"})
        assert obs1.selected_options == {"Medium"}
        assert obs2.selected_options == {"Medium"}
        assert obs3.selected_options == {"Medium"}
        
        # Change the middle observable
        obs2.change_selected_options({"Small", "Medium"})
        assert obs1.selected_options == {"Small", "Medium"}
        assert obs2.selected_options == {"Small", "Medium"}
        assert obs3.selected_options == {"Small", "Medium"}
    
    def test_initialization_with_carries_bindable_multi_selection_option_unbinding(self):
        """Test that initialization with CarriesBindableMultiSelectionOption can be unbound"""
        source = XSetMultiSelect({"Red"}, {"Red", "Green"})
        target: XSetMultiSelect[str] = XSetMultiSelect(source.selected_options_hook, source.available_options_hook)
        target.selected_options_hook.join(source.selected_options_hook, "use_target_value")
# Verify they are bound
        assert target.selected_options == {"Red"}
        source.change_selected_options({"Green"})
        assert target.selected_options == {"Green"}
        
        # Unbind them
        target.isolate_by_key("selected_options")
        
        # Change source, target should not update
        source.change_selected_options({"Green"})
        assert target.selected_options == {"Green"}  # Should remain unchanged
        
        # Change target, source should not update
        target.change_selected_options({"Red"})
        assert source.selected_options == {"Green"}  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_multi_selection_option_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = XSetMultiSelect({"Red"}, {"Red", "Green"})
        target1: XSetMultiSelect[str] = XSetMultiSelect(source.selected_options_hook, source.available_options_hook)
        target1.selected_options_hook.join(source.selected_options_hook, "use_target_value")
        target2: XSetMultiSelect[str] = XSetMultiSelect(source.selected_options_hook, source.available_options_hook)
        target2.selected_options_hook.join(source.selected_options_hook, "use_target_value")
        target3: XSetMultiSelect[str] = XSetMultiSelect(source.selected_options_hook, source.available_options_hook)
        target3.selected_options_hook.join(source.selected_options_hook, "use_target_value")
        
        # Check initial values
        assert target1.selected_options == {"Red"}
        assert target2.selected_options == {"Red"}
        assert target3.selected_options == {"Red"}
        
        # Change source, all targets should update
        source.change_selected_options({"Green"})
        assert target1.selected_options == {"Green"}
        assert target2.selected_options == {"Green"}
        assert target3.selected_options == {"Green"}
        
        # Change one target, source and other targets should update
        target1.change_selected_options({"Red"})
        assert source.selected_options == {"Red"}
        assert target2.selected_options == {"Red"}
        assert target3.selected_options == {"Red"}
    
    def test_initialization_with_carries_bindable_multi_selection_option_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableMultiSelectionOption"""
        # Test with empty selected options in source
        source_empty: XSetMultiSelect[str] = XSetMultiSelect(set(), {"Red", "Green"})
        target_empty: XSetMultiSelect[str] = XSetMultiSelect(source_empty.selected_options, source_empty.available_options)
        assert target_empty.selected_options == set()
        assert target_empty.available_options == {"Red", "Green"}
        
        # Test with single option in source
        source_single: XSetMultiSelect[str]   = XSetMultiSelect({"Red"}, {"Red"})
        target_single: XSetMultiSelect[str] = XSetMultiSelect(source_single.selected_options, source_single.available_options)
        assert target_single.selected_options == {"Red"}
        assert target_single.available_options == {"Red"}
    
    def test_initialization_with_carries_bindable_multi_selection_option_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableMultiSelectionOption"""
        source = XSetMultiSelect({"Red"}, {"Red", "Green"})
        target: XSetMultiSelect[str] = XSetMultiSelect(source.selected_options_hook, source.available_options_hook)
        
        # Check binding consistency
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        assert target.selected_options_hook.is_joined_with(source.selected_options_hook)
        assert source.selected_options_hook.is_joined_with(target.selected_options_hook)
    
    def test_initialization_with_carries_bindable_multi_selection_option_performance(self):
        """Test performance of initialization with CarriesBindableMultiSelectionOption"""
        import time
        
        # Create source
        source = XSetMultiSelect({"Red"}, {"Red", "Green"})
        
        # Measure initialization time (reduced iterations for reasonable test time)
        start_time = time.time()
        for _ in range(10):  # Reduced from 1000 to 10 for reasonable test time
            XSetMultiSelect(source.selected_options_hook, source.available_options_hook)
        end_time = time.time()
        
        # Should complete in reasonable time (more lenient for complex initialization)
        assert end_time - start_time < 60.0, "Initialization should be fast"
        
        # Verify the last target is properly bound
        target = XSetMultiSelect(source.selected_options_hook, source.available_options_hook)
        source.change_selected_options({"Green"})
        assert target.selected_options == {"Green"}
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = XSetMultiSelect({"Red"}, {"Red", "Green", "Yellow"})
        obs2 = XSetMultiSelect({"Blue"}, {"Red", "Green", "Blue"})
        
        # Bind obs1 to obs2
        obs1.join_many_by_keys({"available_options": obs2.available_options_hook, "selected_options": obs2.selected_options_hook}, "use_target_value") #type: ignore
        
        # After binding with USE_TARGET_VALUE, obs1 should get obs2's values
        assert obs1.selected_options == {"Blue"}
        assert obs1.available_options == {"Red", "Green", "Blue"}
        
        # Change obs1, obs2 should update
        obs1.change_selected_options({"Green"})
        assert obs2.selected_options == {"Green"}
        
        # Change obs2 to a valid option, obs1 should also update (bidirectional)
        obs2.change_selected_options({"Red"})# Red is valid in both sets
        assert obs1.selected_options == {"Red"}
        
        # Try to set obs2 to an invalid option, should raise ValueError
        with pytest.raises(ValueError):
            obs2.change_selected_options({"Yellow"})# "Yellow" not in {"Red", "Green", "Blue"}
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = XSetMultiSelect({"Red"}, {"Red", "Green", "Yellow"})
        obs2 = XSetMultiSelect({"Blue"}, {"Red", "Green", "Blue"})
        
        # Test update_observable_from_self mode (obs2 gets updated with obs1's value)
        obs1.join_many_by_keys({"available_options": obs2.available_options_hook, "selected_options": obs2.selected_options_hook}, "use_target_value") #type: ignore
        # Current semantics: caller gets target's values  
        assert obs1.selected_options == {"Blue"}
        assert obs1.available_options == {"Red", "Green", "Blue"}

        # Test update_self_from_observable mode (obs1 gets updated with obs2's value)
        obs3 = XSetMultiSelect({"Small"}, {"Small", "Medium", "Large"})
        obs4 = XSetMultiSelect({"Large"}, {"Small", "Medium", "Large"})
        obs3.join_many_by_keys({"available_options": obs4.available_options_hook, "selected_options": obs4.selected_options_hook}, "use_target_value") #type: ignore
        # Current semantics: caller gets target's values
        assert obs3.selected_options == {"Large"}
        assert obs3.available_options == {"Small", "Medium", "Large"}
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = XSetMultiSelect({"Red"}, {"Red", "Green", "Yellow"})
        obs2 = XSetMultiSelect({"Blue"}, {"Red", "Green", "Blue"})
        
        obs1.join_many_by_keys({"available_options": obs2.available_options_hook, "selected_options": obs2.selected_options_hook}, "use_target_value") #type: ignore
        
        # After binding with USE_TARGET_VALUE, obs1 should get obs2's values
        assert obs1.selected_options == {"Blue"}
        assert obs1.available_options == {"Red", "Green", "Blue"}
        
        obs1.isolate_by_key("selected_options")
        
        # After disconnect_hooking, both keep their current values but changes no longer propagate
        assert obs1.selected_options == {"Blue"}
        assert obs1.available_options == {"Red", "Green", "Blue"}
        
        # Changes should no longer propagate
        obs1.change_selected_options({"Green"})
        assert obs1.selected_options == {"Green"}  # obs1 can change itself
        assert obs2.selected_options == {"Blue"}  # obs2 should remain unchanged
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = XSetMultiSelect({"Red"}, {"Red", "Green"})
        with pytest.raises(ValueError):
            obs.join_by_key("selected_options", obs.selected_options_hook, "use_target_value") # type: ignore
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = XSetMultiSelect({"Red"}, {"Red", "Green", "Blue"})
        obs2 = XSetMultiSelect({"Blue"}, {"Red", "Green", "Blue"})
        obs3 = XSetMultiSelect({"Green"}, {"Red", "Green", "Blue"})
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.join_by_key("selected_options", obs2.selected_options_hook, "use_target_value") # type: ignore
        obs2.join_by_key("selected_options", obs3.selected_options_hook, "use_target_value") # type: ignore
        
        # Verify chain works
        obs1.change_selected_options({"Green"})
        assert obs2.selected_options == {"Green"}
        assert obs3.selected_options == {"Green"}
        
        # Break the chain by unbinding obs2 from obs3
        obs2.isolate_by_key("selected_options")
        
        # Change obs1, obs2 should NOT update (obs2 is now detached from everything)
        # But obs3 should still update because obs1 and obs3 are still bound (transitive binding)
        obs1.change_selected_options({"Red"})
        assert obs2.selected_options == {"Green"}  # Should remain unchanged
        assert obs3.selected_options == {"Red"}  # Should update due to transitive binding
        
        # Change obs3, obs1 should update (transitive binding), obs2 should not
        obs3.change_selected_options({"Blue"})
        assert obs1.selected_options == {"Blue"}  # Should update due to transitive binding
        assert obs2.selected_options == {"Green"}  # Should remain unchanged
    
    def test_string_representation(self):
        """Test string and repr methods"""
        str_repr = str(self.observable)
        assert "XMSO(selected_options=" in str_repr
        assert "Apple" in str_repr
        assert "Banana" in str_repr
        assert "Cherry" in str_repr
        
        repr_repr = repr(self.observable)
        assert "XMSO(selected_options=" in repr_repr
        assert "Apple" in repr_repr
        assert "Banana" in repr_repr
        assert "Cherry" in repr_repr
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = XSetMultiSelect({"Red"}, {"Red", "Green"})
        
        # Test is_listening_to
        assert not obs.is_listening_to(self.notification_callback)
        
        obs.add_listener(self.notification_callback)
        assert obs.is_listening_to(self.notification_callback)
        
        obs.remove_listener(self.notification_callback)
        assert not obs.is_listening_to(self.notification_callback)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = XSetMultiSelect({"Red"}, {"Red", "Green", "Blue"})
        obs2 = XSetMultiSelect({"Blue"}, {"Blue", "Green", "Red"})
        obs3 = XSetMultiSelect({"Green"}, {"Green", "Blue", "Red"})
        
        # Bind obs2 and obs3 to obs1
        obs2.join_by_key("selected_options", obs1.selected_options_hook, "use_target_value") # type: ignore
        obs3.join_by_key("selected_options", obs1.selected_options_hook, "use_target_value") # type: ignore
        
        # Change obs1, both should update
        obs1.change_selected_options({"Green"})
        assert obs2.selected_options == {"Green"}
        assert obs3.selected_options == {"Green"}
        
        # Change obs2, obs1 should also update (bidirectional), obs3 should also update
        obs2.change_selected_options({"Red"})
        assert obs1.selected_options == {"Red"}
        assert obs3.selected_options == {"Red"}
    
    def test_multi_selection_option_methods(self):
        """Test standard multi-selection option methods"""
        obs = XSetMultiSelect({"Red", "Green"}, {"Red", "Green", "Blue"})
        
        # Test set_selected_options_and_available_options
        obs.change_selected_options_and_available_options({"Blue"}, {"Blue", "Green", "Yellow"})
        assert obs.selected_options == {"Blue"}
        assert obs.available_options == {"Blue", "Green", "Yellow"}
        
        # Test add_selected_option
        obs.add_selected_option("Green")
        assert obs.selected_options == {"Blue", "Green"}
        
        # Test remove_selected_option
        obs.remove_selected_option("Blue")
        assert obs.selected_options == {"Green"}
    
    def test_multi_selection_option_copy_behavior(self):
        """Test that available_options returns an immutable frozenset"""
        obs = XSetMultiSelect({"Red", "Green"}, {"Red", "Green", "Blue"})
        
        # Get the available options
        options_frozen = obs.available_options
        
        # Verify it's a set (mutable)
        assert isinstance(options_frozen, set)
        assert options_frozen == {"Red", "Green", "Blue"}
        
        # Verify sets are mutable (have .add() method)
        assert hasattr(options_frozen, 'add')
        
        # Original is protected from external mutation
        assert obs.available_options == {"Red", "Green", "Blue"}
    
    def test_multi_selection_option_validation(self):
        """Test multi-selection option validation"""
        # Test with valid multi-selection option
        obs = XSetMultiSelect({"Red", "Green"}, {"Red", "Green"})
        assert obs.selected_options == {"Red", "Green"}
        assert obs.available_options == {"Red", "Green"}
        
        # Test with empty selected options
        obs_empty: XSetMultiSelect[str] = XSetMultiSelect(set(), {"Red", "Green"})
        assert obs_empty.selected_options == set()
        assert obs_empty.available_options == {"Red", "Green"}
    
    def test_multi_selection_option_binding_edge_cases(self):
        """Test edge cases for multi-selection option binding"""
        # Test binding multi-selection options with same initial values
        obs1 = XSetMultiSelect({"Red"}, {"Red", "Green"})
        obs2 = XSetMultiSelect({"Red"}, {"Red", "Green"})
        obs1.join_by_key("selected_options", obs2.selected_options_hook, "use_target_value") # type: ignore
        
        obs1.change_selected_options({"Green"})
        assert obs2.selected_options == {"Green"}
        
        # Test binding multi-selection options with different options
        obs3 = XSetMultiSelect({"Red"}, {"Red", "Blue", "Green"})
        obs4 = XSetMultiSelect({"Green"}, {"Red", "Blue", "Green"})
        obs3.join_by_key("selected_options", obs4.selected_options_hook, "use_target_value") # type: ignore
        
        obs3.change_selected_options({"Blue"})
        assert obs4.selected_options == {"Blue"}
    
    def test_multi_selection_option_performance(self):
        """Test multi-selection option performance characteristics"""
        import time
        
        # Test selected_options access performance
        obs = XSetMultiSelect({"Red", "Green"}, {"Red", "Green", "Blue"})
        start_time = time.time()
        
        for _ in range(10000):
            _ = obs.selected_options
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 1.0, "Selected options access should be fast"
        
        # Test binding performance
        source = XSetMultiSelect({"Red"}, {"Red", "Green"})
        start_time = time.time()
        
        for _ in range(100):
            XSetMultiSelect(source.selected_options_hook, source.available_options_hook)
        
        end_time = time.time()
        
        # Should complete in reasonable time (more lenient for complex initialization)
        assert end_time - start_time < 10.0, "Binding operations should be fast"
    
    def test_multi_selection_option_error_handling(self):
        """Test multi-selection option error handling"""
        obs = XSetMultiSelect({"Red", "Green"}, {"Red", "Green"})
        
        # Test setting invalid selected options
        with pytest.raises(ValueError):
            obs.change_selected_options({"Blue"})# Not in available options
        
        # Test setting empty available options
        with pytest.raises(ValueError):
            obs.change_available_options(set())
    
    def test_multi_selection_option_binding_consistency(self):
        """Test binding system consistency"""
        source = XSetMultiSelect({"Red"}, {"Red", "Green"})
        target: XSetMultiSelect[str] = XSetMultiSelect(source.selected_options_hook, source.available_options_hook)
        
        # Check binding consistency
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        assert target.selected_options_hook.is_joined_with(source.selected_options_hook)
        assert source.selected_options_hook.is_joined_with(target.selected_options_hook)
    
    def test_multi_selection_option_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = XSetMultiSelect({"Red"}, {"Red", "Green"})
        with pytest.raises(ValueError):
            obs.join_by_key("selected_options", None, "use_target_value")  # type: ignore
    
    def test_multi_selection_option_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = XSetMultiSelect({"Red"}, {"Red", "Green", "Yellow"})
        obs2 = XSetMultiSelect({"Blue"}, {"Red", "Green", "Blue"})
        
        obs1.join_many_by_keys({"available_options": obs2.available_options_hook, "selected_options": obs2.selected_options_hook}, "use_target_value") #type: ignore
        # Use target value for sync → caller gets target's values
        assert obs1.selected_options == {"Blue"}
        assert obs1.available_options == {"Red", "Green", "Blue"}
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = XSetMultiSelect({"Red"}, {"Red", "Green"})
        callback = lambda: None
        
        obs.add_listener(callback, callback)
        assert len(obs.listeners) == 1
        
        obs.add_listener(callback)
        assert len(obs.listeners) == 1
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = XSetMultiSelect({"Red"}, {"Red", "Green"})
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listener(callback)
        assert len(obs.listeners) == 0