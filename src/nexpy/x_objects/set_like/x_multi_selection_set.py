from typing import Generic, TypeVar, Optional, Literal, Mapping, Callable
from collections.abc import Iterable
from logging import Logger

from ...core.hooks.hook_aliases import Hook, ReadOnlyHook
from ...core.hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ...x_objects_base.x_composite_base import XCompositeBase
from ...core.nexus_system.submission_error import SubmissionError
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from .protocols import XMultiSelectionOptionsProtocol
from .utils import likely_settable

T = TypeVar("T")

class XMultiSelectionSet(XCompositeBase[Literal["selected_options", "available_options"], Literal["number_of_selected_options", "number_of_available_options"], Iterable[T], int, "XMultiSelectionSet"], XMultiSelectionOptionsProtocol[T], Generic[T]):


    def __init__(
        self,
        selected_options: Iterable[T] | Hook[Iterable[T]] | ReadOnlyHook[Iterable[T]] | XMultiSelectionOptionsProtocol[T], available_options: Iterable[T] | Hook[Iterable[T]] | ReadOnlyHook[Iterable[T]] | None = None,
        *,
        custom_validator: Optional[Callable[[Mapping[Literal["selected_options", "available_options", "number_of_selected_options", "number_of_available_options"], Iterable[T] | int]], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER) -> None:

        # Handle initialization from XMultiSelectionOptionsProtocol
        if isinstance(selected_options, XMultiSelectionOptionsProtocol):            
            source_observable = selected_options
            initial_selected_options: Iterable[T] = source_observable.selected_options
            initial_available_options: Iterable[T] = source_observable.available_options
            selected_options_hook: Optional[ManagedHookProtocol[Iterable[T]]] = None
            available_options_hook: Optional[ManagedHookProtocol[Iterable[T]]] = None
            observable: Optional[XMultiSelectionOptionsProtocol[T]] = selected_options
        else:
            observable = None
            # Handle initialization from separate selected_options and available_options
            if available_options is None:
                raise ValueError("available_options must be provided when not initializing from XMultiSelectionOptionsProtocol")
            
            if isinstance(available_options, ManagedHookProtocol):
                initial_available_options = available_options.value
                available_options_hook = available_options
            else:
                initial_available_options = set(available_options)
                available_options_hook = None

            if isinstance(selected_options, ManagedHookProtocol):
                initial_selected_options = selected_options.value
                selected_options_hook = selected_options
            else:
                initial_selected_options = set(selected_options)
                selected_options_hook = None

        def is_valid_value(x: Mapping[Literal["selected_options", "available_options"], Iterable[T]]) -> tuple[bool, str]:
            selected_options = set(x["selected_options"])
            available_options = x["available_options"]
            
            if not likely_settable(available_options):
                return False, f"Available options '{available_options}' cannot be used as a set!"
            
            if not selected_options.issubset(available_options):
                return False, f"Selected options '{selected_options}' not in available options '{available_options}'!"

            return True, "Verification method passed"

        super().__init__(
            initial_hook_values={"selected_options": initial_selected_options, "available_options": initial_available_options},
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={"number_of_selected_options": lambda x: len(x["selected_options"]), "number_of_available_options": lambda x: len(x["available_options"])}, # type: ignore
            validate_complete_primary_values_callback=is_valid_value,
            output_value_wrapper={
                "available_options": lambda x: set(x) # type: ignore
            },
            validate_complete_values_custom_callback=custom_validator,
            logger=logger,
            nexus_manager=nexus_manager
        )

        # Establish linking if hooks were provided
        if observable is not None:
            self._join("selected_options", observable.selected_options_hook, "use_target_value") # type: ignore
            self._join("available_options", observable.available_options_hook, "use_target_value") # type: ignore
        if available_options_hook is not None:
            self._join("available_options", available_options_hook, "use_target_value") # type: ignore
        if selected_options_hook is not None and selected_options_hook is not available_options_hook:
            self._join("selected_options", selected_options_hook, "use_target_value") # type: ignore

    #############################################################
    # XMultiSelectionOptionsProtocol implementation
    #############################################################

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> Hook[Iterable[T]]:
        return self._primary_hooks["available_options"]

    @property
    def available_options(self) -> Iterable[T]: # type: ignore
        """Get the available options as an immutable set."""
        return self._value_wrapped("available_options") # type: ignore
    
    @available_options.setter
    def available_options(self, available_options: Iterable[T]) -> None:
        self.change_available_options(available_options)
    
    def change_available_options(self, available_options: Iterable[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Set the available options (automatically converted to set by nexus system)."""
        success, msg = self._submit_value("available_options", available_options, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, available_options, "available_options")

    #-------------------------------- selected options --------------------------------

    @property
    def selected_options_hook(self) -> Hook[Iterable[T]]:
        return self._primary_hooks["selected_options"]

    @property
    def selected_options(self) -> Iterable[T]: # type: ignore
        return self._value_wrapped("selected_options") # type: ignore
    
    @selected_options.setter
    def selected_options(self, selected_options: Iterable[T]) -> None:
        self.change_selected_options(selected_options)
    
    def change_selected_options(self, selected_options: Iterable[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Set the selected options (automatically converted to set by nexus system)."""
        # Let nexus system handle immutability conversion
        success, msg = self._submit_value("selected_options", set(selected_options), logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, selected_options, "selected_options")

    #-------------------------------- length --------------------------------

    @property
    def number_of_available_options_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the number of available options.
        """
        return self._secondary_hooks["number_of_available_options"] # type: ignore

    @property
    def number_of_available_options(self) -> int:
        """
        Get the current number of available options.
        """
        return self._secondary_hooks["number_of_available_options"].value
    
    @property
    def number_of_selected_options_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the number of selected options.
        """
        return self._secondary_hooks["number_of_selected_options"] # type: ignore

    @property
    def number_of_selected_options(self) -> int:
        """
        Get the current number of selected options.
        """
        return self._value_wrapped("number_of_selected_options") # type: ignore

    #-------------------------------- Convenience methods --------------------------------

    def change_selected_options_and_available_options(self, selected_options: Iterable[T], available_options: Iterable[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """
        Set both the selected options and available options atomically.
        
        Args:
            selected_options: The new selected options (set automatically converted)
            available_options: The new set of available options (set automatically converted)
        """
        # Let nexus system handle immutability conversion
        success, msg = self._submit_values({"selected_options": set(selected_options), "available_options": set(available_options)}, logger=logger)
        if not success and raise_submission_error_flag: 
            raise SubmissionError(msg, {"selected_options": selected_options, "available_options": available_options}, "selected_options and available_options")

    def add_available_option(self, option: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Add an option to the available options set."""
        success, msg = self._submit_value("available_options", set(self._primary_hooks["available_options"].value) | {option})
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "available_options")

    def add_available_options(self, options: Iterable[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Add an option to the available options set."""
        success, msg = self._submit_value("available_options", set(self._primary_hooks["available_options"].value) | set(options))
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, options, "available_options")

    def remove_available_option(self, option: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_value("available_options", set(self._primary_hooks["available_options"].value) - {option})
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "available_options")

    def remove_available_options(self, option: Iterable[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_value("available_options", set(self._primary_hooks["available_options"].value) - set(option))
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "available_options")

    def clear_available_options(self, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove all items from the available options set."""
        success, msg = self._submit_value("available_options", set(), logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, "available_options")

    def add_selected_option(self, option: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Add an option to the selected options set."""
        success, msg = self._submit_value("selected_options", set(self._primary_hooks["selected_options"].value) | {option})
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "selected_options")

    def add_selected_options(self, options: Iterable[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Add an option to the selected options set."""
        success, msg = self._submit_value("selected_options", set(self._primary_hooks["selected_options"].value) | set(options))
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, options, "selected_options")

    def remove_selected_option(self, option: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove an option from the selected options set."""
        success, msg = self._submit_value("selected_options", set(self._primary_hooks["selected_options"].value) - {option})
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "selected_options")

    def remove_selected_options(self, option: Iterable[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove an option from the selected options set."""
        success, msg = self._submit_value("selected_options", set(self._primary_hooks["selected_options"].value) - set(option))
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "selected_options")

    def clear_selected_options(self, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove all items from the selected options set."""
        success, msg = self._submit_value("selected_options", set(), logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, "selected_options")

    def __str__(self) -> str:
        sorted_selected = sorted(self.selected_options) # type: ignore
        sorted_available = sorted(self.available_options) # type: ignore
        return f"XMSO(selected_options={sorted_selected}, available_options={sorted_available})"
    
    def __repr__(self) -> str:
        sorted_selected = sorted(self.selected_options) # type: ignore
        sorted_available = sorted(self.available_options) # type: ignore
        return f"XMSO(selected_options={sorted_selected}, available_options={sorted_available})"