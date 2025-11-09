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
    """
    Reactive function coordinator maintaining synchronized variables through custom logic.
    
    XFunction[SHK, SHV] maintains a set of variables (hooks) that are synchronized according to
    a user-defined function. When any variable changes, the function is called to compute
    derived updates to other variables. Generic types SHK and SHV specify the key and value types.

    Type Parameters
    ---------------
    SHK : TypeVar
        The type of hook keys (variable identifiers).
        Examples: str, int, Literal["x", "y", "z"]
    SHV : TypeVar
        The type of hook values (variable values).
        Examples: int, float, str, Any

    Key Features
    ------------
    - **Custom Logic**: User-defined function determines synchronization behavior
    - **Reactive**: Automatic recomputation when any variable changes
    - **Bidirectional**: Function can update multiple variables from any change
    - **Type-Safe**: Full generic type support for keys and values

    See Also
    --------
    XOneWayFunction : One-way function (inputs → output only)
    XValue : For simple single values
    """

    def __init__(
        self,
        complete_variables_per_key: Mapping[SHK, HookProtocol[SHV]|SHV],
        completing_function_callable: Callable[[FunctionValues[SHK, SHV]], tuple[bool, dict[SHK, SHV]]],
        *,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ) -> None:
        """
        Initialize a reactive function coordinator.

        The generic types SHK (key type) and SHV (value type) define the variables.
        Use: XFunction[str, float], XFunction[Literal["x", "y"], int], etc.

        Parameters
        ----------
        complete_variables_per_key : Mapping[SHK, Hook[SHV] | SHV]
            Initial variables as key-value pairs:
            - SHK: Variable identifier (key)
            - Hook[SHV] | SHV: Initial value or hook to connect to

        completing_function_callable : Callable[[FunctionValues[SHK, SHV]], tuple[bool, dict[SHK, SHV]]]
            Function that computes synchronized values:
            - Input: FunctionValues with .submitted and .current dictionaries
            - Output: (success: bool, updates: dict[SHK, SHV])
            - Called when any variable changes
            - Must return consistent values for validation

        logger : Logger, optional
            Logger for debugging operations.

        nexus_manager : NexusManager, optional
            The NexusManager coordinating synchronization.

        Examples
        --------
        Rectangle with synchronized width, height, area:

        >>> def rect_sync(values):
        ...     submitted = values.submitted
        ...     current = values.current
        ...     
        ...     if "width" in submitted and "height" in submitted:
        ...         return True, {"area": submitted["width"] * submitted["height"]}
        ...     elif "width" in submitted:
        ...         return True, {"area": submitted["width"] * current["height"]}
        ...     elif "height" in submitted:
        ...         return True, {"area": current["width"] * submitted["height"]}
        ...     elif "area" in submitted:
        ...         # Calculate width from area and current height
        ...         return True, {"width": submitted["area"] / current["height"]}
        ...     return True, {}
        >>> 
        >>> rect = XFunction[str, float](
        ...     complete_variables_per_key={"width": 10.0, "height": 5.0, "area": 50.0},
        ...     completing_function_callable=rect_sync
        ... )
        >>> rect.get_hook("width").value = 20.0
        >>> rect.get_hook("area").value  # Automatically updated to 100.0
        100.0

        Temperature converter:

        >>> def temp_sync(values):
        ...     if "celsius" in values.submitted:
        ...         c = values.submitted["celsius"]
        ...         return True, {"fahrenheit": c * 9/5 + 32}
        ...     elif "fahrenheit" in values.submitted:
        ...         f = values.submitted["fahrenheit"]
        ...         return True, {"celsius": (f - 32) * 5/9}
        ...     return True, {}
        >>> 
        >>> temp = XFunction[str, float](
        ...     complete_variables_per_key={"celsius": 0.0, "fahrenheit": 32.0},
        ...     completing_function_callable=temp_sync
        ... )
        """


        self._completing_function_callable = completing_function_callable

        #################################################################################################
        # Create function hooks
        #################################################################################################

        self._function_hooks: dict[SHK, OwnedWritableHook[SHV, Self]] = {}
        for key, initial_value in complete_variables_per_key.items():
            function_hook: OwnedWritableHook[SHV, Self] = OwnedWritableHook[SHV, Self](
                owner=self,
                value=initial_value.value if isinstance(initial_value, HookProtocol) else initial_value, # type: ignore
                logger=logger,
                nexus_manager=nexus_manager
            )
            self._function_hooks[key] = function_hook

        #################################################################################################
        # Initialize XBase
        #################################################################################################

        #-------------------------------- Add values to be updated callback --------------------------------

        def add_values_to_be_updated_callback(update_values: UpdateFunctionValues[SHK, SHV]) -> Mapping[SHK, SHV]:
            """
            Add values to be updated by triggering the function.
            This callback is called when any hook value changes.
            
            The function_callable receives a FunctionValues object containing both 
            submitted (what changed) and current (complete current state) values.
            """

            values_to_be_added: dict[SHK, SHV] = {}
               
            # Create FunctionValues object and call the function
            function_values = FunctionValues(submitted=update_values.submitted, current=update_values.current)
            success, synced_values = self._completing_function_callable(function_values)

            if not success:
                raise ValueError(f"Function callable returned invalid values for combination {update_values.submitted}")

            # Build completed_values by merging: submitted_values, then synced_values, then current values
            completed_values: dict[SHK, SHV] = {}
            for key in self._function_hooks.keys():
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
                success, _ = self._completing_function_callable(completed_function_values)
                if not success:
                    raise ValueError(f"Function callable returned invalid values for final state {completed_values}")
            except Exception as e:
                raise ValueError(f"Function callable validation failed: {e}")

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
        # Connect internal hooks to external hooks
        #################################################################################################

        # Connect internal hooks to external hooks if provided
        for key, external_hook_or_value in complete_variables_per_key.items():
            self._function_hooks[key].join(external_hook_or_value, "use_caller_value") if isinstance(external_hook_or_value, HookProtocol) else None # type: ignore

        #################################################################################################

    #########################################################
    # SerializableProtocol implementation
    #########################################################

    def get_values_for_serialization(self) -> Mapping[SHK, SHV]:
        return {key: hook._get_value() for key, hook in self._function_hooks.items()} # type: ignore
    
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
        if key in self._function_hooks:
            return self._function_hooks[key]
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_value_by_key(self, key: SHK) -> SHV:
        """
        Get a value by its key.

        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The value of the hook.
        """

        if key in self._function_hooks:
            return self._function_hooks[key]._get_value() # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_hook_keys(self) -> set[SHK]:
        """
        Get all hook keys.

        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The set of all hook keys.
        """
        return set(self._function_hooks.keys())

    def _get_key_by_hook_or_nexus(self, hook_or_nexus: HookProtocol[SHV]|Nexus[SHV]) -> SHK:
        """
        Get a key by its hook or nexus.

        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The key associated with the hook or nexus.
        """
        for key, hook in self._function_hooks.items():
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