from typing import Generic, TypeVar, Optional, Literal, Mapping, Any, Callable, Self
from collections.abc import Set as AbstractSet
from logging import Logger

from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from nexpy.core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook
from ...core.hooks.protocols.hook_protocol import HookProtocol
from ...foundations.x_composite_base import XCompositeBase
from ...core.nexus_system.submission_error import SubmissionError
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from .protocols import XOptionalSelectionOptionProtocol, XSetProtocol
from ..single_value_like.protocols import XSingleValueProtocol

T = TypeVar("T")

class XOptionalSelectionSet(XCompositeBase[Literal["selected_option", "available_options"], Literal["number_of_available_options"], Optional[T] | AbstractSet[T], int], XOptionalSelectionOptionProtocol[T], Generic[T]):

    def __init__(
        self,
        selected_option: Optional[T] | HookProtocol[Optional[T]] | XSingleValueProtocol[Optional[T]],
        available_options: AbstractSet[T] | HookProtocol[AbstractSet[T]] | XSetProtocol[T],
        *,
        custom_validator: Optional[Callable[[Mapping[Literal["selected_option", "available_options", "number_of_available_options"], Optional[T] | AbstractSet[T]| int]], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER) -> None:

        #########################################################
        # Get initial values and hooks
        #########################################################

        #-------------------------------- selected option --------------------------------

        if isinstance(selected_option, XSingleValueProtocol):
            initial_selected_option: Optional[T] = selected_option.value # type: ignore
            selected_option_hook: Optional[HookProtocol[Optional[T]]] = selected_option.value_hook # type: ignore
        elif isinstance(selected_option, HookProtocol):
            initial_selected_option = selected_option.value # type: ignore
            selected_option_hook = selected_option # type: ignore
        else:
            initial_selected_option = selected_option
            selected_option_hook = None

        #-------------------------------- available options --------------------------------

        if isinstance(available_options, XSetProtocol):
            initial_available_options: AbstractSet[T] = available_options.set # type: ignore
            available_options_hook: Optional[HookProtocol[AbstractSet[T]]] = available_options.set_hook
        elif isinstance(available_options, HookProtocol):
            initial_available_options: AbstractSet[T] = available_options.value
            available_options_hook = available_options
        else:
            raise ValueError("available_options must be a XSetProtocol or HookProtocol")

        #########################################################
        # Prepare and initialize base class
        #########################################################

        #-------------------------------- Validation function --------------------------------

        def is_valid_value(x: Mapping[Literal["selected_option", "available_options"], Any]) -> tuple[bool, str]:
            selected_option = x["selected_option"]
            available_options = x["available_options"]

            if not isinstance(available_options, AbstractSet):
                return False, f"Available options '{available_options}' cannot be used as a set!"

            if not selected_option is None and selected_option not in available_options:
                return False, f"Selected option '{selected_option}' not in available options '{available_options}'!"

            return True, "Verification method passed"

        #-------------------------------- Initialize base class --------------------------------

        super().__init__(
            initial_hook_values={"selected_option": initial_selected_option, "available_options": initial_available_options}, # type: ignore
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={"number_of_available_options": lambda x: len(x["available_options"])}, # type: ignore
            validate_complete_primary_values_callback=is_valid_value,
            output_value_wrapper={
                "available_options": lambda x: set(x) # type: ignore
            },
            custom_validator=custom_validator,
            logger=logger,
            nexus_manager=nexus_manager
        )

        #########################################################
        # Establish joining
        #########################################################

        self._join("selected_option", selected_option_hook, "use_target_value") if selected_option_hook is not None else None # type: ignore
        self._join("available_options", available_options_hook, "use_target_value") if available_options_hook is not None else None # type: ignore

    #########################################################
    # XOptionalSelectionOptionProtocol implementation
    #########################################################

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> OwnedWritableHook[AbstractSet[T], Self]:
        return self._primary_hooks["available_options"] # type: ignore
    
    @property
    def available_options(self) -> set[T]:
        return self._value_wrapped("available_options") # type: ignore

    @available_options.setter
    def available_options(self, available_options: AbstractSet[T]) -> None:
        self.change_available_options(available_options)

    def change_available_options(self, available_options: AbstractSet[T]) -> None:
        success, msg = self._submit_values({"available_options": set(available_options)})
        if not success:
            raise SubmissionError(msg, available_options, "available_options")

    #-------------------------------- selected option --------------------------------
    
    @property
    def selected_option_hook(self) -> OwnedWritableHook[Optional[T], Self]:
        return self._primary_hooks["selected_option"] # type: ignore
    
    @property
    def selected_option(self) -> Optional[T]:
        return self._value_wrapped("selected_option") # type: ignore
    
    @selected_option.setter
    def selected_option(self, selected_option: Optional[T]) -> None:
        self.change_selected_option(selected_option)

    def change_selected_option(self, selected_option: Optional[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        success, msg = self._submit_values({"selected_option": selected_option}, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, selected_option, "selected_option")

    #-------------------------------- change selected option and available options --------------------------------
    
    def change_selected_option_and_available_options(self, selected_option: Optional[T], available_options: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        if selected_option == self._primary_hooks["selected_option"].value and available_options == self._primary_hooks["available_options"].value:
            return
        
        success, msg = self._submit_values({"selected_option": selected_option, "available_options": set(available_options)}, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, {"selected_option": selected_option, "available_options": available_options}, "selected_option and available_options")

    #-------------------------------- length --------------------------------
    
    @property
    def number_of_available_options_hook(self) -> OwnedReadOnlyHook[int, Self]:
        return self._secondary_hooks["number_of_available_options"]

    @property
    def number_of_available_options(self) -> int:
        return self._value_wrapped("number_of_available_options") # type: ignore

    #-------------------------------- convenience methods --------------------------------

    def add_available_option(self, option: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Add an option to the available options set."""
        success, msg = self._submit_values({"available_options": set(self._primary_hooks["available_options"].value) | {option}}) # type: ignore
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "available_options")

    def add_selected_option(self, option: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Add an option to the selected options set."""
        success, msg = self._submit_values({"selected_option": option}, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "selected_option")

    def remove_available_option(self, option: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_values({"available_options": set(self._primary_hooks["available_options"].value) - {option}}, logger=logger) # type: ignore
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "available_options")

    def add_available_options(self, options: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Add an option to the available options set."""
        success, msg = self._submit_values({"available_options": set(self._primary_hooks["available_options"].value) | {option for option in options}}, logger=logger) # type: ignore
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, options, "available_options")

    def remove_available_options(self, options: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_values({"available_options": set(self._primary_hooks["available_options"].value) - {option for option in options}}, logger=logger) # type: ignore
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, options, "available_options")

    def clear_available_options(self, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove all items from the available options set."""
        success, msg = self._submit_values({"available_options": set()}, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, "available_options")

    def clear_selected_option(self, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove all items from the selected options set."""
        success, msg = self._submit_values({"selected_option": None}, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, "selected_option")