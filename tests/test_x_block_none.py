"""
Tests for XBlockNone.

This module tests the XBlockNone class, which maintains two synchronized hooks
(one Optional[T], one T) and raises errors when None values are encountered.
"""

import pytest

from nexpy import XBlockNone, FloatingHook

class TestXBlockNoneBasics:
    """Test basic functionality of XBlockNone."""

    def test_initialization_with_value(self):
        """Test that XBlockNone can be initialized with a value."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        assert obs.hook_with_None.value == 42
        assert obs.hook_without_None.value == 42

    def test_initialization_with_hook_with_none(self):
        """Test initialization with hook_with_None only."""
        hook_with_none = FloatingHook[int | None](42)
        
        obs = XBlockNone[int](
            hook_without_None_or_value=None,
            hook_with_None=hook_with_none
        )
        
        # The observable creates its own internal hooks and connects to the external one
        assert obs.hook_with_None.value == 42
        assert obs.hook_without_None.value == 42

    def test_initialization_with_both_same_value(self):
        """Test initialization with both value and hook having the same value."""
        hook_with_none = FloatingHook[int | None](42)
        
        obs = XBlockNone(
            hook_without_None_or_value=42,
            hook_with_None=hook_with_none
        )
        
        assert obs.hook_with_None.value == 42
        assert obs.hook_without_None.value == 42

    def test_initialization_with_different_values_raises_error(self):
        """Test that initialization with different values raises error."""
        hook_with_none = FloatingHook[int | None](42)
        
        with pytest.raises(ValueError, match="Values do not match"):
            XBlockNone(
                hook_without_None_or_value=100,
                hook_with_None=hook_with_none
            )

    def test_initialization_with_no_values_raises_error(self):
        """Test that initialization with no values raises error."""
        with pytest.raises(ValueError, match="Something non-none must be given"):
            XBlockNone(
                hook_without_None_or_value=None,
                hook_with_None=None
            )


class TestXBlockNoneValueUpdates:
    """Test value updates and synchronization."""

    def test_update_hook_without_none_updates_hook_with_none(self):
        """Test that updating hook_without_None also updates hook_with_None."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        # Update hook_without_none
        obs._submit_values({"value_without_none": 100}) # type: ignore
        
        assert obs.hook_without_None.value == 100
        assert obs.hook_with_None.value == 100

    def test_update_hook_with_none_updates_hook_without_none(self):
        """Test that updating hook_with_None also updates hook_without_None."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        # Update hook_with_none
        obs._submit_values({"value_with_none": 200}) # type: ignore
        
        assert obs.hook_with_None.value == 200
        assert obs.hook_without_None.value == 200

    def test_update_both_hooks_with_same_value(self):
        """Test updating both hooks simultaneously with matching values."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        # Update both with the same value
        obs._submit_values({ "value_without_none": 150, "value_with_none": 150}) # type: ignore
        assert obs.hook_with_None.value == 150

    def test_update_string_values(self):
        """Test with string type instead of int."""
        obs = XBlockNone[str](
            hook_without_None_or_value="hello",
            hook_with_None=None
        )
        
        obs._submit_values({"value_without_none": "world"}) # type: ignore
        
        assert obs.hook_without_None.value == "world"
        assert obs.hook_with_None.value == "world"


class TestXBlockNoneErrorHandling:
    """Test error handling when None values are submitted."""

    def test_update_hook_without_none_with_none_raises_error(self):
        """Test that updating hook_without_None with None raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError
        
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        with pytest.raises(SubmissionError, match="One or both of the values"):
            obs.submit_values_by_keys({"value_without_none": None}) # type: ignore

    def test_update_hook_with_none_with_none_raises_error(self):
        """Test that updating hook_with_None with None raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError
        
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        with pytest.raises(SubmissionError, match="One or both of the values"):
            obs.submit_values_by_keys({"value_with_none": None}) # type: ignore 

    def test_update_both_hooks_with_none_raises_error(self):
        """Test that updating both hooks with None raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError
        
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        with pytest.raises(SubmissionError, match="One or both of the values"):
            obs.submit_values_by_keys({"value_without_none": None,"value_with_none": None}) # type: ignore

    def test_update_both_hooks_with_mismatched_values(self):
        """Test updating both hooks with different values."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        # When you submit both with different values, the system chooses one
        # (the sync system resolves this internally)
        obs._submit_values({ "value_without_none": 100, "value_with_none": 200}) # type: ignore

    def test_update_both_hooks_one_none_one_value_raises_error(self):
        """Test that updating with one None and one value raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError
        
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        with pytest.raises(SubmissionError, match="One or both of the values"):
            obs.submit_values_by_keys({"value_without_none": 100, "value_with_none": None}) # type: ignore


class TestXBlockNoneHookAccess:
    """Test hook accessor methods."""

    def test_get_hook_value_without_none(self):
        """Test _get_hook returns correct hook for value_without_none key."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        retrieved_hook = obs._get_hook_by_key("value_without_none") # type: ignore
        assert retrieved_hook is obs.hook_without_None

    def test_get_hook_value_with_none(self):
        """Test _get_hook returns correct hook for value_with_none key."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        retrieved_hook = obs._get_hook_by_key("value_with_none") # type: ignore
        assert retrieved_hook is obs.hook_with_None

    def test_get_value_reference_of_hook(self):
        """Test _get_value_reference_of_hook returns correct values."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        value_without_none = obs._get_value_by_key("value_without_none") # type: ignore
        value_with_none = obs._get_value_by_key("value_with_none") # type: ignore 
        
        assert value_without_none == 42
        assert value_with_none == 42

    def test_get_hook_keys(self):
        """Test _get_hook_keys returns all keys."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        keys = obs._get_hook_keys() # type: ignore
        assert keys == {"value_without_none", "value_with_none"}

    def test_get_hook_key(self):
        """Test _get_hook_key returns correct key for given hook."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        key_without = obs._get_key_by_hook_or_nexus(obs.hook_without_None) # type: ignore
        key_with = obs._get_key_by_hook_or_nexus(obs.hook_with_None) # type: ignore
        
        assert key_without == "value_without_none"
        assert key_with == "value_with_none"

    def test_get_hook_key_invalid_hook_raises_error(self):
        """Test _get_hook_key raises error for unknown hook."""
        unknown_hook = FloatingHook[int](99)
        
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        with pytest.raises(ValueError, match="not found in"):
            obs._get_key_by_hook_or_nexus(unknown_hook) # type: ignore


