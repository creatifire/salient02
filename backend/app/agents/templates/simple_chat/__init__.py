"""
Simple Chat Agent Template.

This module provides a foundational Pydantic AI-powered chat agent with basic 
functionality for structured responses and session integration.

Key Components:
- ChatResponse: Simple response model for text-based interactions
- SimpleChatAgent: Basic conversational agent using SessionDependencies
- Factory functions: Configuration-driven agent creation and caching

Usage:
    # Simple factory creation
    from app.agents.templates.simple_chat import create_simple_chat_agent
    
    agent, session_deps = await create_simple_chat_agent(session_id="123")
    response = await agent.chat("Hello!", deps=session_deps)
    print(response.message)
    
    # Direct agent creation
    from app.agents.templates.simple_chat import SimpleChatAgent
    
    agent = SimpleChatAgent()
    session_deps = await SessionDependencies.create(session_id="123")
    response = await agent.chat("Hello!", deps=session_deps)
    print(response.message)
"""

from .models import ChatResponse
from .agent import SimpleChatAgent
from .factory import (
    create_simple_chat_agent,
    create_simple_chat_agent_with_deps,
    create_simple_chat_agent_basic,
    clear_agent_cache,
    get_agent_cache_stats
)

__all__ = [
    'ChatResponse',
    'SimpleChatAgent', 
    'create_simple_chat_agent',
    'create_simple_chat_agent_with_deps',
    'create_simple_chat_agent_basic',
    'clear_agent_cache',
    'get_agent_cache_stats'
]
