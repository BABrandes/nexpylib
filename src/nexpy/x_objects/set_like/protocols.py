from typing import Any, TypeVar, Protocol, runtime_checkable, Optional
from collections.abc import Iterable
from ...core.hooks.hook_aliases import Hook, ReadOnlyHook
from ...x_objects_base.carries_some_hooks_protocol import CarriesSomeHooksProtocol

T = TypeVar("T")

@runtime_checkable
class XSetProtocol(CarriesSomeHooksProtocol[Any, Any], Protocol[T]):


    #-------------------------------- set value --------------------------------
    
    @property
    def value_hook(self) -> Hook[Iterable[T]]:
        """
        Get the hook for the set - it can contain any iterable as long as it can be converted to a set.
        """
        ...

    @property
    def value(self) -> set[T]:
        """
        Get the set as a set.
        """
        ...
    
    @value.setter
    def value(self, value: Iterable[T]) -> None:
        self.change_value(value)
        

    
    def change_value(self, value: Iterable[T]) -> None:
        ...

    #-------------------------------- length --------------------------------
    
    @property
    def length_hook(self) -> ReadOnlyHook[int]:
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
class XSelectionOptionsProtocol(Protocol[T]):

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> Hook[Iterable[T]]:
        ...

    @property
    def available_options(self) -> set[T]:
        ...
    
    @available_options.setter
    def available_options(self, available_options: Iterable[T]) -> None:
        self.change_available_options(available_options)

    
    def change_available_options(self, available_options: Iterable[T]) -> None:
        ... 

    #-------------------------------- selected options --------------------------------

    @property
    def selected_option_hook(self) -> Hook[T]:
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
    def number_of_available_options_hook(self) -> ReadOnlyHook[int]:
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

    def change_selected_option_and_available_options(self, selected_option: T, available_options: Iterable[T]) -> None:
        ...

@runtime_checkable
class XOptionalSelectionOptionProtocol(Protocol[T]):

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> Hook[Iterable[T]]:
        ...

    @property
    def available_options(self) -> set[T]:
        ...
    
    @available_options.setter
    def available_options(self, available_options: Iterable[T]) -> None:
        self.change_available_options(available_options)

    def change_available_options(self, available_options: Iterable[T]) -> None:
        ...

    #-------------------------------- selected options --------------------------------

    @property
    def selected_option_hook(self) -> Hook[Optional[T]]:
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
    def number_of_available_options_hook(self) -> ReadOnlyHook[int]:
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

    def change_selected_option_and_available_options(self, selected_option: Optional[T], available_options: Iterable[T]) -> None:
        ...

@runtime_checkable
class XMultiSelectionOptionsProtocol(Protocol[T]):

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> Hook[Iterable[T]]:
        ...

    @property
    def available_options(self) -> set[T]:
        ...
    
    @available_options.setter
    def available_options(self, available_options: Iterable[T]) -> None:
        self.change_available_options(available_options)

    def change_available_options(self, available_options: Iterable[T]) -> None:
        ...

    #-------------------------------- selected options --------------------------------

    @property
    def selected_options_hook(self) -> Hook[Iterable[T]]:
        ...

    @property
    def selected_options(self) -> set[T]:
        ...
    
    @selected_options.setter
    def selected_options(self, selected_options: Iterable[T]) -> None:
        self.change_selected_options(selected_options)

    def change_selected_options(self, selected_options: Iterable[T]) -> None:
        ...

    #-------------------------------- length --------------------------------

    @property
    def number_of_available_options_hook(self) -> ReadOnlyHook[int]:
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
    def number_of_selected_options_hook(self) -> ReadOnlyHook[int]:
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

    def change_selected_options_and_available_options(self, selected_options: Iterable[T], available_options: Iterable[T]) -> None:
        ...

    def clear_selected_options(self) -> None:
        ...
