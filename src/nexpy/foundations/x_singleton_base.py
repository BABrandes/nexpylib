from typing import Callable, Generic, Literal, Mapping, Optional, TypeVar, Self, Any
from logging import Logger
from threading import RLock

from ..core.hooks import OwnedWritableHook, HookProtocol, OwnedHookProtocol
from ..core.nexus_system.nexus import Nexus
from ..core.nexus_system.nexus_manager import NexusManager
from ..core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from ..core.nexus_system.submission_error import SubmissionError

from .carries_single_hook_protocol import CarriesSingleHookProtocol
from .x_base import XBase

T = TypeVar("T")

class XSingletonBase(XBase[Literal["value"], T], CarriesSingleHookProtocol[T], Generic[T]):
    """
    Base class for singleton X objects (single value) with transitive synchronization via Nexus fusion.

    Generic type parameters:
        T: The type of the value

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
            value_or_hook: T|HookProtocol[T]|CarriesSingleHookProtocol[T],
            validate_value_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
            invalidate_after_update_callback: Optional[Callable[[], None]] = None,
            logger: Optional[Logger] = None,
            nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER,
            preferred_publish_mode: Literal["async", "sync", "direct", "off"] = "async"):
        """
        Initialize the XSingletonBase.
        
        Args:
            value_or_hook: Initial value or Hook to join to
            validate_value_callback: Optional validation function for the value
            invalidate_after_update_callback: Optional callback executed after successful state changes
            logger: Optional logger for debugging
            nexus_manager: NexusManager for coordinating updates
        """

        #-------------------------------- Initialization start --------------------------------

        # Initialize lock first
        self._lock = RLock()

        # Extract value and optional hook to join
        if isinstance(value_or_hook, CarriesSingleHookProtocol):
            initial_value: T = value_or_hook._get_single_value() # type: ignore
            external_hook: Optional[OwnedHookProtocol[T]] = value_or_hook._get_single_hook() # type: ignore    
        elif isinstance(value_or_hook, HookProtocol):
            initial_value: T = value_or_hook.value # type: ignore
            external_hook = value_or_hook # type: ignore
        else:
            # Is T
            initial_value = value_or_hook
            external_hook = None

        # Create the value hook
        self._value_hook = OwnedWritableHook[T, Self](
            self,
            initial_value, # type: ignore
            logger,
            nexus_manager
            )

        # Create validation callback wrapper for XBase
        # This captures the user's validation callback directly (no need to store it separately)
        def validate_complete_values_callback_wrapper(values: Mapping[Literal["value"], T]) -> tuple[bool, str]:
            """Validate the complete values using the user's validation method."""
            if "value" not in values:
                return False, "Value key not found in values"
            
            value = values["value"]
            
            # Use custom verification method if provided
            if validate_value_callback is not None:
                try:
                    success, msg = validate_value_callback(value)
                    if not success:
                        return False, msg
                except Exception as e:
                    return False, f"Validation error: {e}"
            
            return True, "Value is valid"

        # Create invalidation callback wrapper for XBase
        def xbase_invalidate_after_update_callback_wrapper() -> tuple[bool, str]:
            """Call user's invalidate callback if provided."""
            if invalidate_after_update_callback is not None:
                try:
                    invalidate_after_update_callback()
                except Exception as e:
                    return False, f"Invalidation error: {e}"
            return True, "Invalidated successfully"

        # Initialize XBase - it will handle weak reference storage
        XBase.__init__( # type: ignore
            self,
            invalidate_after_update_callback=xbase_invalidate_after_update_callback_wrapper,
            validate_complete_values_callback=validate_complete_values_callback_wrapper,
            logger=logger,
            nexus_manager=nexus_manager,
            preferred_publish_mode=preferred_publish_mode
        )

        # If initialized with a Hook, join to it
        self._value_hook.join(external_hook, "use_target_value") if external_hook is not None else None # type: ignore

        #-------------------------------- Initialize finished --------------------------------

    #########################################################
    # CarriesSingleHookProtocol implementation
    #########################################################

    def _get_single_hook(self) -> OwnedWritableHook[T, Self]:
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
        return self._value_hook._get_value() # type: ignore

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

    def join(self, target_hook: HookProtocol[T] | CarriesSingleHookProtocol[T], sync_mode: Literal["use_caller_value", "use_target_value"] = "use_caller_value") -> None:
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

    def is_joined_with(self, hook: HookProtocol[T] | CarriesSingleHookProtocol[T]) -> bool:
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

    # Note: _validate_value() is inherited from XBase and uses the validation callback we provided
    # No need to override it here!

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

    def _get_hook_by_key(self, key: Literal["value"]) -> OwnedWritableHook[T, Self]:
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
        return self._value_hook._get_value() # type: ignore

    def _get_hook_keys(self) -> set[Literal["value"]]:
        """
        Get all keys of the hooks.

        ** This method is not thread-safe and should only be called by the get_hook_keys method.

        Returns:
            The set of keys for the hooks
        """
        return set(["value"])

    def _get_key_by_hook_or_nexus(self, hook_or_nexus: OwnedHookProtocol[T, Any]|Nexus[T]) -> Literal["value"]:
        """
        Get the key for a hook or nexus.

        ** This method is not thread-safe and should only be called by the get_hook_key method.

        Args:
            hook_or_nexus: The hook or nexus to get the key for

        Returns:
            The key for the hook or nexus
        """
        return "value"

    def _join(self, source_hook_key: Literal["value"], target_hook: HookProtocol[T] | CarriesSingleHookProtocol[T], initial_sync_mode: Literal["use_caller_value", "use_target_value"] = "use_caller_value") -> None:
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
        return {"value": self._value_hook._get_value()} # type: ignore

    def set_values_from_serialization(self, values: Mapping[Literal["value"], T]) -> None:
        success, msg = self._submit_values({"value": values["value"]})
        if not success:
            raise ValueError(f"Failed to set values from serialization: {msg}")