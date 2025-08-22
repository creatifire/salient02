"""
Session model for tracking browser sessions and user continuity.

Based on datamodel specification in memorybank/architecture/datamodel.md
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from . import Base


class Session(Base):
    """
    Browser session tracking and user continuity.
    
    Key Features:
    - session_key: Unique identifier stored in browser cookie
    - email: Captured when user provides it during conversation  
    - is_anonymous: Flips to false when email is provided
    - last_activity_at: Updated on each request for session timeout
    - metadata: JSONB field for future extensibility
    
    Usage:
    - Session resumption: Match browser cookie to session_key
    - Email linking: Find sessions with same email value
    - Analytics: Track session duration and activity patterns
    """
    
    __tablename__ = "sessions"
    
    # Primary key - GUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Browser session cookie value - unique across all sessions
    session_key = Column(String(255), unique=True, nullable=False, index=True)
    
    # User email - nullable until provided by user
    email = Column(String(255), nullable=True, index=True)
    
    # Anonymous flag - true until email provided
    is_anonymous = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_activity_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Extensible session data - JSONB for performance and flexibility
    meta = Column(JSONB, nullable=True)
    
    # Relationships (defined with string references to avoid circular imports)
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    llm_requests = relationship("LLMRequest", back_populates="session", cascade="all, delete-orphan")
    profile = relationship("Profile", back_populates="session", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, session_key={self.session_key[:8]}..., email={self.email}, is_anonymous={self.is_anonymous})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "session_key": self.session_key,
            "email": self.email,
            "is_anonymous": self.is_anonymous,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "meta": self.meta
        }
