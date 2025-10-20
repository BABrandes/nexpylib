from typing import Iterable, TypeVar, Optional, Protocol, Mapping, runtime_checkable, final

from ...core.hooks.hook_aliases import Hook, ReadOnlyHook

K = TypeVar("K")
V = TypeVar("V")

@runtime_checkable
class XDictProtocol(Protocol[K, V]):


    #-------------------------------- Dict --------------------------------
    
    @property
    def dict_hook(self) -> Hook[Mapping[K, V]]:
        """
        Get the hook for the dictionary.
        """
        ...

    @property
    def dict(self) -> dict[K, V]:
        """
        Get the immutable dictionary value.
        """
        ...
    
    @final
    @dict.setter
    def dict(self, value: Mapping[K, V]) -> None:
        self.change_dict(value)

    def change_dict(self, new_dict: Mapping[K, V]) -> None:
        """
        Change the dictionary value (lambda-friendly method).
        """
        ...
    
    #-------------------------------- Length --------------------------------
    
    @property
    def length(self) -> int:
        """
        Get the current length of the dictionary.
        """
        ...
    
    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the dictionary length.
        """
        ...

    #-------------------------------- Keys --------------------------------

    @property
    def keys(self) -> set[K]:
        """
        Get all keys from the dictionary as a set.
        """
        ...
    
    @property
    def keys_hook(self) -> ReadOnlyHook[Iterable[K]]:
        """
        Get the hook for the dictionary keys.
        """
        ...

    #-------------------------------- Values --------------------------------

    @property
    def values(self) -> list[V]:
        """
        Get all values from the dictionary as a list.
        """
        ...
    
    @property
    def values_hook(self) -> ReadOnlyHook[Iterable[V]]:
        """
        Get the hook for the dictionary values.
        """
        ...

    #------------------------------------------------------------------------

@runtime_checkable
class XSelectionDictProtocol(XDictProtocol[K, V], Protocol[K, V]):

    
    #-------------------------------- Key --------------------------------

    @property
    def key_hook(self) -> "Hook[K]":
        """Get the key hook."""
        ...

    @property
    def key(self) -> K:
        """Get the current key."""
        ...

    @key.setter
    def key(self, value: K) -> None:
        """Set the current key."""
        ...

    def change_key(self, new_value: K) -> None:
        """Change the current key."""
        ...

    #-------------------------------- Value --------------------------------

    @property
    def value_hook(self) -> "Hook[V]":
        """Get the value hook."""
        ...
    
    @property
    def value(self) -> V:
        """Get the current value."""
        ...
    
    @value.setter
    def value(self, value: V) -> None:
        """Set the current value."""
        ...

    def change_value(self, new_value: V) -> None:
        """Change the current value."""
        ...

    #-------------------------------- Convenience methods -------------------
    
    def change_dict_and_key(self, new_dict_value: Mapping[K, V], new_key_value: K) -> None:
        """Change the dictionary and key behind this hook."""
        ...

    #------------------------------------------------------------------------

@runtime_checkable
class XOptionalSelectionDictProtocol(XDictProtocol[K, V], Protocol[K, V]):


    #-------------------------------- Key --------------------------------

    @property
    def key_hook(self) -> "Hook[Optional[K]]":
        """Get the key hook."""
        ...
    

    @property
    def key(self) -> Optional[K]:
        """Get the current key."""
        ...
    
    @key.setter
    def key(self, value: Optional[K]) -> None:
        """Set the current key."""
        ...

    def change_key(self, new_value: Optional[K]) -> None:
        """Change the current key."""
        ...

    #-------------------------------- Value --------------------------------

    @property
    def value_hook(self) -> "Hook[Optional[V]]":
        """Get the value hook."""
        ...
    
    @property
    def value(self) -> Optional[V]:
        """Get the current value."""
        ...
    
    @value.setter
    def value(self, value: Optional[V]) -> None:
        """Set the current value."""
        ...
    
    def change_value(self, new_value: Optional[V]) -> None:
        """Change the current value."""
        ...

    #-------------------------------- Convenience methods -------------------
    
    def change_dict_and_key(self, new_dict_value: Mapping[K, V], new_key_value: Optional[K]) -> None:
        """Change the dictionary and key behind this hook."""
        ...

    #------------------------------------------------------------------------

@runtime_checkable
class XSelectionDictWithDefaultProtocol(XDictProtocol[K, V], Protocol[K, V]):


    #-------------------------------- Key --------------------------------

    @property
    def key_hook(self) -> "Hook[K]":
        """Get the key hook."""
        ...
    
    @property
    def key(self) -> K:
        """Get the current key."""
        ...

    @key.setter
    def key(self, value: K) -> None:
        """Set the current key."""
        ...
    
    def change_key(self, new_value: K) -> None:
        """Change the current key."""
        ...

    #-------------------------------- Value --------------------------------

    @property
    def value_hook(self) -> "Hook[V]":
        """Get the value hook."""
        ...
    
    @property
    def value(self) -> V:
        """Get the current value."""
        ...
    
    @value.setter
    def value(self, value: V) -> None:
        """Set the current value."""
        ...
    
    def change_value(self, new_value: V) -> None:
        """Change the current value."""
        ...

    #-------------------------------- Convenience methods -------------------
    
    def change_dict_and_key(self, new_dict_value: Mapping[K, V], new_key_value: K) -> None:
        """Change the dictionary and key behind this hook."""
        ...
    
    #------------------------------------------------------------------------

@runtime_checkable
class XOptionalSelectionDictWithDefaultProtocol(XDictProtocol[K, V], Protocol[K, V]):

    
    #-------------------------------- Key --------------------------------

    @property
    def key_hook(self) -> "Hook[Optional[K]]":
        """Get the key hook."""
        ...
    
    @property
    def key(self) -> Optional[K]:
        """Get the current key."""
        ...

    @key.setter
    def key(self, value: Optional[K]) -> None:
        """Set the current key."""
        ...
    
    def change_key(self, new_value: Optional[K]) -> None:
        """Change the current key."""
        ...
    
    #-------------------------------- Value --------------------------------
    
    @property
    def value_hook(self) -> "Hook[Optional[V]]":
        """Get the value hook."""
        ...
    
    @property
    def value(self) -> Optional[V]:
        """Get the current value."""
        ...

    @value.setter
    def value(self, value: Optional[V]) -> None:
        """Set the current value."""
        ...
    
    def change_value(self, new_value: Optional[V]) -> None:
        """Change the current value."""
        ...

    #-------------------------------- Convenience methods -------------------

    def change_dict_and_key(self, new_dict_value: Mapping[K, V], new_key_value: Optional[K]) -> None:
        """Change the dictionary and key behind this hook."""
        ...
    
    #------------------------------------------------------------------------