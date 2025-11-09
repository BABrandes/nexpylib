from typing import Any, TypeVar, Optional, final, Mapping, Generic, Callable, Literal, Self
import warnings
import uuid
from logging import Logger
from abc import abstractmethod
from threading import RLock



from ..core.nexus_system.nexus_manager import NexusManager
from ..core.nexus_system.nexus import Nexus
from ..core.nexus_system.update_function_values import UpdateFunctionValues
from ..core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from ..core.hooks import OwnedHookProtocol, HookProtocol
from ..core.publisher_subscriber.publisher_mixin import PublisherMixin
from ..core.auxiliary.listenable_mixin import ListenableMixin
from ..core.auxiliary.utils import make_weak_callback

from .carries_some_hooks_protocol import CarriesSomeHooksProtocol
from .carries_single_hook_protocol import CarriesSingleHookProtocol

from .serializable_protocol import SerializableProtocol

HK = TypeVar("HK")
HV = TypeVar("HV")


class XBase(CarriesSomeHooksProtocol[HK, HV], ListenableMixin, PublisherMixin, SerializableProtocol[HK, HV], Generic[HK, HV]):
    """
    Base class for observables in the new hook-based architecture.


    Generic type parameters:
        HK: The type of the hook keys
        HV: The type of the hook values

    This class provides the core functionality for observables that manage multiple
    hooks and participate in the sync system. It replaces the old binding system
    with a more flexible approach where observables define their own logic for:
    
    - Value completion (add_values_to_be_updated_callback)
    - Value validation (validate_complete_values_in_isolation_callback)  
    - Invalidation (invalidate_callback)
    
    The new architecture allows observables to define custom behavior for how
    values are synchronized and validated, making the system more extensible.

    Inheritance Structure:
    - Inherits from: CarriesSomeHooksProtocol[HK, HV] (Protocol), Generic[HK, HV], ABC
    - Implements: Most CarriesSomeHooksProtocol methods as @final methods with thread safety
    - Provides: Core sync system functionality, validation, and hook management

    Abstract Methods (Must Implement):
    Subclasses must implement these 4 abstract methods to define their specific behavior:
    
    1. _get_hook(key: HK) -> HookWithOwnerProtocol[HV]
       - Get a hook by its key
       - Must return the hook associated with the given key
       
    2. _get_value_reference_of_hook(key: HK) -> HV  
       - Get a value as a reference by its key
       - Must return a reference to the actual value (not a copy)
       - Modifying the returned value should modify the observable
       
    3. _get_hook_keys() -> set[HK]
       - Get all keys of the hooks managed by this observable
       - Must return the complete set of hook keys
       
    4. _get_hook_key(hook_or_nexus: HookWithOwnerProtocol[HV]|Nexus[HV]) -> HK
       - Get the key for a given hook or nexus
       - Must return the key that identifies the hook/nexus
       - Should raise ValueError if hook/nexus not found

    Provided Functionality:
    - Thread-safe access to all methods via RLock
    - Complete implementation of CarriesSomeHooksProtocol protocol
    - Hook connection/disconnection management
    - Value submission and validation via NexusManager
    - Memory management and cleanup via destroy()
    - Callback-based customization for validation and value completion
    
    Example Implementation:
        class MyObservable(BaseCarriesHooks[str, Any]):
            def __init__(self):
                super().__init__()
                self._hooks = {"value": OwnedHook(self, "initial")}
                
            def _get_hook(self, key: str) -> HookWithOwnerProtocol[Any]:
                return self._hooks[key]
                
            def _get_value_reference_of_hook(self, key: str) -> Any:
                return self._hooks[key].value
                
            def _get_hook_keys(self) -> set[str]:
                return set(self._hooks.keys())
                
            def _get_hook_key(self, hook_or_nexus: HookWithOwnerProtocol[Any]|Nexus[Any]) -> str:
                for key, hook in self._hooks.items():
                    if hook is hook_or_nexus or hook._get_nexus() is hook_or_nexus:  # type: ignore
                        return key
                raise ValueError("Hook not found")
    """

    def __init__(
        self,
        *,
        invalidate_after_update_callback: Optional[Callable[[], tuple[bool, str]]] = None,
        validate_complete_values_callback: Optional[Callable[[Mapping[HK, HV]], tuple[bool, str]]] = None,
        compute_missing_values_callback: Optional[Callable[[UpdateFunctionValues[HK, HV]], Mapping[HK, HV]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER, 
        preferred_publish_mode: Literal["async", "sync", "direct", "off"] = "async",
        ) -> None:
        """
        Initialize the XBase.
        """
        ListenableMixin.__init__(self)
        PublisherMixin.__init__(self, preferred_publish_mode=preferred_publish_mode)

        # Store callbacks (nested closures don't need weak references, bound methods would)
        self._invalidate_after_update_callback = make_weak_callback(invalidate_after_update_callback)
        self._validate_complete_values_callback = make_weak_callback(validate_complete_values_callback)
        self._compute_missing_values_callback = make_weak_callback(compute_missing_values_callback)
        self._logger: Optional[Logger] = logger
        self._nexus_manager: NexusManager = nexus_manager
        self._uuid: uuid.UUID = uuid.uuid4()

        self._lock = RLock()

    @property
    def nexus_manager(self) -> NexusManager:
        """
        Get the nexus manager that this xobject is using.
        """
        return self._nexus_manager

    #########################################################
    # Private methods
    #########################################################

    @final
    def _invalidate(self, raise_error_mode: Literal["raise", "ignore", "warn"] = "raise") -> tuple[bool, str]:
        """
        Invalidate all hooks.

        ** Thread-safe **

        Returns:
            A tuple of (success: bool, message: str)

        Raises:
            ValueError: If the owner has been garbage collected
            ValueError: If the invalidate callback is not provided
        """

        if self._invalidate_after_update_callback is not None:
            try:
                success, msg = self._invalidate_after_update_callback()
                if success == False:
                    return False, msg
                else:
                    return True, msg
            except Exception as e:
                if raise_error_mode == "raise":
                    raise e
                elif raise_error_mode == "ignore":
                    success = False
                    msg = f"Error in invalidate callback: {e}"
                    return success, msg
                elif raise_error_mode == "warn":
                    warnings.warn(f"Error in invalidate callback: {e}", stacklevel=2)
                    success = False
                    msg = f"Error in invalidate callback: {e}"
                    return success, msg
        else:
            return True, "No invalidate callback provided"

    @final
    def _validate_complete_values_in_isolation(self, values: Mapping[HK, HV]) -> tuple[bool, str]:
        """
        Check if the values are valid as part of the owner.
        
        Values are provided for all hooks according to get_hook_keys().

        ** Thread-safe **

        Returns:
            A tuple of (success: bool, message: str)

        Raises:
            ValueError: If the validate complete values in isolation callback is not provided
        """


        if self._validate_complete_values_callback is not None:
            return self._validate_complete_values_callback(values)
        else:
            return True, "No validation in isolation callback provided"

    @final
    def _get_value_of_hook(self, key: HK) -> HV:
        """
        Get a value as a copy by its key.

        ** This method is not thread-safe and should only be called by the get_value_of_hook method.

        Args:
            key: The key of the hook to get the value of

        Returns:
            The value of the hook
        """

        value = self._get_value_by_key(key)
        return value

    @final
    def _get_dict_of_hooks(self) ->  Mapping[HK, OwnedHookProtocol[HV, Self]]:
        """
        Get a dictionary of hooks.

        ** This method is not thread-safe and should only be called by the get_dict_of_hooks method.

        Returns:
            A dictionary of keys to hooks
        """
        hook_dict: dict[HK, OwnedHookProtocol[HV, Self]] = {}
        for key in self._get_hook_keys():
            hook_dict[key] = self._get_hook_by_key(key)
        return hook_dict

    @final
    def _get_dict_of_values(self) -> Mapping[HK, HV]:
        """
        Get a dictionary of values.

        ** This method is not thread-safe and should only be called by the get_dict_of_values method.

        Returns:
            A dictionary of keys to values
        """

        hook_value_dict: Mapping[HK, HV] = {}
        for key in self._get_hook_keys():
            hook_value_dict[key] = self._get_value_of_hook(key)
        return hook_value_dict

    @final
    def _add_values_to_be_updated(self, values: UpdateFunctionValues[HK, HV]) -> Mapping[HK, HV]:
        """
        Add values to be updated.

        ** This method is not thread-safe and should only be called by the add_values_to_be_updated method.
        
        Args:
            values: UpdateFunctionValues containing current (complete state) and submitted (being updated) values
            
        Returns:
            Mapping of additional hook keys to values that should be updated
        """
        with self._lock:
            if self._compute_missing_values_callback is not None:
                return self._compute_missing_values_callback(values)
            else:
                return {}

    def _join(self, source_hook_key: HK, target_hook: HookProtocol[HV]|CarriesSingleHookProtocol[HV], initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Connect a hook to the observable.

        ** This method is not thread-safe and should only be called by the join method.

        Args:
            source_hook_key: The key of the hook to connect
            target_hook: The hook to connect
            initial_sync_mode: The initial synchronization mode

        Raises:
            ValueError: If the source hook key is not found in component_hooks or secondary_hooks
            ValueError: If the connection fails
            ValueError: If the initial synchronization mode is invalid
        """

        if source_hook_key in self._get_hook_keys():
            source_hook: OwnedHookProtocol[HV, Self] = self._get_hook_by_key(source_hook_key)
            if isinstance(target_hook, CarriesSingleHookProtocol):
                target_hook = target_hook._get_hook_by_key(source_hook_key) # type: ignore
            success, msg = source_hook._join(target_hook, initial_sync_mode) # type: ignore
            if not success:
                raise ValueError(msg)
        else:
            raise ValueError(f"Key {source_hook_key} not found in component_hooks or secondary_hooks")

    def _join_many(self, hooks: Mapping[HK, HookProtocol[HV]], initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Connect multiple hooks to the observable simultaneously.

        ** This method is not thread-safe and should only be called by the join_many method.

        Args:
            hooks: A mapping of keys to external hooks to connect
            initial_sync_mode: Determines which hook's value is used initially for each connection:
                - "use_caller_value": Use the external hook's value
                - "use_target_value": Use the observable hook's value

        Raises:
            ValueError: If any key is not found in component_hooks or secondary_hooks
        """

        hook_pairs: list[tuple[HookProtocol[HV], HookProtocol[HV]]] = []
        for key, hook in hooks.items():
            hook_of_observable = self._get_hook_by_key(key)
            match initial_sync_mode:
                case "use_caller_value":
                    hook_pairs.append((hook_of_observable, hook))
                case "use_target_value":
                    hook_pairs.append((hook, hook_of_observable))
                case _: # type: ignore
                    raise ValueError(f"Invalid initial sync mode: {initial_sync_mode}")
        Nexus[HV].join_hook_pairs(*hook_pairs)

    def _isolate(self, key: Optional[HK] = None) -> None:
        """
        Isolate a hook by its key.

        ** This method is not thread-safe and should only be called by the isolate method.

        Args:
            key: The key of the hook to disconnect. If None, all hooks will be disconnected.
        """

        if key is None:
            for hook in self._get_dict_of_hooks().values():
                hook._isolate() # type: ignore
        else:
            self._get_hook_by_key(key)._isolate() # type: ignore

    def _destroy(self) -> None:
        """
        Destroy the observable by disconnecting all hooks, removing listeners, and invalidating.

        ** This method is not thread-safe and should only be called by the destroy method.
        
        This method should be called before the observable is deleted to ensure proper
        memory cleanup and prevent memory leaks. After calling this method, the observable
        should not be used anymore as it will be in an invalid state.
        
        Example:
            >>> obs = XValue("test")
            >>> obs.cleanup()  # Properly clean up before deletion
            >>> del obs
        """

        # Isolate all hooks
        self._isolate(None)

        # Remove all listeners
        self._listeners.clear()

    def _validate_value(self, key: HK, value: HV, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Check if a value is valid.

        ** This method is not thread-safe and should only be called by the validate_value method.

        Args:
            hook_key: The key of the hook to validate
            value: The value to validate

        Returns:
            A tuple of (success: bool, message: str)
        """

        hook: OwnedHookProtocol[HV, Self] = self._get_hook_by_key(key)

        success, msg = self._nexus_manager.submit_values({hook._get_nexus(): value}, mode="Check values", logger=logger) # type: ignore
        if success == False:
            return False, msg
        else:
            return True, "Value is valid"

    def _validate_values(self, values: Mapping[HK, HV], *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Check if the values can be accepted.

        ** This method is not thread-safe and should only be called by the validate_values method.

        Args:
            values: The values to validate

        Returns:
            A tuple of (success: bool, message: str)
        """

        if len(values) == 0:
            return True, "No values provided"

        nexus_and_values: Mapping[Nexus[Any], Any] = self._get_nexus_and_values(values)
        success, msg = self._nexus_manager.submit_values(nexus_and_values, mode="Check values", logger=logger)
        if success == True:
            return True, msg
        else:
            return False, msg

    def _submit_value(self, key: HK, value: HV, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Submit a value to the observable.

        ** This method is not thread-safe and should only be called by the submit_value method.
        
        Args:
            key: The key of the hook to submit the value to
            value: The value to submit
            logger: Optional logger for debugging

        Returns:
            Tuple of (success: bool, message: str)
        """
        success, msg = self._nexus_manager.submit_values(
            {self._get_hook_by_key(key)._get_nexus(): value}, # type: ignore
            mode="Normal submission",
            logger=logger
        )
        return success, msg

    def _submit_values(self, values: Mapping[HK, HV], *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Submit values to the observable using the new hook-based sync system.

        ** This method is not thread-safe and should only be called by the validate_value method.
        
        This method is the main entry point for value submissions in the new architecture.
        It converts the submitted values into nexus-and-values format and delegates to
        the NexusManager for processing.
        
        The NexusManager will:
        1. Complete missing values using add_values_to_be_updated_callback
        2. Validate all values using validation callbacks
        3. Update hook nexuses with new values
        4. Trigger invalidation and listener notifications
        
        Args:
            values: Mapping of hook keys to their new values
            logger: Optional logger for debugging
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails
            
        Returns:
            Tuple of (success: bool, message: str)
        """

        nexus_and_values: dict[Nexus[Any], Any] = self._get_nexus_and_values(values)
        success, msg = self._nexus_manager.submit_values(
            nexus_and_values,
            logger=logger
        )
        return success, msg

    def _get_nexus_and_values(self, values: Mapping[HK, HV]) -> dict[Nexus[Any], Any]:
        """
        Get a dictionary of nexuses and values.
        """
        nexus_and_values: dict[Nexus[Any], Any] = {}
        for key, value in values.items():
            nexus_and_values[self._get_hook_by_key(key)._get_nexus()] = value # type: ignore
        return nexus_and_values

    def _get_nexus_manager(self) -> "NexusManager":
        return self._nexus_manager

    # ------------------ To be implemented by subclasses ------------------

    @abstractmethod
    def _get_hook_by_key(self, key: HK) -> OwnedHookProtocol[HV, Self]:
        """
        Get a hook by its key.

        ** This method is not thread-safe and should only be called by the get_hook method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Args:
            key: The key of the hook to get

        Returns:
            The hook associated with the key
        """
        ...

    @abstractmethod
    def _get_value_by_key(self, key: HK) -> HV:
        """
        Get a value as a copy by its key.

        ** This method is not thread-safe and should only be called by the get_value_of_hook method.

        ** Must be implemented by subclasses to provide efficient lookup for values.

        Args:
            key: The key of the hook to get the value of
        """
        ...

    @abstractmethod
    def _get_hook_keys(self) -> set[HK]:
        """
        Get all keys of the hooks.

        ** This method is not thread-safe and should only be called by the get_hook_keys method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Returns:
            The set of keys for the hooks
        """
        ...

    @abstractmethod
    def _get_key_by_hook_or_nexus(self, hook_or_nexus: OwnedHookProtocol[HV, Any]|Nexus[HV]) -> HK:
        """
        Get the key for a hook or nexus.

        ** This method is not thread-safe and should only be called by the get_hook_key method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Args:
            hook_or_nexus: The hook or nexus to get the key for

        Returns:
            The key for the hook or nexus
        """
        ...

    #########################################################
    # Hash and equality support (using UUID)
    #########################################################

    def __hash__(self) -> int:
        """
        Make XBase hashable using UUID.
        
        This allows XObjects to be used in sets and as dictionary keys.
        """
        return hash(self._uuid)
    
    def __eq__(self, other: Any) -> bool:
        """
        Compare XBase instances by UUID.
        
        Args:
            other: Another object to compare with
            
        Returns:
            True if both objects are XBase instances with the same UUID, False otherwise
        """
        if not isinstance(other, XBase):
            return False
        return self._uuid == other._uuid