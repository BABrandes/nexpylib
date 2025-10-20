from typing import Mapping, Generic, TypeVar

HK = TypeVar("HK")
HV = TypeVar("HV", covariant=True)

class XObjectSerializableMixin(Generic[HK, HV]):
    """
    Protocol for observables that support serialization and deserialization.
    
    This class provides a standardized interface for saving and restoring observable
    states. It enables observables to be persisted to storage (files, databases, etc.)
    and reconstructed later with the same values.
    
    The serialization system is designed to be:
    - **Simple**: Only essential state is serialized (primary hook values)
    - **Type-safe**: Generic parameters ensure type consistency
    - **Flexible**: Works with any serialization format (JSON, pickle, etc.)
    - **Complete**: Captures all necessary state for full reconstruction
    
    Type Parameters:
        HK: The type of hook keys (e.g., Literal["value"], str, etc.)
        HV: The type of hook values (e.g., int, list, dict, etc.)
    
    Architecture:
    ------------
    Observables store their state in primary hooks. The serialization system:
    1. Extracts values from primary hooks (excluding computed/secondary hooks)
    2. Returns them as a mapping of keys to values
    3. Can restore these values to a new observable instance
    
    Secondary hooks (computed values like length, count, etc.) are NOT serialized
    because they are automatically recomputed from primary values.
    
    Usage Pattern:
    -------------
    The serialization lifecycle follows these steps:
    
    1. **Create and use an observable:**
       >>> obs = ObservableSingleValue(42)
       >>> obs.value = 100
    
    2. **Serialize to get state:**
       >>> serialized_data = obs.get_values_for_serialization()
       >>> # serialized_data = {"value": 100}
    
    3. **Save to storage (your choice of format):**
       >>> import json
       >>> json.dump(serialized_data, file)  # Or pickle, YAML, etc.
    
    4. **Later, load from storage:**
       >>> serialized_data = json.load(file)
    
    5. **Create fresh observable:**
       >>> obs_restored = ObservableSingleValue(0)  # Initial value doesn't matter
    
    6. **Restore state:**
       >>> obs_restored.set_values_from_serialization(serialized_data)
       >>> # obs_restored.value == 100
    
    Implementation Requirements:
    ---------------------------
    Classes implementing this protocol must provide:
    
    1. **get_values_for_serialization() -> Mapping[HK, HV]**
       - Returns a mapping of hook keys to their current values
       - Should only include PRIMARY hook values (not computed/secondary)
       - Values should be references (not copies) for efficiency
       - Must include all state needed for complete reconstruction
    
    2. **set_values_from_serialization(values: Mapping[HK, HV]) -> None**
       - Restores observable state from serialized values
       - Should validate values if needed
       - Should update all relevant hooks atomically
       - Should NOT return anything (mutates the observable in place)
    
    Example Implementations:
    -----------------------
    
    **Simple Observable (Single Value):**
        >>> class ObservableSingleValue(ObservableSerializable[Literal["value"], T]):
        ...     def get_values_for_serialization(self):
        ...         return {"value": self._hook.value}
        ...     
        ...     def set_values_from_serialization(self, values):
        ...         self.submit_values(values)
    
    **Complex Observable (Multiple Values):**
        >>> class ObservableRootedPaths(ObservableSerializable[str, Path|str|None]):
        ...     def get_values_for_serialization(self):
        ...         # Return root path and relative paths only
        ...         result = {"root_path": self._root_path}
        ...         for key in self._element_keys:
        ...             result[key] = self.get_relative_path(key)
        ...         return result
        ...     
        ...     def set_values_from_serialization(self, values):
        ...         # Rebuild internal state from serialized values
        ...         self.submit_values(self._prepare_values(values))
    
    Important Notes:
    ---------------
    - **Reference vs Copy**: Methods return/accept references for efficiency.
      The caller should not modify returned values.
    
    - **Validation**: Implementations may validate values during deserialization
      to ensure consistency.
    
    - **Atomic Updates**: Deserialization should update all values atomically
      to maintain consistency.
    
    - **Secondary Hooks**: Never serialize computed/secondary values. They are
      automatically recomputed from primary values.
    
    - **Bindings**: Serialization does NOT preserve bindings between observables.
      Only the current values are saved. Bindings must be recreated manually.
    
    Testing:
    -------
    All serializable observables should follow this test pattern:
    
        >>> # 1. Create and modify
        >>> obs = ObservableXYZ(initial_value)
        >>> obs.modify_state()
        >>> expected = obs.get_state()
        >>> 
        >>> # 2. Serialize
        >>> data = obs.get_values_for_serialization()
        >>> 
        >>> # 3. Delete original
        >>> del obs
        >>> 
        >>> # 4. Create fresh instance
        >>> obs_new = ObservableXYZ(different_value)
        >>> 
        >>> # 5. Deserialize
        >>> obs_new.set_values_from_serialization(data)
        >>> 
        >>> # 6. Verify
        >>> assert obs_new.get_state() == expected
    
    See Also:
    --------
    - ObservableSingleValue: Simple serialization example
    - ObservableList, ObservableDict, ObservableSet: Collection serialization
    - ObservableRootedPaths: Complex multi-value serialization
    - ObservableSelectionEnum: Enum-based serialization
    """

    def get_values_for_serialization(self) -> Mapping[HK, HV]:
        """
        Get the observable's state as a mapping for serialization.
        
        This method extracts all primary hook values needed to reconstruct
        the observable's state. The returned mapping contains references to
        the actual values (not copies).
        
        Returns:
            Mapping[HK, HV]: A mapping of hook keys to their current values.
                            Only primary (non-computed) values are included.
        
        Example:
            >>> obs = ObservableSingleValue(42)
            >>> obs.value = 100
            >>> data = obs.get_values_for_serialization()
            >>> data
            {'value': 100}
        
        Note:
            - The returned values are REFERENCES, not copies
            - Only primary hooks are included (no computed/secondary values)
            - The caller should not modify the returned values
        """
        ...

    def set_values_from_serialization(self, values: Mapping[HK, HV]) -> None:
        """
        Restore the observable's state from serialized values.
        
        This method updates the observable to match the provided state. It should
        validate values if necessary and update all hooks atomically to maintain
        consistency.
        
        Args:
            values: A mapping of hook keys to values, as previously obtained
                   from get_values_for_serialization()
        
        Raises:
            ValueError: If the values are invalid or incompatible
        
        Example:
            >>> obs = ObservableSingleValue(0)
            >>> data = {'value': 100}
            >>> obs.set_values_from_serialization(data)
            >>> obs.value
            100
        
        Note:
            - Values are validated before being applied
            - All hooks are updated atomically
            - Secondary/computed hooks are automatically recalculated
            - This method mutates the observable in place
        """
        ...