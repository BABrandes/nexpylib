from typing import TypeVar, Any, Protocol, runtime_checkable

from .hook_protocol import HookProtocol
from ....foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol

T = TypeVar("T")
O = TypeVar("O", bound="CarriesSomeHooksProtocol[Any, Any]", covariant=True)

@runtime_checkable
class OwnedHookProtocol(HookProtocol[T], Protocol[T, O]):
    """
    Protocol for owned hook objects.
    """
    
    #-------------------------------- owner --------------------------------

    def get_owner(self) -> O:
        """
        Get the owner of this hook.

        ** Thread-safe **
        """
        ...

    @property
    def owner(self) -> O:
        """
        Get the owner of this hook. 

        ** Thread-safe **
        """
        ...