from typing import Generic, Optional, TypeVar, Any
from logging import Logger

from .hook_protocols.owned_full_hook_protocol import OwnedFullHookProtocol

from ..auxiliary.listening_base import ListeningBase
from ..nexus_system.nexus_manager import NexusManager
from ..nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER
from ...x_objects_base.carries_some_hooks_protocol import CarriesSomeHooksProtocol

from .hook_bases.full_hook_base import FullHookBase

T = TypeVar("T")

class OwnedHook(FullHookBase[T], OwnedFullHookProtocol[T], ListeningBase, Generic[T]):
    """
    Hook owned by an X object, providing value access integrated with object's internal synchronization.
    
    OwnedHook is a hook that belongs to a reactive object (like XValue, XDict, XList, etc.).
    Unlike FloatingHook, OwnedHook participates in its owner's internal synchronization
    protocol, ensuring that updates maintain object invariants.
    
    Key Differences from FloatingHook
    ---------------------------------
    - **Owner Integration**: Validation and updates coordinated through owner
    - **Internal Sync**: Participates in owner's multi-hook synchronization
    - **Lifecycle**: Tied to owner's lifecycle
    - **Validation**: Uses owner's validation methods, not isolated callbacks
    
    Key Features
    ------------
    - **Full Value Access**: Both read and write operations
    - **Owner-Based Validation**: Validation delegated to owner object
    - **Automatic Invalidation**: Triggers owner invalidation on changes
    - **Listener Management**: Subscribe to value changes
    - **Join/Isolate**: Can participate in Nexus fusion domains
    - **Thread-Safe**: All operations protected by locks
    
    Parameters
    ----------
    owner : CarriesSomeHooksProtocol[Any, Any]
        The X object that owns this hook
    initial_value : T
        Initial value for the hook
    logger : Optional[Logger], optional
        Logger instance for debugging operations
    nexus_manager : NexusManager, optional
        The NexusManager instance coordinating this hook's synchronization.
        Defaults to DEFAULT_NEXUS_MANAGER (global singleton).
    
    Attributes
    ----------
    value : T
        Current value (read/write property, inherited from FullHookBase)
    owner : CarriesSomeHooksProtocol
        The X object that owns this hook
    
    Examples
    --------
    OwnedHooks are typically created internally by X objects:
    
    >>> import nexpy as nx
    >>> 
    >>> # XValue creates an OwnedHook internally
    >>> value = nx.XValue(42)
    >>> hook = value.hook  # This is an OwnedHook
    >>> 
    >>> # Check ownership
    >>> print(type(hook))  # OwnedHook
    >>> print(hook.owner is value)  # True
    
    Validation is coordinated through the owner:
    
    >>> import nexpy as nx
    >>> 
    >>> # XDictSelect has multiple owned hooks with coordinated validation
    >>> select = nx.XDictSelect({"a": 1, "b": 2}, key="a")
    >>> 
    >>> # When key_hook changes, owner validates consistency with value_hook
    >>> select.key = "b"  # Owner ensures value is updated atomically
    >>> print(select.value)  # 2 (automatically updated by internal sync)
    
    Joining owned hooks:
    
    >>> import nexpy as nx
    >>> 
    >>> value1 = nx.XValue(10)
    >>> value2 = nx.XValue(20)
    >>> 
    >>> # Join their hooks to synchronize the XValue objects
    >>> value1.hook.join(value2.hook)
    >>> 
    >>> value1.value = 30
    >>> print(value2.value)  # 30 (synchronized through Nexus fusion)
    
    See Also
    --------
    FloatingHook : Independent hook not owned by any object
    XValue : Reactive value that owns a hook
    Hook : Protocol for bidirectional hooks
    
    Notes
    -----
    Thread Safety:
        All OwnedHook operations are thread-safe, protected by both the hook's
        internal lock and the NexusManager's global lock during value submissions.
    
    Internal Synchronization:
        When an OwnedHook's value changes, the owner's `_add_values_to_be_updated()`
        and `_validate_complete_values_in_isolation()` methods are called to ensure
        all related hooks (in the same object) remain consistent.
    
    Validation Delegation:
        Unlike FloatingHook which uses isolated validation callbacks, OwnedHook
        delegates validation to its owner via the `is_valid()` method. This allows
        the owner to perform cross-hook validation and maintain object invariants.
    
    Invalidation:
        After successful value updates, the owner's `_invalidate()` method is called,
        allowing the owner to recompute derived state or clear caches.
    """

    def __init__(
            self,
            owner: CarriesSomeHooksProtocol[Any, Any],
            initial_value: T,
            logger: Optional[Logger] = None,
            nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
            ) -> None:

        ListeningBase.__init__(self, logger)
        FullHookBase.__init__( # type: ignore
            self,
            value=initial_value,
            nexus_manager=nexus_manager,
            logger=logger
        )

        self._owner = owner

    @property
    def owner(self) -> CarriesSomeHooksProtocol[Any, T]:
        """Get the owner of this hook."""
        return self._owner

    def _get_owner(self) -> CarriesSomeHooksProtocol[Any, T]:
        """Get the owner of this hook."""

        with self._lock:
            owner = self._owner
            return owner

    def invalidate_owner(self) -> None:
        """Invalidate the owner of this hook."""
        self.owner._invalidate() # type: ignore

    def is_valid(self, value: T) -> bool:
        """Check if the hook is valid."""

        hook_key = self.owner._get_hook_key(self) # type: ignore
        success, _ = self.owner._validate_value(hook_key, value) # type: ignore
        return success

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook."""
        return f"OwnedHook(v={self.value}, id={id(self)})"

    def __str__(self) -> str:
        """Get the string representation of this hook."""
        return f"OwnedHook(v={self.value}, id={id(self)})"