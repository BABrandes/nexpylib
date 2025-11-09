"""
NexPy — Transitive Synchronization and Shared-State Fusion for Python
======================================================================

NexPy (distributed on PyPI as `nexpylib`) is a reactive synchronization framework
for Python that provides a universal mechanism for maintaining coherent shared state
across independent objects through **Nexus fusion** and **internal Hook synchronization**.

Core Concepts
-------------

Nexus Fusion
~~~~~~~~~~~~
Unlike traditional reactive frameworks that propagate changes through dependency graphs,
NexPy creates **fusion domains** where multiple hooks share a single **Nexus**—a
centralized synchronization core that holds and propagates state.

When two hooks are **joined**, their respective Nexuses undergo a **fusion process**:
1. Original Nexuses are destroyed
2. A new unified Nexus is created to hold the shared value
3. Both hooks now belong to the same fusion domain

This joining is:
- **Symmetric** — `A.join(B)` is equivalent to `B.join(A)`
- **Transitive** — Joining creates equivalence chains across all connected hooks
- **Non-directional** — There's no "master" or "slave"; all hooks are equal participants

Example: Transitive Synchronization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> import nexpy as nx
    >>> 
    >>> # Create four independent hooks
    >>> A = nx.FloatingHook(1)
    >>> B = nx.FloatingHook(2)
    >>> C = nx.FloatingHook(3)
    >>> D = nx.FloatingHook(4)
    >>> 
    >>> # Create first fusion domain
    >>> A.join(B)  # → Nexus_AB containing A and B
    >>> 
    >>> # Create second fusion domain
    >>> C.join(D)  # → Nexus_CD containing C and D
    >>> 
    >>> # Fuse both domains by connecting any pair
    >>> B.join(C)  # → Nexus_ABCD
    >>> 
    >>> # All four hooks now share the same Nexus and value
    >>> # Even though A and D were never joined directly!
    >>> A.value = 42
    >>> print(B.value, C.value, D.value)  # 42 42 42

Internal Synchronization
~~~~~~~~~~~~~~~~~~~~~~~~
In addition to global fusion, NexPy maintains **atomic internal synchronization**
among related hooks within a single object through a **transaction-like validation
and update protocol**.

When one hook changes (e.g., `key` in `XDictSelect`), NexPy:
1. Determines which related Nexuses must update (e.g., `value`, `dict`)
2. Queries each affected Nexus via a readiness check (validation pre-step)
3. If all Nexuses report readiness, applies all updates atomically
4. Otherwise rejects the change to maintain global validity

This ensures the system is:
- **Atomic** — All updates occur together or not at all
- **Consistent** — Constraints are always satisfied
- **Isolated** — Concurrent modifications are safely locked
- **Durable (logical)** — Once accepted, coherence persists

Quick Start
-----------

Simple Reactive Value
~~~~~~~~~~~~~~~~~~~~~

    >>> import nexpy as nx
    >>> 
    >>> # Create a reactive value
    >>> temperature = nx.XValue(20.0)
    >>> 
    >>> # Read and update
    >>> print(temperature.value)  # 20.0
    >>> temperature.value = 25.5
    >>> print(temperature.value)  # 25.5

Hook Fusion Across Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> import nexpy as nx
    >>> 
    >>> # Create two independent reactive values
    >>> sensor = nx.XValue(20.0)
    >>> display = nx.XValue(0.0)
    >>> 
    >>> # Fuse them so they share the same state
    >>> sensor.value_hook.join(display.value_hook)
    >>> 
    >>> # Now they're synchronized
    >>> sensor.value = 25.5
    >>> print(display.value)  # 25.5

Reactive Collections
~~~~~~~~~~~~~~~~~~~~

    >>> import nexpy as nx
    >>> 
    >>> # Reactive list
    >>> numbers = nx.XList([1, 2, 3])
    >>> numbers.append(4)
    >>> print(numbers.list)  # [1, 2, 3, 4]
    >>> 
    >>> # Reactive dict
    >>> config = nx.XDict({"debug": False})
    >>> config["debug"] = True
    >>> print(config.dict)  # {"debug": True}

Selection Objects with Internal Sync
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> import nexpy as nx
    >>> 
    >>> # Create a selection from a dictionary
    >>> options = nx.XDictSelect(
    ...     {"low": 1, "medium": 5, "high": 10},
    ...     key="medium"
    ... )
    >>> 
    >>> print(options.value)  # 5
    >>> 
    >>> # Change selection → value automatically updated
    >>> options.key = "high"
    >>> print(options.value)  # 10
    >>> 
    >>> # Change value → dict automatically updated
    >>> options.value = 15
    >>> print(options.dict["high"])  # 15

Architecture
------------

NexPy is organized into four layers:

1. **X Objects Layer** — High-level reactive data structures
   (XValue, XDict, XList, XSet, XDictSelect, etc.)
   
2. **Hook Layer** — Connection points for fusion
   (FloatingHook, OwnedHook)
   
3. **Nexus Layer** — Fusion domain management
   (Nexus, NexusManager)
   
4. **Application Layer** — Your code

Key Features
------------

- **Transitive Hook Fusion** — Join any hooks to create fusion domains with
  automatic transitive synchronization
  
- **Atomic Internal Synchronization** — ACID-like guarantees for multi-hook objects
  with transaction-style validation and updates
  
- **Reactive Collections** — XList, XSet, XDict with full Python protocol support
  
- **Selection Objects** — XDictSelect, XSetSingleSelect with multi-selection variants
  
- **Thread-Safe by Design** — All operations protected by reentrant locks
  
- **Multiple Notification Philosophies** — Listeners (sync), Publish-Subscribe (async),
  and Hooks (bidirectional with validation)

Thread Safety
-------------

All NexPy operations are thread-safe. The NexusManager uses a reentrant lock to
protect the complete synchronization flow, ensuring safe concurrent access from
multiple threads without requiring external locks.

Reentrancy protection prevents recursive modifications of the same Nexus while
allowing independent nested submissions to different Nexuses.

See Also
--------

Documentation:
    - Usage Guide: docs/usage.md
    - Internal Synchronization: docs/internal_sync.md
    - Architecture: docs/architecture.md
    - API Reference: docs/api_reference.md
    - Examples: docs/examples.md
    - Concepts: docs/concepts.md

Links:
    - PyPI: https://pypi.org/project/nexpylib/
    - GitHub: https://github.com/babrandes/nexpylib
    - Issues: https://github.com/babrandes/nexpylib/issues

License
-------

Apache License 2.0

Copyright (c) 2025 Benedikt Axel Brandes
"""

