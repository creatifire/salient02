"""
SQLAlchemy models for Salient chat memory system.

This module provides the database models for Epic 0004: Chat Memory & Persistence.
Models follow the datamodel specification in memorybank/architecture/datamodel.md.

Key Features:
- GUID primary keys for all entities
- Async SQLAlchemy 2.0 compatibility
- JSONB fields for extensible metadata
- Proper foreign key relationships
- Support for future multi-tenant architecture

Models:
- Session: Browser session tracking and user continuity
- Message: Complete chat history with role-based messages
- LLMRequest: LLM usage tracking for cost analysis
- Profile: Incremental customer profile data collection
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

# Create the declarative base for all models
Base = declarative_base()

# Import all models to make them available
from .session import Session
from .message import Message
from .llm_request import LLMRequest
from .profile import Profile

__all__ = [
    "Base",
    "Session", 
    "Message",
    "LLMRequest", 
    "Profile"
]
