"""
Error handling utilities and decorators.
"""

from typing import Callable, Any, Optional
from functools import wraps
import logging
from .exceptions import SiteGenError

# Use standard logging
logger = logging.getLogger(__name__)


def handle_errors(
    reraise: bool = True,
    default_return: Any = None
) -> Callable:
    """
    Decorator for standardized error handling.
    
    Logs all errors using structured logging and optionally reraises them.
    Catches both SiteGenError (custom) and general exceptions.
    
    Args:
        reraise: Whether to reraise exceptions after logging (default: True)
        default_return: Value to return if error caught and not reraised
        
    Returns:
        Decorated function with error handling
        
    Example:
        @handle_errors(reraise=False, default_return=None)
        def risky_operation():
            # If this fails, logs error and returns None
            return do_something()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except SiteGenError as e:
                # Log custom application errors
                logger.error(
                    f"SiteGenError in {func.__name__}: {type(e).__name__}: {str(e)}"
                )
                if reraise:
                    raise
                return default_return
            except Exception as e:
                # Log unexpected errors
                logger.error(
                    f"Unexpected error in {func.__name__}: {type(e).__name__}: {str(e)}"
                )
                if reraise:
                    # Wrap unexpected errors in SiteGenError
                    raise SiteGenError(f"Unexpected error in {func.__name__}: {str(e)}") from e
                return default_return
        
        return wrapper
    return decorator


def format_error_message(
    error: Exception,
    context: Optional[dict] = None
) -> str:
    """
    Format error message with context for clear reporting.
    
    Args:
        error: The exception to format
        context: Optional context dictionary with additional info
        
    Returns:
        Formatted error message string
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Build formatted message
    parts = [f"{error_type}: {error_msg}"]
    
    if context:
        parts.append("\nContext:")
        for key, value in context.items():
            parts.append(f"  {key}: {value}")
    
    return "\n".join(parts)


def log_error(
    error: Exception,
    function_name: str,
    context: Optional[dict] = None
) -> None:
    """
    Log an error with structured context.
    
    Args:
        error: The exception to log
        function_name: Name of the function where error occurred
        context: Optional context dictionary
    """
    error_msg = f"Error in {function_name}: {type(error).__name__}: {str(error)}"
    
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        error_msg += f" | Context: {context_str}"
    
    logger.error(error_msg)


def validate_and_raise(
    condition: bool,
    error_class: type[Exception],
    message: str,
    **context
) -> None:
    """
    Check condition and raise error with context if false.
    
    Args:
        condition: Condition to check
        error_class: Exception class to raise if condition is False
        message: Error message
        **context: Additional context to include in log
        
    Raises:
        error_class: If condition is False
        
    Example:
        validate_and_raise(
            config_file.exists(),
            ConfigError,
            "Config file not found",
            file_path=str(config_file)
        )
    """
    if not condition:
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            logger.error(f"Validation failed: {message} | Context: {context_str}")
        else:
            logger.error(f"Validation failed: {message}")
        raise error_class(message)
