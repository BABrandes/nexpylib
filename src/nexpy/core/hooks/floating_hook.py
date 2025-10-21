from typing import Generic, TypeVar, Optional, Callable
from logging import Logger

from ..auxiliary.listening_base import ListeningBase
from nexpy.core.nexus_system.nexus_manager import NexusManager
from nexpy.core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore

from .hook_bases.full_hook_base import FullHookBase
from .mixin_protocols.hook_with_isolated_validation_protocol import HookWithIsolatedValidationProtocol
from .mixin_protocols.hook_with_reaction_protocol import HookWithReactionProtocol

T = TypeVar("T")

class FloatingHook(FullHookBase[T], HookWithIsolatedValidationProtocol[T], HookWithReactionProtocol, ListeningBase, Generic[T]):
    """
    Independent hook not owned by any x_object, providing full read/write access with validation.
    
    FloatingHook is a standalone hook that can be used for:
    - Simple reactive values without complex object structure
    - Intermediate connection points in fusion networks
    - Testing and prototyping
    - Joining disparate systems
    
    Unlike OwnedHook (which belongs to an X object), FloatingHook is completely
    independent and manages its own lifecycle.
    
    Key Features
    ------------
    - **Full Value Access**: Both read and write operations
    - **Validation Support**: Optional validation callback for value changes
    - **Reaction Callbacks**: Custom side effects on value changes
    - **Listener Management**: Subscribe to value changes
    - **Join/Isolate**: Participate in Nexus fusion domains
    - **Thread-Safe**: All operations protected by locks
    
    Parameters
    ----------
    value : T
        Initial value for the hook
    reaction_callback : Optional[Callable[[], tuple[bool, str]]], optional
        Callback executed after value changes. Should return (success, message).
        Allows custom side effects like logging, caching, etc.
    isolated_validation_callback : Optional[Callable[[T], tuple[bool, str]]], optional
        Validation function called before accepting new values.
        Should return (True, "message") if valid, (False, "error") if invalid.
        When hooks are joined, validation from all hooks in the fusion domain must pass.
    logger : Optional[Logger], optional
        Logger instance for debugging operations
    nexus_manager : NexusManager, optional
        The NexusManager instance coordinating this hook's synchronization.
        Defaults to DEFAULT_NEXUS_MANAGER (global singleton).
    
    Attributes
    ----------
    value : T
        Current value (read/write property)
    
    Examples
    --------
    Create a simple floating hook:
    
    >>> import nexpy as nx
    >>> hook = nx.FloatingHook(42)
    >>> print(hook.value)
    42
    >>> hook.value = 100
    >>> print(hook.value)
    100
    
    With validation:
    
    >>> def validate_positive(value):
    ...     if value > 0:
    ...         return True, "Valid"
    ...     return False, "Value must be positive"
    >>> 
    >>> hook = nx.FloatingHook(10, isolated_validation_callback=validate_positive)
    >>> hook.value = 20  # OK
    >>> hook.value = -5  # Raises ValueError: Value must be positive
    
    With reaction callback:
    
    >>> def on_change():
    ...     print(f"Value changed to: {hook.value}")
    ...     return True, "Logged"
    >>> 
    >>> hook = nx.FloatingHook(0, reaction_callback=on_change)
    >>> hook.value = 42  # Prints: "Value changed to: 42"
    
    Joining hooks:
    
    >>> hook1 = nx.FloatingHook(10)
    >>> hook2 = nx.FloatingHook(20)
    >>> hook1.join(hook2)
    >>> print(hook1.value, hook2.value)  # 10 10 (synchronized)
    >>> hook1.value = 30
    >>> print(hook2.value)  # 30
    
    See Also
    --------
    OwnedHook : Hook owned by an X object
    XValue : High-level reactive value wrapping a FloatingHook
    Hook : Protocol for bidirectional hooks
    
    Notes
    -----
    Thread Safety:
        All FloatingHook operations are thread-safe, protected by both the hook's
        internal lock and the NexusManager's global lock during value submissions.
    
    Memory Management:
        FloatingHooks store values by reference only (no copying). The hook itself
        can be garbage collected when no longer referenced, and its weak reference
        in the Nexus will be automatically cleaned up.
    
    Validation:
        When hooks are joined into a fusion domain, value updates must pass validation
        from ALL hooks in the domain. If any hook rejects the value, the entire
        update is rejected and all hooks retain their previous value.
    """

    def __init__(
        self,
        value: T,
        reaction_callback: Optional[Callable[[], tuple[bool, str]]] = None,
        isolated_validation_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: "NexusManager" = _DEFAULT_NEXUS_MANAGER
        ) -> None:
        
        self._reaction_callback = reaction_callback
        self._isolated_validation_callback = isolated_validation_callback

        ListeningBase.__init__(self, logger)
        FullHookBase.__init__( # type: ignore
            self,
            value=value,
            nexus_manager=nexus_manager,
            logger=logger
        )

    def react_to_value_changed(self) -> None:
        """
        Execute reaction callback after value has changed.
        
        This method is called automatically by the NexusManager after a successful
        value update (Phase 6 of the submission protocol). It allows the hook to
        perform custom side effects like logging, caching, triggering computations, etc.
        
        The reaction callback is executed synchronously before listener notifications,
        ensuring that any state updates from the reaction are visible to listeners.
        
        Notes
        -----
        - Executed AFTER the value has been committed (cannot reject changes)
        - Runs synchronously within the submission lock
        - Should not trigger recursive value updates to the same hook
        - Can safely update independent hooks
        
        See Also
        --------
        validate_value_in_isolation : Validation before value changes
        """
        if self._reaction_callback is not None:
            self._reaction_callback()

    def validate_value_in_isolation(self, value: T) -> tuple[bool, str]:
        """
        Validate a proposed value change for this hook.
        
        This method is called during the validation phase (Phase 4) of the value
        submission protocol, before any values are actually updated. It allows the
        hook to reject invalid values based on custom validation logic.
        
        When hooks are joined in a fusion domain, ALL hooks must accept the value
        for the update to proceed. If any hook rejects the value, the entire
        update is rejected and all hooks retain their previous values (atomicity).
        
        Parameters
        ----------
        value : T
            The proposed new value to validate
        
        Returns
        -------
        tuple[bool, str]
            (success, message) where:
            - success=True means value is acceptable
            - success=False means value is rejected
            - message provides details about validation result
        
        Examples
        --------
        >>> def validate_positive(value):
        ...     if value > 0:
        ...         return True, "Valid positive number"
        ...     return False, "Value must be positive"
        >>> 
        >>> hook = nx.FloatingHook(10, isolated_validation_callback=validate_positive)
        >>> success, msg = hook.validate_value_in_isolation(20)
        >>> print(success)  # True
        >>> success, msg = hook.validate_value_in_isolation(-5)
        >>> print(success)  # False
        
        Notes
        -----
        - Called during Phase 4 (Validation) of the submission protocol
        - Runs before any values are updated (can prevent changes)
        - Executed synchronously within the submission lock
        - Must not have side effects (pure validation only)
        
        See Also
        --------
        react_to_value_changed : Reaction after value changes
        """
        if self._isolated_validation_callback is not None:
            return self._isolated_validation_callback(value)
        else:
            return True, "No isolated validation callback provided"

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook."""
        return f"FloatingHook(v={self.value}, id={id(self)})"
    
    def __str__(self) -> str:
        """Get the string representation of this hook."""
        return f"FloatingHook(v={self.value}, id={id(self)})"
