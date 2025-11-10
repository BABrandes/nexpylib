"""
Tests for XOptionalPlaceholderAdapter.

This module tests the XOptionalPlaceholderAdapter class, which bridges between
Optional[T] (using None) and T (using a placeholder value), perfect for GUI widgets
that cannot handle None values.
"""

import pytest

from nexpy import XOptionalPlaceholderAdapter, FloatingHook


class TestXOptionalPlaceholderAdapterBasics:
    """Test basic functionality of XOptionalPlaceholderAdapter."""

    def test_initialization_with_value(self):
        """Test that XOptionalPlaceholderAdapter can be initialized with a value."""
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            placeholder_value=-1
        )
        
        assert adapter.hook_optional.value == 42
        assert adapter.hook_placeholder.value == 42
        assert adapter.placeholder_value == -1

    def test_initialization_with_none_via_external_hook(self):
        """Test initialization with None value via external hook."""
        external_hook = FloatingHook[int | None](None)
        
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=external_hook,
            placeholder_value=-1
        )
        
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == -1

    def test_initialization_with_external_optional_hook(self):
        """Test initialization with external optional hook."""
        external_hook = FloatingHook[int | None](42)
        
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=external_hook,
            placeholder_value=-1
        )
        
        assert adapter.hook_optional.value == 42
        assert adapter.hook_placeholder.value == 42

    def test_initialization_with_external_placeholder_hook(self):
        """Test initialization with external placeholder hook containing a value."""
        external_hook = FloatingHook[int](42)
        
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=None,
            hook_placeholder=external_hook,
            placeholder_value=-1
        )
        
        assert adapter.hook_optional.value == 42
        assert adapter.hook_placeholder.value == 42

    def test_initialization_with_external_placeholder_hook_at_placeholder(self):
        """Test initialization with external placeholder hook at placeholder value."""
        external_hook = FloatingHook[int](-1)
        
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=None,
            hook_placeholder=external_hook,
            placeholder_value=-1
        )
        
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == -1

    def test_initialization_with_both_hooks_compatible(self):
        """Test initialization with both hooks having compatible values."""
        external_optional = FloatingHook[int | None](42)
        external_placeholder = FloatingHook[int](42)
        
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=external_optional,
            hook_placeholder=external_placeholder,
            placeholder_value=-1
        )
        
        assert adapter.hook_optional.value == 42
        assert adapter.hook_placeholder.value == 42

    def test_initialization_with_both_hooks_none_and_placeholder(self):
        """Test initialization with optional=None and placeholder=placeholder_value."""
        external_optional = FloatingHook[int | None](None)
        external_placeholder = FloatingHook[int](-1)
        
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=external_optional,
            hook_placeholder=external_placeholder,
            placeholder_value=-1
        )
        
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == -1

    def test_initialization_with_incompatible_hooks_raises_error(self):
        """Test that initialization with incompatible hooks raises error."""
        external_optional = FloatingHook[int | None](42)
        external_placeholder = FloatingHook[int](100)
        
        with pytest.raises(ValueError, match="Values do not match"):
            XOptionalPlaceholderAdapter[int](
                hook_optional=external_optional,
                hook_placeholder=external_placeholder,
                placeholder_value=-1
            )

    def test_initialization_with_optional_none_but_placeholder_not_placeholder_raises(self):
        """Test that optional=None but placeholder!=placeholder_value raises error."""
        external_optional = FloatingHook[int | None](None)
        external_placeholder = FloatingHook[int](42)
        
        with pytest.raises(ValueError, match="placeholder must equal placeholder_value"):
            XOptionalPlaceholderAdapter[int](
                hook_optional=external_optional,
                hook_placeholder=external_placeholder,
                placeholder_value=-1
            )

    def test_initialization_with_no_parameters_raises_error(self):
        """Test that initialization with no parameters raises error."""
        with pytest.raises(ValueError, match="At least one parameter must be provided"):
            XOptionalPlaceholderAdapter[int](
                hook_optional=None,
                hook_placeholder=None,
                placeholder_value=-1
            )

    def test_initialization_with_placeholder_value_on_optional_side_raises(self):
        """Test that initializing optional side with placeholder value raises error."""
        with pytest.raises(ValueError, match="Cannot initialize optional side with placeholder value"):
            XOptionalPlaceholderAdapter[int](
                hook_optional=-1,  # This is the placeholder value!
                placeholder_value=-1
            )


