from typing import Any, TypeVar, Protocol, runtime_checkable, Optional, Self
from collections.abc import Set as AbstractSet
from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from nexpy.core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook
from nexpy.core.hooks.protocols.hook_protocol import HookProtocol
from ...foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol

T = TypeVar("T")

@runtime_checkable
class XSetProtocol(CarriesSomeHooksProtocol[Any, Any], Protocol[T]):


    #-------------------------------- set value --------------------------------
    
    @property
    def set_hook(self) -> HookProtocol[AbstractSet[T]]:
        """
        Get the hook for the set - it can contain any iterable as long as it can be converted to a set.
        """
        ...

    @property
    def set(self) -> set[T]:
        """
        Get the current set value.
        """
        ...
    
    @set.setter
    def set(self, value: AbstractSet[T]) -> None:
        """
        Set the set value.
        """
        self.change_set(value)
    
    def change_set(self, value: AbstractSet[T]) -> None:
        """
        Change the set value.
        """
        ...

    #-------------------------------- length --------------------------------
    
    @property
    def length_hook(self) -> HookProtocol[int]:
        """
        Get the hook for the set length.
        """
        ...

    @property
    def length(self) -> int:
        """
        Get the current length of the set.
        """
        ...

@runtime_checkable
class XSelectionOptionsProtocol(CarriesSomeHooksProtocol[Any, Any], Protocol[T]):

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> OwnedWritableHook[AbstractSet[T], Self]:
        ...

    @property
    def available_options(self) -> set[T]:
        ...
    
    @available_options.setter
    def available_options(self, available_options: AbstractSet[T]) -> None:
        self.change_available_options(available_options)

    
    def change_available_options(self, available_options: AbstractSet[T]) -> None:
        ... 

    #-------------------------------- selected options --------------------------------

    @property
    def selected_option_hook(self) -> OwnedWritableHook[T, Self]:
        ...

    @property
    def selected_option(self) -> T:
        ...
    
    @selected_option.setter
    def selected_option(self, selected_option: T) -> None:
        self.change_selected_option(selected_option)

    def change_selected_option(self, selected_option: T) -> None:
        ...

    #-------------------------------- length --------------------------------
    
    @property
    def number_of_available_options_hook(self) -> OwnedReadOnlyHook[int, Self]:
        """
        Get the hook for the set length.
        """
        ...

    @property
    def number_of_available_options(self) -> int:
        """
        Get the current length of the set.
        """
        ...

    #-------------------------------- convenience methods --------------------------------

    def change_selected_option_and_available_options(self, selected_option: T, available_options: AbstractSet[T]) -> None:
        ...

@runtime_checkable
class XOptionalSelectionOptionProtocol(CarriesSomeHooksProtocol[Any, Any], Protocol[T]):

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> OwnedWritableHook[AbstractSet[T], Self]:
        ...

    @property
    def available_options(self) -> set[T]:
        ...
    
    @available_options.setter
    def available_options(self, available_options: AbstractSet[T]) -> None:
        self.change_available_options(available_options)

    def change_available_options(self, available_options: AbstractSet[T]) -> None:
        ...

    #-------------------------------- selected options --------------------------------

    @property
    def selected_option_hook(self) -> OwnedWritableHook[Optional[T], Self]:
        ...

    @property
    def selected_option(self) -> Optional[T]:
        ...
    
    @selected_option.setter
    def selected_option(self, selected_option: Optional[T]) -> None:
        self.change_selected_option(selected_option)

    def change_selected_option(self, selected_option: Optional[T]) -> None:
        ...

    #-------------------------------- length --------------------------------
    
    @property
    def number_of_available_options_hook(self) -> OwnedReadOnlyHook[int, Self]:
        """
        Get the hook for the set length.
        """
        ...

    @property
    def number_of_available_options(self) -> int:
        """
        Get the current length of the set.
        """
        ...

    #-------------------------------- convenience methods --------------------------------

    def change_selected_option_and_available_options(self, selected_option: Optional[T], available_options: AbstractSet[T]) -> None:
        ...

@runtime_checkable
class XMultiSelectionOptionsProtocol(CarriesSomeHooksProtocol[Any, Any], Protocol[T]):

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> OwnedWritableHook[AbstractSet[T], Self]:
        ...

    @property
    def available_options(self) -> set[T]:
        ...
    
    @available_options.setter
    def available_options(self, available_options: AbstractSet[T]) -> None:
        self.change_available_options(available_options)

    def change_available_options(self, available_options: AbstractSet[T]) -> None:
        ...

    #-------------------------------- selected options --------------------------------

    @property
    def selected_options_hook(self) -> OwnedWritableHook[AbstractSet[T], Self]:
        ...

    @property
    def selected_options(self) -> set[T]:
        ...
    
    @selected_options.setter
    def selected_options(self, selected_options: AbstractSet[T]) -> None:
        self.change_selected_options(selected_options)

    def change_selected_options(self, selected_options: AbstractSet[T]) -> None:
        ...

    #-------------------------------- length --------------------------------

    @property
    def number_of_available_options_hook(self) -> OwnedReadOnlyHook[int, Self]:
        """
        Get the hook for the number of available options.
        """
        ...

    @property
    def number_of_available_options(self) -> int:
        """
        Get the current number of available options.
        """
        ...
    
    @property
    def number_of_selected_options_hook(self) -> OwnedReadOnlyHook[int, Self]:
        """
        Get the hook for the number of selected options.
        """
        ...

    @property
    def number_of_selected_options(self) -> int:
        """
        Get the current number of selected options.
        """
        ...

    #-------------------------------- Convenience methods --------------------------------

    def change_selected_options_and_available_options(self, selected_options: AbstractSet[T], available_options: AbstractSet[T]) -> None:
        ...

    def clear_selected_options(self) -> None:
        ...
