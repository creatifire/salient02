"""
Database service module for async session management and connection pooling.

This module provides:
- Async SQLAlchemy engine and session management
- Connection pooling configuration
- Database health checks
- Session lifecycle management
- Graceful startup/shutdown handling

Used by all persistence services (sessions, messages, LLM requests, profiles).
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from loguru import logger

from app.config import get_database_config, get_database_url
from app.models import Base


class DatabaseService:
    """
    Async database service with connection pooling and session management.
    
    Provides:
    - Async engine with connection pooling
    - Session factory for creating async sessions
    - Health check capabilities
    - Graceful startup/shutdown
    """
    
    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the database engine and session factory."""
        if self._is_initialized:
            logger.warning("Database service already initialized")
            return
            
        try:
            # Load database configuration
            db_config = get_database_config()
            database_url = get_database_url()
            
            # Create async engine with connection pooling
            self._engine = create_async_engine(
                database_url,
                pool_size=db_config.get("pool_size", 20),
                max_overflow=db_config.get("max_overflow", 0),
                pool_timeout=db_config.get("pool_timeout", 30),
                pool_pre_ping=True,  # Validate connections before use
                echo=False,  # Set to True for SQL debugging
                future=True,  # Use SQLAlchemy 2.0 style
            )
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Keep objects usable after commit
                autoflush=True,
                autocommit=False,
            )
            
            self._is_initialized = True
            logger.info(
                "Database service initialized",
                extra={
                    "pool_size": db_config.get("pool_size"),
                    "max_overflow": db_config.get("max_overflow"),
                    "pool_timeout": db_config.get("pool_timeout"),
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise

    async def shutdown(self) -> None:
        """Gracefully shutdown the database service."""
        if not self._is_initialized:
            return
            
        try:
            if self._engine:
                await self._engine.dispose()
                logger.info("Database engine disposed")
                
            self._engine = None
            self._session_factory = None
            self._is_initialized = False
            
        except Exception as e:
            logger.error(f"Error during database shutdown: {e}")
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session with automatic cleanup.
        
        Usage:
            async with db_service.get_session() as session:
                # Use session for database operations
                result = await session.execute(...)
                await session.commit()
        """
        if not self._is_initialized or not self._session_factory:
            raise RuntimeError("Database service not initialized")
            
        session = self._session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def health_check(self) -> dict[str, str | bool]:
        """
        Perform a database health check.
        
        Returns:
            dict: Health status with connection info
        """
        if not self._is_initialized:
            return {
                "status": "unhealthy",
                "message": "Database service not initialized",
                "connected": False
            }
            
        try:
            async with self.get_session() as session:
                # Simple query to test connection
                result = await session.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()
                
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
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Database error: {str(e)}",
                "connected": False
            }
        except Exception as e:
            logger.error(f"Unexpected error during health check: {e}")
            return {
                "status": "unhealthy",
                "message": f"Unexpected error: {str(e)}",
                "connected": False
            }

    @property
    def is_initialized(self) -> bool:
        """Check if the database service is initialized."""
        return self._is_initialized

    @property
    def engine(self) -> AsyncEngine:
        """Get the async engine (for advanced use cases)."""
        if not self._engine:
            raise RuntimeError("Database service not initialized")
        return self._engine


# Global database service instance
_db_service: DatabaseService | None = None


def get_database_service() -> DatabaseService:
    """Get the global database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


async def initialize_database() -> None:
    """Initialize the global database service."""
    db_service = get_database_service()
    await db_service.initialize()


async def shutdown_database() -> None:
    """Shutdown the global database service."""
    global _db_service
    if _db_service:
        await _db_service.shutdown()
        _db_service = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI to get database sessions.
    
    Usage in FastAPI routes:
        @app.get("/api/endpoint")
        async def my_endpoint(session: AsyncSession = Depends(get_db_session)):
            # Use session for database operations
    """
    db_service = get_database_service()
    async with db_service.get_session() as session:
        yield session
