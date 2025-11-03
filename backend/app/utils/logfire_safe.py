"""
Safe Logfire wrappers that sanitize SQLAlchemy expressions before serialization.

This module provides defensive wrappers around Logfire calls to prevent
"Boolean value of this clause is not defined" errors when SQLAlchemy expressions
are accidentally passed as log attributes.

This is a safety net - the root cause should be fixed at the data access layer
(see session_extractor.py), but this provides defense-in-depth for error paths.
"""

from typing import Any, Dict
import logfire


def _is_sqlalchemy_expression(value: Any) -> bool:
    """Detect SQLAlchemy expressions without triggering evaluation.
    
    CRITICAL: All checks must be safe and never trigger boolean evaluation.
    Calling bool() or checking truthiness on SQLAlchemy expressions triggers the error.
    
    Args:
        value: Value to check
        
    Returns:
        True if value appears to be a SQLAlchemy expression
    """
    if value is None:
        return False
    
    # CRITICAL: Only use safe attribute checks - never call bool(), str(), or repr()
    # on the value itself, as this triggers SQLAlchemy boolean evaluation
    
    # Check module path first (safest check)
    try:
        # type() is safe - doesn't trigger evaluation
        value_type = type(value)
        type_module = getattr(value_type, '__module__', None)
        
        if type_module and 'sqlalchemy' in str(type_module).lower():
            # Additional checks for expression-like objects using hasattr (safe)
            # These attribute checks are safe - don't trigger boolean evaluation
            if hasattr(value, '__clause_element__') or hasattr(value, 'key'):
                return True
    except Exception:
        # If ANY check fails, assume it's not SQLAlchemy to avoid triggering errors
        # Better to pass through and let Logfire handle it than risk evaluation
        pass
    
    return False


def _sanitize_value(value: Any) -> Any:
    """Convert SQLAlchemy expressions to safe representation.
    
    CRITICAL: This function must NEVER trigger SQLAlchemy boolean evaluation.
    We catch all exceptions during detection to prevent errors.
    
    Args:
        value: Value to sanitize
        
    Returns:
        Safe representation - original value if not SQLAlchemy expression,
        otherwise a placeholder string
    """
    # Wrap detection in try/except to prevent any evaluation errors
    try:
        if _is_sqlalchemy_expression(value):
            # Return placeholder instead of attempting serialization
            # This prevents "Boolean value of this clause is not defined" errors
            return "<sqlalchemy_expression>"
    except Exception:
        # If detection itself fails (might trigger evaluation), treat as SQLAlchemy expression
        # Better to return placeholder than risk error during serialization
        return "<sqlalchemy_expression>"
    
    return value


def _sanitize_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize all values in kwargs dictionary.
    
    Args:
        kwargs: Dictionary of log attributes
        
    Returns:
        Dictionary with SQLAlchemy expressions sanitized
    """
    return {k: _sanitize_value(v) for k, v in kwargs.items()}


def safe_logfire_info(event_name: str, **kwargs):
    """Safe wrapper for logfire.info() that sanitizes SQLAlchemy expressions.
    
    Use this for critical logging paths where SQLAlchemy expressions might
    accidentally be passed (e.g., error handlers, exception logging).
    
    Args:
        event_name: Log event name
        **kwargs: Log attributes (will be sanitized)
    """
    safe_kwargs = _sanitize_kwargs(kwargs)
    logfire.info(event_name, **safe_kwargs)


def safe_logfire_error(event_name: str, **kwargs):
    """Safe wrapper for logfire.error() that sanitizes SQLAlchemy expressions.
    
    Use this for error logging paths where SQLAlchemy expressions might
    accidentally be passed.
    
    Args:
        event_name: Log event name
        **kwargs: Log attributes (will be sanitized)
    """
    safe_kwargs = _sanitize_kwargs(kwargs)
    logfire.error(event_name, **safe_kwargs)


def safe_logfire_warn(event_name: str, **kwargs):
    """Safe wrapper for logfire.warn() that sanitizes SQLAlchemy expressions.
    
    Args:
        event_name: Log event name
        **kwargs: Log attributes (will be sanitized)
    """
    safe_kwargs = _sanitize_kwargs(kwargs)
    logfire.warn(event_name, **safe_kwargs)


def safe_logfire_exception(event_name: str, **kwargs):
    """Safe wrapper for logfire.exception() that sanitizes SQLAlchemy expressions.
    
    Args:
        event_name: Log event name
        **kwargs: Log attributes (will be sanitized)
    """
    safe_kwargs = _sanitize_kwargs(kwargs)
    logfire.exception(event_name, **safe_kwargs)

