"""
Simple Chat Agent Factory Integration.

This module provides factory functions for creating Simple Chat Agent instances
using the existing configuration system and SessionDependencies patterns.

Key Features:
- Integration with existing AgentConfigLoader system
- YAML configuration loading from simple_chat.yaml
- SessionDependencies creation and validation
- Agent instance caching for performance
- Configuration validation and error handling

Design:
- Uses existing config_loader.py for YAML loading
- Integrates with SessionDependencies.create() factory methods
- Provides both simple and advanced creation methods
- Follows existing factory patterns from BaseAgent

Usage:
    # Simple factory creation
    agent = await create_simple_chat_agent(session_id="123")
    
    # With custom configuration
    agent = await create_simple_chat_agent_from_config(
        session_id="123", 
        config_overrides={"temperature": 0.5}
    )
    
    # Using existing session dependencies
    session_deps = await SessionDependencies.create(session_id="123")
    agent = create_simple_chat_agent_with_deps(session_deps)
"""

from __future__ import annotations

import asyncio
from typing import Dict, Optional, Any
import logging
from functools import lru_cache

from app.agents.config_loader import get_agent_config, AgentConfigError
from app.agents.base.dependencies import SessionDependencies
from app.agents.base.types import AgentConfig
from .agent import SimpleChatAgent
from .models import ChatResponse

# Configure logging
logger = logging.getLogger(__name__)


