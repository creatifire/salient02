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
    
    Args:
        value: Value to check
        
    Returns:
        True if value appears to be a SQLAlchemy expression
    """
    if value is None:
        return False
    
    # Check module path - SQLAlchemy expressions come from sqlalchemy modules
    try:
        type_module = type(value).__module__
        if type_module and 'sqlalchemy' in type_module.lower():
            # Additional checks for expression-like objects
            # These attribute checks are safe - don't trigger boolean evaluation
            if hasattr(value, '__clause_element__') or hasattr(value, 'key'):
                return True
    except Exception:
        # If we can't check safely, assume it's not SQLAlchemy
        pass
    
    return False


def _sanitize_value(value: Any) -> Any:
    """Convert SQLAlchemy expressions to safe representation.
    
    Args:
        value: Value to sanitize
        
    Returns:
        Safe representation - original value if not SQLAlchemy expression,
        otherwise a placeholder string
    """
    if _is_sqlalchemy_expression(value):
        # Return placeholder instead of attempting serialization
        # This prevents "Boolean value of this clause is not defined" errors
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