class TestXBlockNoneValidation:
    """Test validation functionality."""

    def test_validate_with_matching_non_none_values(self):
        """Test validation succeeds with matching non-None values."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        # Access the validation callback directly
        is_valid, message = obs._validate_values( # type: ignore
            {"value_without_none": 42, "value_with_none": 42} # type: ignore
        )
        
        assert is_valid is True
        assert message == "Values are valid"

    def test_validate_with_mismatched_values(self):
        """Test validation fails when hooks have mismatched non-None values."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        is_valid, message = obs._validate_values( # type: ignore
            {"value_without_none": 42, "value_with_none": 100} # type: ignore
        )
        
        # Validation fails - both hooks must have matching values since they're joined
        assert is_valid is False
        assert "Values do not match" in message

    def test_validate_with_none_values(self):
        """Test validation fails when values are None."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        is_valid, message = obs._validate_values( # type: ignore
            {"value_without_none": None, "value_with_none": None} # type: ignore
        )
        
        assert is_valid is False
        assert "One or both of the values" in message

    def test_validate_with_missing_keys(self):
        """Test validation succeeds with one key - the other is automatically added."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        is_valid, message = obs._validate_values( # type: ignore
            {"value_without_none": 42} # type: ignore
        )
        
        # Should succeed - the system automatically adds the other value
        assert is_valid is True


class TestXBlockNoneListeners:
    """Test that listeners work correctly with XBlockNone."""

    def test_listener_triggered_on_update(self):
        """Test that listeners are triggered when values update."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        without_none_updates: list[int] = []
        with_none_updates: list[int] = []
        
        def listener_without():
            without_none_updates.append(obs.hook_without_None.value)
        
        def listener_with():
            with_none_updates.append(obs.hook_with_None.value) # type: ignore
        
        obs.hook_without_None.add_listener(listener_without)
        obs.hook_with_None.add_listener(listener_with)
        
        # Update via value_without_none
        obs._submit_values({"value_without_none": 100}) # type: ignore
        
        assert without_none_updates == [100]
        assert with_none_updates == [100]

    def test_listener_triggered_on_synchronized_update(self):
        """Test that both listeners are triggered when one value updates."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        update_count = {"with": 0, "without": 0}
        
        def listener_without():
            update_count["without"] += 1
        
        def listener_with():
            update_count["with"] += 1
        
        obs.hook_without_None.add_listener(listener_without)
        obs.hook_with_None.add_listener(listener_with)
        
        # Update via value_with_none
        obs._submit_values({"value_with_none": 200}) # type: ignore
        
        # Both should be triggered because the observable syncs them
        assert update_count["with"] == 1
        assert update_count["without"] == 1


class TestXBlockNoneComplexTypes:
    """Test XBlockNone with complex types."""

    def test_with_list_type(self):
        """Test with list values."""
        obs = XBlockNone[list[int]](
            hook_without_None_or_value=[1, 2, 3],
            hook_with_None=None
        )
        
        new_list = [4, 5, 6]
        obs._submit_values({"value_without_none": new_list}) # type: ignore
        
        # Values are stored as-is (no immutability conversion)
        assert obs.hook_without_None.value == [4, 5, 6]
        assert obs.hook_with_None.value == [4, 5, 6]

    def test_with_dict_type(self):
        """Test with dict values."""
        initial_dict = {"a": 1, "b": 2}
        obs = XBlockNone[dict[str, int]](
            hook_without_None_or_value=initial_dict,
            hook_with_None=None
        )
        
        new_dict = {"c": 3, "d": 4}
        obs._submit_values({"value_with_none": new_dict}) # type: ignore
        
        # Values are stored as-is (no immutability conversion)
        assert obs.hook_without_None.value == {"c": 3, "d": 4}
        assert obs.hook_with_None.value == {"c": 3, "d": 4}

class TestXBlockNoneEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_update(self):
        """Test submitting empty update dict."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        # Empty update should do nothing
        obs._submit_values({}) # type: ignore
        
        assert obs.hook_without_None.value == 42
        assert obs.hook_with_None.value == 42

    def test_multiple_sequential_updates(self):
        """Test multiple updates in sequence."""
        obs = XBlockNone[int](
            hook_without_None_or_value=0,
            hook_with_None=None
        )
        
        for i in range(1, 6):
            obs._submit_values({"value_without_none": i}) # type: ignore
            assert obs.hook_without_None.value == i
            assert obs.hook_with_None.value == i

    def test_update_with_same_value(self):
        """Test updating with the same value doesn't cause issues."""
        obs = XBlockNone[int](
            hook_without_None_or_value=42,
            hook_with_None=None
        )
        
        # Update with same value
        obs._submit_values({"value_without_none": 42}) # type: ignore
        
        assert obs.hook_without_None.value == 42
        assert obs.hook_with_None.value == 42

