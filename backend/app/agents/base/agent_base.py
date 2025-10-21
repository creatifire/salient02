"""
Base agent class for Pydantic AI agents.

This module provides the foundational BaseAgent class that all specific agent
types inherit from. It provides common functionality including dependency
injection, tool integration, configuration management, and account isolation.

Key Features:
- Integration with Pydantic AI Agent class
- Account-aware dependency injection
- Tool registration and management
- Configuration loading and validation
- Structured response formatting
- Usage tracking and monitoring

Design:
- Follows Pydantic AI patterns and conventions
- Integrates with existing FastAPI and database infrastructure
- Provides foundation for multi-account support (Phase 3+)
- Maintains compatibility with existing session management
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic_ai import Agent
from pydantic_ai.models import Model

from .dependencies import BaseDependencies, AccountScopedDependencies
from .tools_base import BaseTool
from .types import AgentConfig, AgentResponse, AccountContext


DepsType = TypeVar('DepsType', bound=BaseDependencies)


class BaseAgent:
    """
    Base class for all Pydantic AI agents in the system.
    
    Provides common functionality that all agent types need:
    - Pydantic AI Agent integration
    - Dependency injection setup
    - Tool registration and management
    - Configuration loading and validation
    - Account-aware context management
    
    Usage:
        class MyAgent(BaseAgent):
            def __init__(self):
                super().__init__(
                    model_name="openai:gpt-4o",
                    agent_type="my_agent",
                    deps_type=MyDependencies
                )
                self._register_tools()
                
            def _register_tools(self):
                # Register agent-specific tools
                pass
    """
    
    def __init__(
        self,
        model_name: str,
        agent_type: str,
        deps_type: Type[DepsType],
        system_prompt: Optional[str] = None,
        config: Optional[AgentConfig] = None,
    ):
        """
        Initialize the base agent.
        
        Args:
            model_name: Model identifier (e.g., "openai:gpt-4o")
            agent_type: Agent type identifier (e.g., "simple_chat")
            deps_type: Dependency injection class type
            system_prompt: Optional system prompt (overrides config)
            config: Optional agent configuration
        """
        self.agent_type = agent_type
        self.deps_type = deps_type
        self.config = config
        self.tools: Dict[str, BaseTool] = {}
        
        # Determine system prompt
        if system_prompt:
            prompt = system_prompt
        elif config and config.system_prompt:
            prompt = config.system_prompt
        else:
            prompt = f"You are a helpful AI assistant ({agent_type})."
        
        # Create the underlying Pydantic AI agent
        self.agent = Agent(
            model_name,
            deps_type=deps_type,
            result_type=AgentResponse,
            system_prompt=prompt,
        )
        
        # Track usage statistics
        self.usage_stats = {
            "total_requests": 0,
            "total_errors": 0, 
            "total_tool_calls": 0,
        }
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool with this agent.
        
        Args:
            tool: Tool instance to register
        """
        self.tools[tool.name] = tool
        
        # Create Pydantic AI tool decorator and register
        @self.agent.tool
        async def tool_wrapper(ctx, **kwargs) -> Any:
            """Wrapper function for Pydantic AI tool integration."""
            result = await tool.execute(ctx.deps, **kwargs)
            
            # Track tool usage
            self.usage_stats["total_tool_calls"] += 1
            
            if not result.success:
                # Handle tool errors appropriately
                raise Exception(f"Tool {tool.name} failed: {result.error_message}")
            
            return result.result
        
        # Update the wrapper function metadata for Pydantic AI
        tool_wrapper.__name__ = tool.name
        tool_wrapper.__doc__ = tool.description
    
    async def run(
        self, 
        user_message: str,
        deps: DepsType,
        conversation_id: Optional[str] = None,
    ) -> AgentResponse:
        """
        Execute the agent with a user message.
        
        Args:
            user_message: User input message
            deps: Dependency injection context
            conversation_id: Optional conversation identifier
            
        Returns:
            AgentResponse with structured output
        """
        try:
            # Track request
            self.usage_stats["total_requests"] += 1
            
            # Run the agent
            result = await self.agent.run(user_message, deps=deps)
            
            # Ensure we have an AgentResponse
            if isinstance(result.data, AgentResponse):
                response = result.data
            else:
                # Convert to AgentResponse if needed
                response = AgentResponse(
                    content=str(result.data),
                    metadata={
                        "model": str(result.model), 
                        "usage": result.usage(),
                    }
                )
            
            # Add agent and conversation metadata
            response.agent_type = self.agent_type
            response.conversation_id = conversation_id
            
            return response
            
        except Exception as e:
            # Track errors
            self.usage_stats["total_errors"] += 1
            
            # Return error response
            return AgentResponse(
                content=f"I apologize, but I encountered an error processing your request: {str(e)}",
                metadata={
                    "error": True,
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                },
                agent_type=self.agent_type,
                conversation_id=conversation_id,
            )
    
    async def run_sync(
        self,
        user_message: str,
        deps: DepsType,
        conversation_id: Optional[str] = None,
    ) -> AgentResponse:
        """
        Synchronous wrapper for agent execution.
        
        Args:
            user_message: User input message
            deps: Dependency injection context
            conversation_id: Optional conversation identifier
            
        Returns:
            AgentResponse with structured output
        """
        return await self.run(user_message, deps, conversation_id)
    
    def get_tool_names(self) -> List[str]:
        """Get list of registered tool names."""
        return list(self.tools.keys())
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a registered tool by name."""
        return self.tools.get(name)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for this agent."""
        stats = dict(self.usage_stats)
        
        # Add tool statistics
        tool_stats = {}
        for tool_name, tool in self.tools.items():
            tool_stats[tool_name] = tool.get_usage_stats()
        
        stats["tools"] = tool_stats
        return stats
    
    @classmethod
    async def from_config(
        cls,
        config: AgentConfig,
        deps_type: Type[DepsType],
        model_name: Optional[str] = None,
    ) -> BaseAgent:
        """
        Create an agent instance from configuration.
        
        Args:
            config: Agent configuration
            deps_type: Dependency injection class type
            model_name: Optional model override
            
        Returns:
            Configured agent instance
        """
        # Use model from config or override
        if model_name:
            model = model_name
        elif config.model_settings and "model" in config.model_settings:
            model = config.model_settings["model"]
        else:
            model = "openai:gpt-4o"  # Default fallback
        
        # Create agent instance
        agent = cls(
            model_name=model,
            agent_type=config.agent_type,
            deps_type=deps_type,
            system_prompt=config.system_prompt,
            config=config,
        )
        
        return agent
    
    def supports_account_isolation(self) -> bool:
        """Check if this agent supports account-scoped operations."""
        return issubclass(self.deps_type, AccountScopedDependencies)
