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
    from app.agents.config_loader import get_agent_config, get_agent_for_route
    
    # Load specific agent config
    config = await get_agent_config("simple_chat")
    
    # Get agent type for a route
    agent_type = get_agent_for_route("/chat")
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import ValidationError

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
        
        # Construct config file path
        config_file = self.configs_dir / f"{agent_type}.yaml"
        
        if not config_file.exists():
            raise AgentConfigError(
                f"Agent configuration file not found: {config_file}"
            )
        
        try:
            # Load YAML configuration
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data:
                raise AgentConfigError(f"Empty configuration file: {config_file}")
            
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
        
        return configs
    
    def get_configs_directory(self) -> Path:
        """Get the agent configurations directory path."""
        return self.configs_dir


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
