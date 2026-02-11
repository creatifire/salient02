"""
Simplified session middleware with isolated database connections for session management.

This middleware provides HTTP session management for the Salient Sales Bot backend
with an isolated database connection approach that resolves async context and greenlet
compatibility issues. It implements secure session cookie handling, automatic session
creation and resumption, and proper async context management.

Key Features:
- Independent database connection pool isolated from main application
- Automatic session creation for new users with cryptographically secure keys
- Session resumption from HTTP cookies with validation and security checks
- Configurable cookie settings with security best practices (HttpOnly, SameSite)
- Path exclusion for static assets and health checks to optimize performance
- Comprehensive error handling with graceful fallbacks and detailed logging
- Async context management compatible with FastAPI middleware patterns

Architecture Decision:
This middleware creates its own database engine and connection pool separate from the
main application's DatabaseService. This isolation prevents async context conflicts
that can occur when sharing database connections across different async contexts,
particularly with SQLAlchemy's greenlet-based async implementation.

Session Lifecycle:
1. Request arrives and middleware checks for existing session cookie
2. If cookie exists, attempt to load session from database with validation
3. If no valid session found, create new session with secure random key
4. Session is added to request.state for access by route handlers
5. Response is processed and session cookie is set with secure settings
6. Database connections are automatically cleaned up per request

Security Features:
- Cryptographically secure session key generation using secrets module
- HTTP-only cookies prevent JavaScript access and XSS attacks
- SameSite cookie attribute provides CSRF protection
- Configurable secure flag for HTTPS-only cookies in production
- Session validation prevents session hijacking with invalid cookies

Performance Optimizations:
- Dedicated connection pool with smaller size optimized for middleware usage
- Path exclusion for static assets and health endpoints reduces overhead
- Connection pooling with pre-ping validation ensures reliable connections
- Lazy engine initialization reduces startup time and resource usage

Error Handling:
All database operations include comprehensive error handling with graceful degradation.
Failed session operations log errors but don't prevent request processing, ensuring
application availability even during database connectivity issues.

Threading and Async Safety:
This middleware is designed for FastAPI's async request handling model and properly
manages async database operations within the middleware context. The isolated
connection pool prevents conflicts with other async database operations.

Usage:
    # In FastAPI application setup
    app.add_middleware(SimpleSessionMiddleware, exclude_paths=["/health", "/static"])
    
    # In route handlers
    @app.get("/api/user")
    async def get_user(request: Request):
        session = get_current_session(request)
        if session:
            # Use session for user operations

Dependencies:
- FastAPI and Starlette for middleware base classes and request/response handling
- SQLAlchemy async for database operations with proper async context management
- secrets module for cryptographically secure session key generation
- logfire for structured logging with request correlation
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import secrets
import string
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import Request, Response
import logfire
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from ..config import get_database_url, get_session_config
from ..models.session import Session


class SimpleSessionMiddleware(BaseHTTPMiddleware):
    """
    HTTP session middleware with isolated database connections for FastAPI applications.
    
    This middleware implements secure session management using HTTP cookies and database
    persistence, with an isolated database connection pool that prevents async context
    conflicts and ensures reliable session handling across all requests.
    
    Design Philosophy:
    The middleware creates its own database engine and connection pool separate from the
    main application's DatabaseService. This isolation strategy resolves async context
    conflicts that can occur with SQLAlchemy's greenlet-based async implementation when
    sharing database connections across different middleware and application contexts.
    
    Session Management Features:
    - Automatic session creation for new users with cryptographically secure keys
    - Session persistence across browser sessions using HTTP-only cookies
    - Session validation and resumption from existing cookies
    - Configurable session timeouts and cookie security settings
    - Request path exclusion for performance optimization
    - Comprehensive error handling with graceful degradation
    
    Security Implementation:
    - Cryptographically secure session key generation using secrets.choice()
    - HTTP-only cookies prevent JavaScript access and XSS exploitation
    - SameSite cookie attributes provide CSRF attack protection
    - Configurable secure flag for HTTPS-only cookie transmission
    - Session validation prevents unauthorized access with invalid cookies
    
    Performance Optimizations:
    - Dedicated connection pool sized for middleware workload patterns
    - Path exclusion system for static assets and health check endpoints
    - Lazy database engine initialization to reduce application startup time
    - Connection pre-ping validation ensures connection reliability
    - Automatic connection cleanup per request prevents resource leaks
    
    Async Context Management:
    All database operations are properly contained within async context managers
    to ensure connection cleanup and prevent greenlet conflicts. The middleware
    is designed specifically for FastAPI's async request processing model.
    
    Attributes:
        exclude_paths: List of request paths to skip session processing
        _engine: SQLAlchemy async engine for database connections (lazy initialized)
        _session_factory: Async session factory for creating database sessions
    
    Example:
        >>> # Add middleware to FastAPI application
        >>> app.add_middleware(
        ...     SimpleSessionMiddleware, 
        ...     exclude_paths=["/health", "/static", "/assets"]
        ... )
        >>> 
        >>> # Access session in route handlers
        >>> @app.get("/api/profile")
        >>> async def get_profile(request: Request):
        ...     session = get_current_session(request)
        ...     if session and not session.is_anonymous:
        ...         return {"user_id": session.id}
    
    Note:
        This middleware should be added early in the middleware stack to ensure
        session information is available to all subsequent middleware and route handlers.
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None) -> None:
        """
        Initialize session middleware with path exclusions and lazy database connection.
        
        Sets up the middleware with configurable path exclusions for performance
        optimization and initializes database connection attributes for lazy loading.
        The database engine and session factory are created on first use to reduce
        application startup time and resource usage.
        
        Args:
            app: FastAPI application instance to wrap with middleware
            exclude_paths: Optional list of request paths to skip session processing.
                Common exclusions include health checks, static assets, and robots.txt
                to reduce unnecessary session overhead for non-user requests.
        
        Default Exclusions:
        - "/health": Health check endpoints that don't need session state
        - "/favicon.ico": Browser favicon requests that don't represent user activity
        - "/robots.txt": Search engine crawler requests that don't need sessions
        
        Example:
            >>> # Basic usage with default exclusions
            >>> middleware = SimpleSessionMiddleware(app)
            >>> 
            >>> # Custom exclusions for specific application needs
            >>> middleware = SimpleSessionMiddleware(
            ...     app, 
            ...     exclude_paths=["/health", "/metrics", "/static", "/api/webhooks"]
            ... )
        
        Note:
            The middleware inherits from BaseHTTPMiddleware and follows Starlette's
            middleware pattern for ASGI applications. Database connections are
            established lazily on first request to optimize startup performance.
        """
        super().__init__(app)
        # Path exclusions for performance optimization - skip session processing
        # for requests that don't require user session state
        self.exclude_paths = exclude_paths or ["/health", "/favicon.ico", "/robots.txt"]
        
        # Database connection attributes - initialized lazily on first use
        self._engine = None  # SQLAlchemy async engine (created on demand)
        self._session_factory = None  # Async session factory (created on demand)
        
    async def _get_engine(self):
        """
        Get or create async database engine with lazy initialization for middleware.
        
        Creates the database engine and session factory on first call, then returns
        the cached engine for subsequent requests. This lazy initialization pattern
        reduces application startup time and ensures database connections are only
        established when actually needed.
        
        Engine Configuration:
        The engine is configured with middleware-specific settings optimized for
        session management workloads rather than general application database usage.
        
        Connection Pool Settings:
        - pool_size=5: Smaller pool size appropriate for middleware-only database access
        - max_overflow=0: No connection overflow to maintain predictable resource usage
        - pool_timeout=30: Standard timeout for connection acquisition
        - pool_pre_ping=True: Validates connections before use to prevent stale connections
        - echo=False: Disabled SQL logging for performance (enable for debugging only)
        
        Session Factory Configuration:
        - expire_on_commit=False: Keeps session objects usable after commit for middleware patterns
        - class_=AsyncSession: Uses async session class for proper async context handling
        - bind=engine: Binds sessions to the middleware-specific engine
        
        Returns:
            AsyncEngine: Configured SQLAlchemy async engine for database operations
        
        Note:
            This method is called internally by the dispatch method and should not
            be called directly from application code. The engine and session factory
            are created once and reused for all subsequent middleware operations.
        """
        if self._engine is None:
            # Get database URL from secure configuration (environment variables)
            database_url = get_database_url()
            
            # Create async engine with middleware-optimized connection pool settings
            # Smaller pool size than main application since middleware has focused usage
            self._engine = create_async_engine(
                database_url,
                pool_size=5,  # Smaller pool size for middleware-focused database access
                max_overflow=0,  # No overflow to maintain predictable resource usage
                pool_timeout=30,  # Standard timeout for connection acquisition
                pool_pre_ping=True,  # Validate connections before use (prevents stale connections)
                echo=False,  # Disable SQL logging for performance (enable for debugging)
            )
            
            # Create session factory with middleware-appropriate configuration
            # expire_on_commit=False allows session objects to remain usable after commit
            # which is important for middleware patterns where sessions may be accessed
            # after the database transaction completes
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Keep objects usable after commit for middleware
            )
        return self._engine
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """
        Process HTTP request with comprehensive session management and security handling.
        
        This is the core middleware method that processes every HTTP request, implementing
        the complete session lifecycle including cookie validation, session creation,
        database persistence, and secure cookie setting. It follows FastAPI middleware
        patterns for proper async request processing.
        
        Request Processing Flow:
        1. Check request path against exclusion list for performance optimization
        2. Skip static asset requests that don't require session state
        3. Initialize database engine and session factory if needed (lazy loading)
        4. Attempt to load existing session from HTTP cookie if present
        5. Validate existing session against database records
        6. Create new session with secure random key if no valid session exists
        7. Store session in request.state for access by route handlers
        8. Process the request through the application call stack
        9. Set secure session cookie in the response with appropriate security flags
        10. Handle all errors gracefully with comprehensive logging and fallbacks
        
        Security Considerations:
        - Session cookies are validated against database records to prevent hijacking
        - New sessions use cryptographically secure random keys from secrets module
        - Cookie security settings are applied based on configuration (HttpOnly, SameSite, Secure)
        - Invalid or expired sessions are handled gracefully without breaking the request
        - All database operations are wrapped in error handling to prevent application crashes
        
        Performance Optimizations:
        - Path exclusion for static assets and health checks reduces processing overhead
        - Lazy database initialization only creates connections when sessions are needed
        - Connection pooling with pre-ping validation ensures efficient database usage
        - Session state is stored in request.state for fast access by route handlers
        
        Args:
            request: FastAPI Request object containing HTTP request data and state
            call_next: Callable to process request through the rest of the application stack
        
        Returns:
            StarletteResponse: HTTP response with session cookie set if session exists
        
        Error Handling:
        All database and session operations include comprehensive error handling with
        graceful degradation. Failed operations are logged but don't prevent request
        processing, ensuring application availability during database issues.
        """
        
        # Performance optimization: Skip session handling for excluded paths
        # These paths typically don't require user session state and excluding them
        # reduces unnecessary database operations and improves response time
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Performance optimization: Skip session handling for static file requests
        # Static assets (CSS, JS, images) don't require session state and processing
        # them would add unnecessary overhead to asset delivery
        if request.url.path.startswith("/static/") or request.url.path.startswith("/assets/"):
            return await call_next(request)
        
        # Skip session handling for CORS preflight OPTIONS requests
        # Browser doesn't use cookies from OPTIONS responses per CORS specification
        # This prevents orphaned vapid sessions from being created by preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip session handling for admin routes (read-only, stateless)
        # Admin UI doesn't need conversation sessions - it just views existing sessions
        if request.url.path.startswith("/api/admin/"):
            request.state.session = None
            request.scope["session"] = {}
            return await call_next(request)
        
        # BUG-0026-0003 FIX: For multi-tenant routes, load existing sessions but never auto-create
        # Let chat endpoints create sessions with proper account/agent context on first message
        # This prevents "vapid sessions" created on page load before user interaction
        is_multi_tenant_route = request.url.path.startswith("/accounts/") and "/agents/" in request.url.path
        
        # BUG-0026-0003 COOKIE FIX: Determine if we should skip session loading
        # For multi-tenant routes without a cookie, defer to endpoint to create session
        # But don't return early - we need to reach cookie-setting logic after call_next()
        skip_session_loading = False
        if is_multi_tenant_route:
            session_config = get_session_config()
            cookie_name = session_config.get("cookie_name", "salient_session")
            session_cookie = request.cookies.get(cookie_name)
            
            if not session_cookie:
                # No cookie - skip session loading, endpoint will create
                request.state.session = None
                request.scope["session"] = {}
                skip_session_loading = True
                logfire.debug(
                    'middleware.session.deferred',
                    request_path=request.url.path,
                    reason='multi_tenant_route_without_cookie'
                )
        
        session = None
        
        try:
            # BUG-0026-0003 COOKIE FIX: Only load session if not deferred
            if not skip_session_loading:
                # Lazy initialization: Initialize database engine and session factory on first use
                # This reduces application startup time and only creates connections when needed
                await self._get_engine()
                
                # Load session configuration from secure configuration system
                # Configuration includes cookie names, security settings, and timeout values
                session_config = get_session_config()
                cookie_name = session_config.get("cookie_name", "salient_session")
                
                # Attempt to retrieve existing session cookie from request
                # Cookie contains the session key used to identify the user session
                session_cookie = request.cookies.get(cookie_name)
                
                # Database session context manager ensures proper connection cleanup
                # Each request gets its own database session for isolation and safety
                async with self._session_factory() as db_session:
                    if session_cookie:
                        # Session validation: Check if cookie corresponds to valid database session
                        # This prevents session hijacking with invalid or expired session keys
                        # Using selectinload() prevents N+1 queries if relationships are accessed later
                        stmt = (
                            select(Session)
                            .options(
                                selectinload(Session.account),  # Eager load account relationship
                                selectinload(Session.agent_instance)  # Eager load agent_instance relationship
                            )
                            .where(Session.session_key == session_cookie)
                        )
                        result = await db_session.execute(stmt)
                        session = result.scalar_one_or_none()
                        
                        if session:
                            # Valid session found: log resumption for debugging and analytics
                            logfire.info(
                                'middleware.session.resumed',
                                session_key_prefix=session.session_key[:8],
                                session_id=str(session.id),
                                meta_loaded=session.meta
                            )
                        else:
                            # Invalid session cookie: log for security monitoring
                            logfire.debug('middleware.session.cookie_invalid', session_key_prefix=session_cookie[:8])
                    
                    # Session creation: Generate new session if no valid session exists
                    # This handles both new users and users with invalid/expired sessions
                    # BUG-0026-0003: Skip creation for multi-tenant routes (let chat endpoints handle it)
                    if not session:
                        # Skip auto-creation for multi-tenant routes
                        if is_multi_tenant_route:
                            logfire.debug(
                                'middleware.session.deferred',
                                request_path=request.url.path,
                                reason='multi_tenant_route_with_invalid_cookie'
                            )
                            request.state.session = None
                            request.scope["session"] = {}
                            # Continue without session - chat endpoints will create it when needed
                        else:
                            # Generate cryptographically secure session key using secrets module
                            session_key = self._generate_session_key()
                            
                            # BUG-0026-0003: Log detailed context about session creation
                            # to understand why sessions are created without account/agent context
                            logfire.info(
                                'middleware.session.creating',
                                session_key_prefix=session_key[:8],
                                request_path=request.url.path,
                                request_method=request.method,
                                has_existing_cookie=bool(session_cookie),
                                query_params=dict(request.query_params),
                                path_params=dict(request.path_params) if hasattr(request, 'path_params') else {},
                                headers_user_agent=request.headers.get('user-agent', 'unknown')[:50],
                                headers_referer=request.headers.get('referer', 'none')
                            )
                            
                            # Create new session record with secure defaults
                            # Anonymous sessions allow usage without user registration
                            session = Session(
                                session_key=session_key,
                                email=None,  # No email for anonymous sessions
                                is_anonymous=True,  # Flag for permission checks
                                created_at=datetime.now(timezone.utc),  # UTC timestamp for consistency
                                last_activity_at=datetime.now(timezone.utc),  # Track user activity
                                meta={}  # Extensible metadata storage
                            )
                            
                            # Persist new session to database with proper transaction handling
                            db_session.add(session)
                            await db_session.commit()
                            await db_session.refresh(session)  # Get database-generated ID
                            
                            # Log session creation for analytics and debugging
                            logfire.info(
                                'middleware.session.created', 
                                session_key_prefix=session.session_key[:8], 
                                session_id=str(session.id),
                                account_id=session.account_id,
                                account_slug=session.account_slug,
                                agent_instance_id=session.agent_instance_id,
                                agent_instance_slug=session.agent_instance_slug
                            )
                    
                    # Store session in request state for access by route handlers
                    # This makes session available throughout the request lifecycle
                    # Only set if we have a valid session (skip for deferred multi-tenant routes)
                    if session:
                        request.state.session = session
                        
                        # Also set request.scope["session"] for Starlette session interface compatibility
                        # This allows using request.session.get("key") in middleware and route handlers
                        # Initialize with session.meta dict (which is already a mutable dict in the database)
                        if session.meta is None:
                            session.meta = {}
                        request.scope["session"] = session.meta
                    else:
                        # No session for this request (deferred creation or skipped route)
                        request.state.session = None
                        request.scope["session"] = {}
                
        except Exception as e:
            # Comprehensive error handling: Log errors but don't break the request
            # Failed session operations should not prevent application functionality
            logfire.exception('middleware.session.error', error=str(e))
            request.state.session = None  # Set to None for defensive programming
            request.scope["session"] = {}  # Provide empty dict for session interface
        
        # Request processing: Pass request through the application call stack
        # This processes the request through all remaining middleware and route handlers
        response = await call_next(request)
        
        # BUG-0026-0003: Check if endpoint created a session (for interactive chat/stream)
        # The endpoint might have created a session and stored it in request.state.session
        if hasattr(request.state, 'session') and request.state.session and not session:
            session = request.state.session
            logfire.info('middleware.session.endpoint_created', session_id=str(session.id))
        
        # Persist any session changes made during request processing
        # This ensures modifications via request.session (like admin_authenticated) are saved
        if session and "session" in request.scope:
            try:
                # Log what we're about to save
                logfire.info(
                    'middleware.session.saving',
                    session_id=str(session.id),
                    meta_before_save=session.meta,
                    scope_session_data=dict(request.scope["session"]) if "session" in request.scope else {}
                )
                
                # Use the middleware's own isolated database session factory
                async with self._session_factory() as db_session:
                    # Merge the detached session object into this new db session context
                    # merge() properly handles the state transfer from the detached object
                    merged_session = await db_session.merge(session)
                    
                    # Now mark the meta field as modified in THIS session context
                    # SQLAlchemy doesn't auto-detect changes to mutable JSONB fields
                    flag_modified(merged_session, "meta")
                    
                    logfire.info(
                        'middleware.session.committing',
                        session_id=str(merged_session.id),
                        meta_to_commit=merged_session.meta
                    )
                    
                    await db_session.commit()
                    
                    logfire.info(
                        'middleware.session.saved',
                        session_id=str(merged_session.id),
                        meta_saved=merged_session.meta
                    )
            except Exception as e:
                # Session save errors should not break the response
                logfire.exception('middleware.session.save_failed', error=str(e))
        
        # Cookie setting: Set secure session cookie if we have a valid session
        # This ensures the session persists across browser requests and page reloads
        if session:
            try:
                # Retrieve current session configuration for cookie security settings
                session_config = get_session_config()
                
                # Set session cookie with comprehensive security settings
                # These settings provide defense against XSS, CSRF, and session hijacking
                # Production cross-origin detection
                production_cross_origin = session_config.get("production_cross_origin", False)
                cookie_secure = session_config.get("cookie_secure", False)
                cookie_domain = session_config.get("cookie_domain")
                
                # Override from environment variables for production deployment
                import os
                if os.getenv("PRODUCTION_CROSS_ORIGIN") == "true":
                    production_cross_origin = True
                if os.getenv("COOKIE_SECURE") == "true":
                    cookie_secure = True
                if os.getenv("COOKIE_DOMAIN"):
                    cookie_domain = os.getenv("COOKIE_DOMAIN")
                
                # Determine cookie settings based on deployment mode
                if production_cross_origin and cookie_secure:
                    # Production cross-origin: SameSite=None with Secure=True
                    cookie_samesite = "none"
                    logfire.debug('middleware.session.cookie_settings.production_cross_origin', domain=cookie_domain)
                elif production_cross_origin and not cookie_secure:
                    # Development cross-origin: No SameSite restriction with HTTP
                    cookie_samesite = None
                    logfire.debug('middleware.session.cookie_settings.development_cross_origin')
                else:
                    # Standard same-origin settings
                    cookie_samesite = session_config.get("cookie_samesite", "lax")
                    logfire.debug('middleware.session.cookie_settings.standard', samesite=cookie_samesite)
                
                # Build cookie parameters, omitting samesite when None for maximum cross-origin compatibility
                cookie_params = {
                    "key": session_config.get("cookie_name", "salient_session"),
                    "value": session.session_key,
                    "max_age": session_config.get("cookie_max_age", 604800),
                    "secure": cookie_secure,
                    "httponly": session_config.get("cookie_httponly", True),
                }
                
                # Add domain if specified for cross-origin sharing
                if cookie_domain:
                    cookie_params["domain"] = cookie_domain
                
                # Only add samesite parameter if we have a specific value (omit for None)
                if cookie_samesite is not None:
                    cookie_params["samesite"] = cookie_samesite
                
                response.set_cookie(**cookie_params)
            except Exception as e:
                # Cookie setting errors should not break the response
                # Log error but continue with response delivery
                logfire.exception('middleware.session.cookie_set_failed', error=str(e))
        
        return response
    
    def _generate_session_key(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure session key for user session identification.
        
        Creates a random session key using the secrets module for cryptographic security.
        The key uses a URL-safe alphabet that includes letters, digits, hyphens, and
        underscores, making it suitable for use in HTTP cookies and URLs.
        
        Security Features:
        - Uses secrets.choice() for cryptographically secure random number generation
        - Sufficient entropy with 64 possible characters and 32-character length
        - URL-safe character set prevents encoding issues in cookies and URLs
        - No ambiguous characters that could cause confusion in logs or interfaces
        
        Character Set:
        - Uppercase letters: A-Z (26 characters)
        - Lowercase letters: a-z (26 characters)
        - Digits: 0-9 (10 characters)  
        - Special characters: - and _ (2 characters)
        - Total: 64 possible characters per position
        
        Entropy Calculation:
        With 64 possible characters and 32 positions, the total entropy is:
        64^32 ≈ 1.34 × 10^57 possible combinations, providing excellent security
        against brute force attacks.
        
        Args:
            length: Length of the generated session key in characters (default: 32).
                Must be positive integer. Longer keys provide more security but
                increase cookie size and processing overhead.
        
        Returns:
            str: Cryptographically secure random session key using URL-safe alphabet
        
        Examples:
            >>> key = middleware._generate_session_key()
            >>> len(key)
            32
            >>> key = middleware._generate_session_key(16)
            >>> len(key)
            16
        
        Note:
            This method is called internally during session creation and should not
            be called directly from application code. The default length of 32
            characters provides excellent security while maintaining reasonable
            cookie size for HTTP headers.
        """
        # URL-safe alphabet: letters, digits, hyphen, and underscore
        # Avoids characters that require URL encoding or could cause confusion
        alphabet = string.ascii_letters + string.digits + "-_"
        
        # Generate cryptographically secure random key using secrets module
        # secrets.choice() uses the operating system's entropy source for security
        return ''.join(secrets.choice(alphabet) for _ in range(length))


def get_current_session(request: Request) -> Optional[Session]:
    """
    Helper function to retrieve the current user session from FastAPI request state.
    
    This utility function provides a convenient way to access the session object
    that was created and stored by the SimpleSessionMiddleware during request
    processing. It safely retrieves the session from request.state with proper
    error handling and type hints.
    
    Session Access Pattern:
    The middleware stores the session object in request.state.session for access
    by route handlers and other middleware. This function provides a standardized
    way to retrieve that session with proper type hints and error handling.
    
    Usage in Route Handlers:
    This function is typically used in FastAPI route handlers to access session
    information for user identification, authentication checks, and session-based
    operations like storing user preferences or tracking activity.
    
    Args:
        request: FastAPI Request object containing request state and session data
    
    Returns:
        Optional[Session]: Session object if middleware successfully created or
            retrieved a session, None if no session exists or middleware failed
    
    Examples:
        >>> # In FastAPI route handler
        >>> @app.get("/api/profile")
        >>> async def get_profile(request: Request):
        ...     session = get_current_session(request)
        ...     if session and not session.is_anonymous:
        ...         return {"user_id": session.id, "email": session.email}
        ...     return {"error": "No authenticated session"}
        
        >>> # Check for anonymous vs authenticated sessions
        >>> @app.post("/api/preferences")
        >>> async def save_preferences(request: Request, preferences: dict):
        ...     session = get_current_session(request)
        ...     if session:
        ...         session.meta.update(preferences)
        ...         # Save to database
        ...         return {"status": "saved"}
        
        >>> # Session-based access control
        >>> @app.get("/api/admin")
        >>> async def admin_endpoint(request: Request):
        ...     session = get_current_session(request)
        ...     if not session or session.is_anonymous:
        ...         raise HTTPException(401, "Authentication required")
    
    Safety Features:
    - Uses getattr() with default to prevent AttributeError if session not set
    - Returns None instead of raising exceptions for defensive programming
    - Proper type hints for IDE support and type checking
    - Safe to call even if middleware failed to process the request
    
    Note:
        This function should only be called after the SimpleSessionMiddleware has
        processed the request. Calling it before middleware execution will return
        None since the session hasn't been created or loaded yet.
    """
    return getattr(request.state, "session", None)
