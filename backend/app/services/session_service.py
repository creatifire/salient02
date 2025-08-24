"""
Session service for managing browser sessions and user continuity.

This service handles:
- Session creation with secure key generation
- Session lookup and retrieval by session key
- Activity tracking and session timeout management
- Browser cookie management utilities

Based on the session management requirements from Epic 0004-003-001-01.
"""

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from loguru import logger

from ..models.session import Session
from ..config import get_session_config


class SessionService:
    """
    Service for managing browser sessions and user continuity.
    
    Provides secure session creation, lookup, and activity tracking
    with browser cookie integration support.
    """
    
    def __init__(self, db_session: AsyncSession) -> None:
        """
        Initialize session service with database session.
        
        Args:
            db_session: Async SQLAlchemy session for database operations
        """
        self.db_session = db_session
        self._session_config = get_session_config()
    
    async def create_session(
        self, 
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create a new session with secure session key.
        
        Args:
            email: Optional email address if known at creation time
            metadata: Optional metadata dict for extensibility
            
        Returns:
            Session: Newly created session object
            
        Raises:
            SessionError: If session creation fails
        """
        try:
            # Generate secure session key
            session_key = self._generate_session_key()
            
            # Determine anonymous status based on email
            is_anonymous = email is None
            
            # Create session object
            session = Session(
                session_key=session_key,
                email=email,
                is_anonymous=is_anonymous,
                created_at=datetime.now(timezone.utc),
                last_activity_at=datetime.now(timezone.utc),
                meta=metadata or {}
            )
            
            # Add to database
            self.db_session.add(session)
            await self.db_session.commit()
            await self.db_session.refresh(session)
            
            logger.info(
                "Session created successfully",
                extra={
                    "session_id": str(session.id),
                    "session_key": session_key[:8] + "...",  # Log partial key for privacy
                    "email": email,
                    "is_anonymous": is_anonymous
                }
            )
            
            return session
            
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"Session key collision during creation: {e}")
            # Retry with new key on collision (very unlikely with secure generation)
            return await self.create_session(email=email, metadata=metadata)
            
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error during session creation: {e}")
            raise SessionError(f"Failed to create session: {str(e)}") from e
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Unexpected error during session creation: {e}")
            raise SessionError(f"Unexpected error creating session: {str(e)}") from e
    
    async def get_session_by_key(self, session_key: str) -> Optional[Session]:
        """
        Retrieve session by session key.
        
        Args:
            session_key: Browser session key from cookie
            
        Returns:
            Session object if found, None otherwise
            
        Raises:
            SessionError: If database query fails
        """
        try:
            # Query for session by key
            stmt = select(Session).where(Session.session_key == session_key)
            result = await self.db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if session:
                logger.debug(
                    "Session found by key",
                    extra={
                        "session_id": str(session.id),
                        "session_key": session_key[:8] + "...",
                        "email": session.email,
                        "last_activity": session.last_activity_at.isoformat() if session.last_activity_at else None
                    }
                )
            else:
                logger.debug(f"No session found for key: {session_key[:8]}...")
                
            return session
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving session by key: {e}")
            raise SessionError(f"Failed to retrieve session: {str(e)}") from e
            
        except Exception as e:
            logger.error(f"Unexpected error retrieving session by key: {e}")
            raise SessionError(f"Unexpected error retrieving session: {str(e)}") from e
    
    async def update_last_activity(
        self, 
        session_id: UUID, 
        activity_time: Optional[datetime] = None
    ) -> bool:
        """
        Update the last activity timestamp for a session.
        
        Args:
            session_id: UUID of the session to update
            activity_time: Optional timestamp, defaults to current time
            
        Returns:
            bool: True if session was updated, False if session not found
            
        Raises:
            SessionError: If database update fails
        """
        try:
            if activity_time is None:
                activity_time = datetime.now(timezone.utc)
            
            # Update last activity timestamp
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(last_activity_at=activity_time)
            )
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            # Check if any row was updated
            updated = result.rowcount > 0
            
            if updated:
                logger.debug(
                    "Session activity updated",
                    extra={
                        "session_id": str(session_id),
                        "activity_time": activity_time.isoformat()
                    }
                )
            else:
                logger.warning(f"No session found for activity update: {session_id}")
                
            return updated
            
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error updating session activity: {e}")
            raise SessionError(f"Failed to update session activity: {str(e)}") from e
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Unexpected error updating session activity: {e}")
            raise SessionError(f"Unexpected error updating activity: {str(e)}") from e
    
    async def update_session_email(
        self, 
        session_id: UUID, 
        email: str
    ) -> bool:
        """
        Update session with user email and mark as non-anonymous.
        
        Args:
            session_id: UUID of the session to update
            email: User's email address
            
        Returns:
            bool: True if session was updated, False if session not found
            
        Raises:
            SessionError: If database update fails
        """
        try:
            # Update email and anonymous status
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .                values(
                    email=email,
                    is_anonymous=False,
                    last_activity_at=datetime.now(timezone.utc)
                )
            )
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            # Check if any row was updated
            updated = result.rowcount > 0
            
            if updated:
                logger.info(
                    "Session email updated",
                    extra={
                        "session_id": str(session_id),
                        "email": email,
                        "is_anonymous": False
                    }
                )
            else:
                logger.warning(f"No session found for email update: {session_id}")
                
            return updated
            
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error updating session email: {e}")
            raise SessionError(f"Failed to update session email: {str(e)}") from e
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Unexpected error updating session email: {e}")
            raise SessionError(f"Unexpected error updating email: {str(e)}") from e
    
    async def is_session_active(
        self, 
        session: Session, 
        inactivity_minutes: Optional[int] = None
    ) -> bool:
        """
        Check if a session is still active based on last activity.
        
        Args:
            session: Session object to check
            inactivity_minutes: Optional timeout override, uses config default if None
            
        Returns:
            bool: True if session is active, False if expired
        """
        if not session.last_activity_at:
            return False
            
        # Get inactivity timeout from config or parameter
        if inactivity_minutes is None:
            inactivity_minutes = self._session_config.get("inactivity_minutes", 30)
        
        # Calculate expiry time
        expiry_time = session.last_activity_at + timedelta(minutes=inactivity_minutes)
        current_time = datetime.now(timezone.utc)
        
        is_active = current_time < expiry_time
        
        logger.debug(
            "Session activity check",
            extra={
                "session_id": str(session.id),
                "last_activity": session.last_activity_at.isoformat(),
                "current_time": current_time.isoformat(),
                "expiry_time": expiry_time.isoformat(),
                "is_active": is_active,
                "inactivity_minutes": inactivity_minutes
            }
        )
        
        return is_active
    
    def _generate_session_key(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure session key.
        
        Args:
            length: Length of the session key (default 32 characters)
            
        Returns:
            str: Secure random session key
        """
        # Use URL-safe characters for browser cookie compatibility
        alphabet = string.ascii_letters + string.digits + "-_"
        session_key = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        logger.debug(f"Generated session key of length {length}")
        
        return session_key
    
    def get_cookie_config(self) -> Dict[str, Any]:
        """
        Get session cookie configuration from app config.
        
        Returns:
            dict: Cookie configuration parameters
        """
        return {
            "key": self._session_config.get("cookie_name", "salient_session"),
            "max_age": self._session_config.get("cookie_max_age", 604800),  # 7 days
            "secure": self._session_config.get("cookie_secure", False),
            "httponly": self._session_config.get("cookie_httponly", True),
            "samesite": self._session_config.get("cookie_samesite", "lax")
        }


class SessionError(Exception):
    """
    Exception raised when session operations fail.
    
    Used to wrap database errors and provide meaningful error messages
    for session-related failures.
    """
    pass