class TestXOptionalPlaceholderAdapterValueUpdates:
    """Test value updates and synchronization."""

    def test_update_optional_to_none_converts_to_placeholder(self):
        """Test that setting optional to None converts placeholder to placeholder_value."""
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            placeholder_value=-1
        )
        
        # Update to None
        adapter._submit_values({"left": None})  # type: ignore
        
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == -1

    def test_update_optional_to_value_passes_through(self):
        """Test that setting optional to a value passes through to placeholder."""
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            placeholder_value=-1
        )
        
        # Update to different value
        adapter._submit_values({"left": 100})  # type: ignore
        
        assert adapter.hook_optional.value == 100
        assert adapter.hook_placeholder.value == 100

    def test_update_placeholder_to_placeholder_value_converts_to_none(self):
        """Test that setting placeholder to placeholder_value converts optional to None."""
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            placeholder_value=-1
        )
        
        # Update to placeholder value
        adapter._submit_values({"right": -1})  # type: ignore
        
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == -1

    def test_update_placeholder_to_value_passes_through(self):
        """Test that setting placeholder to a value passes through to optional."""
        external_hook = FloatingHook[int | None](None)
        
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=external_hook,
            placeholder_value=-1
        )
        
        # Update to a real value
        adapter._submit_values({"right": 100})  # type: ignore
        
        assert adapter.hook_optional.value == 100
        assert adapter.hook_placeholder.value == 100

    def test_bidirectional_sync_none_to_placeholder(self):
        """Test bidirectional synchronization: None to placeholder and back."""
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            placeholder_value=-1
        )
        
        # Set to None
        adapter._submit_values({"left": None})  # type: ignore
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == -1
        
        # Set back from placeholder side
        adapter._submit_values({"right": 100})  # type: ignore
        assert adapter.hook_optional.value == 100
        assert adapter.hook_placeholder.value == 100
        
        # Set to placeholder from placeholder side
        adapter._submit_values({"right": -1})  # type: ignore
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == -1


class TestXOptionalPlaceholderAdapterValidation:
    """Test validation logic."""

    def test_submitting_placeholder_to_optional_side_fails(self):
        """Test that submitting the placeholder value to optional side is rejected."""
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            placeholder_value=-1
        )
        
        # Try to submit the placeholder value to optional side
        success, message = adapter._submit_values({"left": -1})  # type: ignore
        
        assert success is False
        assert "placeholder value" in message.lower()
        assert "ambiguous" in message.lower()

    def test_placeholder_side_accepts_any_value(self):
        """Test that placeholder side accepts any value including placeholder."""
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            placeholder_value=-1
        )
        
        # Placeholder side should accept placeholder value
        success, message = adapter._submit_values({"right": -1})  # type: ignore
        assert success is True
        
        # And any other value
        success, message = adapter._submit_values({"right": 100})  # type: ignore
        assert success is True


class TestXOptionalPlaceholderAdapterWithExternalHooks:
    """Test integration with external hooks."""

    def test_external_optional_hook_synchronization(self):
        """Test that external optional hook stays synchronized."""
        external_hook = FloatingHook[int | None](42)
        
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=external_hook,
            placeholder_value=-1
        )
        
        # Change through adapter
        adapter._submit_values({"right": 100})  # type: ignore
        assert external_hook.value == 100
        
        # Change through external hook
        external_hook.value = None
        assert adapter.hook_placeholder.value == -1

    def test_external_placeholder_hook_synchronization(self):
        """Test that external placeholder hook stays synchronized."""
        external_hook = FloatingHook[int](42)
        
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=None,
            hook_placeholder=external_hook,
            placeholder_value=-1
        )
        
        # Change through adapter
        adapter._submit_values({"left": None})  # type: ignore
        assert external_hook.value == -1
        
        # Change through external hook
        external_hook.value = 100
        assert adapter.hook_optional.value == 100


