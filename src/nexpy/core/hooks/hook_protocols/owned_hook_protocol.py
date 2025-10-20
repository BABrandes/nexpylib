from typing import Protocol, TypeVar, runtime_checkable

from .managed_hook_protocol import ManagedHookProtocol
from ..mixin_protocols.hook_with_owner_protocol import HookWithOwnerProtocol
from ..mixin_protocols.hook_with_connection_protocol import HookWithConnectionProtocol
from ..mixin_protocols.hook_with_getter_protocol import HookWithGetterProtocol
from ..mixin_protocols.hook_with_setter_protocol import HookWithSetterProtocol

T = TypeVar("T")

@runtime_checkable
class OwnedHookProtocol(ManagedHookProtocol[T], HookWithOwnerProtocol[T], HookWithConnectionProtocol[T], HookWithGetterProtocol[T], HookWithSetterProtocol[T], Protocol[T]):
    """
    Protocol for owned hook objects.
    """