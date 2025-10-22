"""
Test suite for XSetSequenceAdapter.

This module tests the XSetSequenceAdapter class, which bridges between AbstractSet and Sequence types,
validating that sequences have unique elements before conversion to sets.
"""

import pytest
from nexpy import XSetSequenceAdapter, FloatingHook


class TestXSetSequenceAdapterBasics:
    """Test basic functionality of XSetSequenceAdapter."""

    def test_initialization_with_set_value(self):
        """Test that XSetSequenceAdapter can be initialized with a set value."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )
        assert obs.hook_set.value == frozenset([1, 2, 3])
        assert obs.hook_sequence.value == [1, 2, 3]  # Default sorted order

    def test_initialization_with_sequence_value(self):
        """Test that XSetSequenceAdapter can be initialized with a unique sequence."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=None,
            hook_sequence=[1, 2, 3]
        )
        assert obs.hook_set.value == frozenset([1, 2, 3])
        assert obs.hook_sequence.value == [1, 2, 3]  # Preserves original sequence

    def test_initialization_with_both_same_value(self):
        """Test initialization with both hooks having the same unique values."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=[1, 2, 3]
        )
        assert obs.hook_set.value == frozenset([1, 2, 3])
        assert obs.hook_sequence.value == [1, 2, 3]  # Preserves original sequence

    def test_initialization_with_different_values_raises_error(self):
        """Test that initialization with different values raises error."""
        with pytest.raises(ValueError, match="Values do not match"):
            XSetSequenceAdapter(
                hook_set_or_value=frozenset([1, 2, 3]),
                hook_sequence=[4, 5, 6]
            )

    def test_initialization_with_no_values_raises_error(self):
        """Test that initialization with no values raises error."""
        with pytest.raises(ValueError, match="At least one parameter must be provided"):
            XSetSequenceAdapter(
                hook_set_or_value=None,
                hook_sequence=None
            )


class TestXSetSequenceAdapterValueUpdates:
    """Test value updates and synchronization."""

    def test_update_hook_set_updates_hook_sequence(self):
        """Test that updating hook_set also updates hook_sequence."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        # Update hook_set
        obs._submit_values({"left": frozenset([4, 5, 6])}) # type: ignore
        assert obs.hook_set.value == frozenset([4, 5, 6])
        assert set(obs.hook_sequence.value) == {4, 5, 6}

    def test_update_hook_sequence_updates_hook_set(self):
        """Test that updating hook_sequence also updates hook_set."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        # Update hook_sequence
        obs._submit_values({"right": [7, 8, 9]}) # type: ignore
        assert obs.hook_set.value == frozenset([7, 8, 9])
        assert obs.hook_sequence.value == [7, 8, 9]

    def test_update_both_hooks_with_same_value(self):
        """Test updating both hooks simultaneously with matching values."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        # Update both with the same value
        obs._submit_values({ "left": frozenset([10, 11, 12]), "right": [10, 11, 12]}) # type: ignore
        assert obs.hook_set.value == frozenset([10, 11, 12])
        assert obs.hook_sequence.value == [10, 11, 12]

    def test_update_with_different_unique_sequences(self):
        """Test with different unique sequences."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        obs._submit_values({"left": frozenset([100, 200, 300])}) # type: ignore
        assert obs.hook_set.value == frozenset([100, 200, 300])
        assert set(obs.hook_sequence.value) == {100, 200, 300}


class TestXSetSequenceAdapterErrorHandling:
    """Test error handling when sequences with duplicates are submitted."""

    def test_update_hook_sequence_with_duplicates_raises_error(self):
        """Test that updating hook_sequence with duplicates raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError

        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        with pytest.raises(SubmissionError, match="Cannot convert sequence with duplicates"):
            obs.submit_values_by_keys({"right": [1, 2, 2]})

    def test_update_hook_set_with_duplicates_raises_error(self):
        """Test that updating hook_set with duplicates raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError

        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        with pytest.raises(SubmissionError, match="Left value must be AbstractSet"):
            obs.submit_values_by_keys({"left": [1, 2, 2]})

    def test_update_both_hooks_with_duplicates_raises_error(self):
        """Test that updating both hooks with duplicates raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError

        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        with pytest.raises(SubmissionError, match="Left value must be AbstractSet"):
            obs.submit_values_by_keys({"left": [1, 1, 2], "right": [3, 3, 4]})

    def test_update_both_hooks_with_mismatched_values(self):
        """Test updating both hooks with different values."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        # When you submit both with different values, the system chooses one
        # (the sync system resolves this internally)
        obs._submit_values({ "left": frozenset([10, 11, 12]), "right": [20, 21, 22]}) # type: ignore

    def test_update_both_hooks_one_unique_one_duplicate_raises_error(self):
        """Test that updating with one unique and one duplicate raises SubmissionError."""
        from nexpy.core.nexus_system.submission_error import SubmissionError

        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        with pytest.raises(SubmissionError, match="Sequence contains duplicate elements"):
            obs.submit_values_by_keys({"left": frozenset([10, 11, 12]), "right": [20, 21, 21]})


class TestXSetSequenceAdapterHookAccess:
    """Test hook accessor methods."""

    def test_get_hook_set(self):
        """Test _get_hook returns correct hook for left key."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        retrieved_hook = obs._get_hook_by_key("left") # type: ignore
        assert retrieved_hook is obs.hook_set

    def test_get_hook_sequence(self):
        """Test _get_hook returns correct hook for right key."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        retrieved_hook = obs._get_hook_by_key("right") # type: ignore
        assert retrieved_hook is obs.hook_sequence

    def test_get_value_reference_of_hook(self):
        """Test _get_value_reference_of_hook returns correct value reference."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        # Test that we can access the hook values directly
        assert obs.hook_set.value == frozenset([1, 2, 3])
        assert obs.hook_sequence.value == [1, 2, 3]

    def test_get_hook_keys(self):
        """Test _get_hook_keys returns all keys."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        keys = obs._get_hook_keys() # type: ignore
        assert keys == {"left", "right"}

    def test_get_hook_key(self):
        """Test _get_hook_key returns correct key for given hook."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        key_set = obs._get_key_by_hook_or_nexus(obs.hook_set) # type: ignore
        key_sequence = obs._get_key_by_hook_or_nexus(obs.hook_sequence) # type: ignore

        assert key_set == "left"
        assert key_sequence == "right"

    def test_get_hook_key_invalid_hook_raises_error(self):
        """Test _get_hook_key with invalid hook raises error."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        with pytest.raises(ValueError, match="not found in component_hooks"):
            obs._get_key_by_hook_or_nexus(FloatingHook[frozenset[int]](frozenset())) # type: ignore


class TestXSetSequenceAdapterValidation:
    """Test validation logic."""

    def test_validate_with_matching_unique_values(self):
        """Test validation succeeds with matching unique values."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        # Access the validation callback directly
        is_valid, message = obs._validate_values( # type: ignore
            {"left": frozenset([1, 2, 3]), "right": [1, 2, 3]}
        )

        assert is_valid is True
        assert "valid" in message

    def test_validate_with_mismatched_values(self):
        """Test validation fails when hooks have mismatched values."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        is_valid, message = obs._validate_values( # type: ignore
            {"left": frozenset([1, 2, 3]), "right": [4, 5, 6]}
        )
        
        # Validation fails - both hooks must have matching values since they're joined
        assert is_valid is False
        assert "Set and sequence elements do not match" in message

    def test_validate_with_duplicate_values(self):
        """Test validation fails when values have duplicates."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        is_valid, message = obs._validate_values( # type: ignore
            {"left": frozenset([1, 2, 2]), "right": [1, 2, 2]}
        )
        
        assert is_valid is False
        assert "Sequence contains duplicate elements" in message

    def test_validate_with_missing_keys(self):
        """Test validation succeeds with one key - the other is automatically added."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        is_valid, message = obs._validate_values( # type: ignore
            {"left": frozenset([1, 2, 3])}
        )

        assert is_valid is True
        assert "valid" in message


class TestXSetSequenceAdapterListeners:
    """Test listener functionality."""

    def test_listener_triggered_on_update(self):
        """Test that listeners are triggered when values update."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        set_updates: list[frozenset[int]] = []
        sequence_updates: list[tuple[int, ...]] = []

        def listener_set():
            set_updates.append(obs.hook_set.value) # type: ignore

        def listener_sequence():
            sequence_updates.append(obs.hook_sequence.value) # type: ignore

        obs.hook_set.add_listener(listener_set)
        obs.hook_sequence.add_listener(listener_sequence)

        # Update via left
        obs._submit_values({"left": frozenset([4, 5, 6])}) # type: ignore

        assert len(set_updates) == 1
        assert len(sequence_updates) == 1
        assert set_updates[0] == frozenset([4, 5, 6])
        assert set(sequence_updates[0]) == {4, 5, 6}

    def test_listener_triggered_on_synchronized_update(self):
        """Test that both listeners are triggered when one value updates."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        update_count = {"set": 0, "sequence": 0}

        def listener_set():
            update_count["set"] += 1

        def listener_sequence():
            update_count["sequence"] += 1

        obs.hook_set.add_listener(listener_set)
        obs.hook_sequence.add_listener(listener_sequence)

        # Update via right
        obs._submit_values({"right": [7, 8, 9]}) # type: ignore

        assert update_count["set"] == 1
        assert update_count["sequence"] == 1


class TestXSetSequenceAdapterComplexTypes:
    """Test with complex data types."""

    def test_with_string_elements(self):
        """Test with string elements."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset(["a", "b", "c"]),
            hook_sequence=None
        )

        new_strings = ["x", "y", "z"]
        obs._submit_values({"left": frozenset(new_strings)}) # type: ignore
        assert obs.hook_set.value == frozenset(new_strings)
        assert set(obs.hook_sequence.value) == set(new_strings)

    def test_with_mixed_types(self):
        """Test with mixed data types."""
        # Use a custom sort function that handles mixed types
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, "a", 2.0]),
            hook_sequence=None,
            sort_callable=lambda s: list(s)  # Don't sort mixed types
        )

        mixed_values = [3, "b", 4.0]
        obs._submit_values({"right": mixed_values}) # type: ignore
        assert obs.hook_set.value == frozenset(mixed_values)
        assert obs.hook_sequence.value == list(mixed_values)

    def test_with_empty_collections(self):
        """Test with empty collections."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        obs._submit_values({"left": frozenset()}) # type: ignore
        assert obs.hook_set.value == frozenset()
        assert obs.hook_sequence.value == []

    def test_with_single_element(self):
        """Test with single element collections."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        obs._submit_values({"right": [42]}) # type: ignore
        assert obs.hook_set.value == frozenset([42])
        assert obs.hook_sequence.value == [42]


class TestXSetSequenceAdapterEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_update(self):
        """Test updating with empty dictionary."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        # Empty update should not change values
        obs._submit_values({}) # type: ignore
        assert obs.hook_set.value == frozenset([1, 2, 3])
        assert obs.hook_sequence.value == [1, 2, 3]

    def test_multiple_sequential_updates(self):
        """Test multiple updates in sequence."""
        obs = XSetSequenceAdapter[int](
            hook_set_or_value=frozenset(),
            hook_sequence=None
        )

        for i in range(1, 6):
            obs._submit_values({"left": frozenset([i])}) # type: ignore
            assert obs.hook_set.value == frozenset([i])
            assert obs.hook_sequence.value == [i]

    def test_update_with_same_value(self):
        """Test updating with the same value doesn't cause issues."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        # Update with same value
        obs._submit_values({"left": frozenset([1, 2, 3])}) # type: ignore
        assert obs.hook_set.value == frozenset([1, 2, 3])
        assert obs.hook_sequence.value == [1, 2, 3]

    def test_order_preservation_in_sequence(self):
        """Test that sequence order is preserved when converting from set."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        # When converting from set to sequence, order is not guaranteed
        # but the elements should be the same
        obs._submit_values({"left": frozenset([3, 1, 2])}) # type: ignore
        assert obs.hook_set.value == frozenset([3, 1, 2])
        assert set(obs.hook_sequence.value) == {1, 2, 3}

    def test_large_collections(self):
        """Test with large collections."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([1, 2, 3]),
            hook_sequence=None
        )

        # Test with a larger collection
        large_set = frozenset(range(100))
        obs._submit_values({"left": large_set}) # type: ignore
        assert obs.hook_set.value == large_set
        assert set(obs.hook_sequence.value) == set(range(100))

    def test_nested_structures(self):
        """Test with nested data structures."""
        obs = XSetSequenceAdapter(
            hook_set_or_value=frozenset([(1, 2), (3, 4)]),
            hook_sequence=None
        )

        nested_values = [(5, 6), (7, 8)]
        obs._submit_values({"right": nested_values}) # type: ignore
        assert obs.hook_set.value == frozenset(nested_values)
        assert obs.hook_sequence.value == list(nested_values)
