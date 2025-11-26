"""
Agent Execution Service for orchestrating agent setup and execution.

This service consolidates agent initialization, context setup, and execution
patterns that were previously scattered across simple_chat.py and simple_chat_stream().

Key Features:
- Centralized agent context setup
- System prompt injection into message history
- Consistent execution patterns for streaming and non-streaming
- Proper dependency management and session handling
- Comprehensive logging and timing

Business Context:
Provides a single source of truth for agent execution, eliminating duplicate
setup logic and ensuring consistent behavior across all chat endpoints.

Dependencies:
- Pydantic AI for agent execution
- SessionDependencies for tool access
- Config cascade for agent settings
- Logfire for execution tracing
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, List, Optional, Dict
from uuid import UUID

import logfire
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, SystemPromptPart

from ..agents.base.dependencies import SessionDependencies


class AgentExecutionService:
    """
    Service for orchestrating agent setup and execution.
    
    Consolidates all agent initialization and execution logic into reusable
    methods, eliminating duplicate code between streaming and non-streaming
    endpoints while ensuring consistent behavior.
    
    Design Philosophy:
    - Single Responsibility: Setup vs Execution cleanly separated
    - Reusability: Same setup logic for all chat types
    - Testability: Isolated methods easy to test
    - Maintainability: Changes in one place affect all endpoints
    
    Key Responsibilities:
    - Load agent configuration via cascade
    - Create and configure SessionDependencies
    - Load conversation history
    - Inject system prompts into message history
    - Execute agent with proper timing and logging
    - Handle both streaming and non-streaming execution
    
    Thread Safety:
    All methods are static and stateless, making them thread-safe
    when used with async sessions and proper dependency injection.
    """
    
    @staticmethod
    async def setup_execution_context(
        session_id: str,
        agent_name: str = "simple_chat",
        agent_instance_id: Optional[int] = None,
        account_id: Optional[UUID] = None,
        instance_config: Optional[dict] = None,
        message_history: Optional[List[ModelMessage]] = None
    ) -> tuple[Agent, SessionDependencies, dict, str, list, List[ModelMessage], str]:
        """
        Setup complete execution context for agent.
        
        Consolidates all setup logic that was previously scattered in simple_chat():
        - Configuration loading via cascade
        - SessionDependencies creation and configuration
        - Conversation history loading
        - Agent initialization
        - System prompt injection into history
        
        This method represents ~60 lines of setup code that was duplicated between
        streaming and non-streaming endpoints.
        
        Args:
            session_id: Session ID for conversation context
            agent_name: Name of agent to initialize (default: "simple_chat")
            agent_instance_id: Agent instance ID for multi-tenant attribution
            account_id: Account UUID for multi-tenant data isolation
            instance_config: Instance-specific configuration overrides
            message_history: Optional pre-loaded message history
        
        Returns:
            Tuple of (agent, session_deps, prompt_breakdown, system_prompt,
                     tools_list, message_history, requested_model)
        
        Example:
            >>> service = AgentExecutionService()
            >>> agent, deps, breakdown, prompt, tools, history, model = \
            ...     await service.setup_execution_context(
            ...         session_id="550e8400-...",
            ...         agent_instance_id=1,
            ...         account_id=UUID("660e8400-...")
            ...     )
            >>> result = await agent.run(user_message, deps=deps, message_history=history)
        
        Notes:
        - System prompt injection is critical for Pydantic AI history handling
        - account_id is converted to primitive UUID to prevent serialization errors
        - If message_history is None, it will be loaded from database
        """
        # Load agent configuration via cascade
        from ..agents.config_loader import get_agent_history_limit, get_agent_model_settings
        from ..config import load_config
        
        default_history_limit = await get_agent_history_limit(agent_name)
        
        # Create session dependencies with agent config for tools
        session_deps = await SessionDependencies.create(
            session_id=session_id,
            user_id=None,  # Optional for simple chat
            history_limit=default_history_limit
        )
        
        # Add agent-specific fields for tool access
        session_deps.agent_config = instance_config
        session_deps.agent_instance_id = agent_instance_id
        
        # CRITICAL: Convert account_id to Python primitive UUID
        # Prevents Logfire serialization errors when Pydantic AI instruments tool calls
        if account_id is not None:
            session_deps.account_id = UUID(str(account_id)) if not isinstance(account_id, UUID) else account_id
        else:
            session_deps.account_id = None
        
        # Load model settings using centralized cascade
        model_settings = await get_agent_model_settings(agent_name)
        
        # Load conversation history if not provided
        if message_history is None:
            from ..agents.simple_chat import load_conversation_history
            message_history = await load_conversation_history(
                session_id=session_id,
                max_messages=None  # Uses agent history limit internally
            )
        
        # Get the agent (pass instance_config and account_id for multi-tenant support)
        from ..agents.simple_chat import get_chat_agent
        agent, prompt_breakdown, system_prompt, tools_list = await get_chat_agent(
            instance_config=instance_config,
            account_id=account_id
        )
        
        # CRITICAL FIX: Inject system prompt into message history
        # When Pydantic AI sees message_history, it expects the first ModelRequest
        # to include SystemPromptPart. Our database doesn't store system prompts,
        # so we must inject it here.
        if message_history and len(message_history) > 0:
            first_msg = message_history[0]
            if isinstance(first_msg, ModelRequest):
                # Check if SystemPromptPart is already present
                has_system_prompt = any(
                    isinstance(part, SystemPromptPart) for part in first_msg.parts
                )
                
                if not has_system_prompt:
                    # Inject SystemPromptPart at the beginning of the first message
                    system_prompt_part = SystemPromptPart(content=system_prompt)
                    # Create new ModelRequest with SystemPromptPart prepended
                    new_parts = [system_prompt_part] + list(first_msg.parts)
                    message_history[0] = ModelRequest(parts=new_parts)
                    
                    logfire.info(
                        'service.agent_execution.system_prompt_injected',
                        session_id=session_id,
                        original_parts_count=len(first_msg.parts),
                        new_parts_count=len(new_parts)
                    )
        
        # Extract requested model for logging
        config_to_use = instance_config if instance_config is not None else load_config()
        requested_model = config_to_use.get("model_settings", {}).get("model", "unknown")
        
        logfire.info(
            'service.agent_execution.context_setup_complete',
            session_id=session_id,
            agent_name=agent_name,
            agent_instance_id=agent_instance_id,
            account_id=str(account_id) if account_id else None,
            message_history_length=len(message_history),
            requested_model=requested_model
        )
        
        return (
            agent,
            session_deps,
            prompt_breakdown,
            system_prompt,
            tools_list,
            message_history,
            requested_model
        )
    
    @staticmethod
    async def execute_agent(
        agent: Agent,
        message: str,
        session_deps: SessionDependencies,
        message_history: List[ModelMessage],
        session_id: str,
        streaming: bool = False
    ) -> tuple[Any, int]:
        """
        Execute agent with proper timing and logging.
        
        Provides consistent execution pattern for both streaming and non-streaming
        endpoints, including proper timing measurement and detailed logging.
        
        Args:
            agent: Pydantic AI Agent instance to execute
            message: User message to process
            session_deps: SessionDependencies for tool access
            message_history: Conversation history with injected system prompt
            session_id: Session ID for logging
            streaming: Whether this is a streaming execution
        
        Returns:
            Tuple of (result, latency_ms)
            - result: Pydantic AI result object (or stream for streaming=True)
            - latency_ms: Execution latency in milliseconds
        
        Example:
            >>> # Non-streaming
            >>> result, latency = await service.execute_agent(
            ...     agent, "Hello", deps, history, session_id
            ... )
            >>> response = result.output
            
            >>> # Streaming
            >>> stream, latency = await service.execute_agent(
            ...     agent, "Hello", deps, history, session_id, streaming=True
            ... )
            >>> async for chunk in stream:
            ...     print(chunk)
        
        Notes:
        - Timing starts before agent.run() and ends after completion
        - Comprehensive logging of message history for debugging
        - For streaming, returns the stream object immediately (timing is start time)
        """
        start_time = datetime.now(UTC)
        
        # Log message history details for debugging
        logfire.info(
            'service.agent_execution.executing',
            session_id=session_id,
            message_preview=message[:100],
            message_history_length=len(message_history),
            message_history_types=[type(m).__name__ for m in message_history],
            message_history_first_parts=[
                type(p).__name__ for p in message_history[0].parts
            ] if message_history and hasattr(message_history[0], 'parts') else [],
            streaming=streaming
        )
        
        try:
            if streaming:
                # For streaming, return the stream immediately
                # Note: Timing represents stream start, not completion
                stream = agent.run_stream(
                    message,
                    deps=session_deps,
                    message_history=message_history
                )
                end_time = datetime.now(UTC)
                latency_ms = int((end_time - start_time).total_seconds() * 1000)
                
                logfire.info(
                    'service.agent_execution.stream_started',
                    session_id=session_id,
                    latency_ms=latency_ms
                )
                
                return stream, latency_ms
            else:
                # For non-streaming, wait for completion
                result = await agent.run(
                    message,
                    deps=session_deps,
                    message_history=message_history
                )
                end_time = datetime.now(UTC)
                latency_ms = int((end_time - start_time).total_seconds() * 1000)
                
                logfire.info(
                    'service.agent_execution.completed',
                    session_id=session_id,
                    latency_ms=latency_ms,
                    has_result=result is not None
                )
                
                return result, latency_ms
        
        except Exception as e:
            end_time = datetime.now(UTC)
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logfire.exception(
                'service.agent_execution.failed',
                session_id=session_id,
                latency_ms=latency_ms,
                error_type=type(e).__name__,
                streaming=streaming
            )
            raise


# Global service instance for dependency injection
_agent_execution_service: AgentExecutionService | None = None


def get_agent_execution_service() -> AgentExecutionService:
    """
    Get the global AgentExecutionService instance (singleton pattern).
    
    Provides a single instance of the AgentExecutionService for use throughout
    the application, ensuring consistent behavior and resource management.
    
    Returns:
        AgentExecutionService instance for agent operations
    
    Example:
        >>> service = get_agent_execution_service()
        >>> agent, deps, *rest = await service.setup_execution_context(session_id)
    
    Design Notes:
    - Singleton pattern ensures consistent service behavior
    - Thread-safe due to stateless service design
    - Can be easily mocked for testing
    """
    global _agent_execution_service
    if _agent_execution_service is None:
        _agent_execution_service = AgentExecutionService()
    return _agent_execution_service

