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
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from .base.dependencies import SessionDependencies
from ..config import load_config
from .config_loader import get_agent_config  # Fixed: correct function name
from ..services.message_service import get_message_service
from ..services.llm_request_tracker import LLMRequestTracker
from ..services.agent_session import load_agent_conversation, get_session_stats
from typing import List, Optional
import uuid
from uuid import UUID
from datetime import datetime
import time
import os

# Global agent instance (lazy loaded)
_chat_agent = None

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
        config = load_config()
        chat_config = config.get("chat", {})
        max_messages = chat_config.get("history_limit", 20)  # Default to 20 for agent context
    
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

async def create_simple_chat_agent() -> Agent:  # Fixed: async function
    """Create a simple chat agent with OpenRouter provider for cost tracking."""
    config = load_config()
    llm_config = config.get("llm", {})
    
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
    
    # Load agent-specific configuration to get model settings and system prompt
    agent_config = await get_agent_config("simple_chat")
    model_settings = agent_config.model_settings if hasattr(agent_config, 'model_settings') and agent_config.model_settings else {}
    system_prompt = agent_config.system_prompt  # Direct attribute access (AgentConfig is Pydantic model)
    
    # 🎯 OFFICIAL: Follow Pydantic AI documentation exactly
    model = OpenAIChatModel(
        model_name,  # First positional argument, not model_name=
        provider=OpenRouterProvider(api_key=api_key)
    )
    
    logger.info({
        "event": "agent_openrouter_provider_breakthrough",
        "model_name": model_name,
        "provider_type": "OpenRouterProvider", 
        "api_key_masked": f"{api_key[:10]}..." if api_key else "none",
        "cost_tracking": "enabled_via_hybrid_solution"
    })
    
    # Create agent with OpenRouterProvider (official pattern)
    return Agent(
        model,
        deps_type=SessionDependencies,
        system_prompt=system_prompt
    )

async def get_chat_agent() -> Agent:  # Fixed: async function
    """Get or create the global chat agent instance."""
    global _chat_agent
    if _chat_agent is None:
        _chat_agent = await create_simple_chat_agent()  # Fixed: await async function
    return _chat_agent

