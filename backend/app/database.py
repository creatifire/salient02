"""
Database service module for async session management and connection pooling.

This module provides centralized database connectivity for the Salient Sales Bot
backend, implementing the repository pattern with async SQLAlchemy and connection
pooling for optimal performance and resource management.

Key Features:
- Async SQLAlchemy engine with connection pooling configuration
- Session factory for creating properly configured async sessions
- Database health checks with detailed connection status reporting
- Context manager support for automatic session lifecycle management
- Graceful startup/shutdown handling with resource cleanup
- Global service instance pattern for application-wide database access
- FastAPI dependency injection support for route handlers

Architecture:
The DatabaseService uses a singleton pattern via get_database_service() to ensure
a single database connection pool across the application. This approach prevents
connection pool exhaustion and provides consistent database configuration.

Connection Pooling:
Configured with conservative defaults to handle production workloads while
maintaining resource efficiency. Pool settings are tunable via configuration
to accommodate different deployment environments.

Security:
Database URL must be provided via environment variables (never in configuration
files) to prevent credential exposure. All sessions support automatic rollback
on exceptions to maintain data consistency.

Usage:
    # Application startup
    await initialize_database()
    
    # In service classes
    db_service = get_database_service()
    async with db_service.get_session() as session:
        result = await session.execute(query)
        await session.commit()
    
    # FastAPI dependency injection
    @app.get("/api/endpoint")
    async def endpoint(session: AsyncSession = Depends(get_db_session)):
        # Use session for database operations

Thread Safety:
All operations are thread-safe and designed for async/await usage patterns.
The connection pool handles concurrent requests safely.

Performance Considerations:
- Connection pooling reduces connection overhead
- Session factory eliminates repetitive configuration
- Health checks use minimal resources
- Proper cleanup prevents resource leaks

Dependencies:
- SQLAlchemy 2.0+ with async support
- asyncpg driver for PostgreSQL
- loguru for structured logging
- configuration module for database settings
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine, 
    AsyncSession, 
    async_sessionmaker, 
    create_async_engine
)

from .config import get_database_config, get_database_url
from .models import Base


class DatabaseService:
    """
    Async database service with connection pooling and session management.
    
    This service provides a centralized database interface for the Salient Sales Bot
    backend, implementing best practices for async database operations, connection
    pooling, and resource management.
    
    Key Responsibilities:
    - Manage async SQLAlchemy engine with optimized connection pooling
    - Provide session factory for creating properly configured async sessions
    - Implement health check capabilities for monitoring and diagnostics
    - Handle graceful startup and shutdown with resource cleanup
    - Support context manager pattern for automatic session management
    
    Connection Pool Configuration:
    The service uses conservative pool settings optimized for web application
    workloads. Pool size and overflow settings can be tuned via configuration
    to accommodate different deployment scenarios (development, staging, production).
    
    Session Management:
    Sessions are created with automatic rollback on exceptions and proper cleanup
    to prevent resource leaks. The context manager pattern ensures sessions are
    always properly closed, even when exceptions occur.
    
    Thread Safety:
    All methods are thread-safe and designed for concurrent usage in async
    environments. The underlying SQLAlchemy engine handles connection pooling
    safely across multiple coroutines and threads.
    
    Attributes:
        _engine: SQLAlchemy async engine instance for database connections
        _session_factory: Factory for creating configured async sessions
        _is_initialized: Boolean flag tracking service initialization status
    
    Example:
        >>> service = DatabaseService()
        >>> await service.initialize()
        >>> async with service.get_session() as session:
        ...     result = await session.execute(text("SELECT 1"))
        ...     await session.commit()
        >>> await service.shutdown()
    
    Note:
        This class follows the singleton pattern when used via get_database_service()
        to ensure consistent database configuration across the application.
    """
    
    def __init__(self) -> None:
        """
        Initialize database service with default state.
        
        Sets up internal attributes for the async engine, session factory, and
        initialization status. The service must be explicitly initialized via
        the initialize() method before use.
        
        All attributes start as None or False to indicate uninitialized state.
        This prevents accidental usage before proper configuration.
        """
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """
        Initialize the database engine and session factory with connection pooling.
        
        Loads database configuration from environment variables and creates an async
        SQLAlchemy engine with optimized connection pool settings. Also sets up the
        session factory for creating properly configured database sessions.
        
        Connection Pool Settings:
        - pool_size: Number of persistent connections (default: 20)
        - max_overflow: Additional connections beyond pool_size (default: 0)
        - pool_timeout: Seconds to wait for connection (default: 30)
        - pool_pre_ping: Validates connections before use (always True)
        
        Session Factory Configuration:
        - expire_on_commit=False: Keeps objects usable after commit
        - autoflush=True: Automatically flushes before queries
        - autocommit=False: Requires explicit commit() calls
        
        Raises:
            ValueError: If DATABASE_URL environment variable is missing
            SQLAlchemyError: If database connection or configuration fails
            Exception: For any other initialization errors
        
        Note:
            This method is idempotent - calling it multiple times is safe and
            will only log a warning for subsequent calls.
        """
        if self._is_initialized:
            logger.warning("Database service already initialized")
            return
            
        try:
            # Load database configuration from environment and YAML
            db_config = get_database_config()
            database_url = get_database_url()
            
            # Extract pool configuration with defaults optimized for web workloads
            pool_size = db_config.get("pool_size", 20)
            max_overflow = db_config.get("max_overflow", 0)
            pool_timeout = db_config.get("pool_timeout", 30)
            
            # Create async engine with connection pooling
            # pool_pre_ping=True ensures connections are valid before use
            # echo=False prevents SQL logging in production (set to True for debugging)
            self._engine = create_async_engine(
                database_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_pre_ping=True,  # Validate connections before use
                echo=False,  # Set to True for SQL debugging
                future=True,  # Use SQLAlchemy 2.0 style
            )
            
            # Create session factory with async session configuration
            # expire_on_commit=False keeps objects usable after commit
            # This is important for async usage patterns where objects may be
            # accessed after the session transaction completes
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Keep objects usable after commit
                autoflush=True,  # Automatically flush before queries
                autocommit=False,  # Require explicit commit() calls
            )
            
            self._is_initialized = True
            logger.info(
                "Database service initialized successfully",
                extra={
                    "pool_size": pool_size,
                    "max_overflow": max_overflow,
                    "pool_timeout": pool_timeout,
                    "engine_echo": False,
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            # Re-raise to ensure application fails fast on database issues
            raise

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the database service and cleanup resources.
        
        Properly disposes of the SQLAlchemy engine and cleans up the connection
        pool to prevent resource leaks. This method should be called during
        application shutdown to ensure all database connections are closed.
        
        The shutdown process:
        1. Checks if service is initialized (safe to call multiple times)
        2. Disposes of the async engine and its connection pool
        3. Resets all internal state to allow re-initialization if needed
        4. Logs successful shutdown for monitoring
        
        Raises:
            Exception: If engine disposal fails (re-raised after logging)
        
        Note:
            This method is idempotent - calling it on an uninitialized service
            or multiple times is safe and will not raise errors.
        """
        if not self._is_initialized:
            return
            
        try:
            if self._engine:
                # Dispose of the engine and its connection pool
                # This closes all active connections and releases resources
                await self._engine.dispose()
                logger.info("Database engine disposed successfully")
                
            # Reset internal state to allow re-initialization
            self._engine = None
            self._session_factory = None
            self._is_initialized = False
            
        except Exception as e:
            logger.error(f"Error during database shutdown: {e}")
            # Re-raise to indicate shutdown failure to calling code
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session with automatic cleanup and transaction management.
        
        Provides a context manager that creates a new database session from the
        session factory and ensures proper cleanup regardless of success or failure.
        Implements automatic rollback on exceptions to maintain data consistency.
        
        Transaction Management:
        - Session is created from the configured session factory
        - Automatic rollback occurs if any exception is raised
        - Session is always closed in the finally block
        - Caller is responsible for explicit commit() on success
        
        Usage Patterns:
            # Basic usage with explicit commit
            async with db_service.get_session() as session:
                user = User(name="John", email="john@example.com")
                session.add(user)
                await session.commit()
            
            # Query operations (no commit needed)
            async with db_service.get_session() as session:
                result = await session.execute(select(User).where(User.id == 1))
                user = result.scalar_one_or_none()
            
            # Exception handling (automatic rollback)
            try:
                async with db_service.get_session() as session:
                    # If this fails, rollback happens automatically
                    await session.execute(some_complex_operation())
                    await session.commit()
            except SomeError:
                # Session was already rolled back and closed
                handle_error()
        
        Yields:
            AsyncSession: Configured database session ready for use
        
        Raises:
            RuntimeError: If database service is not initialized
            SQLAlchemyError: For database-related errors during session creation
            Exception: Any exception from the calling code (after rollback)
        
        Note:
            This method ensures the session is always properly closed, even if
            exceptions occur. The session factory configuration ensures optimal
            settings for async usage patterns.
        """
        if not self._is_initialized or not self._session_factory:
            raise RuntimeError(
                "Database service not initialized. Call initialize() first."
            )
            
        # Create new session from factory with configured settings
        session = self._session_factory()
        try:
            yield session
        except Exception:
            # Rollback transaction on any exception to maintain consistency
            await session.rollback()
            raise
        finally:
            # Always close session to return connection to pool
            await session.close()

    async def health_check(self) -> Dict[str, str | bool]:
        """
        Perform a comprehensive database health check with detailed status reporting.
        
        Executes a simple SQL query to verify database connectivity, engine health,
        and session creation capabilities. This method is designed for monitoring
        and diagnostic purposes, providing actionable information about database
        status.
        
        Health Check Process:
        1. Verifies service initialization status
        2. Creates a new session using the session factory
        3. Executes a simple "SELECT 1" query to test connectivity
        4. Validates query result to ensure proper database response
        5. Returns structured health information for monitoring systems
        
        Return Values:
        - status: "healthy" or "unhealthy" indicating overall database state
        - message: Descriptive message explaining the current status
        - connected: Boolean indicating if database connection is active
        
        Use Cases:
        - Application startup verification
        - Health check endpoints for load balancers
        - Monitoring system integration
        - Diagnostic troubleshooting
        
        Returns:
            Dict[str, str | bool]: Health status dictionary with keys:
                - status: "healthy" or "unhealthy"
                - message: Human-readable status description
                - connected: Boolean connection status
        
        Example:
            >>> health = await db_service.health_check()
            >>> if health["status"] == "healthy":
            ...     print("Database is ready")
            >>> else:
            ...     print(f"Database issue: {health['message']}")
        
        Note:
            This method uses minimal resources and is safe to call frequently
            for monitoring purposes. It does not impact application performance.
        """
        if not self._is_initialized:
            return {
                "status": "unhealthy",
                "message": "Database service not initialized",
                "connected": False
            }
            
        try:
            async with self.get_session() as session:
                # Execute simple query to test database connectivity
                # Using text() for explicit SQL to avoid ORM overhead
                result = await session.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()
                
                # Validate expected result to ensure database is responding correctly
                if row and row[0] == 1:
                    return {
                        "status": "healthy",
                        "message": "Database connection successful",
                        "connected": True
                    }
                else:
                    return {
                        "status": "unhealthy", 
                        "message": "Database query returned unexpected result",
                        "connected": False
                    }
                    
        except SQLAlchemyError as e:
            # Log SQLAlchemy-specific errors for debugging
            logger.error(f"Database health check failed with SQLAlchemy error: {e}")
            return {
                "status": "unhealthy",
                "message": f"Database error: {str(e)}",
                "connected": False
            }
        except Exception as e:
            # Log unexpected errors that might indicate broader issues
            logger.error(f"Unexpected error during database health check: {e}")
            return {
                "status": "unhealthy",
                "message": f"Unexpected error: {str(e)}",
                "connected": False
            }

    @property
    def is_initialized(self) -> bool:
        """
        Check if the database service is initialized and ready for use.
        
        Returns:
            bool: True if initialize() has been called successfully, False otherwise
        
        Note:
            This property is useful for conditional logic and debugging purposes.
            Most methods will raise RuntimeError if called on uninitialized service.
        """
        return self._is_initialized

    @property
    def engine(self) -> AsyncEngine:
        """
        Get the async SQLAlchemy engine for advanced use cases.
        
        Provides direct access to the underlying SQLAlchemy async engine for
        advanced database operations that require engine-level access. Most
        applications should use get_session() instead for normal operations.
        
        Advanced Use Cases:
        - Creating database metadata and tables
        - Running raw SQL that doesn't fit session patterns
        - Engine-level configuration or inspection
        - Integration with other SQLAlchemy tools
        
        Returns:
            AsyncEngine: The configured SQLAlchemy async engine
        
        Raises:
            RuntimeError: If database service is not initialized
        
        Example:
            >>> engine = db_service.engine
            >>> async with engine.begin() as conn:
            ...     await conn.execute(text("CREATE INDEX ..."))
        
        Warning:
            Direct engine usage bypasses session management and should be used
            carefully. Prefer get_session() for normal database operations.
        """
        if not self._engine:
            raise RuntimeError(
                "Database service not initialized. Call initialize() first."
            )
        return self._engine


# Global database service instance for application-wide access
# This implements the singleton pattern to ensure consistent database configuration
_db_service: DatabaseService | None = None


def get_database_service() -> DatabaseService:
    """
    Get the global database service instance using singleton pattern.
    
    Creates a new DatabaseService instance on first call, then returns the same
    instance for all subsequent calls. This ensures consistent database
    configuration and connection pooling across the entire application.
    
    Singleton Pattern Benefits:
    - Single connection pool shared across all components
    - Consistent configuration throughout application lifecycle
    - Memory efficient (one service instance per application)
    - Thread-safe access to database functionality
    
    Returns:
        DatabaseService: The global database service instance
    
    Note:
        The returned service still needs to be initialized via initialize()
        before use. This separation allows for controlled service startup.
    
    Example:
        >>> db_service = get_database_service()
        >>> await db_service.initialize()
        >>> async with db_service.get_session() as session:
        ...     # Use database session
    """
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


async def initialize_database() -> None:
    """
    Initialize the global database service for application startup.
    
    Convenience function that gets the global database service instance and
    calls its initialize() method. This is typically called during application
    startup to establish database connectivity.
    
    Initialization Process:
    1. Gets or creates the global DatabaseService instance
    2. Loads configuration from environment and YAML files
    3. Creates async engine with connection pooling
    4. Sets up session factory for creating database sessions
    5. Logs successful initialization
    
    Raises:
        ValueError: If DATABASE_URL environment variable is missing
        SQLAlchemyError: If database connection fails
        Exception: For any other initialization errors
    
    Usage:
        # In application startup (e.g., FastAPI lifespan)
        await initialize_database()
    
    Note:
        This function is idempotent and safe to call multiple times.
    """
    db_service = get_database_service()
    await db_service.initialize()


async def shutdown_database() -> None:
    """
    Shutdown the global database service for application cleanup.
    
    Convenience function that properly shuts down the global database service
    and resets the global instance. This ensures all database connections are
    closed and resources are cleaned up during application shutdown.
    
    Shutdown Process:
    1. Checks if global database service exists
    2. Calls service shutdown() to dispose engine and connections
    3. Resets global instance to None for clean state
    4. Logs successful shutdown
    
    Raises:
        Exception: If engine disposal fails during shutdown
    
    Usage:
        # In application shutdown (e.g., FastAPI lifespan)
        await shutdown_database()
    
    Note:
        This function is idempotent and safe to call multiple times or
        when no database service exists.
    """
    global _db_service
    if _db_service:
        await _db_service.shutdown()
        _db_service = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency function for injecting database sessions into routes.
    
    This function serves as a FastAPI dependency that provides database sessions
    to route handlers. It uses the global database service to create sessions
    with proper lifecycle management and automatic cleanup.
    
    Dependency Features:
    - Automatic session creation from the global service
    - Proper session cleanup via context manager
    - Exception handling with automatic rollback
    - Connection pooling through the global service
    
    FastAPI Integration:
    The Depends() mechanism calls this function for each request that declares
    the dependency, ensuring each route gets a fresh database session.
    
    Usage in FastAPI routes:
        @app.get("/api/users/{user_id}")
        async def get_user(
            user_id: int, 
            session: AsyncSession = Depends(get_db_session)
        ):
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
    
    Yields:
        AsyncSession: Configured database session for the request
    
    Raises:
        RuntimeError: If database service is not initialized
        SQLAlchemyError: For database-related errors
    
    Note:
        Each request gets its own session instance, but all sessions share
        the same connection pool for efficiency.
    """
    db_service = get_database_service()
    async with db_service.get_session() as session:
        yield session
