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
from app.agents.base.dependencies import SessionDependencies
from app.config import load_config
from app.agents.config_loader import get_agent_config  # Fixed: correct function name
from app.services.message_service import get_message_service
from typing import List, Optional
import uuid
from datetime import datetime

# Global agent instance (lazy loaded)
_chat_agent = None

async def load_conversation_history(session_id: str, max_messages: int = 20) -> List[ModelMessage]:
    """
    Load conversation history from database and convert to Pydantic AI format.
    
    Retrieves recent messages for the session and converts them to Pydantic AI
    ModelMessage objects that can be passed to agent.run() for context continuation.
    
    Args:
        session_id: Session ID to load history for
        max_messages: Maximum number of recent messages to load
    
    Returns:
        List of Pydantic AI ModelMessage objects in chronological order
    """
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
    """Create a simple chat agent with dynamic configuration from YAML."""
    config = load_config()
    llm_config = config.get("llm", {})
    
    # Build model name from config: openrouter:deepseek/deepseek-chat-v3.1
    provider = llm_config.get("provider", "openrouter")
    model = llm_config.get("model", "deepseek/deepseek-chat-v3.1")
    model_name = f"{provider}:{model}"
    
    # Load agent-specific configuration (ASYNC call - Fixed)
    agent_config = await get_agent_config("simple_chat")  # Fixed: async call with correct function name
    system_prompt = agent_config.system_prompt  # Fixed: direct attribute access (AgentConfig is Pydantic model)
    
    return Agent(
        model_name,
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
    
    # Create session dependencies properly (Fixed)
    session_deps = await SessionDependencies.create(
        session_id=session_id,
        user_id=None,  # Optional for simple chat
        max_history_messages=20
    )
    
    # Load agent configuration for model settings (Fixed: async call)
    agent_config = await get_agent_config("simple_chat")
    model_settings = agent_config.model_settings  # Fixed: direct attribute access
    
    # Load conversation history if not provided (TASK 0017-003)
    if message_history is None:
        # Get max_history_messages from agent config with fallback
        max_history_messages = 20  # Default fallback
        if hasattr(agent_config, 'context_management') and agent_config.context_management:
            max_history_messages = agent_config.context_management.get('max_history_messages', 20)
        
        message_history = await load_conversation_history(
            session_id=session_id,
            max_messages=max_history_messages
        )
    
    # Get the agent (Fixed: await async function)
    agent = await get_chat_agent()
    
    # Run with proper parameters (Pydantic AI handles model settings via agent configuration)
    result = await agent.run(
        message, 
        deps=session_deps, 
        message_history=message_history  # Auto-loaded or provided message history
    )
    
    return {
        'response': result.output,  # Simple string response
        'messages': result.all_messages(),  # Full conversation history (Pydantic AI ModelMessage objects)
        'new_messages': result.new_messages(),  # Only new messages from this run
        'usage': result.usage()  # Built-in usage tracking
    }
