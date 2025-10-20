"""
Nexus System - Core infrastructure for hook value synchronization

This package contains the core nexus system that enables centralized value storage
and synchronization across hooks in the observable framework.
"""

# Note: We avoid importing other modules here to prevent circular imports.
# Import directly from the submodules when needed, e.g.:
#   from observables._nexus_system.immutable_values import make_immutable
#   from observables._nexus_system.nexus_manager import NexusManager

__all__ = [
    "hook_nexus",
    "nexus_manager",
    "default_nexus_manager",
    "has_nexus_manager",
    "has_nexus_manager_protocol",
    "submission_error",
    "update_function_values",
    "immutable_values",
]

