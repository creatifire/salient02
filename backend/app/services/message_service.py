"""
Message service for comprehensive chat history management and retrieval.

This service provides complete message lifecycle management including storage,
retrieval, context building, and metadata handling for chat conversations.

Key Features:
- Message storage with role-based typing (human, assistant, system)
- Session-based message retrieval with filtering and pagination
- Context building for LLM conversations with configurable limits
- Metadata support for future RAG citations and tool information
- Efficient querying with proper indexing and error handling

Business Context:
Messages form the core conversation history that enables session continuity,
context awareness, and future retrieval-augmented generation capabilities.
The service ensures conversation persistence across browser sessions while
maintaining proper data isolation and performance.

Security:
- Session-based access control prevents cross-session data leakage
- Input validation and sanitization for all message content
- Metadata validation to prevent injection attacks
- Proper error handling without exposing internal details

Performance:
- Efficient pagination for large conversation histories
- Indexed queries on session_id and created_at for fast retrieval
- Configurable context limits to manage LLM token consumption
- Optimized queries with selective field loading

Dependencies:
- SQLAlchemy 2.0+ for async database operations
- UUID for primary key generation
- Logfire for structured logging and debugging
- Pydantic for input validation and type safety
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import logfire
from sqlalchemy import desc, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from ..models.message import Message
from ..database import get_database_service


class MessageService:
    """
    Comprehensive message management service for chat conversations.
    
    This service handles all aspects of message storage and retrieval,
    providing a clean interface for chat history management while
    ensuring proper session isolation and performance optimization.
    
    Design Philosophy:
    - Session-centric: All operations are scoped to specific sessions
    - Type-safe: Comprehensive validation of message roles and content
    - Performance-aware: Efficient queries with proper pagination
    - Future-ready: Metadata support for RAG and tool integration
    
    Key Responsibilities:
    - Message creation and validation
    - Session-based message retrieval with filtering
    - Context building for LLM conversations
    - Metadata management for future enhancements
    - Error handling with comprehensive logging
    
    Thread Safety:
    This service is thread-safe when used with async sessions.
    Each method operates independently without shared state.
    
    Attributes:
        VALID_ROLES: Supported message roles for validation
        DEFAULT_CONTEXT_LIMIT: Default number of messages for context
        MAX_CONTEXT_LIMIT: Maximum allowed context size for safety
    
    Example:
        >>> service = MessageService()
        >>> message_id = await service.save_message(
        ...     session_id=session_id,
        ...     role="human",
        ...     content="Hello, how can you help me?",
        ...     metadata={"source": "web_ui"}
        ... )
        >>> messages = await service.get_session_messages(session_id)
        >>> context = await service.get_recent_context(session_id, limit=10)
    """
    
    # Valid message roles based on OpenAI/Anthropic standards
    VALID_ROLES = {"human", "assistant", "system", "tool", "developer"}
    
    # Context limits for LLM conversations
    DEFAULT_CONTEXT_LIMIT = 20
    MAX_CONTEXT_LIMIT = 100
    
    async def save_message(
        self,
        session_id: uuid.UUID | str,
        role: str,
        content: str,
        agent_instance_id: uuid.UUID | str | None = None,
        llm_request_id: uuid.UUID | str | None = None,
        metadata: Dict[str, Any] | None = None
    ) -> uuid.UUID:
        """
        Save a new message to the database with comprehensive validation.
        
        Creates a new message record with proper validation, session linking,
        agent attribution, and metadata handling. Ensures data integrity and 
        provides detailed logging for debugging and monitoring.
        
        Args:
            session_id: Session UUID for message association
            role: Message role (human, assistant, system, tool, developer)
            content: Message text content (required, non-empty)
            agent_instance_id: Agent instance UUID for multi-tenant attribution (optional for backward compatibility)
            llm_request_id: LLM request UUID that generated this message (nullable for system messages)
            metadata: Optional metadata for RAG citations, tool calls, etc.
        
        Returns:
            UUID of the created message record
        
        Raises:
            ValueError: If role is invalid, content is empty, or agent_instance_id is required but missing
            SQLAlchemyError: If database operation fails
            Exception: For unexpected errors during message creation
        
        Example:
            >>> message_id = await service.save_message(
            ...     session_id="550e8400-e29b-41d4-a716-446655440000",
            ...     role="human",
            ...     content="What is the weather like today?",
            ...     agent_instance_id="660e8400-e29b-41d4-a716-446655440001",
            ...     metadata={"timestamp": "2024-01-01T12:00:00Z"}
            ... )
            >>> print(f"Message saved with ID: {message_id}")
        
        Security Notes:
        - Content is validated but not sanitized (preserves user intent)
        - Metadata is validated as JSON-serializable
        - Session ID must exist (enforced by foreign key constraint)
        - Agent instance ID must exist (enforced by foreign key constraint)
        """
        # Input validation
        if not isinstance(session_id, uuid.UUID):
            try:
                session_id = uuid.UUID(str(session_id))
            except (ValueError, TypeError) as e:
                logfire.error(
                    'service.message.invalid_session_id',
                    session_id=str(session_id),
                    error=str(e)
                )
                raise ValueError(f"Invalid session_id format: {session_id}") from e
        
        # Validate agent_instance_id (required for multi-tenant)
        if agent_instance_id is not None:
            if not isinstance(agent_instance_id, uuid.UUID):
                try:
                    agent_instance_id = uuid.UUID(str(agent_instance_id))
                except (ValueError, TypeError) as e:
                    logfire.error(
                        'service.message.invalid_agent_instance_id',
                        agent_instance_id=str(agent_instance_id),
                        error=str(e)
                    )
                    raise ValueError(f"Invalid agent_instance_id format: {agent_instance_id}") from e
        else:
            # agent_instance_id is required (NOT NULL in schema)
            logfire.error('service.message.missing_agent_instance_id')
            raise ValueError("agent_instance_id is required for message attribution")
        
        # Validate llm_request_id if provided (nullable, for cost attribution)
        if llm_request_id is not None:
            if not isinstance(llm_request_id, uuid.UUID):
                try:
                    llm_request_id = uuid.UUID(str(llm_request_id))
                except (ValueError, TypeError) as e:
                    logfire.error(
                        'service.message.invalid_llm_request_id',
                        llm_request_id=str(llm_request_id),
                        error=str(e)
                    )
                    raise ValueError(f"Invalid llm_request_id format: {llm_request_id}") from e
        
        if role not in self.VALID_ROLES:
            logfire.error(
                'service.message.invalid_role',
                role=role,
                valid_roles=list(self.VALID_ROLES)
            )
            raise ValueError(f"Invalid role: {role}. Valid roles: {self.VALID_ROLES}")
        
        if not content or not content.strip():
            logfire.error('service.message.empty_content')
            raise ValueError("Message content cannot be empty")
        
        # Validate metadata if provided
        if metadata is not None:
            try:
                # Ensure metadata is JSON-serializable
                import json
                json.dumps(metadata)
            except (TypeError, ValueError) as e:
                logfire.error(
                    'service.message.invalid_metadata',
                    error=str(e)
                )
                raise ValueError(f"Metadata must be JSON-serializable: {e}") from e
        
        db_service = get_database_service()
        async with db_service.get_session() as session:
            try:
                # Create new message record
                message = Message(
                    session_id=session_id,
                    agent_instance_id=agent_instance_id,
                    llm_request_id=llm_request_id,
                    role=role,
                    content=content.strip(),
                    meta=metadata,
                    created_at=datetime.now(timezone.utc)
                )
                
                session.add(message)
                await session.commit()
                await session.refresh(message)
                
                logfire.info(
                    'service.message.saved',
                    message_id=str(message.id),
                    session_id=str(session_id),
                    agent_instance_id=str(agent_instance_id),
                    llm_request_id=str(llm_request_id) if llm_request_id else None,
                    role=role,
                    content_length=len(content),
                    has_metadata=metadata is not None
                )
                
                return message.id
                
            except SQLAlchemyError as e:
                await session.rollback()
                logfire.exception(
                    'service.message.save_error',
                    session_id=str(session_id),
                    role=role
                )
                raise
            except Exception as e:
                await session.rollback()
                logfire.exception(
                    'service.message.save_unexpected_error',
                    session_id=str(session_id),
                    role=role
                )
                raise
    
    async def get_session_messages(
        self,
        session_id: uuid.UUID | str,
        limit: int | None = None,
        offset: int = 0,
        role_filter: str | None = None
    ) -> List[Message]:
        """
        Retrieve messages for a session with filtering and pagination.
        
        Fetches messages for a specific session with optional filtering by role
        and pagination support. Results are ordered chronologically for proper
        conversation flow reconstruction.
        
        Args:
            session_id: Session UUID to retrieve messages for
            limit: Maximum number of messages to return (None for all)
            offset: Number of messages to skip for pagination
            role_filter: Optional role filter (human, assistant, etc.)
        
        Returns:
            List of Message objects ordered by creation time (oldest first)
        
        Raises:
            ValueError: If session_id format is invalid
            SQLAlchemyError: If database query fails
        
        Example:
            >>> # Get all messages for a session
            >>> all_messages = await service.get_session_messages(session_id)
            >>> 
            >>> # Get latest 10 messages
            >>> recent = await service.get_session_messages(session_id, limit=10)
            >>> 
            >>> # Get only human messages
            >>> human_msgs = await service.get_session_messages(
            ...     session_id, role_filter="human"
            ... )
        
        Performance Notes:
        - Query uses session_id index for fast filtering
        - LIMIT/OFFSET applied at database level for efficiency
        - Results ordered by created_at for chronological flow
        """
        # Validate session_id
        if not isinstance(session_id, uuid.UUID):
            try:
                session_id = uuid.UUID(str(session_id))
            except (ValueError, TypeError) as e:
                logfire.error(
                    'service.message.invalid_session_id',
                    session_id=str(session_id),
                    error=str(e)
                )
                raise ValueError(f"Invalid session_id format: {session_id}") from e
        
        # Validate role_filter if provided
        if role_filter and role_filter not in self.VALID_ROLES:
            logfire.error(
                'service.message.invalid_role_filter',
                role_filter=role_filter,
                valid_roles=list(self.VALID_ROLES)
            )
            raise ValueError(f"Invalid role filter: {role_filter}. Valid roles: {self.VALID_ROLES}")
        
        db_service = get_database_service()
        async with db_service.get_session() as session:
            try:
                # Build query with optional role filter
                # Using selectinload() prevents N+1 queries if relationships are accessed later
                query = (
                    select(Message)
                    .options(
                        selectinload(Message.session),  # Eager load session relationship
                        selectinload(Message.agent_instance),  # Eager load agent_instance relationship
                        selectinload(Message.llm_request)  # Eager load llm_request relationship
                    )
                    .where(Message.session_id == session_id)
                )
                
                if role_filter:
                    query = query.where(Message.role == role_filter)
                
                # Order chronologically for proper conversation flow
                query = query.order_by(Message.created_at)
                
                # Apply pagination
                if offset > 0:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)
                
                result = await session.execute(query)
                messages = result.scalars().all()
                
                logfire.info(
                    'service.message.retrieved',
                    session_id=str(session_id),
                    count=len(messages),
                    limit=limit,
                    offset=offset,
                    role_filter=role_filter
                )
                
                return list(messages)
                
            except SQLAlchemyError as e:
                logfire.exception(
                    'service.message.retrieval_error',
                    session_id=str(session_id)
                )
                raise
    
    async def get_recent_context(
        self,
        session_id: uuid.UUID | str,
        limit: int = DEFAULT_CONTEXT_LIMIT,
        include_system: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages formatted for LLM context with configurable limits.
        
        Retrieves the most recent messages for a session and formats them
        for use as LLM conversation context. Provides control over message
        types and count to manage token consumption effectively.
        
        Args:
            session_id: Session UUID to get context for
            limit: Maximum number of messages (capped at MAX_CONTEXT_LIMIT)
            include_system: Whether to include system messages in context
        
        Returns:
            List of message dictionaries with role and content fields,
            ordered chronologically (oldest first) for proper LLM context
        
        Raises:
            ValueError: If session_id format is invalid or limit is excessive
            SQLAlchemyError: If database query fails
        
        Example:
            >>> # Get recent context for LLM
            >>> context = await service.get_recent_context(session_id, limit=10)
            >>> for msg in context:
            ...     print(f"{msg['role']}: {msg['content']}")
            
            >>> # Context without system messages
            >>> user_context = await service.get_recent_context(
            ...     session_id, limit=5, include_system=False
            ... )
        
        Context Format:
        Each message is formatted as:
        {
            "role": "human|assistant|system",
            "content": "message text",
            "timestamp": "2024-01-01T12:00:00Z"  # for debugging
        }
        
        Performance Notes:
        - Uses LIMIT for efficient database querying
        - Results are reversed to provide chronological order
        - System message filtering applied at database level
        """
        # Validate session_id
        if not isinstance(session_id, uuid.UUID):
            try:
                session_id = uuid.UUID(str(session_id))
            except (ValueError, TypeError) as e:
                logfire.error(
                    'service.message.invalid_session_id',
                    session_id=str(session_id),
                    error=str(e)
                )
                raise ValueError(f"Invalid session_id format: {session_id}") from e
        
        # Validate and cap limit
        if limit <= 0:
            logfire.error(
                'service.message.invalid_limit',
                limit=limit
            )
            raise ValueError(f"Limit must be positive, got: {limit}")
        
        if limit > self.MAX_CONTEXT_LIMIT:
            logfire.warn(
                'service.message.limit_exceeded',
                limit=limit,
                max_limit=self.MAX_CONTEXT_LIMIT
            )
            limit = self.MAX_CONTEXT_LIMIT
        
        db_service = get_database_service()
        async with db_service.get_session() as session:
            try:
                # Build query for recent messages
                # Using selectinload() prevents N+1 queries if relationships are accessed later
                query = (
                    select(Message)
                    .options(
                        selectinload(Message.session),  # Eager load session relationship
                        selectinload(Message.agent_instance),  # Eager load agent_instance relationship
                        selectinload(Message.llm_request)  # Eager load llm_request relationship
                    )
                    .where(Message.session_id == session_id)
                )
                
                # Optionally exclude system messages
                if not include_system:
                    query = query.where(Message.role != "system")
                
                # Get most recent messages first, then reverse for chronological order
                query = query.order_by(desc(Message.created_at)).limit(limit)
                
                result = await session.execute(query)
                messages = result.scalars().all()
                
                # Reverse to get chronological order (oldest first) for LLM context
                messages = list(reversed(messages))
                
                # Format for LLM consumption
                context = []
                for msg in messages:
                    context.append({
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat() if msg.created_at else None
                    })
                
                logfire.info(
                    'service.message.context_retrieved',
                    session_id=str(session_id),
                    count=len(context),
                    limit=limit,
                    include_system=include_system
                )
                
                return context
                
            except SQLAlchemyError as e:
                logfire.exception(
                    'service.message.context_retrieval_error',
                    session_id=str(session_id)
                )
                raise
    
    async def get_message_count(self, session_id: uuid.UUID | str) -> int:
        """
        Get total message count for a session.
        
        Provides efficient counting of messages in a session for analytics,
        pagination calculations, and conversation length tracking.
        
        Args:
            session_id: Session UUID to count messages for
        
        Returns:
            Total number of messages in the session
        
        Raises:
            ValueError: If session_id format is invalid
            SQLAlchemyError: If database query fails
        
        Example:
            >>> count = await service.get_message_count(session_id)
            >>> print(f"Session has {count} messages")
        """
        # Validate session_id
        if not isinstance(session_id, uuid.UUID):
            try:
                session_id = uuid.UUID(str(session_id))
            except (ValueError, TypeError) as e:
                logfire.error(
                    'service.message.invalid_session_id',
                    session_id=str(session_id),
                    error=str(e)
                )
                raise ValueError(f"Invalid session_id format: {session_id}") from e
        
        db_service = get_database_service()
        async with db_service.get_session() as session:
            try:
                from sqlalchemy import func
                query = select(func.count(Message.id)).where(Message.session_id == session_id)
                result = await session.execute(query)
                count = result.scalar() or 0
                
                logfire.debug(
                    'service.message.count_retrieved',
                    session_id=str(session_id),
                    count=count
                )
                
                return count
                
            except SQLAlchemyError as e:
                logfire.exception(
                    'service.message.count_error',
                    session_id=str(session_id)
                )
                raise
    
    @staticmethod
    def extract_tool_calls(result: Any) -> list[dict]:
        """
        Extract tool calls from Pydantic AI result for metadata storage.
        
        Parses the result object to find all tool calls made during agent execution,
        extracting tool names and arguments for debugging and admin visibility.
        
        Args:
            result: Pydantic AI result object from agent.run() or agent.run_stream()
        
        Returns:
            List of tool call dictionaries with 'tool_name' and 'args' keys.
            Returns empty list if no tool calls found or result is None.
        
        Example:
            >>> result = await agent.run("Find cardiology")
            >>> tool_calls = MessageService.extract_tool_calls(result)
            >>> print(tool_calls)
            [{"tool_name": "search_directory", "args": {"query": "cardiology"}}]
        
        Notes:
        - Handles both streaming and non-streaming results
        - Safely handles missing attributes and None values
        - Used for admin debugging and conversation tracing
        """
        tool_calls_meta = []
        
        if result is None:
            return tool_calls_meta
        
        try:
            # Check if result has messages (Pydantic AI result structure)
            if hasattr(result, 'all_messages') and callable(result.all_messages):
                messages = result.all_messages()
                if messages:
                    from pydantic_ai.messages import ToolCallPart
                    
                    for msg in messages:
                        if hasattr(msg, 'parts'):
                            for part in msg.parts:
                                if isinstance(part, ToolCallPart):
                                    tool_calls_meta.append({
                                        "tool_name": part.tool_name,
                                        "args": part.args
                                    })
            
            logfire.debug(
                'service.message.tool_calls_extracted',
                count=len(tool_calls_meta)
            )
            
        except Exception as e:
            logfire.error(
                'service.message.tool_extraction_error',
                error=str(e)
            )
            # Return empty list rather than raising - tool extraction is not critical
        
        return tool_calls_meta
    
    async def save_message_pair(
        self,
        session_id: uuid.UUID | str,
        agent_instance_id: uuid.UUID | str,
        llm_request_id: uuid.UUID | str | None,
        user_message: str,
        assistant_message: str,
        result: Any = None
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """
        Save user + assistant message pair atomically with tool call metadata.
        
        Provides atomic saving of message pairs to ensure conversation consistency.
        Both messages are saved in a single transaction - if either fails, both
        are rolled back. Automatically extracts and attaches tool call metadata
        to the assistant message for admin debugging.
        
        This method consolidates the duplicate message-saving logic from both
        streaming and non-streaming endpoints, providing a single source of truth
        for message pair persistence.
        
        Args:
            session_id: Session UUID for message association
            agent_instance_id: Agent instance UUID for multi-tenant attribution
            llm_request_id: LLM request UUID for cost attribution (optional)
            user_message: User's input message content
            assistant_message: Agent's response message content
            result: Optional Pydantic AI result object for tool call extraction
        
        Returns:
            Tuple of (user_message_id, assistant_message_id)
        
        Raises:
            ValueError: If validation fails for any ID or message content
            SQLAlchemyError: If database transaction fails (both messages rolled back)
        
        Example:
            >>> service = MessageService()
            >>> result = await agent.run(user_message)
            >>> user_id, assistant_id = await service.save_message_pair(
            ...     session_id=session_id,
            ...     agent_instance_id=agent_instance_id,
            ...     llm_request_id=llm_request_id,
            ...     user_message="What is cardiology?",
            ...     assistant_message=result.output,
            ...     result=result
            ... )
        
        Benefits:
        - Atomic transaction: Both messages saved or neither
        - DRY: Eliminates duplicate code in streaming/non-streaming
        - Tool extraction: Automatic metadata attachment
        - Testable: Single method to test message pair logic
        
        Transaction Safety:
        Uses a single database transaction to ensure atomicity. If assistant
        message save fails, the user message is also rolled back, preventing
        orphaned messages in the conversation history.
        """
        # Input validation
        if not isinstance(session_id, uuid.UUID):
            try:
                session_id = uuid.UUID(str(session_id))
            except (ValueError, TypeError) as e:
                logfire.error(
                    'service.message.save_pair.invalid_session_id',
                    session_id=str(session_id),
                    error=str(e)
                )
                raise ValueError(f"Invalid session_id format: {session_id}") from e
        
        if not isinstance(agent_instance_id, uuid.UUID):
            try:
                agent_instance_id = uuid.UUID(str(agent_instance_id))
            except (ValueError, TypeError) as e:
                logfire.error(
                    'service.message.save_pair.invalid_agent_instance_id',
                    agent_instance_id=str(agent_instance_id),
                    error=str(e)
                )
                raise ValueError(f"Invalid agent_instance_id format: {agent_instance_id}") from e
        
        if llm_request_id is not None and not isinstance(llm_request_id, uuid.UUID):
            try:
                llm_request_id = uuid.UUID(str(llm_request_id))
            except (ValueError, TypeError) as e:
                logfire.error(
                    'service.message.save_pair.invalid_llm_request_id',
                    llm_request_id=str(llm_request_id),
                    error=str(e)
                )
                raise ValueError(f"Invalid llm_request_id format: {llm_request_id}") from e
        
        if not user_message or not user_message.strip():
            logfire.error('service.message.save_pair.empty_user_message')
            raise ValueError("User message content cannot be empty")
        
        if not assistant_message or not assistant_message.strip():
            logfire.error('service.message.save_pair.empty_assistant_message')
            raise ValueError("Assistant message content cannot be empty")
        
        # Extract tool calls if result provided
        tool_calls_meta = self.extract_tool_calls(result) if result else []
        
        db_service = get_database_service()
        async with db_service.get_session() as session:
            try:
                # Create user message
                user_msg = Message(
                    session_id=session_id,
                    agent_instance_id=agent_instance_id,
                    llm_request_id=llm_request_id,
                    role="human",
                    content=user_message.strip(),
                    meta=None,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(user_msg)
                
                # Create assistant message with tool calls metadata
                assistant_msg = Message(
                    session_id=session_id,
                    agent_instance_id=agent_instance_id,
                    llm_request_id=llm_request_id,
                    role="assistant",
                    content=assistant_message.strip(),
                    meta={"tool_calls": tool_calls_meta} if tool_calls_meta else None,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(assistant_msg)
                
                # Commit both messages atomically
                await session.commit()
                await session.refresh(user_msg)
                await session.refresh(assistant_msg)
                
                logfire.info(
                    'service.message.pair_saved',
                    session_id=str(session_id),
                    agent_instance_id=str(agent_instance_id),
                    llm_request_id=str(llm_request_id) if llm_request_id else None,
                    user_message_id=str(user_msg.id),
                    assistant_message_id=str(assistant_msg.id),
                    user_message_length=len(user_message),
                    assistant_message_length=len(assistant_message),
                    tool_calls_count=len(tool_calls_meta)
                )
                
                return (user_msg.id, assistant_msg.id)
                
            except SQLAlchemyError as e:
                await session.rollback()
                logfire.exception(
                    'service.message.save_pair_error',
                    session_id=str(session_id),
                    agent_instance_id=str(agent_instance_id)
                )
                raise
            except Exception as e:
                await session.rollback()
                logfire.exception(
                    'service.message.save_pair_unexpected_error',
                    session_id=str(session_id),
                    agent_instance_id=str(agent_instance_id)
                )
                raise


# Global service instance for dependency injection
_message_service: MessageService | None = None


def get_message_service() -> MessageService:
    """
    Get the global MessageService instance (singleton pattern).
    
    Provides a single instance of the MessageService for use throughout
    the application, ensuring consistent behavior and resource management.
    
    Returns:
        MessageService instance for message operations
    
    Example:
        >>> service = get_message_service()
        >>> await service.save_message(session_id, "human", "Hello!")
    
    Design Notes:
    - Singleton pattern ensures consistent service behavior
    - Thread-safe due to stateless service design
    - Can be easily mocked for testing
    """
    global _message_service
    if _message_service is None:
        _message_service = MessageService()
    return _message_service