async def simple_chat(
    message: str, 
    session_id: str,  # Fixed: simplified interface - create SessionDependencies internally
    message_history: Optional[List[ModelMessage]] = None  # Fixed: proper type annotation
) -> dict:
    """
    Simple chat function using Pydantic AI agent with YAML configuration.
    
    Automatically loads conversation history from database if not provided,
    enabling multi-turn conversations with context continuity.
    
    Args:
        message: User message to process
        session_id: Session ID for conversation continuity
        message_history: Optional pre-loaded message history (auto-loaded if None)
    
    Returns:
        dict with response, messages, new_messages, and usage data
    """
    
    # Get history_limit from config for session dependencies
    config = load_config()
    chat_config = config.get("chat", {})
    default_history_limit = chat_config.get("history_limit", 20)
    
    # Create session dependencies properly (Fixed)
    session_deps = await SessionDependencies.create(
        session_id=session_id,
        user_id=None,  # Optional for simple chat
        history_limit=default_history_limit
    )
    
    # Load agent configuration for model settings (Fixed: async call)
    agent_config = await get_agent_config("simple_chat")
    model_settings = agent_config.model_settings  # Fixed: direct attribute access
    
    # Load conversation history if not provided (TASK 0017-003-005: Agent Session Service Integration)
    if message_history is None:
        message_history = await load_agent_conversation(session_id)
        
        # TASK 0017-003-005-03: Log session bridging for analytics
        from loguru import logger
        logger.info({
            "event": "agent_session_bridging",
            "session_id": session_id,
            "loaded_messages": len(message_history),
            "cross_endpoint_continuity": len(message_history) > 0,
            "agent_type": "simple_chat",
            "bridging_method": "agent_session_service"
        })
    
    # Get the agent (Fixed: await async function)
    agent = await get_chat_agent()
    
    # STEP 1 & 2: Pydantic AI + OpenRouter Integration with Cost Tracking
    start_time = datetime.utcnow()
    
    # 🎯 BREAKTHROUGH: Single-call solution with direct OpenRouter client for cost data
    llm_request_id = None
    real_cost = 0.0
    response_text = ""
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    latency_ms = 0
    
    # Check if we have an OpenRouterProvider to access its client
    openrouter_api_key = config.get("llm", {}).get("api_key") or os.getenv('OPENROUTER_API_KEY')
    
    try:
        if openrouter_api_key:
            # 🎯 Single-call breakthrough: Direct OpenRouter client with cost data
            from pydantic_ai.providers.openrouter import OpenRouterProvider
            provider = OpenRouterProvider(api_key=openrouter_api_key)
            direct_client = provider.client
            
            # Convert message history to API format
            api_messages = []
            if message_history:
                for msg in message_history:
                    if hasattr(msg, 'parts') and msg.parts:
                        for part in msg.parts:
                            if hasattr(part, 'content'):
                                role = "assistant" if isinstance(msg, ModelResponse) else "user"
                                api_messages.append({"role": role, "content": part.content})
            
            # Add current message
            api_messages.append({"role": "user", "content": message})
            
            # Make single cost-enabled call
            response = await direct_client.chat.completions.create(
                model=config.get("llm", {}).get("model", "anthropic/claude-3.5-sonnet"),
                messages=api_messages,
                extra_body={"usage": {"include": True}},  # 🔑 Critical for OpenRouter cost
                max_tokens=model_settings.get('max_tokens', 1000) if model_settings else 1000,
                temperature=model_settings.get('temperature', 0.7) if model_settings else 0.7
            )
            
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Extract response and accurate cost data
            response_text = response.choices[0].message.content
            
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            real_cost = float(response.usage.cost) if hasattr(response.usage, 'cost') else 0.0
            
        else:
            # Fallback: Use Pydantic AI without cost data
            result = await agent.run(message, deps=session_deps, message_history=message_history)
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            response_text = result.output
            usage_data = result.usage() if hasattr(result, 'usage') else None
            
            if usage_data:
                prompt_tokens = getattr(usage_data, 'input_tokens', 0)
                completion_tokens = getattr(usage_data, 'output_tokens', 0)
                total_tokens = getattr(usage_data, 'total_tokens', prompt_tokens + completion_tokens)
            
        # Log the breakthrough cost tracking results
        from loguru import logger
        logger.info({
            "event": "breakthrough_single_call_cost_tracking",
            "session_id": session_id,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens
            },
            "real_cost": real_cost,
            "cost_found": real_cost > 0,
            "method": "direct_openrouter_client_single_call" if openrouter_api_key else "pydantic_ai_fallback",
            "latency_ms": latency_ms
        })
        
        # Store cost data using LLMRequestTracker
        if prompt_tokens > 0 or completion_tokens > 0:
            from decimal import Decimal
            tracker = LLMRequestTracker()
            llm_request_id = await tracker.track_llm_request(
                session_id=UUID(session_id),
                provider="openrouter",
                model=config.get("llm", {}).get("model", "unknown"),
                request_body={
                    "message_length": len(message), 
                    "has_history": len(message_history) > 0 if message_history else False,
                    "method": "breakthrough_single_call_openrouter"
                },
                response_body={
                    "response_length": len(response_text),
                    "openrouter_cost": real_cost,
                    "breakthrough_solution": True
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
        from loguru import logger
        logger.error(f"Breakthrough cost tracking failed (non-critical): {e}")
        llm_request_id = None
        real_cost = 0.0
        response_text = "Error processing request"
    
    # Create usage data object for compatibility
    class UsageData:
        def __init__(self, prompt_tokens, completion_tokens, total_tokens):
            self.input_tokens = prompt_tokens
            self.output_tokens = completion_tokens
            self.total_tokens = total_tokens
            self.requests = 1
            self.details = {}
    
    usage_obj = UsageData(prompt_tokens, completion_tokens, total_tokens)
    
    # TASK 0017-003-005-02: Add session continuity stats
    session_stats = await get_session_stats(session_id)
    
    return {
        'response': response_text,  # Direct response from OpenRouter
        'usage': usage_obj,  # Compatible usage object
        'llm_request_id': str(llm_request_id) if llm_request_id else None,
        # 🎯 BREAKTHROUGH: Real OpenRouter cost tracking data
        'cost_tracking': {
            'real_cost': real_cost,
            'method': 'breakthrough_single_call_openrouter',
            'provider': 'OpenRouterProvider',
            'cost_found': real_cost > 0,
            'breakthrough_solution': True
        },
        # TASK 0017-003-005: Agent Conversation Loading - Session continuity monitoring
        'session_continuity': session_stats
    }
