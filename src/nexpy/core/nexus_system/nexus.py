from typing import Generic, Optional, TypeVar, TYPE_CHECKING, Any
import logging
import weakref
import time

from ..auxiliary.utils import log

if TYPE_CHECKING:
    from ..hooks.protocols.hook_protocol import HookProtocol
    from ...foundations.carries_single_hook_protocol import CarriesSingleHookProtocol
    from .nexus_manager import NexusManager
    
T = TypeVar("T")

class Nexus(Generic[T]):
    """
    Shared synchronization core for transitive hook fusion.

    A Nexus represents a fusion domain — a group of hooks that share the same value 
    and are synchronized together. When hooks are joined, their Nexuses undergo fusion:
    the original Nexuses are destroyed and a new unified Nexus is created.
    
    This creates transitive synchronization: joining A→B and B→C automatically 
    synchronizes A and C, forming a dynamic equivalence network.
    
    Type Parameters:
        T: The type of value stored in this nexus. All hooks in this nexus must
           have compatible types with T.
    
    Architecture:
        - **Centralized Storage**: Each nexus stores exactly one value
        - **Multiple Hooks**: Many hooks can reference the same nexus
        - **Automatic Merging**: When hooks connect, their nexuses merge
        - **Weak References**: Hooks are stored as weak refs for automatic cleanup
        - **Synchronous Updates**: All hooks see value changes simultaneously
    
    Key Features:
        - Value storage with previous value tracking
        - Hook group management via weak references
        - Thread-safe operations (relies on NexusManager's lock)
        - Automatic dead reference cleanup
        - Integration with NexusManager for validation
    
    Lifecycle:
        1. **Creation**: Created with initial value and set of hooks
        2. **Merging**: Multiple nexuses can merge when hooks connect
        3. **Updates**: Values updated through NexusManager.submit_values()
        4. **Cleanup**: Dead hook references automatically cleaned up
    
    Example:
        Direct nexus usage (typically created automatically)::
        
            from ...nexus_system.nexus import Nexus
            from observables._hooks.hook import Hook
            
            # Create hooks
            hook1 = Hook(42)
            hook2 = Hook(42)
            
            # Create a shared nexus
            shared_nexus = HookNexus(
                value=100,
                hooks={hook1, hook2},
                nexus_manager=DEFAULT_NEXUS_MANAGER
            )
            
            # Both hooks now share the same value
            print(hook1.value)  # 100
            print(hook2.value)  # 100
    """

    def __init__(
        self,
        value: T,
        hooks: set["HookProtocol[T]"] = set["HookProtocol[T]"](), # type: ignore
        logger: Optional[logging.Logger] = None,
        nexus_manager: Optional["NexusManager"] = None
        ) -> None:
        """
        Initialize a new HookNexus.
        
        Args:
            value: The initial value to store in this nexus. This is the shared value
                that all hooks in this nexus will reference.
            hooks: Set of Hook instances that should share this value. Each hook will
                be stored as a weak reference for automatic cleanup. Default is empty set.
            logger: Optional logger for debugging hook operations. If provided, logs
                will be generated for hook addition, removal, and merging. Default is None.
            nexus_manager: The NexusManager responsible for coordinating value updates
                and validation. If None, uses the global DEFAULT_NEXUS_MANAGER.
        
        Example:
            Create nexus with specific hooks::
            
                hook1 = Hook(0)
                hook2 = Hook(0)
                
                # Create nexus containing both hooks
                nexus = HookNexus(
                    value=42,
                    hooks={hook1, hook2},
                    logger=my_logger,
                    nexus_manager=custom_manager
                )
                
                # All hooks in the nexus share the same value
                assert hook1.value == 42
                assert hook2.value == 42
        """
        super().__init__()
        
        from .default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
        
        if nexus_manager is None:
            nexus_manager = _DEFAULT_NEXUS_MANAGER

        # Generate a meaningful ID for this nexus using the manager's counter
        self._nexus_id: str = nexus_manager._generate_nexus_id() # type: ignore
        self._creation_time: float = time.time()
        
        self._nexus_manager: "NexusManager" = nexus_manager
        self._hooks: set[weakref.ref["HookProtocol[T]"]] = {weakref.ref(hook) for hook in hooks}
        self._stored_value: T = value
        self._previous_stored_value: T = value
        self._logger: Optional[logging.Logger] = logger
        self._submit_depth_counter: int = 0
        self._submit_touched_hooks: set["HookProtocol[T]"] = set()
        
        # Track hook count for performance optimization
        self._hook_count: int = len(hooks)

        # Register this nexus with the manager for tracking
        self._nexus_manager._register_nexus(self) # type: ignore

        log(self, "HookNexus.__init__", self._logger, True, f"Successfully initialized hook nexus with ID {self._nexus_id}")

    def __del__(self) -> None:
        """Cleanup when nexus is destroyed."""
        try:
            # Unregister from manager if it still exists
            if hasattr(self, '_nexus_manager') and hasattr(self._nexus_manager, '_unregister_nexus'):
                self._nexus_manager._unregister_nexus(self) # type: ignore
        except Exception:
            # Ignore errors during cleanup - the manager might already be destroyed
            pass

    def _get_hooks(self) -> set["HookProtocol[T]"]:
        """Get the actual hooks from weak references, filtering out dead references."""
        alive_hooks: set["HookProtocol[T]"] = set()
        dead_refs: set[weakref.ref["HookProtocol[T]"]] = set()
        
        for hook_ref in self._hooks:
            hook = hook_ref()
            if hook is not None:
                alive_hooks.add(hook)
            else:
                dead_refs.add(hook_ref)
        
        # Remove dead references and update count
        if dead_refs:
            self._hooks -= dead_refs
            self._hook_count -= len(dead_refs)
        
        return alive_hooks

    def add_hook(self, hook: "HookProtocol[T]") -> tuple[bool, str]:
        self._hooks.add(weakref.ref(hook))
        self._hook_count += 1
        log(self, "add_hook", self._logger, True, "Successfully added hook")
        return True, "Successfully added hook"

    def remove_hook(self, hook: "HookProtocol[T]") -> tuple[bool, str]:
        try:
            # Find and remove the weak reference to this hook
            hook_ref_to_remove = None
            for hook_ref in self._hooks:
                if hook_ref() is hook:
                    hook_ref_to_remove = hook_ref
                    break
            
            if hook_ref_to_remove is not None:
                self._hooks.remove(hook_ref_to_remove)
                self._hook_count -= 1
                log(self, "remove_hook", self._logger, True, "Successfully removed hook")
                return True, "Successfully removed hook"
            else:
                log(self, "remove_hook", self._logger, False, "Hook not found")
                return False, "Hook not found"
        except KeyError:
            return False, "Hook not found in nexus"

    @property
    def hooks(self) -> tuple["HookProtocol[T]", ...]:
        return tuple(self._get_hooks())
    
    @property
    def hook_count(self) -> int:
        """
        Get the number of hooks in this nexus.
        
        Returns:
            The number of hooks currently connected to this nexus.
        """
        return self._hook_count
    
    @property
    def stored_value(self) -> Any:
        """
        Get the value of the Nexus.

        Returns:
            The value stored in this Nexus.
            
        """
        return self._stored_value

    @property
    def previous_stored_value(self) -> Any:
        """
        Get the previous stored value of the Nexus.

        Returns:
            The previous value stored in this Nexus.
        """
        return self._previous_stored_value

    @property
    def nexus_id(self) -> str:
        """
        Get the unique ID of this nexus.

        Returns:
            A unique string identifier for this nexus, useful for tracking and debugging.
        """
        return self._nexus_id

    @property
    def creation_time(self) -> float:
        """
        Get the creation timestamp of this nexus.

        Returns:
            Unix timestamp when this nexus was created.
        """
        return self._creation_time

    @staticmethod
    def _create_merged_nexuses(*nexuses: "Nexus[T]") -> "Nexus[T]":
        """
        Merge multiple hook nexuses into a single hook nexus.

        - There must not be any overlapping hooks in the input nexuses
        - The hooks must be synced to the same value (already ensured via submit_values)
        - Compatible types (e.g., set/frozenset) are allowed
        - The hooks in both nexuses must be disjoint, if not something went wrong in the binding system

        Args:
            *hook_nexuses: The hook nexuses to merge

        Returns:
            A new hook nexus that contains all the hooks from the input nexuses

        Raises:
            ValueError: If the hook nexuses are not disjoint
        """
        
        if len(nexuses) == 0:
            raise ValueError("No hook nexuses provided")
        
        # Get the first hook nexus's value as the reference
        reference_value = nexuses[0]._stored_value

        # Check that all nexus managers are the same
        for nexus in nexuses:
            if nexus._nexus_manager != nexuses[0]._nexus_manager:
                raise ValueError("The nexus managers must be the same")
        nexus_manager: "NexusManager" = nexuses[0]._nexus_manager
        
        # Note: We don't check for strict type equality anymore since the values
        # have already been synchronized via submit_values before merging.
        # Compatible types like set/frozenset can be merged as they share the same conceptual value.

        # Check if any nexuses have overlapping hooks (not disjoint) and collect all hooks
        # Optimize: Use a single set to track all hooks instead of O(n²) pairwise intersection
        all_hooks: set["HookProtocol[T]"] = set()
        list_of_hook_sets: list[set["HookProtocol[T]"]] = []
        
        for hook_nexus in nexuses:
            hook_set = hook_nexus._get_hooks()
            if all_hooks & hook_set:  # Check for intersection with existing hooks
                raise ValueError("The hook nexuses must be disjoint")
            all_hooks.update(hook_set)
            list_of_hook_sets.append(hook_set)  # Store for later use
        
        # Create new merged nexus with the reference value and empty hooks (will be added below)
        merged_nexus: Nexus[T] = Nexus[T](
            value=reference_value,
            hooks=set(),
            nexus_manager=nexus_manager,
        )
        
        # Add all hooks to the merged nexus (reuse the already computed hook sets)
        for hook_set in list_of_hook_sets:
            for hook in hook_set:
                merged_nexus.add_hook(hook)
        
        return merged_nexus
    
    @staticmethod
    def join_hook_pairs(*hook_pairs: tuple["HookProtocol[T]|CarriesSingleHookProtocol[T]", "HookProtocol[T]|CarriesSingleHookProtocol[T]"]) -> tuple[bool, str]:
        """
        Join a list of hook pairs together.

        This method implements the core hook connection process:
        
        1. Get the two nexuses from the hooks to connect
        2. Submit one of the hooks' value to the other nexus
        3. If successful, both nexus must now have the same value
        4. Merge the nexuses to one -> Connection established!
        
        The value of the first hook in each pair will be used to set the value of the second hook.
        After successful linking, both hooks will share the same nexus and remain synchronized.

        Args:
            *hook_pairs: The pairs of hooks to connect. Each pair is (source_hook, target_hook)
                        where source_hook's value will be submitted to target_hook's nexus.

        Returns:
            A tuple containing a boolean indicating if the connection was successful and a string message
            
        Raises:
            ValueError: If nexus managers differ between hooks or if linking fails
        """

        # Step 1: Validate that all nexus managers are the same
        for hook_pair in hook_pairs:
            if hook_pair[0].nexus_manager != hook_pair[1].nexus_manager:  # type: ignore
                raise ValueError("The nexus managers must be the same")
        nexus_manager = hook_pairs[0][0].nexus_manager  # type: ignore

        # Step 2: Link values from source hooks to target nexuses
        # This ensures both nexuses have the same value before merging
        nexus_and_values: dict["Nexus[Any]", Any] = {}
        for hook_pair in hook_pairs:
            nexus_to_take_value_from: Nexus[Any] = hook_pair[0]._get_nexus() # type: ignore
            nexus_to_be_updated: Nexus[Any] = hook_pair[1]._get_nexus() # type: ignore
            nexus_and_values[nexus_to_be_updated] = nexus_to_take_value_from.stored_value
        success, msg = nexus_manager.submit_values(nexus_and_values)  # type: ignore
        if not success:
            raise ValueError(msg)  # type: ignore
        
        # Step 3: Merge nexuses now that they have the same value
        # This establishes the connection by making both hooks share the same nexus
        for hook_pair in hook_pairs:
            hook_nexus_1: Nexus[Any] = hook_pair[0]._get_nexus() # type: ignore   
            hook_nexus_2: Nexus[Any] = hook_pair[1]._get_nexus() # type: ignore
            
            # Skip if hooks already share the same nexus (already joined)
            if hook_nexus_1 is hook_nexus_2:
                continue
                
            merged_nexus: Nexus[T] = Nexus[T]._create_merged_nexuses(hook_nexus_1, hook_nexus_2)
            
            # Update all hooks to point to the merged nexus
            # NOTE: Caller (join method) already holds locks in proper order via lock ordering
            for hook in merged_nexus._get_hooks():
                hook._nexus = merged_nexus # type: ignore  # Direct assignment bypasses _replace_nexus lock

        return True, "Successfully linked hook pairs"
    
    @staticmethod
    def link_hooks(source_hook: "HookProtocol[T]", target_hook: "HookProtocol[T]") -> tuple[bool, str]:
        """
        Link two hooks together.

        Args:
            source_hook: The hook to link to the target hook
            target_hook: The hook to link to the source hook

        Raises:
            ValueError: If the hooks are not of the same type
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        
        # Check that all nexus managers are the same
        if source_hook._get_nexus_manager() != target_hook._get_nexus_manager(): # type: ignore
            raise ValueError("The nexus managers must be the same")
        nexus_manager: "NexusManager" = source_hook._get_nexus_manager() # type: ignore

        # Validate that both hooks are not None
        if source_hook is None or target_hook is None: # type: ignore
            raise ValueError("Cannot connect None hooks")
        
        # Check if the hooks are already connected
        if source_hook._get_nexus() == target_hook._get_nexus(): # type: ignore
            return True, "Hooks are already connected"
        
        # Ensure that the value in both hook nexuses is the same
        # The source_hook's value becomes the source of truth
        success, msg = nexus_manager.submit_values({target_hook._get_nexus(): source_hook.value})  # type: ignore
        if not success:
            raise ValueError(msg)
            
        # Then merge the hook nexuses
        # Use the synchronized value for the merged group
        merged_nexus: Nexus[T] = Nexus[T]._create_merged_nexuses(source_hook._get_nexus(), target_hook._get_nexus()) # type: ignore
        
        # Replace all hooks' hook nexuses with the merged one
        for hook in merged_nexus._get_hooks():
            hook._replace_nexus(merged_nexus) # type: ignore

        return True, "Successfully linked hooks"

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook nexus."""
        return f"Nexus(id={self._nexus_id}, v={self.stored_value}, {len(self._get_hooks())} hooks)"
    
    def __str__(self) -> str:
        """Get the string representation of this hook nexus."""
        return f"Nexus(id={self._nexus_id}, v={self.stored_value})"