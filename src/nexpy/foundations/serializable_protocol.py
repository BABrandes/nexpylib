from typing import Mapping, TypeVar, Protocol, runtime_checkable

HK = TypeVar("HK")
HV = TypeVar("HV")

@runtime_checkable
class SerializableProtocol(Protocol[HK, HV]):
    """
    Protocol for object state that support serialization and deserialization.
    
    This protocol provides a standardized interface for saving and restoring object
    state. It enables object state to be persisted to storage (files, databases, etc.)
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
    NexPy objects store their state in primary hooks. The serialization system:
    1. Extracts values from primary hooks (excluding computed/secondary hooks)
    2. Returns them as a mapping of keys to values
    3. Can restore these values to a new NexPy object instance
    
    Secondary hooks (computed values like length, count, etc.) are NOT serialized
    because they are automatically recomputed from primary values.
    
    Usage Pattern:
    -------------
    The serialization lifecycle follows these steps:
    
    1. **Create and use a NexPy object:**
       >>> obs = XValue(42)
       >>> obs.value = 100
    
    2. **Serialize to get state:**
       >>> serialized_data = obs.get_values_for_serialization()
       >>> # serialized_data = {"value": 100}
    
    3. **Save to storage (your choice of format):**
       >>> import json
       >>> json.dump(serialized_data, file)  # Or pickle, YAML, etc.
    
    4. **Later, load from storage:**
       >>> serialized_data = json.load(file)
    
    5. **Create fresh NexPy object:**
       >>> obs_restored = XValue(0)  # Initial value doesn't matter
    
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
       - Restores NexPy object state from serialized values
       - Should validate values if needed
       - Should update all relevant hooks atomically
       - Should NOT return anything (mutates the NexPy object in place)
    
    Example Implementations:
    -----------------------
    
    **Simple X Object (Single Value):**
        >>> class XValue(XBase[Literal["value"], T]):
        ...     def get_values_for_serialization(self):
        ...         return {"value": self._hook.value}
        ...     
        ...     def set_values_from_serialization(self, values):
        ...         self.submit_values(values)
    
    **Complex X Object (Multiple Values):**
        >>> class XRootedPaths(XBase[str, Path|str|None]):
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
    
    - **Fusion Domains**: Serialization does NOT preserve hook fusion/joins.
      Only the current values are saved. Fusions must be recreated manually.
    
    Testing:
    -------
    All serializable X objects should follow this test pattern:
    
        >>> # 1. Create and modify
        >>> obj = XValue(initial_value)
        >>> obj.modify_state()
        >>> expected = obj.get_state()
        >>> 
        >>> # 2. Serialize
        >>> data = obj.get_values_for_serialization()
        >>> 
        >>> # 3. Delete original
        >>> del obj
        >>> 
        >>> # 4. Create fresh instance
        >>> obj_new = XValue(different_value)
        >>> 
        >>> # 5. Deserialize
        >>> obj_new.set_values_from_serialization(data)
        >>> 
        >>> # 6. Verify
        >>> assert obj_new.get_state() == expected
    
    See Also:
    --------
    - XValue: Simple serialization example
    - XList, XDict, XSet: Collection serialization
    - XRootedPaths: Complex multi-value serialization
    - XDictSelect, XSetSingleSelect: Selection serialization
    """

    def get_values_for_serialization(self) -> Mapping[HK, HV]:
        """
        Get the NexPy object's state as a mapping for serialization.
        
        This method extracts all primary hook values needed to reconstruct
        the NexPy object's state. The returned mapping contains references to
        the actual values (not copies).
        
        Returns:
            Mapping[HK, HV]: A mapping of hook keys to their current values.
                            Only primary (non-computed) values are included.
        
        Example:
            >>> obj = XValue(42)
            >>> obj.value = 100
            >>> data = obj.get_values_for_serialization()
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
        Restore the NexPy object's state from serialized values.
        
        This method updates the NexPy object to match the provided state. It should
        validate values if necessary and update all hooks atomically to maintain
        consistency.
        
        Args:
            values: A mapping of hook keys to values, as previously obtained
                   from get_values_for_serialization()
        
        Raises:
            ValueError: If the values are invalid or incompatible
        
        Example:
            >>> obj = XValue(0)
            >>> data = {'value': 100}
            >>> obj.set_values_from_serialization(data)
            >>> obj.value
            100
        
        Note:
            - Values are validated before being applied
            - All hooks are updated atomically
            - Secondary/computed hooks are automatically recalculated
            - This method mutates the NexPy object in place
        """
        ...