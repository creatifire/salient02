"""
Agent configuration loading and management system.

This module provides configuration loading capabilities for Pydantic AI agents,
including YAML template loading, agent selection logic, and validation.

Key Features:
- Load agent configurations from YAML templates
- Agent selection based on app.yaml routing configuration
- Configuration validation and schema enforcement
- Route-based agent selection logic
- Integration with existing app configuration system

Usage:
    from backend.app.agents.config_loader import get_agent_config, get_agent_for_route
    
    # Load specific agent config
    config = await get_agent_config("simple_chat")
    
    # Get agent type for a route
    agent_type = get_agent_for_route("/chat")
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml
from pydantic import ValidationError
import logfire

from ..config import load_config
from .base.types import AgentConfig


class AgentConfigError(Exception):
    """Custom exception for agent configuration errors."""
    pass


class AgentConfigLoader:
    """
    Agent configuration loading and management system.
    
    Handles loading agent configurations from YAML files, validating them,
    and providing agent selection logic based on routes and defaults.
    """
    
    def __init__(self):
        """Initialize the config loader with app configuration."""
        self.app_config = load_config()
        self.agent_config = self.app_config.get("agents", {})
        self.routes_config = self.app_config.get("routes", {})
        
        # Get configs directory path
        self.configs_dir = Path(
            self.agent_config.get("configs_directory", "./config/agent_configs/")
        )
        
        # Make path relative to backend directory if needed
        if not self.configs_dir.is_absolute():
            backend_dir = Path(__file__).parent.parent.parent  # Go up to backend/
            self.configs_dir = backend_dir / self.configs_dir
        
        self._config_cache: Dict[str, AgentConfig] = {}
    
    async def get_agent_config(self, agent_type: str) -> AgentConfig:
        """
        Load and validate configuration for a specific agent type.
        
        Args:
            agent_type: Agent type identifier (e.g., "simple_chat")
            
        Returns:
            Validated AgentConfig instance
            
        Raises:
            AgentConfigError: If configuration loading or validation fails
        """
        # Check cache first
        if agent_type in self._config_cache:
            return self._config_cache[agent_type]
        
        # Construct config file path - try new folder structure first
        config_file = self.configs_dir / agent_type / "config.yaml"
        
        # Fall back to legacy flat structure if new structure doesn't exist
        if not config_file.exists():
            config_file = self.configs_dir / f"{agent_type}.yaml"
            
        if not config_file.exists():
            raise AgentConfigError(
                f"Agent configuration file not found. Tried: {self.configs_dir / agent_type / 'config.yaml'} and {self.configs_dir / f'{agent_type}.yaml'}"
            )
        
        try:
            # Load YAML configuration
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data:
                raise AgentConfigError(f"Empty configuration file: {config_file}")
            
            # Load external prompt files if specified
            if "prompts" in config_data and "system_prompt_file" in config_data["prompts"]:
                prompt_file_path = config_data["prompts"]["system_prompt_file"]
                
                # Resolve relative path from the config file directory
                if prompt_file_path.startswith("./"):
                    prompt_file_path = prompt_file_path[2:]  # Remove "./"
                    prompt_file = config_file.parent / prompt_file_path
                else:
                    prompt_file = Path(prompt_file_path)
                    if not prompt_file.is_absolute():
                        prompt_file = config_file.parent / prompt_file_path
                
                if not prompt_file.exists():
                    raise AgentConfigError(f"System prompt file not found: {prompt_file}")
                
                try:
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        system_prompt = f.read().strip()
                    
                    # Replace the file reference with the actual prompt content
                    config_data["system_prompt"] = system_prompt
                    
                    # Keep the file reference for debugging/tracking
                    config_data["prompts"]["system_prompt_loaded_from"] = str(prompt_file)
                    
                except Exception as e:
                    raise AgentConfigError(f"Failed to load system prompt from {prompt_file}: {e}")
            
            # Validate and create AgentConfig
            agent_config = AgentConfig(**config_data)
            
            # Verify agent_type matches filename
            if agent_config.agent_type != agent_type:
                raise AgentConfigError(
                    f"Agent type mismatch: file '{agent_type}.yaml' contains "
                    f"agent_type '{agent_config.agent_type}'"
                )
            
            # Cache the validated config
            self._config_cache[agent_type] = agent_config
            
            return agent_config
            
        except yaml.YAMLError as e:
            raise AgentConfigError(f"Invalid YAML in {config_file}: {e}")
        except ValidationError as e:
            raise AgentConfigError(f"Invalid agent configuration in {config_file}: {e}")
        except Exception as e:
            raise AgentConfigError(f"Failed to load agent config {config_file}: {e}")
    
    def get_available_agents(self) -> List[str]:
        """
        Get list of available agent types from app configuration.
        
        Returns:
            List of available agent type identifiers
        """
        return self.agent_config.get("available_agents", ["simple_chat"])
    
    def get_default_agent(self) -> str:
        """
        Get the default agent type from app configuration.
        
        Returns:
            Default agent type identifier
        """
        return self.agent_config.get("default_agent", "simple_chat")
    
    def get_agent_for_route(self, route: str) -> str:
        """
        Get the appropriate agent type for a given route.
        
        Args:
            route: HTTP route path (e.g., "/chat", "/agents/simple-chat")
            
        Returns:
            Agent type identifier to use for this route
        """
        # Check if route has specific agent assignment
        if route in self.routes_config:
            agent_type = self.routes_config[route]
            
            # Validate that the agent is available
            if agent_type in self.get_available_agents():
                return agent_type
            else:
                # Fall back to default if configured agent is not available
                pass
        
        # Check for pattern matches (e.g., /agents/{agent_type})
        if route.startswith("/agents/"):
            parts = route.split("/")
            if len(parts) >= 3:
                agent_type = parts[2]  # /agents/simple-chat -> simple-chat
                
                # Convert URL slug to agent type if needed
                agent_type = agent_type.replace("-", "_")
                
                if agent_type in self.get_available_agents():
                    return agent_type
        
        # Return default agent
        return self.get_default_agent()
    
    async def validate_agent_availability(self, agent_type: str) -> bool:
        """
        Check if an agent type is available and has valid configuration.
        
        Args:
            agent_type: Agent type identifier
            
        Returns:
            True if agent is available and has valid config
        """
        try:
            if agent_type not in self.get_available_agents():
                return False
            
            # Try to load the configuration
            await self.get_agent_config(agent_type)
            return True
            
        except AgentConfigError:
            return False
    
    async def list_agent_configs(self) -> Dict[str, AgentConfig]:
        """
        Load all available agent configurations.
        
        Returns:
            Dictionary mapping agent types to their configurations
        """
        configs = {}
        
        for agent_type in self.get_available_agents():
            try:
                config = await self.get_agent_config(agent_type)
                configs[agent_type] = config
            except AgentConfigError as e:
                # Log error but continue with other configs
                print(f"Warning: Failed to load config for {agent_type}: {e}")
        
        return config


async def get_agent_history_limit(agent_name: str = "simple_chat") -> int:
    """
    Get history_limit using agent-first configuration cascade with enhanced monitoring.
    
    Now uses the generic cascade infrastructure for consistency.
    Implements the proper cascade: agent config → global config → fallback (50)
    Includes comprehensive audit trail, performance monitoring, and troubleshooting guidance.
    
    Args:
        agent_name: Agent name for configuration lookup
        
    Returns:
        History limit value using proper cascade logic
    """
    # Use generic cascade infrastructure for consistency
    return await get_agent_parameter(
        agent_name=agent_name,
        parameter_path="context_management.history_limit",
        fallback=50,
        global_path="chat.history_limit"
    )


def get_configs_directory() -> Path:
    """Get the agent configurations directory path."""
    config_loader = get_config_loader()
    return config_loader.configs_dir


async def get_agent_parameter(agent_name: str, parameter_path: str, fallback: Any = None, 
                             global_path: str = None, account_slug: Optional[str] = None,
                             instance_slug: Optional[str] = None) -> Any:
    """
    Generic configuration cascade function for any parameter.
    
    Implements the agent→global→fallback cascade pattern with comprehensive monitoring.
    Supports both legacy agent_type-based paths and multi-tenant account/instance paths.
    
    Args:
        agent_name: Agent name for configuration lookup (legacy) or agent_type identifier
        parameter_path: Dot-notation path to parameter (e.g., "model_settings.temperature")
        fallback: Fallback value if parameter not found in any source
        global_path: Optional custom path in global config (defaults to parameter_path)
        account_slug: Optional account identifier for multi-tenant path (if provided, instance_slug required)
        instance_slug: Optional instance identifier for multi-tenant path (if provided, account_slug required)
        
    Returns:
        Parameter value using proper cascade logic with comprehensive audit trail
        
    Examples:
        # Legacy pattern (backward compatible)
        await get_agent_parameter("simple_chat", "model_settings.temperature", 0.7)
        
        # Multi-tenant pattern (BUG-0023-002 fix)
        await get_agent_parameter("simple_chat", "model_settings.temperature", 0.7,
                                 account_slug="wyckoff", instance_slug="wyckoff_info_chat1")
    """
    from ..config import load_config
    from .cascade_monitor import CascadeAuditTrail, CascadeMetrics
    
    # Initialize comprehensive audit trail
    audit_trail = CascadeAuditTrail(agent_name, parameter_path)
    
    try:
        # STEP 1: Try agent-specific configuration first (highest priority)
        # Use multi-tenant path if account_slug and instance_slug provided (BUG-0023-002 fix)
        if account_slug and instance_slug:
            # Multi-tenant path: agent_configs/{account_slug}/{instance_slug}/config.yaml
            from .instance_loader import _get_config_path
            agent_config_path_obj = _get_config_path(account_slug, instance_slug)
            agent_config_path = str(agent_config_path_obj)
            
            try:
                with audit_trail.attempt_source("agent_config", agent_config_path) as attempt:
                    # Load config directly from file (multi-tenant pattern)
                    if not agent_config_path_obj.exists():
                        attempt.failure(f"Config file not found: {agent_config_path}")
                    else:
                        import yaml
                        with open(agent_config_path_obj, 'r', encoding='utf-8') as f:
                            config_data = yaml.safe_load(f)
                        
                        if config_data:
                            # Navigate through the parameter path
                            value = _get_nested_parameter(config_data, parameter_path)
                            if value is not None:
                                return attempt.success(value)
                        
                        attempt.failure(f"Agent config exists but missing {parameter_path} parameter")
            except Exception as e:
                # Exception will be recorded by the context manager
                pass
        else:
            # Legacy path: agent_configs/{agent_name}/config.yaml (backward compatibility)
            agent_config_path = f"backend/config/agent_configs/{agent_name}/config.yaml"
            try:
                with audit_trail.attempt_source("agent_config", agent_config_path) as attempt:
                    agent_config = await get_agent_config(agent_name)
                    
                    # Navigate through the parameter path
                    value = _get_nested_parameter_from_object(agent_config, parameter_path)
                    if value is not None:
                        return attempt.success(value)
                    
                    attempt.failure(f"Agent config exists but missing {parameter_path} parameter")
            except Exception as e:
                # Exception will be recorded by the context manager
                pass
        
        # STEP 2: Fall back to global configuration (app.yaml)
        global_config_path = "backend/config/app.yaml"
        try:
            with audit_trail.attempt_source("global_config", global_config_path) as attempt:
                global_config = load_config()
                
                # Use custom global path if provided, otherwise use parameter_path
                lookup_path = global_path or parameter_path
                value = _get_nested_parameter(global_config, lookup_path)
                if value is not None:
                    return attempt.success(value)
                
                attempt.failure(f"Global config exists but missing {lookup_path} parameter")
        except Exception as e:
            # Exception will be recorded by the context manager
            pass
        
        # STEP 3: Use fallback value (last resort)
        with audit_trail.attempt_source("hardcoded_fallback", "hardcoded in code") as attempt:
            if fallback is not None:
                # Log fallback usage for monitoring if it's not expected
                if parameter_path != "context_management.history_limit":  # Don't warn for known fallbacks
                    CascadeMetrics.log_fallback_usage(
                        agent_name, 
                        parameter_path, 
                        f"Both agent and global configs unavailable or missing {parameter_path}"
                    )
                
                return attempt.success(fallback)
            else:
                attempt.failure(f"No fallback value provided for {parameter_path}")
                raise ValueError(f"Parameter {parameter_path} not found in any configuration source and no fallback provided")
            
    finally:
        audit_trail.finalize_and_log()


def _get_nested_parameter(config_dict: dict, parameter_path: str) -> Any:
    """
    Navigate through nested dictionary using dot notation.
    
    Args:
        config_dict: Dictionary to navigate
        parameter_path: Dot-notation path (e.g., "model_settings.temperature")
        
    Returns:
        Parameter value or None if not found
        
    Examples:
        _get_nested_parameter({"model_settings": {"temperature": 0.3}}, "model_settings.temperature") → 0.3
        _get_nested_parameter({"tools": {"vector_search": {"enabled": True}}}, "tools.vector_search.enabled") → True
    """
    try:
        current = config_dict
        for key in parameter_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    except (KeyError, TypeError, AttributeError):
        return None


def _get_nested_parameter_from_object(config_obj: Any, parameter_path: str) -> Any:
    """
    Navigate through nested object attributes using dot notation.
    
    Args:
        config_obj: Object to navigate (Pydantic model or similar)
        parameter_path: Dot-notation path (e.g., "model_settings.temperature")
        
    Returns:
        Parameter value or None if not found
        
    Examples:
        _get_nested_parameter_from_object(agent_config, "model_settings.temperature") → 0.3
        _get_nested_parameter_from_object(agent_config, "tools.vector_search.enabled") → True
    """
    try:
        current = config_obj
        path_parts = parameter_path.split('.')
        
        for i, key in enumerate(path_parts):
            if hasattr(current, key):
                current = getattr(current, key)
                # If we got a dictionary and there are more path parts, continue with dict navigation
                if isinstance(current, dict) and i < len(path_parts) - 1:
                    remaining_path = '.'.join(path_parts[i + 1:])
                    return _get_nested_parameter(current, remaining_path)
            else:
                return None
        return current
    except (AttributeError, TypeError, KeyError):
        return None


async def get_agent_model_settings(agent_name: str, account_slug: Optional[str] = None,
                                   instance_slug: Optional[str] = None) -> dict:
    """
    Get model settings using agent-first configuration cascade with mixed inheritance.
    
    Implements comprehensive model parameter cascade: agent config → global config → fallbacks
    Supports mixed inheritance where individual parameters can come from different sources.
    Supports both legacy agent_type-based paths and multi-tenant account/instance paths.
    
    Args:
        agent_name: Agent name for configuration lookup (legacy) or agent_type identifier
        account_slug: Optional account identifier for multi-tenant path (BUG-0023-002 fix)
        instance_slug: Optional instance identifier for multi-tenant path (BUG-0023-002 fix)
        
    Returns:
        Dictionary with model settings using proper cascade logic for each parameter
        
    Example Result:
        {
            "model": "moonshotai/kimi-k2-0905",  # From agent config
            "temperature": 0.3,                  # From agent or global config
            "max_tokens": 2000                   # From agent or global config
        }
    """
    # Define model parameters with their fallback values and global paths
    model_parameters = {
        "model": {
            "agent_path": "model_settings.model",
            "global_path": "llm.model", 
            "fallback": "deepseek/deepseek-chat-v3.1"
        },
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
    
    # Use generic cascade for each parameter independently (mixed inheritance)
    model_settings = {}
    
    for param_name, config in model_parameters.items():
        try:
            value = await get_agent_parameter(
                agent_name=agent_name,
                parameter_path=config["agent_path"],
                fallback=config["fallback"],
                global_path=config["global_path"],
                account_slug=account_slug,
                instance_slug=instance_slug
            )
            model_settings[param_name] = value
        except Exception as e:
            # Log error but continue with fallback
            logfire.warn(
                'config.agent.model_setting_error',
                param_name=param_name,
                agent_name=agent_name,
                error=str(e),
                fallback=config["fallback"]
            )
            model_settings[param_name] = config["fallback"]
    
    return model_settings


async def get_agent_tool_config(agent_name: str, tool_name: str,
                                account_slug: Optional[str] = None,
                                instance_slug: Optional[str] = None) -> dict:
    """
    Get tool configuration using agent-first configuration cascade with mixed inheritance.
    
    Implements comprehensive tool parameter cascade: agent config → fallbacks
    Supports mixed inheritance where individual parameters can come from different sources.
    Enables per-agent tool enable/disable capability with comprehensive monitoring.
    Supports both legacy agent_type-based paths and multi-tenant account/instance paths.
    
    Args:
        agent_name: Agent name for configuration lookup (legacy) or agent_type identifier
        tool_name: Tool name (e.g., 'vector_search', 'web_search', 'conversation_management')
        account_slug: Optional account identifier for multi-tenant path (BUG-0023-002 fix)
        instance_slug: Optional instance identifier for multi-tenant path (BUG-0023-002 fix)
        
    Returns:
        Dictionary with tool configuration using proper cascade logic for each parameter
        
    Example Result:
        {
            "enabled": True,              # From agent config or fallback
            "max_results": 5,            # From agent config or fallback
            "similarity_threshold": 0.7   # From agent config or fallback
        }
    """
    # Define tool-specific parameter configurations
    tool_configs = {
        "vector_search": {
            "enabled": {
                "agent_path": "tools.vector_search.enabled",
                "fallback": True
            },
            "max_results": {
                "agent_path": "tools.vector_search.max_results",
                "fallback": 5
            },
            "similarity_threshold": {
                "agent_path": "tools.vector_search.similarity_threshold",
                "fallback": 0.7
            },
            "namespace_isolation": {
                "agent_path": "tools.vector_search.namespace_isolation",
                "fallback": True
            }
        },
        "web_search": {
            "enabled": {
                "agent_path": "tools.web_search.enabled",
                "fallback": False
            },
            "provider": {
                "agent_path": "tools.web_search.provider",
                "fallback": "exa"
            },
            "max_results": {
                "agent_path": "tools.web_search.max_results",
                "fallback": 10
            }
        },
        "conversation_management": {
            "enabled": {
                "agent_path": "tools.conversation_management.enabled",
                "fallback": True
            },
            "auto_summarize_threshold": {
                "agent_path": "tools.conversation_management.auto_summarize_threshold",
                "fallback": 10
            }
        },
        "profile_capture": {
            "enabled": {
                "agent_path": "tools.profile_capture.enabled",
                "fallback": False
            }
        },
        "email_summary": {
            "enabled": {
                "agent_path": "tools.email_summary.enabled",
                "fallback": False
            }
        }
    }
    
    # Get the parameter configuration for this tool
    if tool_name not in tool_configs:
        logfire.warn(
            'config.agent.unknown_tool',
            tool_name=tool_name,
            agent_name=agent_name,
            action='returning_empty_config'
        )
        return {"enabled": False}
    
    parameters = tool_configs[tool_name]
    
    # Use generic cascade for each parameter independently (mixed inheritance)
    tool_config = {}
    
    for param_name, config in parameters.items():
        try:
            value = await get_agent_parameter(
                agent_name=agent_name,
                parameter_path=config["agent_path"],
                fallback=config["fallback"],
                global_path=None,  # Tools don't have global config equivalents
                account_slug=account_slug,
                instance_slug=instance_slug
            )
            tool_config[param_name] = value
        except Exception as e:
            # Log error but continue with fallback
            logfire.warn(
                'config.agent.tool_setting_error',
                param_name=param_name,
                tool_name=tool_name,
                agent_name=agent_name,
                error=str(e),
                fallback=config["fallback"]
            )
            tool_config[param_name] = config["fallback"]
    
    return tool_config


# Global config loader instance
_config_loader: Optional[AgentConfigLoader] = None


def get_config_loader() -> AgentConfigLoader:
    """Get the global agent configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = AgentConfigLoader()
    return _config_loader


# Convenience functions for common operations
async def get_agent_config(agent_type: str) -> AgentConfig:
    """Load configuration for a specific agent type."""
    return await get_config_loader().get_agent_config(agent_type)


def get_agent_for_route(route: str) -> str:
    """Get the appropriate agent type for a given route."""
    return get_config_loader().get_agent_for_route(route)


def get_available_agents() -> List[str]:
    """Get list of available agent types."""
    return get_config_loader().get_available_agents()


def get_default_agent() -> str:
    """Get the default agent type."""
    return get_config_loader().get_default_agent()


async def validate_agent_availability(agent_type: str) -> bool:
    """Check if an agent type is available and has valid configuration."""
    return await get_config_loader().validate_agent_availability(agent_type)
