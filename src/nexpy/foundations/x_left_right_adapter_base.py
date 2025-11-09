from typing import Generic, Literal, Mapping, Optional, TypeVar
from logging import Logger
from abc import abstractmethod

from ..core.nexus_system.update_function_values import UpdateFunctionValues
from ..core.nexus_system.nexus_manager import NexusManager
from ..core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from .x_composite_base import XCompositeBase

# Type variables for the two types being transferred
T1 = TypeVar("T1")  # First type (e.g., T, float, AbstractSet)
T2 = TypeVar("T2")  # Second type (e.g., Optional[T], int, Sequence)

class XLeftRightAdapterBase(
    XCompositeBase[Literal["left", "right"], Literal[...], T1 | T2, None], 
    Generic[T1, T2]
):
    """
    Base class for left-right adapter X objects that bridge between incompatible types.

    Generic type parameters:
        T1: The left-side type
        T2: The right-side type

    Adapter objects maintain two synchronized hooks with different but related types,
    allowing connections between hooks that wouldn't normally be type-compatible.
    They validate and potentially transform values during adaptation to ensure consistency.
    
    This class serves as the foundation for specific adapter implementations like:
    - XOptionalAdapter: T ↔ Optional[T] (blocks None values)
    - XFloatIntAdapter: float ↔ int (validates integer values)
    - XSetSequenceAdapter: AbstractSet ↔ Sequence (validates uniqueness)
    
    Architecture:
    - Two primary hooks: "left" and "right" with types T1 and T2
    - Bidirectional synchronization with validation
    - Subclasses define conversion and validation logic
    
    Type Parameters:
        T1: The left-side type
        T2: The right-side type
        
    Notes:
        Subclasses must implement:
        - _convert_left_to_right: Convert T1 → T2
        - _convert_right_to_left: Convert T2 → T1
        - _validate_left: Validate T1 value
        - _validate_right: Validate T2 value
    """
    
    def __init__(
        self,
        initial_hook_values: Mapping[Literal["left", "right"], T1 | T2],
        *,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER,
        preferred_publish_mode: Literal["async", "sync", "direct", "off"] = "async",
    ) -> None:
        """
        Initialize the adapter base.
        
        Args:
            initial_hook_values: Initial values or hooks for left and right sides
            logger: Optional logger for debugging
            nexus_manager: Nexus manager for coordination
        """

        #################################################################################################
        # Initialize XCompositeBase
        #################################################################################################

        # -------------------------------- Prepare callbacks --------------------------------

        def _compute_missing_primary_values_callback(
            update_values: UpdateFunctionValues[Literal["left", "right"], T1 | T2]
        ) -> Mapping[Literal["left", "right"], T1 | T2]:
            """
            Compute missing value by converting the submitted value.
            """
            submitted = update_values.submitted
            
            if "left" in submitted and "right" not in submitted:
                # Left changed, convert to right
                left_value = submitted["left"]
                right_value = self._convert_left_to_right(left_value)  # type: ignore
                return {"right": right_value}
                
            elif "right" in submitted and "left" not in submitted:
                # Right changed, convert to left
                right_value = submitted["right"]
                left_value = self._convert_right_to_left(right_value)  # type: ignore
                return {"left": left_value}
                
            else:
                # Both submitted or neither submitted
                return {}
        
        def _validate_complete_primary_values_callback(
            values: Mapping[Literal["left", "right"], T1 | T2]
        ) -> tuple[bool, str]:
            """
            Validate both values are present and consistent.
            """
            if "left" not in values or "right" not in values:
                return False, "Both left and right values must be present"
            
            left_value = values["left"]
            right_value = values["right"]
            
            # Validate individual values
            left_valid, left_msg = self._validate_left(left_value)  # type: ignore
            if not left_valid:
                return False, f"Left validation failed: {left_msg}"
            
            right_valid, right_msg = self._validate_right(right_value)  # type: ignore
            if not right_valid:
                return False, f"Right validation failed: {right_msg}"
            
            # Validate consistency between values
            consistent, consistency_msg = self._validate_consistency(left_value, right_value)  # type: ignore
            if not consistent:
                return False, f"Consistency check failed: {consistency_msg}"
            
            return True, "Values are valid and consistent"
        
        # --------------------- Initialize XCompositeBase --------------------------------

        super().__init__(
            initial_hook_values=initial_hook_values,
            compute_missing_primary_values_callback=_compute_missing_primary_values_callback,
            compute_secondary_values_callback=None,
            validate_complete_primary_values_callback=_validate_complete_primary_values_callback,
            invalidate_after_update_callback=None,
            custom_validator=None,
            logger=logger,
            nexus_manager=nexus_manager,
            preferred_publish_mode=preferred_publish_mode
        )

        #################################################################################################
    
    #########################################################################
    # Abstract methods for subclasses to implement
    #########################################################################
    
    @abstractmethod
    def _convert_left_to_right(self, left_value: T1) -> T2:
        """
        Convert a left-side value to right-side type.
        
        Args:
            left_value: Value of type T1
            
        Returns:
            Converted value of type T2
        """
        ...
    
    @abstractmethod
    def _convert_right_to_left(self, right_value: T2) -> T1:
        """
        Convert a right-side value to left-side type.
        
        Args:
            right_value: Value of type T2
            
        Returns:
            Converted value of type T1
        """
        ...
    
    @abstractmethod
    def _validate_left(self, left_value: T1) -> tuple[bool, str]:
        """
        Validate a left-side value.
        
        Args:
            left_value: Value to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        ...
    
    @abstractmethod
    def _validate_right(self, right_value: T2) -> tuple[bool, str]:
        """
        Validate a right-side value.
        
        Args:
            right_value: Value to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        ...
    
    def _validate_consistency(self, left_value: T1, right_value: T2) -> tuple[bool, str]:
        """
        Validate consistency between left and right values.
        
        Default implementation converts left to right and compares.
        Subclasses can override for custom consistency checks.
        
        Args:
            left_value: Left-side value
            right_value: Right-side value
            
        Returns:
            Tuple of (is_consistent, message)
        """
        try:
            converted_right = self._convert_left_to_right(left_value)
            if self._nexus_manager.is_not_equal(converted_right, right_value):
                return False, f"Values are inconsistent: {left_value} != {right_value}"
            return True, "Values are consistent"
        except Exception as e:
            return False, f"Consistency check error: {e}"

