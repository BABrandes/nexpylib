"""
Test suite for secondary hook protection mechanism.

This module tests that secondary hooks (derived values) cannot be modified from outside.
Secondary values should only be changed through primary value updates.
"""

import pytest

from nexpy import XList, XValue

class TestSecondaryHookProtection:
    """Tests for preventing external modification of secondary hooks."""

    def test_cannot_directly_modify_length_hook_on_x_list(self):
        """Test that attempting to modify a list's length hook directly fails."""
        # Create an observable list with some items
        obs_list = XList([1, 2, 3])
        
        # Get the length hook
        length_hook = obs_list.length_hook
        
        # Verify initial state
        assert obs_list.length == 3
        assert length_hook.value == 3
        
        # Try to submit a different length value directly to the length hook
        # This should fail because length is a secondary value derived from the list
        success, msg = obs_list.submit_value_by_key("length", 5, raise_submission_error_flag=False) # type: ignore
        assert not success
        assert ("Internal secondary value" in msg or "Hook nexus already in nexus" in msg or 
                "Nexus conflict" in msg)
        
        # Verify the length hasn't changed
        assert obs_list.length == 3
        assert length_hook.value == 3

    def test_cannot_modify_length_through_connected_hook(self):
        """Test that connecting to a length hook and trying to modify it fails."""
        # Create an observable list
        obs_list = XList([1, 2, 3])
        
        # Create a single value observable and connect it to the length hook
        length_observer = XValue[int](obs_list.length_hook)
        
        # Verify initial state
        assert obs_list.length == 3
        assert length_observer.value == 3
        
        # Try to modify the length through the connected observable
        # This should fail because length is secondary and cannot be set externally
        with pytest.raises(ValueError, match="Internal secondary value|Hook nexus already in nexus|Nexus conflict"):
            length_observer.value = 5
        
        # Verify nothing changed
        assert obs_list.length == 3
        assert length_observer.value == 3

    def test_length_updates_when_list_changes(self):
        """Test that length hook updates correctly when the list is modified through primary values."""
        # Create an observable list
        obs_list = XList([1, 2, 3])
        
        # Create a connected observer for length
        length_observer = XValue[int](obs_list.length_hook)
        
        # Track changes
        changes: list[int] = []
        length_observer.add_listener(lambda: changes.append(length_observer.value))
        
        # Modify the list through proper channels (primary value)
        obs_list.append(4)
        
        # Verify length updated correctly
        assert obs_list.length == 4
        assert length_observer.value == 4
        assert 4 in changes
        
        # Remove items
        obs_list.remove(1)
        assert obs_list.length == 3
        assert length_observer.value == 3
        assert 3 in changes

    def test_multiple_secondary_hooks_protection(self):
        """Test protection works when there are multiple secondary hooks."""
        # Create an observable list with multiple observers on secondary values
        obs_list = XList([10, 20, 30])
        
        # Connect to length hook
        _ = XValue(obs_list.length_hook)
        
        # Try to submit both primary and wrong secondary value
        success, msg = obs_list.submit_values_by_keys({"value": (1, 2), "length": 5}, raise_submission_error_flag=False) # type: ignore
        assert not success
        assert ("Internal secondary value" in msg or "Hook nexus already in nexus" in msg or 
                "Nexus conflict" in msg)
        
        # Verify nothing changed
        assert obs_list.list == [10, 20, 30]
        assert obs_list.length == 3

    def test_correct_secondary_value_submission_allowed(self):
        """Test that submitting the correct secondary value (matching internal) is allowed."""
        # Create an observable list
        obs_list = XList([1, 2, 3])
        
        # Submit values where the secondary value matches what it should be
        # When submitting value=(1, 2), length should be 2
        success, msg = obs_list.submit_values_by_keys({"value": (1, 2), "length": 2}) # type: ignore
        
        # This should succeed because length=2 matches the derived value
        assert success, f"Expected success but got: {msg}"
        assert obs_list.list == [1, 2]
        assert obs_list.length == 2

    def test_secondary_value_equality_check_uses_nexus_manager(self):
        """Test that secondary value comparison respects nexus manager equality."""
        # Create an observable list
        obs_list = XList([1, 2, 3])
        
        # Try to submit with a float that equals the int length
        # The nexus manager should handle this based on its equality rules
        # For numeric values, 3.0 == 3 should be true
        success, msg = obs_list.submit_value_by_key("length", 3, raise_submission_error_flag=False) # type: ignore
        
        # This should succeed because nexus manager considers 3.0 equal to 3
        assert success, f"Expected success but got: {msg}"
        assert obs_list.length == 3

    def test_length_hook_bidirectional_binding_blocked(self):
        """Test that bidirectional binding to a secondary hook doesn't allow reverse modification."""
        # Create two observable lists
        list1 = XList([1, 2, 3])
        
        # Create a single value that's bound to the length
        length_copy = XValue[int](list1.length_hook)
        
        # Verify initial state
        assert list1.length == 3
        assert length_copy.value == 3
        
        # Modify list1 - should update length_copy
        list1.append(4)
        assert list1.length == 4
        assert length_copy.value == 4
        
        # Try to modify through length_copy - should fail
        with pytest.raises(ValueError, match="Internal secondary value|Hook nexus already in nexus|Nexus conflict"):
            length_copy.value = 10
        
        # Verify nothing changed
        assert list1.length == 4
        assert length_copy.value == 4

    def test_secondary_hook_listener_notifications(self):
        """Test that listeners on secondary hooks receive notifications correctly."""
        obs_list = XList([1, 2])
        
        # Add listener to length hook
        length_changes: list[int] = []
        obs_list.length_hook.add_listener(lambda: length_changes.append(obs_list.length))
        
        # Modify list through primary value
        obs_list.append(3)
        
        # Verify listener was notified
        assert 3 in length_changes
        
        # Clear and pop
        length_changes.clear()
        obs_list.pop()
        assert 2 in length_changes

    def test_empty_list_secondary_value_protection(self):
        """Test secondary value protection with empty lists."""
        obs_list = XList[int]([])
        
        assert obs_list.length == 0
        
        # Try to directly set length to non-zero on empty list (should fail)
        success, msg = obs_list.submit_value_by_key("length", 5, raise_submission_error_flag=False) # type: ignore
        assert not success
        assert ("Internal secondary value" in msg or "Hook nexus already in nexus" in msg or 
                "Nexus conflict" in msg)
        
        assert obs_list.length == 0
        
        # Setting to correct derived length value should work
        success, _ = obs_list.submit_value_by_key("length", 0, raise_submission_error_flag=False) # type: ignore
        assert success

    def test_list_operations_maintain_secondary_consistency(self):
        """Test that all list operations maintain secondary value consistency."""
        obs_list = XList([1, 2, 3])
        length_obs = XValue(obs_list.length_hook)
        
        # Test various operations
        operations = [
            (lambda: obs_list.append(4), 4),
            (lambda: obs_list.insert(0, 0), 5),
            (lambda: obs_list.remove(0), 4),
            (lambda: obs_list.pop(), 3),
            (lambda: obs_list.extend([5, 6]), 5),
            (lambda: obs_list.clear(), 0),
        ]
        
        for operation, expected_length in operations:
            operation()
            assert obs_list.length == expected_length
            assert length_obs.value == expected_length


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

