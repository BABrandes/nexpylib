from typing import Any, Optional
import types


class SubmissionError(ValueError):
    """Exception raised when a value cannot be accepted for submission.
    
    This exception automatically hides the frame where it is raised from
    the traceback to provide cleaner error messages.
    """
    
    # Hide the module path in traceback by using 'builtins' as the module
    # This makes the exception appear like a built-in exception (e.g., ValueError)
    __module__ = "builtins"
    
    def __init__(self, message: str, value: Any, key: Optional[str] = None):
        """
        Args:
            message: The message to display
            value: The value that caused the error
            key: The key that caused the error
        """

        self.value = value
        self.key = key
        
        if key is not None:
            full_message = f"Cannot accept value {value} for submission to key {key}: {message}"
        else:
            full_message = f"Cannot accept value {value} for submission: {message}"
        
        super().__init__(full_message)
    
    def __getattribute__(self, name: str) -> Any:
        """Intercept __traceback__ access to return a trimmed version."""
        if name == '__traceback__':
            # Get the actual traceback from the base class
            tb = super().__getattribute__('__traceback__')
            # Return a trimmed version
            return self._trim_traceback(tb)
        else:
            return super().__getattribute__(name)
    
    @staticmethod
    def _trim_traceback(tb: types.TracebackType) -> Optional[types.TracebackType]:
        """Trim the last frame from a traceback."""
        if tb is None: # type: ignore
            return None
            
        # Collect all frames
        frames: list[types.TracebackType] = []
        current = tb
        while current is not None:
            frames.append(current)
            current = current.tb_next
        
        # If there's only one frame, keep it
        if len(frames) <= 1:
            return tb
        
        # Create a new traceback chain excluding the last frame
        new_tb = None
        last_tb = None
        
        for i in range(len(frames) - 1):  # Exclude the last frame
            frame_obj = frames[i]
            next_tb = types.TracebackType(
                None,  # tb_next will be set later
                frame_obj.tb_frame,
                frame_obj.tb_lasti,
                frame_obj.tb_lineno
            )
            
            if new_tb is None:
                new_tb = next_tb
            else:
                # Link the previous traceback to this one
                object.__setattr__(last_tb, 'tb_next', next_tb)
            
            last_tb = next_tb
        
        return new_tb if new_tb is not None else tb
