"""
Session middleware for automatic session management in FastAPI.

This middleware provides transparent session handling:
- Auto-creates sessions for new visitors
- Loads existing sessions from browser cookies
- Updates session activity on each request
- Sets secure session cookies with proper configuration
- Provides session context to route handlers

The middleware runs on every request and ensures that:
1. Every request has an associated session
2. Session activity is tracked automatically
3. Session cookies are managed securely
4. Session data is available in request.state
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import asyncio
from typing import Callable, Optional
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import logfire

from ..database import get_database_service
from ..services.session_service import SessionService, SessionError
from ..models.session import Session


class SessionMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic session management.
    
    This middleware:
    - Checks for existing session cookies on each request
    - Creates new sessions for visitors without valid cookies
    - Updates session activity timestamps automatically
    - Sets secure session cookies in responses
    - Makes session data available to route handlers via request.state.session
    
    The middleware is designed to be transparent - routes don't need to
    explicitly handle session management unless they need session-specific data.
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        """
        Initialize session middleware.
        
        Args:
            app: FastAPI application instance
            exclude_paths: Optional list of paths to exclude from session handling
        """
        super().__init__(app)
        # Paths that don't need session handling (health checks, static files, etc.)
        self.exclude_paths = exclude_paths or ["/health", "/favicon.ico", "/robots.txt"]
        
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """
        Process request with automatic session management.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler in chain
            
        Returns:
            Response with session cookie set if needed
        """
        # Skip session handling for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Skip session handling for static file requests
        if request.url.path.startswith("/static/") or request.url.path.startswith("/assets/"):
            return await call_next(request)
            
        session = None
        session_service = None
        cookie_config = None
        
        try:
            # Get database service and check if it's initialized
            db_service = get_database_service()
            if not db_service.is_initialized:
                logfire.warn('middleware.session.db_not_initialized')
                request.state.session = None
                return await call_next(request)
            
            # Create session service with a new database session
            async with db_service.get_session() as db_session:
                session_service = SessionService(db_session)
                cookie_config = session_service.get_cookie_config()
                
                # Try to load existing session from cookie
                session_cookie = request.cookies.get(cookie_config["key"])
                if session_cookie:
                    session = await session_service.get_session_by_key(session_cookie)
                    
                    if session:
                        # Check if session is still active
                        is_active = await session_service.is_session_active(session)
                        if is_active:
                            # Update activity timestamp
                            await session_service.update_last_activity(session.id)
                            logfire.debug(
                                'middleware.session.resumed',
                                session_id=str(session.id),
                                session_key_prefix=session.session_key[:8],
                                path=request.url.path,
                                client=request.client.host if request.client else None
                            )
                        else:
                            # Session expired, will create new one
                            expired_session_id = str(session.id)
                            session = None
                            logfire.info(
                                'middleware.session.expired',
                                expired_session_id=expired_session_id,
                                path=request.url.path
                            )
                
                # Create new session if none exists or expired
                if not session:
                    session = await session_service.create_session()
                    logfire.info(
                        'middleware.session.created',
                        session_id=str(session.id),
                        session_key_prefix=session.session_key[:8],
                        path=request.url.path,
                        client=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent", "")[:100]  # Truncate for logs
                    )
                
                # Add session to request state for route access
                request.state.session = session
                # Note: We can't pass the session_service since it's tied to this DB session
                # Routes that need session service should create their own
                
        except Exception as e:
            logfire.exception(
                'middleware.session.error',
                error=str(e),
                path=request.url.path,
                client=request.client.host if request.client else None,
                error_type=type(e).__name__
            )
            # Continue without session on error - don't break the app
            request.state.session = None
        
        # Process the request
        response = await call_next(request)
        
        # Set session cookie in response if we have a session
        if session and cookie_config:
            try:
                response.set_cookie(
                    key=cookie_config["key"],
                    value=session.session_key,
                    max_age=cookie_config["max_age"],
                    secure=cookie_config["secure"],
                    httponly=cookie_config["httponly"],
                    samesite=cookie_config["samesite"]
                )
                
                logfire.debug(
                    'middleware.session.cookie_set',
                    session_id=str(session.id),
                    path=request.url.path,
                    cookie_name=cookie_config["key"],
                    max_age=cookie_config["max_age"]
                )
                
            except Exception as e:
                logfire.exception(
                    'middleware.session.cookie_set_failed',
                    error=str(e),
                    session_id=str(session.id) if session else None,
                    path=request.url.path
                )
        
        return response


def get_current_session(request: Request) -> Optional[Session]:
    """
    Helper function to get the current session from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Session object if available, None otherwise
        
    Example:
        @app.get("/api/profile")
        async def get_profile(request: Request):
            session = get_current_session(request)
            if session:
                return {"session_id": str(session.id)}
            return {"error": "No session"}
    """
    return getattr(request.state, "session", None)


def get_session_service(request: Request) -> Optional[SessionService]:
    """
    Helper function to get the session service from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        SessionService instance if available, None otherwise
        
    Example:
        @app.post("/api/update-email")
        async def update_email(request: Request, email: str):
            session = get_current_session(request)
            session_service = get_session_service(request)
            if session and session_service:
                await session_service.update_session_email(session.id, email)
                return {"success": True}
            return {"error": "No session"}
    """
    return getattr(request.state, "session_service", None)


async def require_session(request: Request) -> Session:
    """
    Helper function to get session or raise an error if not available.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Session object
        
    Raises:
        SessionError: If no session is available
        
    Example:
        @app.get("/api/protected")
        async def protected_endpoint(request: Request):
            session = await require_session(request)  # Will raise if no session
            return {"session_id": str(session.id)}
    """
    session = get_current_session(request)
    if not session:
        raise SessionError("No active session available")
    return session
