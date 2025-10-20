"""
Session model for tracking browser sessions and user continuity.

This module provides the Session SQLAlchemy model for managing user sessions
in the Salient chat system. Sessions enable conversation persistence across
browser refreshes and provide the foundation for customer profile development.

Based on datamodel specification in memorybank/architecture/datamodel.md

Key Features:
- Cryptographically secure session keys for browser cookies
- Anonymous sessions that can be upgraded when email is provided
- Activity tracking for session timeout and analytics
- JSONB metadata for extensible session data
- Foreign key relationships to messages, LLM requests, and profiles

Security Considerations:
- Session keys must be cryptographically secure (generated via secrets module)
- HTTP-only cookies prevent XSS attacks on session tokens
- Email addresses are indexed but not unique (allows multiple sessions per email)
- All timestamps use timezone-aware datetime for consistency
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from . import Base


class Session(Base):
    """
    User session for chat persistence and resumption.
    
    Sessions are automatically created on first chat interaction and
    persist across browser sessions via HTTP-only cookies. This enables
    conversation continuity without requiring user registration.
    
    The session_key serves as the primary identifier and must be
    cryptographically secure to prevent session hijacking.
    
    Business Rules:
    - Sessions start as anonymous (is_anonymous=True)
    - When user provides email, is_anonymous becomes False
    - last_activity_at is updated on every request for timeout tracking
    - Session keys are 32-character URL-safe base64 strings
    - Email addresses can appear in multiple sessions (no uniqueness constraint)
    
    Relationships:
    - messages: One-to-many chat message history
    - llm_requests: One-to-many LLM API call tracking
    - profile: One-to-one customer profile data
    
    Security:
    - session_key must be generated using secrets.token_urlsafe(32)
    - HTTP-only cookies prevent client-side access
    - SameSite=Lax prevents CSRF attacks
    - Timezone-aware timestamps for consistent logging
    
    Attributes:
        id: UUID primary key for internal referencing
        session_key: Unique 32-char identifier stored in browser cookie
        email: User email address (nullable until provided)
        is_anonymous: True until email is provided by user
        created_at: Session creation timestamp (timezone-aware)
        last_activity_at: Last request timestamp for timeout detection
        meta: JSONB field for extensible session metadata
    """
    
    __tablename__ = "sessions"
    
    # Primary key - UUID for scalability and security
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        comment="Primary key for session identification"
    )
    
    # Browser session cookie value - unique across all sessions
    # Must be cryptographically secure (generated via secrets.token_urlsafe)
    session_key: Mapped[str] = mapped_column(
        String(64),  # 32-char base64 + padding
        unique=True, 
        nullable=False, 
        index=True,
        comment="Cryptographically secure session identifier for browser cookies"
    )
    
    # User email - nullable until provided during conversation
    # Indexed for email-based session linking but not unique (multiple sessions per email allowed)
    email: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True, 
        index=True,
        comment="User email address when provided during conversation"
    )
    
    # Anonymous flag - starts True, becomes False when email is provided
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="True for anonymous sessions, False when email is provided"
    )
    
    # Session lifecycle timestamps - timezone-aware for consistent logging
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=func.now(),
        comment="Session creation timestamp (UTC)"
    )
    
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=func.now(),
        comment="Last request timestamp for session timeout detection"
    )
    
    # Extensible session metadata - JSONB for performance and flexibility
    # Store session-specific data like user preferences, browser info, etc.
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, 
        nullable=True,
        comment="Extensible session metadata in JSON format"
    )
    
    # Multi-tenant architecture columns
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Account this session belongs to"
    )
    
    account_slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Denormalized account slug for query performance"
    )
    
    agent_instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Agent instance handling this session"
    )
    
    agent_instance_slug: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Denormalized agent instance slug for fast analytics - avoids JOINs to agent_instances"
    )
    
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID when authenticated (null for anonymous sessions)"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="Last session update timestamp"
    )
    
    # Relationships - defined with string references to avoid circular imports
    # CASCADE DELETE ensures data consistency when sessions are removed
    
    # Multi-tenant relationships
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="sessions",
        doc="Account that owns this session"
    )
    
    agent_instance: Mapped["AgentInstanceModel"] = relationship(
        "AgentInstanceModel",
        doc="Agent instance handling this session"
    )
    
    # One-to-many: Session → Messages (chat history)
    messages: Mapped[list["Message"]] = relationship(
        "Message", 
        back_populates="session", 
        cascade="all, delete-orphan",
        doc="All chat messages in this session"
    )
    
    # One-to-many: Session → LLMRequests (API usage tracking)
    llm_requests: Mapped[list["LLMRequest"]] = relationship(
        "LLMRequest", 
        back_populates="session", 
        cascade="all, delete-orphan",
        doc="All LLM API requests made during this session"
    )
    
    # One-to-one: Session → Profile (customer data accumulation)
    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile", 
        back_populates="session", 
        uselist=False, 
        cascade="all, delete-orphan",
        doc="Customer profile data associated with this session"
    )
    
    def __repr__(self) -> str:
        """String representation for debugging and logging.
        
        Only shows first 8 characters of session_key for security.
        """
        return (
            f"<Session("
            f"id={self.id}, "
            f"session_key={self.session_key[:8]}..., "
            f"email={self.email}, "
            f"is_anonymous={self.is_anonymous}"
            f")>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation suitable for API responses and logging.
            Timestamps are converted to ISO format for consistent serialization.
            
        Example:
            >>> session = Session(session_key="abc123", email="user@example.com")
            >>> session.to_dict()
            {
                'id': 'a1b2c3d4-...', 
                'session_key': 'abc123',
                'email': 'user@example.com',
                'is_anonymous': False,
                'created_at': '2024-01-01T12:00:00+00:00',
                'last_activity_at': '2024-01-01T12:30:00+00:00',
                'meta': {},
                'account_id': 'xyz...',
                'account_slug': 'acme',
                'agent_instance_id': 'abc...',
                'agent_instance_slug': 'simple_chat1'
            }
        """
        return {
            "id": str(self.id),
            "session_key": self.session_key,
            "email": self.email,
            "is_anonymous": self.is_anonymous,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity_at": (
                self.last_activity_at.isoformat() 
                if self.last_activity_at else None
            ),
            "meta": self.meta or {},
            "account_id": str(self.account_id) if self.account_id else None,
            "account_slug": self.account_slug,
            "agent_instance_id": str(self.agent_instance_id) if self.agent_instance_id else None,
            "agent_instance_slug": self.agent_instance_slug
        }