class SimpleChatAgentFactory:
    """
    Factory class for creating and managing Simple Chat Agent instances.
    
    Provides methods for creating agents with different configuration sources
    and dependency injection patterns. Integrates with the existing configuration
    system and provides caching for performance optimization.
    """
    
    def __init__(self):
        """Initialize the factory with configuration loading capability."""
        self._agent_cache: Dict[str, SimpleChatAgent] = {}
        self._config_cache: Optional[AgentConfig] = None
    
    async def create_agent(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        config_overrides: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> tuple[SimpleChatAgent, SessionDependencies]:
        """
        Create a Simple Chat Agent instance with session dependencies.
        
        Args:
            session_id: Session identifier for conversation tracking
            user_id: Optional user identifier
            config_overrides: Optional configuration parameter overrides
            use_cache: Whether to use cached agent instances (default: True)
            
        Returns:
            Tuple of (SimpleChatAgent instance, SessionDependencies instance)
            
        Raises:
            AgentConfigError: If configuration loading fails
            ValueError: If session_id is invalid
            RuntimeError: If agent creation fails
        """
        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty")
        
        try:
            # Load configuration
            config = await self._get_agent_config()
            
            # Apply configuration overrides
            if config_overrides:
                config = self._apply_config_overrides(config, config_overrides)
            
            # Create session dependencies
            session_deps = await SessionDependencies.create(
                session_id=session_id.strip(),
                user_id=user_id
            )
            
            # Create or retrieve cached agent
            cache_key = self._generate_cache_key(config, session_id)
            
            if use_cache and cache_key in self._agent_cache:
                logger.info(f"Using cached Simple Chat Agent for session {session_id}")
                agent = self._agent_cache[cache_key]
            else:
                # Create new agent instance
                agent = self._create_agent_from_config(config)
                
                if use_cache:
                    self._agent_cache[cache_key] = agent
                    logger.info(f"Created and cached Simple Chat Agent for session {session_id}")
                else:
                    logger.info(f"Created Simple Chat Agent (no caching) for session {session_id}")
            
            return agent, session_deps
            
        except Exception as e:
            logger.error(f"Failed to create Simple Chat Agent for session {session_id}: {e}")
            raise RuntimeError(f"Agent creation failed: {str(e)}") from e
    
    async def create_agent_with_deps(
        self,
        session_deps: SessionDependencies,
        config_overrides: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> SimpleChatAgent:
        """
        Create a Simple Chat Agent with existing SessionDependencies.
        
        Args:
            session_deps: Pre-created SessionDependencies instance
            config_overrides: Optional configuration parameter overrides
            use_cache: Whether to use cached agent instances (default: True)
            
        Returns:
            SimpleChatAgent instance configured for the session
            
        Raises:
            AgentConfigError: If configuration loading fails
            RuntimeError: If agent creation fails
        """
        try:
            # Load configuration
            config = await self._get_agent_config()
            
            # Apply configuration overrides
            if config_overrides:
                config = self._apply_config_overrides(config, config_overrides)
            
            # Create or retrieve cached agent
            cache_key = self._generate_cache_key(config, session_deps.session_id)
            
            if use_cache and cache_key in self._agent_cache:
                logger.info(f"Using cached Simple Chat Agent for session {session_deps.session_id}")
                return self._agent_cache[cache_key]
            else:
                # Create new agent instance
                agent = self._create_agent_from_config(config)
                
                if use_cache:
                    self._agent_cache[cache_key] = agent
                    logger.info(f"Created and cached Simple Chat Agent for session {session_deps.session_id}")
                else:
                    logger.info(f"Created Simple Chat Agent (no caching) for session {session_deps.session_id}")
                
                return agent
                
        except Exception as e:
            logger.error(f"Failed to create Simple Chat Agent with deps: {e}")
            raise RuntimeError(f"Agent creation failed: {str(e)}") from e
    
    def create_agent_simple(
        self,
        model_name: str = "openai:gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> SimpleChatAgent:
        """
        Create a Simple Chat Agent with basic configuration (no YAML loading).
        
        Args:
            model_name: LLM model identifier
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            SimpleChatAgent instance with basic configuration
        """
        logger.info(f"Creating simple agent with model {model_name}, temp={temperature}")
        
        return SimpleChatAgent(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def _get_agent_config(self) -> AgentConfig:
        """Load and cache the simple_chat agent configuration."""
        if self._config_cache is None:
            try:
                self._config_cache = await get_agent_config("simple_chat")
                logger.info("Loaded simple_chat configuration from YAML")
            except AgentConfigError as e:
                logger.error(f"Failed to load simple_chat configuration: {e}")
                raise
        
        return self._config_cache
    
    def _create_agent_from_config(self, config: AgentConfig) -> SimpleChatAgent:
        """Create agent instance from loaded configuration."""
        # Extract model settings
        model_settings = config.model_settings or {}
        model_name = model_settings.get("model", "openai:gpt-4o")
        temperature = model_settings.get("temperature", 0.3)
        max_tokens = model_settings.get("max_tokens", 2000)
        
        # Use system prompt from config
        system_prompt = config.system_prompt
        
        logger.info(f"Creating agent with config: model={model_name}, temp={temperature}")
        
        return SimpleChatAgent(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
    
    def _apply_config_overrides(
        self,
        config: AgentConfig,
        overrides: Dict[str, Any]
    ) -> AgentConfig:
        """Apply configuration overrides to the base configuration."""
        # Create a copy of the config data
        config_dict = config.dict()
        
        # Apply overrides to model_settings
        if "model_settings" not in config_dict:
            config_dict["model_settings"] = {}
        
        model_settings = config_dict["model_settings"]
        
        # Handle common overrides
        for key in ["model", "temperature", "max_tokens"]:
            if key in overrides:
                model_settings[key] = overrides[key]
        
        # Handle system prompt override
        if "system_prompt" in overrides:
            config_dict["system_prompt"] = overrides["system_prompt"]
        
        logger.info(f"Applied config overrides: {overrides}")
        
        # Create new AgentConfig with overrides
        return AgentConfig(**config_dict)
    
    def _generate_cache_key(self, config: AgentConfig, session_id: str) -> str:
        """Generate cache key for agent instances."""
        model_settings = config.model_settings or {}
        key_components = [
            config.agent_type,
            model_settings.get("model", "openai:gpt-4o"),
            str(model_settings.get("temperature", 0.3)),
            str(model_settings.get("max_tokens", 2000)),
            str(hash(config.system_prompt))[:8]  # Short hash of system prompt
        ]
        return "|".join(key_components)
    
    def clear_cache(self) -> int:
        """Clear the agent cache and return number of cached agents."""
        count = len(self._agent_cache)
        self._agent_cache.clear()
        self._config_cache = None
        logger.info(f"Cleared {count} cached agents")
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_agents": len(self._agent_cache),
            "config_cached": self._config_cache is not None,
            "cache_keys": list(self._agent_cache.keys())
        }


# Global factory instance
_factory: Optional[SimpleChatAgentFactory] = None


def get_factory() -> SimpleChatAgentFactory:
    """Get the global Simple Chat Agent factory instance."""
    global _factory
    if _factory is None:
        _factory = SimpleChatAgentFactory()
    return _factory


# Convenience factory functions
async def create_simple_chat_agent(
    session_id: str,
    user_id: Optional[str] = None,
    config_overrides: Optional[Dict[str, Any]] = None,
    use_cache: bool = True
) -> tuple[SimpleChatAgent, SessionDependencies]:
    """
    Create a Simple Chat Agent with session dependencies.
    
    Convenience function that uses the global factory instance.
    
    Args:
        session_id: Session identifier for conversation tracking
        user_id: Optional user identifier
        config_overrides: Optional configuration parameter overrides
        use_cache: Whether to use cached agent instances (default: True)
        
    Returns:
        Tuple of (SimpleChatAgent instance, SessionDependencies instance)
    """
    return await get_factory().create_agent(
        session_id=session_id,
        user_id=user_id,
        config_overrides=config_overrides,
        use_cache=use_cache
    )


async def create_simple_chat_agent_with_deps(
    session_deps: SessionDependencies,
    config_overrides: Optional[Dict[str, Any]] = None,
    use_cache: bool = True
) -> SimpleChatAgent:
    """
    Create a Simple Chat Agent with existing SessionDependencies.
    
    Args:
        session_deps: Pre-created SessionDependencies instance
        config_overrides: Optional configuration parameter overrides
        use_cache: Whether to use cached agent instances (default: True)
        
    Returns:
        SimpleChatAgent instance configured for the session
    """
    return await get_factory().create_agent_with_deps(
        session_deps=session_deps,
        config_overrides=config_overrides,
        use_cache=use_cache
    )


def create_simple_chat_agent_basic(
    model_name: str = "openai:gpt-4o",
    temperature: float = 0.3,
    max_tokens: int = 2000
) -> SimpleChatAgent:
    """
    Create a Simple Chat Agent with basic configuration (no YAML loading).
    
    Args:
        model_name: LLM model identifier
        temperature: Sampling temperature
        max_tokens: Maximum response tokens
        
    Returns:
        SimpleChatAgent instance with basic configuration
    """
    return get_factory().create_agent_simple(
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens
    )


def clear_agent_cache() -> int:
    """Clear the global agent cache and return number of cached agents."""
    return get_factory().clear_cache()


def get_agent_cache_stats() -> Dict[str, Any]:
    """Get cache statistics from the global factory."""
    return get_factory().get_cache_stats()
