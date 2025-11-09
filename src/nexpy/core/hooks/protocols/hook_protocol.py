from typing import TypeVar, runtime_checkable, TYPE_CHECKING, Literal, Mapping, Protocol

from ...auxiliary.listenable_protocol import ListenableProtocol
from ...publisher_subscriber.publisher_protocol import PublisherProtocol

if TYPE_CHECKING:
    from nexpy.core.nexus_system.nexus_manager import NexusManager
    from nexpy.core.nexus_system.nexus import Nexus
    from ....foundations.carries_single_hook_protocol import CarriesSingleHookProtocol

T = TypeVar("T")

@runtime_checkable
class HookProtocol(ListenableProtocol, PublisherProtocol, Protocol[T]):
    """
    Protocol for hook objects.
    """

    #########################################################
    # Public Protocol methods
    #########################################################

    #-------------------------------- value --------------------------------

    def get_value(self) -> T:
        """
        Get the value behind this hook.

        ** Thread-safe **
        """
        ...

    @property
    def value(self) -> T:
        """
        Get the value behind this hook.

        ** Thread-safe **
        """
        ...
    
    #-------------------------------- nexus_manager --------------------------------

    def get_nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this hook belongs to.

        ** Thread-safe **
        """
        ...

    @property
    def nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this hook belongs to.

        ** Thread-safe **
        """
        ...

    #-------------------------------- nexus --------------------------------

    def get_nexus(self) -> "Nexus[T]":
        """
        Get the nexus that this hook belongs to.

        ** Thread-safe **
        """
        ...

    @property
    def nexus(self) -> "Nexus[T]":
        """
        Get the nexus that this hook belongs to.

        ** Thread-safe **
        """
        ...

    #-------------------------------- join --------------------------------

    def join(self, target_hook: "HookProtocol[T]|CarriesSingleHookProtocol[T]", initial_sync_mode: Literal["use_caller_value", "use_target_value"], raise_join_error_flag: bool = True) -> tuple[bool, str]:
        """
        Join this hook to another hook.

        ** Thread-safe **

        Args:
            target_hook: The hook to join to
            initial_sync_mode: The initial synchronization mode
            raise_join_error_flag: Whether to raise a JoinError if the join fails

        Returns:
            A tuple containing a boolean indicating if the join was successful and a string message
        """
        ...

    def isolate(self) -> None:
        """
        Isolate this hook from the nexus.

        ** Thread-safe **
        """
        ...

    def is_joined_with(self, target_hook_or_nexus: "HookProtocol[T]|Nexus[T]|CarriesSingleHookProtocol[T]") -> bool:
        """
        Check if this hook is joined to another hook or the hook of a CarriesSingleHookProtocol.

        ** Thread-safe **
        """
        ...

    def is_joined(self) -> bool:
        """
        Check if this hook is joined to other hooks via a shared nexus.

        ** Thread-safe **
        """
        ...

    #########################################################
    # Internal Protocol methods
    #########################################################

    def _get_value(self) -> T:
        """
        Get the value behind this hook.
        """
        ...

    def _get_nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this hook belongs to.
        """
        ...

    def _get_nexus(self) -> "Nexus[T]":
        """
        Get the nexus that this hook belongs to.
        """
        ...

    def _join(self, target_hook: "HookProtocol[T]|CarriesSingleHookProtocol[T]", initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> tuple[bool, str]:
        """
        Join this hook to another hook.
        """
        ...

    def _isolate(self) -> None:
        """
        Isolate this hook from the nexus.
        """
        ...

    def _is_joined_with(self, target_hook_or_nexus: "HookProtocol[T]|Nexus[T]|CarriesSingleHookProtocol[T]") -> bool:
        """
        Check if this hook is joined to another hook or the hook of a CarriesSingleHookProtocol.
        """
        ...

    def _is_joined(self) -> bool:
        """
        Check if this hook is joined to other hooks via a shared nexus.
        """
        ...

    def _validate_value(self, value: T) -> tuple[bool, str]:
        """
        Validate if a value could be submitted to this hook, either internally or externally.

        Args:
            value: The value to validate

        Returns:
            A tuple containing a boolean indicating if the value is valid and a string message
        """
        ...

    @staticmethod
    def _validate_values(values: Mapping["HookProtocol[T]|CarriesSingleHookProtocol[T]", T]) -> tuple[bool, str]:
        """
        Validate if a values could be submitted to this hook, either internally or externally.

        Args:
            values: The values to validate

        Returns:
            A tuple containing a boolean indicating if the values are valid and a string message
        """
        ...