from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable, TypeVar
if TYPE_CHECKING:
    from ....foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol

T = TypeVar("T")

@runtime_checkable
class HookWithOwnerProtocol(Protocol[T]): # type: ignore
    """
    Protocol for hook objects that have an owner.
    """
    
    @property
    def owner(self) -> "CarriesSomeHooksProtocol[Any, Any]":
        """
        Get the owner of this hook.
        """
        ...

