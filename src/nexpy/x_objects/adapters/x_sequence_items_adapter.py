from __future__ import annotations

from typing import Generic, Iterable, Literal, Mapping, Optional, Sequence, TypeVar, Self, cast
from logging import Logger

from ...foundations.x_composite_base import XCompositeBase
from ...x_objects.list_like.protocols import XListProtocol
from ...x_objects.single_value_like.protocols import XSingleValueProtocol
from ...core.hooks.protocols.hook_protocol import HookProtocol
from ...core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook
from ...core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from ...core.nexus_system.update_function_values import UpdateFunctionValues
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER  # type: ignore
from ...core.nexus_system.submission_error import SubmissionError

T = TypeVar("T")
PrimaryKey = str
SecondaryKey = Literal["length"]

class XSequenceItemsAdapter(XCompositeBase[PrimaryKey, SecondaryKey, Sequence[T] | T, int], Generic[T]):
    """
    Adapter that synchronizes a fixed-length sequence with per-item hooks.

    This X object maintains:
      - One primary hook for the entire sequence (list or tuple)
      - `n` primary hooks, one for each item (indexes 0..n-1)
      - One secondary hook for the sequence length

    Updating any item hook updates the sequence hook, and updating the sequence
    hook fan-outs to the individual item hooks. The sequence length is fixed and
    determined by the initial sequence.

    Parameters
    ----------
    sequence_or_hook : Sequence[T] | HookProtocol[Sequence[T]] | XListProtocol[T]
        Initial sequence value or external source to join. Accepts direct lists/tuples,
        a hook providing the sequence, or another list-like X object implementing ``XListProtocol``.
        The resulting sequence must have a fixed length.
    item_hooks : Mapping[int, HookProtocol[T] | XSingleValueProtocol[T]]
        | Sequence[Optional[HookProtocol[T] | XSingleValueProtocol[T]]] | None
        Optional external hooks for individual items. A mapping lets you provide hooks for
        specific indices (it may be sparse). A sequence must match the sequence length and
        may contain ``None`` for positions without external hooks. Hooks supplied via
        ``XSingleValueProtocol`` are automatically resolved to their value hooks.
    logger : Optional[Logger], default=None
        Optional logger for debugging and tracing.
    nexus_manager : NexusManager, default=_DEFAULT_NEXUS_MANAGER
        Nexus manager managing synchronization.
    preferred_publish_mode : Literal["async", "sync", "direct", "off"], default="async"
        Preferred publish mode for the underlying X object.

    Raises
    ------
    ValueError
        - If the initial sequence is not a list or tuple
        - If a sequence of item hooks has a length different from the initial sequence
        - If provided item hooks have mismatching initial values
        - If submissions attempt to change the sequence length
    """

    _SEQUENCE_KEY: PrimaryKey = "sequence"
    _LENGTH_KEY: SecondaryKey = "length"
    _ITEM_KEY_TEMPLATE: str = "item_{index}"

    def __init__(
        self,
        sequence_or_hook: Sequence[T] | HookProtocol[Sequence[T]] | XListProtocol[T],
        *,
        item_hooks: Mapping[int, HookProtocol[T] | XSingleValueProtocol[T]]
        | Sequence[Optional[HookProtocol[T] | XSingleValueProtocol[T]]] | None = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER,
        preferred_publish_mode: Literal["async", "sync", "direct", "off"] = "async",
    ) -> None:

        # Store the original item hook specification (for debugging/introspection)
        self._item_hooks_source = item_hooks

        #################################################################################################
        # Collect external hooks
        #################################################################################################

        external_sequence_hook: Optional[HookProtocol[Sequence[T]]]
        initial_sequence_raw: Sequence[T]
        if isinstance(sequence_or_hook, HookProtocol):
            external_sequence_hook = sequence_or_hook
            initial_sequence_raw = sequence_or_hook.value
        elif isinstance(sequence_or_hook, XListProtocol):
            external_sequence_hook = sequence_or_hook.list_hook
            initial_sequence_raw = sequence_or_hook.list
        else:
            external_sequence_hook = None
            initial_sequence_raw = sequence_or_hook

        if not isinstance(initial_sequence_raw, (list, tuple)):
            raise ValueError(
                f"Initial sequence must be a list or tuple, got {type(initial_sequence_raw)}"
            )

        self._sequence_is_tuple = isinstance(initial_sequence_raw, tuple)
        self._expected_length: int = len(initial_sequence_raw)
        self._item_keys = tuple[PrimaryKey, ...](
            self._item_key_for_index(index) for index in range(self._expected_length)
        )

        normalized_initial_sequence = self._normalize_sequence(initial_sequence_raw)

        external_item_hooks: dict[int, HookProtocol[T]] = {}
        if item_hooks is not None:
            if isinstance(item_hooks, Mapping):
                for index, hook_like in item_hooks.items():
                    self._ensure_valid_index(index)
                    resolved_hook = self._resolve_item_hook(hook_like)
                    if nexus_manager.is_not_equal(
                        resolved_hook.value, normalized_initial_sequence[index]
                    ):
                        raise ValueError(
                            f"Initial value mismatch for item {index}: {resolved_hook.value!r} != {normalized_initial_sequence[index]!r}"
                        )
                    external_item_hooks[index] = resolved_hook
            else:
                provided_length = len(item_hooks)
                if provided_length != self._expected_length:
                    raise ValueError(
                        f"Item hooks length mismatch: expected {self._expected_length}, received {provided_length}"
                    )
                for index, hook_like in enumerate[HookProtocol[T] | XSingleValueProtocol[T] | None](item_hooks):
                    if hook_like is None:
                        continue
                    resolved_hook = self._resolve_item_hook(hook_like)
                    if nexus_manager.is_not_equal(
                        resolved_hook.value, normalized_initial_sequence[index]
                    ):
                        raise ValueError(
                            f"Initial value mismatch for item {index}: {resolved_hook.value!r} != {normalized_initial_sequence[index]!r}"
                        )
                    external_item_hooks[index] = resolved_hook

        initial_hook_values: dict[
            PrimaryKey,
            Sequence[T] | T | HookProtocol[Sequence[T]] | HookProtocol[T],
        ] = {}
        initial_hook_values[self._SEQUENCE_KEY] = (
            external_sequence_hook
            if external_sequence_hook is not None
            else normalized_initial_sequence
        )

        for index, key in enumerate(self._item_keys):
            external_hook = external_item_hooks.get(index)
            initial_value: Sequence[T] | T = normalized_initial_sequence[index]
            initial_hook_values[key] = external_hook if external_hook is not None else initial_value

        #################################################################################################
        # Initialize XCompositeBase
        #################################################################################################

        # -------------------------------- Compute missing primary values callback --------------------------------

        def _compute_missing_primary_values_callback(
            update_values: UpdateFunctionValues[PrimaryKey, Sequence[T] | T]
        ) -> Mapping[PrimaryKey, Sequence[T] | T]:
            submitted = update_values.submitted
            additional: dict[PrimaryKey, Sequence[T] | T] = {}

            if self._SEQUENCE_KEY in submitted:
                sequence_value = self._normalize_sequence(
                    cast(Sequence[T], submitted[self._SEQUENCE_KEY])
                )
                additional[self._SEQUENCE_KEY] = sequence_value
                for index, key in enumerate(self._item_keys):
                    additional[key] = sequence_value[index]
                return additional

            updated_indices = [
                index for index, key in enumerate(self._item_keys) if key in submitted
            ]
            if not updated_indices:
                return additional

            base_sequence = cast(Sequence[T], update_values.current[self._SEQUENCE_KEY])
            mutable_values = list(base_sequence)

            for index in updated_indices:
                key = self._item_keys[index]
                mutable_values[index] = cast(T, submitted[key])

            additional[self._SEQUENCE_KEY] = self._build_sequence(mutable_values)
            return additional

        # -------------------------------- Validate complete primary values callback --------------------------------

        def _validate_complete_primary_values_callback(
            values: Mapping[PrimaryKey, Sequence[T] | T]
        ) -> tuple[bool, str]:
            if self._SEQUENCE_KEY not in values:
                return False, "Sequence value must be provided"

            try:
                normalized_sequence_local = self._normalize_sequence(
                    cast(Sequence[T], values[self._SEQUENCE_KEY])
                )
            except ValueError as exc:
                return False, str(exc)

            for index, key in enumerate(self._item_keys):
                if key not in values:
                    return False, f"Missing value for item {index}"
                item_value = values[key]
                if self._get_nexus_manager().is_not_equal(
                    item_value, normalized_sequence_local[index]
                ):
                    mismatch_message = (
                        f"Item {index} value mismatch: {item_value!r} != {normalized_sequence_local[index]!r}"
                    )
                    return False, mismatch_message

            return True, "Values are valid"

        # -------------------------------- Custom validator --------------------------------

        def _custom_validator(
            values: Mapping[PrimaryKey | SecondaryKey, Sequence[T] | T | int]
        ) -> tuple[bool, str]:
            if self._LENGTH_KEY in values:
                submitted_length = cast(int, values[self._LENGTH_KEY])
                if submitted_length != self._expected_length:
                    return False, "Length hook is read-only and cannot change"
            return True, "Values are valid"

        # -------------------------------- Sequence output wrapper --------------------------------

        def _sequence_output_wrapper(
            value: Sequence[T] | T | int,
        ) -> Sequence[T] | T | int:
            if isinstance(value, (list, tuple)):
                return self._build_sequence(cast(Sequence[T], value))
            return value
            
        # -------------------------------- Initialize XCompositeBase --------------------------------

        super().__init__(
            initial_hook_values=cast(
                Mapping[
                    PrimaryKey,
                    Sequence[T] | T | HookProtocol[Sequence[T] | T],
                ],
                initial_hook_values,
            ),
            compute_missing_primary_values_callback=_compute_missing_primary_values_callback,
            compute_secondary_values_callback={
                self._LENGTH_KEY: lambda primary: len(
                    cast(Sequence[T], primary[self._SEQUENCE_KEY])
                )
            },
            validate_complete_primary_values_callback=_validate_complete_primary_values_callback,
            invalidate_after_update_callback=None,
            custom_validator=_custom_validator,
            output_value_wrapper={
                self._SEQUENCE_KEY: _sequence_output_wrapper,
            },
            logger=logger,
            nexus_manager=nexus_manager,
            preferred_publish_mode=preferred_publish_mode,
        )

        #################################################################################################

    #################################################################################################
    # Helper methods
    #################################################################################################

    def _item_key_for_index(self, index: int) -> PrimaryKey:
        return self._ITEM_KEY_TEMPLATE.format(index=index)

    def _ensure_valid_index(self, index: int) -> None:
        if index < 0 or index >= self._expected_length:
            raise ValueError(
                f"Index {index} out of range for sequence of length {self._expected_length}"
            )

    def _normalize_sequence(self, sequence_value: Sequence[T]) -> Sequence[T]:
        if not isinstance(sequence_value, (list, tuple)):
            raise ValueError(
                f"Sequence must remain a list or tuple, got {type(sequence_value)}"
            )
        if len(sequence_value) != self._expected_length:
            raise ValueError(
                f"Sequence length must remain {self._expected_length}, received {len(sequence_value)}"
            )
        return self._build_sequence(sequence_value)

    def _build_sequence(self, values: Iterable[T]) -> Sequence[T]:
        if self._sequence_is_tuple:
            return tuple(values)
        return list(values)

    def _resolve_item_hook(
        self,
        hook_like: HookProtocol[T] | XSingleValueProtocol[T],
    ) -> HookProtocol[T]:
        if isinstance(hook_like, HookProtocol):
            return hook_like
        if isinstance(hook_like, XSingleValueProtocol): # type: ignore[arg-type]
            return hook_like.value_hook
        raise TypeError(f"Unsupported hook type: {type(hook_like)}")

    #################################################################################################
    # Public API - Hooks and values
    #################################################################################################

    # -------------------------------- sequence --------------------------------

    @property
    def sequence(self) -> Sequence[T]:
        return self._value_wrapped(self._SEQUENCE_KEY)  # type: ignore[return-value]

    @sequence.setter
    def sequence(self, value: Sequence[T]) -> None:
        self.change_sequence(value)

    def change_sequence(
        self,
        value: Sequence[T],
        *,
        raise_submission_error_flag: bool = True,
    ) -> tuple[bool, str]:
        success, message = self.submit_value_by_key(
            self._SEQUENCE_KEY, value, raise_submission_error_flag=raise_submission_error_flag
        )
        return success, message

    @property
    def sequence_hook(self) -> OwnedWritableHook[Sequence[T], Self]:
        return self._primary_hooks[self._SEQUENCE_KEY]  # type: ignore[return-value]

    # -------------------------------- item hooks --------------------------------

    def item_hook(self, index: int) -> OwnedWritableHook[T, Self]:
        self._ensure_valid_index(index)
        return self._primary_hooks[self._item_keys[index]]  # type: ignore[return-value]

    def item_value(self, index: int) -> T:
        self._ensure_valid_index(index)
        return self._get_value_by_key(self._item_keys[index])  # type: ignore[return-value]

    def change_item(
        self,
        index: int,
        value: T,
        *,
        raise_submission_error_flag: bool = True,
    ) -> tuple[bool, str]:
        self._ensure_valid_index(index)
        key = self._item_keys[index]
        success, message = self.submit_value_by_key(
            key, value, raise_submission_error_flag=raise_submission_error_flag
        )
        if not success and raise_submission_error_flag:
            raise SubmissionError(message, value, key)
        return success, message

    # -------------------------------- length --------------------------------

    @property
    def length(self) -> int:
        return len(self._value_wrapped(self._SEQUENCE_KEY))  # type: ignore[arg-type]

    @property
    def length_hook(self) -> OwnedReadOnlyHook[int, Self]:
        return self._secondary_hooks[self._LENGTH_KEY]

    #########################################################
    # Public API - other methods
    #########################################################

    @property
    def item_keys(self) -> tuple[PrimaryKey, ...]:
        return self._item_keys


    def __len__(self) -> int:
        return self._expected_length
