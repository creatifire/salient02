"""
Direct Pydantic AI Agent Implementation for Simple Chat.

This module implements a simple chat agent using Pydantic AI with:
- YAML configuration loading
- Session dependency injection  
- Dynamic model configuration from app.yaml and agent config
- Proper async/await patterns following Pydantic AI conventions

Key Components:
- create_simple_chat_agent(): Creates agent with YAML config
- get_chat_agent(): Lazy-loaded global agent instance
- simple_chat(): Main chat function with session handling

Dependencies:
- SessionDependencies from base.dependencies
- get_agent_config from config_loader
- load_config from app.config
"""

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart
from .openrouter import OpenRouterModel, create_openrouter_provider_with_cost_tracking
from .base.dependencies import SessionDependencies
from ..config import load_config
from .config_loader import get_agent_config  # Fixed: correct function name
from ..services.message_service import get_message_service
from ..services.llm_request_tracker import LLMRequestTracker
from typing import List, Optional
import uuid
from uuid import UUID
from datetime import datetime, UTC
import time
import os

# Global agent instance (lazy loaded)
# Global caching disabled for production reliability
# _chat_agent = None  # Removed: Always create fresh agents

async def load_conversation_history(session_id: str, max_messages: Optional[int] = None) -> List[ModelMessage]:
    """
    Load conversation history from database and convert to Pydantic AI format.
    
    Retrieves recent messages for the session and converts them to Pydantic AI
    ModelMessage objects that can be passed to agent.run() for context continuation.
    
    Args:
        session_id: Session ID to load history for
        max_messages: Maximum number of recent messages to load (None to use config)
    
    Returns:
        List of Pydantic AI ModelMessage objects in chronological order
    """
    # Get max_messages from config if not provided
    if max_messages is None:
        from ..agents.config_loader import get_agent_history_limit
        max_messages = await get_agent_history_limit("simple_chat")
    
    message_service = get_message_service()
    
    # Convert string session_id to UUID
    try:
        session_uuid = uuid.UUID(session_id)
    except (ValueError, TypeError):
        # If session_id is not a valid UUID, return empty history
        return []
    
    # Retrieve recent messages from database
    db_messages = await message_service.get_session_messages(
        session_id=session_uuid,
        limit=max_messages
    )
    
    if not db_messages:
        return []
    
    # Convert database messages to Pydantic AI ModelMessage format
    pydantic_messages = []
    for msg in db_messages:
        # Convert based on role
        if msg.role in ("human", "user"):
            # Create user request message
            pydantic_message = ModelRequest(
                parts=[UserPromptPart(
                    content=msg.content,
                    timestamp=msg.created_at or datetime.now()
                )]
            )
        elif msg.role == "assistant":
            # Create assistant response message  
            pydantic_message = ModelResponse(
                parts=[TextPart(content=msg.content)],
                usage=None,  # Historical messages don't have usage data
                model_name="simple-chat",  # Agent name for historical messages
                timestamp=msg.created_at or datetime.now()
            )
        else:
            # Skip system messages and unknown roles (Pydantic AI handles system messages)
            continue
            
        pydantic_messages.append(pydantic_message)
    
    return pydantic_messages

