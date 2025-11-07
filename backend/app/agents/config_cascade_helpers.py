"""
Configuration cascade helper functions.

This module provides reusable utilities for configuration cascade patterns,
consolidating path resolution and parameter navigation logic.
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

from pathlib import Path
from typing import Any, Dict, Optional
import logfire


def get_nested_value(source: Any, path: str, default: Any = None) -> Any:
    """
    Navigate through nested structure (dict or object) using dot notation.
    
    Unified navigation function that handles both dictionary navigation
    (e.g., from YAML) and object attribute navigation (e.g., Pydantic models).
    
    Args:
        source: Dictionary or object to navigate
        path: Dot-notation path (e.g., "model_settings.temperature")
        default: Default value to return if path not found
        
    Returns:
        Value at the specified path, or default if not found
        
    Examples:
        # Dictionary navigation
        get_nested_value({"model": {"temp": 0.3}}, "model.temp") → 0.3
        
        # Object navigation
        get_nested_value(agent_config, "model_settings.temperature") → 0.3
        
        # Mixed navigation (object with dict attributes)
        get_nested_value(config_obj, "tools.vector_search.enabled") → True
    """
    try:
        current = source
        path_parts = path.split('.')
        
        for i, key in enumerate(path_parts):
            # Try dictionary access first
            if isinstance(current, dict):
                if key in current:
                    current = current[key]
                else:
                    return default
            # Try object attribute access
            elif hasattr(current, key):
                current = getattr(current, key)
                # If we got a dictionary and there are more path parts, continue with dict navigation
                if isinstance(current, dict) and i < len(path_parts) - 1:
                    remaining_path = '.'.join(path_parts[i + 1:])
                    return get_nested_value(current, remaining_path, default)
            else:
                return default
                
        return current if current is not None else default
        
    except (KeyError, TypeError, AttributeError):
        return default


def resolve_config_path(
    agent_name: str,
    account_slug: Optional[str] = None,
    instance_slug: Optional[str] = None
) -> Path:
    """
    Resolve configuration file path for agent.
    
    Consolidates multi-tenant vs legacy path resolution logic into a single
    function. Returns the appropriate config file path based on parameters.
    
    Args:
        agent_name: Agent type identifier (e.g., "simple_chat")
        account_slug: Optional account identifier for multi-tenant path
        instance_slug: Optional instance identifier for multi-tenant path
        
    Returns:
        Path to the agent configuration file
        
    Examples:
        # Multi-tenant path
        resolve_config_path("simple_chat", "wyckoff", "wyckoff_info_chat1")
        → backend/config/agent_configs/wyckoff/wyckoff_info_chat1/config.yaml
        
        # Legacy path (backward compatible)
        resolve_config_path("simple_chat")
        → backend/config/agent_configs/simple_chat/config.yaml
    """
    from pathlib import Path
    
    # Get base configs directory
    backend_dir = Path(__file__).parent.parent.parent  # Go up to backend/
    configs_dir = backend_dir / "config" / "agent_configs"
    
    # Multi-tenant path: agent_configs/{account_slug}/{instance_slug}/config.yaml
    if account_slug and instance_slug:
        return configs_dir / account_slug / instance_slug / "config.yaml"
    
    # Legacy path: agent_configs/{agent_name}/config.yaml (backward compatibility)
    return configs_dir / agent_name / "config.yaml"


async def cascade_parameters(
    agent_name: str,
    parameter_specs: Dict[str, Dict[str, Any]],
    get_agent_parameter_func,  # Pass function to avoid circular import
    account_slug: Optional[str] = None,
    instance_slug: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute parameter cascade for multiple parameters using generic infrastructure.
    
    Consolidates the cascade loop pattern used in get_agent_model_settings and
    get_agent_tool_config into a single reusable function with error handling.
    
    Args:
        agent_name: Agent name for configuration lookup
        parameter_specs: Dictionary of parameter specifications with agent_path, global_path, fallback
        get_agent_parameter_func: The get_agent_parameter function (passed to avoid circular import)
        account_slug: Optional account identifier for multi-tenant path
        instance_slug: Optional instance identifier for multi-tenant path
        
    Returns:
        Dictionary with resolved parameter values using proper cascade logic
        
    Example parameter_specs:
        {
            "temperature": {
                "agent_path": "model_settings.temperature",
                "global_path": "llm.temperature",
                "fallback": 0.7
            },
            "max_tokens": {
                "agent_path": "model_settings.max_tokens",
                "global_path": "llm.max_tokens",
                "fallback": 1024
            }
        }
    """
    result = {}
    
    for param_name, config in parameter_specs.items():
        try:
            value = await get_agent_parameter_func(
                agent_name=agent_name,
                parameter_path=config["agent_path"],
                fallback=config["fallback"],
                global_path=config.get("global_path"),  # Optional for tools
                account_slug=account_slug,
                instance_slug=instance_slug
            )
            result[param_name] = value
        except Exception as e:
            # Log error but continue with fallback
            logfire.warn(
                'config.cascade.parameter_error',
                param_name=param_name,
                agent_name=agent_name,
                error=str(e),
                fallback=config["fallback"]
            )
            result[param_name] = config["fallback"]
    
    return result

