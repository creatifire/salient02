"""
Retry logic with exponential backoff for LLM and API calls.
"""

from functools import wraps
import time
import logging
from typing import Callable, Any
from ..errors.exceptions import LLMRetryExhausted

logger = logging.getLogger(__name__)


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> Callable:
    """
    Decorator for exponential backoff retry logic.
    
    Retries failed function calls with exponentially increasing delays.
    Useful for transient API errors, rate limiting, network issues.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential growth (default: 2.0)
        
    Returns:
        Decorated function with retry logic
        
    Raises:
        LLMRetryExhausted: If all retry attempts fail
        
    Example:
        @exponential_backoff(max_retries=3, base_delay=1.0)
        def api_call():
            return requests.get('https://api.example.com')
            
        # Will retry up to 3 times with delays: 1s, 2s, 4s
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Final attempt failed - raise LLMRetryExhausted
                        error_msg = f"Failed after {max_retries + 1} attempts: {str(e)}"
                        logger.error(
                            f"Retry exhausted for {func.__name__}: {error_msg}"
                        )
                        raise LLMRetryExhausted(error_msg) from e
                    
                    # Calculate exponential delay with cap
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_retries + 1} for {func.__name__}: "
                        f"{type(e).__name__}: {str(e)} | Retrying in {delay:.2f}s"
                    )
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def calculate_delay(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> float:
    """
    Calculate exponential backoff delay for a given attempt.
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        exponential_base: Base for exponential growth
        
    Returns:
        Delay in seconds (capped at max_delay)
        
    Example:
        >>> calculate_delay(0, base_delay=1.0)  # First retry
        1.0
        >>> calculate_delay(1, base_delay=1.0)  # Second retry
        2.0
        >>> calculate_delay(2, base_delay=1.0)  # Third retry
        4.0
    """
    delay = base_delay * (exponential_base ** attempt)
    return min(delay, max_delay)


def should_retry(exception: Exception, retryable_exceptions: tuple = None) -> bool:
    """
    Determine if an exception should trigger a retry.
    
    Args:
        exception: The exception that occurred
        retryable_exceptions: Tuple of exception types to retry
                            (default: all exceptions are retryable)
        
    Returns:
        True if should retry, False otherwise
        
    Example:
        >>> should_retry(ConnectionError(), (ConnectionError, TimeoutError))
        True
        >>> should_retry(ValueError(), (ConnectionError, TimeoutError))
        False
    """
    if retryable_exceptions is None:
        return True
    
    return isinstance(exception, retryable_exceptions)
