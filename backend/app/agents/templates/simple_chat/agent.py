"""
Simple Chat Agent Implementation.

This module provides a basic Pydantic AI-powered conversational agent that uses
the existing SessionDependencies pattern for integration with the current system.

Key Features:
- Basic conversational agent using Pydantic AI framework
- Integration with existing SessionDependencies and session management
- Static system prompt for consistent behavior
- ChatResponse structured outputs for API compatibility
- OpenAI GPT-4o model with optimized settings for conversation

Design:
- Inherits from BaseAgent for common functionality
- Uses SessionDependencies for session context and database integration
- Returns ChatResponse objects instead of generic AgentResponse
- Minimal configuration for foundation layer simplicity

Usage:
    # Create agent instance
    agent = SimpleChatAgent()
    
    # Create session dependencies
    session_deps = await SessionDependencies.create(session_id="123", user_id="user-456")
    
    # Generate response
    response = await agent.chat("Hello, how are you today?", deps=session_deps)
    print(response.message)
"""

from __future__ import annotations

import asyncio
from datetime import datetime, UTC
from typing import Optional, AsyncGenerator

from pydantic_ai import Agent
from pydantic_ai.models import Model

from app.agents.base.dependencies import SessionDependencies
from app.agents.base.agent_base import BaseAgent
from .models import ChatResponse


