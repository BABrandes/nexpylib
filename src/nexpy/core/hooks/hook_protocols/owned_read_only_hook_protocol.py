from typing import Protocol, TypeVar, runtime_checkable

from .managed_hook_protocol import ManagedHookProtocol
from ..mixin_protocols.hook_with_owner_protocol import HookWithOwnerProtocol

T = TypeVar("T")


@runtime_checkable
class OwnedReadOnlyHookProtocol(ManagedHookProtocol[T], HookWithOwnerProtocol[T], Protocol[T]):
    """
    Protocol for owned read-only hook objects that cannot submit values.
    """