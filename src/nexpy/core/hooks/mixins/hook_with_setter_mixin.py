from typing import TypeVar, Optional, Mapping, Any, Sequence, TYPE_CHECKING, Generic
from logging import Logger

from nexpy.core.hooks.protocols.hook_protocol import HookProtocol
from nexpy.core.nexus_system.nexus import Nexus
from nexpy.core.nexus_system.nexus_manager import NexusManager

if TYPE_CHECKING:
    from ....foundations.carries_single_hook_protocol import CarriesSingleHookProtocol
    from ..protocols.hook_protocol import HookProtocol

T = TypeVar("T")

class HookWithSetterMixin(HookProtocol[T], Generic[T]):
    """
    Mixin for hook objects that can change their value.
    """

    def __init__(self) -> None:
        """
        Initialize the hook with a setter.
        """
        pass

    def _change_value(self, value: T, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Change the value behind this hook.

        ** This method is not thread-safe and should only be called by the change_value method.
        """
        
        return self._get_nexus_manager().submit_values({self._get_nexus(): value}, mode="Normal submission", logger=logger)

    @staticmethod
    def _change_values(
        hooks_and_values: Mapping["HookProtocol[Any]|CarriesSingleHookProtocol[Any]", Any]|Sequence[tuple["HookProtocol[Any]|CarriesSingleHookProtocol[Any]", Any]],
        *,
        logger: Optional[Logger] = None,
        ) -> tuple[bool, str]:
        """
        Change the values behind this hook.

        ** This method is not thread-safe and should only be called by the change_values method.
        """
        
        from ....foundations.carries_single_hook_protocol import CarriesSingleHookProtocol

        nexus_and_values: dict["Nexus[Any]", Any] = {}
        if isinstance(hooks_and_values, Mapping):
            for hook, value in hooks_and_values.items():
                if isinstance(hook, HookProtocol):
                    nexus_and_values[hook._get_nexus()] = value
                if isinstance(hook, CarriesSingleHookProtocol):
                    nexus_and_values[hook._get_nexus()] = value # type: ignore

        elif isinstance(hooks_and_values, Sequence): # type: ignore
            for hook, value in hooks_and_values:
                if isinstance(hook, HookProtocol):
                    hook_nexus: Nexus[Any] = hook._get_nexus()
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