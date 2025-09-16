"""
Agent Session Service for conversation history loading and management.

This service provides functions to load conversation history from the database
and convert it to Pydantic AI ModelMessage format for agent consumption.

Key Features:
- Load conversation history from any endpoint (legacy /chat or /agents/simple-chat/chat)
- Convert database message roles to Pydantic AI ModelMessage types
- Cross-endpoint conversation continuity
- Session statistics and monitoring

Business Context:
Enables agents to load conversation history from the database, maintaining
context across different endpoints and providing seamless conversation
continuity for users.

Dependencies:
- MessageService for database message retrieval
- Pydantic AI message types for proper agent integration
- UUID handling for session identification
"""

from typing import List, Dict, Any, Optional
from .message_service import get_message_service
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart
from datetime import datetime
import uuid


async def load_agent_conversation(session_id: str, max_messages: Optional[int] = None) -> List[ModelMessage]:
    """
    Load conversation history from database and convert to Pydantic AI format.
    
    Retrieves recent messages for the given session from the database (from any endpoint)
    and converts them to the proper Pydantic AI ModelMessage format for agent consumption.
    
    Args:
        session_id: Session UUID string to load conversation for
        max_messages: Maximum number of recent messages to load (None to use config default)
        
    Returns:
        List of ModelMessage objects in chronological order (oldest first), limited by max_messages
        
    Raises:
        ValueError: If session_id format is invalid
        
    Example:
        >>> history = await load_agent_conversation("123e4567-e89b-12d3-a456-426614174000")
        >>> print(f"Loaded {len(history)} messages from database")
        >>> # Or with custom limit
        >>> history = await load_agent_conversation("123e4567-e89b-12d3-a456-426614174000", max_messages=20)
    """
    # Get message limit from agent-first configuration cascade if not provided
    if max_messages is None:
        from ..agents.config_loader import get_agent_history_limit
        max_messages = await get_agent_history_limit("simple_chat")  # Default to simple_chat for now
    
    message_service = get_message_service()
    
    # Get recent messages for this session (from any endpoint) with configurable limit
    db_messages = await message_service.get_session_messages(
        session_id=uuid.UUID(session_id),
        limit=max_messages  # Respects configuration
    )
    
    if not db_messages:
        return []
    
    # Convert DB messages to Pydantic AI ModelMessage format
    pydantic_messages = []
    for msg in db_messages:
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
                model_name="agent-session",  # Identifier for loaded session messages
                timestamp=msg.created_at or datetime.now()
            )
        else:
            # Skip system messages and unknown roles
            continue
            
        pydantic_messages.append(pydantic_message)
    
    return pydantic_messages


async def get_session_stats(session_id: str) -> Dict[str, Any]:
    """
    Get comprehensive session statistics for monitoring conversation continuity.
    
    Provides detailed analytics and debugging information about session message counts,
    cross-endpoint continuity status, message distribution, and recent activity.
    
    Args:
        session_id: Session UUID string to get statistics for
        
    Returns:
        Dictionary with comprehensive session statistics including:
        - total_messages: Total message count in session
        - session_id: The session ID
        - cross_endpoint_continuity: Whether session has any messages
        - message_breakdown: Counts by role (human, assistant, system, etc.)
        - recent_activity: Information about most recent messages
        - analytics: Additional metrics for monitoring
        
    Example:
        >>> stats = await get_session_stats("123e4567-e89b-12d3-a456-426614174000")
        >>> print(f"Session has {stats['total_messages']} messages")
        >>> print(f"Message breakdown: {stats['message_breakdown']}")
    """
    message_service = get_message_service()
    
    # Get total message count for this session
    total_messages = await message_service.get_message_count(
        session_id=uuid.UUID(session_id)
    )
    
    # Get recent messages for detailed analysis
    recent_messages = await message_service.get_session_messages(
        session_id=uuid.UUID(session_id),
        limit=10  # Last 10 messages for analysis
    )
    
    # Analyze message breakdown by role
    message_breakdown = {}
    recent_sources = set()
    
    for msg in recent_messages:
        # Count by role
        role = msg.role
        if role not in message_breakdown:
            message_breakdown[role] = 0
        message_breakdown[role] += 1
        
        # Track sources for cross-endpoint analysis
        if msg.meta and "source" in msg.meta:
            recent_sources.add(msg.meta["source"])
    
    # Determine if there's evidence of cross-endpoint usage
    cross_endpoint_evidence = len(recent_sources) > 1
    
    # Calculate conversation metrics
    has_conversation = message_breakdown.get("human", 0) > 0 and message_breakdown.get("assistant", 0) > 0
    conversation_turns = min(message_breakdown.get("human", 0), message_breakdown.get("assistant", 0))
    
    return {
        "total_messages": total_messages,
        "session_id": session_id,
        "cross_endpoint_continuity": total_messages > 0,
        "message_breakdown": message_breakdown,
        "recent_activity": {
            "recent_message_count": len(recent_messages),
            "sources_detected": list(recent_sources),
            "cross_endpoint_evidence": cross_endpoint_evidence
        },
        "analytics": {
            "has_conversation": has_conversation,
            "conversation_turns": conversation_turns,
            "session_health": "active" if total_messages > 0 else "empty",
            "bridging_capable": True  # Agent session service is available
        }
    }
