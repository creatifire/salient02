"""
Services package for business logic and data access layer.

This package contains service classes that handle:
- Session management and user tracking
- Message persistence and chat history
- LLM request tracking and cost monitoring
- Profile data collection and management

Services follow dependency injection patterns and use async/await
for database operations.
"""

from .session_service import SessionService

__all__ = ["SessionService"]
