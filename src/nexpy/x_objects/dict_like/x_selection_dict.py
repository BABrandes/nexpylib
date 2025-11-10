from typing import Literal, TypeVar, Generic, Mapping, Any, Callable, Optional, Self
from logging import Logger

from .x_dict_selection_base import XDictSelectionBase
from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from .protocols import XSelectionDictProtocol
from ...core.nexus_system.update_function_values import UpdateFunctionValues
from ...core.nexus_system.submission_error import SubmissionError

K = TypeVar("K")
V = TypeVar("V")

class XSelectionDict(XDictSelectionBase[K, V, K, V], XSelectionDictProtocol[K, V], Generic[K, V]):
    """
    Reactive dictionary with required key selection and synchronized value access.
    
    XDictSelect[K, V] (alias: XSelectionDict[K, V]) maintains a dictionary, selected key,
    and corresponding value, all synchronized reactively. The key must always exist in
    the dictionary. Generic types K and V specify key and value types.

    Type Parameters
    ---------------
    K : TypeVar
        The type of dictionary keys. Must be hashable.
    V : TypeVar
        The type of dictionary values.

    Valid States
    ------------
    ┌─────────────────┬──────────────────────────┬──────────────────────────┐
    │                 │    if key in dict        │  if key not in dict      │
    ├─────────────────┼──────────────────────────┼──────────────────────────┤
    │ if key is       │                          │                          │
    │ not None        │           ✓              │         error            │
    ├─────────────────┼──────────────────────────┼──────────────────────────┤
    │ if key is       │                          │                          │
    │ None            │         error            │         error            │
    └─────────────────┴──────────────────────────┴──────────────────────────┘
    
    Synchronization
    ---------------
    - When dict or key changes → value is automatically updated
    - When value changes → dictionary is updated at current key
    - When key changes → value is updated to match new key

    See Also
    --------
    XDictSelectOptional : Optional key selection (can be None)
    XDictSelectDefault : Required key with default value
    XSetSingleSelect : Set-based selection (no value mapping)
    """

    def _create_add_values_callback(self) -> Callable[[UpdateFunctionValues[Literal["dict", "key", "value"], Any]], Mapping[Literal["dict", "key", "value"], Any]
    ]:
        """
        Create the add_values_to_be_updated_callback for selection logic.
        
        This callback ensures that key must always exist in dict.
        """
        def add_values_to_be_updated_callback(
            update_values: UpdateFunctionValues[Literal["dict", "key", "value"], Any]
        ) -> Mapping[Literal["dict", "key", "value"], Any]:
            
            match ("dict" in update_values.submitted, "key" in update_values.submitted, "value" in update_values.submitted):
                case (True, True, True):
                    # All three values provided - validate consistency
                    if update_values.submitted["key"] not in update_values.submitted["dict"]:
                        raise KeyError(f"Key {update_values.submitted['key']} not in dictionary")
                    expected_value = update_values.submitted["dict"][update_values.submitted["key"]]
                    if update_values.submitted["value"] != expected_value:
                        return {"value": expected_value}
                    return {}
                    
                case (True, True, False):
                    # Dict and key provided - get value from dict
                    if update_values.submitted["key"] not in update_values.submitted["dict"]:
                        raise KeyError(f"Key {update_values.submitted['key']} not in dictionary")
                    return {"value": update_values.submitted["dict"][update_values.submitted["key"]]}
                
                case (True, False, True):
                    # Dict and value provided - validate value matches current key
                    if update_values.submitted["value"] != update_values.submitted["dict"][update_values.current["key"]]:
                        raise ValueError(f"Value {update_values.submitted['value']} is not the same as the value in the dictionary {update_values.submitted['dict'][update_values.current['key']]}")
                    return {}
                
                case (True, False, False):
                    # Dict provided - get value for current key
                    if update_values.current["key"] not in update_values.submitted["dict"]:
                        raise KeyError(f"Current key {update_values.current['key']} not in submitted dictionary")
                    return {"value": update_values.submitted["dict"][update_values.current["key"]]}
                
                case (False, True, True):
                    # Key and value provided - update dict with new value
                    if update_values.submitted["key"] not in update_values.current["dict"]:
                        raise KeyError(f"Key {update_values.submitted['key']} not in current dictionary")
                    _dict = dict(update_values.current["dict"])
                    _dict[update_values.submitted["key"]] = update_values.submitted["value"]
                    return {"dict": _dict}
                
                case (False, True, False):
                    # Key provided - get value from current dict
                    if update_values.submitted["key"] not in update_values.current["dict"]:
                        raise KeyError(f"Key {update_values.submitted['key']} not in dictionary")
                    return {"value": update_values.current["dict"][update_values.submitted["key"]]}
                
                case (False, False, True):
                    # Value provided - update dict at current key
                    current_dict = update_values.current["dict"]
                    _dict = dict(current_dict)
                    _dict[update_values.current["key"]] = update_values.submitted["value"]
                    return {"dict": _dict}
                
                case (False, False, False):
                    # Nothing provided - no updates needed
                    return {}

            raise ValueError("Invalid keys")
        
        return add_values_to_be_updated_callback

    def _create_validation_callback(self) -> Callable[[Mapping[Literal["dict", "key", "value"], Any]], tuple[bool, str]]:
        """
        Create the validate_complete_values_in_isolation_callback for selection.
        
        Validates that dict/key/value are consistent and key is in dict.
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

            # Check that the key is in the dictionary
            if values["key"] not in values["dict"]:
                return False, f"Key {values['key']} not in dictionary"

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
        
        Returns dict[key].
        """
        return initial_dict[initial_key]

    #########################################################
    # XSelectionDictProtocol implementation
    #########################################################

    #-------------------------------- Key --------------------------------

    @property
    def key_hook(self) -> OwnedWritableHook[K, Self]:
        """Get the key hook."""
        
        return self._primary_hooks["key"]

    @property
    def key(self) -> K:
        """Get the current key."""
        
        return self._primary_hooks["key"].value

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
        
        return self._primary_hooks["value"].value
    
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