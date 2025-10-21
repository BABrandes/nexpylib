from typing import Callable, Generic, Literal, Mapping, Optional, TypeVar
from logging import Logger
from threading import RLock

from ..core.auxiliary.listening_base import ListeningBase
from ..core.hooks.hook_protocols.owned_hook_protocol import OwnedHookProtocol
from ..core.hooks.owned_hook import OwnedHook
from ..core.hooks.hook_aliases import Hook, ReadOnlyHook
from ..core.nexus_system.nexus import Nexus
from ..core.nexus_system.nexus_manager import NexusManager
from ..core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from ..core.nexus_system.submission_error import SubmissionError

from .carries_single_hook_protocol import CarriesSingleHookProtocol
from .x_object_serializable_mixin import XObjectSerializableMixin
from .carries_some_hooks_base import CarriesSomeHooksBase

T = TypeVar("T")

class XSimpleBase(ListeningBase, CarriesSomeHooksBase[Literal["value"], T, "XSimpleBase[T]"], CarriesSingleHookProtocol[T], XObjectSerializableMixin[Literal["value"], T], Generic[T]):
    """
    Base class for simple X objects (single value) with transitive synchronization via Nexus fusion.
    
    This class provides the core implementation for X objects that wrap a single value,
    including hook management, validation, and synchronization. It serves as the foundation
    for XValue and similar single-value X object types.
    
    The class handles:
    - Hook creation and management
    - Value validation
    - Bidirectional synchronization through join()
    - Listener notifications
    - Thread-safe operations
    
    Type Parameters:
        T: The type of value being stored
    """

    def __init__(
            self,
            *,
            value_or_hook: T|Hook[T]|ReadOnlyHook[T]|CarriesSingleHookProtocol[T],
            validation_in_isolation_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
            invalidate_callback: Optional[Callable[[], None]] = None,
            logger: Optional[Logger] = None,
            nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER):
        """
        Initialize the XSimpleBase.
        
        Args:
            value_or_hook: Initial value or Hook to join to
            verification_method: Optional validation function
            invalidate_callback: Optional callback for post-change actions
            logger: Optional logger for debugging
            nexus_manager: NexusManager for coordinating updates
        """

        #-------------------------------- Initialization start --------------------------------

        # Initialize lock first
        self._lock = RLock()
        
        # Store configuration
        self._verification_method = validation_in_isolation_callback
        self._invalidate_callback = invalidate_callback
        self._logger = logger
        self._nexus_manager = nexus_manager

        if isinstance(value_or_hook, CarriesSingleHookProtocol):
            value: T = value_or_hook._get_single_value() # type: ignore
            hook: Optional[OwnedHookProtocol[T]] = value_or_hook._get_single_hook() # type: ignore    
        elif isinstance(value_or_hook, Hook):
            value: T = value_or_hook.value # type: ignore
            hook = value_or_hook # type: ignore
        else:
            # Is T
            value = value_or_hook # type: ignore
            hook = None

        # Initialize the BaseListening
        ListeningBase.__init__(self, logger)

        # Create the value hook
        self._value_hook = OwnedHook[T](
            self,
            value, # type: ignore
            logger,
            nexus_manager
            )

        # Create validation callback that uses the verification method
        def validate_complete_values_in_isolation_callback(
            self_ref: "XSimpleBase[T]", 
            values: Mapping[Literal["value"], T]
        ) -> tuple[bool, str]:
            """Validate the complete values using the verification method."""
            if "value" not in values:
                return False, "Value key not found in values"
            
            value = values["value"]
            
            # Use custom verification method if provided
            if self_ref._verification_method is not None:
                try:
                    success, msg = self_ref._verification_method(value)
                    if not success:
                        return False, msg
                except Exception as e:
                    return False, f"Validation error: {e}"
            
            return True, "Value is valid"

        CarriesSomeHooksBase.__init__( # type: ignore
            self,
            validate_complete_values_in_isolation_callback=validate_complete_values_in_isolation_callback,
            logger=logger,
            nexus_manager=nexus_manager
        )

        # If initialized with a Hook, join to it
        if hook is not None:
            self._value_hook.join(hook, "use_target_value")

        #-------------------------------- Initialize finished --------------------------------

    #########################################################
    # CarriesSingleHookProtocol implementation
    #########################################################

    def _get_single_hook(self) -> OwnedHook[T]:
        """
        Get the hook for the single value.
        
        ** This method is not thread-safe and should only be called within a lock.
        
        Returns:
            The hook for the single value
        """
        return self._value_hook

    def _get_single_value(self) -> T:
        """
        Get the value of the single hook.
        
        ** This method is not thread-safe and should only be called within a lock.
        
        Returns:
            The value of the single hook
        """
        return self._value_hook.value

    def _get_nexus(self) -> Nexus[T]:
        """
        Get the nexus for the single value.
        
        ** This method is not thread-safe and should only be called within a lock.
        
        Returns:
            The nexus for the single value
        """
        return self._value_hook._get_nexus() # type: ignore

    #########################################################
    # Public API
    #########################################################

    def join(self, target_hook: Hook[T] | ReadOnlyHook[T] | CarriesSingleHookProtocol[T], sync_mode: Literal["use_caller_value", "use_target_value"] = "use_caller_value") -> None:
        """
        Join this observable to another hook (thread-safe).
        
        This triggers Nexus fusion, creating a transitive synchronization domain.
        
        Args:
            target_hook: The hook or observable to join to
            sync_mode: Which value to use initially:
                - "use_caller_value": Use this observable's value
                - "use_target_value": Use the target hook's value
        """
        with self._lock:
            if isinstance(target_hook, CarriesSingleHookProtocol):
                target_hook = target_hook._get_single_hook()
            else:
                target_hook = target_hook
            
            if sync_mode not in ("use_caller_value", "use_target_value"):
                raise ValueError(f"Invalid sync mode: {sync_mode}. Must be 'use_caller_value' or 'use_target_value'")
            
            if sync_mode == "use_caller_value":
                self._value_hook.join(target_hook, "use_caller_value")
            else:
                self._value_hook.join(target_hook, "use_target_value")

    def isolate(self) -> None:
        """
        Isolate this observable from its fusion domain (thread-safe).
        
        Creates a new independent Nexus for this observable.
        """
        with self._lock:
            self._value_hook.isolate()

    def is_joined_with(self, hook: Hook[T] | ReadOnlyHook[T] | CarriesSingleHookProtocol[T]) -> bool:
        """
        Check if this observable is joined with another hook (thread-safe).
        
        Args:
            hook: The hook or observable to check
            
        Returns:
            True if joined (share the same Nexus), False otherwise
        """
        with self._lock:
            if isinstance(hook, CarriesSingleHookProtocol):
                target_hook = hook._get_single_hook()
            else:
                target_hook = hook
            return self._value_hook.is_joined_with(target_hook)

    #########################################################
    # Validation and Submission
    #########################################################

    def _validate_value(self, key: Literal["value"], value: T, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Validate a value.

        ** This method is not thread-safe and should only be called by the validate_value method.
        
        Args:
            key: The key of the hook to validate
            value: The value to validate
            
        Returns:
            Tuple of (success, message)
        """
        # First check custom verification method if provided
        if self._verification_method is not None:
            try:
                success, msg = self._verification_method(value)
                if not success:
                    return False, msg
            except Exception as e:
                return False, f"Validation error: {e}"
        
        # Then check with NexusManager
        success, msg = self._nexus_manager.submit_values({self._value_hook._get_nexus(): value}, mode="Check values", logger=logger) # type: ignore
        if not success:
            return False, msg
        else:
            return True, "Value is valid"

    def _submit_value(self, key: Literal["value"], value: T, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Submit a new value through the NexusManager.

        ** This method is not thread-safe and should only be called by the submit_value method.
        
        Args:
            hook_key: The key of the hook to submit the value to
            value: The new value to submit
            logger: Optional logger for debugging
            
        Returns:
            Tuple of (success, message)
        """
        success, msg = self._nexus_manager.submit_values({self._value_hook._get_nexus(): value}, mode="Normal submission", logger=logger) # type: ignore
        if not success:
            return False, msg
        else:
            return True, "Value submitted successfully"

    def validate_value(self, value: T, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Validate a value without changing it (thread-safe).
        
        Args:
            value: The value to validate
            logger: Optional logger for debugging
            
        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            return self._validate_value("value", value, logger=logger)

    def submit_value(self, value: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Submit a new value (thread-safe).
        
        Args:
            value: The new value to submit
            logger: Optional logger for debugging
            raise_submission_error_flag: If True, raise SubmissionError on failure
            
        Returns:
            Tuple of (success, message)
            
        Raises:
            SubmissionError: If raise_submission_error_flag is True and submission fails
        """
        with self._lock:
            success, msg = self._submit_value("value", value, logger=logger)
            if not success and raise_submission_error_flag:
                raise SubmissionError(msg, value)
            return success, msg

    #########################################################
    # CarriesSomeHooksProtocol implementation
    #########################################################

    def _get_hook_by_key(self, key: Literal["value"]) -> OwnedHookProtocol[T]:
        """
        Get a hook by its key.

        ** This method is not thread-safe and should only be called by the get_hook method.

        Args:
            key: The key of the hook to get

        Returns:
            The hook associated with the key
        """
        return self._value_hook

    def _get_value_by_key(self, key: Literal["value"]) -> T:
        """
        Get a value as a copy by its key.

        ** This method is not thread-safe and should only be called by the get_value_of_hook method.

        Args:
            key: The key of the hook to get the value of
        """
        return self._value_hook.value

    def _get_hook_keys(self) -> set[Literal["value"]]:
        """
        Get all keys of the hooks.

        ** This method is not thread-safe and should only be called by the get_hook_keys method.

        Returns:
            The set of keys for the hooks
        """
        return set(["value"])

    def _get_key_by_hook_or_nexus(self, hook_or_nexus: OwnedHookProtocol[T]|Nexus[T]) -> Literal["value"]:
        """
        Get the key for a hook or nexus.

        ** This method is not thread-safe and should only be called by the get_hook_key method.

        Args:
            hook_or_nexus: The hook or nexus to get the key for

        Returns:
            The key for the hook or nexus
        """
        return "value"

    def _join(self, source_hook_key: Literal["value"], target_hook: Hook[T] | ReadOnlyHook[T] | CarriesSingleHookProtocol[T], initial_sync_mode: Literal["use_caller_value", "use_target_value"] = "use_caller_value") -> None:
        """
        Join the single hook to the target hook.

        ** This method is not thread-safe and should only be called by the join method.
        """
        if source_hook_key != "value":
            raise ValueError(f"Invalid source hook key: {source_hook_key}")

        self._value_hook.join(target_hook, initial_sync_mode)

    def _isolate(self, key: Optional[Literal["value"]] = None) -> None:
        """
        Isolate the single hook.

        ** This method is not thread-safe and should only be called by the isolate method.
        """
        self._value_hook.isolate()

    #########################################################
    # ObservableSerializable implementation
    #########################################################

    def get_values_for_serialization(self) -> Mapping[Literal["value"], T]:
        return {"value": self._value_hook.value}

    def set_values_from_serialization(self, values: Mapping[Literal["value"], T]) -> None:
        success, msg = self._submit_value("value", values["value"])
        if not success:
            raise ValueError(msg)