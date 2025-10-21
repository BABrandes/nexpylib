from typing import TypeVar, runtime_checkable, Protocol, TYPE_CHECKING, Mapping, Any, final, Optional, Sequence
from logging import Logger

from .hook_with_connection_protocol import HookWithConnectionProtocol


from ...auxiliary.listening_protocol import ListeningProtocol
from nexpy.core.nexus_system.has_nexus_manager_protocol import HasNexusManagerProtocol
from ...publisher_subscriber.publisher_protocol import PublisherProtocol
from nexpy.core.nexus_system.submission_error import SubmissionError

if TYPE_CHECKING:
    from nexpy.core.nexus_system.nexus import Nexus
    from nexpy.core.nexus_system.nexus_manager import NexusManager
    from .hook_with_getter_protocol import HookWithGetterProtocol
    from ....x_objects_base.carries_single_hook_protocol import CarriesSingleHookProtocol

T = TypeVar("T")

@runtime_checkable
class HookWithSetterProtocol(ListeningProtocol, PublisherProtocol, HasNexusManagerProtocol, Protocol[T]):
    """
    Protocol for hook objects that can submit values (have setter functionality).
    
    This protocol extends the base hook functionality with the ability to submit values,
    making it suitable for primary hooks in observables that can be modified directly.
    """    
    @property
    def value(self) -> T:
        """
        Get the value behind this hook.

        ** The returned value is a copy, so modifying is allowed.
        """
        ...

    @value.setter
    def value(self, value: T) -> None:
        """
        Set the value behind this hook.
        """
        ...

    def change_value(self, value: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Submit a value to this hook. This will not invalidate the hook!
        """
        ...

    @staticmethod
    def change_values(hooks_and_values: Mapping["HookWithGetterProtocol[Any]|CarriesSingleHookProtocol[Any]", Any]|Sequence[tuple["HookWithGetterProtocol[Any]|CarriesSingleHookProtocol[Any]", Any]], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Submit values to this hook. This will not invalidate the hook!
        """
        ...

    #########################################################
    # Final methods - With submission capability
    #########################################################

    @final
    def _change_value(self, value: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Submit a value to this hook. This will not invalidate the hook!

        ** This method is not thread-safe and should only be called by the change_value method.

        Args:
            value: The value to submit
            logger: The logger to use
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails
        """

        if not isinstance(self, HookWithConnectionProtocol):
            raise ValueError("This hook does not have connection functionality")

        hook_nexus: Nexus[T] = self._get_nexus() # type: ignore
        success, msg = self.nexus_manager.submit_values({hook_nexus: value}, mode="Normal submission", logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, value)
        return success, msg


    @final
    @staticmethod
    def _change_values(hooks_and_values: Mapping["HookWithGetterProtocol[Any]|CarriesSingleHookProtocol[Any]", Any]|Sequence[tuple["HookWithGetterProtocol[Any]|CarriesSingleHookProtocol[Any]", Any]], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Submit values to this hook. This will not invalidate the hook!

        ** This method is not thread-safe and should only be called by the change_values method.

        Args:
            values: The values to submit
            logger: The logger to use
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails
        """

        if len(hooks_and_values) == 0:
            return True, "No values provided"

        from ....x_objects_base.carries_single_hook_protocol import CarriesSingleHookProtocol

        nexus_and_values: dict["Nexus[Any]", Any] = {}
        if isinstance(hooks_and_values, Mapping):
            for hook, value in hooks_and_values.items():
                if isinstance(hook, HookWithConnectionProtocol):
                    nexus_and_values[hook._get_nexus()] = value # type: ignore
                if isinstance(hook, CarriesSingleHookProtocol):
                    nexus_and_values[hook._get_nexus()] = value # type: ignore

        elif isinstance(hooks_and_values, Sequence): # type: ignore
            for hook, value in hooks_and_values:
                if isinstance(hook, HookWithConnectionProtocol):
                    hook_nexus: Nexus[Any] = hook._get_nexus() # type: ignore
                    if hook_nexus in nexus_and_values:
                        raise ValueError("All hook nexuses must be unique")
                    nexus_and_values[hook_nexus] = value
                if isinstance(hook, CarriesSingleHookProtocol):
                    nexus_and_values[hook._get_nexus()] = value # type: ignore
        else:
            raise ValueError("hooks_and_values must be a mapping or a sequence")

        nexus: Nexus[Any] = nexus_and_values[next(iter(nexus_and_values.keys()))]
        nexus_manager: "NexusManager" = nexus._nexus_manager # type: ignore
        return nexus_manager.submit_values(nexus_and_values, mode="Normal submission", logger=logger)