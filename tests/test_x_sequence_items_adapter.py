"""
Test suite for XSequenceItemsAdapter.

This module verifies synchronization between the sequence hook and per-item hooks,
ensuring the adapter maintains fixed-length constraints and integrates with external hooks.
"""

import pytest
from typing import Sequence

from nexpy import XSequenceItemsAdapter, FloatingHook
from nexpy.core.nexus_system.submission_error import SubmissionError


class TestXSequenceItemsAdapterInitialization:
    """Basic initialization behaviour."""

    def test_initialization_with_list(self):
        adapter: XSequenceItemsAdapter[int] = XSequenceItemsAdapter([1, 2, 3])

        assert adapter.sequence == [1, 2, 3]
        assert adapter.length == 3
        assert adapter.length_hook.value == 3
        assert adapter.item_keys == ("item_0", "item_1", "item_2")
        assert [adapter.item_value(i) for i in range(3)] == [1, 2, 3]

    def test_initialization_with_tuple_preserves_type(self):
        adapter: XSequenceItemsAdapter[int] = XSequenceItemsAdapter((10, 20))

        assert isinstance(adapter.sequence, tuple)
        assert adapter.sequence == (10, 20)
        assert adapter.length == 2
        assert [adapter.item_value(i) for i in range(2)] == [10, 20]


class TestXSequenceItemsAdapterSynchronization:
    """Synchronization between sequence and item hooks."""

    def test_change_item_updates_sequence(self):
        adapter: XSequenceItemsAdapter[int] = XSequenceItemsAdapter([0, 1, 2])

        adapter.change_item(1, 99)

        assert adapter.sequence == [0, 99, 2]
        assert adapter.item_value(0) == 0
        assert adapter.item_value(1) == 99
        assert adapter.item_value(2) == 2

    def test_change_sequence_updates_items(self):
        adapter: XSequenceItemsAdapter[int] = XSequenceItemsAdapter([5, 6, 7])

        adapter.change_sequence([10, 20, 30])

        assert adapter.sequence == [10, 20, 30]
        assert [adapter.item_value(i) for i in range(3)] == [10, 20, 30]

    def test_sequence_provided_via_hook_stays_in_sync(self):
        sequence_hook: FloatingHook[Sequence[int]] = FloatingHook([1, 2, 3])
        adapter: XSequenceItemsAdapter[int] = XSequenceItemsAdapter(
            sequence_hook,
            item_hooks=[None, None, None],
        )

        sequence_hook.value = [4, 5, 6]

        assert adapter.sequence == [4, 5, 6]
        assert [adapter.item_value(i) for i in range(3)] == [4, 5, 6]

    def test_external_item_hook_stays_joined(self):
        external_item_hook: FloatingHook[int] = FloatingHook(2)
        adapter: XSequenceItemsAdapter[int] = XSequenceItemsAdapter(
            [1, 2, 3],
            item_hooks={1: external_item_hook},
        )

        external_item_hook.value = 200

        assert adapter.sequence == [1, 200, 3]
        assert adapter.item_value(1) == 200

        adapter.change_item(1, 500)

        assert external_item_hook.value == 500
        assert adapter.sequence == [1, 500, 3]


class TestXSequenceItemsAdapterValidation:
    """Validation and error handling."""

    def test_rejects_sequence_of_wrong_length(self):
        adapter: XSequenceItemsAdapter[int] = XSequenceItemsAdapter([1, 2, 3])

        with pytest.raises(SubmissionError, match="Sequence length must remain"):
            adapter.change_sequence([1, 2])

    def test_length_hook_is_read_only(self):
        adapter: XSequenceItemsAdapter[int] = XSequenceItemsAdapter([7, 8, 9])

        # The length hook is read-only and computed from the sequence.
        # Trying to submit a length value different from the actual sequence length
        # results in a nexus conflict (the computed length is 3, but we're trying to submit 5).
        success, message = adapter._submit_values(  # type: ignore[attr-defined]
            {
                "sequence": [7, 8, 9],  # Length 3 sequence (correct)
                "item_0": 7,
                "item_1": 8,
                "item_2": 9,
                "length": 5,  # Trying to set length to 5 (incorrect)
            }
        )

        assert not success
        assert "Nexus conflict" in message  # The computed length (3) conflicts with submitted length (5)

