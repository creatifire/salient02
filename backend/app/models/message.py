"""
Message model for complete chat history with role-based messages.

Based on datamodel specification in memorybank/architecture/datamodel.md
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from . import Base


class Message(Base):
    """
    Complete chat history with support for future RAG citations.
    
    Key Features:
    - role: Support for human|assistant|system|tool|developer message types
    - content: Message text content
    - metadata: Citations, doc_ids, scores, tool call information  
    - session_id: Links to browser session for conversation context
    
    Usage:
    - Chat history: Retrieve conversation flow for session
    - Context building: Provide recent messages to LLM
    - Analytics: Track conversation patterns and effectiveness
    - RAG support: Store citation metadata for retrieval augmentation
    """
    
    __tablename__ = "messages"
    
    # Primary key - UUID v7 (time-ordered)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid7)
    
    # Foreign key to sessions table
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    
    # Foreign key to agent_instances table (multi-tenant)
    agent_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Agent instance that handled this message"
    )
    
    # Foreign key to llm_requests table (cost attribution)
    llm_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("llm_requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="LLM request that generated this message (nullable for system messages)"
    )
    
    # Message role - supports OpenAI/Anthropic message patterns
    # Valid values: human, assistant, system, tool, developer
    role = Column(String(20), nullable=False)
    
    # Message text content
    content = Column(Text, nullable=False)
    
    # Extensible metadata for citations, document IDs, confidence scores, tool information
    # Examples:
    # - RAG citations: {"citations": [{"doc_id": "123", "score": 0.85, "snippet": "..."}]}
    # - Tool calls: {"tool_calls": [{"name": "search", "args": {...}, "result": {...}}]}
    # - Developer notes: {"debug_info": "...", "model_version": "gpt-4"}
    meta = Column(JSONB, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="messages")
    agent_instance = relationship("AgentInstanceModel", back_populates="messages")
    llm_request = relationship("LLMRequest", back_populates="messages")
    
    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, session_id={self.session_id}, role={self.role}, content='{content_preview}')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "llm_request_id": str(self.llm_request_id) if self.llm_request_id else None,
            "role": self.role,
            "content": self.content,
            "meta": self.meta,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