async def create_simple_chat_agent(instance_config: Optional[dict] = None) -> Agent:  # Fixed: async function
    """
    Create a simple chat agent with OpenRouter provider for cost tracking.
    
    Args:
        instance_config: Optional instance-specific configuration. If provided, uses this
                        instead of loading the global config. This enables multi-tenant
                        support where each instance can have different model settings.
    """
    config = instance_config if instance_config is not None else load_config()
    llm_config = config.get("model_settings", {})
    
    # Get OpenRouter configuration
    model_name = llm_config.get("model", "anthropic/claude-3.5-sonnet")
    api_key = llm_config.get("api_key") or os.getenv('OPENROUTER_API_KEY')
    
    # DEBUG: Log API key status
    from loguru import logger
    logger.info({
        "event": "agent_creation_debug",
        "model_name": model_name,
        "has_api_key_in_config": bool(llm_config.get("api_key")),
        "has_api_key_in_env": bool(os.getenv('OPENROUTER_API_KEY')),
        "final_api_key_found": bool(api_key),
        "api_key_source": "config" if llm_config.get("api_key") else ("env" if os.getenv('OPENROUTER_API_KEY') else "none")
    })
    
    if not api_key:
        # Fallback to simple model name for development without API key
        model_name_simple = f"openrouter:{model_name}"
        agent_config = await get_agent_config("simple_chat")
        logger.warning({
            "event": "agent_fallback_mode",
            "reason": "no_api_key",
            "model_used": model_name_simple,
            "cost_tracking": "disabled"
        })
        return Agent(
            model_name_simple,
            deps_type=SessionDependencies,
            system_prompt=agent_config.system_prompt
        )
    
    # Load agent-specific configuration for system prompt
    agent_config = await get_agent_config("simple_chat")
    system_prompt = agent_config.system_prompt  # Direct attribute access (AgentConfig is Pydantic model)
    
    # Use centralized model settings cascade with comprehensive monitoring
    # BUT: if instance_config was provided, use that instead of loading global config
    if instance_config is not None:
        # Multi-tenant mode: use the instance-specific config that was already extracted
        model_settings = llm_config
        model_name = llm_config.get("model", "anthropic/claude-3.5-sonnet")
        logger.info({
            "event": "instance_config_used",
            "model_settings": model_settings,
            "selected_model": model_name,
            "source": "instance_config"
        })
    else:
        # Single-tenant mode: use the centralized cascade
        from .config_loader import get_agent_model_settings
        model_settings = await get_agent_model_settings("simple_chat")
        model_name = model_settings["model"]
        logger.info({
            "event": "centralized_model_cascade",
            "model_settings": model_settings,
            "selected_model": model_name,
            "source": "global_config"
        })
    
    # Use OpenRouterModel with cost-tracking provider
    provider = create_openrouter_provider_with_cost_tracking(api_key)
    model = OpenRouterModel(
        model_name,  # Now properly uses agent-first cascade
        provider=provider
    )
    
    logger.info({
        "event": "agent_openrouter_provider_with_cost_tracking",
        "model_name": model_name,
        "provider_type": "OpenRouterProvider_CustomClient", 
        "api_key_masked": f"{api_key[:10]}..." if api_key else "none",
        "cost_tracking": "enabled_via_custom_asyncopenai_client",
        "usage_tracking": "always_included"
    })
    
    # Create agent with OpenRouterProvider (official pattern)
    return Agent(
        model,
        deps_type=SessionDependencies,
        system_prompt=system_prompt
    )

async def get_chat_agent(instance_config: Optional[dict] = None) -> Agent:  # Fixed: async function
    """
    Create a fresh chat agent instance.
    
    Note: Global caching disabled for production reliability.
    Configuration changes take effect immediately after server restart
    without requiring session cookie clearing or cache invalidation.
    
    Args:
        instance_config: Optional instance-specific configuration for multi-tenant support
    """
    # Always create fresh agent to pick up latest configuration
    # This ensures config changes work reliably in production
    return await create_simple_chat_agent(instance_config=instance_config)