from .foundations.x_base import XBase
from .foundations.x_singleton_base import XSingletonBase
from .foundations.x_composite_base import XCompositeBase

from .x_objects.single_value_like.x_single_value import XSingleValue as XValue

from .x_objects.list_like.x_list import XList
from .x_objects.set_like.x_set import XSet
from .x_objects.dict_like.x_dict import XDict

from .x_objects.single_value_like.protocols import XSingleValueProtocol
from .x_objects.list_like.protocols import XListProtocol
from .x_objects.set_like.protocols import XSetProtocol
from .x_objects.dict_like.protocols import XDictProtocol

from .x_objects.set_like.x_selection_set import XSelectionSet as XSetSingleSelect
from .x_objects.set_like.x_optional_selection_set import XOptionalSelectionSet as XSetSingleSelectOptional
from .x_objects.set_like.x_multi_selection_set import XMultiSelectionSet as XSetMultiSelect

from .x_objects.dict_like.x_selection_dict import XSelectionDict as XDictSelect
from .x_objects.dict_like.x_optional_selection_dict import XOptionalSelectionDict as XDictSelectOptional
from .x_objects.dict_like.x_selection_dict_with_default import XSelectionDictWithDefault as XDictSelectDefault
from .x_objects.dict_like.x_optional_selection_dict_with_default import XOptionalSelectionDictWithDefault as XDictSelectOptionalDefault

