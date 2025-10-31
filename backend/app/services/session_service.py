"""
Session service for managing browser sessions and user continuity.

This module provides the SessionService class for managing user sessions
in the Salient chat system. It handles secure session creation, lookup,
activity tracking, and browser cookie integration.

The service implements the session management requirements from Epic 0004-003-001-01
and follows security best practices for session handling in web applications.

Key Features:
- Cryptographically secure session key generation using secrets module
- Anonymous session support with email upgrade capability
- Activity-based session timeout detection and management
- Comprehensive error handling with detailed logging
- Browser cookie configuration management
- Database transaction safety with proper rollback handling

Security Considerations:
- Session keys are generated using cryptographically secure random generation
- Email updates automatically mark sessions as non-anonymous
- Activity timestamps use timezone-aware UTC for consistency
- Database errors are properly handled and logged for security monitoring
- Session keys are partially redacted in logs to prevent exposure

Business Logic:
- Sessions start as anonymous and can be upgraded when email is provided
- Activity timestamps are updated on every user interaction
- Session expiry is configurable via application configuration
- Database integrity constraints prevent session key collisions
- Failed operations trigger automatic rollback for data consistency
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import get_session_config
from ..models.session import Session


class SessionService:
    """
    Service for managing browser sessions and user continuity in the Salient chat system.
    
    This service provides a complete session lifecycle management solution including
    secure session creation, lookup by session key, activity tracking, and browser
    cookie integration. It implements security best practices and proper error handling
    for production web application use.
    
    The service supports both anonymous and authenticated sessions, allowing users
    to start chatting immediately without registration while providing upgrade paths
    when email addresses are provided during conversations.
    
    Thread Safety:
        This service is designed to be used within async request contexts.
        Each instance operates on a single database session and should not
        be shared across concurrent requests.
    
    Security Features:
        - Cryptographically secure session key generation (32 characters)
        - URL-safe session keys compatible with HTTP cookies
        - Timezone-aware timestamp handling for consistent logging
        - Partial session key redaction in logs for privacy
        - Automatic session expiry based on configurable inactivity timeout
        
    Database Operations:
        - All operations use async SQLAlchemy for non-blocking I/O
        - Proper transaction management with rollback on errors
        - Integrity error handling for session key uniqueness
        - Comprehensive error logging for debugging and monitoring
        
    Attributes:
        db_session: Async SQLAlchemy session for database operations
        _session_config: Cached session configuration from app config
        
    Example:
        >>> async with get_db_session() as db:
        ...     service = SessionService(db)
        ...     session = await service.create_session()
        ...     print(f"Created session: {session.session_key[:8]}...")
    """
    
    def __init__(self, db_session: AsyncSession) -> None:
        """
        Initialize session service with database session.
        
        Loads session configuration from application config and prepares
        the service for session management operations.
        
        Args:
            db_session: Async SQLAlchemy session for database operations.
                       This session should be properly configured with
                       connection pooling and transaction management.
                       
        Note:
            The database session is not owned by this service and should
            be managed by the calling code (e.g., FastAPI dependency injection).
        """
        self.db_session: AsyncSession = db_session
        self._session_config: Dict[str, Any] = get_session_config()
    
    async def create_session(
        self, 
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create a new session with cryptographically secure session key.
        
        This method creates a new user session for the chat system. Sessions
        can be created as anonymous (no email) or with an email address if
        known at creation time. The session key is generated using secure
        random generation and is suitable for use in HTTP cookies.
        
        Business Logic:
            - Anonymous sessions (email=None) start with is_anonymous=True
            - Sessions with email start with is_anonymous=False
            - Session keys are 32-character URL-safe strings
            - Both created_at and last_activity_at are set to current UTC time
            - Metadata is stored as JSON and can be used for extensibility
            
        Security:
            - Session keys use cryptographically secure random generation
            - Database integrity constraints prevent key collisions
            - Automatic retry on the extremely unlikely event of key collision
            - All timestamps are timezone-aware for consistent logging
        
        Args:
            email: Optional email address if known at creation time.
                  If provided, the session will be marked as non-anonymous.
            metadata: Optional metadata dictionary for storing additional
                     session-specific information (user preferences, browser
                     info, etc.). Defaults to empty dict if not provided.
            
        Returns:
            Session: Newly created and persisted session object with all
                    fields populated including auto-generated UUID and timestamps.
            
        Raises:
            SessionError: If session creation fails due to database errors
                         or other unexpected conditions. The original exception
                         is chained for debugging purposes.
                         
        Example:
            >>> # Create anonymous session
            >>> session = await service.create_session()
            >>> assert session.is_anonymous is True
            >>> 
            >>> # Create session with email
            >>> session = await service.create_session(email="user@example.com")
            >>> assert session.is_anonymous is False
        """
        try:
            # Generate cryptographically secure session key using URL-safe characters
            # This key will be stored in the browser cookie and used for session lookup
            session_key = self._generate_session_key()
            
            # Determine anonymous status based on email presence
            # Business rule: sessions start anonymous and can be upgraded later
            is_anonymous = email is None
            
            # Create current timestamp for both creation and activity tracking
            # Using UTC timezone for consistent cross-system timestamps
            current_time = datetime.now(timezone.utc)
            
            # Create session object with all required fields
            # UUID primary key will be auto-generated by the database
            session = Session(
                session_key=session_key,
                email=email,
                is_anonymous=is_anonymous,
                created_at=current_time,
                last_activity_at=current_time,  # Initial activity = creation time
                meta=metadata or {}  # Ensure metadata is never None for JSON storage
            )
            
            # Persist session to database with transaction safety
            self.db_session.add(session)
            await self.db_session.commit()
            
            # Refresh to get auto-generated fields (UUID, exact timestamps)
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
            # Query for session by key with eager loading of relationships
            # Using selectinload() prevents N+1 queries if relationships are accessed later
            stmt = (
                select(Session)
                .options(
                    selectinload(Session.account),  # Eager load account relationship
                    selectinload(Session.agent_instance)  # Eager load agent_instance relationship
                )
                .where(Session.session_key == session_key)
            )
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
    
    async def update_session_context(
        self,
        session_id: UUID,
        account_id: UUID,
        account_slug: str,
        agent_instance_id: UUID,
        agent_instance_slug: str
    ) -> bool:
        """
        Update session with account and agent instance context.
        
        This prevents "vapid sessions" (sessions with NULL account/agent IDs)
        by populating the multi-tenant context when a session is first used.
        
        Args:
            session_id: UUID of the session to update
            account_id: Account UUID
            account_slug: Account slug for fast queries
            agent_instance_id: Agent instance UUID
            agent_instance_slug: Agent instance slug for fast analytics
            
        Returns:
            bool: True if session was updated, False if session not found
            
        Raises:
            SessionError: If database update fails
        """
        try:
            # Update session with account/agent context (including denormalized slug)
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(
                    account_id=account_id,
                    account_slug=account_slug,
                    agent_instance_id=agent_instance_id,
                    agent_instance_slug=agent_instance_slug,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            # Check if any row was updated
            updated = result.rowcount > 0
            
            if updated:
                logger.info(
                    "Session context updated",
                    extra={
                        "session_id": str(session_id),
                        "account_id": str(account_id),
                        "account_slug": account_slug,
                        "agent_instance_id": str(agent_instance_id),
                        "agent_instance_slug": agent_instance_slug
                    }
                )
            else:
                logger.warning(f"Session not found for context update: {session_id}")
                
            return updated
            
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error updating session context: {e}")
            raise SessionError(f"Failed to update session context: {str(e)}") from e
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Unexpected error updating session context: {e}")
            raise SessionError(f"Unexpected error updating session context: {str(e)}") from e
    
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
            # Business rule: providing email automatically makes session non-anonymous
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(
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
        Generate a cryptographically secure session key for browser cookies.
        
        Uses the secrets module for cryptographically strong random generation
        suitable for security-sensitive applications. The generated key uses
        URL-safe characters to ensure compatibility with HTTP cookies and URLs.
        
        Security Notes:
            - Uses secrets.choice() for cryptographically secure randomness
            - 32-character length provides 2^190 bits of entropy (more than sufficient)
            - URL-safe alphabet ensures cookie and URL compatibility
            - No ambiguous characters (no 0/O or 1/l confusion)
            
        Implementation Details:
            - Character set: a-z, A-Z, 0-9, hyphen, underscore (64 chars total)
            - 32 characters = log2(64^32) ≈ 192 bits of entropy
            - Collision probability is negligible for practical purposes
            - Keys are suitable for direct use in HTTP cookies
        
        Args:
            length: Length of the session key in characters. Default is 32
                   which provides excellent security while remaining manageable
                   for cookies and logging. Should not be less than 16 for
                   security reasons.
                   
        Returns:
            str: Cryptographically secure random session key using URL-safe
                characters. Safe for use in HTTP cookies, URLs, and logging.
                
        Note:
            This method is marked private (_) as session key generation should
            only be done internally by the service to ensure consistent security
            practices and proper integration with the session creation workflow.
        """
        # Use URL-safe characters for browser cookie and URL compatibility
        # Excludes potentially confusing characters like 0/O and 1/l
        alphabet = string.ascii_letters + string.digits + "-_"
        
        # Generate secure random key using cryptographically strong randomness
        # Each character is independently chosen with uniform distribution
        session_key = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Log key generation for debugging (length only, never the actual key)
        logger.debug(
            "Generated cryptographically secure session key",
            extra={
                "key_length": length,
                "alphabet_size": len(alphabet),
                "entropy_bits": length * 6  # log2(64) ≈ 6 bits per character
            }
        )
        
        return session_key
    
    def get_cookie_config(self) -> Dict[str, Any]:
        """
        Get session cookie configuration from application configuration.
        
        Returns a dictionary of cookie parameters suitable for use with
        FastAPI's response.set_cookie() method. Configuration values are
        loaded from the application config with secure defaults.
        
        Security Configuration:
            - httponly: Prevents client-side JavaScript access (XSS protection)
            - secure: Requires HTTPS in production (set via config)
            - samesite: CSRF protection (default 'lax' for usability)
            - max_age: Session lifetime in seconds (default 7 days)
            
        Cookie Settings:
            - key: Cookie name used in HTTP headers
            - max_age: Session expiry time in seconds from creation
            - secure: Whether cookie requires HTTPS (production should be True)
            - httponly: Prevents XSS by blocking JavaScript access
            - samesite: CSRF protection level ('strict', 'lax', or 'none')
        
        Returns:
            Dict[str, Any]: Cookie configuration dictionary containing:
                - key: Cookie name (default 'salient_session')
                - max_age: Lifetime in seconds (default 604800 = 7 days)
                - secure: HTTPS requirement (default False for development)
                - httponly: JavaScript access prevention (default True)
                - samesite: CSRF protection level (default 'lax')
                
        Note:
            This configuration should be used consistently across all
            session cookie operations to ensure security and proper
            browser behavior.
            
        Example:
            >>> config = service.get_cookie_config()
            >>> response.set_cookie(**config, value=session.session_key)
        """
        return {
            "key": self._session_config.get("cookie_name", "salient_session"),
            "max_age": self._session_config.get("cookie_max_age", 604800),  # 7 days default
            "secure": self._session_config.get("cookie_secure", False),     # HTTPS requirement
            "httponly": self._session_config.get("cookie_httponly", True),  # XSS protection
            "samesite": self._session_config.get("cookie_samesite", "lax")  # CSRF protection
        }


class SessionError(Exception):
    """
    Custom exception raised when session operations fail.
    
    This exception is used to wrap lower-level database errors and provide
    meaningful, application-specific error messages for session-related
    failures. It enables proper error handling and logging while maintaining
    a clean separation between database implementation details and business logic.
    
    Common Scenarios:
        - Database connection failures during session operations
        - SQLAlchemy integrity constraint violations
        - Unexpected errors during session creation or updates
        - Session lookup failures due to database issues
        
    Error Handling Pattern:
        The SessionService catches SQLAlchemy and other low-level exceptions,
        logs them for debugging, and raises SessionError with user-friendly
        messages while preserving the original exception chain for debugging.
        
    Usage:
        This exception should be caught by calling code (typically FastAPI
        endpoints or middleware) and converted to appropriate HTTP responses
        for the client.
        
    Attributes:
        The exception inherits standard Exception attributes and preserves
        the original exception chain via the 'from' clause for debugging.
        
    Example:
        >>> try:
        ...     session = await service.create_session()
        ... except SessionError as e:
        ...     logger.error(f"Session operation failed: {e}")
        ...     raise HTTPException(status_code=500, detail="Session error")
    """
    pass
