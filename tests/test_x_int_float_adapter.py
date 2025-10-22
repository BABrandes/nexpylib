"""
Test suite for XIntFloatAdapter.

This module tests the XIntFloatAdapter class, which bridges between int and float types,
validating that float values are integer-valued before conversion.
"""

import pytest
from nexpy import XIntFloatAdapter, FloatingHook


class TestXIntFloatAdapterBasics:
    """Test basic functionality of XIntFloatAdapter."""

    def test_initialization_with_int_value(self):
        """Test that XIntFloatAdapter can be initialized with an int value."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )
        assert obs.hook_int.value == 42
        assert obs.hook_float.value == 42.0

    def test_initialization_with_float_value(self):
        """Test that XIntFloatAdapter can be initialized with an integer-valued float."""
        obs = XIntFloatAdapter(
            hook_int_or_value=None,
            hook_float=42.0
        )
        assert obs.hook_int.value == 42
        assert obs.hook_float.value == 42.0

    def test_initialization_with_both_same_value(self):
        """Test initialization with both hooks having the same integer value."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=42.0
        )
        assert obs.hook_int.value == 42
        assert obs.hook_float.value == 42.0

    def test_initialization_with_different_values_raises_error(self):
        """Test that initialization with different values raises error."""
        with pytest.raises(ValueError, match="Values do not match"):
            XIntFloatAdapter(
                hook_int_or_value=42,
                hook_float=43.0
            )

    def test_initialization_with_no_values_raises_error(self):
        """Test that initialization with no values raises error."""
        with pytest.raises(ValueError, match="At least one parameter must be provided"):
            XIntFloatAdapter(
                hook_int_or_value=None,
                hook_float=None
            )


class TestXIntFloatAdapterValueUpdates:
    """Test value updates and synchronization."""

    def test_update_hook_int_updates_hook_float(self):
        """Test that updating hook_int also updates hook_float."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        # Update hook_int
        obs._submit_values({"left": 100}) # type: ignore
        assert obs.hook_int.value == 100
        assert obs.hook_float.value == 100.0

    def test_update_hook_float_updates_hook_int(self):
        """Test that updating hook_float also updates hook_int."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        # Update hook_float
        obs._submit_values({"right": 200.0}) # type: ignore
        assert obs.hook_int.value == 200
        assert obs.hook_float.value == 200.0

    def test_update_both_hooks_with_same_value(self):
        """Test updating both hooks simultaneously with matching values."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        # Update both with the same value
        obs._submit_values({ "left": 150, "right": 150.0}) # type: ignore
        assert obs.hook_int.value == 150
        assert obs.hook_float.value == 150.0

    def test_update_string_values(self):
        """Test with different integer values."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        obs._submit_values({"left": 999}) # type: ignore
        assert obs.hook_int.value == 999
        assert obs.hook_float.value == 999.0


