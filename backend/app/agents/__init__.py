"""
Pydantic AI agents module for the Salient Sales Bot backend.

This module provides the foundation for multi-agent support with account-aware
dependency injection, tool integration, and configuration management.

Key Components:
- base/: Base agent classes and shared functionality
- simple_chat/: General conversational agent (Phase 1)
- sales/: Sales-focused agent with CRM integration (Phase 2)
- shared/: Common utilities and tools
- factory/: Agent instance creation and management (Phase 3+)

Architecture:
- Account-scoped dependency injection for multi-tenant support
- YAML-based configuration with database migration path
- Tool-based architecture with structured outputs
- Integration with existing FastAPI and database infrastructure

Usage:
    from app.agents.base import BaseAgent, BaseDependencies
    # SimpleChatAgent removed in Phase 0 cleanup - will be reimplemented in Phase 3
"""

__version__ = "0.1.0"

# Import base classes for easy access
from .base import (
    BaseAgent,
    BaseDependencies,
    BaseToolOutput,
)

__all__ = [
    "BaseAgent", 
    "BaseDependencies",
    "BaseToolOutput",
]
