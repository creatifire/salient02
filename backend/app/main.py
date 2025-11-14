"""
Salient Sales Bot FastAPI backend application with comprehensive chat and session management.

This module implements the main FastAPI application for the Salient Sales Bot backend,
providing a production-ready web service with real-time chat capabilities, secure session
management, and comprehensive monitoring. It serves as the primary entry point for all
HTTP requests and orchestrates the interaction between frontend, database, and LLM services.

Application Architecture:
The application follows a layered architecture with clear separation of concerns:
- Presentation Layer: HTMX-enabled frontend with server-side rendering
- API Layer: RESTful endpoints and Server-Sent Events for real-time communication
- Business Logic Layer: Session management, chat processing, and LLM integration
- Data Layer: Async database service with connection pooling and persistence
- Infrastructure Layer: Logging, health monitoring, and configuration management

Core Features:
- Real-time chat interface with HTMX frontend for dynamic user interactions
- Server-Sent Events (SSE) streaming for live LLM response delivery
- Async database persistence for chat history, sessions, and user profiles
- Comprehensive health monitoring with database connectivity checks
- Structured logging with JSON format, rotation, and retention policies
- Secure session management with HTTP-only cookies and CSRF protection
- OpenRouter LLM integration with streaming responses and cost optimization

API Endpoints:
- GET /: Main chat interface with configurable UI features and session handling
- GET /health: Comprehensive health check including database connectivity status
- GET /events/stream: Server-Sent Events endpoint for streaming LLM responses
- POST /chat: Non-streaming chat endpoint for fallback compatibility
- GET /api/session: Session information endpoint for debugging and development
- GET /dev/logs/tail: Development log tailing endpoint (configurable access)

Session Management:
Automatic session creation and management using SimpleSessionMiddleware with:
- Cryptographically secure session keys for user identification
- HTTP-only cookies with configurable security settings (Secure, SameSite)
- Database persistence for session continuity across browser sessions
- Anonymous session support for users without explicit registration
- Session validation and automatic cleanup for security and performance

Security Features:
- Environment-based configuration preventing credential exposure in code
- HTTP-only session cookies preventing XSS attacks via JavaScript access
- SameSite cookie attributes providing CSRF protection
- Input validation and sanitization for all user-provided data
- Comprehensive error handling with security-conscious logging
- Configurable CORS policies and rate limiting capabilities (future enhancement)

Performance Optimizations:
- Async request handling with FastAPI for high concurrency support
- Database connection pooling with configurable pool sizes and timeouts
- Lazy loading of configuration and services to reduce startup time
- Path-based middleware exclusions for static assets and health checks
- Efficient Server-Sent Events streaming with connection management

Production Readiness:
- Graceful application lifecycle management with proper startup/shutdown sequences
- Comprehensive health checks for monitoring and load balancer integration
- Structured JSON logging with configurable levels, rotation, and retention
- Configuration-driven feature flags for environment-specific deployment
- Error handling with graceful degradation and detailed diagnostic information

Development Features:
- Live log tailing endpoint for real-time debugging and monitoring
- Session information API for development and troubleshooting
- Configurable frontend debug modes and feature toggles
- Development-friendly error messages and diagnostic information

Dependencies:
- FastAPI: Modern async web framework with automatic API documentation
- Starlette: ASGI foundation with middleware support and SSE capabilities
- SQLAlchemy: Async ORM for database operations with connection pooling
- Jinja2: Template engine for server-side HTML rendering
- Logfire: Observability platform with structured logging, tracing, and metrics
- OpenRouter: LLM API integration for chat completion and streaming

Usage:
    # Production deployment
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
    
    # Development with auto-reload
    uvicorn backend.app.main:app --reload --reload-dir backend
    
    # Configuration via environment variables
    export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"
    export OPENROUTER_API_KEY="your-api-key"
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import asyncio
import glob
import json
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Load environment variables from .env file at project root
# Must be done before any other imports that depend on env vars (Logfire, database, etc.)
from dotenv import load_dotenv
import os

# Determine project root (../../ from backend/app/main.py)
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
load_dotenv(dotenv_path=env_file)
print(f"✅ Environment variables loaded from: {env_file}")
print(f"   LOGFIRE_TOKEN: {'SET' if os.getenv('LOGFIRE_TOKEN') else 'NOT SET'}")

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from markdown_it import MarkdownIt
from sse_starlette.sse import EventSourceResponse
import logfire

from .config import load_config
from .database import get_database_service, initialize_database, shutdown_database
from .middleware.simple_session_middleware import SimpleSessionMiddleware, get_current_session
from .openrouter_client import chat_completion_content, stream_chat_chunks
from .services.message_service import get_message_service


# Application directory structure for template and static file serving
# BASE_DIR: Points to the backend/ directory for accessing templates and config
# TEMPLATES_DIR: Jinja2 template directory for HTML rendering
# STATIC_DIR: Static assets directory for serving images, CSS, JS files
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Initialize markdown renderer for processing assistant messages
# Configure with GFM-like features including tables for comprehensive markdown support
markdown_renderer = MarkdownIt("default", {"breaks": True, "html": False}).enable(['table'])

# Configure Logfire observability at module level (before app creation)
# This must happen early to properly initialize OpenTelemetry instrumentation
try:
    logfire.configure()
    print("✅ Logfire configured successfully")
except Exception as e:
    # Log Logfire configuration errors for debugging
    # App can run without observability if token is missing or invalid
    print(f"⚠️  Logfire configuration failed: {type(e).__name__}: {e}")
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI application lifespan management with graceful startup and shutdown sequences.
    
    This async context manager handles the complete application lifecycle, ensuring
    proper initialization of all services during startup and clean resource cleanup
    during shutdown. It replaces the deprecated @app.on_event pattern with the
    modern FastAPI lifespan approach for better resource management and error handling.
    
    Startup Sequence:
    1. Configure structured logging with rotation and retention policies
    2. Initialize database service with connection pooling and health checks
    3. Verify database connectivity and log initialization status
    4. Handle initialization errors with proper logging and application failure
    
    Shutdown Sequence:
    1. Log application shutdown initiation for monitoring and debugging
    2. Gracefully close database connections and dispose of connection pools
    3. Ensure all background tasks complete before application termination
    4. Log successful shutdown or any errors encountered during cleanup
    
    Error Handling:
    All initialization and shutdown operations include comprehensive error handling
    with structured logging. Startup failures result in application termination
    to prevent running in an inconsistent state, while shutdown errors are logged
    but don't prevent application exit.
    
    Benefits over @app.on_event:
    - Better resource management with async context manager pattern
    - Guaranteed cleanup execution even if startup fails
    - Improved error handling and logging capabilities
    - Modern FastAPI pattern recommended for production applications
    
    Args:
        app: FastAPI application instance (provided by FastAPI framework)
    
    Yields:
        None: Control to the FastAPI application during normal operation
    
    Raises:
        Exception: Re-raises any startup errors to prevent application start with
            incomplete initialization, ensuring fail-fast behavior for reliability
    """
    # Startup sequence: Initialize all application services and dependencies
    logfire.info('app.startup.begin')
    
    try:
        # Initialize database service with connection pooling and health verification
        await initialize_database()
        logfire.info('app.startup.database_initialized')
    except Exception as e:
        # Log startup failure and re-raise to prevent application start
        logfire.error('app.startup.database_init_failed', error=str(e))
        raise  # Fail-fast: don't start application with incomplete initialization
    
    # Yield control to FastAPI application - normal operation begins here
    yield  # Application runs here
    
    # Shutdown sequence: Clean up all resources and close connections gracefully
    logfire.info('app.shutdown.begin')
    try:
        # Gracefully shutdown database connections and dispose of connection pools
        await shutdown_database()
        logfire.info('app.shutdown.database_closed')
    except Exception as e:
        # Log shutdown errors but don't prevent application exit
        logfire.error('app.shutdown.database_error', error=str(e))


