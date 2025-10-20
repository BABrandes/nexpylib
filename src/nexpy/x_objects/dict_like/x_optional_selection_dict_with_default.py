from typing import Literal, TypeVar, Generic, Optional, Mapping, Any, Callable
from logging import Logger

from ...core.hooks.hook_aliases import Hook, ReadOnlyHook
from ...core.hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from .x_dict_base import XDictBase
from .protocols import XOptionalSelectionDictWithDefaultProtocol
from ...core.nexus_system.update_function_values import UpdateFunctionValues
from ...core.nexus_system.submission_error import SubmissionError

K = TypeVar("K")
V = TypeVar("V")

class XOptionalSelectionDictWithDefault(
    XDictBase[K, V, Optional[K], Optional[V]], 
    XOptionalSelectionDictWithDefaultProtocol[K, V], 
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
    │ None            │      None (value)        │      None (value)        │
    └─────────────────┴──────────────────────────┴──────────────────────────┘
    
    **Optional + Default Behavior:**
    - If key is None, then value must be None
    - If key is not None and not in dict, a default entry is automatically created
    - The default value can be a constant or a callable: Callable[[K], V]
    - Allows setting value to None even when key is not None (for flexibility)
    
    """

    def __init__(
        self,
        dict_hook: Mapping[K, V] | Hook[Mapping[K, V]] | ReadOnlyHook[Mapping[K, V]],
        key_hook: Optional[K] | Hook[Optional[K]] | ReadOnlyHook[Optional[K]] = None,
        value_hook: Optional[Hook[Optional[V]]] | ReadOnlyHook[Optional[V]] = None,
        default_value: V | Callable[[K], V] = None,  # type: ignore
        logger: Optional[Logger] = None
    ):
        """
        Initialize an ObservableOptionalDefaultSelectionDict.
        
        Args:
            dict_hook: The mapping or hook containing the mapping
            key_hook: The initial key or hook (can be None)
            value_hook: Optional hook for the value (if None, will be derived)
            default_value: Default value or callable to use when key is not in dict
            logger: Optional logger for debugging
        """
        # Store default_value for use in callbacks
        self._default_value: V | Callable[[K], V] = default_value
        
        # Pre-process dict to add default entry if needed (before wrapping in Map)
        if not isinstance(dict_hook, ManagedHookProtocol):
            # Extract initial key
            initial_key = key_hook.value if isinstance(key_hook, ManagedHookProtocol) else key_hook # type: ignore
            # Add default entry if key is not None and not in dict
            if initial_key is not None and initial_key not in dict_hook: # type: ignore
                _dict = dict(dict_hook) # type: ignore
                _dict[initial_key] = self._get_default_value(initial_key) # type: ignore
                dict_hook = _dict # type: ignore
        
        # Call parent constructor
        super().__init__(dict_hook, key_hook, value_hook, invalidate_callback=None, logger=logger) # type: ignore

    def _get_default_value(self, key: K) -> V:
        """Helper to get default value (call if callable, return if constant)."""
        if callable(self._default_value):
            return self._default_value(key)  # type: ignore
        return self._default_value  # type: ignore

    def _create_add_values_callback(self) -> Callable[
        ["XOptionalSelectionDictWithDefault[K, V]", UpdateFunctionValues[Literal["dict", "key", "value"], Any]], 
        Mapping[Literal["dict", "key", "value"], Any]
    ]:
        """
        Create the add_values_to_be_updated_callback for optional + default logic.
        
        Handles None keys AND auto-creates missing keys with default values.
        """
        def add_values_to_be_updated_callback(
            self_ref: "XOptionalSelectionDictWithDefault[K, V]",
            update_values: UpdateFunctionValues[Literal["dict", "key", "value"], Any]
        ) -> Mapping[Literal["dict", "key", "value"], Any]:
            
            match ("dict" in update_values.submitted, "key" in update_values.submitted, "value" in update_values.submitted):
                case (True, True, True):
                    # All three values provided - pass through for validation
                    return {}
                    
                case (True, True, False):
                    # Dict and key provided - get value from dict (or None if key is None)
                    if update_values.submitted["key"] is None:
                        return {"value": None}
                    else:
                        # Auto-create default if key not in dict
                        if update_values.submitted["key"] not in update_values.submitted["dict"]:
                            _dict = dict(update_values.submitted["dict"])
                            _default_val = self_ref._get_default_value(update_values.submitted["key"])
                            _dict[update_values.submitted["key"]] = _default_val
                            return {"dict": _dict, "value": _default_val}
                        return {"value": update_values.submitted["dict"][update_values.submitted["key"]]}
                
                case (True, False, True):
                    # Dict and value provided - validate value matches current key
                    if update_values.current["key"] is None:
                        if update_values.submitted["value"] is not None:
                            raise ValueError(f"Value {update_values.submitted['value']} is not None when key is None")
                        return {}
                    else:
                        # Allow None dict to pass through
                        if update_values.submitted["dict"] is not None:
                            if update_values.submitted["value"] != update_values.submitted["dict"][update_values.current["key"]]:
                                raise ValueError(f"Value {update_values.submitted['value']} is not the same as the value in the dictionary {update_values.submitted['dict'][update_values.current['key']]}")
                        return {}
                
                case (True, False, False):
                    # Dict provided - get value for current key (or None if key is None)
                    if update_values.current["key"] is None:
                        return {"value": None}
                    else:
                        # Auto-create default if key not in dict
                        if update_values.current["key"] not in update_values.submitted["dict"]:
                            _dict = dict(update_values.submitted["dict"])
                            _default_val = self_ref._get_default_value(update_values.current["key"])
                            _dict[update_values.current["key"]] = _default_val
                            return {"dict": _dict, "value": _default_val}
                        return {"value": update_values.submitted["dict"][update_values.current["key"]]}
                
                case (False, True, True):
                    # Key and value provided - update dict with new value
                    if update_values.submitted["key"] is None:
                        return {}
                    else:
                        _dict = dict(update_values.current["dict"])
                        _dict[update_values.submitted["key"]] = update_values.submitted["value"]
                        return {"dict": _dict}
                
                case (False, True, False):
                    # Key provided - get value from current dict (or create default)
                    if update_values.submitted["key"] is None:
                        return {"value": None}
                    else:
                        # Auto-create default if key not in dict
                        if update_values.submitted["key"] not in update_values.current["dict"]:
                            _dict = dict(update_values.current["dict"])
                            _default_val = self_ref._get_default_value(update_values.submitted["key"])
                            _dict[update_values.submitted["key"]] = _default_val
                            return {"dict": _dict, "value": _default_val}
                        return {"value": update_values.current["dict"][update_values.submitted["key"]]}
                
                case (False, False, True):
                    # Value provided - if current key is None, value must be None, otherwise update dict
                    if update_values.current["key"] is None:
                        if update_values.submitted["value"] is not None:
                            raise ValueError(f"Value {update_values.submitted['value']} is not None when key is None")
                        return {}
                    else:
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
        Create the validate_complete_values_in_isolation_callback for optional + default selection.
        
        Validates that dict/key/value are consistent with optional and auto-create handling.
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

            if values["key"] is None:
                # Check that the value is None when the key is None
                if values["value"] is not None:
                    return False, "Value is not None when key is None"
            else:
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
        initial_key: Optional[K]
    ) -> Optional[V]:
        """
        Compute the initial value from dict and key.
        
        Returns None if key is None, returns default if key not in dict.
        """
        if initial_key is None:
            return None
        elif initial_key not in initial_dict:
            # Return default value
            return self._get_default_value(initial_key)
        else:
            return initial_dict[initial_key]

    #########################################################
    # ObservableOptionalDefaultSelectionDictProtocol implementation
    #########################################################

    #-------------------------------- Key --------------------------------

    @property
    def key_hook(self) -> "Hook[Optional[K]]":
        """Get the key hook."""
        return self._primary_hooks["key"] # type: ignore
    
    @property
    def key(self) -> Optional[K]:
        """Get the current key."""
        return self._primary_hooks["key"].value # type: ignore

    @key.setter
    def key(self, value: Optional[K]) -> None:
        """Set the current key."""
        success, msg = self._submit_value("key", value)
        if not success:
            raise ValueError(msg)
    
    def change_key(self, new_value: Optional[K]) -> None:
        """Change the current key."""
        success, msg = self._submit_value("key", new_value)
        if not success:
            raise ValueError(msg)
    
    #-------------------------------- Value --------------------------------
    
    @property
    def value_hook(self) -> "Hook[Optional[V]]":
        """Get the value hook."""
        return self._primary_hooks["value"] # type: ignore
    
    @property
    def value(self) -> Optional[V]:
        """Get the current value."""
        return self._primary_hooks["value"].value # type: ignore

    @value.setter
    def value(self, value: Optional[V]) -> None:
        """Set the current value."""
        success, msg = self._submit_value("value", value)
        if not success:
            raise ValueError(msg)
    
    def change_value(self, new_value: Optional[V]) -> None:
        """Change the current value."""
        success, msg = self._submit_value("value", new_value)
        if not success:
            raise ValueError(msg)

    #-------------------------------- Convenience methods -------------------

    def change_dict_and_key(self, new_dict_value: Mapping[K, V], new_key_value: Optional[K]) -> None:
        """Change the dictionary and key behind this hook."""
        success, msg = self._submit_values({"dict": new_dict_value, "key": new_key_value})
        if not success:
            raise SubmissionError(msg, {"dict": new_dict_value, "key": new_key_value}, "dict and key")
    
    #------------------------------------------------------------------------