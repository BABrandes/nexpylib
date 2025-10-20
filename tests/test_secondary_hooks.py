"""
Test cases for secondary hooks functionality across all observable types.

This test file validates the secondary hook architecture and ensures that
secondary hooks are properly recomputed when component values change.
"""

import pytest

from nexpy import XList, XDictSelect, XSet
from nexpy import XSetSingleSelect, XSetSingleSelectOptional, XSetMultiSelect


class TestEmitterHooksBasicFunctionality:
    """Test basic secondary hook functionality."""
    
    def test_x_list_length_secondary_hook(self):
        """Test that XList has a length secondary hook."""
        obs_list = XList([1, 2, 3])
        
        # Check that length hook exists
        assert "length" in [key for key in obs_list._secondary_hooks.keys()] # type: ignore
        
        # Check initial length value
        assert obs_list.length == 3
        
        # Check get_value_of_hook works for secondary hooks
        assert obs_list.length == 3
    
    def test_observable_dict_length_secondary_hook(self):
        """Test that XDictSelect has a length secondary hook.""" 
        obs_dict = XDictSelect({"a": 1, "b": 2}, "a")
        
        # Check that length hook exists
        assert "length" in [key for key in obs_dict._secondary_hooks.keys()] # type: ignore
        
        # Check initial length value
        assert obs_dict.length == 2
        
        # Check get_value_of_hook works for secondary hooks
        assert obs_dict.length == 2
    
    def test_observable_set_length_secondary_hook(self):
        """Test that XSet has a length secondary hook."""
        obs_set = XSet({1, 2, 3, 4})
        
        # Check that length hook exists
        assert "length" in [key for key in obs_set._secondary_hooks.keys()] # type: ignore
        
        # Check initial length value
        assert obs_set.length == 4
        
        # Check get_value_of_hook works for secondary hooks
        assert obs_set.length == 4
    
    def test_observable_tuple_length_secondary_hook(self):
        """Test that XList has a length secondary hook."""
        obs_tuple = XList((1, 2, 3, 4, 5))
        
        # Check that length hook exists
        assert "length" in [key for key in obs_tuple._secondary_hooks.keys()] # type: ignore
        
        # Check initial length value
        assert obs_tuple.length == 5
        
        # Check get_value_of_hook works for secondary hooks
        assert obs_tuple.length == 5


class TestEmitterHooksRecomputation:
    """Test that secondary hooks are properly recomputed when component values change."""
    
    def test_x_list_length_updates_on_append(self):
        """Test that length secondary hook updates when list is modified."""
        obs_list = XList([1, 2])
        
        # Initial length should be 2
        assert obs_list.length == 2
        
        # Append an item
        obs_list.append(3)
        
        # Length should now be 3 - THIS WILL FAIL due to the bug
        # The secondary hook is not being recomputed
        assert obs_list.length == 3, "Length secondary hook should update when list changes"
    
    def test_x_list_length_updates_on_clear(self):
        """Test that length secondary hook updates when list is cleared."""
        obs_list = XList([1, 2, 3, 4])
        
        # Initial length should be 4
        assert obs_list.length == 4
        
        # Clear the list
        obs_list.clear()
        
        # Length should now be 0
        assert obs_list.length == 0, "Length secondary hook should update when list is cleared"
    
    def test_x_list_length_updates_on_direct_assignment(self):
        """Test that length secondary hook updates when list_value is directly assigned."""
        obs_list = XList([1, 2])
        
        # Initial length should be 2
        assert obs_list.length == 2
        
        # Directly assign new list
        obs_list.list = [1, 2, 3, 4, 5]
        
        # Length should now be 5
        assert obs_list.length == 5, "Length secondary hook should update when list_value is assigned"
    
    def test_observable_dict_length_updates_on_modification(self):
        """Test that length secondary hook updates when dict is modified."""
        obs_dict = XDictSelect({"a": 1, "b": 2}, "a")
        
        # Initial length should be 2
        assert obs_dict.length == 2
        
        # Change to a dict with more keys
        obs_dict.change_dict_and_key({"a": 1, "b": 2, "c": 3}, "a")
        
        # Length should now be 3
        assert obs_dict.length == 3, "Length secondary hook should update when dict changes"

    def test_observable_tuple_length_updates_on_modification(self):
        """Test that length secondary hook updates when tuple is modified."""
        obs_tuple = XList((1, 2, 3))
        
        # Initial length should be 3
        assert obs_tuple.length == 3
        
        # Replace the tuple
        obs_tuple.change_value((1, 2, 3, 4, 5)) # type: ignore
        
        # Length should now be 5
        assert obs_tuple.length == 5, "Length secondary hook should update when tuple changes"