# FastAPI application instance with comprehensive configuration
# Title and lifespan management for production deployment
app = FastAPI(title="Salient Backend", lifespan=lifespan)

# Logfire Instrumentation: Automatic tracing for FastAPI, Pydantic AI, Pydantic, and HTTPX
# This captures all HTTP requests, LLM calls, model validation, external API calls, and OpenTelemetry GenAI attributes
try:
    logfire.instrument_fastapi(app)
    logfire.instrument_pydantic_ai()
    logfire.instrument_pydantic()  # Trace all Pydantic model validation
    logfire.instrument_httpx()  # Trace all outbound HTTP requests (OpenRouter, etc.)
    print("✅ Logfire instrumentation complete (FastAPI + Pydantic AI + Pydantic + HTTPX)")
except Exception as e:
    # Log instrumentation errors for debugging
    # App can run without Logfire instrumentation if configuration failed
    print(f"⚠️  Logfire instrumentation failed: {type(e).__name__}: {e}")
    pass

# CORS Middleware Configuration: Enable cross-origin requests for development
# Allows frontend (localhost:4321) to communicate with backend (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321", "http://127.0.0.1:4321"],  # Frontend origins
    allow_credentials=True,  # Enable session cookie sharing
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Middleware Configuration: Session management with path exclusions
# SimpleSessionMiddleware provides automatic session creation, validation, and persistence
# Excluded paths are optimized for performance (health checks, static assets, dev tools)
app.add_middleware(
    SimpleSessionMiddleware,
    exclude_paths=["/health", "/favicon.ico", "/robots.txt", "/dev/logs/tail", "/static", "/api/config"]
)

