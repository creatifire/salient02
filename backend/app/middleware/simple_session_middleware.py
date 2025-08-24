"""
Simplified session middleware that creates its own database connections.

This is a temporary version to test if the issue is with database service sharing
or if there's a fundamental greenlet/async issue.
"""

import secrets
import string
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from loguru import logger

from ..models.session import Session
from ..config import get_database_url, get_session_config


class SimpleSessionMiddleware(BaseHTTPMiddleware):
    """
    Simplified session middleware that creates its own database connections.
    
    This version bypasses the shared database service to isolate potential
    async context or greenlet issues.
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/favicon.ico", "/robots.txt"]
        self._engine = None
        self._session_factory = None
        
    async def _get_engine(self):
        """Get or create async engine for this middleware."""
        if self._engine is None:
            database_url = get_database_url()
            self._engine = create_async_engine(
                database_url,
                pool_size=5,  # Smaller pool for middleware
                max_overflow=0,
                pool_timeout=30,
                pool_pre_ping=True,
                echo=False,
            )
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._engine
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Process request with simplified session management."""
        
        # Skip session handling for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Skip session handling for static file requests
        if request.url.path.startswith("/static/") or request.url.path.startswith("/assets/"):
            return await call_next(request)
            
        session = None
        
        try:
            # Initialize engine if needed
            await self._get_engine()
            
            # Get session configuration
            session_config = get_session_config()
            cookie_name = session_config.get("cookie_name", "salient_session")
            
            # Try to load existing session from cookie
            session_cookie = request.cookies.get(cookie_name)
            
            async with self._session_factory() as db_session:
                if session_cookie:
                    # Try to find existing session
                    stmt = select(Session).where(Session.session_key == session_cookie)
                    result = await db_session.execute(stmt)
                    session = result.scalar_one_or_none()
                    
                    if session:
                        logger.debug(f"Session resumed: {session.session_key[:8]}...")
                    else:
                        logger.debug(f"Session cookie invalid: {session_cookie[:8]}...")
                
                # Create new session if none exists
                if not session:
                    session_key = self._generate_session_key()
                    session = Session(
                        session_key=session_key,
                        email=None,
                        is_anonymous=True,
                        created_at=datetime.now(timezone.utc),
                        last_activity_at=datetime.now(timezone.utc),
                        meta={}
                    )
                    
                    db_session.add(session)
                    await db_session.commit()
                    await db_session.refresh(session)
                    
                    logger.info(f"New session created: {session.session_key[:8]}...")
                
                # Add session to request state
                request.state.session = session
                
        except Exception as e:
            logger.error(f"Simple session middleware error: {e}")
            request.state.session = None
        
        # Process the request
        response = await call_next(request)
        
        # Set session cookie if we have a session
        if session:
            try:
                session_config = get_session_config()
                response.set_cookie(
                    key=session_config.get("cookie_name", "salient_session"),
                    value=session.session_key,
                    max_age=session_config.get("cookie_max_age", 604800),
                    secure=session_config.get("cookie_secure", False),
                    httponly=session_config.get("cookie_httponly", True),
                    samesite=session_config.get("cookie_samesite", "lax")
                )
            except Exception as e:
                logger.error(f"Failed to set session cookie: {e}")
        
        return response
    
    def _generate_session_key(self, length: int = 32) -> str:
        """Generate a cryptographically secure session key."""
        alphabet = string.ascii_letters + string.digits + "-_"
        return ''.join(secrets.choice(alphabet) for _ in range(length))


def get_current_session(request: Request) -> Optional[Session]:
    """Helper function to get the current session from request state."""
    return getattr(request.state, "session", None)
