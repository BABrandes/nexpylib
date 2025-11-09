from typing import Callable, Generic, Mapping, Optional, TypeVar, Literal, Self, Any
from logging import Logger

from ..core.hooks import OwnedWritableHook, OwnedReadOnlyHook, OwnedHookProtocol, HookProtocol
from ..core.nexus_system.nexus import Nexus
from ..core.nexus_system.nexus_manager import NexusManager
from ..core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from ..core.nexus_system.submission_error import SubmissionError

from .x_base import XBase
from ..core.nexus_system.update_function_values import UpdateFunctionValues

PHK = TypeVar("PHK")
SHK = TypeVar("SHK")
PHV = TypeVar("PHV", covariant=True)
SHV = TypeVar("SHV", covariant=True)

class XCompositeBase(XBase[PHK|SHK, PHV|SHV], Generic[PHK, SHK, PHV, SHV]):
    """
    Base class for composite X objects (multiple hooks) in the hook-based architecture.

    Generic type parameters:
        PHK: The type of the primary hook keys
        SHK: The type of the secondary hook keys
        PHV: The type of the primary hook values
        SHV: The type of the secondary hook values

    This class combines BaseListening and BaseCarriesHooks to provide the complete
    interface for observables. It implements a flexible hook-based system that replaces
    traditional binding approaches with a more powerful and extensible architecture.
    
    **Architecture Overview:**
    
    The BaseXObject uses a dual-hook system:
    
    1. **Primary Hooks (PHK -> PHV)**: Represent the core state of the X object.
       These are the main data components that can be directly modified and validated.
       
    2. **Secondary Hooks (SHK -> SHV)**: Represent derived/computed values calculated
       from primary hooks. These are read-only and automatically updated when primary
       values change.
    
    **Key Components:**
    
    - **Hook Management**: Manages both primary and secondary hooks with type safety
    - **Value Submission**: Uses NexusManager for coordinated value updates and validation
    - **Custom Logic**: Supports validation, value completion, and invalidation callbacks
    - **Listener Support**: Integrates with BaseListening for change notifications
    - **Type Safety**: Full generic type support for keys and values
    
    **Core Callback System:**
    
    1. **internal_verification_method**: Validates that all primary values together represent
       a valid state. Called first during validation, before any state changes are applied.
       Operates on primary values only.
       
    2. **custom_validator**: Additional validation on both primary and secondary values.
       Called after internal_verification_method. Operates on all hook values (primary + secondary).
       
    3. **secondary_hook_callbacks**: Calculate derived values from primary values.
       These are automatically recalculated when primary values change.
       
    4. **add_values_to_be_updated_callback**: Adds additional values to complete
       partial updates (e.g., updating a dict when a dict value changes).
       
    5. **invalidate_callback**: Called after successful state changes for external
       actions outside the hook system.
    
    **Type Parameters:**
    - `PHK`: Type of primary hook keys
    - `SHK`: Type of secondary hook keys  
    - `PHV`: Type of primary hook values
    - `SHV`: Type of secondary hook values
    - `O`: The X object class type (for self-referential typing)
    
    **Usage Examples:**
    
    1. **Basic Observable Creation:**
        ```python
        from observables import BaseXObject
        
        # Create observable with primary hooks
        obs = BaseXObject({
            'name': 'John',
            'age': 30
        })
        
        # Add secondary hooks
        obs = BaseXObject(
            initial_component_values_or_hooks={'name': 'John', 'age': 30},
            secondary_hook_callbacks={
                'greeting': lambda values: f"Hello, {values['name']}!"
            }
        )
        ```
    
    2. **With Validation:**
        ```python
        def validate_person(values):
            if values['age'] < 0:
                return False, "Age cannot be negative"
            return True, "Valid person"
        
        obs = BaseXObject(
            initial_component_values_or_hooks={'name': 'John', 'age': 30},
            internal_verification_method=validate_person
        )
        ```
    
    3. **With Value Completion:**
        ```python
        def complete_dict_updates(self, current, submitted):
            additional = {}
            if 'dict_value' in submitted and 'dict' in current:
                new_dict = current['dict'].copy()
                new_dict[self.current_key] = submitted['dict_value']
                additional['dict'] = new_dict
            return additional
        
        obs = BaseXObject(
            initial_component_values_or_hooks={'dict': {}, 'dict_value': 'test'},
            add_values_to_be_updated_callback=complete_dict_updates
        )
        ```
    
    **Implementation Requirements:**
    
    Subclasses must implement the abstract methods from BaseCarriesHooks:
    - `_get_hook(key)`: Get hook by key
    - `_get_value_reference_of_hook(key)`: Get hook value by key
    - `_get_hook_keys()`: Get all hook keys
    - `_get_hook_key(hook_or_nexus)`: Get key for hook/nexus
    
    **Error Handling:**
    - Raises ValueError for overlapping primary/secondary keys
    - Raises ValueError for failed validation
    - Logs errors from callbacks but doesn't raise them
    - Provides detailed error messages for debugging
    
    **Performance Considerations:**
    - Uses cached key sets for O(1) lookups
    - Lazy evaluation of secondary values
    - Efficient equality checking via NexusManager
    - Minimal memory overhead for hook management
    
    **Related Classes:**
    - XEnum: X object wrapper for enum values
    - XDict: X object wrapper for dictionaries
    - XBlockNone: X object wrapper for blocks of none and non-none values
    - XList: X object wrapper for lists
    - XSet: X object wrapper for sets
    - XAnyValue/XValue: X object wrapper for single values
    - XSelectionSet/XSetSelect: X object wrapper for selection options
    """

    def __init__(
            self,
            *,
            initial_hook_values: Mapping[PHK, PHV|HookProtocol[PHV]],
            compute_missing_primary_values_callback: Optional[Callable[[UpdateFunctionValues[PHK, PHV]], Mapping[PHK, PHV]]],
            compute_secondary_values_callback: Optional[Mapping[SHK, Callable[[Mapping[PHK, PHV]], SHV]]],
            validate_complete_primary_values_callback: Optional[Callable[[Mapping[PHK, PHV]], tuple[bool, str]]],
            invalidate_after_update_callback: Optional[Callable[[], None]] = None,
            custom_validator: Optional[Callable[[Mapping[PHK|SHK, PHV|SHV]], tuple[bool, str]]] = None,
            output_value_wrapper: Optional[Mapping[PHK|SHK, Callable[[PHV|SHV], PHV|SHV]]] = None,
            logger: Optional[Logger] = None,
            nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER,
            preferred_publish_mode: Literal["async", "sync", "direct", "off"] = "async"):
        """
        Initialize the XCompositeBase with hook-based architecture.
        
        This is the base class for many X objects in the library. The first four parameters
        are mandatory to ensure all subclasses explicitly define their core structure, though
        they may be set to None if not needed for a particular implementation.

        Parameters
        ----------
        initial_hook_values : Mapping[PHK, PHV|OwnedHookProtocol[PHV]] (required)
            Initial values or hooks for primary hooks.
            Can contain either direct values (PHV) or OwnedHookProtocol objects that will be connected.
            These represent the primary state of the X object.
            This parameter is mandatory and must always be provided.
            
        compute_missing_primary_values_callback : Optional[Callable[[UpdateFunctionValues[PHK, PHV]], Mapping[PHK, PHV]]] (required)
            Function that adds additional primary values to make a potentially invalid
            submission become valid. Called during value submission to complete partial updates.
            This parameter is mandatory but can be set to None if not needed.
            
            The function signature is:
            ``(update_values: UpdateFunctionValues[PHK, PHV]) -> Mapping[PHK, PHV]``
            
            Parameters
            ----------
            update_values : UpdateFunctionValues[PHK, PHV]
                Object containing current and submitted values
                
            Returns
            -------
            Mapping[PHK, PHV]
                Additional primary values to include in the submission
                
            Notes
            -----
            Use cases:
            - Dictionary management: When changing a dict value, also update the dict itself
            - Composite updates: Ensure related values are updated together
            - Dependency resolution: Add missing values based on submitted changes
            
            Examples
            --------
            >>> def complete_dict_updates(update_values):
            ...     additional = {}
            ...     if 'dict_value' in update_values.submitted:
            ...         # Update the dict when a dict value changes
            ...         new_dict = update_values.current['dict'].copy()
            ...         new_dict[update_values.current['key']] = update_values.submitted['dict_value']
            ...         additional['dict'] = new_dict
            ...     return additional
            
        compute_secondary_values_callback : Optional[Mapping[SHK, Callable[[Mapping[PHK, PHV]], SHV]]] (required)
            Mapping of secondary hook keys to calculation functions.
            These functions compute derived values from primary values. Secondary hooks are
            read-only and automatically updated when primary values change.
            This parameter is mandatory but can be set to None if there are no secondary values.
            
            The function signature for each callback is:
            ``(primary_values: Mapping[PHK, PHV]) -> SHV``
            
            Parameters
            ----------
            primary_values : Mapping[PHK, PHV]
                Current values of all primary hooks
                
            Returns
            -------
            SHV
                The calculated secondary value
                
            Notes
            -----
            - Only sending: Secondary hooks send values but don't receive direct updates
            - Equality checks: Changes are detected using nexus_manager.is_equal()
            - Precision tolerance: May change minimally due to floating-point precision
            - Automatic updates: Recalculated whenever primary values change
            
            Examples
            --------
            >>> secondary_callbacks = {
            ...     'length': lambda values: len(values['items']),
            ...     'sum': lambda values: sum(values['numbers']),
            ...     'average': lambda values: sum(values['numbers']) / len(values['numbers'])
            ... }
            
        validate_complete_primary_values_callback : Optional[Callable[[Mapping[PHK, PHV]], tuple[bool, str]]] (required)
            Validation function that verifies all primary values together represent
            a valid state. Called FIRST during validation, before custom_validator.
            Operates on primary values only.
            This parameter is mandatory but can be set to None if no validation is needed.
            
            The function signature is:
            ``(primary_values: Mapping[PHK, PHV]) -> tuple[bool, str]``
            
            Parameters
            ----------
            primary_values : Mapping[PHK, PHV]
                Complete mapping of all primary hook values
                
            Returns
            -------
            tuple[bool, str]
                (is_valid, message) where:
                - is_valid: True if the state is valid, False otherwise
                - message: Human-readable description of validation result
                
            Examples
            --------
            >>> def validate_dict_state(values):
            ...     if 'dict' in values and 'key' in values:
            ...         return values['key'] in values['dict'], "Key must exist in dict"
            ...     return True, "Valid state"
            
        invalidate_after_update_custom_callback : Optional[Callable[[], None]], optional
            Optional function called after a new valid state is established.
            Used for further actions outside the hook system, such as triggering external
            events or updating dependent systems.
            
            The function signature is:
            ``() -> None``
            
            Notes
            -----
            - Called only on new valid states: Executed after successful validation
            - External actions: Use for side effects outside the hook system
            - Error handling: Exceptions are caught and logged
            - No return value: Function should not return anything
            
            Examples
            --------
            >>> def on_state_change():
            ...     # Trigger external events
            ...     external_system.notify_change()
            ...     # Update UI
            ...     ui.refresh()
            ...     # Log state change
            ...     logger.info("X object state changed")
            
        custom_validator : Optional[Callable[[Mapping[PHK|SHK, PHV|SHV]], tuple[bool, str]]], optional
            Optional validation function that validates all hook values (primary and secondary).
            Called SECOND during validation, after validate_complete_primary_values_callback and after 
            secondary values have been computed. This allows validation across all values.
            
            The function signature is:
            ``(all_values: Mapping[PHK|SHK, PHV|SHV]) -> tuple[bool, str]``
            
            Parameters
            ----------
            all_values : Mapping[PHK|SHK, PHV|SHV]
                Complete mapping of all hook values (primary + secondary)
                
            Returns
            -------
            tuple[bool, str]
                (is_valid, message) where:
                - is_valid: True if the state is valid, False otherwise
                - message: Human-readable description of validation result
                
            Notes
            -----
            - Called after validate_complete_primary_values_callback
            - Has access to both primary and secondary values
            - Useful for cross-validation between primary and derived values
            
            Examples
            --------
            >>> def validate_all_values(values):
            ...     # Can validate across primary and secondary values
            ...     if values.get('total') != sum(values.get('items', [])):
            ...         return False, "Total doesn't match sum of items"
            ...     return True, "Valid state"
            
        output_value_wrapper : Optional[Mapping[PHK|SHK, Callable[[PHV|SHV], PHV|SHV]]], optional
            Optional mapping of hook keys to wrapper functions that transform values when
            accessed via value_by_key(). Does not affect internal hook values.
            
            The function signature for each wrapper is:
            ``(value: PHV|SHV) -> PHV|SHV``
            
            Notes
            -----
            - Only affects external access via value_by_key()
            - Internal hook values remain unchanged
            - Useful for type conversion or value formatting on output
            
            Examples
            --------
            >>> output_wrappers = {
            ...     'price': lambda x: round(x, 2),  # Round price to 2 decimals
            ...     'name': lambda x: x.upper()       # Convert name to uppercase
            ... }
            
        logger : Optional[Logger], optional
            Optional logger instance for debugging and error reporting.
            If None, uses the default logging configuration.
            
        nexus_manager : NexusManager, optional
            NexusManager instance for coordinating value updates.
            Defaults to _DEFAULT_NEXUS_MANAGER. Controls how values are synchronized
            and equality is checked across the hook system.
            
        Notes
        -----
        Base Class Design:
        - This class serves as the foundation for all complex X objects in the library
        - The first four parameters are mandatory to ensure consistent initialization across subclasses
        - Subclasses may pass None for callbacks they don't need, but must explicitly provide them
        
        Implementation Notes:
        - Primary hooks represent the core state of the X object
        - Secondary hooks are derived values calculated from primary hooks
        - All value changes go through the nexus manager for coordination
        - Validation occurs before any state changes are applied
        - Invalidation callbacks are only called for valid state transitions
        
        Error Handling:
        - Raises ValueError if primary and secondary hook keys overlap
        - Raises ValueError if validate_complete_primary_values_callback or custom_validator returns False
        - Raises ValueError if compute_missing_primary_values_callback returns invalid keys
        - Logs errors from invalidate_after_update_custom_callback but doesn't raise them
        """

        #################################################################################################
        # Initialization start
        #################################################################################################

        # Initialize fields
        self._primary_hooks: dict[PHK, OwnedWritableHook[PHV, Self]] = {}
        self._secondary_hooks: dict[SHK, OwnedReadOnlyHook[SHV, Self]] = {}
        self._secondary_values: dict[SHK, SHV] = {}
        """Just to ensure that the secondary values cannot be modified from outside. They can be different, but only within the nexus manager's equality check. These values are never used for anything else."""

        # Eager Caching
        self._primary_hook_keys = set(initial_hook_values.keys())
        if compute_secondary_values_callback is not None:
            self._secondary_hook_keys: set[SHK] = set(compute_secondary_values_callback.keys())
        else:
            self._secondary_hook_keys = set()

        # Some checks:
        if self._primary_hook_keys & self._secondary_hook_keys:
            raise ValueError("Primary hook keys and secondary hook keys must be disjoint")

        # Collect the output value wrappers (Ensure that the output values are always have a certain type)
        self._output_value_wrappers: dict[PHK|SHK, Callable[[PHV|SHV], PHV|SHV]] = {}
        if output_value_wrapper is not None:
            for key, wrapper in output_value_wrapper.items():
                self._output_value_wrappers[key] = wrapper

        #################################################################################################
        # Initialize BaseCarriesHooks
        #################################################################################################

        # -------------------------------- Prepare callbacks --------------------------------

        def internal_invalidate_callback() -> tuple[bool, str]:
            if invalidate_after_update_callback is not None:
                try:
                    invalidate_after_update_callback()
                except Exception as e:
                    raise ValueError(f"Error in the act_on_invalidation_callback: {e}")
            return True, "Successfully invalidated"

        def internal_validation_in_isolation_callback(values: Mapping[PHK|SHK, PHV|SHV]) -> tuple[bool, str]:
            
            # First, do the internal verification method
            if validate_complete_primary_values_callback is not None:
                primary_values_dict: dict[PHK, PHV] = dict(self.primary_values)
                for key, value in values.items():
                    if key in self._primary_hooks:
                        primary_values_dict[key] = value # type: ignore
                    elif key in self._secondary_hooks:
                        # Check if internal secondary values are equal to the values
                        if not self._get_nexus_manager().is_equal(self._secondary_values[key], value): # type: ignore
                            return False, f"Internal secondary value for key {key} ( {self._secondary_values[key]} ) is not equal to the submitted value {value}" # type: ignore
                    else:
                        raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")
                success, msg = validate_complete_primary_values_callback(primary_values_dict)
                if not success:
                    return False, msg
            
            # Then, do the custom validator
            if custom_validator is not None:
                success, msg = custom_validator(values)
                if not success:
                    return False, msg
            return True, "Values are valid"

        def internal_add_values_to_be_updated_callback(update_values: UpdateFunctionValues[PHK|SHK, PHV|SHV]) -> Mapping[PHK|SHK, PHV|SHV]:
            # Step 1: Complete the primary values
            primary_values: dict[PHK, PHV] = {}
            for key, hook in self._primary_hooks.items():
                if key in update_values.submitted:
                    primary_values[key] = update_values.submitted[key] # type: ignore
                else:
                    primary_values[key] = hook._get_value() # type: ignore

            # Step 2: Generate additionally values if add_values_to_be_updated_callback is provided
            additional_values: dict[PHK|SHK, PHV|SHV] = {}
            if compute_missing_primary_values_callback is not None:
                current_values_only_primary: Mapping[PHK, PHV] = {}
                for key, value in update_values.current.items():
                    if key in self._primary_hook_keys:
                        current_values_only_primary[key] = value # type: ignore
                submitted_values_only_primary: Mapping[PHK, PHV] = {}
                for key, value in update_values.submitted.items():
                    if key in self._primary_hook_keys:
                        submitted_values_only_primary[key] = value # type: ignore

                additional_values = compute_missing_primary_values_callback(UpdateFunctionValues(current=current_values_only_primary, submitted=submitted_values_only_primary)) # type: ignore
                # Check this they only contain primary hook keys
                for key in additional_values.keys():
                    if key not in self._primary_hook_keys:
                        raise ValueError(f"Additional values keys must only contain primary hook keys")

                primary_values.update(additional_values) # type: ignore

            # Step 3: Generate the secondary values
            for key in self._secondary_hooks.keys():
                value = self._secondary_hook_callbacks[key](primary_values)
                self._secondary_values[key] = value
                additional_values[key] = value

            # Step 4: Return the additional values
            return additional_values

        # --------------------- Initialize XBase --------------------------------
        
        XBase.__init__( # type: ignore
            self,
            logger=logger,
            invalidate_after_update_callback=internal_invalidate_callback,
            validate_complete_values_callback=internal_validation_in_isolation_callback,
            compute_missing_values_callback=internal_add_values_to_be_updated_callback,
            nexus_manager=nexus_manager,
            preferred_publish_mode=preferred_publish_mode
        )

        #################################################################################################
        # Set inital values
        #################################################################################################

        # -------------------------------- Primary values and hooks --------------------------------

        initial_primary_hook_values: dict[PHK, PHV] = {}
        for key, value in initial_hook_values.items():

            # Resolve the initial value and the external hook
            if isinstance(value, HookProtocol):
                initial_value: PHV = value._get_value() # type: ignore
                external_hook: Optional[HookProtocol[PHV]] = value # type: ignore
            else:
                initial_value = value
                external_hook = None

            # Create the initial value and the internal hook
            initial_primary_hook_values[key] = initial_value
            self._primary_hooks[key] = OwnedWritableHook[PHV, Self](self, initial_value, logger, nexus_manager) # type: ignore
            
            # Join the external hook to the internal hook
            external_hook._join(self._primary_hooks[key], "use_target_value") if external_hook is not None else None # type: ignore

        # -------------------------------- Secondary values and hooks --------------------------------

        self._secondary_hook_callbacks: dict[SHK, Callable[[Mapping[PHK, PHV]], SHV]] = {}
        if compute_secondary_values_callback is not None:
            for key, _callback in compute_secondary_values_callback.items():
                self._secondary_hook_callbacks[key] = _callback
                value = _callback(initial_primary_hook_values)
                self._secondary_values[key] = value
                secondary_hook = OwnedReadOnlyHook[SHV, Self](self, value, logger, nexus_manager)
                self._secondary_hooks[key] = secondary_hook

        #################################################################################################

    #########################################################################
    # CarriesSomeHooksBase methods implementation
    #########################################################################

    def _get_hook_by_key(self, key: PHK|SHK) -> OwnedHookProtocol[PHV|SHV, Self]:
        """
        Get a hook by its key.
        
        Parameters
        ----------
        key : PHK or SHK
            The key identifying the hook (primary or secondary)
            
        Returns
        -------
        OwnedHookProtocol[PHV|SHV, Self]
            The hook associated with the key
            
        Raises
        ------
        ValueError
            If the key is not found in primary or secondary hooks
            
        Notes
        -----
        This method must be implemented by subclasses to provide access to hooks.
        It should return the appropriate hook based on whether the key belongs to
        primary or secondary hooks.
        """
        if key in self._primary_hooks:
            return self._primary_hooks[key] # type: ignore
        elif key in self._secondary_hooks:
            return self._secondary_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")

    def _get_hook_keys(self) -> set[PHK|SHK]:
        """
        Get all hook keys (primary and secondary).
        
        Returns
        -------
        set[PHK|SHK]
            Set of all hook keys (both primary and secondary)
            
        Notes
        -----
        This method must be implemented by subclasses to provide access to all hook keys.
        It should return the union of primary and secondary hook keys.
        """
        return set(self._primary_hooks.keys()) | set(self._secondary_hooks.keys())

    def _get_value_by_key(self, key: PHK|SHK) -> PHV|SHV:
        """
        Get a value by its key.
        """
        return self._get_hook_by_key(key).value

    def _get_key_by_hook_or_nexus(self, hook_or_nexus: OwnedHookProtocol[PHV|SHV, Any]|Nexus[PHV|SHV]) -> PHK|SHK:
        """
        Get the key for a hook or nexus.

        Parameters
        ----------
        hook_or_nexus : OwnedHookProtocol[PHV|SHV, Self] or Nexus[PHV|SHV]
            The hook or nexus to get the key for

        Returns
        -------
        PHK or SHK
            The key for the hook or nexus

        Raises
        ------
        ValueError
            If the hook or nexus is not found in component_hooks or secondary_hooks
            
        Notes
        -----
        This method must be implemented by subclasses to provide reverse lookup from hooks to keys.
        It should search through both primary and secondary hooks to find the matching key.
        """
        if isinstance(hook_or_nexus, Nexus):
            for key, hook in self._primary_hooks.items():
                if hook._get_nexus() == hook_or_nexus: # type: ignore
                    return key
            for key, hook in self._secondary_hooks.items():
                if hook._get_nexus() == hook_or_nexus: # type: ignore
                    return key
            raise ValueError(f"Hook {hook_or_nexus} not found in component_hooks or secondary_hooks")
        elif isinstance(hook_or_nexus, OwnedHookProtocol): #type: ignore
            for key, hook in self._primary_hooks.items():
                if hook == hook_or_nexus:
                    return key
            for key, hook in self._secondary_hooks.items():
                if hook == hook_or_nexus:
                    return key
            raise ValueError(f"Hook {hook_or_nexus} not found in component_hooks or secondary_hooks")
        else:
            raise ValueError(f"Hook {hook_or_nexus} not found in component_hooks or secondary_hooks")

    #########################################################
    # Serialization methods implementation
    #########################################################

    def get_values_for_serialization(self) -> Mapping[PHK|SHK, PHV|SHV]:
        """
        Get the values for serialization.
        """
        return {key: self._get_value_by_key(key) for key in self._get_hook_keys()}

    def set_values_from_serialization(self, values: Mapping[PHK|SHK, PHV|SHV]) -> None:
        """
        Set the values from serialization.
        """
        success, msg = self._submit_values(values)
        if not success:
            raise ValueError(f"Failed to set values from serialization: {msg}")

    #########################################################################
    # Other methods (maybe for a future protocol)
    #########################################################################

    def _value_wrapped(self, key: PHK|SHK) -> PHV|SHV:
        if key in self._output_value_wrappers:
            return self._output_value_wrappers[key](self._get_value_by_key(key))
        else:
            return self._get_value_by_key(key)

    def join_many_by_keys(self, source_hooks: Mapping[PHK|SHK, HookProtocol[PHV|SHV]], initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Join many hooks by their keys.
        """
        for key, hook in source_hooks.items():
            self.join_by_key(key, hook, initial_sync_mode)

    def join_by_key(self, source_hook_key: PHK|SHK, target_hook: HookProtocol[PHV|SHV], initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Join a hook by its key.

        ** Thread-safe **

        Args:
            source_hook_key: The key of the hook to join
            target_hook: The hook to join
            initial_sync_mode: The initial synchronization mode
        Returns:
            None

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
            ValueError: If the hook is not a primary or secondary hook
        """
        with self._lock:
            return self._join(source_hook_key, target_hook, initial_sync_mode)

    def isolate_by_key(self, key: PHK|SHK) -> None:
        """
        Isolate a hook by its key.

        ** Thread-safe **

        Args:
            key: The key of the hook to isolate

        Returns:
            None

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """
        with self._lock:
            self._isolate(key)

    def isolate_all(self) -> None:
        """
        Isolate all hooks.

        ** Thread-safe **

        Args:
            None
        """
        with self._lock:
            self._isolate(None)

    def value_by_key(self, key: PHK|SHK) -> PHV|SHV:
        """
        Get the value of a hook by its key.

        ** Thread-safe **

        Args:
            key: The key of the hook to get the value of

        Returns:
            PHV|SHV: The value of the hook

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """
        with self._lock:
            return self._value_wrapped(key)

    def hook_by_key(self, key: PHK|SHK) -> OwnedHookProtocol[PHV|SHV, Self]:
        """
        Get a hook by its key.

        ** Thread-safe **

        Args:
            key: The key of the hook to get

        Returns:
            OwnedHookProtocol[PHV|SHV, Self]: The hook

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """
        with self._lock:
            return self._get_hook_by_key(key)

    @property
    def hook_keys(self) -> set[PHK|SHK]:
        """
        Get all hook keys.

        ** Thread-safe **

        Returns:
            set[PHK|SHK]: The set of all hook keys

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
            ValueError: If the hook is not a primary or secondary hook
        """
        with self._lock:
            return self._get_hook_keys()

    def validate_values_by_keys(self, values: Mapping[PHK, PHV]) -> tuple[bool, str]:
        """
        This method checks if the provided values would be valid for submission. 

        ** Thread-safe **

        Args:
            values: The values to validate

        Returns:
            A tuple of (success: bool, message: str)
        """
        
        with self._lock:
            return self._validate_values(values) # type: ignore

    def validate_value_by_key(self, key: PHK, value: PHV) -> tuple[bool, str]: # type: ignore
        """
        This method checks if the provided value would be valid for submission. 

        ** Thread-safe **

        Args:
            key: The key of the hook to submit the value to
            value: The value to submit
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails

        Returns:
            A tuple of (success: bool, message: str)
        """
        
        with self._lock:
            return self._validate_value(key, value)

    def submit_values_by_keys(self, values: Mapping[PHK, PHV], *, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        This method submits the provided values to the X object.

        ** Thread-safe **

        Args:
            values: The values to submit
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails

        Returns:
            A tuple of (success: bool, message: str)

        Raises:
            SubmissionError: If the submission fails
        """
        
        with self._lock:
            success, msg = self._submit_values(values) # type: ignore
            if not success and raise_submission_error_flag:
                raise SubmissionError(msg, values)
            return success, msg

    def submit_value_by_key(self, key: PHK, value: PHV, *, raise_submission_error_flag: bool = True) -> tuple[bool, str]: # type: ignore
        """
        This method submits the provided value to the X object.

        Args:
            key: The key of the hook to submit the value to
            value: The value to submit
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails

        Returns:
            A tuple of (success: bool, message: str)

        Raises:
            SubmissionError: If the submission fails

        ** Thread-safe **
        """
        
        with self._lock:
            success, msg = self._submit_value(key, value)
            if not success and raise_submission_error_flag:
                raise SubmissionError(msg, value, str(key))
            return success, msg

    #########################################################################
    # Other private methods
    #########################################################################

    def _get_key_for_primary_hook(self, hook_or_nexus: OwnedHookProtocol[PHV|SHV, Self]|Nexus[PHV|SHV]) -> PHK:
        """
        Get the key for a primary hook.
        
        Parameters
        ----------
        hook_or_nexus : OwnedHookProtocol[PHV|SHV, Self] or Nexus[PHV|SHV]
            The hook or nexus to get the key for
            
        Returns
        -------
        PHK
            The key for the primary hook
            
        Raises
        ------
        ValueError
            If the hook is not a primary hook
            
        Notes
        -----
        This method must be implemented by subclasses to provide efficient lookup for primary hooks.
        It should only search through primary hooks and raise an error if not found.
        """
        for key, hook in self._primary_hooks.items():
            if hook == hook_or_nexus or hook._get_nexus() == hook_or_nexus: # type: ignore
                return key
        raise ValueError(f"Hook {hook_or_nexus} is not a primary hook!")

    def _get_key_for_secondary_hook(self, hook_or_nexus: OwnedHookProtocol[PHV|SHV, Self]|Nexus[PHV|SHV]) -> SHK:
        """
        Get the key for a secondary hook.
        
        Parameters
        ----------
        hook_or_nexus : OwnedHookProtocol[PHV|SHV, Self] or Nexus[PHV|SHV]
            The hook or nexus to get the key for
            
        Returns
        -------
        SHK
            The key for the secondary hook
            
        Raises
        ------
        ValueError
            If the hook is not a secondary hook
            
        Notes
        -----
        This method must be implemented by subclasses to provide efficient lookup for secondary hooks.
        It should only search through secondary hooks and raise an error if not found.
        """
        for key, hook in self._secondary_hooks.items():
            if hook == hook_or_nexus or hook._get_nexus() == hook_or_nexus: # type: ignore
                return key
        raise ValueError(f"Hook {hook_or_nexus} is not a secondary hook!")

    #########################################################################
    # Other public methods
    #########################################################################

    @property
    def primary_hooks(self) -> Mapping[PHK, OwnedWritableHook[PHV, Self]]:
        """
        Get the primary hooks of the X object.
        
        Returns
        -------
        Mapping[PHK, OwnedWritableHook[PHV, Self]]
            Copy of the primary hooks dictionary
            
        Notes
        -----
        This property must be implemented by subclasses to provide access to primary hooks.
        It should return a copy to prevent external modification.
        """
        return self._primary_hooks.copy()
    
    @property
    def secondary_hooks(self) -> Mapping[SHK, OwnedReadOnlyHook[SHV, Self]]:
        """
        Get the secondary hooks of the X object.
        
        Returns
        -------
        Mapping[SHK, OwnedReadOnlyHook[SHV, Self]]
            Copy of the secondary hooks dictionary
            
        Notes
        -----
        This property must be implemented by subclasses to provide access to secondary hooks.
        It should return a copy to prevent external modification.
        """
        return self._secondary_hooks.copy()

    @property
    def primary_values(self) -> dict[PHK, PHV]:
        """
        Get the values of the primary component hooks as a dictionary.
        
        Returns
        -------
        dict[PHK, PHV]
            Dictionary mapping primary hook keys to their current values
            
        Notes
        -----
        This property must be implemented by subclasses to provide access to primary values.
        It should return the current values of all primary hooks.
        """
        return {key: hook._get_value() for key, hook in self._primary_hooks.items()} # type: ignore
    
    @property
    def secondary_values(self) -> dict[SHK, SHV]:
        """
        Get the values of the secondary component hooks as a dictionary.
        
        Returns
        -------
        dict[SHK, SHV]
            Dictionary mapping secondary hook keys to their current values
            
        Notes
        -----
        This property must be implemented by subclasses to provide access to secondary values.
        It should return the current values of all secondary hooks.
        """
        return {key: hook._get_value() for key, hook in self._secondary_hooks.items()} # type: ignore

    @property
    def primary_hook_keys(self) -> set[PHK]:
        """
        Get the keys of the primary component hooks.
        
        Returns
        -------
        set[PHK]
            Set of primary hook keys
            
        Notes
        -----
        This property must be implemented by subclasses to provide access to primary hook keys.
        It should return the cached set of primary hook keys for efficient lookup.
        """
        return self._primary_hook_keys

    @property
    def secondary_hook_keys(self) -> set[SHK]:
        """
        Get the keys of the secondary component hooks.
        
        Returns
        -------
        set[SHK]
            Set of secondary hook keys
            
        Notes
        -----
        This property must be implemented by subclasses to provide access to secondary hook keys.
        It should return the cached set of secondary hook keys for efficient lookup.
        """
        return self._secondary_hook_keys