class SimpleChatAgent:
    """
    Basic Pydantic AI conversational agent for simple chat interactions.
    
    Provides foundational chat capabilities using the existing session management
    infrastructure. Designed for text-based conversations without complex tool
    integration, serving as the foundation for more advanced agent capabilities.
    
    Features:
    - Pydantic AI Agent integration with SessionDependencies
    - Structured ChatResponse outputs for API compatibility
    - Static system prompt for consistent conversational behavior
    - OpenAI GPT-4o model with conversation-optimized settings
    - Integration with existing session and database infrastructure
    
    Configuration:
    - Model: openai:gpt-4o (high-quality conversation)
    - Temperature: 0.3 (balanced creativity and consistency)
    - Response format: ChatResponse with message, confidence, metadata
    - Session integration: Uses SessionDependencies for context
    """
    
    # Static system prompt for consistent behavior
    SYSTEM_PROMPT = """You are a helpful, friendly AI assistant focused on providing clear and useful responses.

Key guidelines:
- Be conversational and approachable while maintaining professionalism
- Provide accurate, helpful information based on your knowledge
- If you're not sure about something, say so rather than guessing
- Keep responses concise but complete
- Ask clarifying questions when the user's request is ambiguous
- Be respectful and considerate in all interactions

Your goal is to assist users with their questions and tasks in a helpful, reliable manner."""
    
    def __init__(
        self,
        model_name: str = "openai:gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the Simple Chat Agent.
        
        Args:
            model_name: LLM model identifier (default: openai:gpt-4o)
            temperature: Sampling temperature (default: 0.3)
            max_tokens: Maximum response tokens (default: 2000)
            system_prompt: Custom system prompt (uses default if None)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or self.SYSTEM_PROMPT
        
        # Create the underlying Pydantic AI agent
        self.agent = Agent(
            model_name,
            deps_type=SessionDependencies,
            system_prompt=self.system_prompt
        )
        
        # Usage tracking
        self.usage_stats = {
            "total_conversations": 0,
            "total_messages": 0,
            "total_errors": 0,
            "average_response_length": 0.0
        }
        
        # Response length tracking for statistics
        self._response_lengths = []
    
    async def chat(
        self,
        message: str,
        deps: SessionDependencies,
        include_confidence: bool = True
    ) -> ChatResponse:
        """
        Generate a chat response for the given user message.
        
        Args:
            message: User input message
            deps: Session dependencies with context and database access
            include_confidence: Whether to include confidence scoring
            
        Returns:
            ChatResponse with structured output
            
        Raises:
            ValueError: If message is empty or invalid
            RuntimeError: If agent execution fails
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
        
        try:
            # Track conversation
            self.usage_stats["total_conversations"] += 1
            self.usage_stats["total_messages"] += 1
            
            # Start timing
            start_time = datetime.now(UTC)
            
            # Run the agent
            result = await self.agent.run(message.strip(), deps=deps)
            
            # Calculate response time
            end_time = datetime.now(UTC)
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Extract response content
            response_content = str(result.data) if result.data else "I apologize, but I wasn't able to generate a response to your message."
            
            # Track response length for statistics
            self._response_lengths.append(len(response_content))
            if self._response_lengths:
                self.usage_stats["average_response_length"] = sum(self._response_lengths) / len(self._response_lengths)
            
            # Calculate confidence (simple heuristic for now)
            confidence = None
            if include_confidence:
                confidence = self._calculate_response_confidence(response_content, result)
            
            # Build metadata
            metadata = {
                "model": self.model_name,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "response_time_ms": round(response_time_ms, 2)
            }
            
            # Add usage information if available
            if hasattr(result, 'usage') and result.usage():
                usage = result.usage()
                metadata.update({
                    "tokens_used": getattr(usage, 'total_tokens', None),
                    "prompt_tokens": getattr(usage, 'prompt_tokens', None),
                    "completion_tokens": getattr(usage, 'completion_tokens', None)
                })
            
            # Create structured response
            response = ChatResponse(
                message=response_content,
                confidence=confidence,
                metadata=metadata,
                session_id=deps.session_id
            )
            
            return response
            
        except Exception as e:
            # Track errors
            self.usage_stats["total_errors"] += 1
            
            # Create error response
            error_response = ChatResponse(
                message=f"I apologize, but I encountered an error processing your message: {str(e)}",
                confidence=0.0,
                metadata={
                    "error": True,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "model": self.model_name
                },
                session_id=deps.session_id
            )
            
            # Re-raise for debugging in development
            raise RuntimeError(f"Agent execution failed: {str(e)}") from e
    
    def _calculate_response_confidence(self, response_content: str, result) -> float:
        """
        Calculate confidence score for the response using simple heuristics.
        
        Args:
            response_content: Generated response text
            result: Pydantic AI result object
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.8  # Base confidence
        
        # Adjust based on response characteristics
        if len(response_content) < 10:
            confidence -= 0.2  # Very short responses may be less helpful
        elif len(response_content) > 1000:
            confidence -= 0.1  # Very long responses may be verbose
        
        # Penalize apologetic language (may indicate uncertainty)
        apologetic_phrases = ["i don't know", "i'm not sure", "i apologize", "sorry, i can't"]
        if any(phrase in response_content.lower() for phrase in apologetic_phrases):
            confidence -= 0.1
        
        # Bonus for helpful structure
        helpful_indicators = ["here's", "you can", "i recommend", "the answer is"]
        if any(phrase in response_content.lower() for phrase in helpful_indicators):
            confidence += 0.05
        
        # Ensure within bounds
        return max(0.0, min(1.0, confidence))
    
    async def chat_stream(
        self,
        message: str,
        deps: SessionDependencies,
        include_confidence: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming chat response (placeholder for future streaming support).
        
        Args:
            message: User input message
            deps: Session dependencies with context and database access
            include_confidence: Whether to include confidence scoring
            
        Yields:
            Response text chunks
            
        Note:
            Currently returns the full response as a single chunk.
            Future implementation will support true streaming.
        """
        response = await self.chat(message, deps, include_confidence)
        yield response.message
    
    def get_usage_stats(self) -> dict:
        """
        Get usage statistics for this agent instance.
        
        Returns:
            Dictionary with usage statistics
        """
        return dict(self.usage_stats)
    
    def reset_usage_stats(self) -> None:
        """Reset usage statistics for this agent instance."""
        self.usage_stats = {
            "total_conversations": 0,
            "total_messages": 0,
            "total_errors": 0,
            "average_response_length": 0.0
        }
        self._response_lengths = []
    
    @property
    def model_info(self) -> dict:
        """Get model configuration information."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system_prompt_length": len(self.system_prompt)
        }
    
    def __repr__(self) -> str:
        return f"SimpleChatAgent(model={self.model_name}, temp={self.temperature})"
