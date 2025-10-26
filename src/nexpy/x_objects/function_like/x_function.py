from typing import Generic, TypeVar, Optional, Mapping, Callable, Self
from logging import Logger

from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from nexpy.core.hooks.protocols.hook_protocol import HookProtocol
from nexpy.foundations.x_base import XBase
from nexpy.core.nexus_system.nexus import Nexus
from nexpy.core.nexus_system.update_function_values import UpdateFunctionValues
from nexpy.core.nexus_system.submission_error import SubmissionError
from .function_values import FunctionValues
from nexpy.core.nexus_system.nexus_manager import NexusManager
from nexpy.core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore

SHK = TypeVar("SHK")
SHV = TypeVar("SHV")

class XFunction(XBase[SHK, SHV], Generic[SHK, SHV]):


    def __init__(
        self,
        complete_variables_per_key: Mapping[SHK, HookProtocol[SHV]|SHV],
        completing_function_callable: Callable[[FunctionValues[SHK, SHV]], tuple[bool, dict[SHK, SHV]]],
        *,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ) -> None:


        self._completing_function_callable = completing_function_callable

        # Create sync hooks with initial values
        self._sync_hooks: dict[SHK, OwnedWritableHook[SHV, Self]] = {}
        for key, initial_value in complete_variables_per_key.items():
            sync_hook: OwnedWritableHook[SHV, Self] = OwnedWritableHook[SHV, Self](
                owner=self,
                value=initial_value.value if isinstance(initial_value, HookProtocol) else initial_value, # type: ignore
                logger=logger,
                nexus_manager=nexus_manager
            )
            self._sync_hooks[key] = sync_hook

        def add_values_to_be_updated_callback(
            self_ref: Self,
            update_values: UpdateFunctionValues[SHK, SHV]
        ) -> Mapping[SHK, SHV]:
            """
            Add values to be updated by triggering the synchronization function.
            This callback is called when any hook value changes.
            
            The function_callable receives a FunctionValues object containing both 
            submitted (what changed) and current (complete current state) values.
            """

            values_to_be_added: dict[SHK, SHV] = {}
               
            # Create FunctionValues object and call the function
            function_values = FunctionValues(submitted=update_values.submitted, current=update_values.current)
            success, synced_values = self_ref._completing_function_callable(function_values)

            if not success:
                raise ValueError(f"Function callable returned invalid values for combination {update_values.submitted}")

            # Build completed_values by merging: submitted_values, then synced_values, then current values
            completed_values: dict[SHK, SHV] = {}
            for key in self_ref._sync_hooks.keys():
                if key in update_values.submitted:
                    completed_values[key] = update_values.submitted[key]
                elif key in synced_values:
                    completed_values[key] = synced_values[key]
                else:
                    completed_values[key] = update_values.current[key]

            # Add all synced values to the values to be added, if they are not already in the submitted values
            for key in synced_values:
                if not key in update_values.submitted:
                    values_to_be_added[key] = synced_values[key]

            # Call the function again with completed values to validate the final state
            try:
                completed_function_values = FunctionValues(submitted=completed_values, current=completed_values)
                success, _ = self_ref._completing_function_callable(completed_function_values)
                if not success:
                    raise ValueError(f"Function callable returned invalid values for final state {completed_values}")
            except Exception as e:
                raise ValueError(f"Function callable validation failed: {e}")

            return values_to_be_added

        XBase.__init__( # type: ignore
            self,
            logger=logger,
            invalidate_after_update_callback=None,
            validate_complete_values_callback=None,
            compute_missing_values_callback=add_values_to_be_updated_callback # type: ignore
        )

        # Connect internal hooks to external hooks if provided
        for key, external_hook_or_value in complete_variables_per_key.items():
            internal_hook = self._sync_hooks[key]
            if isinstance(external_hook_or_value, HookProtocol):
                internal_hook.join(external_hook_or_value, "use_caller_value") # type: ignore

    #########################################################
    # SerializableProtocol implementation
    #########################################################

    def get_values_for_serialization(self) -> Mapping[SHK, SHV]:
        return {key: hook._get_value() for key, hook in self._sync_hooks.items()} # type: ignore
    
    def set_values_from_serialization(self, values: Mapping[SHK, SHV]) -> None:
        values_to_submit: dict[SHK, SHV] = {}
        for key, value in values.items():
            values_to_submit[key] = value
        self._submit_values(values_to_submit)
        
    #########################################################################
    # CarriesSomeHooksBase abstract methods
    #########################################################################

    def _get_hook_by_key(self, key: SHK) -> OwnedWritableHook[SHV, Self]:
        """
        Get a hook by its key.
        
        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The hook associated with the key.
        """
        if key in self._sync_hooks:
            return self._sync_hooks[key]
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_value_by_key(self, key: SHK) -> SHV:
        """
        Get a value by its key.

        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The value of the hook.
        """

        if key in self._sync_hooks:
            return self._sync_hooks[key]._get_value() # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_hook_keys(self) -> set[SHK]:
        """
        Get all hook keys.

        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The set of all hook keys.
        """
        return set(self._sync_hooks.keys())

    def _get_key_by_hook_or_nexus(self, hook_or_nexus: HookProtocol[SHV]|Nexus[SHV]) -> SHK:
        """
        Get a key by its hook or nexus.

        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The key associated with the hook or nexus.
        """
        for key, hook in self._sync_hooks.items():
            if hook is hook_or_nexus:
                return key
        raise ValueError(f"Hook {hook_or_nexus} not found in hooks")

    #########################################################################
    # Public methods
    #########################################################################

    #-------------------------------- Hooks, values, and keys --------------------------------

    def hook(self, key: SHK) -> OwnedWritableHook[SHV, Self]:
        """
        Get a hook by its key.

        ** Thread-safe **

        Returns:
            The hook associated with the key.
        """
        with self._lock:
            return self._get_hook_by_key(key)

    def keys(self) -> set[SHK]:
        """
        Get all hook keys.

        ** Thread-safe **

        Returns:
            The set of all hook keys.
        """
        with self._lock:
            return set(self._get_hook_keys())

    def key(self, hook: OwnedWritableHook[SHV, Self]) -> SHK:
        """
        Get a key by its hook.

        ** Thread-safe **

        Returns:
            The key associated with the hook.
        """
        with self._lock:
            return self._get_key_by_hook_or_nexus(hook)

    def hooks(self) -> dict[SHK, OwnedWritableHook[SHV, Self]]:
        """
        Get all hooks.

        ** Thread-safe **

        Returns:
            The dictionary of hooks.
        """
        with self._lock:
            return self._get_dict_of_hooks() # type: ignore

    def value(self, key: SHK) -> SHV:
        """
        Get a value by its key.

        ** Thread-safe **

        Returns:
            The value of the hook.
        """
        with self._lock:
            return self._get_value_by_key(key)

    #-------------------------------- Functionality --------------------------------

    @property
    def completing_function_callable(self) -> Callable[[FunctionValues[SHK, SHV]], tuple[bool, dict[SHK, SHV]]]:
        """Get the completing function callable."""
        return self._completing_function_callable

    def change_values(self, values: Mapping[SHK, SHV]) -> None:
        """
        Change the values of the X object.
        """
        success, msg = self._submit_values(values)
        if not success:
            raise SubmissionError(msg, values)