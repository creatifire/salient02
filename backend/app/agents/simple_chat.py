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
from pydantic_ai.messages import ModelMessage
from app.agents.base.dependencies import SessionDependencies
from app.config import load_config
from app.agents.config_loader import get_agent_config  # Fixed: correct function name
from typing import List, Optional

# Global agent instance (lazy loaded)
_chat_agent = None

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
    """Simple chat function using Pydantic AI agent with YAML configuration."""
    
    # Create session dependencies properly (Fixed)
    session_deps = await SessionDependencies.create(
        session_id=session_id,
        user_id=None,  # Optional for simple chat
        max_history_messages=20
    )
    
    # Load agent configuration for model settings (Fixed: async call)
    agent_config = await get_agent_config("simple_chat")
    model_settings = agent_config.model_settings  # Fixed: direct attribute access
    
    # Get the agent (Fixed: await async function)
    agent = await get_chat_agent()
    
    # Run with proper parameters
    result = await agent.run(
        message, 
        deps=session_deps, 
        message_history=message_history,  # Pydantic AI handles message conversion
        # Model settings from agent config with fallback
        temperature=model_settings.get("temperature", 0.3),
        max_tokens=model_settings.get("max_tokens", 1024)
    )
    
    return {
        'response': result.output,  # Simple string response
        'messages': result.all_messages(),  # Full conversation history (Pydantic AI ModelMessage objects)
        'new_messages': result.new_messages(),  # Only new messages from this run
        'usage': result.usage()  # Built-in usage tracking
    }
