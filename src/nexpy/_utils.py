from typing import Any, Optional
from logging import Logger


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