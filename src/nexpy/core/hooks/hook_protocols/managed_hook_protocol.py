from typing import Protocol, TypeVar, runtime_checkable, Hashable

from ..mixin_protocols.hook_with_connection_protocol import HookWithConnectionProtocol
from ..mixin_protocols.hook_with_getter_protocol import HookWithGetterProtocol
from nexpy.core.nexus_system.has_nexus_manager_protocol import HasNexusManagerProtocol
from nexpy.core.nexus_system.has_nexus_protocol import HasNexusProtocol
T = TypeVar("T")

@runtime_checkable
class ManagedHookProtocol(HookWithConnectionProtocol[T], HookWithGetterProtocol[T], HasNexusManagerProtocol, HasNexusProtocol[T], Hashable, Protocol[T]):
    """
    Protocol for managed hook objects.
    """