from .x_objects.function_like.function_values import FunctionValues
from .x_objects.function_like.x_function import XFunction
from .x_objects.function_like.x_one_way_function import XOneWayFunction


from .x_objects.specialized.xobject_rooted_paths import XRootedPaths
from .x_objects.specialized.xobject_subscriber import XSubscriber

# Adapter objects
from .x_objects.adapters.x_optional_adapter import XOptionalAdapter
from .x_objects.adapters.x_optional_placeholder_adapter import XOptionalPlaceholderAdapter
from .x_objects.adapters.x_int_float_adapter import XIntFloatAdapter
from .x_objects.adapters.x_set_sequence_adapter import XSetSequenceAdapter
from .x_objects.adapters.x_sequence_items_adapter import XSequenceItemsAdapter

# Hook protocols
from nexpy.core.hooks.protocols.hook_protocol import HookProtocol as Hook

# Hook implementations
from nexpy.core.hooks.implementations.floating_hook import FloatingHook

from .core.publisher_subscriber.publisher_protocol import PublisherProtocol
from .core.publisher_subscriber.value_publisher import ValuePublisher

from .core.nexus_system.update_function_values import UpdateFunctionValues
from .core.nexus_system.system_analysis import write_report

# Configuration module
from . import default

__all__ = [
    # Modern clean aliases
    'XValue',
    'XList',
    'XSet',
    'XDict',
    'XDictSelect',

    # Selection objects (set-like)
    'XSetSingleSelect',
    'XSetSingleSelectOptional',
    'XSetMultiSelect',

    # Selection objects (dict-like)
    'XDictSelect',
    'XDictSelectOptional',
    'XDictSelectDefault',
    'XDictSelectOptionalDefault',

    # Function objects
    'XFunction',
    'XOneWayFunction',

    # Adapter objects
    'XOptionalAdapter',
    'XOptionalPlaceholderAdapter',
    'XIntFloatAdapter',
    'XSetSequenceAdapter',
    'XSequenceItemsAdapter',

    # Specialized objects
    'XSubscriber',
    'XRootedPaths',
    
    # Base classes
    'XBase',
    'XSingletonBase',
    'XCompositeBase',

    # Modern protocol aliases
    'XSingleValueProtocol',
    'XDictProtocol',
    'XListProtocol',
    'XSetProtocol',

    # Hooks (user-facing)
    'FloatingHook',
    'Hook',
    
    # Function utilities
    'FunctionValues',
    'UpdateFunctionValues',

    # Publisher/Subscriber
    'PublisherProtocol',
    'ValuePublisher',

    # Utilities
    'write_report',

    # Configuration
    'default',
]

# Package metadata
try:
    from ._version import __version__, __version_tuple__
except ImportError:
    __version__ = "0.6.0"
    __version_tuple__ = (0, 6, 0)

__author__ = 'Benedikt Axel Brandes'
__year__ = '2025'

# Package description
__description__ = 'NexPy - Transitive synchronization and shared-state fusion for Python through Nexus fusion and atomic internal synchronization'
__keywords__ = ['nexus', 'system', 'reactive', 'binding', 'data-binding', 'reactive-programming']
__url__ = 'https://github.com/babrandes/nexpylib'
__project_urls__ = {
    'Bug Reports': 'https://github.com/babrandes/nexpylib/issues',
    'Source': 'https://github.com/babrandes/nexpylib',
    'Documentation': 'https://github.com/babrandes/nexpylib#readme',
}

# Development status
__classifiers__ = [
    'Development Status :: 3 - Alpha',  # Not production ready
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.13',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]
