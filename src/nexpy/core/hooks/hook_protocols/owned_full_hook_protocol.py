from typing import Protocol, TypeVar, runtime_checkable

from .full_hook_protocol import FullHookProtocol
from ..mixin_protocols.hook_with_owner_protocol import HookWithOwnerProtocol

T = TypeVar("T")


@runtime_checkable
class OwnedFullHookProtocol(FullHookProtocol[T], HookWithOwnerProtocol[T], Protocol[T]):
    ...