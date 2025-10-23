from typing import Any, Optional, Callable
import weakref
from logging import Logger

def make_weak_callback(callback: Optional[Callable[..., Any]]) -> Optional[Callable[..., Any]]:
    """
    Convert callback to weak reference if it's a bound method.
    
    Args:
        callback: The callback to convert (can be None, a function, or a bound method)
        
    Returns:
        None if callback is None
        A wrapper using WeakMethod if callback is a bound method
        The original callback if it's a regular function
    """
    if callback is None:
        return None
    
    if hasattr(callback, '__self__'):
        # It's a bound method - use WeakMethod to avoid circular references
        weak_ref = weakref.WeakMethod(callback)
        
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            method = weak_ref()
            if method is None:
                raise RuntimeError("Callback object was garbage collected")
            return method(*args, **kwargs)
        
        return wrapper
    else:
        # It's a regular function - safe to store directly
        return callback

def log(subject: Any, action: str, logger: Optional[Logger], success: bool, message: Optional[str] = None) -> None:
    if logger is None:
        return

    if not success:
        if message is None:
            message = "No message provided"
        logger.debug(f"{subject}: Action {action} returned False: {message}")
    else:
        if message is None:
            logger.debug(f"{subject}: Action {action} returned True")
        else:
            logger.debug(f"{subject}: Action {action} returned True: {message}")