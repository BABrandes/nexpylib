

from typing import Generic, Optional, TypeVar, Any, Literal, Mapping, Callable, Self
from collections.abc import Set as AbstractSet
from logging import Logger

from nexpy.core.hooks.protocols.hook_protocol import HookProtocol
from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from nexpy.core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook
from ...foundations.x_composite_base import XCompositeBase
from ...core.nexus_system.submission_error import SubmissionError
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from .protocols import XSelectionOptionsProtocol
from ..set_like.protocols import XSetProtocol
from ..single_value_like.protocols import XSingleValueProtocol

T = TypeVar("T")

class XSelectionSet(XCompositeBase[Literal["selected_option", "available_options"], Literal["number_of_available_options"], T | AbstractSet[T], int], XSelectionOptionsProtocol[T], Generic[T]):

    def __init__(
        self,
        selected_option: T | HookProtocol[T] | XSingleValueProtocol[T],
        available_options: AbstractSet[T] | HookProtocol[AbstractSet[T]] | XSetProtocol[T] | None = None,
        *,
        custom_validator: Optional[Callable[[Mapping[Literal["selected_option", "available_options", "number_of_available_options"], T | AbstractSet[T] | int]], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER) -> None:

        #########################################################
        # Get initial values and hooks
        #########################################################

        #-------------------------------- selected option --------------------------------

        if isinstance(selected_option, XSingleValueProtocol):
            initial_selected_option: T = selected_option.value # type: ignore
            selected_option_hook: Optional[HookProtocol[T]] = selected_option.value_hook # type: ignore

        elif isinstance(selected_option, HookProtocol):
            initial_selected_option = selected_option.value # type: ignore
            selected_option_hook = selected_option # type: ignore
        else:
            initial_selected_option = selected_option
            selected_option_hook = None

        #-------------------------------- available options --------------------------------

        if available_options is None:
            raise ValueError("available_options is required")
        elif isinstance(available_options, XSetProtocol):
            initial_available_options: AbstractSet[T] = available_options.set # type: ignore
            available_options_hook: Optional[HookProtocol[AbstractSet[T]]] = available_options.set_hook
        elif isinstance(available_options, HookProtocol):
            initial_available_options: AbstractSet[T] = available_options.value
            available_options_hook = available_options
        elif isinstance(available_options, AbstractSet):
            # Plain set provided
            initial_available_options = available_options
            available_options_hook = None
        else:
            raise ValueError("available_options must be a XSetProtocol, HookProtocol, or AbstractSet")

        #########################################################
        # Prepare and initialize base class
        #########################################################

        #-------------------------------- Validation function --------------------------------

        def is_valid_value(x: Mapping[Literal["selected_option", "available_options"], Any]) -> tuple[bool, str]:
            selected_option = x["selected_option"]
            available_options = x["available_options"]

            if not isinstance(available_options, AbstractSet):
                return False, f"Available options '{available_options}' cannot be used as a set!"

            if selected_option not in available_options:
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
    # XSelectionOptionsProtocol implementation
    #########################################################

    #-------------------------------- available options --------------------------------
    
    @property
    def available_options_hook(self) -> OwnedWritableHook[AbstractSet[T], Self]:
        return self._primary_hooks["available_options"] # type: ignore

    @property
    def available_options(self) -> set[T]:
        return self._primary_hooks["available_options"].value # type: ignore

    @available_options.setter
    def available_options(self, available_options: AbstractSet[T]) -> None:
        self.change_available_options(available_options)

    def change_available_options(self, available_options: AbstractSet[T]) -> None:        
        success, msg = self._submit_value("available_options", set(available_options))
        if not success:
            raise SubmissionError(msg, available_options, "available_options")

    #-------------------------------- selected option --------------------------------

    @property
    def selected_option_hook(self) -> OwnedWritableHook[T, Self]:
        return self._primary_hooks["selected_option"] # type: ignore

    @property
    def selected_option(self) -> T:
        return self._primary_hooks["selected_option"].value # type: ignore
    
    @selected_option.setter
    def selected_option(self, selected_option: T) -> None:
        self.change_selected_option(selected_option)

    def change_selected_option(self, selected_option: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        if selected_option == self._primary_hooks["selected_option"].value:
            return
        
        success, msg = self._submit_value("selected_option", selected_option, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, selected_option, "selected_option")
    
    def change_selected_option_and_available_options(self, selected_option: T, available_options: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        if selected_option == self._primary_hooks["selected_option"].value and available_options == self._primary_hooks["available_options"].value:
            return
        
        success, msg = self._submit_values({"selected_option": selected_option, "available_options": set(available_options)}, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, {"selected_option": selected_option, "available_options": available_options}, "selected_option and available_options")

    #-------------------------------- number of available options --------------------------------

    @property
    def number_of_available_options_hook(self) -> OwnedReadOnlyHook[int, Self]:
        return self._secondary_hooks["number_of_available_options"]

    @property
    def number_of_available_options(self) -> int:
        return len(self._primary_hooks["available_options"].value) # type: ignore

    #-------------------------------- convenience methods --------------------------------

    def add_available_option(self, option: T) -> None:
        """Add an option to the available options set."""
        success, msg = self._submit_values({"available_options": self._primary_hooks["available_options"].value | set([option])}) # type: ignore
        if not success:
            raise SubmissionError(msg, option, "available_options")

    def add_available_options(self, options: AbstractSet[T]) -> None:
        """Add an option to the available options set."""
        success, msg = self._submit_values({"available_options": self._primary_hooks["available_options"].value | set(options)}) # type: ignore
        if not success:
            raise SubmissionError(msg, options, "available_options")

    def remove_available_option(self, option: T) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_values({"available_options": self._primary_hooks["available_options"].value - set([option])}) # type: ignore
        if not success:
            raise SubmissionError(msg, option, "available_options")

    def remove_available_options(self, options: AbstractSet[T]) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_values({"available_options": self._primary_hooks["available_options"].value - set(options)}) # type: ignore
        if not success:
            raise SubmissionError(msg, options, "available_options")

    def __str__(self) -> str:
        sorted_options = sorted(self.available_options) # type: ignore
        return f"XSS(selected_option={self.selected_option}, available_options={sorted_options})"
    
    def __repr__(self) -> str:
        sorted_options = sorted(self.available_options) # type: ignore
        return f"XSS(selected_option={self.selected_option}, available_options={sorted_options})"