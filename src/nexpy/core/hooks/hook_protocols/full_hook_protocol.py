from typing import TypeVar, runtime_checkable, Protocol

from ...auxiliary.listening_protocol import ListeningProtocol
from nexpy.core.nexus_system.has_nexus_manager_protocol import HasNexusManagerProtocol
from ...publisher_subscriber.publisher_protocol import PublisherProtocol
from ..hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ..mixin_protocols.hook_with_setter_protocol import HookWithSetterProtocol

T = TypeVar("T")

@runtime_checkable
class FullHookProtocol(ManagedHookProtocol[T], HookWithSetterProtocol[T], ListeningProtocol, PublisherProtocol, HasNexusManagerProtocol, Protocol[T]):
    """
    Protocol for full hook objects (Getter and Setter).
    """