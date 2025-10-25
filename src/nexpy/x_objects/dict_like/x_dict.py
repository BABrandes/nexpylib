from typing import Generic, TypeVar, Optional, Literal, Any, Mapping, Sequence
from collections.abc import Set as AbstractSet
from logging import Logger

from ...core.hooks.hook_aliases import Hook, ReadOnlyHook
from ...core.hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ...foundations.x_composite_base import XCompositeBase
from .protocols import XDictProtocol
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER
from ...core.nexus_system.submission_error import SubmissionError

K = TypeVar("K")
V = TypeVar("V")
    
class XDict(XCompositeBase[Literal["dict"], Literal["length", "keys", "values"], Mapping[K, V], int|set[K]|list[V], "XDict"], XDictProtocol[K, V], Generic[K, V]):

    def __init__(
        self,
        observable_or_hook_or_value: Mapping[K, V] | Hook[Mapping[K, V]] | ReadOnlyHook[Mapping[K, V]] | XDictProtocol[K, V] | None = None,
        *,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ) -> None:

        if observable_or_hook_or_value is None:
            initial_dict_value: Mapping[K, V] = {}
            hook: Optional[ManagedHookProtocol[Mapping[K, V]]] = None
        elif isinstance(observable_or_hook_or_value, Mapping):
            initial_dict_value = observable_or_hook_or_value
            hook = None
        elif isinstance(observable_or_hook_or_value, XDictProtocol):
            initial_dict_value = observable_or_hook_or_value.dict
            hook = observable_or_hook_or_value.dict_hook
        elif isinstance(observable_or_hook_or_value, ManagedHookProtocol): # type: ignore
            initial_dict_value = observable_or_hook_or_value.value
            hook = observable_or_hook_or_value
        else:
            raise ValueError("Invalid initial value")

        def is_valid_value(x: Mapping[Literal["dict"], Any]) -> tuple[bool, str]:
            return (True, "Verification method passed") if isinstance(x["dict"], Mapping) else (False, "Value is not a Map")

        super().__init__(
            initial_hook_values={"dict": initial_dict_value},
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={
                "length": lambda x: len(x["dict"]),
                "keys": lambda x: set(x["dict"].keys()),
                "values": lambda x: list(x["dict"].values())
            },
            validate_complete_primary_values_callback=is_valid_value,
            output_value_wrapper={
                "dict": lambda x: dict(x), # type: ignore
                "keys": lambda x: set(x), # type: ignore
                "values": lambda x: list(x) # type: ignore
            },
            logger=logger,
            nexus_manager=nexus_manager
        )

        if hook is not None:
            self._join("dict", hook, "use_target_value") # type: ignore

    #########################################################
    # XDictProtocol implementation
    #########################################################

    #-------------------------------- Dict --------------------------------

    @property
    def dict_hook(self) -> Hook[Mapping[K, V]]:
        """Get the dictionary hook."""
        
        return self._primary_hooks["dict"]
    
    @property
    def dict(self) -> dict[K, V]: # type: ignore
        """Get the current dictionary."""
        return self._value_wrapped("dict") # type: ignore
    
    @dict.setter
    def dict(self, value: Mapping[K, V]) -> None:
        """Set the current dictionary."""
        self.change_dict(value)
    
    def change_dict(self, value: Mapping[K, V], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Change the current dictionary."""
        success, msg = self._submit_value("dict", value, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, value, "dict")

    #-------------------------------- Length --------------------------------

    @property
    def length(self) -> int:
        """Get the current length of the dictionary."""
        return len(self._value_wrapped("dict")) # type: ignore
    
    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """Get the hook for the dictionary length."""
        return self._secondary_hooks["length"] # type: ignore

    #-------------------------------- Keys --------------------------------

    @property
    def keys(self) -> set[K]:
        """Get the current keys of the dictionary."""
        return frozenset(self._value_wrapped("dict").keys()) # type: ignore
    
    @property
    def keys_hook(self) -> ReadOnlyHook[AbstractSet[K]]:
        """Get the hook for the dictionary keys."""
        return self._secondary_hooks["keys"] # type: ignore

    #-------------------------------- Values --------------------------------

    @property
    def values(self) -> list[V]:
        """Get the current values of the dictionary."""
        return list(self._value_wrapped("dict").values()) # type: ignore
    
    @property
    def values_hook(self) -> ReadOnlyHook[Sequence[V]]:
        """Get the hook for the dictionary values."""
        return self._secondary_hooks["values"] # type: ignore

    #########################################################
    # Standard dict interface implementation
    #########################################################
    
    def set_item(self, key: K, value: V) -> None:
        """
        Set a single key-value pair.
        
        Creates a new Mapping with the updated key-value pair.
        
        Args:
            key: The key to set or update
            value: The value to associate with the key
        """
        current = self._primary_hooks["dict"].value
        if key in current and current[key] == value:
            return  # No change
        new_dict = dict(current)
        new_dict[key] = value
        
        success, msg = self._submit_value("dict", new_dict)
        if not success:
            raise ValueError(msg)
    
    def get_item(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        Get a value by key with optional default.
        
        Args:
            key: The key to look up
            default: Default value to return if key is not found
            
        Returns:
            The value associated with the key, or the default value if key not found
        """
        return self._primary_hooks["dict"].value.get(key, default)
    
    def has_key(self, key: K) -> bool:
        """
        Check if a key exists in the dictionary.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._primary_hooks["dict"].value
    
    def remove_item(self, key: K) -> None:
        """
        Remove a key-value pair from the dictionary.
        
        Creates a new Mapping without the specified key.
        
        Args:
            key: The key to remove
        """
        current = self._primary_hooks["dict"].value
        if key not in current:
            return  # No change
        new_dict = {k: v for k, v in current.items() if k != key}
        success, msg = self._submit_value("dict", new_dict)
        if not success:
            raise ValueError(msg)
    
    def clear(self) -> None:
        """
        Clear all items from the dictionary.
        
        Creates a new empty Mapping.
        """
        if not self._primary_hooks["dict"].value:
            return  # No change
        success, msg = self._submit_value("dict", {})
        if not success:
            raise ValueError(msg)
    
    def update(self, other_dict: Mapping[K, V]) -> None:
        """
        Update the dictionary with items from another mapping.
        
        Creates a new Mapping with the updated items.
        
        Args:
            other_dict: Mapping containing items to add or update
        """
        if not other_dict:
            return  # No change
        # Check if any values would actually change
        current = self._primary_hooks["dict"].value
        has_changes = False
        for key, value in other_dict.items():
            if key not in current or current[key] != value:
                has_changes = True
                break
        
        if not has_changes:
            return  # No change
        
        new_dict = dict(current)
        new_dict.update(other_dict)
        success, msg = self._submit_value("dict", new_dict)
        if not success:
            raise ValueError(msg)
    
    def items(self) -> tuple[tuple[K, V], ...]:
        """
        Get all key-value pairs from the dictionary as a tuple of tuples.
        
        Returns:
            A tuple of tuples, each containing a key-value pair
        """
        return tuple(self._primary_hooks["dict"].value.items())
    
    def __len__(self) -> int:
        """
        Get the number of key-value pairs in the dictionary.
        
        Returns:
            The number of key-value pairs
        """
        return len(self._primary_hooks["dict"].value)
    
    def __contains__(self, key: K) -> bool:
        """
        Check if a key exists in the dictionary.
        
        Args:
            key: The key to check for
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._primary_hooks["dict"].value
    
    def __getitem__(self, key: K) -> V:
        """
        Get a value by key.
        
        Args:
            key: The key to look up
            
        Returns:
            The value associated with the key
            
        Raises:
            KeyError: If the key is not found in the dictionary
        """
        current = self._primary_hooks["dict"].value
        if key not in current:
            raise KeyError(f"Key '{key}' not found in dictionary")
        return current[key]
    
    def __setitem__(self, key: K, value: V) -> None:
        """
        Set a key-value pair in the dictionary.
        
        Creates a new Mapping with the updated key-value pair.
        
        Args:
            key: The key to set or update
            value: The value to associate with the key
        """
        current = self._primary_hooks["dict"].value
        new_dict = {**current, key: value}
        success, msg = self._submit_value("dict", new_dict)
        if not success:
            raise ValueError(msg)
    
    def __delitem__(self, key: K) -> None:
        """
        Remove a key-value pair from the dictionary.
        
        Creates a new Mapping without the specified key.
        
        Args:
            key: The key to remove
            
        Raises:
            KeyError: If the key is not found in the dictionary
        """
        current = self._primary_hooks["dict"].value
        if key not in current:
            raise KeyError(f"Key '{key}' not found in dictionary")
        new_dict = {k: v for k, v in current.items() if k != key}
        success, msg = self._submit_value("dict", new_dict)
        if not success:
            raise ValueError(msg)
    
    def __str__(self) -> str:
        return f"OD(dict={dict(self._primary_hooks['dict'].value)})"
    
    def __repr__(self) -> str:
        return f"XDict({dict(self._primary_hooks['dict'].value)})"

    #### ObservableSerializable implementation ####

    def get_values_for_serialization(self) -> Mapping[Literal["dict", "length", "keys", "values"], Any]:
        return {"dict": self._primary_hooks["dict"].value}

    def set_values_from_serialization(self, values: Mapping[Literal["dict", "length", "keys", "values"], Any]) -> None:
        success, msg = self._submit_values({"dict": values["dict"]})
        if not success:
            raise ValueError(msg)
