from typing import Generic, TypeVar, TYPE_CHECKING, Optional, Literal, Mapping, Any, Callable, Union
from logging import Logger
import inspect
import threading
from threading import RLock

from ....core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from ...nexus_system.submission_error import SubmissionError
from ...auxiliary.listenable_mixin import ListenableMixin
from ...publisher_subscriber.publisher_mixin import PublisherMixin
from ..protocols.hook_protocol import HookProtocol

if TYPE_CHECKING:
    from ....core.nexus_system.nexus_manager import NexusManager
    from ....core.nexus_system.nexus import Nexus
    from ....foundations.carries_single_hook_protocol import CarriesSingleHookProtocol
    from ...publisher_subscriber.subscriber import Subscriber
else:  # pragma: no cover - for type checking only
    Subscriber = Any

SubscriberLike = Union["Subscriber", Callable[[], None]]

T = TypeVar("T")


class HookBase(HookProtocol[T], ListenableMixin, PublisherMixin, Generic[T]):  
    """
    Base class for minimal hook objects.
    """

    #########################################################
    # Initialization
    #########################################################

    def __init__(
        self,
        *,
        value_or_nexus: T|"Nexus[T]",
        logger: Optional[Logger] = None,
        nexus_manager: Optional["NexusManager"] = _DEFAULT_NEXUS_MANAGER,
        preferred_publish_mode: Literal["async", "sync", "direct", "off"] = "async",
        ):

        #-------------------------------- Initialization start --------------------------------

        #-------------------------------- Initalize nexus -------------------------------------

        from nexpy.core.nexus_system.nexus import Nexus

        if isinstance(value_or_nexus, Nexus):
            # Nexus given for value
            if value_or_nexus._nexus_manager != nexus_manager: # type: ignore
                raise ValueError("The nexus manager must be the same")
            self._nexus: "Nexus[T]" = value_or_nexus
        else:
            # Value given for value
            from nexpy.core.nexus_system.nexus import Nexus
            if nexus_manager is None:
                raise ValueError("Nexus manager must be provided if value is given")
            self._nexus = Nexus[T](value_or_nexus, hooks=set[HookProtocol[T]](), logger=logger, nexus_manager=nexus_manager)

        #-------------------------------- Initialize other attributes --------------------------------

        self._logger = logger
        self._lock: threading.RLock = RLock()

        ListenableMixin.__init__(self)
        PublisherMixin.__init__(self, preferred_publish_mode=preferred_publish_mode, logger=logger)

        #-------------------------------- Add hook to nexus --------------------------------
        
        self._nexus.add_hook(self)

        #-------------------------------- Initialization complete --------------------------------

    #########################################################
    # Protocol public methods
    #########################################################

    @property
    def nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this hook belongs to.

        ** Thread-safe **
        """
        with self._lock:
            return self._get_nexus_manager()

    @property
    def nexus(self) -> "Nexus[T]":
        """
        Get the nexus that this hook belongs to.

        ** Thread-safe **
        """
        with self._lock:
            return self._get_nexus()


    def get_value(self) -> T:
        """
        Get the value behind this hook.

        ** Thread-safe **
        """

        with self._lock:
            return self._get_value()

    @property
    def value(self) -> T:
        """
        Get the value behind this hook.

        ** Thread-safe **
        """
        return self._get_value()

    def get_nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this hook belongs to.

        ** Thread-safe **
        """
        return self._get_nexus_manager()

    def get_nexus(self) -> "Nexus[T]":
        """
        Get the nexus that this hook belongs to.

        ** Thread-safe **
        """
        with self._lock:
            return self._get_nexus()

    def join(self, target_hook: "HookProtocol[T]|CarriesSingleHookProtocol[T]", initial_sync_mode: Literal["use_caller_value", "use_target_value"], raise_join_error_flag: bool = True) -> tuple[bool, str]:
        """
        Join this hook to another hook.

        ** Thread-safe **
        """
        with self._lock:
            success, msg = self._join(target_hook, initial_sync_mode)
            if not success and raise_join_error_flag:
                if initial_sync_mode == "use_caller_value":
                    value = self._get_value()
                elif initial_sync_mode == "use_target_value":
                    value = target_hook._get_value() # type: ignore
                else:
                    raise ValueError(f"Invalid initial sync mode: {initial_sync_mode}")
                raise SubmissionError(msg, value)
            return success, msg

    def isolate(self) -> None:
        """
        Isolate this hook from the nexus.

        ** Thread-safe **
        """
        with self._lock:
            return self._isolate()

    def is_joined_with(self, target_hook_or_nexus: "HookProtocol[T]|Nexus[T]|CarriesSingleHookProtocol[T]") -> bool:
        """
        Check if this hook is joined to another hook or the hook of a CarriesSingleHookProtocol.

        ** Thread-safe **
        """
        with self._lock:
            return self._is_joined_with(target_hook_or_nexus)

    def is_joined(self) -> bool:
        """
        Check if this hook is joined to other hooks via a shared nexus.

        ** Thread-safe **
        """
        with self._lock:
            return self._is_joined()

    #########################################################
    # PublisherProtocol forwarding methods (resolving linter errors, could be removed...)
    #########################################################

    def add_subscriber(self, subscriber: SubscriberLike) -> None:
        """
        Add a subscriber or callback to receive publications from this hook.
        """
        PublisherMixin.add_subscriber(self, subscriber)

    def remove_subscriber(self, subscriber: SubscriberLike) -> None:
        """
        Remove a subscriber or callback from this hook.
        """
        PublisherMixin.remove_subscriber(self, subscriber)

    def publish(
        self,
        mode: Literal["async", "sync", "direct", "off", None] = None,
        raise_error_mode: Literal["raise", "ignore", "warn"] = "raise",
    ) -> None:
        """
        Publish an update to all subscribed listeners.
        """
        PublisherMixin.publish(self, mode=mode, raise_error_mode=raise_error_mode)

    @property
    def preferred_publish_mode(self) -> Literal["async", "sync", "direct", "off"]:
        """
        Get the preferred publish mode for this hook.
        """
        return PublisherMixin.preferred_publish_mode.fget(self)  # type: ignore[misc]

    @preferred_publish_mode.setter
    def preferred_publish_mode(self, mode: Literal["async", "sync", "direct", "off"]) -> None:
        """
        Set the preferred publish mode for this hook.
        """
        PublisherMixin.preferred_publish_mode.fset(self, mode)  # type: ignore[misc]

    #########################################################
    # Protocol private methods
    #########################################################

    def _get_value(self) -> T:
        """
        Get the value behind this hook.
        """
        return self._nexus._stored_value # type: ignore

    def _get_nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this hook belongs to.
        """
        return self._nexus._nexus_manager # type: ignore

    def _get_nexus(self) -> "Nexus[T]":
        """
        Get the nexus that this hook belongs to.
        """
        return self._nexus

    def _join(self, target_hook: "HookProtocol[T]|CarriesSingleHookProtocol[T]", initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> tuple[bool, str]:
        """
        Join this hook to another hook.

        ** This method is not thread-safe and should only be called by the join method.

        This method implements the core hook connection process:
        
        1. Get the two nexuses from the hooks to connect
        2. Submit one of the hooks' value to the other nexus
        3. If successful, both nexus must now have the same value
        4. Merge the nexuses to one -> Connection established!
        
        After connection, both hooks will share the same nexus and remain synchronized.

        Args:
            target_hook: The hook or CarriesSingleHookProtocol to connect to
            initial_sync_mode: Determines which hook's value is used initially:
                - "use_caller_value": Use this hook's value (caller = self)
                - "use_target_value": Use the target hook's value
            
        Returns:
            A tuple containing a boolean indicating if the connection was successful and a string message
        """

        from nexpy.core.nexus_system.nexus import Nexus
        from nexpy.foundations.carries_single_hook_protocol import CarriesSingleHookProtocol

        if target_hook is None:
            raise ValueError("Cannot connect to None hook")

        if isinstance(target_hook, CarriesSingleHookProtocol):
            target_hook = target_hook._get_single_hook() # type: ignore
        
        # Prevent joining a hook to itself
        if self is target_hook:
            raise ValueError("Cannot join a hook to itself")
        
        # Deadlock prevention: Check if hooks are already joined
        # If they share the same nexus, joining again is a no-op (but not an error)
        if self._nexus is target_hook._get_nexus():
            return True, "Hooks already joined"
        
        if initial_sync_mode == "use_caller_value":
            success, msg = Nexus[T].join_hook_pairs((self, target_hook))
        elif initial_sync_mode == "use_target_value":                
            success, msg = Nexus[T].join_hook_pairs((target_hook, self))
        else:
            raise ValueError(f"Invalid sync mode: {initial_sync_mode}")

        return success, msg
    
    def _isolate(self) -> None:
        """
        Isolate this hook from the hook nexus.

        ** This method is not thread-safe and should only be called by the isolate method.

        If this is the corresponding nexus has only this one hook, nothing will happen.
        """

        from nexpy.core.nexus_system.nexus import Nexus

        # Check if we're being called during garbage collection by inspecting the call stack
        is_being_garbage_collected = any(frame.function == '__del__' for frame in inspect.stack())

        # If we're being garbage collected and not in the nexus anymore,
        # it means other hooks were already garbage collected and their weak
        # references were cleaned up. This is fine - just skip the disconnect.
        if is_being_garbage_collected and self not in self._nexus.hooks:
            return
        
        if self not in self._nexus.hooks:
            raise ValueError("Hook was not found in its own hook nexus!")
        
        if len(self._nexus.hooks) <= 1:
            # If we're the last hook, we're already effectively disconnected
            return
        
        # Create a new isolated nexus for this hook
        new_hook_nexus = Nexus(self._get_value(), hooks={self}, nexus_manager=self._get_nexus_manager(), logger=self._logger)
        
        # Remove this hook from the current nexus
        self._nexus.remove_hook(self)
        
        # Update this hook's nexus reference
        self._nexus = new_hook_nexus

        # The remaining hooks in the old nexus will continue to be bound together
        # This effectively breaks the connection between this hook and all others

    def _is_joined_with(self, target_hook_or_nexus: "HookProtocol[T]|Nexus[T]|CarriesSingleHookProtocol[T]") -> bool:
        """
        Check if this hook is joined to another hook or the hook of a CarriesSingleHookProtocol.

        ** This method is not thread-safe and should only be called by the is_joined_with method.

        Args:
            target_hook_or_nexus: The hook or CarriesSingleHookProtocol to check if it is joined to

        Returns:
            True if the hook is joined to the other hook or CarriesSingleHookProtocol, False otherwise
        """
        # Import at runtime to avoid circular imports
        from nexpy.foundations.carries_single_hook_protocol import CarriesSingleHookProtocol
        from nexpy.core.nexus_system.nexus import Nexus

        if isinstance(target_hook_or_nexus, CarriesSingleHookProtocol):
            target_nexus = target_hook_or_nexus._get_nexus() # type: ignore
        elif isinstance(target_hook_or_nexus, Nexus):
            target_nexus = target_hook_or_nexus
        elif isinstance(target_hook_or_nexus, HookProtocol): # type: ignore
            target_nexus = target_hook_or_nexus._get_nexus()
        else:
            raise ValueError(f"Invalid target hook or nexus: {target_hook_or_nexus}")

        return target_nexus is self._nexus

    def _is_joined(self) -> bool:
        """
        Check if this hook is joined to other hooks via a shared nexus.

        ** This method is not thread-safe and should only be called by the is_joined method.
        """

        return len(self._nexus.hooks) > 1

    def _validate_value(self, value: T, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Check if the value is valid for submission.

        ** This method is not thread-safe and should only be called by the validate_value method.
        
        Note: This method only validates, it does not submit values.
        """
        return self._get_nexus_manager().submit_values({self._get_nexus(): value}, mode="Check values", logger=logger)

    @staticmethod
    def _validate_values(values: Mapping["HookProtocol[T]|CarriesSingleHookProtocol[T]", T], *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Check if the values are valid for submission.

        ** This method is not thread-safe and should only be called by the validate_values method.
        
        Note: This method only validates, it does not submit values.
        """

        if len(values) == 0:
            return True, "No values provided"

        nexus_manager: "NexusManager" = next(iter(values.keys()))._get_nexus_manager() # type: ignore
        nexus_and_values: Mapping[Nexus[Any], Any] = {}
        for hook, value in values.items():
            if hook._get_nexus_manager() != nexus_manager: # type: ignore
                raise ValueError("The nexus managers must be the same")
            nexus_and_values[hook._get_nexus()] = value # type: ignore
        return nexus_manager.submit_values(nexus_and_values, mode="Check values", logger=logger)