class TestXOptionalPlaceholderAdapterDifferentTypes:
    """Test adapter with different data types."""

    def test_with_string_type(self):
        """Test adapter with string type."""
        adapter = XOptionalPlaceholderAdapter[str](
            hook_optional="Hello",
            placeholder_value="<empty>"
        )
        
        assert adapter.hook_optional.value == "Hello"
        assert adapter.hook_placeholder.value == "Hello"
        
        adapter._submit_values({"left": None})  # type: ignore
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == "<empty>"

    def test_with_float_type(self):
        """Test adapter with float type."""
        adapter = XOptionalPlaceholderAdapter[float](
            hook_optional=3.14,
            placeholder_value=float('nan')
        )
        
        assert adapter.hook_optional.value == 3.14
        assert adapter.hook_placeholder.value == 3.14
        
        adapter._submit_values({"left": None})  # type: ignore
        assert adapter.hook_optional.value is None
        # Note: NaN != NaN, so we check differently
        import math
        assert math.isnan(adapter.hook_placeholder.value)

    def test_with_list_type(self):
        """Test adapter with list type."""
        adapter = XOptionalPlaceholderAdapter[list[int]](
            hook_optional=[1, 2, 3],
            placeholder_value=[]
        )
        
        assert adapter.hook_optional.value == [1, 2, 3]
        assert adapter.hook_placeholder.value == [1, 2, 3]
        
        adapter._submit_values({"left": None})  # type: ignore
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == []


class TestXOptionalPlaceholderAdapterGUIUseCases:
    """Test real-world GUI use cases."""

    def test_dropdown_widget_placeholder(self):
        """Test typical dropdown widget use case with placeholder text."""
        # Widget that can't handle None, needs "<Select an option>" placeholder
        # Initialize with None via external hook
        external_optional = FloatingHook[str | None](None)
        
        adapter = XOptionalPlaceholderAdapter[str](
            hook_optional=external_optional,
            placeholder_value="<Select an option>"
        )
        
        # Widget displays placeholder
        assert adapter.hook_placeholder.value == "<Select an option>"
        
        # User makes selection
        adapter._submit_values({"right": "Option 1"})  # type: ignore
        assert adapter.hook_optional.value == "Option 1"
        
        # User clears selection (widget shows placeholder again)
        adapter._submit_values({"right": "<Select an option>"})  # type: ignore
        assert adapter.hook_optional.value is None

    def test_numeric_input_with_sentinel_value(self):
        """Test numeric input widget that uses -1 as 'no value' sentinel."""
        # Widget that uses -1 to represent "no value"
        external_optional = FloatingHook[int | None](None)
        
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=external_optional,
            placeholder_value=-1
        )
        
        # Widget shows -1
        assert adapter.hook_placeholder.value == -1
        
        # User enters value
        adapter._submit_values({"right": 42})  # type: ignore
        assert adapter.hook_optional.value == 42
        
        # Logic layer clears value
        adapter._submit_values({"left": None})  # type: ignore
        assert adapter.hook_placeholder.value == -1

    def test_color_picker_with_transparent_placeholder(self):
        """Test color picker widget with transparent/default color placeholder."""
        # Widget that uses "transparent" to represent no color selected
        adapter = XOptionalPlaceholderAdapter[str](
            hook_optional="#FF0000",
            placeholder_value="transparent"
        )
        
        assert adapter.hook_placeholder.value == "#FF0000"
        
        # User clears color
        adapter._submit_values({"right": "transparent"})  # type: ignore
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == "transparent"


