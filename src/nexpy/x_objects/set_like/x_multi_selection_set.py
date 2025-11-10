from typing import Generic, TypeVar, Optional, Literal, Mapping, Callable, Self
from collections.abc import Set as AbstractSet
from logging import Logger

from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from nexpy.core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook

from ...core.hooks.protocols.hook_protocol import HookProtocol
from ...foundations.x_composite_base import XCompositeBase
from ...core.nexus_system.submission_error import SubmissionError
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from .protocols import XMultiSelectionOptionsProtocol, XSetProtocol

T = TypeVar("T")

class XMultiSelectionSet(XCompositeBase[Literal["selected_options", "available_options"], Literal["number_of_selected_options", "number_of_available_options"], AbstractSet[T], int], XMultiSelectionOptionsProtocol[T], Generic[T]):
    """
    Reactive multiple-selection container with validation against available options.
    
    XSetMultiSelect[T] (alias: XMultiSelectionSet[T]) maintains a set of selected options
    that must be a subset of available options. The generic type T specifies the option type.

    Type Parameters
    ---------------
    T : TypeVar
        The type of selectable options. Must be hashable.
        Examples: XSetMultiSelect[str], XSetMultiSelect[int]

    Key Features
    ------------
    - **Multiple Selection**: Select zero or more options simultaneously
    - **Validation**: selected_options ⊆ available_options
    - **Reactive**: Changes trigger notifications
    - **Type-Safe**: Full generic type support

    See Also
    --------
    XSetSingleSelect : Required single selection
    XSetSingleSelectOptional : Optional single selection
    """

    def __init__(
        self,
        selected_options: AbstractSet[T] | HookProtocol[AbstractSet[T]] | XSetProtocol[T],
        available_options: AbstractSet[T] | HookProtocol[AbstractSet[T]] | XSetProtocol[T],
        *,
        custom_validator: Optional[Callable[[Mapping[Literal["selected_options", "available_options", "number_of_selected_options", "number_of_available_options"], AbstractSet[T] | int]], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER) -> None:
        """
        Initialize multiple-selection container.

        The generic type T specifies the option type (must be hashable).
        Use: XSetMultiSelect[str], XSetMultiSelect[MyEnum], etc.

        Parameters
        ----------
        selected_options : AbstractSet[T] | Hook[AbstractSet[T]] | XSet[T]
            Initial selected options (must be subset of available_options).

        available_options : AbstractSet[T] | Hook[AbstractSet[T]] | XSet[T]
            Set of available options to select from.

        custom_validator : Callable, optional
            Additional validation function.

        logger : Logger, optional
            Logger for debugging.

        nexus_manager : NexusManager, optional
            Coordination manager.

        Examples
        --------
        Multiple selection:

        >>> colors = {"red", "green", "blue", "yellow"}
        >>> sel = XSetMultiSelect[str](
        ...     selected_options={"red", "blue"},
        ...     available_options=colors
        ... )
        >>> sel.selected_options
        {'red', 'blue'}
        >>> sel.add_selected("green")
        >>> sel.selected_options
        {'red', 'blue', 'green'}
        """

        #########################################################
        # Get initial values and hooks
        #########################################################

        #-------------------------------- selected options --------------------------------

        if isinstance(selected_options, XSetProtocol):
            initial_selected_options = set[T](selected_options.set)
            selected_options_hook: Optional[HookProtocol[AbstractSet[T]]] = selected_options.set_hook
        elif isinstance(selected_options, HookProtocol):
            initial_selected_options = set[T](selected_options.value)
            selected_options_hook = selected_options
        elif isinstance(selected_options, AbstractSet):
            # Plain set provided
            initial_selected_options = selected_options
            selected_options_hook = None
        else:
            raise ValueError("selected_options must be a XSetProtocol, HookProtocol, or AbstractSet")

        #-------------------------------- available options --------------------------------

        if isinstance(available_options, XSetProtocol):
            initial_available_options = set[T](available_options.set)
            available_options_hook: Optional[HookProtocol[AbstractSet[T]]] = available_options.set_hook
        elif isinstance(available_options, HookProtocol):
            initial_available_options = set[T](available_options.value)
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

        def is_valid_value(x: Mapping[Literal["selected_options", "available_options"], AbstractSet[T]]) -> tuple[bool, str]:
            selected_options = set[T](x["selected_options"])
            available_options = x["available_options"]
            
            if not isinstance(available_options, AbstractSet): # type: ignore
                return False, f"Available options '{available_options}' cannot be used as a set!"
            
            if not selected_options.issubset(available_options):
                return False, f"Selected options '{selected_options}' not in available options '{available_options}'!"

            return True, "Verification method passed"

        #-------------------------------- Initialize base class --------------------------------

        super().__init__(
            initial_hook_values={"selected_options": initial_selected_options, "available_options": initial_available_options},
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={"number_of_selected_options": lambda x: len(x["selected_options"]), "number_of_available_options": lambda x: len(x["available_options"])},
            validate_complete_primary_values_callback=is_valid_value,
            output_value_wrapper={
                "available_options": lambda x: set[T](x) # type: ignore
            },
            custom_validator=custom_validator,
            logger=logger,
            nexus_manager=nexus_manager
        )

        #########################################################
        # Establish linking
        #########################################################

        self._join("selected_options", selected_options_hook, "use_target_value") if selected_options_hook is not None else None # type: ignore
        self._join("available_options", available_options_hook, "use_target_value") if available_options_hook is not None else None # type: ignore

    #############################################################
    # XMultiSelectionOptionsProtocol implementation
    #############################################################

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> OwnedWritableHook[AbstractSet[T], Self]:
        return self._primary_hooks["available_options"]

    @property
    def available_options(self) -> AbstractSet[T]: # type: ignore
        """Get the available options as an immutable set."""
        return self._value_wrapped("available_options") # type: ignore
    
    @available_options.setter
    def available_options(self, available_options: AbstractSet[T]) -> None:
        self.change_available_options(available_options)
    
    def change_available_options(self, available_options: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Set the available options (automatically converted to set by nexus system)."""
        success, msg = self._submit_value("available_options", available_options, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, available_options, "available_options")

    #-------------------------------- selected options --------------------------------

    @property
    def selected_options_hook(self) -> OwnedWritableHook[AbstractSet[T], Self]:
        return self._primary_hooks["selected_options"]

    @property
    def selected_options(self) -> AbstractSet[T]: # type: ignore
        return self._value_wrapped("selected_options") # type: ignore
    
    @selected_options.setter
    def selected_options(self, selected_options: AbstractSet[T]) -> None:
        self.change_selected_options(selected_options)
    
    def change_selected_options(self, selected_options: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Set the selected options (automatically converted to set by nexus system)."""
        # Let nexus system handle immutability conversion
        success, msg = self._submit_value("selected_options", set(selected_options), logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, selected_options, "selected_options")

    #-------------------------------- length --------------------------------

    @property
    def number_of_available_options_hook(self) -> OwnedReadOnlyHook[int, Self]:
        """
        Get the hook for the number of available options.
        """
        return self._secondary_hooks["number_of_available_options"]

    @property
    def number_of_available_options(self) -> int:
        """
        Get the current number of available options.
        """
        return self._secondary_hooks["number_of_available_options"].value
    
    @property
    def number_of_selected_options_hook(self) -> OwnedReadOnlyHook[int, Self]:
        """
        Get the hook for the number of selected options.
        """
        return self._secondary_hooks["number_of_selected_options"]

    @property
    def number_of_selected_options(self) -> int:
        """
        Get the current number of selected options.
        """
        return self._value_wrapped("number_of_selected_options") # type: ignore

    #-------------------------------- Convenience methods --------------------------------

    def change_selected_options_and_available_options(self, selected_options: AbstractSet[T], available_options: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
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
        success, msg = self._submit_value("available_options", set[T](self._primary_hooks["available_options"]._get_value()) | {option}) # type: ignore
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "available_options")

    def add_available_options(self, options: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Add an option to the available options set."""
        success, msg = self._submit_value("available_options", set[T](self._primary_hooks["available_options"]._get_value()) | set[T](options)) # type: ignore
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, options, "available_options")

    def remove_available_option(self, option: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_value("available_options", set[T](self._primary_hooks["available_options"]._get_value()) - {option}) # type: ignore
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "available_options")

    def remove_available_options(self, option: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_value("available_options", set[T](self._primary_hooks["available_options"]._get_value()) - set[T](option)) # type: ignore
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "available_options")

    def clear_available_options(self, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove all items from the available options set."""
        success, msg = self._submit_value("available_options", set(), logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, "available_options")

    def add_selected_option(self, option: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Add an option to the selected options set."""
        success, msg = self._submit_value("selected_options", set[T](self._primary_hooks["selected_options"]._get_value()) | {option}) # type: ignore
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "selected_options")

    def add_selected_options(self, options: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Add an option to the selected options set."""
        success, msg = self._submit_value("selected_options", set[T](self._primary_hooks["selected_options"]._get_value()) | set[T](options)) # type: ignore
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, options, "selected_options")

    def remove_selected_option(self, option: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove an option from the selected options set."""
        success, msg = self._submit_value("selected_options", set[T](self._primary_hooks["selected_options"]._get_value()) - {option}) # type: ignore
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, option, "selected_options")

    def remove_selected_options(self, option: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """Remove an option from the selected options set."""
        success, msg = self._submit_value("selected_options", set[T](self._primary_hooks["selected_options"]._get_value()) - set[T](option)) # type: ignore
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