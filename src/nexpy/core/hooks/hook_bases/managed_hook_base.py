from typing import Generic, TypeVar, Optional, Literal
from threading import RLock
import logging
import inspect

from ..hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ..mixin_protocols.hook_with_connection_protocol import HookWithConnectionProtocol

from ...utils import log
from ...auxiliary.listening_base import ListeningBase
from nexpy.core.nexus_system.nexus_manager import NexusManager
from nexpy.core.nexus_system.nexus import Nexus
from nexpy.core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from ....foundations.carries_single_hook_protocol import CarriesSingleHookProtocol
from ...publisher_subscriber.publisher import Publisher

T = TypeVar("T")


class ManagedHookBase(ManagedHookProtocol[T], Publisher, ListeningBase, Generic[T]):
    """
    A base class for managed hooks that participate in transitive synchronization.
    
    ManagedHook references a Nexus and can be joined with other hooks to form fusion domains.
    When joined, the respective Nexuses undergo fusion: original Nexuses are destroyed and 
    a new unified Nexus is created, enabling transitive synchronization.
    
    Example:
        hook_a.join(hook_b)  # Creates fusion domain AB
        hook_c.join(hook_d)  # Creates fusion domain CD
        hook_b.join(hook_c)  # Fuses both domains → ABCD
        # Now all four hooks share one Nexus and are transitively synchronized
    
    It provides a lightweight way to create reactive values with full hook system capabilities.
    
    Type Parameters:
        T: The type of value stored in this hook. Can be any Python type - primitives,
           collections, custom objects, etc.
    
    Multiple Inheritance:
        - ManagedHookProtocol[T]: Implements the managed hook interface for binding and value access
        - Publisher: Can publish notifications to subscribers (async, sync, direct modes)
        - ManagedHookProtocol[T]: Implements the managed hook interface for binding and value access
        - BaseListening: Support for listener callbacks (synchronous notifications)
        - Generic[T]: Type-safe generic value storage
    
    Key Capabilities:
        - **Value Storage**: Stores value in a centralized HookNexus
        - **Bidirectional Binding**: Can connect to other hooks for value synchronization
        - **Validation**: Supports validation callbacks before value changes
        - **Listeners**: Synchronous callbacks on value changes
        - **Publishing**: Asynchronous subscriber notifications
        - **Thread Safety**: All operations protected by reentrant lock
        - **Getter**: Can get values directly
    
    Three Notification Mechanisms:
        1. **Listeners**: Synchronous callbacks via `add_listeners()`
        2. **Subscribers**: Async notifications via `add_subscriber()` (Publisher)
        3. **Connected Hooks**: Bidirectional sync via `connect_hook()`
    
    Example:
        Basic standalone getter hook usage::
        
            from observables._hooks.getter_hook_base import GetterHookBase
            
            # Create a getter hook
            temperature = GetterHookBase(20.0)
            
            # Add listener
            temperature.add_listeners(lambda: print(f"Temp: {temperature.value}"))
            
            # Connect to another hook
            display = GetterHookBase(0.0)
            temperature.connect_hook(display, "use_caller_value")
            
            # Values can only be changed through connected getter hooks
    """

    def __init__(
        self,
        value: T,
        nexus_manager: "NexusManager" = _DEFAULT_NEXUS_MANAGER,
        logger: Optional[logging.Logger] = None
        ) -> None:
        """
        Initialize a new standalone GetterHook.
        
        Args:
            value: The initial value for this hook. Can be any Python type.
            nexus_manager: The NexusManager that coordinates value updates and
                validation across all hooks. If not provided, uses the global
                DEFAULT_NEXUS_MANAGER which is shared across the entire application.
                Default is DEFAULT_NEXUS_MANAGER.
            logger: Optional logger for debugging hook operations. If provided,
                operations like connection, disconnection, and value changes will
                be logged. Default is None.
        
        Note:
            The hook is created with publishing disabled by default 
            (preferred_publish_mode="off"). This is because hooks are typically
            used with the listener pattern rather than pub-sub. You can enable
            publishing by adding subscribers and calling publish() explicitly.
        
        Example:
            Create getter hooks with different configurations::
            
                # Simple getter hook with default settings
                counter = GetterHookBase(0)
                
                # Getter hook with custom nexus manager
                from observables._utils.nexus_manager import NexusManager
                custom_manager = NexusManager()
                custom_hook = GetterHookBase(42, nexus_manager=custom_manager)
                
                # Getter hook with logging enabled
                import logging
                logger = logging.getLogger(__name__)
                logged_hook = GetterHookBase("data", logger=logger)
        """

        from nexpy.core.nexus_system.nexus import Nexus

        ListeningBase.__init__(self, logger)
        self._value = value
        self._nexus_manager = nexus_manager

        Publisher.__init__(self, preferred_publish_mode="off", logger=logger)

        self._hook_nexus: Nexus[T] = Nexus(value, hooks={self}, nexus_manager=nexus_manager, logger=logger)
        self._lock: RLock = RLock()

    #########################################################
    # Public properties and methods
    #########################################################

    @property
    def nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this hook belongs to.

        ** Thread-safe **
        """
        with self._lock:
            return self._nexus_manager

    @property
    def value(self) -> T:
        """
        Get the value behind this hook.

        ** Thread-safe **
        
        Returns:
            The immutable value stored in the hook nexus.
            
        Note:
            All values are automatically converted to immutable forms by the nexus system:
            - dict → immutables.Map
            - list → tuple
            - set → frozenset
            - Primitives and frozen dataclasses remain unchanged
            
            Since values are immutable, it's safe to use them directly.
        """
        with self._lock:
            return self._get_value()

    @value.setter
    def value(self, value: T) -> None:
        raise ValueError("Value cannot be set for managed hooks without implementation of HookWithSetterProtocol")

    @property
    def previous_value(self) -> T:
        """
        Get the previous value behind this hook.

        ** Thread-safe **
        """
        with self._lock:
            return self._get_previous_value()

    def join(self, target_hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]", initial_sync_mode: Literal["use_caller_value", "use_target_value"] = "use_target_value") -> tuple[bool, str]:
        """
        Join this hook to another hook.

        ** Thread-safe **

        Args:
            target_hook: The hook or CarriesSingleHookProtocol to connect to
            initial_sync_mode: Determines which hook's value is used initially. Defaults to "use_target_value"
                (adopts the target's value, useful when joining to potentially large nexuses).
                - "use_caller_value": Use this hook's value (caller = self)
                - "use_target_value": Use the target hook's value (default)

        Returns:
            A tuple containing a boolean indicating if the connection was successful and a string message
        """
        
        # Get the actual hook if CarriesSingleHookProtocol is passed
        actual_target = target_hook._get_single_hook() if isinstance(target_hook, CarriesSingleHookProtocol) else target_hook # type: ignore
        
        # Validate that target is not None
        if actual_target is None: # type: ignore
            raise ValueError("Cannot join to None target")
        
        # Deadlock prevention: Acquire locks in consistent order (by object ID)
        # This prevents circular wait when two threads try to join A→B and B→A simultaneously
        if id(self) < id(actual_target):
            # Acquire in order: self first, then target
            with self._lock:
                with actual_target._lock: # type: ignore
                    return self._join(target_hook, initial_sync_mode)
        else:
            # Acquire in order: target first, then self  
            with actual_target._lock: # type: ignore
                with self._lock:
                    return self._join(target_hook, initial_sync_mode)

    def isolate(self) -> None:
        """
        Isolate this hook from the hook nexus.

        ** Thread-safe **
        """
        with self._lock:
            self._isolate()

    
    def is_joined_with(self, hook_or_carries_single_hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]") -> bool:
        """
        Check if this hook is connected to another hook or CarriesSingleHookLike.

        ** Thread-safe **

        Args:
            hook_or_carries_single_hook: The hook or CarriesSingleHookProtocol to check if it is connected to

        Returns:
            True if the hook is connected to the other hook or CarriesSingleHookProtocol, False otherwise
        """
        with self._lock:
            return self._is_joined_with(hook_or_carries_single_hook)

    def is_linked(self) -> bool:
        """
        Check if this hook is connected to another hook.

        ** Thread-safe **

        Returns:
            True if the hook is connected to another hook, False otherwise
        """
        with self._lock:
            return self._is_linked()

    #########################################################
    # Private methods
    #########################################################

    def _get_value(self) -> T:
        """
        Get the value behind this hook.

        ** This method is not thread-safe and should only be called by the get_value method.
        """
        return self._hook_nexus.stored_value

    def _get_previous_value(self) -> T:
        """
        Get the previous value behind this hook.

        ** This method is not thread-safe and should only be called by the get_previous_value method.
        """
        return self._hook_nexus.previous_stored_value

    def _get_nexus(self) -> "Nexus[T]":
        """
        Get the hook nexus that this hook belongs to.

        ** This method is not thread-safe and should only be called by the get_hook_nexus method.
        """
        return self._hook_nexus

    def _get_nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this hook belongs to.

        ** This method is not thread-safe and should only be called by the get_nexus_manager method.
        """
        return self._nexus_manager

    def _join(self, target_hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]", initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> tuple[bool, str]:
        """
        Join this hook to another hook.

        ** This method is not thread-safe and should only be called by the join method.

        This method implements the core hook connection process:
        
        1. Get the two nexuses from the hooks to connect
        2. Submit one of the hooks' value to the other nexus
        3. If successful, both nexus must now have the same value
        4. Merge the nexuses to one -> Connection established!
        
        After connection, both hooks will share the same nexus and remain synchronized.

        Args:
            target_hook: The hook or CarriesSingleHookProtocol to connect to
            initial_sync_mode: Determines which hook's value is used initially:
                - "use_caller_value": Use this hook's value (caller = self)
                - "use_target_value": Use the target hook's value
            
        Returns:
            A tuple containing a boolean indicating if the connection was successful and a string message
        """

        from nexpy.core.nexus_system.nexus import Nexus


        if target_hook is None: # type: ignore
            raise ValueError("Cannot connect to None hook")

        if isinstance(target_hook, CarriesSingleHookProtocol):
            target_hook = target_hook._get_single_hook() # type: ignore
        
        # Prevent joining a hook to itself
        if self is target_hook:
            raise ValueError("Cannot join a hook to itself")
        
        # Deadlock prevention: Check if hooks are already joined
        # If they share the same nexus, joining again is a no-op (but not an error)
        if self._hook_nexus is target_hook._get_nexus():
            log(self, "join", self._logger, True, "Hooks already share the same nexus - no join needed")
            return True, "Hooks already joined"
        
        if initial_sync_mode == "use_caller_value":
            success, msg = Nexus[T].join_hook_pairs((self, target_hook))
        elif initial_sync_mode == "use_target_value":                
            success, msg = Nexus[T].join_hook_pairs((target_hook, self))
        else:
            raise ValueError(f"Invalid sync mode: {initial_sync_mode}")

        log(self, "join", self._logger, success, msg)

        return success, msg
    
    def _isolate(self) -> None:
        """
        Isolate this hook from the hook nexus.

        ** This method is not thread-safe and should only be called by the isolate method.

        If this is the corresponding nexus has only this one hook, nothing will happen.
        """

        log(self, "disconnect_hook", self._logger, True, "Disconnecting hook initiated")

        from nexpy.core.nexus_system.nexus import Nexus

        # Check if we're being called during garbage collection by inspecting the call stack
        is_being_garbage_collected = any(frame.function == '__del__' for frame in inspect.stack())

        # If we're being garbage collected and not in the nexus anymore,
        # it means other hooks were already garbage collected and their weak
        # references were cleaned up. This is fine - just skip the disconnect.
        if is_being_garbage_collected and self not in self._hook_nexus.hooks:
            log(self, "disconnect", self._logger, True, "Hook already removed during garbage collection, skipping disconnect")
            return
        
        if self not in self._hook_nexus.hooks:
            raise ValueError("Hook was not found in its own hook nexus!")
        
        if len(self._hook_nexus.hooks) <= 1:
            # If we're the last hook, we're already effectively disconnected
            log(self, "disconnect", self._logger, True, "Hook was the last in the nexus, so it is already 'disconnected'")
            return
        
        # Create a new isolated nexus for this hook
        new_hook_nexus = Nexus(self.value, hooks={self}, nexus_manager=self._nexus_manager, logger=self._logger)
        
        # Remove this hook from the current nexus
        self._hook_nexus.remove_hook(self)
        
        # Update this hook's nexus reference
        self._hook_nexus = new_hook_nexus

        log(self, "disconnect", self._logger, True, "Successfully disconnected hook")
        
        # The remaining hooks in the old nexus will continue to be bound together
        # This effectively breaks the connection between this hook and all others


    def _is_joined_with(self, hook_or_carries_single_hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]") -> bool:
        """
        Check if this hook is connected to another hook or CarriesSingleHookLike.

        ** This method is not thread-safe and should only be called by the is_joined_with method.

        Args:
            hook_or_carries_single_hook: The hook or CarriesSingleHookProtocol to check if it is connected to

        Returns:
            True if the hook is connected to the other hook or CarriesSingleHookProtocol, False otherwise
        """

        if isinstance(hook_or_carries_single_hook, CarriesSingleHookProtocol):
            hook_or_carries_single_hook = hook_or_carries_single_hook._get_single_hook() # type: ignore
        return hook_or_carries_single_hook in self._hook_nexus.hooks

    def _is_linked(self) -> bool:
        """
        Check if this hook is connected to another hook.

        ** This method is not thread-safe and should only be called by the is_linked method.
        """

        return len(self._hook_nexus.hooks) > 1

    def _replace_nexus(self, nexus: "Nexus[T]") -> None:
        """
        Replace the nexus that this hook belongs to.
        
        NOTE: This method assumes the caller already holds self._lock for thread safety.
        It does NOT acquire the lock itself to avoid deadlocks during join operations.

        Args:
            nexus: The new nexus to replace the current one
        """
        self._hook_nexus = nexus
        log(self, "replace_nexus", self._logger, True, "Successfully replaced nexus")

    def __hash__(self) -> int:
        """
        Hash the hook based on its identity.
        """
        return hash(id(self))

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook."""
        return f"GetterHook(v={self.value}, id={id(self)})"

    def __str__(self) -> str:
        """Get the string representation of this hook."""
        return f"GetterHook(v={self.value}, id={id(self)})"
