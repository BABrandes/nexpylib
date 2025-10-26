from typing import Mapping, Any, Optional, Callable, Literal, Sequence, TYPE_CHECKING
import weakref

from threading import RLock, local
from logging import Logger

if TYPE_CHECKING:
    from ..hooks.protocols.hook_protocol import HookProtocol
    from .nexus import Nexus

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
        super().__init__()

        # ----------- Thread Safety -----------

        self._lock = RLock()  # Thread-safe lock for submit_values operations
        self._thread_local = local()  # Thread-local storage for tracking active hook nexuses

        # ----------- Nexus Tracking -----------

        self._registered_nexuses: list[weakref.ref["Nexus[Any]"]] = []  # Weak references to all registered nexuses
        self._next_nexus_id: int = 1  # Counter for generating unique nexus IDs

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
    # Nexus Tracking Methods
    ##################################################################################################################

    def _generate_nexus_id(self) -> str:
        """Generate a unique nexus ID.
        
        Returns:
            A unique string identifier for a nexus in the format "nexus_{id}".
        """
        nexus_id = f"nexus_{self._next_nexus_id}"
        self._next_nexus_id += 1
        return nexus_id

    def _register_nexus(self, nexus: "Nexus[Any]") -> None:
        """Register a nexus with this manager for tracking purposes (internal use only).
        
        Args:
            nexus: The nexus to register. A weak reference will be stored.
        """
        self._registered_nexuses.append(weakref.ref(nexus))

    def _unregister_nexus(self, nexus: "Nexus[Any]") -> None:
        """Unregister a nexus from this manager (internal use only).
        
        Args:
            nexus: The nexus to unregister.
        """
        # Remove the weak reference to this nexus
        nexus_ref_to_remove = None
        for nexus_ref in self._registered_nexuses:
            if nexus_ref() is nexus:
                nexus_ref_to_remove = nexus_ref
                break
        
        if nexus_ref_to_remove is not None:
            self._registered_nexuses.remove(nexus_ref_to_remove)

    def _cleanup_dead_nexus_references(self) -> None:
        """Remove dead weak references from the registered nexuses list."""
        alive_refs: list[weakref.ref["Nexus[Any]"]] = []
        for nexus_ref in self._registered_nexuses:
            if nexus_ref() is not None:
                alive_refs.append(nexus_ref)
        
        self._registered_nexuses = alive_refs

    def get_active_nexuses(self) -> list["Nexus[Any]"]:
        """Get all currently active nexuses registered with this manager.
        
        Returns:
            List of active nexuses. Dead references are automatically cleaned up.
        """
        self._cleanup_dead_nexus_references()
        
        active_nexuses: list["Nexus[Any]"] = []
        for nexus_ref in self._registered_nexuses:
            nexus = nexus_ref()
            if nexus is not None:
                active_nexuses.append(nexus)
        
        return active_nexuses

    def get_nexus_count(self) -> int:
        """Get the number of currently active nexuses.
        
        Returns:
            Number of active nexuses registered with this manager.
        """
        self._cleanup_dead_nexus_references()
        return len(self._registered_nexuses)

    ##################################################################################################################
    # Synchronization of Nexus and Values
    ##################################################################################################################

    def _internal_submit_values(self, nexus_and_values: Mapping["Nexus[Any]", Any], mode: Literal["Normal submission", "Forced submission", "Check values"], logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Internal implementation of submit_values with optimized performance.

        Comprehensive performance analysis shows that internal_submit_2 is superior
        across ALL tested scenarios with speedups ranging from 47x to 11,280x.
        
        Performance characteristics:
        - Small scale: 47-133x speedup
        - Medium scale: 1,000-2,000x speedup  
        - Large scale: 7,000-11,000x speedup
        - Memory usage: 100-1,300x more efficient
        
        Therefore, we always use the optimized implementation.
        """
        from .internal_submit_methods.internal_submit_3 import internal_submit_values
        return internal_submit_values(self, nexus_and_values, mode, logger)

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
            # Import Nexus here for isinstance check at runtime
            from .nexus import Nexus
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
    def get_nexus_and_values(hooks: set["HookProtocol[Any]"]) -> Mapping["Nexus[Any]", Any]:
        """
        Get the nexus and values dictionary for a set of hooks.
        """
        nexus_and_values: dict["Nexus[Any]", Any] = {}
        for hook in hooks:
            nexus_and_values[hook._get_nexus()] = hook.value # type: ignore
        return nexus_and_values