async def simple_chat(
    message: str, 
    session_id: str,  # Fixed: simplified interface - create SessionDependencies internally
    message_history: Optional[List[ModelMessage]] = None,  # Fixed: proper type annotation
    instance_config: Optional[dict] = None  # Multi-tenant: instance-specific configuration
) -> dict:
    """
    Simple chat function using Pydantic AI agent with YAML configuration.
    
    Automatically loads conversation history from database if not provided,
    enabling multi-turn conversations with context continuity.
    
    Args:
        message: User message to process
        session_id: Session ID for conversation context
        message_history: Optional pre-loaded message history
        instance_config: Optional instance-specific config for multi-tenant support
    
    Args:
        message: User message to process
        session_id: Session ID for conversation continuity
        message_history: Optional pre-loaded message history (auto-loaded if None)
    
    Returns:
        dict with response, messages, new_messages, and usage data
    """
    from loguru import logger
    
    # Get history_limit from agent-first configuration cascade
    from .config_loader import get_agent_history_limit
    default_history_limit = await get_agent_history_limit("simple_chat")
    
    # Create session dependencies properly (Fixed)
    session_deps = await SessionDependencies.create(
        session_id=session_id,
        user_id=None,  # Optional for simple chat
        history_limit=default_history_limit
    )
    
    # Load model settings using centralized cascade (Fixed: comprehensive cascade)
    from .config_loader import get_agent_model_settings
    model_settings = await get_agent_model_settings("simple_chat")
    
    # Load conversation history if not provided (TASK 0017-003)
    if message_history is None:
        # Use centralized cascade function for consistent behavior
        message_history = await load_conversation_history(
            session_id=session_id,
            max_messages=None  # load_conversation_history will use get_agent_history_limit internally
        )
    
    # Get the agent (Fixed: await async function)
    # Pass instance_config for multi-tenant support
    agent = await get_chat_agent(instance_config=instance_config)
    
    # Extract requested model for debugging
    config_to_use = instance_config if instance_config is not None else load_config()
    requested_model = config_to_use.get("model_settings", {}).get("model", "unknown")
    
    # Pure Pydantic AI agent execution
    start_time = datetime.now(UTC)
    
    try:
        # Execute agent with Pydantic AI
        result = await agent.run(message, deps=session_deps, message_history=message_history)
        end_time = datetime.now(UTC)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Extract response and usage data
        response_text = result.output
        usage_data = result.usage() if hasattr(result, 'usage') else None
        
        if usage_data:
            prompt_tokens = getattr(usage_data, 'input_tokens', 0)
            completion_tokens = getattr(usage_data, 'output_tokens', 0)
            total_tokens = getattr(usage_data, 'total_tokens', prompt_tokens + completion_tokens)
            
            # Extract cost from OpenRouterModel vendor_details
            real_cost = 0.0
            
            # Get the latest message response with OpenRouter metadata
            new_messages = result.new_messages()
            if new_messages:
                latest_message = new_messages[-1]  # Last message (assistant response)
                if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
                    # DEBUG: Log full provider_details to see what OpenRouter returned
                    logger.warning({
                        "event": "openrouter_provider_details_debug",
                        "provider_details": latest_message.provider_details,
                        "requested_model": requested_model
                    })
                    
                    vendor_cost = latest_message.provider_details.get('cost')
                    if vendor_cost is not None:
                        real_cost = float(vendor_cost)
                        logger.info(f"✅ OpenRouterModel cost extraction: ${real_cost}")
        else:
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            real_cost = 0.0
            
        # Log OpenRouterModel results
        logger.info({
            "event": "openrouter_model_execution",
            "session_id": session_id,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens
            },
            "real_cost": real_cost,
            "method": "openrouter_model_vendor_details",
            "cost_tracking": "enabled",
            "cost_found": real_cost > 0,
            "latency_ms": latency_ms
        })
        
        # Store cost data using LLMRequestTracker
        llm_request_id = None  # Initialize to None for cases where tracking is skipped
        if prompt_tokens > 0 or completion_tokens > 0:
            from decimal import Decimal
            tracker = LLMRequestTracker()
            
            # Use centralized model settings for tracking consistency
            tracking_model = model_settings["model"]
            
            llm_request_id = await tracker.track_llm_request(
                session_id=UUID(session_id),
                provider="openrouter",
                model=tracking_model,
                request_body={
                    "message_length": len(message), 
                    "has_history": len(message_history) > 0 if message_history else False,
                    "method": "direct_openrouter"
                },
                response_body={
                    "response_length": len(response_text),
                    "openrouter_cost": real_cost
                },
                tokens={"prompt": prompt_tokens, "completion": completion_tokens, "total": total_tokens},
                cost_data={
                    "unit_cost_prompt": 0.0,
                    "unit_cost_completion": 0.0,
                    "total_cost": Decimal(str(real_cost))
                },
                latency_ms=latency_ms
            )
            
    except Exception as e:
        # Log tracking errors but don't break the response
        logger.error(f"Cost tracking failed (non-critical): {e}")
        import traceback
        logger.debug(f"Cost tracking error traceback: {traceback.format_exc()}")
        llm_request_id = None
        real_cost = 0.0
        response_text = "Error processing request"
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    # Create usage data object for compatibility
    class UsageData:
        def __init__(self, prompt_tokens, completion_tokens, total_tokens):
            self.input_tokens = prompt_tokens
            self.output_tokens = completion_tokens
            self.total_tokens = total_tokens
            self.requests = 1
            self.details = {}
    
    usage_obj = UsageData(prompt_tokens, completion_tokens, total_tokens)
    
    # Get session stats for continuity monitoring
    from ..services.agent_session import get_session_stats
    session_stats = await get_session_stats(session_id)
    
    return {
        'response': response_text,  # Response from Pydantic AI
        'usage': usage_obj,  # Compatible usage object
        'llm_request_id': str(llm_request_id) if llm_request_id else None,
        # Cost tracking data (via OpenRouterModel)
        'cost_tracking': {
            'real_cost': real_cost,
            'method': 'openrouter_model_vendor_details',
            'provider': 'OpenRouterProvider',
            'cost_found': real_cost > 0,
            'status': 'enabled'
        },
        # Session continuity monitoring
        'session_continuity': session_stats
    }


