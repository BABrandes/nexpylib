from typing import Any, Literal, Mapping, Optional
from logging import Logger, basicConfig, getLogger, DEBUG

from nexpy import XDictSelectOptionalDefault
from nexpy import XCompositeBase
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


class TestObservableOptionalDefaultSelectionDict:
    """Test ObservableOptionalDefaultSelectionDict functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_owner = MockObservable("test_owner")

    def test_basic_creation(self):
        """Test basic ObservableOptionalDefaultSelectionDict creation."""
        # Create test data
        test_dict = {"a": 1, "b": 2, "c": 3}
        test_key = "b"
        default_value = 999
        
        # Create default selection dict
        selection_dict = XDictSelectOptionalDefault(
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

    def test_creation_with_none_key(self):
        """Test creation with None key returns None value."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        # Create with None key
        selection_dict = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Verify creation
        assert selection_dict is not None
        assert selection_dict.value == None
        assert selection_dict.key is None

    def test_creation_with_missing_key(self):
        """Test creation with key not in dict creates default entry."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        # Create with key not in dict
        selection_dict = XDictSelectOptionalDefault(
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

    def test_none_key_behavior(self):
        """Test that None key gives None value."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Initially key "a" should give value 1
        assert selection_dict.value == 1
        assert selection_dict.key == "a"
        
        # Set key to None - should give None value
        selection_dict.key = None
        assert selection_dict.value == None
        assert selection_dict.key is None
        
        # Set key back to "b" - should use dict value
        selection_dict.key = "b"
        assert selection_dict.value == 2
        assert selection_dict.key == "b"

    def test_missing_key_creates_default_entry(self):
        """Test that missing key creates default entry."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Set key to one not in dict - should create default entry
        selection_dict.key = "z"
        assert selection_dict.value == default_value
        assert selection_dict.key == "z"
        assert selection_dict.dict_hook.value["z"] == default_value

    def test_value_setting_with_none_key(self):
        """Test setting value when key is None."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Should be able to set value to None when key is None
        selection_dict.value = None
        assert selection_dict.value == None
        
        # Should not be able to set value to non-None when key is None
        with pytest.raises(ValueError, match="not None when key is None"):
            selection_dict.value = 123

    def test_value_setting_with_valid_key(self):
        """Test setting value when key is valid."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Should be able to set value when key is valid
        selection_dict.value = 777
        assert selection_dict.value == 777
        assert selection_dict.dict_hook.value["a"] == 777

    def test_verification_method(self):
        """Test the verification method."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Test valid values with key
        success, msg = selection_dict._validate_values({"dict": {"a": 1, "b": 2}, "key": "a", "value": 1}) # type: ignore
        assert success
        
        # Test valid values with None key and None value
        success, msg = selection_dict._validate_values({"dict": {"a": 1, "b": 2}, "key": None, "value": None}) # type: ignore
        assert success
        
        # Test invalid - None key with non-None value
        success, msg = selection_dict._validate_values({"dict": {"a": 1, "b": 2}, "key": None, "value": 123}) # type: ignore
        assert not success
        assert "not None when key is None" in msg
        
        # Test invalid - key not in dict
        success, msg = selection_dict._validate_values({"dict": {"a": 1, "b": 2}, "key": "z", "value": 1}) # type: ignore
        assert not success
        assert "not in dictionary" in msg
        
        # Test invalid - value doesn't match dictionary value
        success, msg = selection_dict._validate_values({"dict": {"a": 1, "b": 2}, "key": "a", "value": 999}) # type: ignore
        assert not success
        assert "not equal to value in dictionary" in msg

    def test_set_dict_and_key(self):
        """Test set_dict_and_key method."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Set valid dict and key
        new_dict = {"x": 100, "y": 200}
        selection_dict.change_dict_and_key(new_dict, "x")
        assert selection_dict.dict_hook.value == new_dict
        assert selection_dict.key == "x"
        assert selection_dict.value == 100
        
        # Set dict and None key
        selection_dict.change_dict_and_key(new_dict, None)
        assert selection_dict.dict_hook.value == new_dict
        assert selection_dict.key is None
        assert selection_dict.value == None

        # Set dict and missing key - should create default entry
        selection_dict.change_dict_and_key(new_dict, "z")
        assert selection_dict.key == "z"
        assert selection_dict.value == default_value
        assert selection_dict.dict_hook.value["z"] == default_value

    def test_edge_cases(self):
        """Test edge cases."""
        # Test with empty dict and None key
        empty_dict: dict[str, int] = {}
        default_value = 999
        selection_dict = XDictSelectOptionalDefault(
            dict_hook=empty_dict,
            key_hook=None,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        assert selection_dict.value == None
        assert selection_dict.key is None
        
        # Test with default value that equals a dict value
        test_dict = {"a": 999, "b": 2}
        selection_dict2 = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            default_value=999,  # Same as dict["a"]
            logger=logger
        )
        
        assert selection_dict2.value == None  # None because key is None
        assert selection_dict2.key is None
        
        # Set key to "a" - should work even though default value equals dict["a"]
        selection_dict2.key = "a"
        assert selection_dict2.value == 999
        assert selection_dict2.key == "a"

    def test_properties(self):
        """Test property access."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = XDictSelectOptionalDefault(
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

    def test_callable_default_value(self):
        """Test using a callable as default value."""
        test_dict = {"a": 1, "b": 2}
        
        # Create a callable that returns key-specific defaults
        def default_factory(key: str) -> int:
            return len(key) * 100  # Different value based on key length
        
        selection_dict = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_factory,
            logger=logger
        )
        
        # Initial key "a" should use dict value
        assert selection_dict.value == 1
        
        # Set key to None - should give None value
        selection_dict.key = None
        assert selection_dict.value == None
        
        # Set key to "xyz" (not in dict) - should use callable to create default
        selection_dict.key = "xyz"
        assert selection_dict.value == 300  # len("xyz") * 100 = 300
        assert selection_dict.dict_hook.value["xyz"] == 300

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
        │ None            │      None (value)        │      None (value)        │
        └─────────────────┴──────────────────────────┴──────────────────────────┘
        """
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        # Case 1: key is not None AND key in dict -> ✓
        selection_dict = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        assert selection_dict.key == "a"
        assert selection_dict.value == 1
        
        # Case 2: key is not None AND key not in dict -> default (auto-create)
        selection_dict_autocreate = XDictSelectOptionalDefault(
            dict_hook=test_dict.copy(),
            key_hook="z",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        assert selection_dict_autocreate.key == "z"
        assert selection_dict_autocreate.value == default_value
        assert selection_dict_autocreate.dict_hook.value["z"] == default_value
        
        # Case 3: key is None AND key in dict -> None (value)
        selection_dict_none = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        assert selection_dict_none.key is None
        assert selection_dict_none.value is None
        
        # Case 4: key is None AND key not in dict -> None (value)
        empty_dict: dict[str, int] = {}
        selection_dict_empty = XDictSelectOptionalDefault(
            dict_hook=empty_dict,
            key_hook=None,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        assert selection_dict_empty.key is None
        assert selection_dict_empty.value is None

    def test_callable_default_value_in_initialization(self):
        """Test callable default value during initialization."""
        test_dict = {"a": 1}
        
        def default_factory(key: str) -> int:
            return ord(key[0]) if key else 0  # Use ASCII value of first char
        
        # Create with key not in dict
        selection_dict = XDictSelectOptionalDefault(
            dict_hook=test_dict,
            key_hook="z",
            value_hook=None,
            default_value=default_factory,
            logger=logger
        )
        
        # Should have created default entry using callable
        assert selection_dict.value == ord("z")  # 122
        assert selection_dict.dict_hook.value["z"] == ord("z")

