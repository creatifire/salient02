"""
Common dependency injection patterns for Pydantic AI agents.

This module provides dependency injection classes that are injected into
agent execution context, providing access to database connections, vector
stores, session management, and account context.

Key Classes:
- BaseDependencies: Core dependencies for all agents
- SessionDependencies: Session-aware dependencies
- AccountScopedDependencies: Multi-account dependencies (Phase 3+)

Design:
- Follows Pydantic AI dependency injection patterns
- Integrates with existing FastAPI database and session infrastructure
- Provides account isolation and resource management
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID

from ...database import get_db_session, get_database_service  # Existing database integration
from ...config import load_config  # Existing configuration system
from .types import AccountContext, DatabaseConnection, VectorDBConfig


@dataclass
class BaseDependencies:
    """
    Core dependencies injected into all agent execution contexts.
    
    This class provides the basic dependencies that all agents need:
    - Database connection for persistence
    - Configuration access
    - Basic session information
    
    Usage in Pydantic AI agents:
        @dataclass
        class MyAgentDeps(BaseDependencies):
            # Additional dependencies specific to agent type
            pass
            
        agent = Agent('openai:gpt-4o', deps_type=MyAgentDeps)
    """
    
    # Database connection (integrates with existing database.py)
    db_connection: DatabaseConnection
    
    # Configuration access
    config: Dict[str, Any]
    
    # Session context
    session_id: str
    user_id: Optional[str] = None
    
    @classmethod
    async def create(
        cls,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> BaseDependencies:
        """
        Factory method to create dependencies with proper initialization.
        
        Args:
            session_id: Current session identifier
            user_id: Optional user identifier
            
        Returns:
            Initialized BaseDependencies instance
        """
        # Load configuration using existing config system
        config = load_config()
        
        # Create database connection (placeholder - integrate with existing system)
        db_connection = DatabaseConnection()
        
        return cls(
            db_connection=db_connection,
            config=config,
            session_id=session_id,
            user_id=user_id,
        )


@dataclass
class SessionDependencies(BaseDependencies):
    """
    Session-aware dependencies for agents that need session context.
    
    Extends BaseDependencies with session-specific functionality including
    conversation history, user preferences, and session state management.
    
    Used by agents that maintain conversational context across interactions.
    """
    
    # Session metadata
    session_created_at: Optional[str] = None
    session_metadata: Optional[Dict[str, Any]] = None
    
    # Conversation context
    conversation_history: Optional[list] = None
    history_limit: int = 20
    
    # Agent configuration (for tool access)
    agent_config: Optional[Dict[str, Any]] = None
    
    # db_session removed - tools create own sessions via get_db_session() (BUG-0023-001)
    # This eliminates concurrent DB operation errors while preserving parallel tool execution
    
    # Multi-tenant support
    agent_instance_id: Optional[int] = None  # Agent instance ID (for attribution)
    account_id: Optional[UUID] = None  # Account ID (for multi-tenant data isolation)
    
    @classmethod
    async def create(
        cls,
        session_id: str,
        user_id: Optional[str] = None,
        history_limit: int = 20,
    ) -> SessionDependencies:
        """
        Factory method to create session-aware dependencies.
        
        Args:
            session_id: Current session identifier
            user_id: Optional user identifier
            history_limit: Maximum conversation history to maintain
            
        Returns:
            Initialized SessionDependencies instance
        """
        # Create base dependencies
        base = await BaseDependencies.create(session_id, user_id)
        
        # TODO: Load session metadata from database using existing session service
        # from app.services.session_service import get_session_metadata
        # session_metadata = await get_session_metadata(session_id)
        
        return cls(
            # Copy base dependency fields
            db_connection=base.db_connection,
            config=base.config,
            session_id=base.session_id,
            user_id=base.user_id,
            
            # Session-specific fields
            history_limit=history_limit,
            conversation_history=[],  # TODO: Load from database
            session_metadata={},  # TODO: Load from database
        )


@dataclass 
class AccountScopedDependencies(SessionDependencies):
    """
    Multi-account dependencies for Phase 3+ multi-tenant support.
    
    Extends SessionDependencies with account context, vector database
    routing, and resource management for multi-tenant deployments.
    
    Features:
    - Account isolation and context
    - Vector database routing (Pinecone vs pgvector by tier)
    - Resource limits and quota enforcement
    - Account-specific configuration overrides
    """
    
    # Account context
    account_context: AccountContext = None
    
    # Vector database configuration (account-specific routing) 
    vector_config: VectorDBConfig = None
    
    # Resource management (with defaults)
    resource_limits: Dict[str, Any] = None
    usage_tracking: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.resource_limits is None:
            self.resource_limits = {}
        if self.usage_tracking is None:
            self.usage_tracking = {}
    
    @classmethod
    async def create(
        cls,
        session_id: str, 
        account_id: str = "default",
        user_id: Optional[str] = None,
        history_limit: int = 20,
    ) -> AccountScopedDependencies:
        """
        Factory method to create account-scoped dependencies.
        
        Args:
            session_id: Current session identifier
            account_id: Account identifier (default="default" for Phase 1)
            user_id: Optional user identifier
            history_limit: Maximum conversation history to maintain
            
        Returns:
            Initialized AccountScopedDependencies instance
        """
        # Create session dependencies
        session_deps = await SessionDependencies.create(
            session_id, user_id, history_limit
        )
        
        # Create account context (Phase 1: use defaults)
        account_context = AccountContext(
            account_id=account_id,
            account_name="Default Account",  # TODO: Load from database in Phase 3
            subscription_tier="standard",   # TODO: Load from database in Phase 3
        )
        
        # Configure vector database routing based on subscription tier
        if account_context.subscription_tier == "budget":
            # Budget tier uses pgvector (local PostgreSQL extension)
            vector_config = VectorDBConfig(
                provider="pgvector",
                connection_params={"database_url": session_deps.config["database"]["url"]},
            )
        else:
            # Standard/Professional/Enterprise use Pinecone
            vector_config = VectorDBConfig(
                provider="pinecone", 
                connection_params=session_deps.config.get("vector", {}),
                namespace=f"account_{account_id}",  # Account isolation
            )
        
        # Resource limits (TODO: Load from database in Phase 3)
        resource_limits = {
            "max_tokens_per_day": 100000,
            "max_requests_per_hour": 1000,
            "max_vector_searches_per_day": 5000,
        }
        
        return cls(
            # Copy session dependency fields
            db_connection=session_deps.db_connection,
            config=session_deps.config,
            session_id=session_deps.session_id,
            user_id=session_deps.user_id,
            history_limit=session_deps.history_limit,
            conversation_history=session_deps.conversation_history,
            session_metadata=session_deps.session_metadata,
            
            # Account-scoped fields
            account_context=account_context,
            vector_config=vector_config,
            resource_limits=resource_limits,
            usage_tracking={},
        )
