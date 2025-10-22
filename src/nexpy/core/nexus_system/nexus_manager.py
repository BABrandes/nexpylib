from typing import Mapping, Any, Optional, TYPE_CHECKING, Callable, Literal, Sequence
from types import MappingProxyType

from threading import RLock, local
from logging import Logger

from ..._utils import log

if TYPE_CHECKING:
    from ...foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol

from ..hooks.hook_aliases import Hook
from ..auxiliary.listening_protocol import ListeningProtocol
from .nexus import Nexus
from .update_function_values import UpdateFunctionValues
from ..publisher_subscriber.publisher_protocol import PublisherProtocol

class NexusManager:
    """
    Central coordinator for transitive synchronization and Nexus fusion (thread-safe).
    
    The NexusManager orchestrates the complete synchronization flow:
    1. Receives value submissions from observables
    2. Completes missing values using add_values_to_be_updated_callback
    3. Validates all values using validation callbacks
    4. Updates Nexuses with new values (propagating to all hooks in the fusion domain)
    5. Triggers invalidation, reactions, publishing, and listener notifications
    
    Nexus Fusion Process:
    When hooks are joined, the NexusManager performs Nexus fusion:
    - Destroys the original Nexuses
    - Creates a new unified Nexus for the fusion domain
    - Ensures transitive synchronization across all joined hooks
    
    Hook Connection Process:
    The NexusManager plays a crucial role in the hook connection process:
    1. Get the two nexuses from the hooks to connect
    2. Submit one of the hooks' value to the other nexus (via submit_values)
    3. If successful, both nexus must now have the same value
    4. Merge the nexuses to one -> Connection established!
    
    Three Notification Philosophies
    --------------------------------
    This system supports three distinct notification mechanisms, each with different
    characteristics and use cases:
    
    1. **Listeners (Synchronous Unidirectional)**
       - Callbacks registered via `add_listener()` on observables or hooks
       - Executed synchronously during `submit_values()` (Phase 6)
       - Unidirectional: listeners observe changes but cannot validate or reject them
       - Use case: UI updates, logging, simple reactions to state changes
       - Thread-safe: protected by the same lock as value submission
    
    2. **Publish-Subscribe (Asynchronous Unidirectional)**
       - Based on Publisher/Subscriber pattern with weak reference management
       - Executed asynchronously via asyncio tasks (Phase 6)
       - Unidirectional: subscribers react to publications but cannot validate or reject them
       - Use case: Decoupled components, async I/O operations, external system notifications
       - Thread-safe: each subscriber reaction runs independently in the event loop
       - Non-blocking: publishing returns immediately, reactions happen in background
    
    3. **Hooks (Synchronous Bidirectional with Validation)**
       - Connected hooks share values through HookNexus (value synchronization)
       - Validation occurs before value changes (Phase 4)
       - Bidirectional: any connected hook can reject changes via validation
       - Enforces valid state: all hooks in a nexus always have consistent, validated values
       - Use case: Maintaining invariants across connected state, bidirectional data binding
       - Thread-safe: protected by the same lock as value submission
    
    Thread Safety
    -------------
    All value submission operations are protected by a reentrant lock (RLock),
    ensuring safe concurrent access from multiple threads. The lock serializes
    submissions while allowing nested calls from the same thread.
    
    Reentrancy Protection
    ---------------------
    Nested submit_values() calls are allowed as long as they modify independent
    hook nexuses. However, attempting to modify a hook nexus that's already being
    modified in the current submission chain will raise RuntimeError. This ensures
    atomicity and prevents subtle bugs from overlapping modifications.
    """

    def __init__(
        self,
        value_equality_callbacks: dict[tuple[type[Any], type[Any]], Callable[[Any, Any, float], bool]] | None = None,
        registered_immutable_types: set[type[Any]] | None = None,
        float_accuracy: Optional[float] = None
        ):

        # ----------- Thread Safety -----------

        self._lock = RLock()  # Thread-safe lock for submit_values operations
        self._thread_local = local()  # Thread-local storage for tracking active hook nexuses

        # ----------- Equality Callbacks -----------

        self._value_equality_callbacks: dict[tuple[type[Any], type[Any]], Callable[[Any, Any, float], bool]] = {}
        if value_equality_callbacks is not None:
            self._value_equality_callbacks.update(value_equality_callbacks)
        
        # Note: registered_immutable_types is not currently used but kept for future support
        if registered_immutable_types is None:
            registered_immutable_types = set()

        # ----------- Float Accuracy -----------
        
        self._float_accuracy = float_accuracy  # None means use module-level default

        # ----------------------------------------

    ##################################################################################################################
    # Float Accuracy Property
    ##################################################################################################################
    
    @property
    def FLOAT_ACCURACY(self) -> float:
        """Get the float accuracy tolerance for this manager.
        
        If not explicitly set, returns the module-level default from default_nexus_manager.
        This allows per-manager customization while defaulting to the global setting.
        
        Returns:
            float: The float comparison tolerance to use
        """
        if self._float_accuracy is not None:
            return self._float_accuracy
        # Import here to avoid circular dependency
        from . import default_nexus_manager
        return default_nexus_manager.FLOAT_ACCURACY
    
    @FLOAT_ACCURACY.setter
    def FLOAT_ACCURACY(self, value: float) -> None:
        """Set the float accuracy tolerance for this manager.
        
        Args:
            value: The new float comparison tolerance
        """
        self._float_accuracy = value

    ##################################################################################################################
    # Equality Callbacks
    ##################################################################################################################

    def add_value_equality_callback(self, value_type_pair: tuple[type[Any], type[Any]], value_equality_callback: Callable[[Any, Any, float], bool]) -> None:
        """Add a value equality callback for a specific pair of value types.
        
        Args:
            value_type_pair: Tuple of (type1, type2) for the comparison
            value_equality_callback: Callback function that takes (value1: type1, value2: type2, float_accuracy: float) and returns bool
        """

        if value_type_pair in self._value_equality_callbacks:
            raise ValueError(f"Value equality callback for {value_type_pair} already exists")

        self._value_equality_callbacks[value_type_pair] = value_equality_callback

    def remove_value_equality_callback(self, value_type_pair: tuple[type[Any], type[Any]]) -> None:
        """Remove a value equality callback for a specific pair of value types."""
        if value_type_pair not in self._value_equality_callbacks:
            raise ValueError(f"Value equality callback for {value_type_pair} does not exist")
        del self._value_equality_callbacks[value_type_pair]

    def replace_value_equality_callback(self, value_type_pair: tuple[type[Any], type[Any]], value_equality_callback: Callable[[Any, Any, float], bool]) -> None:
        """Replace a value equality callback for a specific pair of value types.
        
        Args:
            value_type_pair: Tuple of (type1, type2) for the comparison
            value_equality_callback: Callback function that takes (value1: type1, value2: type2, float_accuracy: float) and returns bool
        """
        if value_type_pair not in self._value_equality_callbacks:
            raise ValueError(f"Value equality callback for {value_type_pair} does not exist")
        self._value_equality_callbacks[value_type_pair] = value_equality_callback

    def exists_value_equality_callback(self, value_type_pair: tuple[type[Any], type[Any]]) -> bool:
        """Check if a value equality callback exists for a specific pair of value types."""
        return value_type_pair in self._value_equality_callbacks

    def types_of_value_equality_callbacks(self) -> set[tuple[type[Any], type[Any]]]:
        """Get the type pairs of value equality callbacks."""
        return set(self._value_equality_callbacks.keys())

    def is_equal(self, value1: Any, value2: Any) -> bool:
        """
        Checks if two values are equal.

        ** Please use this method instead of the built-in equality operator (==) for equality checks of values within hook system! **
        
        This method supports cross-type comparisons using registered equality callbacks.
        For example, you can compare float with int using appropriate tolerance.
        
        All registered callbacks receive the manager's FLOAT_ACCURACY as a third parameter.
        """

        type1: type[Any] = type(value1) # type: ignore
        type2: type[Any] = type(value2) # type: ignore
        type_pair = (type1, type2)

        # Check if we have a registered callback for this type pair
        if type_pair in self._value_equality_callbacks:
            callback = self._value_equality_callbacks[type_pair]
            # All callbacks must accept float_accuracy parameter
            return callback(value1, value2, float_accuracy=self.FLOAT_ACCURACY)  # type: ignore

        # Fall back to built-in equality
        return value1 == value2

    def is_not_equal(self, value1: Any, value2: Any) -> bool:
        """
        Check if two values are not equal.
        
        ** Please use this method instead of the built-in inequality operator (!=) for equality checks of values within hook system! **
        """
        return not self.is_equal(value1, value2)

    def reset(self) -> None:
        """Reset the nexus manager state for testing purposes."""
        pass

    ##################################################################################################################
    # Synchronization of Nexus and Values
    ##################################################################################################################

    @staticmethod
    def _filter_nexus_and_values_for_owner(nexus_and_values: dict["Nexus[Any]", Any], owner: "CarriesSomeHooksProtocol[Any, Any]") -> tuple[dict[Any, Any], dict[Any, Hook[Any]]]:
        """
        This method extracts the value and hook dict from the nexus and values dictionary for a specific owner.
        It essentially filters the nexus and values dictionary to only include values which the owner has a hook for. It then finds the hook keys for the owner and returns the value and hook dict for these keys.

        Args:
            nexus_and_values: The nexus and values dictionary
            owner: The owner to filter for

        Returns:
            A tuple containing the value and hook dict corresponding to the owner
        """

        from ..hooks.mixin_protocols.hook_with_owner_protocol import HookWithOwnerProtocol
        from ..hooks.hook_aliases import Hook

        key_and_value_dict: dict[Any, Any] = {}
        key_and_hook_dict: dict[Any, Hook[Any]] = {}
        for nexus, value in nexus_and_values.items():
            for hook in nexus.hooks:
                if isinstance(hook, HookWithOwnerProtocol):
                    if hook.owner is owner:
                        hook_key: Any = owner._get_key_by_hook_or_nexus(hook) # type: ignore
                        key_and_value_dict[hook_key] = value
                        key_and_hook_dict[hook_key] = hook # type: ignore
        return key_and_value_dict, key_and_hook_dict

    @staticmethod
    def _complete_nexus_and_values_for_owner(value_dict: dict[Any, Any], owner: "CarriesSomeHooksProtocol[Any, Any]", as_reference_values: bool = False) -> None:
        """
        Complete the value dict for an owner.

        Args:
            value_dict: The value dict to complete
            owner: The owner to complete the value dict for
            as_reference_values: If True, the values will be returned as reference values
        """

        for hook_key in owner._get_hook_keys(): # type: ignore
            if hook_key not in value_dict:
                if as_reference_values:
                    value_dict[hook_key] = owner._get_value_by_key(hook_key) # type: ignore
                else:
                    value_dict[hook_key] = owner._get_value_by_key(hook_key) # type: ignore

    def _complete_nexus_and_values_dict(self, nexus_and_values: dict["Nexus[Any]", Any]) -> tuple[bool, str]:
        """
        Complete the nexus and values dictionary using add_values_to_be_updated_callback.
        
        This method iteratively calls the add_values_to_be_updated_callback on all
        affected observables to complete missing values. For example, if a dictionary
        value is updated, the dictionary itself must be updated as well.
        
        The process continues until no more values need to be added, ensuring all
        related values are synchronized.
        """

        def insert_value_and_hook_dict_into_nexus_and_values(nexus_and_values: dict["Nexus[Any]", Any], value_dict: dict[Any, Any], hook_dict: dict[Any, Hook[Any]]) -> tuple[bool, str]:
            """
            This method inserts the value and hook dict into the nexus and values dictionary.
            It inserts the values from the value dict into the nexus and values dictionary. The hook dict helps to find the hook nexus for each value.
            """
            if value_dict.keys() != hook_dict.keys():
                return False, "Value and hook dict keys do not match"
            for hook_key, value in value_dict.items():
                nexus: Nexus[Any] = hook_dict[hook_key]._get_nexus() # type: ignore
                if nexus in nexus_and_values:
                    # The nexus is already in the nexus and values, this is not good. But maybe the associated value is the same?
                    current_value: Any = nexus_and_values[nexus]
                    # Use proper equality comparison that handles NaN values correctly
                    if not self.is_equal(current_value, value):
                        return False, f"Hook nexus already in nexus and values and the associated value is not the same! ({current_value} != {value})"
                nexus_and_values[nexus] = value
            return True, "Successfully inserted value and hook dict into nexus and values"

        def update_nexus_and_value_dict(owner: "CarriesSomeHooksProtocol[Any, Any]", nexus_and_values: dict["Nexus[Any]", Any]) -> tuple[Optional[int], str]:
            """
            This method updates the nexus and values dictionary with the additional nexus and values, if requested by the owner.
            """

            # Step 1: Prepare the value and hook dict to provide to the owner method
            value_dict, hook_dict = NexusManager._filter_nexus_and_values_for_owner(nexus_and_values, owner)

            # Step 2: Get the additional values from the owner method
            current_values_of_owner: Mapping[Any, Any] = owner._get_dict_of_values() # type: ignore
            update_values = UpdateFunctionValues(current=current_values_of_owner, submitted=MappingProxyType(value_dict)) # Wrap the value_dict in MappingProxyType to prevent mutation by the owner function!

            try:
                additional_value_dict: Mapping[Any, Any] = owner._add_values_to_be_updated(update_values) # type: ignore
            except Exception as e:
                return None, f"Error in '_add_values_to_be_updated' of owner '{owner}': {e} (update_values: {update_values})"

            # Step 4: Make the new values ready for the sync system add them to the value and hook dict
            for hook_key, value in additional_value_dict.items():
                error_msg, value_for_storage = self._convert_value_for_storage(value)
                if error_msg is not None:
                    return None, f"Value of type {type(value).__name__} cannot be converted for storage: {error_msg}"
                value_dict[hook_key] = value_for_storage
                hook_dict[hook_key] = owner._get_hook_by_key(hook_key) # type: ignore

            # Step 5: Insert the value and hook dict into the nexus and values
            number_of_items_before: int = len(nexus_and_values)
            success, msg = insert_value_and_hook_dict_into_nexus_and_values(nexus_and_values, value_dict, hook_dict)
            if success == False:
                return None, msg
            number_of_inserted_items: int = len(nexus_and_values) - number_of_items_before

            # Step 6: Return the nexus and values
            return number_of_inserted_items, "Successfully updated nexus and values"

        from ..hooks.mixin_protocols.hook_with_owner_protocol import HookWithOwnerProtocol
            
        # This here is the main loop: We iterate over all the hooks to see if they belong to an owner, which require more values to be changed if the current values would change.
        while True:

            # Step 1: Collect the all the owners that need to be checked for additional nexus and values
            owners_to_check_for_additional_nexus_and_values: list["CarriesSomeHooksProtocol[Any, Any]"] = []
            for nexus in nexus_and_values:
                for hook in nexus.hooks:
                    if isinstance(hook, HookWithOwnerProtocol):
                        if hook.owner not in owners_to_check_for_additional_nexus_and_values:
                            owners_to_check_for_additional_nexus_and_values.append(hook.owner)

            # Step 2: Check for each owner if there are additional nexus and values
            number_of_inserted_items: Optional[int] = 0
            for owner in owners_to_check_for_additional_nexus_and_values:
                number_of_inserted_items, msg = update_nexus_and_value_dict(owner, nexus_and_values)
                if number_of_inserted_items is None:
                    return False, msg
                if number_of_inserted_items > 0:
                    break

            # Step 3: If no additional nexus and values were found, break the loop
            if number_of_inserted_items == 0:
                break

        return True, "Successfully updated nexus and values"

    def _convert_value_for_storage(self, value: Any) -> tuple[Optional[str], Any]:
        """
        Convert a value for storage in a Nexus.
        
        Currently disabled - values are stored as-is without conversion.
        """
        # Immutability system disabled - pass through values as-is
        return None, value

    def _internal_submit_values(self, nexus_and_values: Mapping["Nexus[Any]", Any], mode: Literal["Normal submission", "Forced submission", "Check values"], logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Internal implementation of submit_values.

        This method is not thread-safe and should only be called by the submit_values method.
        
        This method is a crucial part of the hook connection process:
        1. Get the two nexuses from the hooks to connect
        2. Submit one of the hooks' value to the other nexus (this method)
        3. If successful, both nexus must now have the same value
        4. Merge the nexuses to one -> Connection established!
        
        Parameters
        ----------
        mode : Literal["Normal submission", "Forced submission", "Check values"]
            Controls the submission behavior:
            - "Normal submission": Only submits values that differ from current values
            - "Forced submission": Submits all values regardless of equality
            - "Check values": Only validates without updating
        """

        from ..hooks.mixin_protocols.hook_with_owner_protocol import HookWithOwnerProtocol
        from ..hooks.mixin_protocols.hook_with_isolated_validation_protocol import HookWithIsolatedValidationProtocol
        from ..hooks.mixin_protocols.hook_with_reaction_protocol import HookWithReactionProtocol
        from ..hooks.mixin_protocols.hook_with_connection_protocol import HookWithConnectionProtocol

        #########################################################
        # Check if the values are immutable
        #########################################################

        _nexus_and_values: dict["Nexus[Any]", Any] = {}
        for nexus, value in nexus_and_values.items():
            error_msg, value_for_storage = self._convert_value_for_storage(value)
            if error_msg is not None:
                return False, f"Value of type {type(value).__name__} cannot be converted for storage: {error_msg}"
            _nexus_and_values[nexus] = value_for_storage

        #########################################################
        # Check if the values are even different from the current values
        #########################################################

        match mode:
            case "Normal submission":
                # Filter to only values that differ from current (using immutable versions)
                filtered_nexus_and_values: dict["Nexus[Any]", Any] = {}
                for nexus, value in _nexus_and_values.items():
                    if not self.is_equal(nexus._stored_value, value): # type: ignore
                        filtered_nexus_and_values[nexus] = value
                
                _nexus_and_values = filtered_nexus_and_values

                log(self, "NexusManager._internal_submit_values", logger, True, f"Initially {len(nexus_and_values)} nexus and values submitted, after checking for equality {len(_nexus_and_values)}")

                if len(_nexus_and_values) == 0:
                    return True, "Values are the same as the current values. No submission needed."

            case "Forced submission":
                # Use all immutable values
                pass

            case "Check values":
                # Use all immutable values
                pass

            case _: # type: ignore
                raise ValueError(f"Invalid mode: {mode}")

        #########################################################
        # Value Completion
        #########################################################

        # Step 1: Update the nexus and values
        complete_nexus_and_values: dict["Nexus[Any]", Any] = {}
        complete_nexus_and_values.update(_nexus_and_values)
        success, msg = self._complete_nexus_and_values_dict(complete_nexus_and_values)
        if success == False:
            return False, msg

        # Step 2: Collect the owners and floating hooks to validate, react to, and notify
        owners_that_are_affected: list["CarriesSomeHooksProtocol[Any, Any]"] = []
        hooks_with_validation: set[HookWithIsolatedValidationProtocol[Any]] = set()
        hooks_with_reaction: set[HookWithReactionProtocol] = set()
        publishers: set[PublisherProtocol] = set()
        for nexus, value in complete_nexus_and_values.items():
            for hook in nexus.hooks:
                if isinstance(hook, HookWithReactionProtocol):
                    hooks_with_reaction.add(hook)
                if isinstance(hook, HookWithIsolatedValidationProtocol):
                    # Hooks that are owned by an observable are validated by the observable. They do not need to be validated in isolation.
                    if not isinstance(hook, HookWithOwnerProtocol):
                        hooks_with_validation.add(hook)
                if isinstance(hook, HookWithOwnerProtocol):
                    if hook.owner not in owners_that_are_affected:
                        owners_that_are_affected.append(hook.owner)
                    if isinstance(hook.owner, PublisherProtocol):
                        publishers.add(hook.owner)
                publishers.add(hook) # type: ignore

        #########################################################
        # Value Validation
        #########################################################

        # Step 3: Validate the values
        for owner in owners_that_are_affected:
            value_dict, _ = NexusManager._filter_nexus_and_values_for_owner(complete_nexus_and_values, owner)
            NexusManager._complete_nexus_and_values_for_owner(value_dict, owner, as_reference_values=True)
            try:
                success, msg = owner._validate_complete_values_in_isolation(value_dict) # type: ignore
            except Exception as e:
                return False, f"Error in '_validate_complete_values_in_isolation' of owner '{owner}': {e} (value_dict: {value_dict})"
            if success == False:    
                return False, msg
        for floating_hook in hooks_with_validation:
            assert isinstance(floating_hook, HookWithConnectionProtocol)
            try:
                success, msg = floating_hook.validate_value_in_isolation(complete_nexus_and_values[floating_hook._get_nexus()]) # type: ignore
            except Exception as e:
                return False, f"Error in 'validate_value_in_isolation' of floating hook '{floating_hook}': {e} (complete_nexus_and_values: {complete_nexus_and_values})"
            if success == False:
                return False, msg

        #########################################################
        # Value Update
        #########################################################

        if mode == "Check values":
            return True, "Values are valid"

        # Step 4: Update each nexus with the new value
        for nexus, value in complete_nexus_and_values.items():
            nexus._previous_stored_value = nexus._stored_value # type: ignore
            nexus._stored_value = value # type: ignore

        #########################################################
        # Invalidation, Reaction, and Notification
        #########################################################

        # Step 5a: Invalidate the affected owners and hooks
        for owner in owners_that_are_affected:
            owner._invalidate() # type: ignore

        # Step 5b: React to the value changes
        for hook in hooks_with_reaction:
            hook.react_to_value_changed()

        # Step 5c: Publish the value changes
        for publisher in publishers:
            publisher.publish(None)

        # Step 5d: Notify the listeners

        # Optimize: Only notify hooks that are actually affected by the value changes
        hooks_to_be_notified: set[Hook[Any]] = set()
        for nexus, value in complete_nexus_and_values.items():
            hooks_of_nexus: set[Hook[Any]] = set(nexus.hooks) # type: ignore
            hooks_to_be_notified.update(hooks_of_nexus)

        def notify_listeners(obj: "ListeningProtocol | Hook[Any]"):
            """
            This method notifies the listeners of an object.
            """

            try:
                obj._notify_listeners() # type: ignore
            except RuntimeError:
                # RuntimeError indicates a programming error (like recursive submit_values)
                # that should not be silently caught - re-raise it immediately
                raise
            except Exception as e:
                if logger is not None:
                    logger.error(f"Error in listener callback: {e}")

        # Notify owners and hooks that are owned        
        for owner in owners_that_are_affected:
            if isinstance(owner, ListeningProtocol):
                notify_listeners(owner)
            # Only notify hooks that are actually affected
            for hook in owner._get_dict_of_hooks().values(): # type: ignore
                if hook in hooks_to_be_notified:
                    hooks_to_be_notified.remove(hook)
                    notify_listeners(hook)

        # Notify the remaining hooks
        for hook in hooks_to_be_notified:
            notify_listeners(hook)

        return True, "Values are submitted"

    def submit_values(
        self,
        nexus_and_values: Mapping["Nexus[Any]", Any]|Sequence[tuple["Nexus[Any]", Any]],
        mode: Literal["Normal submission", "Forced submission", "Check values"] = "Normal submission",
        logger: Optional[Logger] = None
        ) -> tuple[bool, str]:
        """
        Submit values to the hook nexuses - the central orchestration point for all value changes.
        
        This is the main entry point for value submissions in the observable system. It orchestrates
        the complete submission flow through five distinct phases, ensuring consistency, validation,
        and proper notification of all affected components.
        
        **IMPORTANT - No Value Copying**: This method works exclusively with value references, never
        creating copies of the submitted values. This design choice enables efficient handling of
        complex objects (large lists, nested dictionaries, custom classes, etc.) without incurring
        time penalties from copying operations. All value comparisons, assignments, and propagations
        use references only.
        
        Submission Flow (Six Phases)
        ------------------------------

        **Phase 1: Value Equality Check**
            Depending on the mode, this phase checks if the values are different from the current values using `is_equal`.
            If they are the same, the submission is skipped.
        
        **Phase 2: Value Completion**
            The system completes any missing related values using `add_values_to_be_updated_callback`
            from affected observables. This is an iterative process:
            
            - Identifies all observables (owners) affected by the submitted values
            - For each owner, calls their `_add_values_to_be_updated()` method
            - The owner can return additional values that need to be updated
            - Process repeats until no new values are added
            
            Example: When updating a dict item, the dict observable itself must also be updated.
            The completion phase ensures both the item and parent dict are in the submission.
        
        **Phase 3: Value Collection**
            Collects all affected components for validation and notification:
            
            - All observables (owners) that own hooks in the affected nexuses
            - All floating hooks with validation mixins
            - All hooks with reaction mixins
            - All publishers (observables and hooks that implement PublisherProtocol)
            
            This step prepares the sets of objects that will be processed in later phases.
        
        **Phase 4: Value Validation**
            Validates all values before any changes are committed:
            
            - For each affected observable: calls `validate_complete_values_in_isolation()`
              with ALL its hook values (both submitted and current values as references)
            - For each floating hook with validation: calls `validate_value_in_isolation()`
            - If any validation fails, the entire submission is rejected (no partial updates)
            
            This ensures atomicity - either all values are valid and applied, or none are.
        
        **Phase 5: Value Update** (skipped if mode="Check values")
            Updates the hook nexuses with new values:
            
            - Saves current value as `_previous_value` for each nexus
            - Assigns new value to `_value` (reference assignment only)
            - All hooks in the nexus immediately see the new value
        
        **Phase 6: Invalidation, Reaction, Publishing, and Notification**
            Propagates changes to all affected components:
            
            - **Invalidation** (Synchronous): Calls `invalidate()` on all affected observables
              (allows observables to recompute derived state)
              
            - **Reaction** (Synchronous): Calls `react_to_value_changed()` on hooks with reaction mixins
              (enables custom side effects like logging, caching, etc.)
              
            - **Publishing** (Asynchronous): Calls `publish()` on all publishers (observables and hooks)
              * Publications are executed asynchronously via asyncio tasks
              * The `publish()` call returns immediately without blocking
              * Subscriber reactions run independently in the event loop
              * Useful for decoupled async operations like network calls, file I/O, etc.
              * Subscribers cannot affect the current submission (already committed)
              
            - **Listener Notification** (Synchronous): Triggers `_notify_listeners()` on:
              * All affected observables (if they implement BaseListeningProtocol)
              * All hooks in affected nexuses
              * Listener callbacks execute synchronously before `submit_values()` returns
        
        Parameters
        ----------
        nexus_and_values : Mapping[Nexus[Any], Any]|Sequence[tuple[Nexus[Any], Any]]
            Mapping of hook nexuses to their new values. The values are used by reference
            only - no copies are created. Each nexus will be updated with its corresponding
            value, and all hooks in that nexus will reflect the change.
            
        mode : Literal["Normal submission", "Forced submission", "Check values"], default="Normal submission"
            Controls the submission behavior:
            
            - **"Normal submission"**: Checks if values differ from current values first (using `is_equal`).
              Only submits and processes values that are actually different, skipping unchanged values.
              Returns early if all values match current values. This is the most efficient mode for
              typical value updates.
              
            - **"Forced submission"**: Submits all values regardless of whether they match current values.
              Bypasses the equality check and processes all submitted values through the complete
              submission flow. Useful when you need to ensure all validation, reaction, and notification
              logic runs even for unchanged values.
              
            - **"Check values"**: Performs only phases 2-4 (value completion and validation) without
              actually updating values (phase 5) or triggering notifications (phase 6). Useful for
              pre-validation of potential changes without committing them.
            
        logger : Optional[Logger], default=None
            Optional logger for debugging the submission process. Currently not actively
            used in the implementation but reserved for future debugging capabilities.
        
        Returns
        -------
        tuple[bool, str]
            A tuple of (success, message):
            - success: True if submission succeeded, False if any step failed
            - message: Descriptive message about the result
              * On success: "Values are valid" (if mode="Check values") or "Values are submitted" (if mode="Normal submission") or "Values are submitted" (if mode="Forced submission")
              * On failure: Specific error message indicating what went wrong
        
        Raises
        ------
        RuntimeError
            If a recursive `submit_values()` call attempts to modify hook nexuses that are
            already being modified in the current submission. This indicates an incorrect
            implementation where a user-implemented callback (validation, completion, invalidation,
            reaction, or listener) is attempting to modify the same data during its own modification.
            
            Note: Recursive calls to `submit_values()` ARE allowed if they modify completely
            independent hook nexuses (no overlap). Only overlapping modifications are forbidden.
            
        Additionally, callback methods called during submission may raise exceptions:
            - `_add_values_to_be_updated()` may raise ValueError if value completion logic fails
            - `validate_complete_values_in_isolation()` may raise if validation logic fails
            
        Most validation errors are returned as (False, error_message) tuples rather than
        raised as exceptions.
        
        Notes
        -----
        **Performance Characteristics**:
        - O(1) value updates per nexus (reference assignment only)
        - O(n) where n = number of affected observables + hooks
        - Iterative completion phase may add overhead if many related values must be completed
        - No copying overhead regardless of value size or complexity
        
        **Thread Safety**:
        This method IS thread-safe. It uses a reentrant lock (RLock) to ensure that
        concurrent calls to `submit_values` are serialized. The lock protects the entire
        submission flow (all 6 phases), ensuring atomicity across the completion,
        validation, update, and notification phases. Multiple threads can safely call
        `submit_values` concurrently without external synchronization.
        
        **Reentrancy Protection**:
        This method uses thread-local state tracking to prevent modification of the same
        hook nexuses during nested `submit_values()` calls. Each thread maintains a set of
        currently active hook nexuses being modified. If a recursive call attempts to modify
        any nexus already in the active set, a RuntimeError is raised.
        
        **Independent Nested Submissions ARE Allowed**:
        Recursive `submit_values()` calls are permitted as long as they modify completely
        different hook nexuses (no overlap with the active set). This allows callbacks to
        trigger independent value changes in other parts of the system. For example, a
        listener on observable A can safely trigger an update to observable B, as long as
        B's hooks don't overlap with A's hooks.
        
        **Overlapping Modifications ARE Forbidden**:
        Attempting to modify a hook nexus that's already being modified in the current
        submission chain will raise RuntimeError. This enforces atomicity - each hook nexus
        can only be modified once per submission flow. Callbacks should return additional
        values to be included in the current atomic submission rather than triggering
        overlapping modifications.
        
        **Value Completion Cycle Detection**:
        The completion phase uses a simple iteration limit to prevent infinite loops.
        If an observable's `_add_values_to_be_updated()` continuously adds new values
        without converging, the system may not detect this efficiently.
        
        **Notification Order**:
        Listeners are notified in this order:
        1. Observable-level listeners (for observables that are BaseListeningProtocol)
        2. Hook-level listeners for owned hooks
        3. Hook-level listeners for floating hooks
        
        Examples
        --------
        Basic value submission:
        
        >>> hook = FloatingHook[int](42)
        >>> nexus = hook.hook_nexus
        >>> manager = NexusManager()
        >>> success, msg = manager.submit_values({nexus: 100})
        >>> success
        True
        >>> hook.value
        100
        
        Validation-only check:
        
        >>> hook = FloatingHook[int](42)
        >>> nexus = hook.hook_nexus
        >>> manager = NexusManager()
        >>> # Check if value would be valid without applying it
        >>> success, msg = manager.submit_values({nexus: 200}, mode="Check values")
        >>> success
        True
        >>> hook.value  # Value unchanged
        42
        
        Submitting complex objects by reference:
        
        >>> large_dict = {i: [j for j in range(1000)] for i in range(1000)}
        >>> hook = FloatingHook[dict](large_dict)
        >>> nexus = hook.hook_nexus
        >>> # Modify the dict in-place
        >>> large_dict[1000] = [999]
        >>> # Submit - no copying occurs, immediate update
        >>> manager.submit_values({nexus: large_dict})
        (True, 'Values are submitted')
        
        Independent recursive submissions (allowed):
        
        >>> hook1 = FloatingHook[int](1)
        >>> hook2 = FloatingHook[int](2)
        >>> def listener_triggers_independent_update():
        ...     # This is fine - hook2 is independent from hook1
        ...     hook2.submit_value(99)
        >>> hook1.add_listeners(listener_triggers_independent_update)
        >>> hook1.submit_value(42)
        (True, 'Values are submitted')
        >>> hook1.value
        42
        >>> hook2.value  # Also updated by the listener
        99
        
        Overlapping recursive submissions (forbidden):
        
        >>> hook = FloatingHook[int](1)
        >>> def bad_listener():
        ...     # This is BAD - trying to modify the same hook during its own update
        ...     hook.submit_value(99)
        >>> hook.add_listeners(bad_listener)
        >>> hook.submit_value(42)
        Traceback (most recent call last):
            ...
        RuntimeError: Recursive submit_values call detected with overlapping hook nexuses!
        
        See Also
        --------
        HookNexus : The data structure that holds synchronized hook values
        BaseCarriesHooks.submit_values : Higher-level interface for submitting values to observables
        FloatingHook.submit_value : Convenient method for submitting a single value to a floating hook
        """

        if isinstance(nexus_and_values, Sequence):
            # check if the sequence is a list of tuples of (Nexus[Any], Any) and that the hook nexuses are unique
            if not all(isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], Nexus) for item in nexus_and_values): # type: ignore
                raise ValueError("The sequence must be a list of tuples of (Nexus[Any], Any)")
            if len(set(item[0] for item in nexus_and_values)) != len(nexus_and_values):
                raise ValueError("The nexuses must be unique")
            nexus_and_values = dict(nexus_and_values)
        
        # Get the set of nexuses being submitted
        new_nexuses = set(nexus_and_values.keys())
        
        # Check for overlap with currently active nexuses (indicates incorrect implementation)
        active_nexuses: set["Nexus[Any]"] = getattr(self._thread_local, 'active_nexuses', set())
        overlapping_nexuses = active_nexuses & new_nexuses
        
        if overlapping_nexuses:
            raise RuntimeError(
                f"Recursive submit_values call detected with overlapping nexuses! " +
                f"This indicates an incorrect implementation. " +
                f"User-implemented callbacks (validation, completion, invalidation, reaction, listeners) " +
                f"attempted to modify {len(overlapping_nexuses)} nexus(es) that are already being modified " +
                f"in the current submission. Each nexus can only be modified once per atomic submission. " +
                f"Independent submissions to different nexuses are allowed."
            )
        
        with self._lock:
            # Add the new nexuses to the active set for this thread
            if not hasattr(self._thread_local, 'active_nexuses'):
                self._thread_local.active_nexuses = set()
            self._thread_local.active_nexuses.update(new_nexuses) # type: ignore
            
            try:
                return self._internal_submit_values(nexus_and_values, mode, logger)
            finally:
                # Always remove the nexuses we added, even if an error occurs
                self._thread_local.active_nexuses -= new_nexuses # type: ignore

    ########################################################################################################################
    # Helper Methods
    ########################################################################################################################

    @staticmethod
    def get_nexus_and_values(hooks: set["Hook[Any]"]) -> dict[Nexus[Any], Any]:
        """
        Get the nexus and values dictionary for a set of hooks.
        """
        nexus_and_values: dict[Nexus[Any], Any] = {}
        for hook in hooks:
            nexus_and_values[hook._get_nexus()] = hook.value # type: ignore
        return nexus_and_values
