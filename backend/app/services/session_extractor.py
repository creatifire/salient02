"""
Session field extractor for safe attribute access.

This module provides utilities to extract account-related fields from Session
models as Python primitives, avoiding SQLAlchemy expression serialization issues.

The primary function `get_session_account_fields()` uses direct column queries
to guarantee Python primitive values instead of SQLAlchemy expressions.
"""

from typing import Tuple, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.session import Session


async def get_session_account_fields(
    db_session: AsyncSession,
    session_id: UUID
) -> Tuple[Optional[UUID], Optional[str]]:
    """Extract account_id and account_slug as Python primitives.
    
    Uses direct column query to guarantee Python values, not SQLAlchemy expressions.
    This prevents "Boolean value of this clause is not defined" errors when values
    are passed to Logfire or other serialization systems.
    
    Args:
        db_session: Active SQLAlchemy async session
        session_id: Session UUID to query
        
    Returns:
        Tuple of (account_id, account_slug) as Python primitives.
        Both values will be None if session not found or fields are null.
        
    Example:
        ```python
        async with db_service.get_session() as db_session:
            account_id, account_slug = await get_session_account_fields(
                db_session, UUID(session_id)
            )
            # account_id is Python UUID or None (never SQLAlchemy expression)
            # account_slug is Python str or None (never SQLAlchemy expression)
        ```
    """
    # Query columns directly - guarantees Python primitives, not model attributes
    result = await db_session.execute(
        select(Session.account_id, Session.account_slug)
        .where(Session.id == session_id)
    )
    row = result.first()
    
    if not row:
        return (None, None)
    
    # Row values are guaranteed to be Python primitives
    # account_id: UUID | None (from UUID(as_uuid=True) column)
    # account_slug: str | None (from String column)
    return (row.account_id, row.account_slug)

