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
        
        # Get system_prompt from instance_config (multi-tenant) or fallback config (single-tenant)
        if instance_config is not None and 'system_prompt' in instance_config:
            system_prompt = instance_config['system_prompt']
        else:
            agent_config = await get_agent_config("simple_chat")
            system_prompt = agent_config.system_prompt
        
        logger.warning({
            "event": "agent_fallback_mode",
            "reason": "no_api_key",
            "model_used": model_name_simple,
            "cost_tracking": "disabled"
        })
        return Agent(
            model_name_simple,
            deps_type=SessionDependencies,
            system_prompt=system_prompt
        )
    
    # Load system prompt from instance_config (multi-tenant) or agent config (single-tenant)
    if instance_config is not None and 'system_prompt' in instance_config:
        # Multi-tenant mode: use the instance-specific system prompt
        system_prompt = instance_config['system_prompt']
        logger.info(f"Using system_prompt from instance_config (length: {len(system_prompt)})")
    else:
        # Single-tenant mode: load from agent config file
        agent_config = await get_agent_config("simple_chat")
        system_prompt = agent_config.system_prompt
        logger.info(f"Using system_prompt from agent config (length: {len(system_prompt)})")
    
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
    agent_instance_id: Optional[int] = None,  # Multi-tenant: agent instance ID for message attribution
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
        agent_instance_id: Agent instance ID for multi-tenant message attribution
        message_history: Optional pre-loaded message history
        instance_config: Optional instance-specific config for multi-tenant support
    
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
            
            # Extract costs from OpenRouter provider_details
            prompt_cost = 0.0
            completion_cost = 0.0
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
                    
                    # Extract total cost
                    vendor_cost = latest_message.provider_details.get('cost')
                    if vendor_cost is not None:
                        real_cost = float(vendor_cost)
                    
                    # Extract detailed costs from cost_details
                    cost_details = latest_message.provider_details.get('cost_details', {})
                    if cost_details:
                        prompt_cost = float(cost_details.get('upstream_inference_prompt_cost', 0.0))
                        completion_cost = float(cost_details.get('upstream_inference_completions_cost', 0.0))
                        logger.info(f"✅ OpenRouter cost extraction: total=${real_cost}, prompt=${prompt_cost}, completion=${completion_cost}")
        else:
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            prompt_cost = 0.0
            completion_cost = 0.0
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
            
            # Get tracking model from instance_config (multi-tenant) or cascade (single-tenant)
            if instance_config is not None:
                # Multi-tenant mode: use the instance-specific config
                tracking_model = instance_config.get("model_settings", {}).get("model", requested_model)
                logger.info(f"Using tracking_model from instance_config: {tracking_model}")
            else:
                # Single-tenant mode: use the centralized cascade
                tracking_model = model_settings["model"]
                logger.info(f"Using tracking_model from cascade: {tracking_model}")
            
            # Build full request body with actual messages sent to LLM
            request_messages = []
            # Add history messages (Pydantic AI ModelRequest/ModelResponse objects)
            if message_history:
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
                "content": message
            })
            
            # Build full response body with actual LLM response
            response_body_full = {
                "content": response_text,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                },
                "model": requested_model
            }
            
            # Add provider details if available
            new_messages = result.new_messages()
            if new_messages:
                latest_message = new_messages[-1]
                if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
                    response_body_full["provider_details"] = latest_message.provider_details
            
            # Load session to extract denormalized fields for cost attribution
            from ..models.session import Session
            from ..database import get_database_service
            db_service = get_database_service()
            async with db_service.get_session() as db_session:
                session_record = await db_session.get(Session, UUID(session_id))
                if not session_record:
                    logger.error({
                        "event": "non_streaming_session_not_found",
                        "session_id": session_id
                    })
                    raise ValueError(f"Session not found: {session_id}")
                
                # Extract denormalized fields for fast billing queries
                account_id = session_record.account_id
                account_slug = session_record.account_slug
                agent_instance_slug = instance_config.get("instance_name", "unknown") if instance_config else "simple_chat"
                agent_type = instance_config.get("agent_type", "simple_chat") if instance_config else "simple_chat"
            
            llm_request_id = await tracker.track_llm_request(
                session_id=UUID(session_id),
                provider="openrouter",
                model=tracking_model,
                request_body={
                    "messages": request_messages,
                    "model": requested_model,
                    "temperature": model_settings.get("temperature"),
                    "max_tokens": model_settings.get("max_tokens")
                },
                response_body=response_body_full,
                tokens={"prompt": prompt_tokens, "completion": completion_tokens, "total": total_tokens},
                cost_data={
                    "prompt_cost": prompt_cost,
                    "completion_cost": completion_cost,
                    "total_cost": Decimal(str(real_cost))
                },
                latency_ms=latency_ms,
                agent_instance_id=agent_instance_id,  # Multi-tenant: pass agent instance ID
                # Denormalized fields for fast billing queries (no JOINs)
                account_id=account_id,
                account_slug=account_slug,
                agent_instance_slug=agent_instance_slug,
                agent_type=agent_type,
                completion_status="complete"
            )
        
        # Save messages to database for multi-tenant message attribution
        if agent_instance_id is not None:
            from ..services.message_service import MessageService
            message_service = MessageService()
            
            try:
                # Save user message
                await message_service.save_message(
                    session_id=UUID(session_id),
                    agent_instance_id=agent_instance_id,
                    role="human",
                    content=message
                )
                
                # Save assistant response
                await message_service.save_message(
                    session_id=UUID(session_id),
                    agent_instance_id=agent_instance_id,
                    role="assistant",
                    content=response_text
                )
                
                logger.info({
                    "event": "messages_saved",
                    "session_id": session_id,
                    "agent_instance_id": agent_instance_id,
                    "user_message_length": len(message),
                    "assistant_message_length": len(response_text)
                })
            except Exception as msg_error:
                logger.error({
                    "event": "message_save_failed",
                    "error": str(msg_error),
                    "session_id": session_id,
                    "agent_instance_id": agent_instance_id
                })
                # Don't fail the request if message saving fails
            
    except Exception as e:
        # Log tracking errors but don't break the response
        logger.error(f"Cost tracking failed (non-critical): {e}")
        import traceback
        logger.debug(f"Cost tracking error traceback: {traceback.format_exc()}")
        llm_request_id = None
        prompt_cost = 0.0
        completion_cost = 0.0
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
            chunk_count = 0
            async for chunk in result.stream_text(delta=True):
                chunk_count += 1
                logger.debug({
                    "event": "streaming_chunk_received",
                    "session_id": session_id,
                    "chunk_number": chunk_count,
                    "chunk_length": len(chunk) if chunk else 0,
                    "chunk_preview": chunk[:50] if chunk else None
                })
                if chunk:  # Only append and yield non-empty chunks
                    chunks.append(chunk)
                    yield {"event": "message", "data": chunk}
            
            end_time = datetime.now(UTC)
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.info({
                "event": "streaming_loop_complete",
                "session_id": session_id,
                "total_chunks": chunk_count,
                "chunks_sent": len(chunks),
                "model": requested_model
            })
            
            # Get full response text
            response_text = "".join(chunks).strip()
            
            # Handle empty response - LLM returned tokens but no actual text content
            if not response_text:
                logger.error({
                    "event": "streaming_empty_response",
                    "session_id": session_id,
                    "model": requested_model,
                    "total_chunks_iterated": chunk_count,
                    "chunks_with_content": len(chunks),
                    "message": "LLM completed but returned no text content"
                })
                # Return error to client instead of trying to save empty message
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "message": "Model returned no content",
                        "retry": True,
                        "chunks_received": chunk_count
                    })
                }
                return  # Exit early, don't try to save messages
            
            # Track cost after stream completes
            usage_data = result.usage()
            
            if usage_data:
                prompt_tokens = getattr(usage_data, 'input_tokens', 0)
                completion_tokens = getattr(usage_data, 'output_tokens', 0)
                total_tokens = getattr(usage_data, 'total_tokens', prompt_tokens + completion_tokens)
                
                # Calculate costs using genai-prices
                # Pydantic AI doesn't populate provider_details for streaming responses,
                # so we use genai-prices to calculate costs from token usage
                # See: memorybank/lessons-learned/pydantic-ai-streaming-cost-tracking.md
                prompt_cost = 0.0
                completion_cost = 0.0
                total_cost = 0.0
                
                try:
                    from genai_prices import calc_price
                    
                    # Calculate price using the actual model from agent config
                    # Model name extracted from instance_config or global config (line 549)
                    price = calc_price(
                        usage=usage_data,
                        model_ref=requested_model,  # Use actual model from config
                        provider_id="openrouter"
                    )
                    
                    # Extract individual costs
                    prompt_cost = float(price.input_price)
                    completion_cost = float(price.output_price)
                    total_cost = float(price.total_price)
                    
                    logger.info({
                        "event": "streaming_cost_calculated",
                        "session_id": session_id,
                        "model": requested_model,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "prompt_cost": prompt_cost,
                        "completion_cost": completion_cost,
                        "total_cost": total_cost,
                        "method": "genai-prices"
                    })
                    
                except LookupError as e:
                    # Model not in genai-prices database - use fallback pricing from config
                    import yaml
                    import os
                    from pathlib import Path
                    
                    # Load fallback pricing from config file
                    # __file__ = backend/app/agents/simple_chat.py
                    # .parent = backend/app/agents/
                    # .parent = backend/app/
                    # .parent = backend/
                    config_dir = Path(__file__).parent.parent.parent / "config"
                    fallback_pricing_path = config_dir / "fallback_pricing.yaml"
                    
                    fallback_pricing_models = {}
                    if fallback_pricing_path.exists():
                        with open(fallback_pricing_path, 'r') as f:
                            fallback_config = yaml.safe_load(f)
                            fallback_pricing_models = fallback_config.get('models', {})
                    
                    if requested_model in fallback_pricing_models:
                        pricing = fallback_pricing_models[requested_model]
                        prompt_cost = (prompt_tokens / 1_000_000) * pricing["input_per_1m"]
                        completion_cost = (completion_tokens / 1_000_000) * pricing["output_per_1m"]
                        total_cost = prompt_cost + completion_cost
                        
                        logger.info({
                            "event": "streaming_cost_calculated",
                            "session_id": session_id,
                            "model": requested_model,
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "prompt_cost": prompt_cost,
                            "completion_cost": completion_cost,
                            "total_cost": total_cost,
                            "method": "fallback_pricing",
                            "source": pricing.get("source", "unknown"),
                            "config_file": str(fallback_pricing_path)
                        })
                    else:
                        logger.warning({
                            "event": "streaming_cost_calculation_failed",
                            "session_id": session_id,
                            "model": requested_model,
                            "error": f"Model not in genai-prices or fallback pricing: {e}",
                            "error_type": "LookupError",
                            "fallback": "zero_cost",
                            "suggestion": f"Add model to {fallback_pricing_path}"
                        })
                        
                except Exception as e:
                    logger.warning({
                        "event": "streaming_cost_calculation_failed",
                        "session_id": session_id,
                        "model": requested_model,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "fallback": "zero_cost"
                    })
                
                # Prepare cost_data dict for LLMRequestTracker
                cost_data = {
                    "prompt_cost": prompt_cost,
                    "completion_cost": completion_cost,
                    "total_cost": total_cost
                }
            else:
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
                prompt_cost = 0.0
                completion_cost = 0.0
                real_cost = 0.0
                cost_data = {
                    "prompt_cost": 0.0,
                    "completion_cost": 0.0,
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
                
                tracker = LLMRequestTracker()
                
                # Get tracking model from instance_config (multi-tenant) or cascade (single-tenant)
                if instance_config is not None:
                    # Multi-tenant mode: use the instance-specific config
                    model_settings = instance_config.get("model_settings", {})
                    tracking_model = model_settings.get("model", requested_model)
                    logger.info({
                        "event": "streaming_model_config_loaded",
                        "source": "instance_config",
                        "tracking_model": tracking_model,
                        "temperature": model_settings.get("temperature"),
                        "max_tokens": model_settings.get("max_tokens"),
                        "session_id": session_id
                    })
                else:
                    # Single-tenant mode: use the centralized cascade
                    from .config_loader import get_agent_model_settings
                    model_settings = await get_agent_model_settings("simple_chat")
                    tracking_model = model_settings["model"]
                    logger.info({
                        "event": "streaming_model_config_loaded",
                        "source": "cascade",
                        "tracking_model": tracking_model,
                        "temperature": model_settings.get("temperature"),
                        "max_tokens": model_settings.get("max_tokens"),
                        "session_id": session_id
                    })
                
                # Build full request body with actual messages sent to LLM
                request_messages = []
                # Add history messages (Pydantic AI ModelRequest/ModelResponse objects)
                if message_history:
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
                    "content": message
                })
                
                # Build full response body with actual LLM response
                response_body_full = {
                    "content": response_text,
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens
                    },
                    "model": requested_model,
                    "streaming": {
                        "chunks_sent": len(chunks)
                    }
                }
                
                # Add provider details if available
                new_messages = result.new_messages()
                if new_messages:
                    latest_message = new_messages[-1]
                    if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
                        response_body_full["provider_details"] = latest_message.provider_details
                
                # Load session to extract denormalized fields for cost attribution
                from ..models.session import Session
                from ..database import get_database_service
                db_service = get_database_service()
                async with db_service.get_session() as db_session:
                    session_record = await db_session.get(Session, UUID(session_id))
                    if not session_record:
                        logger.error({
                            "event": "streaming_session_not_found",
                            "session_id": session_id
                        })
                        raise ValueError(f"Session not found: {session_id}")
                    
                    # Extract denormalized fields for fast billing queries
                    account_id = session_record.account_id
                    account_slug = session_record.account_slug
                    agent_instance_slug = instance_config.get("instance_name", "unknown") if instance_config else "simple_chat"
                    agent_type = instance_config.get("agent_type", "simple_chat") if instance_config else "simple_chat"
                
                # Log tracking attempt for debugging
                logger.debug({
                    "event": "streaming_llm_tracking_start",
                    "session_id": session_id,
                    "tracking_model": tracking_model,
                    "requested_model": requested_model,
                    "tokens": {"prompt": prompt_tokens, "completion": completion_tokens, "total": total_tokens},
                    "cost": cost_data.get("total_cost", 0.0),
                    "has_model_settings": model_settings is not None,
                    "model_settings_keys": list(model_settings.keys()) if model_settings else [],
                    # Denormalized attribution
                    "account_slug": account_slug,
                    "agent_instance_slug": agent_instance_slug,
                    "agent_type": agent_type
                })
                
                llm_request_id = await tracker.track_llm_request(
                    session_id=UUID(session_id),
                    provider="openrouter",
                    model=tracking_model,
                    request_body={
                        "messages": request_messages,
                        "model": requested_model,
                        "temperature": model_settings.get("temperature"),
                        "max_tokens": model_settings.get("max_tokens"),
                        "stream": True
                    },
                    response_body=response_body_full,
                    tokens={
                        "prompt": prompt_tokens,
                        "completion": completion_tokens,
                        "total": total_tokens
                    },
                    cost_data=cost_data,
                    latency_ms=latency_ms,
                    agent_instance_id=agent_instance_id,
                    # Denormalized fields for fast billing queries (no JOINs)
                    account_id=account_id,
                    account_slug=account_slug,
                    agent_instance_slug=agent_instance_slug,
                    agent_type=agent_type,
                    completion_status="complete"
                )
                
                logger.info({
                    "event": "streaming_llm_tracked",
                    "session_id": session_id,
                    "llm_request_id": str(llm_request_id),
                    "model": tracking_model,
                    "total_cost": cost_data.get("total_cost", 0.0)
                })
            
            # Save messages to database
            logger.info({
                "event": "streaming_messages_saving",
                "session_id": session_id,
                "agent_instance_id": str(agent_instance_id),
                "user_message_length": len(message),
                "assistant_message_length": len(response_text),
                "completion_status": "complete"
            })
            
            message_service = get_message_service()
            
            # Save user message
            await message_service.save_message(
                session_id=UUID(session_id),
                agent_instance_id=agent_instance_id,
                role="human",
                content=message
            )
            
            # Save assistant response
            await message_service.save_message(
                session_id=UUID(session_id),
                agent_instance_id=agent_instance_id,
                role="assistant",
                content=response_text
            )
            
            logger.info({
                "event": "streaming_messages_saved",
                "session_id": session_id,
                "completion_status": "complete"
            })
            
            # Yield completion event
            yield {"event": "done", "data": ""}
            
    except Exception as e:
        import traceback
        logger.error({
            "event": "streaming_error",
            "session_id": session_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "chunks_sent": len(chunks),
            "has_instance_config": instance_config is not None,
            "traceback": traceback.format_exc()
        })
        
        # Save partial response if any chunks were sent
        if chunks:
            logger.info({
                "event": "streaming_partial_messages_saving",
                "session_id": session_id,
                "partial_response_length": len("".join(chunks)),
                "chunks_sent": len(chunks),
                "completion_status": "partial"
            })
            message_service = get_message_service()
            partial_response = "".join(chunks)
            
            # Save user message
            await message_service.save_message(
                session_id=UUID(session_id),
                agent_instance_id=agent_instance_id,
                role="human",
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
            
            logger.info({
                "event": "streaming_partial_messages_saved",
                "session_id": session_id,
                "completion_status": "partial",
                "error_type": type(e).__name__
            })
            
            # Note: Not tracking partial LLM requests since token counts are unavailable in error cases
        
        # Yield error event
        yield {"event": "error", "data": json.dumps({"message": str(e)})}
