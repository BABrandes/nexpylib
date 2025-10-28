from typing import Literal, TypeVar, Generic, Optional, Mapping, Any, Callable, Self
from logging import Logger

from nexpy.core.hooks.protocols.hook_protocol import HookProtocol
from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from nexpy.x_objects.dict_like.protocols import XDictProtocol
from ...core.nexus_system.update_function_values import UpdateFunctionValues
from .x_dict_selection_base import XDictSelectionBase
from .protocols import XSelectionDictWithDefaultProtocol
from ...core.nexus_system.submission_error import SubmissionError

K = TypeVar("K")
V = TypeVar("V")

class XSelectionDictWithDefault(
    XDictSelectionBase[K, V, K, V], 
    XSelectionDictWithDefaultProtocol[K, V], 
    Generic[K, V]
):
    """

    
    Valid Key Combinations:
    ┌─────────────────┬──────────────────────────┬──────────────────────────┐
    │                 │    if key in dict        │  if key not in dict      │
    ├─────────────────┼──────────────────────────┼──────────────────────────┤
    │ if key is       │                          │                          │
    │ not None        │           ✓              │   default (auto-create)  │
    ├─────────────────┼──────────────────────────┼──────────────────────────┤
    │ if key is       │                          │                          │
    │ None            │         error            │         error            │
    └─────────────────┴──────────────────────────┴──────────────────────────┘
    
    **Default Value Behavior:**
    - The key must not be None
    - If the key is not in the dictionary, a default entry is automatically added to the dictionary for this key
    - The default value can be a constant or a callable that takes the key and returns the value: Callable[[K], V]
    - This allows creating different default values based on which key is being accessed
    - The value will always match the dictionary value at the key (after default entry creation if needed)

    """

    def __init__(
        self,
        dict_hook: Mapping[K, V] | HookProtocol[Mapping[K, V]] | XDictProtocol[K, V],
        key_hook: K | HookProtocol[K],
        default_value: V | Callable[[K], V],
        value_hook: Optional[HookProtocol[V]] = None,
        logger: Optional[Logger] = None
    ):

        # Store default_value for use in callbacks
        self._default_value: V | Callable[[K], V] = default_value
        
        # Pre-process dict to add default entry if needed (before wrapping in Map)
        if not isinstance(dict_hook, HookProtocol):
            # Extract initial key
            initial_key = key_hook._get_value() if isinstance(key_hook, HookProtocol) else key_hook # type: ignore
            # Add default entry if key not in dict
            if initial_key not in dict_hook: # type: ignore
                _dict = dict[K, V](dict_hook) # type: ignore
                _dict[initial_key] = self._get_default_value(initial_key) # type: ignore
                dict_hook = _dict
        
        # Call parent constructor
        super().__init__(dict_hook, key_hook, value_hook, invalidate_callback=None, logger=logger) # type: ignore

    def _get_default_value(self, key: K) -> V:
        """Helper to get default value (call if callable, return if constant)."""
        if callable(self._default_value):
            return self._default_value(key)  # type: ignore
        return self._default_value

    def _create_add_values_callback(self) -> Callable[[UpdateFunctionValues[Literal["dict", "key", "value"], Any]], Mapping[Literal["dict", "key", "value"], Any]]:
        """
        Create the add_values_to_be_updated_callback for default selection logic.
        
        This callback auto-creates missing keys with default values.
        """
        def add_values_to_be_updated_callback(
            update_values: UpdateFunctionValues[Literal["dict", "key", "value"], Any]
        ) -> Mapping[Literal["dict", "key", "value"], Any]:
            
            match ("dict" in update_values.submitted, "key" in update_values.submitted, "value" in update_values.submitted):
                case (True, True, True):
                    # All three values provided - pass through for validation
                    # Validation callback will check if key is in dict
                    return {}
                    
                case (True, True, False):
                    # Dict and key provided - derive value from dict
                    # If key not in dict, validation will catch it
                    if update_values.submitted["key"] is not None and update_values.submitted["key"] in update_values.submitted["dict"]:
                        return {"value": update_values.submitted["dict"][update_values.submitted["key"]]}
                    return {}
                
                case (True, False, True):
                    # Dict and value provided - validate value matches current key
                    if update_values.current["key"] not in update_values.submitted["dict"]:
                        raise KeyError(f"Current key {update_values.current['key']} not in submitted dictionary")
                    if update_values.submitted["value"] != update_values.submitted["dict"][update_values.current["key"]]:
                        raise ValueError(f"Value {update_values.submitted['value']} is not the same as the value in the dictionary {update_values.submitted['dict'][update_values.current['key']]}")
                    return {}
                
                case (True, False, False):
                    # Dict provided alone - current key must be in dict
                    if update_values.current["key"] not in update_values.submitted["dict"]:
                        raise KeyError(f"Current key {update_values.current['key']} not in submitted dictionary")
                    return {"value": update_values.submitted["dict"][update_values.current["key"]]}
                
                case (False, True, True):
                    # Key and value provided - update dict with new value
                    _dict = dict(update_values.current["dict"])
                    _dict[update_values.submitted["key"]] = update_values.submitted["value"]
                    return {"dict": _dict}
                
                case (False, True, False):
                    # Key provided alone - add key to dict with default if not present
                    if update_values.submitted["key"] not in update_values.current["dict"]:
                        _dict = dict(update_values.current["dict"])
                        _default_val = self._get_default_value(update_values.submitted["key"])
                        _dict[update_values.submitted["key"]] = _default_val
                        return {"dict": _dict, "value": _default_val}
                    return {"value": update_values.current["dict"][update_values.submitted["key"]]}
                
                case (False, False, True):
                    # Value provided alone - update dict at current key
                    _dict = dict(update_values.current["dict"])
                    _dict[update_values.current["key"]] = update_values.submitted["value"]
                    return {"dict": _dict}
                
                case (False, False, False):
                    # Nothing provided - no updates needed
                    return {}

            raise ValueError("Invalid keys")
        
        return add_values_to_be_updated_callback

    def _create_validation_callback(self) -> Callable[
        [Mapping[Literal["dict", "key", "value"], Any]], 
        tuple[bool, str]
    ]:
        """
        Create the validate_complete_values_in_isolation_callback for default selection.
        
        Validates that dict/key/value are consistent. Key must not be None.
        """
        def validate_complete_values_in_isolation_callback(
            values: Mapping[Literal["dict", "key", "value"], Any]
        ) -> tuple[bool, str]:
            
            # Check that all three values are present
            if "dict" not in values:
                return False, "Dict not in values"
            if "key" not in values:
                return False, "Key not in values"
            if "value" not in values:
                return False, "Value not in values"

            # Check that the dictionary is not None
            if values["dict"] is None:
                return False, "Dictionary is None"
            
            # Check that the key is not None
            if values["key"] is None:
                return False, "Key must not be None"

            # Check that the key is in the dictionary
            if values["key"] not in values["dict"]:
                return False, "Key not in dictionary"

            # Check that the value is equal to the value in the dictionary
            if values["value"] != values["dict"][values["key"]]:
                return False, "Value not equal to value in dictionary"

            return True, "Validation of complete value set in isolation passed"
        
        return validate_complete_values_in_isolation_callback

    def _compute_initial_value(
        self, 
        initial_dict: Mapping[K, V], 
        initial_key: K
    ) -> V:
        """
        Compute the initial value from dict and key.
        
        If key is not in dict, returns the default value (dict will be updated during init).
        """
        if initial_key not in initial_dict:
            # Return default value
            return self._get_default_value(initial_key)
        else:
            return initial_dict[initial_key]

    #########################################################
    # ObservableDefaultSelectionDictProtocol implementation
    #########################################################

    #-------------------------------- Key --------------------------------

    @property
    def key_hook(self) -> OwnedWritableHook[K, Self]:
        """Get the key hook."""
        return self._primary_hooks["key"]
    
    @property
    def key(self) -> K:
        """Get the current key."""
        return self._primary_hooks["key"].value # type: ignore

    @key.setter
    def key(self, value: K) -> None:
        """Set the current key."""
        self.change_key(value)
    
    def change_key(self, value: K, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Change the current key."""
        success, msg = self._submit_value("key", value, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, value, "key")

    #-------------------------------- Value --------------------------------

    @property
    def value_hook(self) -> OwnedWritableHook[V, Self]:
        """Get the value hook."""
        return self._primary_hooks["value"]
    
    @property
    def value(self) -> V:
        """Get the current value."""
        return self._primary_hooks["value"].value # type: ignore
    
    @value.setter
    def value(self, value: V) -> None:
        """Set the current value."""
        self.change_value(value)
    
    def change_value(self, value: V, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Change the current value."""
        success, msg = self._submit_value("value", value, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, value, "value")

    #-------------------------------- Convenience methods -------------------
    
    def change_dict_and_key(self, dict_value: Mapping[K, V], key_value: K, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Change the dictionary and key behind this hook."""
        success, msg = self._submit_values({"dict": dict_value, "key": key_value}, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, {"dict": dict_value, "key": key_value}, "dict and key")
    
    #------------------------------------------------------------------------