class TestXOptionalPlaceholderAdapterProperties:
    """Test adapter properties and attributes."""

    def test_placeholder_value_property_readonly(self):
        """Test that placeholder_value property is accessible."""
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            placeholder_value=-1
        )
        
        assert adapter.placeholder_value == -1

    def test_hook_properties_return_correct_types(self):
        """Test that hook properties return the correct hook types."""
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            placeholder_value=-1
        )
        
        # Both should be accessible
        assert hasattr(adapter, 'hook_optional')
        assert hasattr(adapter, 'hook_placeholder')
        
        # Both should have values
        assert hasattr(adapter.hook_optional, 'value')
        assert hasattr(adapter.hook_placeholder, 'value')


class TestXOptionalPlaceholderAdapterEdgeCases:
    """Test edge cases and special scenarios."""

    def test_placeholder_same_as_valid_value_but_distinguished(self):
        """Test that adapter correctly distinguishes placeholder from actual value."""
        # Use 0 as placeholder, which could also be a valid value
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            placeholder_value=0
        )
        
        # Set to None -> should become 0 (placeholder)
        adapter._submit_values({"left": None})  # type: ignore
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == 0
        
        # Try to set optional to 0 -> should be rejected as ambiguous
        success, message = adapter._submit_values({"left": 0})  # type: ignore
        assert success is False

    def test_multiple_adapters_with_different_placeholders(self):
        """Test multiple adapters with different placeholder values."""
        adapter1 = XOptionalPlaceholderAdapter[int](
            hook_optional=10,
            placeholder_value=-1
        )
        
        adapter2 = XOptionalPlaceholderAdapter[int](
            hook_optional=20,
            placeholder_value=-999
        )
        
        adapter1._submit_values({"left": None})  # type: ignore
        adapter2._submit_values({"left": None})  # type: ignore
        
        assert adapter1.hook_placeholder.value == -1
        assert adapter2.hook_placeholder.value == -999

    def test_adapter_with_custom_equality(self):
        """Test adapter with custom object types (using default equality)."""
        class CustomObject:
            def __init__(self, value: int):
                super().__init__()
                self.value = value
            
            def __eq__(self, other: object) -> bool:
                if not isinstance(other, CustomObject):
                    return False
                return self.value == other.value
        
        placeholder = CustomObject(-1)
        
        adapter = XOptionalPlaceholderAdapter[CustomObject](
            hook_optional=CustomObject(42),
            placeholder_value=placeholder
        )
        
        assert adapter.hook_optional.value == 42
        
        # Set to None
        adapter._submit_values({"left": None})  # type: ignore
        assert adapter.hook_optional.value is None
        assert adapter.hook_placeholder.value == placeholder


class TestXOptionalPlaceholderAdapterStressTests:
    """Stress tests and performance-related tests."""

    def test_rapid_value_changes(self):
        """Test rapid switching between None and values."""
        adapter = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            placeholder_value=-1
        )
        
        # Rapidly switch between values
        for i in range(100):
            if i % 2 == 0:
                adapter._submit_values({"left": None})  # type: ignore
                assert adapter.hook_placeholder.value == -1
            else:
                adapter._submit_values({"right": i})  # type: ignore
                assert adapter.hook_optional.value == i

    def test_adapter_chain_with_placeholder(self):
        """Test chaining adapters together with shared hook."""
        # Create two adapters that share a hook - both must use same placeholder!
        shared_placeholder_hook = FloatingHook[int](42)
        
        adapter1 = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            hook_placeholder=shared_placeholder_hook,
            placeholder_value=-1
        )
        
        adapter2 = XOptionalPlaceholderAdapter[int](
            hook_optional=42,
            hook_placeholder=shared_placeholder_hook,
            placeholder_value=-1  # Same placeholder value!
        )
        
        # Change through adapter1
        adapter1._submit_values({"left": None})  # type: ignore
        assert adapter1.hook_placeholder.value == -1
        
        # adapter2 should see the change and interpret -1 as its placeholder too
        assert adapter2.hook_placeholder.value == -1
        assert adapter2.hook_optional.value is None

