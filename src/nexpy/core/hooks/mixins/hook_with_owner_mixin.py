from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from ....foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol

O = TypeVar("O", bound="CarriesSomeHooksProtocol[Any, Any]", covariant=True)

class HookWithOwnerMixin(Generic[O]):
    """
    Mixin for hook objects that have an owner.
    """

    def __init__(self, owner: O) -> None:
        """
        Initialize the hook with an owner.
        """
        self._owner = owner

    def _get_owner(self) -> O:
        """
        Get the owner of this hook.
        """

        return self._owner

