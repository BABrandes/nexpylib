from typing import Generic, TypeVar, Optional, Mapping, Any, Sequence, TYPE_CHECKING
import logging

from ..hook_protocols.full_hook_protocol import FullHookProtocol
from ..hook_bases.managed_hook_base import ManagedHookBase
from ...nexus_system.nexus_manager import NexusManager
from ...nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER
from ..mixin_protocols.hook_with_getter_protocol import HookWithGetterProtocol

if TYPE_CHECKING:
    from ....x_objects_base.carries_single_hook_protocol import CarriesSingleHookProtocol

T = TypeVar("T")


class FullHookBase(ManagedHookBase[T], FullHookProtocol[T], Generic[T]):
    """
    A base class for hooks with setter functionality (can submit values).
    
    Hook extends GetterHookBase to add the ability to submit values, making it suitable
    for primary hooks in observables that can be modified directly.
    
    Type Parameters:
        T: The type of value stored in this hook. Can be any Python type - primitives,
           collections, custom objects, etc.
    
    Multiple Inheritance:
        - GetterHookBase[T]: Provides all getter functionality and basic hook capabilities
        - HookProtocol[T]: Implements the full hook interface including submit_value method
        - Generic[T]: Type-safe generic value storage
    
    Key Capabilities (inherited from GetterHookBase):
        - **Value Storage**: Stores value in a centralized HookNexus
        - **Bidirectional Binding**: Can connect to other hooks for value synchronization
        - **Validation**: Supports validation callbacks before value changes
        - **Listeners**: Synchronous callbacks on value changes
        - **Publishing**: Asynchronous subscriber notifications
        - **Thread Safety**: All operations protected by reentrant lock
    
    Additional Capabilities (from HookProtocol):
        - **Value Submission**: Can submit values via submit_value() method
    
    Example:
        Basic standalone hook usage::
        
            from observables._hooks.hook_base import HookBase
            
            # Create a hook
            temperature = HookBase(20.0)
            
            # Add listener
            temperature.add_listeners(lambda: print(f"Temp: {temperature.value}"))
            
            # Change value
            temperature.submit_value(25.0)  # Prints: "Temp: 25.0"
            
            # Connect to another hook
            display = HookBase(0.0)
            temperature.connect_hook(display, "use_caller_value")
            
            # Now they're synchronized
            temperature.submit_value(30.0)
            print(display.value)  # 30.0
    """

    def __init__(
        self,
        value: T,
        nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER,
        logger: Optional[logging.Logger] = None
        ) -> None:
        """
        Initialize a new standalone Hook with setter functionality.
        
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
            Create hooks with different configurations::
            
                # Simple hook with default settings
                counter = HookBase(0)
                
                # Hook with custom nexus manager
                from observables._utils.nexus_manager import NexusManager
                custom_manager = NexusManager()
                custom_hook = HookBase(42, nexus_manager=custom_manager)
                
                # Hook with logging enabled
                import logging
                logger = logging.getLogger(__name__)
                logged_hook = HookBase("data", logger=logger)
        """
        ManagedHookBase.__init__(self, value, nexus_manager, logger) #type: ignore

    #########################################################
    # Public properties and methods
    #########################################################

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
        """
        Set the value behind this hook.

        ** Thread-safe **
        """
        with self._lock:
            self._change_value(value, logger=self._logger, raise_submission_error_flag=True)

    def change_value(self, value: T, *, logger: Optional[logging.Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Change the value behind this hook.

        ** Thread-safe **
        """
        with self._lock:
            return self._change_value(value, logger=logger, raise_submission_error_flag=raise_submission_error_flag)

    @staticmethod
    def change_values(hooks_and_values: Mapping["HookWithGetterProtocol[Any]|CarriesSingleHookProtocol[Any]", Any]|Sequence[tuple["HookWithGetterProtocol[Any]|CarriesSingleHookProtocol[Any]", Any]], *, logger: Optional[logging.Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Change the values behind this hook.

        ** Thread-safe **
        """
        return FullHookBase._change_values(hooks_and_values, logger=logger, raise_submission_error_flag=raise_submission_error_flag)

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook."""
        return f"Hook(v={self.value}, id={id(self)})"

    def __str__(self) -> str:
        """Get the string representation of this hook."""
        return f"Hook(v={self.value}, id={id(self)})"