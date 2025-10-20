from typing import Callable, Generic, Mapping, Optional, TypeVar
from logging import Logger

from ...core.hooks.owned_hook import OwnedHook
from ...core.hooks.hook_aliases import Hook, ReadOnlyHook
from ...core.hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ...core.auxiliary.listening_base import ListeningBase
from ...x_objects_base.carries_some_hooks_base import CarriesSomeHooksBase
from ...core.nexus_system.nexus import Nexus
from ...core.nexus_system.update_function_values import UpdateFunctionValues
from ...core.nexus_system.submission_error import SubmissionError
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER

# Type variables for input and output hook names and values
IHK = TypeVar("IHK")  # Input Hook Keys
OHK = TypeVar("OHK")  # Output Hook Keys
IHV = TypeVar("IHV")  # Input Hook Values
OHV = TypeVar("OHV")  # Output Hook Values


class XOneWayFunction(ListeningBase, CarriesSomeHooksBase[IHK|OHK, IHV|OHV, "XOneWayFunction"], Generic[IHK, OHK, IHV, OHV]):


    def __init__(
        self,
        input_variables_per_key: Mapping[IHK, Hook[IHV]|ReadOnlyHook[IHV]],
        one_way_function_callable: Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]],
        function_output_hook_keys: set[OHK],
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
    ) -> None:

        self._one_way_function_callable: Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]] = one_way_function_callable

        self._input_hooks: dict[IHK, OwnedHook[IHV]] = {}
        self._output_hooks: dict[OHK, OwnedHook[OHV]] = {}

        # Create input hooks for all keys, connecting to external hooks when provided
        for key, external_hook_or_value in input_variables_per_key.items():
            # Create internal hook
            initial_value_input: IHV = external_hook_or_value.value if isinstance(external_hook_or_value, ManagedHookProtocol) else external_hook_or_value # type: ignore
            internal_hook_input: OwnedHook[IHV] = OwnedHook(
                owner=self,
                initial_value=initial_value_input,
                logger=logger,
                nexus_manager=nexus_manager
            )
            self._input_hooks[key] = internal_hook_input

        # Create output hooks for all keys
        output_values: dict[OHK, OHV] = self._one_way_function_callable(self.get_input_values()) # type: ignore
        for key in function_output_hook_keys:
            if key not in output_values:
                raise ValueError(f"Function callable must return all output keys. Missing key: {key}")
            internal_hook_output: OwnedHook[OHV] = OwnedHook(
                owner=self,
                initial_value=output_values[key],
                logger=logger,
                nexus_manager=nexus_manager
            )
            self._output_hooks[key] = internal_hook_output

        ListeningBase.__init__(self, logger)

        def add_values_to_be_updated_callback(
            self_ref: "XOneWayFunction[IHK, OHK, IHV, OHV]",
            update_values: UpdateFunctionValues[IHK|OHK, IHV|OHV]
        ) -> Mapping[IHK|OHK, IHV|OHV]:
            """
            Add values to be updated by triggering the function transformation.
            This callback is called when any hook value changes.
            
            NOTE: The function_callable is ALWAYS called with COMPLETE sets of values
            by merging update_values.submitted (changed keys) with update_values.current (unchanged keys).
            This ensures transformations always have all required inputs available.
            """

            values_to_be_added: dict[IHK|OHK, IHV|OHV] = {}

            # Check if any input values changed - if so, trigger function transformation
            input_keys = set(input_variables_per_key.keys())
            if any(key in update_values.submitted for key in input_keys):
                # Trigger function transformation

                # Use submitted values for changed keys, current values for unchanged keys
                input_values: dict[IHK, IHV] = {}
                for key in input_keys:
                    if key in update_values.submitted:
                        input_values[key] = update_values.submitted[key] # type: ignore
                    else:
                        input_values[key] = update_values.current[key] # type: ignore
                
                # Call function callable with complete input values
                output_values: Mapping[OHK, OHV] = one_way_function_callable(input_values)
                
                # Add all output values to be updated
                values_to_be_added.update(output_values) # type: ignore

            # Remove values that are already in the submitted values
            for key in update_values.submitted:
                values_to_be_added.pop(key, None)

            return values_to_be_added

        CarriesSomeHooksBase.__init__( # type: ignore
            self,
            logger=logger,
            invalidate_callback=None,
            validate_complete_values_in_isolation_callback=None,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback
        )

        # Connect internal input hooks to external hooks if provided
        for key, external_hook_or_value in input_variables_per_key.items():
            internal_hook_input = self._input_hooks[key]
            if isinstance(external_hook_or_value, ManagedHookProtocol): # type: ignore
                internal_hook_input.connect_hook(external_hook_or_value, "use_caller_value") # type: ignore

    #########################################################################
    # CarriesSomeHooksBase abstract methods
    #########################################################################

    def _get_hook_by_key(self, key: IHK|OHK) -> OwnedHook[IHV|OHV]:
        """
        Get a hook by its key.

        ** This method is not thread-safe and should only be called by the get_hook method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Args:
            key: The key of the hook to get

        Returns:
            The hook associated with the key
        """

        if key in self._input_hooks:
            return self._input_hooks[key] # type: ignore
        elif key in self._output_hooks:
            return self._output_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_value_by_key(self, key: IHK|OHK) -> IHV|OHV:
        """
        Get a value as a copy by its key.

        ** This method is not thread-safe and should only be called by the get_value_of_hook method.

        ** Must be implemented by subclasses to provide efficient lookup for values.

        Args:
            key: The key of the hook to get the value of
        """

        if key in self._input_hooks:
            return self._input_hooks[key].value # type: ignore
        elif key in self._output_hooks:
            return self._output_hooks[key].value # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_hook_keys(self) -> set[IHK|OHK]:
        """
        Get all keys of the hooks.

        ** This method is not thread-safe and should only be called by the get_hook_keys method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Returns:
            The set of keys for the hooks
        """

        return set(self._input_hooks.keys()) | set(self._output_hooks.keys())

    def _get_key_by_hook_or_nexus(self, hook_or_nexus: Hook[IHV]|ReadOnlyHook[OHV]|Nexus[IHV|OHV]) -> IHK|OHK: # type: ignore
        """
        Get the key for a hook or nexus.

        ** This method is not thread-safe and should only be called by the get_hook_key method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Args:
            hook_or_nexus: The hook or nexus to get the key for

        Returns:
            The key for the hook or nexus
        """

        for key, hook in self._input_hooks.items():
            if hook is hook_or_nexus:
                return key
        for key, hook in self._output_hooks.items():
            if hook is hook_or_nexus:
                return key
        raise ValueError(f"Hook {hook_or_nexus} not found in hooks")


    #########################################################################
    # Public API
    #########################################################################

    #-------------------------------- Hooks, values, and keys --------------------------------

    def hook(self, key: IHK|OHK) -> Hook[IHV|OHV]:
        """
        Get a hook by its key.

        ** Thread-safe **

        Returns:
            The hook associated with the key.
        """
        with self._lock:
            return self._get_hook_by_key(key)

    def keys(self) -> set[IHK|OHK]:
        """
        Get all hook keys.

        ** Thread-safe **

        Returns:
            The set of all hook keys.
        """
        with self._lock:
            return set(self._get_hook_keys())

    def key(self, hook: Hook[IHV]|ReadOnlyHook[OHV]) -> IHK|OHK:
        """
        Get a key by its hook.

        ** Thread-safe **

        Returns:
            The key associated with the hook.
        """
        with self._lock:
            return self._get_key_by_hook_or_nexus(hook)

    def hooks(self) -> dict[IHK|OHK, Hook[IHV|OHV]]:
        """
        Get all hooks.

        ** Thread-safe **

        Returns:
            The dictionary of hooks.
        """
        with self._lock:
            return self._get_dict_of_hooks() # type: ignore

    def value(self, key: IHK|OHK) -> IHV|OHV:
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
    def function_callable(self) -> Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]]:
        """Get the function callable."""
        return self._one_way_function_callable

    def input_variable_keys(self) -> set[IHK]:
        """Get the input variable keys."""
        with self._lock:
            return set(self._input_hooks.keys())

    def change_values(self, values: Mapping[IHK|OHK, IHV|OHV]) -> None:
        """
        Change the values of the observable.
        """
        success, msg = self._submit_values(values)
        if not success:
            raise SubmissionError(msg, values)
