"""
Shared business logic helpers for chat agents.

This module consolidates duplicated patterns from simple_chat.py to reduce
code duplication and provide reusable functions for chat operations.

Extracted from BUG-0017-009 refactoring.
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
from ..services.message_service import get_message_service
from ..database import get_database_service
from dataclasses import dataclass
import logfire


def build_request_messages(message_history: List[ModelMessage], current_message: str) -> List[Dict[str, str]]:
    """
    Build request messages from conversation history.
    
    Converts Pydantic AI ModelMessage objects to the format expected by
    LLM request tracking and other systems.
    
    Args:
        message_history: List of Pydantic AI ModelMessage objects
        current_message: Current user message to append
        
    Returns:
        List of message dictionaries with role and content
        
    Example:
        >>> messages = build_request_messages(history, "Hello")
        >>> messages
        [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}, {"role": "user", "content": "Hello"}]
    """
    request_messages = []
    
    for msg in message_history:
        # Determine role and extract content from Pydantic AI message objects
        if isinstance(msg, ModelRequest):
            role = "user"
            content = msg.parts[0].content if msg.parts else ""
        elif isinstance(msg, ModelResponse):
            role = "assistant"
            content = msg.parts[0].content if msg.parts else ""
        else:
            continue
        
        request_messages.append({
            "role": role,
            "content": content
        })
    
    # Add current user message
    request_messages.append({
        "role": "user",
        "content": current_message
    })
    
    return request_messages


def build_response_body(
    response_text: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    requested_model: str,
    result: Any,
    streaming_chunks: Optional[int] = None
) -> Dict[str, Any]:
    """
    Build response body with usage information and provider details.
    
    Consolidates response body construction for both streaming and non-streaming responses.
    
    Args:
        response_text: The LLM response text
        prompt_tokens: Number of prompt tokens used
        completion_tokens: Number of completion tokens generated
        total_tokens: Total tokens (prompt + completion)
        requested_model: Model identifier requested
        result: Pydantic AI result object (for extracting provider details)
        streaming_chunks: Optional number of chunks sent (for streaming responses)
        
    Returns:
        Response body dictionary with usage and provider details
    """
    response_body = {
        "content": response_text,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        },
        "model": requested_model
    }
    
    # Add streaming information if provided
    if streaming_chunks is not None:
        response_body["streaming"] = {
            "chunks_sent": streaming_chunks
        }
    
    # Add provider details if available
    new_messages = result.new_messages()
    if new_messages:
        latest_message = new_messages[-1]
        if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
            response_body["provider_details"] = latest_message.provider_details
    
    return response_body


async def extract_session_account_info(session_id: UUID) -> Tuple[Optional[UUID], Optional[str]]:
    """
    Extract account fields from session for cost attribution.
    
    Loads session from database and extracts denormalized account_id and account_slug
    fields for proper cost attribution and tracking.
    
    Args:
        session_id: Session UUID to load
        
    Returns:
        Tuple of (account_id, account_slug)
        
    Raises:
        Any database errors are logged and re-raised
    """
    from ..services.session_extractor import get_session_account_fields as _get_fields
    
    db_service = get_database_service()
    async with db_service.get_session() as db_session:
        account_id, account_slug = await _get_fields(db_session, session_id)
        return account_id, account_slug


async def save_message_pair(
    session_id: str,
    user_message: str,
    assistant_message: str,
    requested_model: str,
    account_id: Optional[UUID] = None,
    account_slug: Optional[str] = None,
    agent_instance_slug: Optional[str] = None
) -> None:
    """
    Save user-assistant message pair to database.
    
    Consolidates message saving logic for both streaming and non-streaming responses.
    Handles account_id conversion and provides detailed logging.
    
    Args:
        session_id: Session ID (will be converted to UUID)
        user_message: User's message content
        assistant_message: Assistant's response content
        requested_model: Model identifier used
        account_id: Optional account UUID for multi-tenant tracking
        account_slug: Optional account slug for multi-tenant tracking
        agent_instance_slug: Optional agent instance identifier
        
    Raises:
        Logs errors but does not re-raise to prevent message save failures from breaking the chat flow
    """
    try:
        message_service = get_message_service()
        
        # Convert string session_id to UUID
        try:
            session_uuid = UUID(session_id)
        except (ValueError, TypeError) as e:
            logfire.error(
                'chat.save_message_pair.invalid_session_id',
                session_id=session_id,
                error=str(e)
            )
            return
        
        # Convert account_id to UUID if provided as string
        account_uuid = None
        if account_id:
            try:
                account_uuid = UUID(str(account_id)) if not isinstance(account_id, UUID) else account_id
            except (ValueError, TypeError) as e:
                logfire.warn(
                    'chat.save_message_pair.invalid_account_id',
                    account_id=account_id,
                    error=str(e)
                )
        
        # Save user message
        await message_service.save_message(
            session_id=session_uuid,
            role="user",
            content=user_message,
            model=requested_model,
            account_id=account_uuid,
            account_slug=account_slug,
            agent_instance_slug=agent_instance_slug
        )
        
        # Save assistant message
        await message_service.save_message(
            session_id=session_uuid,
            role="assistant",
            content=assistant_message,
            model=requested_model,
            account_id=account_uuid,
            account_slug=account_slug,
            agent_instance_slug=agent_instance_slug
        )
        
        logfire.info(
            'chat.message_pair_saved',
            session_id=str(session_uuid),
            account_slug=account_slug,
            agent_instance_slug=agent_instance_slug
        )
        
    except Exception as e:
        # Log error but don't raise - message save failures shouldn't break chat flow
        logfire.error(
            'chat.save_message_pair.error',
            session_id=session_id,
            error=str(e),
            error_type=type(e).__name__
        )


@dataclass
class ChatExecutionContext:
    """
    Consolidated execution context for chat operations.
    
    Centralizes all initialization and config loading for simple_chat() and 
    simple_chat_stream() functions, eliminating scattered config access patterns.
    """
    session_deps: Any  # SessionDependencies
    message_history: List[ModelMessage]
    agent: Any  # Pydantic AI Agent
    requested_model: str
    model_settings: Dict[str, Any]


async def initialize_chat_context(
    session_id: str,
    agent_instance_id: Optional[int],
    account_id: Optional[UUID],
    instance_config: Optional[dict],
    message_history: Optional[List[ModelMessage]] = None
) -> ChatExecutionContext:
    """
    Initialize all chat execution context in one place.
    
    Consolidates configuration loading, session dependency creation, history loading,
    and agent initialization - eliminating duplicated initialization logic between
    simple_chat() and simple_chat_stream() functions.
    
    Args:
        session_id: Session ID for conversation context
        agent_instance_id: Agent instance ID for multi-tenant
        account_id: Account UUID for multi-tenant
        instance_config: Instance-specific configuration
        message_history: Optional pre-loaded message history
        
    Returns:
        ChatExecutionContext with all initialized components
        
    Example:
        >>> ctx = await initialize_chat_context(session_id, agent_id, account_id, config)
        >>> result = await ctx.agent.run(message, deps=ctx.session_deps, message_history=ctx.message_history)
    """
    from .config_loader import get_agent_history_limit, get_agent_model_settings
    from ..config import load_config
    
    # Load history_limit from agent-first configuration cascade
    default_history_limit = await get_agent_history_limit("simple_chat")
    
    # Create session dependencies with agent config for tools
    from .base.dependencies import SessionDependencies
    session_deps = await SessionDependencies.create(
        session_id=session_id,
        user_id=None,  # Optional for simple chat
        history_limit=default_history_limit
    )
    
    # Add agent-specific fields for tool access
    session_deps.agent_config = instance_config
    session_deps.agent_instance_id = agent_instance_id
    
    # Convert account_id to Python UUID (simplified)
    if account_id is not None:
        session_deps.account_id = UUID(str(account_id)) if account_id and not isinstance(account_id, UUID) else account_id
    else:
        session_deps.account_id = None
    
    # Load model settings using centralized cascade
    model_settings = await get_agent_model_settings("simple_chat")
    
    # Load conversation history if not provided
    if message_history is None:
        from ..agents.simple_chat import load_conversation_history
        message_history = await load_conversation_history(
            session_id=session_id,
            max_messages=None  # Uses get_agent_history_limit internally
        )
    
    # Get the agent (pass instance_config and account_id for multi-tenant support)
    from ..agents.simple_chat import get_chat_agent
    agent = await get_chat_agent(instance_config=instance_config, account_id=account_id)
    
    # Extract requested model for logging and tracking
    config_to_use = instance_config if instance_config is not None else load_config()
    requested_model = config_to_use.get("model_settings", {}).get("model", "unknown")
    
    return ChatExecutionContext(
        session_deps=session_deps,
        message_history=message_history,
        agent=agent,
        requested_model=requested_model,
        model_settings=model_settings
    )

