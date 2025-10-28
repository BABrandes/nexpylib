from typing import Literal, TypeVar, Generic, Mapping, Any, Callable, Optional, Self
from logging import Logger

from .x_dict_selection_base import XDictSelectionBase
from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from .protocols import XOptionalSelectionDictProtocol
from ...core.nexus_system.update_function_values import UpdateFunctionValues
from ...core.nexus_system.submission_error import SubmissionError

K = TypeVar("K")
V = TypeVar("V")

class XOptionalSelectionDict(
    XDictSelectionBase[K, V, Optional[K], Optional[V]], 
    XOptionalSelectionDictProtocol[K, V], 
    Generic[K, V]
):
    """

    
    Valid Key Combinations:
    ┌─────────────────┬──────────────────────────┬──────────────────────────┐
    │                 │    if key in dict        │  if key not in dict      │
    ├─────────────────┼──────────────────────────┼──────────────────────────┤
    │ if key is       │                          │                          │
    │ not None        │           ✓              │         error            │
    ├─────────────────┼──────────────────────────┼──────────────────────────┤
    │ if key is       │                          │                          │
    │ None            │      None (value)        │      None (value)        │
    └─────────────────┴──────────────────────────┴──────────────────────────┘
    
    **Optional Behavior:**
    - If key is None, then value must be None
    - If key is not None, then value must match the dictionary value at that key
    - Allows setting value to None even when key is not None (for flexibility)
    

    """

    def _create_add_values_callback(self) -> Callable[[UpdateFunctionValues[Literal["dict", "key", "value"], Any]], Mapping[Literal["dict", "key", "value"], Any]]:
        """
        Create the add_values_to_be_updated_callback for optional selection logic.
        
        This callback handles None keys and ensures value consistency.
        """
        def add_values_to_be_updated_callback(
            update_values: UpdateFunctionValues[Literal["dict", "key", "value"], Any]
        ) -> Mapping[Literal["dict", "key", "value"], Any]:
            
            match ("dict" in update_values.submitted, "key" in update_values.submitted, "value" in update_values.submitted):
                case (True, True, True):
                    # All three values provided - validate consistency
                    # Note: None dict will be caught by validation callback
                    if update_values.submitted["key"] is None:
                        if update_values.submitted["value"] is not None:
                            raise ValueError(f"Value must be None when key is None")
                        return {}
                    else:
                        # Allow None dict to pass through - validation will catch it
                        if update_values.submitted["dict"] is not None:
                            if update_values.submitted["key"] not in update_values.submitted["dict"]:
                                raise KeyError(f"Key {update_values.submitted['key']} not in dictionary")
                            expected_value = update_values.submitted["dict"][update_values.submitted["key"]]
                            if update_values.submitted["value"] != expected_value:
                                return {"value": expected_value}
                        return {}
                        
                case (True, True, False):
                    # Dict and key provided - get value from dict
                    if update_values.submitted["key"] is None:
                        return {"value": None}
                    else:
                        # Allow None dict to pass through - validation will catch it
                        if update_values.submitted["dict"] is not None:
                            if update_values.submitted["key"] not in update_values.submitted["dict"]:
                                raise KeyError(f"Key {update_values.submitted['key']} not in dictionary")
                            return {"value": update_values.submitted["dict"][update_values.submitted["key"]]}
                        return {}
                
                case (True, False, True):
                    # Dict and value provided - validate value matches current key
                    if update_values.current["key"] is None:
                        if update_values.submitted["value"] is not None:
                            raise ValueError(f"Value {update_values.submitted['value']} is not None when key is None")
                        return {}
                    else:
                        # Allow None dict to pass through - validation will catch it
                        if update_values.submitted["dict"] is not None:
                            if update_values.submitted["value"] != update_values.submitted["dict"][update_values.current["key"]]:
                                raise ValueError(f"Value {update_values.submitted['value']} is not the same as the value in the dictionary {update_values.submitted['dict'][update_values.current['key']]}")
                        return {}
                
                case (True, False, False):
                    # Dict provided - get value for current key
                    if update_values.current["key"] is None:
                        return {"value": None}
                    else:
                        # Allow None dict to pass through - validation will catch it
                        if update_values.submitted["dict"] is not None:
                            return {"value": update_values.submitted["dict"][update_values.current["key"]]}
                        return {}
                
                case (False, True, True):
                    # Key and value provided - update dict with new value
                    if update_values.submitted["key"] is None:
                        return {}
                    else:
                        _dict = dict(update_values.current["dict"])
                        _dict[update_values.submitted["key"]] = update_values.submitted["value"]
                        return {"dict": _dict}
                
                case (False, True, False):
                    # Key provided - get value from current dict
                    if update_values.submitted["key"] is None:
                        return {"value": None}
                    else:
                        if update_values.submitted["key"] not in update_values.current["dict"]:
                            raise KeyError(f"Key {update_values.submitted['key']} not in dictionary")
                        return {"value": update_values.current["dict"][update_values.submitted["key"]]}
                
                case (False, False, True):
                    # Value provided - if current key is None, value must be None, otherwise update dict
                    if update_values.current["key"] is None:
                        if update_values.submitted["value"] is not None:
                            raise ValueError(f"Value {update_values.submitted['value']} is not None when key is None")
                        else:
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
        Create the validate_complete_values_in_isolation_callback for optional selection.
        
        Validates that dict/key/value are consistent with optional None handling.
        """
        def validate_complete_values_in_isolation_callback(
            values: Mapping[Literal["dict", "key", "value"], Any]
        ) -> tuple[bool, str]:
            
            # Check that all three values are in the values
            if "dict" not in values:
                return False, "Dict not in values"
            if "key" not in values:
                return False, "Key not in values"
            if "value" not in values:
                return False, "Value not in values"
            
            # Check that the dictionary is not None
            if values["dict"] is None or not isinstance(values["dict"], Mapping):
                return False, "Dictionary is None or not a mapping"

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
        
        Returns None if key is None, otherwise returns dict[key].
        """
        if initial_key is None:
            return None
        else:
            return initial_dict[initial_key]

    #########################################################
    # ObservableOptionalSelectionDictProtocol implementation
    #########################################################

    #-------------------------------- Key --------------------------------

    @property
    def key_hook(self) -> OwnedWritableHook[Optional[K], Self]:
        """Get the key hook."""
        return self._primary_hooks["key"]
    

    @property
    def key(self) -> Optional[K]:
        """Get the current key."""
        return self._value_wrapped("key") # type: ignore
    
    @key.setter
    def key(self, value: Optional[K]) -> None:
        """Set the current key."""
        self.change_key(value)

    def change_key(self, value: Optional[K], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Change the current key."""
        success, msg = self._submit_value("key", value, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, value, "key")

    #-------------------------------- Value --------------------------------

    @property
    def value_hook(self) -> OwnedWritableHook[Optional[V], Self]:
        """Get the value hook."""
        return self._primary_hooks["value"]
    
    @property
    def value(self) -> Optional[V]:
        """Get the current value."""
        return self._value_wrapped("value") # type: ignore
    
    @value.setter
    def value(self, value: Optional[V]) -> None:
        self.change_value(value)
    
    def change_value(self, value: Optional[V], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Change the current value."""
        success, msg = self._submit_value("value", value, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, value, "value")

    #-------------------------------- Convenience methods -------------------
    
    def change_dict_and_key(self, dict_value: Mapping[K, V], key_value: Optional[K], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Change the dictionary and key behind this hook."""
        success, msg = self._submit_values({"dict": dict_value, "key": key_value}, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, {"dict": dict_value, "key": key_value}, "dict and key")

    #------------------------------------------------------------------------