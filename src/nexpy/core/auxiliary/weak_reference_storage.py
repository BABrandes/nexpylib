from typing import Generic, Iterable, TypeVar
import weakref
import time

T = TypeVar("T")

class WeakReferenceStorage(Generic[T]):
    """
    Generic storage for weak references with automatic cleanup.
    
    This class provides a reusable container for managing weak references to objects
    of type T. It automatically cleans up dead references based on time and size
    thresholds, preventing memory leaks from accumulating garbage collected objects.
    
    Type Parameters:
        T: The type of objects being stored as weak references. Can be any class
           that supports weak referencing (most Python objects except some built-ins).
    
    Attributes:
        _references: Set of weak references to objects of type T.
        _cleanup_interval: Time threshold (seconds) for triggering cleanup.
        _max_references_before_cleanup: Size threshold for triggering cleanup.
        _last_cleanup_time: Timestamp of the last cleanup operation.
    
    Example:
        Basic usage::
        
            from observables._utils.weak_reference_storage import WeakReferenceStorage
            
            # Create storage for any object type
            storage = WeakReferenceStorage[MyClass](
                cleanup_interval=30.0,
                max_references_before_cleanup=50
            )
            
            # Add objects
            obj = MyClass()
            storage.add_reference(weakref.ref(obj))
            
            # Access references
            for ref in storage.weak_references:
                obj = ref()
                if obj is not None:
                    process(obj)
            
            # Automatic cleanup when thresholds met
            storage.cleanup()
    """

    def __init__(
        self,
        cleanup_interval: float = 60.0,  # seconds
        max_references_before_cleanup: int = 1000
        ) -> None:
        """
        Initialize a new WeakReferenceStorage.
        
        Args:
            cleanup_interval: Time in seconds between automatic cleanup operations.
                When this much time has passed since the last cleanup, dead references
                will be removed on the next cleanup() call. Default is 60 seconds.
            max_references_before_cleanup: Maximum number of references to store
                before triggering automatic cleanup. When this threshold is reached,
                dead references are immediately removed. Default is 1000 references.
        
        Example:
            Create storage with custom thresholds::
            
                # Aggressive cleanup (every 10 seconds or 50 references)
                fast_storage = WeakReferenceStorage[MyClass](
                    cleanup_interval=10.0,
                    max_references_before_cleanup=50
                )
                
                # Relaxed cleanup (every 5 minutes or 10000 references)
                lazy_storage = WeakReferenceStorage[MyClass](
                    cleanup_interval=300.0,
                    max_references_before_cleanup=10000
                )
        """
        self._references: set[weakref.ref[T]] = set()
        self._cleanup_interval = cleanup_interval
        self._max_references_before_cleanup = max_references_before_cleanup
        self._last_cleanup_time = time.time()

    def add_reference(self, reference: weakref.ref[T]) -> None:
        self.cleanup()
        self._references.add(reference)

    def remove_reference(self, reference: weakref.ref[T]) -> None:
        self.cleanup()
        self._references.remove(reference)

    @property
    def weak_references(self) -> Iterable[weakref.ref[T]]:
        for reference in self._references:
            yield reference

    @property
    def references(self) -> Iterable[T | None]:
        for reference in self._references:
            yield reference()

    def cleanup(self) -> None:
        """
        Check if a cleanup is needed based on time or size thresholds.
        """
        time_threshold_reached = (time.time() - self._last_cleanup_time) >= self._cleanup_interval
        size_threshold_reached = len(self._references) >= self._max_references_before_cleanup
        
        if time_threshold_reached or size_threshold_reached:
            self.remove_dead_references()

    def remove_dead_references(self) -> None:
        """
        Remove all dead references and update the last cleanup time.
        """
        dead_references: set[weakref.ref[T]] = set()
        for reference in self._references:
            referenced_value = reference()
            if referenced_value is None:
                dead_references.add(reference)
        self._references -= dead_references
        self._last_cleanup_time = time.time()