"""
nexpy - A Python library for scientific computing and data analysis.

This package provides tools and utilities for various scientific computing tasks.
"""

from .x_objects.x_any_value import XAnyValue as XValue

from .x_objects.list_like.x_list import XList
from .x_objects.set_like.x_set import XSet
from .x_objects.dict_like.x_dict import XDict

from .x_objects.list_like.protocols import XListProtocol
from .x_objects.set_like.protocols import XSetProtocol
from .x_objects.dict_like.protocols import XDictProtocol

from .x_objects.set_like.x_selection_set import XSelectionSet as XSetSelect
from .x_objects.set_like.x_optional_selection_set import XOptionalSelectionSet as XSetOptionalSelect
from .x_objects.set_like.x_multi_selection_set import XMultiSelectionSet as XSetMultiSelect

from .x_objects.dict_like.x_selection_dict import XSelectionDict as XDictSelect
from .x_objects.dict_like.x_optional_selection_dict import XOptionalSelectionDict as XDictSelectOptional
from .x_objects.dict_like.x_selection_dict_with_default import XSelectionDictWithDefault as XDictSelectDefault
from .x_objects.dict_like.x_optional_selection_dict_with_default import XOptionalSelectionDictWithDefault as XDictSelectOptionalDefault

from .x_objects.function_like.function_values import FunctionValues
from .x_objects.function_like.x_function import XFunction
from .x_objects.function_like.x_one_way_function import XOneWayFunction


from .x_objects.complex.xobject_rooted_paths import XRootedPaths
from .x_objects.complex.xobject_block_none import XBlockNone
from .x_objects.complex.xobject_subscriber import XSubscriber

from .core.hooks.floating_hook import FloatingHook
from .core.hooks.hook_aliases import Hook, ReadOnlyHook

from .core.publisher_subscriber.publisher_protocol import PublisherProtocol
from .core.publisher_subscriber.value_publisher import ValuePublisher
from .core.publisher_subscriber.publisher import Publisher

from .core.nexus_system.update_function_values import UpdateFunctionValues
from .core.nexus_system.system_analysis import write_report

from .x_objects_base.x_object_serializable_mixin import XObjectSerializableMixin

__all__ = [
    # Modern clean aliases
    'XValue',
    'XList',
    'XSet',
    'XDict',
    'XDictSelect',

    # Selection objects (set-like)
    'XSetSelect',
    'XSetOptionalSelect',
    'XSetMultiSelect',

    # Selection objects (dict-like)
    'XDictSelect',
    'XDictSelectOptional',
    'XDictSelectDefault',
    'XDictSelectOptionalDefault',

    # Function objects
    'XFunction',
    'XOneWayFunction',
    'XBlockNone',

    # Complex objects
    'XSubscriber',
    'XRootedPaths',

    # Modern protocol aliases
    'XDictProtocol',
    'XListProtocol',
    'XSetProtocol',

    # Hooks (user-facing)
    'FloatingHook',
    'Hook',
    'ReadOnlyHook',
    
    # Function utilities
    'FunctionValues',
    'UpdateFunctionValues',

    # Publisher/Subscriber
    'PublisherProtocol',
    'ValuePublisher',
    'Publisher',

    # Utilities
    'XObjectSerializableMixin',
    'write_report',
]

# Package metadata
try:
    from ._version import __version__, __version_tuple__
except ImportError:
    __version__ = "0.0.1"
    __version_tuple__ = (0, 0, 1)

__author__ = 'Benedikt Axel Brandes'
__year__ = '2025'

# Package description
__description__ = 'Nexus System - A Python library to manage complex objects in an always valid state'
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
