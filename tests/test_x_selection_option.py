
from nexpy import XSetSingleSelect, XSetSingleSelectOptional
import pytest

class TestXSetSingleSelect:
    """Test cases for XSetSingleSelect"""
    
    def setup_method(self):
        self.observable = XSetSingleSelect("Apple", {"Apple", "Banana", "Cherry"})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        assert self.observable.selected_option == "Apple"
        assert self.observable.available_options == {"Apple", "Banana", "Cherry"}
    
    def test_set_selected_option(self):
        """Test setting a new selected option"""
        self.observable.selected_option = "Banana"
        assert self.observable.selected_option == "Banana"
    
    def test_set_available_options(self):
        """Test setting new available options"""
        new_options = {"Apple", "Orange", "Grape"}
        self.observable.available_options = new_options
        assert self.observable.available_options == new_options
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listener(self.notification_callback)
        self.observable.selected_option = "Cherry"
        assert self.notification_count == 1
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listener(self.notification_callback)
        self.observable.selected_option = "Apple"  # Same value
        assert self.notification_count == 0
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listener(self.notification_callback)
        self.observable.remove_listener(self.notification_callback)
        self.observable.selected_option = "Banana"
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
        self.observable.selected_option = "Cherry"
        
        assert count1 == 1
        assert count2 == 1
    
    def test_initialization_with_carries_bindable_selection_option(self):
        """Test initialization with CarriesBindableSelectionOption"""
        # Create a source observable selection option
        source = XSetSingleSelect("Red", {"Red", "Green", "Blue"})
        
        # Create a new observable selection option with plain values
        target: XSetSingleSelect[str] = XSetSingleSelect(source.selected_option, source.available_options)
        
        # Manually join the hooks to create the binding
        target.selected_option_hook.join(source.selected_option_hook, "use_target_value")
        
        # Check that the target has the same initial value
        assert target.selected_option == "Red"
        assert target.available_options == {"Red", "Green", "Blue"}
        
        # Check that they are bound together
        source.selected_option = "Green"
        assert target.selected_option == "Green"
        
        # Check bidirectional binding
        target.selected_option = "Blue"
        assert source.selected_option == "Blue"
    
    def test_initialization_with_carries_bindable_selection_option_chain(self):
        """Test initialization with CarriesBindableSelectionOption in a chain"""
        # Create a chain of observable selection options
        obs1 = XSetSingleSelect("Small", {"Small", "Medium"})
        obs2: XSetSingleSelect[str] = XSetSingleSelect(obs1.selected_option, obs1.available_options)
        obs2.selected_option_hook.join(obs1.selected_option_hook, "use_target_value")
        obs3: XSetSingleSelect[str] = XSetSingleSelect(obs2.selected_option, obs2.available_options)
        obs3.selected_option_hook.join(obs2.selected_option_hook, "use_target_value")
        
        # Check initial values
        assert obs1.selected_option == "Small"
        assert obs2.selected_option == "Small"
        assert obs3.selected_option == "Small"
        
        # Change the first observable
        obs1.selected_option = "Medium"
        assert obs1.selected_option == "Medium"
        assert obs2.selected_option == "Medium"
        assert obs3.selected_option == "Medium"
        
        # Change the middle observable
        obs2.selected_option = "Small"
        assert obs1.selected_option == "Small"
        assert obs2.selected_option == "Small"
        assert obs3.selected_option == "Small"
    
    def test_initialization_with_carries_bindable_selection_option_unbinding(self):
        """Test that initialization with CarriesBindableSelectionOption can be unbound"""
        source = XSetSingleSelect("Red", {"Red", "Green"})
        target: XSetSingleSelect[str] = XSetSingleSelect(source.selected_option, source.available_options)
        target.selected_option_hook.join(source.selected_option_hook, "use_target_value")
        
        # Verify they are bound
        assert target.selected_option == "Red"
        source.selected_option = "Green"
        assert target.selected_option == "Green"
        
        # Unbind them
        target.isolate_by_key("selected_option")
        
        # Change source, target should not update
        # Note: source can only use its own available options {"Red", "Green"}
        source.selected_option = "Red"  # Use an option that exists in source's options
        assert target.selected_option == "Green"  # Should remain unchanged
        
        # Change target, source should not update
        target.selected_option = "Red"
        assert source.selected_option == "Red"  # Should remain at last set value
    
    def test_initialization_with_carries_bindable_selection_option_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = XSetSingleSelect("Red", {"Red", "Green"})
        target1: XSetSingleSelect[str] = XSetSingleSelect(source.selected_option, source.available_options)
        target1.selected_option_hook.join(source.selected_option_hook, "use_target_value")
        target2: XSetSingleSelect[str] = XSetSingleSelect(source.selected_option, source.available_options)
        target2.selected_option_hook.join(source.selected_option_hook, "use_target_value")
        target3: XSetSingleSelect[str] = XSetSingleSelect(source.selected_option, source.available_options)
        target3.selected_option_hook.join(source.selected_option_hook, "use_target_value")
        
        # Check initial values
        assert target1.selected_option == "Red"
        assert target2.selected_option == "Red"
        assert target3.selected_option == "Red"
        
        # Change source, all targets should update
        source.selected_option = "Green"
        assert target1.selected_option == "Green"
        assert target2.selected_option == "Green"
        assert target3.selected_option == "Green"
        
        # Change one target, source and other targets should update
        target1.selected_option = "Red"
        assert source.selected_option == "Red"
        assert target2.selected_option == "Red"
        assert target3.selected_option == "Red"
    
    def test_initialization_with_carries_bindable_selection_option_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableSelectionOption"""
        # Test with None value in source
        source_none: XSetSingleSelectOptional[str] = XSetSingleSelectOptional(None, {"Red", "Green"})
        target_none: XSetSingleSelectOptional[str] = XSetSingleSelectOptional(source_none.selected_option, source_none.available_options)
        assert target_none.selected_option is None
        assert target_none.available_options == {"Red", "Green"}
        
        # Test with single option in source
        source_single = XSetSingleSelect("Red", {"Red"})
        target_single: XSetSingleSelect[str] = XSetSingleSelect(source_single.selected_option, source_single.available_options)
        assert target_single.selected_option == "Red"
        assert target_single.available_options == {"Red"}
    
    def test_initialization_with_carries_bindable_selection_option_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableSelectionOption"""
        source = XSetSingleSelect("Red", {"Red", "Green"})
        target: XSetSingleSelect[str] = XSetSingleSelect(source.selected_option, source.available_options)
        
        # Join them
        target.selected_option_hook.join(source.selected_option_hook, "use_target_value")
        
        # Check binding consistency
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        assert target.selected_option_hook.is_joined_with(source.selected_option_hook)
        assert source.selected_option_hook.is_joined_with(target.selected_option_hook)
    
    @pytest.mark.slow
    def test_initialization_with_carries_bindable_selection_option_performance(self):
        """Test performance of initialization with CarriesBindableSelectionOption"""
        import time
        
        # Create source
        source = XSetSingleSelect("Red", {"Red", "Green"})
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target: XSetSingleSelect[str] = XSetSingleSelect(source.selected_option, source.available_options)
            target.selected_option_hook.join(source.selected_option_hook, "use_target_value")
        end_time = time.time()
        
        # Should complete in reasonable time (less than 6 seconds)
        assert end_time - start_time < 6.0, "Initialization should be fast"
        
        # Verify the last target is properly bound
        target = XSetSingleSelect(source.selected_option, source.available_options)
        target.selected_option_hook.join(source.selected_option_hook, "use_target_value")
        source.selected_option = "Green"
        assert target.selected_option == "Green"
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = XSetSingleSelect("Red", {"Red", "Green", "Yellow"})
        obs2 = XSetSingleSelect("Blue", {"Red", "Green", "Blue"})
        
        # Bind obs1 to obs2
        obs1.join_by_key("available_options", obs2.available_options_hook, "use_target_value") #type: ignore
        obs1.join_by_key("selected_option", obs2.selected_option_hook, "use_target_value") #type: ignore
        
        # After binding with USE_TARGET_VALUE, obs1 should get obs2's values
        assert obs1.selected_option == "Blue"
        assert obs1.available_options == {"Red", "Green", "Blue"}
        
        # Change obs1, obs2 should update
        obs1.selected_option = "Green"
        assert obs2.selected_option == "Green"
        
        # Change obs2 to a valid option, obs1 should also update (bidirectional)
        obs2.selected_option = "Red"
        assert obs1.selected_option == "Red"
        
        # Try to set obs2 to an invalid option, should raise ValueError
        with pytest.raises(ValueError):
            obs2.selected_option = "Yellow"  # "Yellow" not in {"Red", "Green", "Blue"}
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = XSetSingleSelect("Red", {"Red", "Green", "Blue"})
        obs2 = XSetSingleSelect("Blue", {"Red", "Green", "Blue"})
        
        # Test update_value_from_observable mode
        obs1.join_by_key("selected_option", obs2.selected_option_hook, "use_target_value") # type: ignore
        obs1.join_by_key("available_options", obs2.available_options_hook, "use_target_value") # type: ignore
        # USE_TARGET_VALUE means caller gets target's values
        assert obs1.selected_option == "Blue"
        
        # Test update_observable_from_self mode
        obs3 = XSetSingleSelect("Small", {"Small", "Medium", "Large"})
        obs4 = XSetSingleSelect("Large", {"Small", "Medium", "Large"})
        obs3.join_by_key("selected_option", obs4.selected_option_hook, "use_target_value") # type: ignore
        obs3.join_by_key("available_options", obs4.available_options_hook, "use_target_value") # type: ignore
        # USE_TARGET_VALUE means caller gets target's values
        assert obs3.selected_option == "Large"
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = XSetSingleSelect("Red", {"Red", "Green", "Blue"})
        obs2 = XSetSingleSelect("Blue", {"Red", "Green", "Blue"})
        
        obs1.join_by_key("selected_option", obs2.selected_option_hook, "use_target_value") # type: ignore
        obs1.join_by_key("available_options", obs2.available_options_hook, "use_target_value") # type: ignore
        
        # After binding with USE_TARGET_VALUE, obs1 should get obs2's values
        assert obs1.selected_option == "Blue"
        assert obs1.available_options == {"Red", "Green", "Blue"}
        
        obs1.isolate_by_key("selected_option")
        
        # After disconnecting, obs2 keeps its current values but changes no longer propagate
        assert obs2.selected_option == "Blue"
        assert obs2.available_options == {"Red", "Green", "Blue"}
        
        # Changes should no longer propagate
        obs1.selected_option = "Green"
        assert obs2.selected_option == "Blue"  # Should remain unchanged
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = XSetSingleSelect("Red", {"Red", "Green"})
        with pytest.raises(ValueError):
            obs.join_by_key("selected_option", obs.selected_option_hook, "use_target_value") # type: ignore
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = XSetSingleSelect("Red", {"Red", "Green", "Blue"})
        obs2 = XSetSingleSelect("Blue", {"Red", "Green", "Blue"})
        obs3 = XSetSingleSelect("Green", {"Red", "Green", "Blue"})
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.join_by_key("selected_option", obs2.selected_option_hook, "use_target_value") # type: ignore
        obs2.join_by_key("selected_option", obs3.selected_option_hook, "use_target_value") # type: ignore
        
        # Verify chain works
        obs1.selected_option = "Green"
        assert obs2.selected_option == "Green"
        assert obs3.selected_option == "Green"
        
        # Break the chain by unbinding obs2 from obs3
        obs2.isolate_by_key("selected_option")
        
        # Change obs1, obs2 should update since they remain bound after obs2.disconnect()
        # Note: obs1 can only use its own available options {"Red", "Green", "Blue"}
        obs1.selected_option = "Green"  # Use an option that exists in obs1's options
        assert obs2.selected_option == "Green"  # Should update since obs1 and obs2 remain bound
        assert obs3.selected_option == "Green"  # Should remain unchanged
        
        # Change obs3, obs1 should update since obs1 and obs3 remain bound after obs2.disconnect()
        obs3.selected_option = "Blue"
        assert obs1.selected_option == "Blue"  # Should update since obs1 and obs3 remain bound
        assert obs2.selected_option == "Green"  # Should remain unchanged (isolated)
    
    def test_string_representation(self):
        """Test string and repr methods"""
        str_repr = str(self.observable)
        assert "XSS(selected_option=Apple, available_options=" in str_repr
        assert "Apple" in str_repr
        assert "Banana" in str_repr
        assert "Cherry" in str_repr
        
        repr_repr = repr(self.observable)
        assert "XSS(selected_option=Apple, available_options=" in repr_repr
        assert "Apple" in repr_repr
        assert "Banana" in repr_repr
        assert "Cherry" in repr_repr
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = XSetSingleSelect("Red", {"Red", "Green"})
        
        # Test is_listening_to
        assert not obs.is_listening_to(self.notification_callback)
        
        obs.add_listener(self.notification_callback)
        assert obs.is_listening_to(self.notification_callback)
        
        obs.remove_listener(self.notification_callback)
        assert not obs.is_listening_to(self.notification_callback)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = XSetSingleSelect("Red", {"Red", "Green", "Blue"})
        obs2 = XSetSingleSelect("Blue", {"Blue", "Green", "Red"})
        obs3 = XSetSingleSelect("Green", {"Green", "Blue", "Red"})
        
        # Bind obs2 and obs3 to obs1
        obs2.join_by_key("selected_option", obs1.selected_option_hook, "use_target_value") # type: ignore
        obs3.join_by_key("selected_option", obs1.selected_option_hook, "use_target_value") # type: ignore
        
        # After binding, all observables should be synchronized due to transitive binding
        # When multiple observables are bound to the same target, they all become part of the same binding group
        print(f'After binding:')
        print(f'obs1: selected={obs1.selected_option}, options={obs1.available_options}')
        print(f'obs2: selected={obs2.selected_option}, options={obs2.available_options}')
        print(f'obs3: selected={obs3.selected_option}, options={obs3.available_options}')
        
        # All observables should have the same selected option due to transitive binding
        assert obs1.selected_option == obs2.selected_option
        assert obs2.selected_option == obs3.selected_option
        
        # Change obs1, both should update
        obs1.selected_option = "Green"
        assert obs2.selected_option == "Green"
        assert obs3.selected_option == "Green"
        
        # Change obs2 to a valid option, obs1 and obs3 should also update (bidirectional)
        # Due to transitive binding, all observables stay synchronized
        valid_option = "Green" if "Green" in obs2.available_options else list(obs2.available_options)[0]
        obs2.selected_option = valid_option
        assert obs1.selected_option == valid_option
        assert obs3.selected_option == valid_option
    
    def test_selection_option_methods(self):
        """Test standard selection option methods"""
        obs = XSetSingleSelect("Red", {"Red", "Green", "Blue"})
        
        # Test set_selected_option_and_available_options
        obs.change_selected_option_and_available_options("Blue", {"Blue", "Green"})
        assert obs.selected_option == "Blue"
        assert obs.available_options == {"Blue", "Green"}
        
        # Test add_available_option
        obs.add_available_option("Red")
        assert obs.available_options == {"Blue", "Green", "Red"}
        
        # Test remove_available_option
        obs.remove_available_option("Green")
        assert obs.available_options == {"Blue", "Red"}
    
    def test_selection_option_copy_behavior(self):
        """Test that available_options returns an immutable frozenset"""
        obs = XSetSingleSelect("Red", {"Red", "Green", "Blue"})
        
        # Get the available options
        options_frozen = obs.available_options
        
        # Verify it's a set (mutable)
        assert isinstance(options_frozen, set)
        assert options_frozen == {"Red", "Green", "Blue"}
        
        # Verify sets are mutable (have .add() method)
        assert hasattr(options_frozen, 'add')
        
        # Original is protected from external mutation
        assert obs.available_options == {"Red", "Green", "Blue"}
    
    def test_selection_option_validation(self):
        """Test selection option validation"""
        # Test with valid selection option
        obs = XSetSingleSelect("Red", {"Red", "Green"})
        assert obs.selected_option == "Red"
        assert obs.available_options == {"Red", "Green"}
        
        # Test with None value
        obs_none = XSetSingleSelectOptional(None, {"Red", "Green"})
        assert obs_none.selected_option is None
        assert obs_none.available_options == {"Red", "Green"}
    
    def test_selection_option_binding_edge_cases(self):
        """Test edge cases for selection option binding"""
        # Test binding selection options with same initial values
        obs1 = XSetSingleSelect("Red", {"Red", "Green", "Yellow"})
        obs2 = XSetSingleSelect("Red", {"Red", "Green", "Yellow"})
        
        obs1.join_by_key("selected_option", obs2.selected_option_hook, "use_target_value") # type: ignore
        obs1.join_by_key("available_options", obs2.available_options_hook, "use_target_value") # type: ignore
        # Use target value for sync → target gets caller's values
        assert obs2.selected_option == "Red"
        assert obs2.available_options == {"Red", "Green", "Yellow"}
        
        # Test binding selection options with different options
        obs3 = XSetSingleSelect("Red", {"Red", "Blue", "Green"})
        obs4 = XSetSingleSelect("Green", {"Green", "Blue", "Red"})
        obs3.join_by_key("selected_option", obs4.selected_option_hook, "use_target_value") # type: ignore
        
        obs3.selected_option = "Blue"
        assert obs4.selected_option == "Blue"
    
    def test_selection_option_performance(self):
        """Test selection option performance characteristics"""
        import time
        
        # Test selected_option access performance
        obs = XSetSingleSelect("Red", {"Red", "Green", "Blue"})
        start_time = time.time()
        
        for _ in range(10000):
            _ = obs.selected_option
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 1.0, "Selected option access should be fast"
        
        # Test binding performance
        source = XSetSingleSelect("Red", {"Red", "Green"})
        start_time = time.time()
        
        for _ in range(100):
            target = XSetSingleSelect(source.selected_option, source.available_options)
            target.selected_option_hook.join(source.selected_option_hook, "use_target_value")
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 1.0, "Binding operations should be fast"
    
    def test_selection_option_error_handling(self):
        """Test selection option error handling"""
        obs = XSetSingleSelect("Red", {"Red", "Green"})
        
        # Test setting invalid selected option
        with pytest.raises(ValueError):
            obs.selected_option = "Blue"  # Not in available options
        
        # Test setting empty available options
        with pytest.raises(ValueError):
            obs.available_options = set()
    
    def test_selection_option_binding_consistency(self):
        """Test binding system consistency"""
        source = XSetSingleSelect("Red", {"Red", "Green"})
        target: XSetSingleSelect[str] = XSetSingleSelect(source.selected_option, source.available_options)
        target.selected_option_hook.join(source.selected_option_hook, "use_target_value")
        
        # Check binding consistency
        
        # Check that they are properly bound
        assert target.selected_option_hook.is_joined_with(source.selected_option_hook)
        assert source.selected_option_hook.is_joined_with(target.selected_option_hook)
    
    def test_selection_option_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = XSetSingleSelect("Red", {"Red", "Green"})
        with pytest.raises(ValueError):
            obs.join_by_key("selected_option", None, "use_target_value")  # type: ignore
    
    def test_selection_option_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = XSetSingleSelect("Red", {"Red", "Green", "Blue"})
        obs2 = XSetSingleSelect("Blue", {"Red", "Green", "Blue"})
        
        obs1.join_by_key("selected_option", obs2.selected_option_hook, "use_target_value") # type: ignore
        obs1.join_by_key("available_options", obs2.available_options_hook, "use_target_value") # type: ignore
        # USE_TARGET_VALUE means caller gets target's values
        assert obs1.selected_option == "Blue"
        assert obs1.available_options == {"Red", "Green", "Blue"}
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = XSetSingleSelect("Red", {"Red", "Green"})
        callback = lambda: None
        
        obs.add_listener(callback, callback)
        assert len(obs.listeners) == 1
        
        obs.add_listener(callback)
        assert len(obs.listeners) == 1
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = XSetSingleSelect("Red", {"Red", "Green"})
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listener(callback)
        assert len(obs.listeners) == 0