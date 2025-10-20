from typing import TypeVar, runtime_checkable, Protocol, TYPE_CHECKING, Mapping, Any, final, Optional, Hashable
from logging import Logger

from ...auxiliary.listening_protocol import ListeningProtocol
from ...nexus_system.has_nexus_manager_protocol import HasNexusManagerProtocol
from ...publisher_subscriber.publisher_protocol import PublisherProtocol
from ...nexus_system.has_nexus_protocol import HasNexusProtocol

if TYPE_CHECKING:
    from ...nexus_system.nexus import Nexus
    from ...nexus_system.nexus_manager import NexusManager

T = TypeVar("T")

@runtime_checkable
class HookWithGetterProtocol(ListeningProtocol, PublisherProtocol, HasNexusManagerProtocol, HasNexusProtocol[T], Hashable, Protocol[T]):
    """
    Protocol for getter hook objects that can get values.
    
    This protocol extends the base hook functionality with the ability to get values,
    making it suitable for getter hooks in observables that can get values.
    """    


    #########################################################
    # Public Properties and methods
    #########################################################

    @property
    def value(self) -> T:
        """
        Get the value behind this hook.
        
        ** Thread-safe **
        """
        ...

    @value.setter
    def value(self, value: T) -> None:
        raise ValueError("Value cannot be set for connection hooks without implementation of HookWithSetterProtocol")
        
    @property
    def previous_value(self) -> T:
        """
        Get the previous value behind this hook.

        ** Thread-safe **
        """
        ...

    #########################################################
    # Private Properties and methods
    #########################################################

    def _get_value(self) -> T:
        """
        Get the value behind this hook.

        ** This method is not thread-safe and should only be called by the get_value method.
        """
        ...

    def _get_previous_value(self) -> T:
        """
        Get the previous value behind this hook.

        ** This method is not thread-safe and should only be called by the get_previous_value method.
        """
        ...

    #########################################################
    # Final methods
    #########################################################

    @final
    def _validate_value(self, value: T, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Check if the value is valid for submission.

        ** This method is not thread-safe and should only be called by the validate_value method.
        
        Note: This method only validates, it does not submit values.
        """
        return self._get_nexus_manager().submit_values({self._get_nexus(): value}, mode="Check values", logger=logger) # type: ignore

    @staticmethod
    @final
    def _validate_values(values: Mapping["HookWithGetterProtocol[Any]", Any], *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Check if the values are valid for submission.

        ** This method is not thread-safe and should only be called by the validate_values method.
        
        Note: This method only validates, it does not submit values.
        """
        if len(values) == 0:
            return True, "No values provided"
        nexus_manager: "NexusManager" = next(iter(values.keys()))._get_nexus_manager()
        nexus_and_values: Mapping[Nexus[Any], Any] = {}
        for hook, value in values.items():
            if hook._get_nexus_manager() != nexus_manager:
                raise ValueError("The nexus managers must be the same")
            nexus_and_values[hook._get_nexus()] = value # type: ignore
        return nexus_manager.submit_values(nexus_and_values, mode="Check values", logger=logger)
