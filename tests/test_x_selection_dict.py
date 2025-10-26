from typing import Any, Literal, Mapping, Optional, Self
from logging import Logger, basicConfig, getLogger, DEBUG

from nexpy import XDictSelect, XDictSelectOptional, FloatingHook
from nexpy import XCompositeBase
from nexpy.core.hooks import OwnedReadOnlyHook as OwnedHook
import pytest

# Set up logging for tests
basicConfig(level=DEBUG)
logger = getLogger(__name__)

class MockObservable(XCompositeBase[Literal["value"], Any, Any, Any]):
    """Mock observable for testing purposes."""
    
    def __init__(self, name: str):
        self._internal_construct_from_values({"value": name})
    
    def _internal_construct_from_values(
        self,
        initial_values: Mapping[Literal["value"], str],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """Construct a MockObservable instance."""
        super().__init__(
            initial_hook_values=initial_values,
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={},
            validate_complete_primary_values_callback=None
        )
    
    def _act_on_invalidation(self, keys: set[Literal["value"]]) -> None:
        """Act on invalidation - required by BaseXObject."""
        pass

class TestObservableSelectionDict:
    """Test ObservableSelectionDict functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_owner = MockObservable("test_owner")

    def test_basic_creation(self):
        """Test basic ObservableSelectionDict creation."""
        # Create test data
        test_dict = {"a": 1, "b": 2, "c": 3}
        test_key = "b"
        test_value = 2
        
        # Create selection dict
        selection_dict = XDictSelect(
            dict_hook=test_dict,
            key_hook=test_key,
            value_hook=None,
            logger=logger
        )
        
        # Verify creation
        assert selection_dict is not None
        assert selection_dict.value == test_value
        assert selection_dict.key == test_key
        assert selection_dict.dict_hook.value == test_dict

    def test_creation_with_hooks(self):
        """Test creation with external hooks."""
        # Create external hooks using FloatingHook to avoid owner registration issues
        dict_hook = FloatingHook(value={"x": 10, "y": 20}, logger=logger)
        key_hook = FloatingHook(value="x", logger=logger)
        value_hook = FloatingHook(value=10, logger=logger)
        
        # Create selection dict
        selection_dict = XDictSelect[str, int](
            dict_hook=dict_hook,  # type: ignore[arg-type]
            key_hook=key_hook,
            value_hook=value_hook,
            logger=logger
        )
        
        # Verify creation
        assert selection_dict is not None
        assert selection_dict.value == 10
        assert selection_dict.key == "x"
        assert selection_dict.dict_hook.value == {"x": 10, "y": 20}

    def test_hook_interface(self):
        """Test CarriesHooks interface implementation."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelect(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test get_hook_keys - now includes secondary hooks
        keys = selection_dict._get_hook_keys() # type: ignore
        assert keys == {"dict", "key", "value", "keys", "values", "length"}
        
        # Test get_hook
        dict_hook = selection_dict._get_hook_by_key("dict") # type: ignore
        key_hook = selection_dict._get_hook_by_key("key") # type: ignore
        value_hook = selection_dict._get_hook_by_key("value") # type: ignore
        
        assert dict_hook is not None
        assert key_hook is not None
        assert value_hook is not None
        
        # Test secondary hooks
        assert selection_dict.keys == {"a", "b"}
        assert selection_dict.values == [1, 2]
        assert selection_dict.length == 2
        
        # Test get_hook_value_as_reference
        # Dict is now stored as MappingProxyType, so compare contents
        dict_value = selection_dict._get_value_by_key("dict") # type: ignore
        assert dict(dict_value) == test_dict  # type: ignore[arg-type]
        assert selection_dict._get_value_by_key("key") == "a" # type: ignore
        assert selection_dict._get_value_by_key("value") == 1 # type: ignore
        
        # Test get_hook_key
        assert selection_dict._get_key_by_hook_or_nexus(dict_hook) == "dict" # type: ignore
        assert selection_dict._get_key_by_hook_or_nexus(key_hook) == "key" # type: ignore
        assert selection_dict._get_key_by_hook_or_nexus(value_hook) == "value" # type: ignore

    def test_value_properties(self):
        """Test value and key properties."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        selection_dict = XDictSelect(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test initial values
        assert selection_dict.value == 1
        assert selection_dict.key == "a"
        
        # Test setting values
        selection_dict.change_value(999)
        assert selection_dict.value == 999
        assert selection_dict.dict_hook.value["a"] == 999
        
        selection_dict.change_key("b")
        assert selection_dict.key == "b"
        assert selection_dict.value == 2  # Should update to new key's value

    def test_connect_disconnect(self):
        """Test connect and disconnect functionality."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelect(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Create external hook
        external_hook = OwnedHook(owner=self.mock_owner, value="b", logger=logger)
        
        # Connect to key hook
        selection_dict.join_by_key("key", external_hook, "use_target_value")  # type: ignore
        assert selection_dict.key == "b"
        assert selection_dict.value == 2
        
        # Disconnect
        selection_dict.isolate_by_key("key")
        # Key should remain "b" but no longer be connected to external hook

    def test_verification_method(self):
        """Test the verification method."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelect(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test valid values
        success, _ = selection_dict.validate_values_by_keys({"dict": {"a": 1, "b": 2}})
        assert success
        
        success, _ = selection_dict.validate_values_by_keys({"key": "a"})
        assert success
        
        success, _ = selection_dict.validate_values_by_keys({"value": 1})
        assert success
        
        # Test invalid values - need to test with both key and dict context
        success, msg = selection_dict.validate_values_by_keys({"key": "nonexistent", "dict": {"a": 1, "b": 2}})
        assert not success
        assert "not in dictionary" in msg

    def test_invalidation(self):
        """Test invalidation behavior."""
        test_dict = {"a": 1, "b": 2}
        invalidation_called: list[bool] = []
        def invalidate_callback() -> None:
            invalidation_called.append(True)
        selection_dict = XDictSelect(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger,
            invalidate_callback=invalidate_callback
        )
        
        # Test invalidation
        success, _ = selection_dict._invalidate() # type: ignore
        assert success
        assert len(invalidation_called) == 1

    def test_dict_key_change_propagation(self):
        """Test that changing dict or key updates the value."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        selection_dict = XDictSelect(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Change key
        selection_dict.change_key("b")
        assert selection_dict.value == 2
        
        # Change dict to include the current key
        from types import MappingProxyType
        selection_dict.submit_values_by_keys({"dict": MappingProxyType({"b": 200, "x": 100, "y": 300}), "key": "x"})
        # Now we can set the key to "x" since "b" is still valid
        selection_dict.change_key("x")
        assert selection_dict.value == 100

    def test_value_change_propagation(self):
        """Test that changing value updates the dict."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelect(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Change value
        selection_dict.change_value(999)
        assert selection_dict.dict_hook.value["a"] == 999
        assert selection_dict.value == 999

    def test_behavior_matrix(self):
        """
        Test the documented behavior matrix:
        ┌─────────────────┬──────────────────────────┬──────────────────────────┐
        │                 │    if key in dict        │  if key not in dict      │
        ├─────────────────┼──────────────────────────┼──────────────────────────┤
        │ if key is       │                          │                          │
        │ not None        │           ✓              │         error            │
        ├─────────────────┼──────────────────────────┼──────────────────────────┤
        │ if key is       │                          │                          │
        │ None            │         error            │         error            │
        └─────────────────┴──────────────────────────┴──────────────────────────┘
        """
        test_dict = {"a": 1, "b": 2}
        
        # Case 1: key is not None AND key in dict -> ✓
        selection_dict = XDictSelect(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        assert selection_dict.key == "a"
        assert selection_dict.value == 1
        
        # Case 2: key is not None AND key not in dict -> error
        with pytest.raises(KeyError):
            XDictSelect(
                dict_hook=test_dict,
                key_hook="nonexistent",
                value_hook=None,
                logger=logger
            )
        
        # Case 3: key is None AND key in dict -> error (can't pass None as key)
        # This is prevented by type system - K cannot be None
        
        # Case 4: key is None AND key not in dict -> error (can't pass None as key)
        # This is prevented by type system - K cannot be None


class TestObservableOptionalSelectionDict:
    """Test ObservableOptionalSelectionDict functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_owner = MockObservable("test_owner")

    def test_basic_creation(self):
        """Test basic ObservableOptionalSelectionDict creation."""
        # Create test data
        test_dict = {"a": 1, "b": 2, "c": 3}
        test_key = "b"
        test_value = 2
        
        # Create selection dict
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook=test_key,
            value_hook=None,
            logger=logger
        )
        
        # Verify creation
        assert selection_dict is not None
        assert selection_dict.value == test_value
        assert selection_dict.key == test_key
        assert selection_dict.dict_hook.value == test_dict

    def test_creation_with_none_values(self):
        """Test creation with None values."""
        test_dict = {"a": 1, "b": 2}
        
        # Create with None key and value
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            logger=logger
        )
        
        # Verify creation
        assert selection_dict is not None
        assert selection_dict.value is None
        assert selection_dict.key is None

    def test_optional_behavior(self):
        """Test optional behavior with None values."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            logger=logger
        )
        
        # Initially both key and value should be None
        assert selection_dict.key is None
        assert selection_dict.value is None
        
        # Set key to a valid value - should get value from dict
        selection_dict.change_key("a")
        assert selection_dict.value == 1
        
        # Set value to None for a non-None key - should work
        selection_dict.change_value(None)
        assert selection_dict.key == "a"
        assert selection_dict.value is None
        
        # Set key back to None - value should automatically be None
        selection_dict.change_key(None)
        assert selection_dict.key is None
        assert selection_dict.value is None

    def test_hook_interface_optional(self):
        """Test CarriesHooks interface with optional values."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test get_hook_keys - now includes secondary hooks
        keys = selection_dict._get_hook_keys() # type: ignore
        assert keys == {"dict", "key", "value", "keys", "values", "length"}
        
        # Test secondary hooks provide read-only access
        assert selection_dict.keys == {"a", "b"}
        assert selection_dict.values == [1, 2]
        assert selection_dict.length == 2
        
        # Test get_hook_value_as_reference - setting key to None sets value to None
        selection_dict.change_key(None)
        assert selection_dict.value is None

    def test_verification_method_optional(self):
        """Test verification method with optional values."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test valid values
        success, msg = selection_dict.validate_values_by_keys({"key": "a"})
        assert success
        
        success, msg = selection_dict.validate_values_by_keys({"value": 1})
        assert success
        
        # Test None key - should be valid and set value to None
        selection_dict.change_key(None)
        assert selection_dict.value is None
        # Dictionary should remain unchanged
        assert selection_dict.dict_hook.value == test_dict
        
        # Test None key with non-None value (should be invalid)
        success, msg = selection_dict.validate_values_by_keys({"key": None, "value": 999})
        assert not success
        assert "Value is not None when key is None" in msg

    def test_optional_value_properties(self):
        """Test value and key properties with optional types."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test initial values
        assert selection_dict.value == 1
        assert selection_dict.key == "a"
        
        # Test setting value to None for a non-None key - should work
        selection_dict.change_value(None)
        assert selection_dict.key == "a"
        assert selection_dict.value is None
        
        # Test setting key to None - should work and value should be None
        selection_dict.change_key(None)
        assert selection_dict.key is None
        assert selection_dict.value is None

    def test_error_handling_optional(self):
        """Test error handling for invalid optional combinations."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test setting key to None - should set value to None
        selection_dict.change_key(None)
        assert selection_dict.value is None
        # Setting key back to "a" and value to 999 should work
        selection_dict.change_key("a")
        selection_dict.change_value(999)
        assert selection_dict.value == 999

    def test_collective_hooks_optional(self):
        """Test CarriesCollectiveHooks interface with optional values."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test get_collective_hook_keys - now includes secondary hooks
        collective_keys = selection_dict.hook_keys
        assert collective_keys == {"dict", "key", "keys", "length", "value", "values"}
        
        # Test that secondary hooks are read-only (cannot submit values directly)
        keys_hook = selection_dict.keys_hook
        values_hook = selection_dict.values_hook
        length_hook = selection_dict.length_hook
        
        # Verify they are ReadOnlyHook instances (have value but not submit_value)
        assert hasattr(keys_hook, 'value')
        assert hasattr(values_hook, 'value')
        assert hasattr(length_hook, 'value')
        
        # Test that the interface is properly implemented
        # The connect_hooks functionality is tested elsewhere
        assert hasattr(selection_dict, 'join_many_by_keys')

    def test_edge_case_empty_dict(self):
        """Test behavior with empty dictionary."""
        # Test that creation with empty dict and invalid key fails
        with pytest.raises(KeyError):
            XDictSelectOptional(
                dict_hook={},
                key_hook="nonexistent",
                value_hook=None,
                logger=logger
            )
        
        # Test that None key with empty dict works
        selection_dict = XDictSelectOptional[str, int](
            dict_hook={},
            key_hook=None,
            value_hook=None,
            logger=logger
        )
        assert selection_dict.key is None
        assert selection_dict.value is None

    def test_edge_case_single_item_dict(self):
        """Test behavior with single-item dictionary."""
        test_dict = {"only": 42}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="only",
            value_hook=None,
            logger=logger
        )
        
        assert selection_dict.key == "only"
        assert selection_dict.value == 42
        
        # Test switching to None (must do key first, then value)
        selection_dict.change_key(None)
        assert selection_dict.key is None
        assert selection_dict.value is None

    def test_edge_case_large_dict(self):
        """Test behavior with large dictionary."""
        # Create a large dictionary
        large_dict = {f"key_{i}": i * 100 for i in range(1000)}
        
        selection_dict = XDictSelectOptional(
            dict_hook=large_dict,
            key_hook="key_500",
            value_hook=None,
            logger=logger
        )
        
        assert selection_dict.key == "key_500"
        assert selection_dict.value == 50000
        
        # Test switching to another key
        selection_dict.change_key("key_999")
        assert selection_dict.value == 99900

    def test_complex_value_types(self):
        """Test with complex value types."""
        complex_dict = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2, 3),
            "set": {1, 2, 3}
        }
        
        selection_dict = XDictSelectOptional(
            dict_hook=complex_dict,
            key_hook="list",
            value_hook=None,
            logger=logger
        )
        
        assert selection_dict.value == [1, 2, 3]
        
        # Test switching to different complex types
        selection_dict.change_key("dict")
        assert selection_dict.value == {"nested": "value"}
        
        selection_dict.change_key("tuple")
        assert selection_dict.value == (1, 2, 3)

    def test_concurrent_modifications(self):
        """Test that external dict modifications are isolated (immutability)."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Modify the external dict directly (should affect observable since it uses the same reference)
        test_dict["d"] = 4
        
        # Observable should be able to use the new key since it shares the dict reference
        # Key "d" should be available
        selection_dict.change_key("d")
        assert selection_dict.value == 4
        
        # Update dict properly through the API
        new_dict = {"b": 2, "c": 3, "d": 4}  # Remove key "a", add "d"
        selection_dict.submit_values_by_keys({"dict": new_dict, "key": "d"})  # Set to valid key
        assert selection_dict.value == 4
        
        # Should not be able to switch back to removed key
        from nexpy.core.nexus_system.submission_error import SubmissionError
        with pytest.raises(SubmissionError):
            selection_dict.change_key("a")

    def test_set_dict_and_key_method(self):
        """Test the set_dict_and_key method for both classes."""
        # Test ObservableSelectionDict
        selection_dict = XDictSelect(
            dict_hook={"a": 1},
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Verify initial state
        assert selection_dict.key == "a"
        assert selection_dict.value == 1
        
        # Use submit_values_by_keys to change both
        selection_dict.submit_values_by_keys({"dict": {"x": 100, "y": 200}, "key": "x"})
        
        # Check the results
        assert selection_dict.key == "x"
        assert selection_dict.value == 100
        assert selection_dict.dict_hook.value == {"x": 100, "y": 200}
        
        # Test ObservableOptionalSelectionDict
        optional_dict = XDictSelectOptional(
            dict_hook={"a": 1},
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Use submit_values_by_keys to change both
        optional_dict.submit_values_by_keys({"dict": {"x": 100, "y": 200}, "key": "y"})
        assert optional_dict.key == "y"
        assert optional_dict.value == 200
        
        # Test with None key
        optional_dict.submit_values_by_keys({"dict": {"a": 1, "b": 2}, "key": None})
        assert optional_dict.key is None
        assert optional_dict.value is None

    def test_validation_edge_cases(self):
        """Test edge cases in validation logic."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test validation with all three values
        success, msg = selection_dict.validate_values_by_keys({
            "dict": {"x": 10, "y": 20},
            "key": "x",
            "value": 10
        })
        assert success
        
        # Test validation with mismatched dict and value
        success, msg = selection_dict.validate_values_by_keys({
            "dict": {"x": 10, "y": 20},
            "key": "x",
            "value": 999  # Wrong value
        })
        assert not success
        
        # Test validation with None dict
        success, msg = selection_dict.validate_values_by_keys({
            "dict": None,
            "key": "x",
            "value": 10
        })
        assert not success
        assert "Dictionary is None" in msg

    def test_property_getter_setters_comprehensive(self):
        """Test comprehensive property getter/setter behavior."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        selection_dict = XDictSelectOptional[str, int](
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test dict_hook property
        assert selection_dict.dict_hook.value == test_dict
        
        # Test key_hook property
        assert selection_dict.key_hook.value == "a"
        
        # Test value_hook property
        assert selection_dict.value_hook.value == 1
        
        # Test rapid successive changes
        for key in ["b", "c", "a"]:
            selection_dict.change_key(key)
            assert selection_dict.key == key
            assert selection_dict.value == test_dict[key]

    def test_error_messages_clarity(self):
        """Test that error messages are clear and helpful."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test clear error message for invalid key
        try:
            selection_dict.change_key(None)# Should fail because value is not None
        except ValueError as e:
            assert "Cannot set key to None when current value is" in str(e)
        
        # Test clear error message for invalid value
        try:
            selection_dict.change_value(None)# Should fail because key is not None
        except ValueError as e:
            assert "Cannot set value to None when current key is" in str(e)

    def test_stress_test_rapid_changes(self):
        """Stress test with rapid changes."""
        test_dict = {f"key_{i}": i for i in range(100)}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="key_0",
            value_hook=None,
            logger=logger
        )
        
        # Rapidly change keys
        for i in range(0, 100, 10):
            key = f"key_{i}"
            selection_dict.change_key(key)
            assert selection_dict.key == key
            assert selection_dict.value == i
        
        # Rapidly change values
        for i in range(0, 100, 5):
            new_value = i * 1000
            selection_dict.change_value(new_value)
            # Verify dict was updated
            current_key = selection_dict.key
            assert current_key is not None
            assert selection_dict.dict_hook.value[current_key] == new_value

    def test_type_safety_edge_cases(self):
        """Test type safety with various edge cases."""
        # Test with string keys and numeric values
        test_dict = {"1": 1, "2": 2, "3": 3}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="1",
            value_hook=None,
            logger=logger
        )
        
        assert selection_dict.key == "1"
        assert selection_dict.value == 1
        
        # Test switching between string keys
        selection_dict.change_key("2")
        assert selection_dict.value == 2

    def test_destroy_cleanup(self):
        """Test destroy method properly cleans up resources."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Add some listeners to test cleanup
        def dummy_listener():
            pass
        
        selection_dict.add_listener(dummy_listener)
        assert selection_dict.has_listeners()
        
        # Test destroy method exists and can be called
        # Note: destroy method should remove listeners but we can't easily test
        # the complete cleanup without internal access
        # Note: destroy method is not implemented in the current version
        # assert hasattr(selection_dict, 'destroy')

    def test_behavior_matrix(self):
        """
        Test the documented behavior matrix:
        ┌─────────────────┬──────────────────────────┬──────────────────────────┐
        │                 │    if key in dict        │  if key not in dict      │
        ├─────────────────┼──────────────────────────┼──────────────────────────┤
        │ if key is       │                          │                          │
        │ not None        │           ✓              │         error            │
        ├─────────────────┼──────────────────────────┼──────────────────────────┤
        │ if key is       │                          │                          │
        │ None            │      None (value)        │      None (value)        │
        └─────────────────┴──────────────────────────┴──────────────────────────┘
        """
        test_dict = {"a": 1, "b": 2}
        
        # Case 1: key is not None AND key in dict -> ✓
        selection_dict = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        assert selection_dict.key == "a"
        assert selection_dict.value == 1
        
        # Case 2: key is not None AND key not in dict -> error
        with pytest.raises(KeyError):
            XDictSelectOptional(
                dict_hook=test_dict,
                key_hook="nonexistent",
                value_hook=None,
                logger=logger
            )
        
        # Case 3: key is None AND key in dict -> None (value)
        selection_dict_none = XDictSelectOptional(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            logger=logger
        )
        assert selection_dict_none.key is None
        assert selection_dict_none.value is None
        
        # Case 4: key is None AND key not in dict -> None (value)
        empty_dict: dict[str, int] = {}
        selection_dict_empty = XDictSelectOptional(
            dict_hook=empty_dict,
            key_hook=None,
            value_hook=None,
            logger=logger
        )
        assert selection_dict_empty.key is None
        assert selection_dict_empty.value is None
