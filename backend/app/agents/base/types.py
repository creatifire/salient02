"""
Shared types and Pydantic models for agent system.

This module defines common data structures used across all agent types,
including responses, configurations, and account context information.

Key Models:
- AccountContext: Account-scoped context for multi-tenant support
- AgentConfig: Agent configuration loaded from YAML
- AgentResponse: Structured agent response format
- ToolResult: Standard tool execution result format
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class AccountContext(BaseModel):
    """Account context for multi-tenant agent operations."""
    
    account_id: str = Field(
        description="Account identifier (default='default' for Phase 1)"
    )
    account_name: str = Field(
        description="Human-readable account name"
    )
    subscription_tier: str = Field(
        default="standard",
        description="Account subscription tier (budget|standard|professional|enterprise)"
    )
    vector_db_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Vector database configuration for this account"
    )
    resource_limits: Dict[str, Any] = Field(
        default_factory=dict,
        description="Account-specific resource limits and quotas"
    )


class AgentConfig(BaseModel):
    """Agent configuration loaded from YAML templates."""
    
    agent_type: str = Field(description="Agent type identifier (e.g., 'simple_chat')")
    name: str = Field(description="Human-readable agent name")
    description: str = Field(description="Agent description and capabilities")
    
    system_prompt: str = Field(description="System prompt template for the agent")
    
    model_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="LLM model configuration (model, temperature, max_tokens)"
    )
    
    tools: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool configurations and settings"
    )
    
    context_management: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context management settings (history_limit, context_window_tokens, etc.)"
    )
    
    prompts: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Prompt configuration and metadata (system_prompt_file, loaded_from, etc.)"
    )
    
    dependencies: Dict[str, Any] = Field(
        default_factory=dict,
        description="Required dependencies (vector_db, session, etc.)"
    )


class ToolResult(BaseModel):
    """Standard result format for tool execution."""
    
    tool_name: str = Field(description="Name of the tool that was executed")
    success: bool = Field(description="Whether the tool execution succeeded")
    result: Any = Field(description="Tool execution result data")
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )
    execution_time_ms: Optional[float] = Field(
        default=None,
        description="Tool execution time in milliseconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the tool execution"
    )


class AgentResponse(BaseModel):
    """Structured response format from agent execution."""
    
    content: str = Field(description="Main response content")
    tool_results: List[ToolResult] = Field(
        default_factory=list,
        description="Results from any tools that were executed"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Response metadata (model used, tokens, etc.)"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation/session identifier"
    )
    agent_type: Optional[str] = Field(
        default=None,
        description="Type of agent that generated this response"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response generation timestamp"
    )


@dataclass
class DatabaseConnection:
    """Database connection wrapper for dependency injection."""
    # This will be properly implemented to match existing database.py patterns
    pass


@dataclass 
class VectorDBConfig:
    """Vector database configuration for dependency injection."""
    provider: str  # 'pinecone' or 'pgvector'
    connection_params: Dict[str, Any]
    namespace: Optional[str] = None
