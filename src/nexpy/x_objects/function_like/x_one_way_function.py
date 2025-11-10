from typing import Callable, Generic, Mapping, Optional, TypeVar, Self
from logging import Logger

from nexpy.core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook
from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from nexpy.core.hooks.protocols.hook_protocol import HookProtocol
from ...foundations.x_base import XBase
from ...core.nexus_system.nexus import Nexus
from ...core.nexus_system.update_function_values import UpdateFunctionValues
from ...core.nexus_system.submission_error import SubmissionError
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore

# Type variables for input and output hook names and values
IHK = TypeVar("IHK")  # Input Hook Keys
OHK = TypeVar("OHK")  # Output Hook Keys
IHV = TypeVar("IHV")  # Input Hook Values
OHV = TypeVar("OHV")  # Output Hook Values


class XOneWayFunction(XBase[IHK|OHK, IHV|OHV], Generic[IHK, OHK, IHV, OHV]):
    """
    Reactive one-way function computing outputs from inputs.

    XOneWayFunction[IHK, OHK, IHV, OHV] maintains input variables and computes output
    variables using a pure function. When inputs change, outputs are automatically
    recomputed. Outputs are read-only. Four generic types specify the structure.

    Type Parameters
    ---------------
    IHK : TypeVar
        Type of input hook keys (input variable identifiers).
    OHK : TypeVar
        Type of output hook keys (output variable identifiers).
    IHV : TypeVar
        Type of input hook values (input data types).
    OHV : TypeVar
        Type of output hook values (output data types).

    Key Features
    ------------
    - **One-Way**: Inputs → Outputs (outputs cannot be modified directly)
    - **Pure Function**: Outputs computed from inputs only
    - **Reactive**: Automatic recomputation when inputs change
    - **Read-Only Outputs**: Output hooks cannot be written to
    - **Type-Safe**: Full generic type support for keys and values

    See Also
    --------
    XFunction : Bidirectional function with arbitrary synchronization logic
    XValue : For simple single values
    """

    def __init__(
        self,
        input_variables_per_key: Mapping[IHK, HookProtocol[IHV]|IHV],
        one_way_function_callable: Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]],
        function_output_hook_keys: set[OHK],
        *,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ) -> None:
        """
        Initialize a one-way reactive function.

        The four generic types define the structure:
        - IHK, IHV: Input key and value types
        - OHK, OHV: Output key and value types
        Use: XOneWayFunction[str, str, float, float], etc.

        Parameters
        ----------
        input_variables_per_key : Mapping[IHK, Hook[IHV] | IHV]
            Input variables as key-value pairs.
            These are writable and trigger function recomputation.

        one_way_function_callable : Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]]
            Pure function computing outputs from inputs:
            - Input: Current input values as Mapping[IHK, IHV]
            - Output: Computed output values as Mapping[OHK, OHV]
            - Must return all output keys specified
            - Called when any input changes

        function_output_hook_keys : set[OHK]
            Set of output variable keys the function produces.
            All keys must be present in function's return value.

        logger : Logger, optional
            Logger for debugging operations.

        nexus_manager : NexusManager, optional
            The NexusManager coordinating synchronization.

        Examples
        --------
        Simple arithmetic (x, y → sum, product):

        >>> def compute(inputs):
        ...     x = inputs["x"]
        ...     y = inputs["y"]
        ...     return {"sum": x + y, "product": x * y}
        >>> 
        >>> calc = XOneWayFunction[str, str, float, float](
        ...     input_variables_per_key={"x": 3.0, "y": 4.0},
        ...     one_way_function_callable=compute,
        ...     function_output_hook_keys={"sum", "product"}
        ... )
        >>> calc.get_input_hook("x").value = 10.0
        >>> calc.get_output_hook("sum").value  # Automatically updated
        14.0
        >>> calc.get_output_hook("product").value
        40.0

        Statistics (values → mean, std):

        >>> import statistics
        >>> def stats(inputs):
        ...     values = inputs["values"]
        ...     return {
        ...         "mean": statistics.mean(values),
        ...         "stdev": statistics.stdev(values) if len(values) > 1 else 0.0
        ...     }
        >>> 
        >>> analyzer = XOneWayFunction[str, str, list[float], float](
        ...     input_variables_per_key={"values": [1.0, 2.0, 3.0, 4.0, 5.0]},
        ...     one_way_function_callable=stats,
        ...     function_output_hook_keys={"mean", "stdev"}
        ... )
        >>> analyzer.get_output_hook("mean").value
        3.0

        Note: Output hooks are read-only:

        >>> calc.get_output_hook("sum").value = 999.0  # Error!
        Traceback (most recent call last):
            ...
        AttributeError: ...
        """

        self._one_way_function_callable: Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]] = one_way_function_callable

        self._input_hooks: dict[IHK, OwnedWritableHook[IHV, Self]] = {}
        self._output_hooks: dict[OHK, OwnedReadOnlyHook[OHV, Self]] = {}

        #################################################################################################
        # Create input hooks
        #################################################################################################

        for key, external_hook_or_value in input_variables_per_key.items():
            # Create internal hook
            initial_value_input: IHV = external_hook_or_value.value if isinstance(external_hook_or_value, HookProtocol) else external_hook_or_value # type: ignore
            internal_hook_input: OwnedWritableHook[IHV, Self] = OwnedWritableHook[IHV, Self](
                owner=self,
                value=initial_value_input,
                logger=logger,
                nexus_manager=nexus_manager
            )
            self._input_hooks[key] = internal_hook_input

        #################################################################################################
        # Create output hooks
        #################################################################################################

        input_values: Mapping[IHK, IHV] = {key: hook.value for key, hook in self._input_hooks.items()}
        output_values: dict[OHK, OHV] = self._one_way_function_callable(input_values) # type: ignore
        for key in function_output_hook_keys:
            if key not in output_values:
                raise ValueError(f"Function callable must return all output keys. Missing key: {key}")
            internal_hook_output: OwnedReadOnlyHook[OHV, Self] = OwnedReadOnlyHook[OHV, Self](
                owner=self,
                value=output_values[key],
                logger=logger,
                nexus_manager=nexus_manager
            )
            self._output_hooks[key] = internal_hook_output

        #################################################################################################
        # Initialize XBase
        #################################################################################################

        #-------------------------------- Add values to be updated callback -----------------------------

        def add_values_to_be_updated_callback(
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

        #-------------------------------- Initialize XBase ---------------------------------------------

        XBase.__init__( # type: ignore
            self,
            logger=logger,
            invalidate_after_update_callback=None,
            validate_complete_values_callback=None,
            compute_missing_values_callback=add_values_to_be_updated_callback
        )

        #################################################################################################
        # Connect internal input hooks to external hooks
        #################################################################################################

        # Connect internal input hooks to external hooks if provided
        for key, external_hook_or_value in input_variables_per_key.items():
            self._input_hooks[key].join(external_hook_or_value, "use_caller_value") if isinstance(external_hook_or_value, HookProtocol) else None # type: ignore

        #################################################################################################

    #########################################################
    # SerializableProtocol implementation
    #########################################################

    def get_values_for_serialization(self) -> Mapping[IHK|OHK, IHV|OHV]:
        return {key: hook._get_value() for key, hook in self._input_hooks.items()} | {key: hook._get_value() for key, hook in self._output_hooks.items()} # type: ignore

    def set_values_from_serialization(self, values: Mapping[IHK|OHK, IHV|OHV]) -> None:
        values_to_submit: dict[IHK|OHK, IHV|OHV] = {}
        for key, value in values.items():
            values_to_submit[key] = value
        self._submit_values(values_to_submit)

    #########################################################################
    # CarriesSomeHooksBase abstract methods
    #########################################################################

    def _get_hook_by_key(self, key: IHK|OHK) -> OwnedWritableHook[IHV|OHV, Self]|OwnedReadOnlyHook[IHV|OHV, Self]:
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

    def _get_key_by_hook_or_nexus(self, hook_or_nexus: OwnedWritableHook[IHV, Self]|OwnedReadOnlyHook[OHV, Self]|Nexus[IHV|OHV]) -> IHK|OHK: # type: ignore
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

    def hook(self, key: IHK|OHK) -> OwnedWritableHook[IHV|OHV, Self]|OwnedReadOnlyHook[IHV|OHV, Self]:
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
            return set[IHK|OHK](self._get_hook_keys())

    def key(self, hook: OwnedWritableHook[IHV|OHV, Self]|OwnedReadOnlyHook[IHV|OHV, Self]) -> IHK|OHK:
        """
        Get a key by its hook.

        ** Thread-safe **

        Returns:
            The key associated with the hook.
        """
        with self._lock:
            return self._get_key_by_hook_or_nexus(hook) # type: ignore

    def hooks(self) -> dict[IHK|OHK, OwnedWritableHook[IHV|OHV, Self]|OwnedReadOnlyHook[IHV|OHV, Self]]:
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
        Change the values of the X object.
        """
        success, msg = self._submit_values(values)
        if not success:
            raise SubmissionError(msg, values)
