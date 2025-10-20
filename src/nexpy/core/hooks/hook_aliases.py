# observables/hooks.py
from typing import Protocol, TypeVar, runtime_checkable
from .hook_protocols.full_hook_protocol import FullHookProtocol as _FullHookProtocol
from .hook_protocols.read_only_hook_protocol import ReadOnlyHookProtocol as _ReadOnlyHookProtocol

T = TypeVar("T")

@runtime_checkable
class Hook(_FullHookProtocol[T], Protocol[T]):
    """Bidirectional hook (send + receive)."""
    pass

@runtime_checkable
class ReadOnlyHook(_ReadOnlyHookProtocol[T], Protocol[T]):
    """Receive-only hook (no send)."""
    pass

__all__ = ["Hook", "ReadOnlyHook"]