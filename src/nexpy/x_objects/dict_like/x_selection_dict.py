from typing import Literal, TypeVar, Generic, Mapping, Any, Callable

from .x_dict_selection_base import XDictSelectionBase, Hook
from .protocols import XSelectionDictProtocol
from ...core.nexus_system.update_function_values import UpdateFunctionValues
from ...core.nexus_system.submission_error import SubmissionError

K = TypeVar("K")
V = TypeVar("V")

class XSelectionDict(XDictSelectionBase[K, V, K, V], XSelectionDictProtocol[K, V], Generic[K, V]):
    """
 
    Valid Key Combinations:
    ┌─────────────────┬──────────────────────────┬──────────────────────────┐
    │                 │    if key in dict        │  if key not in dict      │
    ├─────────────────┼──────────────────────────┼──────────────────────────┤
    │ if key is       │                          │                          │
    │ not None        │           ✓              │         error            │
    ├─────────────────┼──────────────────────────┼──────────────────────────┤
    │ if key is       │                          │                          │
    │ None            │         error            │         error            │
    └─────────────────┴──────────────────────────┴──────────────────────────┘
    
    The X object ensures that these three components stay synchronized:
    - When dict or key changes, value is automatically updated
    - When value changes, the dictionary is updated at the current key
    - When key changes, value is updated to match the new key
    
    """

    def _create_add_values_callback(self) -> Callable[["XSelectionDict[K, V]", UpdateFunctionValues[Literal["dict", "key", "value"], Any]], Mapping[Literal["dict", "key", "value"], Any]
    ]:
        """
        Create the add_values_to_be_updated_callback for selection logic.
        
        This callback ensures that key must always exist in dict.
        """
        def add_values_to_be_updated_callback(
            self_ref: "XSelectionDict[K, V]",
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
                raise KeyError(f"Key {values['key']} not in dictionary")

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
    def key_hook(self) -> "Hook[K]":
        """Get the key hook."""
        
        return self._primary_hooks["key"] # type: ignore

    @property
    def key(self) -> K:
        """Get the current key."""
        
        return self._primary_hooks["key"].value # type: ignore

    @key.setter
    def key(self, value: K) -> None:
        """Set the current key."""
        
        success, msg = self._submit_value("key", value)
        if not success:
            raise ValueError(msg)

    def change_key(self, new_value: K) -> None:
        """Change the current key."""

        success, msg = self._submit_value("key", new_value)
        if not success:
            raise SubmissionError(msg, new_value, "key")

    #-------------------------------- Value --------------------------------

    @property
    def value_hook(self) -> "Hook[V]":
        """Get the value hook."""
        
        return self._primary_hooks["value"] # type: ignore
    
    @property
    def value(self) -> V:
        """Get the current value."""
        
        return self._primary_hooks["value"].value # type: ignore
    
    @value.setter
    def value(self, value: V) -> None:
        """Set the current value."""
        
        success, msg = self._submit_value("value", value)
        if not success:
            raise ValueError(msg)

    def change_value(self, new_value: V) -> None:
        """Change the current value."""
        
        success, msg = self._submit_value("value", new_value)
        if not success:
            raise SubmissionError(msg, new_value, "value")

    #-------------------------------- Convenience methods -------------------
    
    def change_dict_and_key(self, new_dict_value: Mapping[K, V], new_key_value: K) -> None:
        """Change the dictionary and key behind this hook."""
        
        success, msg = self._submit_values({"dict": new_dict_value, "key": new_key_value})
        if not success:
            raise SubmissionError(msg, {"dict": new_dict_value, "key": new_key_value}, "dict and key")

    #------------------------------------------------------------------------