# Static file serving configuration for assets (images, CSS, JS)
# Mount static files directory for serving SVG icons and other assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Template engine configuration for server-side rendering
# Jinja2Templates provides HTML template rendering with context injection for dynamic content
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))



async def _load_chat_history_for_session(session_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Load chat history for a session with UI-optimized formatting.
    
    Retrieves recent chat messages for the given session and formats them
    for immediate display in the chat UI. The function handles pagination,
    role filtering, and content preparation to ensure optimal user experience
    during session resumption.
    
    Chat History Strategy:
    - Loads recent messages (configurable limit via app.yaml chat.history_limit, default 50)
    - Excludes system messages from UI display (keeps conversation clean)
    - Formats messages for immediate HTML rendering without additional processing
    - Handles empty history gracefully with no visual artifacts
    - Provides error recovery for database connection issues
    
    Message Formatting:
    Each returned message contains:
    - role: 'human' or 'assistant' for proper CSS styling
    - content: Message text ready for display (sanitized/validated)
    - timestamp: Creation time for debugging and analytics
    - message_id: Unique identifier for future reference
    
    Performance Considerations:
    - Configurable message limit (app.yaml chat.history_limit) to prevent slow page loads
    - Uses efficient database queries with proper indexing and ORDER BY + LIMIT
    - Graceful degradation if message service is unavailable
    - Minimal processing overhead during template rendering
    
    Args:
        session_id: UUID of the session to load history for
    
    Returns:
        List of formatted message dictionaries for template rendering.
        Returns empty list if no messages or on error (graceful degradation).
    
    Example Return Value:
        [
            {
                "role": "human",
                "content": "Hello, what products do you offer?",
                "timestamp": "2024-01-01T10:00:00Z",
                "message_id": "550e8400-e29b-41d4-a716-446655440000"
            },
            {
                "role": "assistant", 
                "content": "We offer SmartFresh storage solutions...",
                "timestamp": "2024-01-01T10:00:05Z",
                "message_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        ]
    
    Error Handling:
    - Database connection errors: Returns empty list, logs warning
    - Invalid session_id: Returns empty list, logs error
    - Message service unavailable: Returns empty list, continues gracefully
    - No messages found: Returns empty list (normal case)
    
    Security Notes:
    - Session isolation enforced at database level
    - Content returned as-is (no additional sanitization needed for templates)
    - Message IDs included for audit trails and debugging
    """
    try:
        # Get message service for database operations
        message_service = get_message_service()
        
        # Load recent messages (configurable limit) excluding system messages for cleaner UI
        # Use proper SQLAlchemy 2.0 async syntax to get most recent messages first
        from sqlalchemy import desc, select
        from sqlalchemy.orm import selectinload
        from .models.message import Message
        
        # Get configurable history limit from app config
        config = load_config()
        chat_config = config.get("chat", {})
        default_history_limit = chat_config.get("history_limit", 50)
        
        # For agent-specific limits, we could extend this later to check agent config
        # For now, use the global chat history limit
        history_limit = default_history_limit

        db_service = get_database_service()
        async with db_service.get_session() as db_session:
            # Build query for most recent N messages (descending order by created_at)
            # Using selectinload() prevents N+1 queries if relationships are accessed later
            stmt = (
                select(Message)
                .options(
                    selectinload(Message.session),  # Eager load session relationship
                    selectinload(Message.agent_instance),  # Eager load agent_instance relationship
                    selectinload(Message.llm_request)  # Eager load llm_request relationship
                )
                .where(Message.session_id == session_id)
                .order_by(desc(Message.created_at))
                .limit(history_limit)
            )
            
            # Execute query and get results
            result = await db_session.execute(stmt)
            messages = result.scalars().all()
            
            # Reverse to get chronological order (oldest first) for natural conversation flow
            messages = list(reversed(messages))
        
        # Format messages for template rendering
        formatted_history = []
        for msg in messages:
            # Skip system messages in UI display (keep conversation clean)
            if msg.role == "system":
                continue
                
            # Map roles for frontend display
            display_role = "user" if msg.role == "human" else "bot"
            
            # Process content based on configuration and role
            processed_content = msg.content
            if display_role == "bot":
                # Get configuration for HTML processing
                cfg = load_config()
                ui_cfg = cfg.get("ui") or {}
                allow_basic_html = ui_cfg.get("allow_basic_html", True)
                
                # Render markdown for assistant messages if HTML is allowed
                if allow_basic_html and processed_content:
                    try:
                        processed_content = markdown_renderer.render(processed_content)
                    except Exception as e:
                        logfire.warn(
                            'app.chat_history.markdown_render_failed',
                            session_id=str(session_id),
                            message_id=str(msg.id),
                            error=str(e)
                        )
                        # Fallback to original content if markdown rendering fails
                        processed_content = msg.content
            
            formatted_message = {
                "role": display_role,
                "content": processed_content,
                "raw_content": msg.content,  # Store original for copying
                "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                "message_id": str(msg.id),
                "original_role": msg.role  # Preserve original for debugging
            }
            formatted_history.append(formatted_message)
        
        logfire.info(
            'app.chat_history.loaded',
            session_id=str(session_id),
            message_count=len(formatted_history),
            total_messages=len(messages)
        )
        
        return formatted_history
        
    except Exception as e:
        # Graceful degradation - return empty history on any error
        logfire.error(
            'app.chat_history.load_error',
            session_id=str(session_id),
            error=str(e),
            error_type=type(e).__name__
        )
        return []



# Multi-Tenant Account-Agent Instance Router Registration
# Include multi-tenant endpoints for account-scoped agent instances
from .api.account_agents import router as account_agents_router
app.include_router(account_agents_router)

# Admin API Router Registration
# Include admin debugging endpoints for chat tracing and LLM inspection
from .api.admin import router as admin_router
app.include_router(admin_router)