class TestEmitterHooksSelection:
    """Test secondary hooks for selection observables."""
    
    def test_selection_option_number_of_available_options(self):
        """Test that XSetSingleSelect has number_of_available_options secondary hook."""
        obs = XSetSingleSelect("a", {"a", "b", "c"})
        
        # Check that hook exists
        assert "number_of_available_options" in [key for key in obs._secondary_hooks.keys()] # type: ignore
        
        # Check initial value
        assert obs.number_of_available_options == 3
        
        # Modify available options
        obs.available_options = {"a", "b", "c", "d", "e"}
        
        # Should update to 5
        assert obs.number_of_available_options == 5, "Emitter hook should update when available options change"
    
    def test_optional_selection_option_number_of_available_options(self):
        """Test that XSetSingleSelectOptional has number_of_available_options secondary hook."""
        obs = XSetSingleSelectOptional(None, {"a", "b", "c"})
        
        # Check that hook exists  
        assert "number_of_available_options" in [key for key in obs._secondary_hooks.keys()] # type: ignore
        
        # Check initial value
        assert obs.number_of_available_options == 3
        
        # Modify available options
        obs.available_options = {"a", "b"}
        
        # Should update to 2
        assert obs.number_of_available_options == 2, "Emitter hook should update when available options change"
    
    def test_multi_selection_option_secondary_hooks(self):
        """Test that XSetMultiSelect has multiple secondary hooks."""
        obs = XSetMultiSelect({"a", "b"}, {"a", "b", "c", "d"})
        
        # Check that hooks exist
        assert "number_of_selected_options" in [key for key in obs._secondary_hooks.keys()] # type: ignore
        assert "number_of_available_options" in [key for key in obs._secondary_hooks.keys()] # type: ignore
        
        # Check initial values
        assert obs.number_of_selected_options == 2
        assert obs.number_of_available_options == 4
        
        # Modify selected options
        obs.selected_options = {"a", "b", "c"}
        
        # Should update
        assert obs.number_of_selected_options == 3, "Selected options secondary hook should update"
        
        # Modify available options
        obs.available_options = {"a", "b", "c", "d", "e", "f"}
        
        # Should update
        assert obs.number_of_available_options == 6, "Available options secondary hook should update"


class TestEmitterHooksListeners:
    """Test that secondary hooks properly notify listeners when they change."""
    
    def test_secondary_hook_listener_notification(self):
        """Test that listeners are notified when secondary hooks change."""
        obs_list = XList([1, 2])
        
        # Track listener calls
        listener_calls: list[int] = []
        
        def length_listener():
            listener_calls.append(obs_list.length)
        
        # Add listener to length hook
        length_hook = obs_list.length_hook
        length_hook.add_listener(length_listener)
        
        # Modify the list
        obs_list.append(3)
        obs_list.append(4)
        
        # Listeners should have been called with updated values
        # This test will fail due to the secondary hook bug
        assert len(listener_calls) == 2, "Length hook listener should be called when list changes"
        assert listener_calls == [3, 4], "Listener should receive updated length values"
    
    def test_secondary_hook_binding(self):
        """Test that secondary hooks can be bound to other observables."""
        obs_list = XList([1, 2, 3])
        
        # Create another observable to bind to the length
        from nexpy import XValue
        length_tracker = XValue(0)
        
        # Bind the length hook to the single value (reverse direction)
        length_hook = obs_list.length_hook
        length_hook.join(length_tracker.value_hook, "use_caller_value")  # type: ignore
        
        # Initial binding should work
        assert length_tracker.value == 3
        
        # Modify the list
        obs_list.extend([4, 5])
        
        # The bound observable should reflect the new length
        assert length_tracker.value == 5, "Bound observable should receive updated length from secondary hook"


class TestSecondaryHooksEdgeCases:
    """Test edge cases for secondary hooks."""
    
    def test_empty_secondary_hooks(self):
        """Test observables with no secondary hooks."""
        from nexpy import XValue
        obs = XValue(42)
        
        # Should have no secondary hooks (XValue only has _value_hook)
        assert hasattr(obs, '_value_hook') # type: ignore
        # XValue doesn't have secondary hooks, so no secondary hook callbacks
        assert not hasattr(obs, '_secondary_hook_callbacks') # type: ignore
    
    def test_get_value_of_hook_with_invalid_key(self):
        """Test get_value_of_hook with invalid secondary hook key."""
        obs_list = XList([1, 2, 3])
        
        with pytest.raises(ValueError, match="Key nonexistent not found"):
            obs_list._get_value_by_key("nonexistent") # type: ignore
    
    def test_get_hook_with_invalid_key(self):
        """Test get_hook with invalid secondary hook key."""
        obs_list = XList([1, 2, 3])
        
        with pytest.raises(ValueError, match="Key nonexistent not found"):
            obs_list._get_hook_by_key("nonexistent") # type: ignore
    
    def test_attach_to_secondary_hook(self):
        """Test attaching to secondary hooks."""
        obs_list = XList([1, 2, 3])
        
        from nexpy import XValue
        target = XValue(0)
        
        # Should be able to attach to secondary hook
        obs_list.join_by_key("length", target.value_hook, "use_caller_value")  # type: ignore
        
        # Should sync immediately
        assert target.value == 3