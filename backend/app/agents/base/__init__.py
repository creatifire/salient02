"""
Base agent classes and shared functionality for Pydantic AI agents.

This module provides the foundation classes that all agents inherit from,
including dependency injection patterns, tool base classes, and shared types.

Components:
- agent_base.py: Base agent class with common functionality
- dependencies.py: Common dependency injection patterns
- tools_base.py: Base tool classes for agent capabilities
- types.py: Shared Pydantic models and type definitions

Design Principles:
- Account-aware dependency injection for multi-tenant support
- Consistent tool interface across all agent types
- Structured outputs with validation
- Integration with existing database and session management
"""

from .agent_base import BaseAgent
from .dependencies import BaseDependencies, SessionDependencies, AccountScopedDependencies
from .tools_base import BaseTool, BaseToolOutput
from .types import (
    AgentResponse,
    ToolResult,
    AgentConfig,
    AccountContext,
)

__all__ = [
    # Core agent infrastructure
    "BaseAgent",
    "BaseDependencies", 
    "SessionDependencies",
    "AccountScopedDependencies",
    
    # Tool infrastructure
    "BaseTool",
    "BaseToolOutput",
    
    # Types and models
    "AgentResponse",
    "ToolResult",
    "AgentConfig",
    "AccountContext",
]
