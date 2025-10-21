from typing import Generic, TypeVar, Optional, Mapping, Callable
from logging import Logger

from ...core.hooks.owned_hook import OwnedHook
from ...core.hooks.hook_aliases import Hook, ReadOnlyHook
from ...core.hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ...core.hooks.hook_protocols.owned_full_hook_protocol import OwnedFullHookProtocol
from ...core.auxiliary.listening_base import ListeningBase
from ...x_objects_base.x_base import XBase
from ...core.nexus_system.nexus import Nexus
from ...core.nexus_system.update_function_values import UpdateFunctionValues
from ...core.nexus_system.submission_error import SubmissionError
from .function_values import FunctionValues
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore

SHK = TypeVar("SHK")
SHV = TypeVar("SHV")

class XFunction(ListeningBase, XBase[SHK, SHV, "XFunction"], Generic[SHK, SHV]):


    def __init__(
        self,
        complete_variables_per_key: Mapping[SHK, Hook[SHV]|ReadOnlyHook[SHV]|SHV],
        completing_function_callable: Callable[[FunctionValues[SHK, SHV]], tuple[bool, dict[SHK, SHV]]],
        *,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ) -> None:


        self._completing_function_callable = completing_function_callable

        # Create sync hooks with initial values
        self._sync_hooks: dict[SHK, OwnedHook[SHV]] = {}
        for key, initial_value in complete_variables_per_key.items():
            sync_hook: OwnedHook[SHV] = OwnedHook[SHV](
                owner=self,
                initial_value=initial_value.value if isinstance(initial_value, ManagedHookProtocol) else initial_value, # type: ignore
                logger=logger,
                nexus_manager=nexus_manager
            )
            self._sync_hooks[key] = sync_hook

        ListeningBase.__init__(self, logger)

        def add_values_to_be_updated_callback(
            self_ref: "XFunction[SHK, SHV]",
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
                    completed_values[key] = update_values.submitted[key] # type: ignore
                elif key in synced_values:
                    completed_values[key] = synced_values[key] # type: ignore
                else:
                    completed_values[key] = update_values.current[key] # type: ignore

            # Add all synced values to the values to be added, if they are not already in the submitted values
            for key in synced_values: # type: ignore
                if not key in update_values.submitted:
                    values_to_be_added[key] = synced_values[key] # type: ignore

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
            invalidate_callback=None,
            validate_complete_values_in_isolation_callback=None,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback
        )

        # Connect internal hooks to external hooks if provided
        for key, external_hook_or_value in complete_variables_per_key.items():
            internal_hook = self._sync_hooks[key]
            if isinstance(external_hook_or_value, ManagedHookProtocol): # type: ignore
                internal_hook.join(external_hook_or_value, "use_caller_value") # type: ignore

    #########################################################################
    # CarriesSomeHooksBase abstract methods
    #########################################################################

    def _get_hook_by_key(self, key: SHK) -> OwnedFullHookProtocol[SHV]:
        """
        Get a hook by its key.
        
        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The hook associated with the key.
        """
        if key in self._sync_hooks:
            return self._sync_hooks[key] # type: ignore
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
            return self._sync_hooks[key].value # type: ignore
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

    def _get_key_by_hook_or_nexus(self, hook_or_nexus: "Hook[SHV]|Nexus[SHV]") -> SHK:
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

    def hook(self, key: SHK) -> Hook[SHV]:
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

    def key(self, hook: Hook[SHV]) -> SHK:
        """
        Get a key by its hook.

        ** Thread-safe **

        Returns:
            The key associated with the hook.
        """
        with self._lock:
            return self._get_key_by_hook_or_nexus(hook)

    def hooks(self) -> dict[SHK, Hook[SHV]]:
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