class TestXIntFloatAdapterErrorHandling:
    """Test error handling when non-integer float values are submitted."""

    def test_update_hook_float_with_non_integer_raises_error(self):
        """Test that updating hook_float with non-integer value raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError

        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        with pytest.raises(SubmissionError, match="Cannot convert non-integer float"):
            obs.submit_values_by_keys({"right": 42.5})

    def test_update_hook_int_with_non_integer_float_raises_error(self):
        """Test that updating hook_int with non-integer float raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError

        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        with pytest.raises(SubmissionError, match="Left value must be int"):
            obs.submit_values_by_keys({"left": 42.5})

    def test_update_both_hooks_with_non_integer_raises_error(self):
        """Test that updating both hooks with non-integer values raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError

        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        with pytest.raises(SubmissionError, match="Left value must be int"):
            obs.submit_values_by_keys({"left": 100.5, "right": 200.5})

    def test_update_both_hooks_with_mismatched_values(self):
        """Test updating both hooks with different values."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        # When you submit both with different values, the system chooses one
        # (the sync system resolves this internally)
        obs._submit_values({ "left": 100, "right": 200.0}) # type: ignore

    def test_update_both_hooks_one_integer_one_non_integer_raises_error(self):
        """Test that updating with one integer and one non-integer raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError

        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        with pytest.raises(SubmissionError, match="Float value must be integer-valued"):
            obs.submit_values_by_keys({"left": 100, "right": 200.5})


class TestXIntFloatAdapterHookAccess:
    """Test hook accessor methods."""

    def test_get_hook_int(self):
        """Test _get_hook returns correct hook for left key."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        retrieved_hook = obs._get_hook_by_key("left") # type: ignore
        assert retrieved_hook is obs.hook_int

    def test_get_hook_float(self):
        """Test _get_hook returns correct hook for right key."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        retrieved_hook = obs._get_hook_by_key("right") # type: ignore
        assert retrieved_hook is obs.hook_float

    def test_get_value_reference_of_hook(self):
        """Test _get_value_reference_of_hook returns correct value reference."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        # Test that we can access the hook values directly
        assert obs.hook_int.value == 42
        assert obs.hook_float.value == 42.0

    def test_get_hook_keys(self):
        """Test _get_hook_keys returns all keys."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        keys = obs._get_hook_keys() # type: ignore
        assert keys == {"left", "right"}

    def test_get_hook_key(self):
        """Test _get_hook_key returns correct key for given hook."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        key_int = obs._get_key_by_hook_or_nexus(obs.hook_int) # type: ignore
        key_float = obs._get_key_by_hook_or_nexus(obs.hook_float) # type: ignore

        assert key_int == "left"
        assert key_float == "right"

    def test_get_hook_key_invalid_hook_raises_error(self):
        """Test _get_hook_key with invalid hook raises error."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        with pytest.raises(ValueError, match="not found in component_hooks"):
            obs._get_key_by_hook_or_nexus(FloatingHook[int](42)) # type: ignore


class TestXIntFloatAdapterValidation:
    """Test validation logic."""

    def test_validate_with_matching_integer_values(self):
        """Test validation succeeds with matching integer values."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        # Access the validation callback directly
        is_valid, message = obs._validate_values( # type: ignore
            {"left": 42, "right": 42.0}
        )

        assert is_valid is True
        assert "valid" in message

    def test_validate_with_mismatched_values(self):
        """Test validation fails when hooks have mismatched values."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        is_valid, message = obs._validate_values( # type: ignore
            {"left": 42, "right": 100.0}
        )
        
        # Validation fails - both hooks must have matching values since they're joined
        assert is_valid is False
        assert "Values are inconsistent" in message

    def test_validate_with_non_integer_values(self):
        """Test validation fails when values are non-integer."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        is_valid, message = obs._validate_values( # type: ignore
            {"left": 42.5, "right": 42.5}
        )
        
        assert is_valid is False
        assert "Left value must be int" in message

    def test_validate_with_missing_keys(self):
        """Test validation succeeds with one key - the other is automatically added."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        is_valid, message = obs._validate_values( # type: ignore
            {"left": 42}
        )

        assert is_valid is True
        assert "valid" in message


class TestXIntFloatAdapterListeners:
    """Test listener functionality."""

    def test_listener_triggered_on_update(self):
        """Test that listeners are triggered when values update."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        int_updates: list[int] = []
        float_updates: list[float] = []

        def listener_int():
            int_updates.append(obs.hook_int.value)

        def listener_float():
            float_updates.append(obs.hook_float.value)

        obs.hook_int.add_listener(listener_int)
        obs.hook_float.add_listener(listener_float)

        # Update via left
        obs._submit_values({"left": 100}) # type: ignore

        assert len(int_updates) == 1
        assert len(float_updates) == 1
        assert int_updates[0] == 100
        assert float_updates[0] == 100.0

    def test_listener_triggered_on_synchronized_update(self):
        """Test that both listeners are triggered when one value updates."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        update_count = {"int": 0, "float": 0}

        def listener_int():
            update_count["int"] += 1

        def listener_float():
            update_count["float"] += 1

        obs.hook_int.add_listener(listener_int)
        obs.hook_float.add_listener(listener_float)

        # Update via right
        obs._submit_values({"right": 200.0}) # type: ignore

        assert update_count["int"] == 1
        assert update_count["float"] == 1


class TestXIntFloatAdapterComplexTypes:
    """Test with complex integer types."""

    def test_with_large_integers(self):
        """Test with large integer values."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        large_int = 2**31 - 1  # Max 32-bit signed integer
        obs._submit_values({"left": large_int}) # type: ignore
        assert obs.hook_int.value == large_int
        assert obs.hook_float.value == float(large_int)

    def test_with_negative_integers(self):
        """Test with negative integer values."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        negative_int = -1000
        obs._submit_values({"right": float(negative_int)}) # type: ignore
        assert obs.hook_int.value == negative_int
        assert obs.hook_float.value == float(negative_int)

    def test_with_zero(self):
        """Test with zero values."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        obs._submit_values({"left": 0}) # type: ignore
        assert obs.hook_int.value == 0
        assert obs.hook_float.value == 0.0


class TestXIntFloatAdapterEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_update(self):
        """Test updating with empty dictionary."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        # Empty update should not change values
        obs._submit_values({}) # type: ignore
        assert obs.hook_int.value == 42
        assert obs.hook_float.value == 42.0

    def test_multiple_sequential_updates(self):
        """Test multiple updates in sequence."""
        obs = XIntFloatAdapter(
            hook_int_or_value=0,
            hook_float=None
        )

        for i in range(1, 6):
            obs._submit_values({"left": i}) # type: ignore
            assert obs.hook_int.value == i
            assert obs.hook_float.value == float(i)

    def test_update_with_same_value(self):
        """Test updating with the same value doesn't cause issues."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        # Update with same value
        obs._submit_values({"left": 42}) # type: ignore
        assert obs.hook_int.value == 42
        assert obs.hook_float.value == 42.0

    def test_float_precision_edge_cases(self):
        """Test edge cases with float precision."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        # Test with values that might have precision issues
        test_values = [1.0, 2.0, 3.0, 100.0, 1000.0]
        
        for val in test_values:
            obs._submit_values({"right": val}) # type: ignore
            assert obs.hook_int.value == int(val)
            assert obs.hook_float.value == val

    def test_very_large_numbers(self):
        """Test with very large numbers."""
        obs = XIntFloatAdapter(
            hook_int_or_value=42,
            hook_float=None
        )

        # Test with a large but still representable integer
        large_number = 10**15
        obs._submit_values({"left": large_number}) # type: ignore
        assert obs.hook_int.value == large_number
        assert obs.hook_float.value == float(large_number)