async def simple_chat_stream(
    message: str,
    session_id: str,
    agent_instance_id: UUID,
    message_history: Optional[List[ModelMessage]] = None,
    instance_config: Optional[dict] = None
):
    """
    Streaming version of simple_chat using Pydantic AI agent.run_stream().
    
    Yields SSE-formatted events with incremental text chunks.
    
    Args:
        message: User message to process
        session_id: Session ID for conversation context
        agent_instance_id: Agent instance ID for message attribution
        message_history: Optional pre-loaded message history
        instance_config: Optional instance-specific config for multi-tenant support
        
    Yields:
        dict: SSE events with format:
            - {"event": "message", "data": chunk} - Text chunks
            - {"event": "done", "data": ""} - Completion
            - {"event": "error", "data": json.dumps({"message": "..."})} - Errors
    """
    from loguru import logger
    import json
    
    # Get history_limit from agent-first configuration cascade
    from .config_loader import get_agent_history_limit
    default_history_limit = await get_agent_history_limit("simple_chat")
    
    # Create session dependencies
    session_deps = await SessionDependencies.create(
        session_id=session_id,
        user_id=None,
        history_limit=default_history_limit
    )
    
    # Load conversation history if not provided
    if message_history is None:
        message_history = await load_conversation_history(
            session_id=session_id,
            max_messages=None
        )
    
    # Get the agent (pass instance_config for multi-tenant support)
    agent = await get_chat_agent(instance_config=instance_config)
    
    # Extract requested model for logging
    config_to_use = instance_config if instance_config is not None else load_config()
    requested_model = config_to_use.get("model_settings", {}).get("model", "unknown")
    
    chunks = []
    start_time = datetime.now(UTC)
    
    try:
        # Execute agent with streaming
        async with agent.run_stream(message, deps=session_deps, message_history=message_history) as result:
            # Stream with delta=True for incremental chunks only
            async for chunk in result.stream_text(delta=True):
                chunks.append(chunk)
                yield {"event": "message", "data": chunk}
            
            end_time = datetime.now(UTC)
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Get full response text
            response_text = "".join(chunks)
            
            # Track cost after stream completes
            usage_data = result.usage()
            
            if usage_data:
                prompt_tokens = getattr(usage_data, 'input_tokens', 0)
                completion_tokens = getattr(usage_data, 'output_tokens', 0)
                total_tokens = getattr(usage_data, 'total_tokens', prompt_tokens + completion_tokens)
                
                # Extract cost from OpenRouterModel vendor_details
                real_cost = 0.0
                new_messages = result.new_messages()
                if new_messages:
                    latest_message = new_messages[-1]
                    if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
                        vendor_cost = latest_message.provider_details.get('cost')
                        if vendor_cost is not None:
                            real_cost = float(vendor_cost)
                
                # Prepare cost_data dict for LLMRequestTracker
                cost_data = {
                    "unit_cost_prompt": 0.0,  # Not provided by OpenRouter in streaming
                    "unit_cost_completion": 0.0,
                    "total_cost": real_cost
                }
            else:
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
                real_cost = 0.0
                cost_data = {
                    "unit_cost_prompt": 0.0,
                    "unit_cost_completion": 0.0,
                    "total_cost": 0.0
                }
            
            # Log streaming execution
            logger.info({
                "event": "openrouter_model_streaming",
                "session_id": session_id,
                "chunks_sent": len(chunks),
                "tokens": {
                    "prompt": prompt_tokens,
                    "completion": completion_tokens,
                    "total": total_tokens
                },
                "real_cost": cost_data["total_cost"],
                "latency_ms": latency_ms,
                "completion_status": "complete"
            })
            
            # Store cost data using LLMRequestTracker
            llm_request_id = None
            if prompt_tokens > 0 or completion_tokens > 0:
                from decimal import Decimal
                from .config_loader import get_agent_model_settings
                
                tracker = LLMRequestTracker()
                model_settings = await get_agent_model_settings("simple_chat")
                tracking_model = model_settings["model"]
                
                llm_request_id = await tracker.track_llm_request(
                    session_id=UUID(session_id),
                    provider="openrouter",
                    model=tracking_model,
                    request_body={
                        "message_length": len(message),
                        "has_history": len(message_history) > 0 if message_history else False,
                        "method": "streaming_openrouter"
                    },
                    response_body={
                        "response_length": len(response_text),
                        "chunks_sent": len(chunks)
                    },
                    tokens={
                        "prompt": prompt_tokens,
                        "completion": completion_tokens,
                        "total": total_tokens
                    },
                    cost_data=cost_data,
                    latency_ms=latency_ms,
                    agent_instance_id=agent_instance_id
                )
            
            # Save messages to database
            message_service = get_message_service()
            
            # Save user message
            await message_service.save_message(
                session_id=UUID(session_id),
                agent_instance_id=agent_instance_id,
                role="user",
                content=message
            )
            
            # Save assistant response
            await message_service.save_message(
                session_id=UUID(session_id),
                agent_instance_id=agent_instance_id,
                role="assistant",
                content=response_text
            )
            
            # Yield completion event
            yield {"event": "done", "data": ""}
            
    except Exception as e:
        logger.error({
            "event": "streaming_error",
            "session_id": session_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "chunks_sent": len(chunks)
        })
        
        # Save partial response if any chunks were sent
        if chunks:
            message_service = get_message_service()
            partial_response = "".join(chunks)
            
            # Save user message
            await message_service.save_message(
                session_id=UUID(session_id),
                agent_instance_id=agent_instance_id,
                role="user",
                content=message
            )
            
            # Save partial assistant response with metadata
            await message_service.save_message(
                session_id=UUID(session_id),
                agent_instance_id=agent_instance_id,
                role="assistant",
                content=partial_response,
                metadata={
                    "partial": True,
                    "error": str(e),
                    "completion_status": "partial",
                    "chunks_received": len(chunks)
                }
            )
            
            # Note: Not tracking partial LLM requests since token counts are unavailable in error cases
        
        # Yield error event
        yield {"event": "error", "data": json.dumps({"message": str(e)})}
