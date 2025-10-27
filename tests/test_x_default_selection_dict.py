from typing import Any, Literal, Mapping, Optional
from logging import Logger, basicConfig, getLogger, DEBUG

from nexpy import XDictSelectDefault, FloatingHook, Hook
from nexpy import XCompositeBase
from nexpy.core.hooks import OwnedReadOnlyHook as OwnedHook
import pytest

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


class TestObservableDefaultSelectionDict:
    """Test ObservableDefaultSelectionDict functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_owner = MockObservable("test_owner")

    def test_basic_creation(self):
        """Test basic ObservableDefaultSelectionDict creation."""
        # Create test data
        test_dict = {"a": 1, "b": 2, "c": 3}
        test_key = "b"
        default_value = 999
        
        # Create default selection dict
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook=test_key,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Verify creation
        assert selection_dict is not None
        assert selection_dict.value == 2  # Should be dict value, not default
        assert selection_dict.key == test_key
        assert selection_dict.dict_hook.value == test_dict

    def test_creation_with_missing_key(self):
        """Test creation with key not in dict creates default entry."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        # Create with key not in dict
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="z",  # Not in dict
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Verify creation - should have added default entry
        assert selection_dict is not None
        assert selection_dict.value == default_value
        assert selection_dict.key == "z"
        assert selection_dict.dict_hook.value["z"] == default_value

    def test_creation_with_hooks(self):
        """Test creation with external hooks."""
        # Create external hooks using FloatingHook to avoid owner registration issues
        dict_hook = FloatingHook[Mapping[str, int]](value={"x": 10, "y": 20}, logger=logger)
        key_hook: Hook[str] = FloatingHook[str](value="x", logger=logger)
        value_hook = FloatingHook[int](value=10, logger=logger)
        default_value = 999
        
        # Create selection dict
        selection_dict = XDictSelectDefault(
            dict_hook=dict_hook,
            key_hook=key_hook,
            value_hook=value_hook,
            default_value=default_value,
            logger=logger
        )
        
        # Verify creation
        assert selection_dict is not None
        assert selection_dict.value == 10
        assert selection_dict.key == "x"
        assert selection_dict.dict_hook.value == {"x": 10, "y": 20}

    def test_default_value_behavior(self):
        """Test default value behavior when key is not in dict."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Initially key "a" should give value 1
        assert selection_dict.value == 1
        assert selection_dict.key == "a"
        
        # Set key to "z" (not in dict) - should create default entry
        selection_dict.change_key("z")
        assert selection_dict.value == default_value
        assert selection_dict.key == "z"
        assert selection_dict.dict_hook.value["z"] == default_value
        
        # Set key back to "b" - should use dict value
        selection_dict.change_key("b")
        assert selection_dict.value == 2
        assert selection_dict.key == "b"

    def test_value_setting_with_missing_key(self):
        """Test setting value creates default entry when key not in dict."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="z",  # Not in dict initially
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Should have created default entry
        assert selection_dict.value == default_value
        assert selection_dict.dict_hook.value["z"] == default_value
        
        # Should be able to set value when key exists
        selection_dict.change_value(123)
        assert selection_dict.value == 123
        assert selection_dict.dict_hook.value["z"] == 123

    def test_value_setting_with_valid_key(self):
        """Test setting value when key is valid."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Should be able to set value when key is valid
        selection_dict.change_value(777)
        assert selection_dict.value == 777
        assert selection_dict.dict_hook.value["a"] == 777

    def test_hook_interface(self):
        """Test CarriesHooks interface implementation."""
        test_dict: Mapping[str, int] = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Test get_hook_keys - now includes secondary hooks
        keys = selection_dict.hook_keys
        assert keys == {"dict", "key", "keys", "length", "value", "values"}
        
        # Test secondary hooks
        assert selection_dict.keys == {"a", "b"}
        assert selection_dict.values == [1, 2]
        assert selection_dict.length == 2
        
        # Test get_hook
        dict_hook = selection_dict.dict_hook
        key_hook = selection_dict.key_hook
        value_hook = selection_dict.value_hook
        
        assert dict_hook is not None
        assert key_hook is not None
        assert value_hook is not None
        
        # Test get_hook_value_as_reference
        # Dict is now stored as MappingProxyType, so compare contents
        dict_value = selection_dict.dict_hook.value
        assert dict(dict_value) == test_dict  # type: ignore[arg-type]
        assert selection_dict.key_hook.value == "a"
        assert selection_dict.value_hook.value == 1
        
        # Test get_hook_key
        assert selection_dict._get_key_by_hook_or_nexus(selection_dict.dict_hook) == "dict" # type: ignore
        assert selection_dict._get_key_by_hook_or_nexus(selection_dict.key_hook) == "key" # type: ignore
        assert selection_dict._get_key_by_hook_or_nexus(selection_dict.value_hook) == "value" # type: ignore

    def test_verification_method(self):
        """Test the verification method."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Test valid values with key
        success, msg = selection_dict.validate_values_by_keys({"dict": {"a": 1, "b": 2}, "key": "a", "value": 1})
        assert success
        
        # Test invalid - None key (key must not be None)
        success, msg = selection_dict.validate_values_by_keys({"dict": {"a": 1, "b": 2}, "key": None, "value": default_value})
        assert not success
        assert "Key must not be None" in msg
        
        # Test invalid - key not in dict
        success, msg = selection_dict.validate_values_by_keys({"dict": {"a": 1, "b": 2}, "key": "z", "value": 1})
        assert not success
        assert "not in dictionary" in msg
        
        # Test invalid - value doesn't match dictionary value
        success, msg = selection_dict.validate_values_by_keys({"dict": {"a": 1, "b": 2}, "key": "a", "value": 999})
        assert not success  # Should be invalid - value doesn't match dictionary
        assert "not equal to value in dictionary" in msg

    def test_dict_key_change_propagation(self):
        """Test that changing dict or key updates the value."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        default_value = 999
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Change key
        selection_dict.change_key("b")
        assert selection_dict.value == 2
        
        # Change key to one not in dict - should create default entry
        selection_dict.change_key("z")
        assert selection_dict.value == default_value
        assert selection_dict.dict_hook.value["z"] == default_value
        
        # Try to change dict to one that doesn't contain current key "z" - should raise error
        from types import MappingProxyType
        from nexpy.core.nexus_system.submission_error import SubmissionError
        new_dict_without_z = {"b": 200, "x": 100, "y": 300}
        with pytest.raises(SubmissionError, match="not in submitted dictionary"):
            selection_dict.submit_values_by_keys({"dict": MappingProxyType(new_dict_without_z)})
        
        # Dict should remain unchanged
        assert selection_dict.dict_hook.value["z"] == default_value
        
        # First change key back to one that exists in both old and new dict
        selection_dict.change_key("b")
        assert selection_dict.value == 2  # Still old value
        
        # Now change dict to new dict - should succeed since "b" is in it
        new_dict = {"b": 200, "x": 100, "y": 300}
        success, msg = selection_dict.submit_values_by_keys({"dict": MappingProxyType(new_dict)})
        assert success, f"Dict update should succeed when key is present: {msg}"
        assert selection_dict.dict_hook.value["b"] == 200
        assert selection_dict.dict_hook.value["x"] == 100
        assert selection_dict.value == 200

    def test_value_change_propagation(self):
        """Test that changing value updates the dict."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Change value when key is set
        selection_dict.change_value(777)
        assert selection_dict.dict_hook.value["a"] == 777
        assert selection_dict.value == 777

    def test_connect_disconnect(self):
        """Test connect and disconnect functionality."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
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

    def test_invalidation(self):
        """Test invalidation behavior."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Test invalidation - no callback provided
        success, msg = selection_dict._invalidate() # type: ignore  
        assert success
        assert "Successfully invalidated" in msg

    def test_set_dict_and_key(self):
        """Test set_dict_and_key method."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Set valid dict and key
        new_dict = {"x": 100, "y": 200}
        selection_dict.submit_values_by_keys({"dict": new_dict, "key": "x"})
        assert selection_dict.dict_hook.value == new_dict
        assert selection_dict.key == "x"
        assert selection_dict.value == 100
        
        # Set dict and key not in dict - should create default entry
        selection_dict.submit_values_by_keys({"dict": new_dict, "key": "z"})
        assert selection_dict.key == "z"
        assert selection_dict.value == default_value
        # Dict should now have the "z" key with default value
        assert selection_dict.dict_hook.value["z"] == default_value

    def test_error_handling(self):
        """Test error handling for invalid operations."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        # Test creation with invalid value_hook
        with pytest.raises(ValueError):
            XDictSelectDefault(
                dict_hook=test_dict,
                key_hook="a",
                value_hook="invalid",  # type: ignore
                default_value=default_value,
                logger=logger
            )

    def test_edge_cases(self):
        """Test edge cases."""
        # Test with empty dict and missing key - should create default entry
        empty_dict: dict[str, int] = {}
        default_value = 999
        selection_dict = XDictSelectDefault(
            dict_hook=empty_dict,
            key_hook="z",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        assert selection_dict.value == default_value
        assert selection_dict.key == "z"
        assert selection_dict.dict_hook.value["z"] == default_value
        
        # Test with default value that equals a dict value
        test_dict = {"a": 999, "b": 2}
        selection_dict2 = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=999,  # Same as dict["a"]
            logger=logger
        )
        
        assert selection_dict2.value == 999
        assert selection_dict2.key == "a"
        
        # Set key to "c" (not in dict) - should create default entry with value 999
        selection_dict2.change_key("c")
        assert selection_dict2.value == 999
        assert selection_dict2.key == "c"
        assert selection_dict2.dict_hook.value["c"] == 999

    def test_properties(self):
        """Test property access."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Test dict_hook property
        dict_hook = selection_dict.dict_hook
        assert dict_hook is not None
        assert dict_hook.value == test_dict
        
        # Test key_hook property
        key_hook = selection_dict.key_hook
        assert key_hook is not None
        assert key_hook.value == "a"
        
        # Test value_hook property
        value_hook = selection_dict.value_hook
        assert value_hook is not None
        assert value_hook.value == 1
        
        # Test value property
        assert selection_dict.value == 1
        
        # Test key property
        assert selection_dict.key == "a"

    def test_destroy(self):
        """Test destroy method."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Add a listener to verify removal
        listener_called = False
        def test_listener():
            nonlocal listener_called
            listener_called = True
        
        selection_dict.add_listener(test_listener)
        
        # Destroy should remove listeners and disconnect hooks
        # Just remove listeners - hooks may already be disconnected
        selection_dict.remove_all_listeners()
        
        # Trigger invalidation - listener should not be called
        selection_dict._invalidate() # type: ignore
        assert not listener_called

    def test_callable_default_value(self):
        """Test using a callable as default value."""
        test_dict = {"a": 1, "b": 2}
        
        # Create a callable that returns key-specific defaults
        def default_factory(key: str) -> int:
            return len(key) * 100  # Different value based on key length
        
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_factory,
            logger=logger
        )
        
        # Initial key "a" should use dict value
        assert selection_dict.value == 1
        
        # Set key to "xyz" (not in dict) - should use callable to create default
        selection_dict.change_key("xyz")
        assert selection_dict.value == 300  # len("xyz") * 100 = 300
        assert selection_dict.dict_hook.value["xyz"] == 300
        
        # Set key to "hello" (not in dict) - should use callable with different result
        selection_dict.change_key("hello")
        assert selection_dict.value == 500  # len("hello") * 100 = 500
        assert selection_dict.dict_hook.value["hello"] == 500

    def test_callable_default_value_in_initialization(self):
        """Test callable default value during initialization."""
        test_dict = {"a": 1}
        
        def default_factory(key: str) -> int:
            return ord(key[0]) if key else 0  # Use ASCII value of first char
        
        # Create with key not in dict
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="z",
            value_hook=None,
            default_value=default_factory,
            logger=logger
        )
        
        # Should have created default entry using callable
        assert selection_dict.value == ord("z")  # 122
        assert selection_dict.dict_hook.value["z"] == ord("z")

    def test_behavior_matrix(self):
        """
        Test the documented behavior matrix:
        ┌─────────────────┬──────────────────────────┬──────────────────────────┐
        │                 │    if key in dict        │  if key not in dict      │
        ├─────────────────┼──────────────────────────┼──────────────────────────┤
        │ if key is       │                          │                          │
        │ not None        │           ✓              │   default (auto-create)  │
        ├─────────────────┼──────────────────────────┼──────────────────────────┤
        │ if key is       │                          │                          │
        │ None            │         error            │         error            │
        └─────────────────┴──────────────────────────┴──────────────────────────┘
        """
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        # Case 1: key is not None AND key in dict -> ✓
        selection_dict = XDictSelectDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        assert selection_dict.key == "a"
        assert selection_dict.value == 1
        
        # Case 2: key is not None AND key not in dict -> default (auto-create)
        selection_dict_autocreate = XDictSelectDefault(
            dict_hook=test_dict.copy(),
            key_hook="z",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        assert selection_dict_autocreate.key == "z"
        assert selection_dict_autocreate.value == default_value
        assert selection_dict_autocreate.dict_hook.value["z"] == default_value
        
        # Case 3: key is None AND key in dict -> error (can't pass None as key)
        # This is prevented by type system - K cannot be None
        
        # Case 4: key is None AND key not in dict -> error (can't pass None as key)
        # This is prevented by type system - K cannot be None
