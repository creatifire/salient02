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
- Loguru: Advanced logging with structured output and rotation support
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

# Logfire Instrumentation: Automatic tracing for FastAPI and Pydantic AI
# This captures all HTTP requests, LLM calls, and OpenTelemetry GenAI attributes
try:
    logfire.instrument_fastapi(app)
    logfire.instrument_pydantic_ai()
    print("✅ Logfire instrumentation complete (FastAPI + Pydantic AI)")
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


def _register_legacy_endpoints() -> None:
    """Register legacy endpoints conditionally based on configuration."""
    config = load_config()
    legacy_config = config.get("legacy", {})
    
    if legacy_config.get("enabled", True):
        # Register legacy endpoints with their original decorators
        app.get("/", response_class=HTMLResponse)(serve_base_page)
        app.get("/events/stream")(sse_stream) 
        app.post("/chat", response_class=PlainTextResponse)(chat_fallback)
        
        logger.info({
            "event": "legacy_endpoints_registered",
            "endpoints": ["/", "/events/stream", "/chat"],
            "enabled": True
        })
    else:
        logger.info({
            "event": "legacy_endpoints_disabled", 
            "message": "Legacy endpoints disabled via configuration",
            "enabled": False
        })


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
                        logger.warning({
                            "event": "markdown_render_failed",
                            "session_id": str(session_id),
                            "message_id": str(msg.id),
                            "error": str(e)
                        })
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
        
        logger.info({
            "event": "chat_history_loaded",
            "session_id": str(session_id),
            "message_count": len(formatted_history),
            "total_messages": len(messages)
        })
        
        return formatted_history
        
    except Exception as e:
        # Graceful degradation - return empty history on any error
        logger.error({
            "event": "chat_history_load_error", 
            "session_id": str(session_id),
            "error": str(e),
            "error_type": type(e).__name__
        })
        return []


async def serve_base_page(request: Request) -> HTMLResponse:
    """
    Serve the main chat interface with HTMX-enabled dynamic interactions and chat history.
    
    This endpoint renders the primary chat page using server-side templates with
    configuration-driven feature flags and session-aware rendering. It provides
    the foundation for the chat application with configurable UI settings and
    comprehensive session tracking for analytics and debugging.
    
    Chat History Loading:
    Automatically loads existing chat history when a session resumes, enabling
    seamless conversation continuity across browser refreshes and visits. The
    history is pre-populated in the template for immediate display without
    additional API calls.
    
    Template Rendering:
    Uses Jinja2Templates to render index.html with context data including:
    - Configuration-driven feature flags for UI behavior
    - Input handling settings (debounce, shortcuts, newline behavior)
    - Debug toggles for development and troubleshooting
    - Session information for personalization and tracking
    - Pre-loaded chat history for session continuity
    
    Configuration Integration:
    Loads settings from app.yaml with environment variable overrides:
    - UI configuration for feature flags and visual settings
    - Chat input configuration for user interaction behavior
    - Logging configuration for frontend debug capabilities
    - Security settings for exposing backend functionality
    - Chat history configuration for load limits and filtering
    
    Session Handling:
    Automatically retrieves current session via SimpleSessionMiddleware for:
    - User activity tracking and analytics
    - Session continuity across page reloads
    - Debugging and monitoring capabilities
    - Personalization and user experience optimization
    - Chat history loading and persistence
    
    Security Features:
    - Configurable backend chat exposure via expose_backend_chat flag
    - Session tracking with partial key logging for privacy
    - User agent and client IP logging for security monitoring
    - Input validation through template context injection
    - Session-isolated chat history access
    
    Returns:
        HTMLResponse: Rendered HTML page with HTMX capabilities, dynamic configuration,
            and pre-loaded chat history, or 404 Not Found if backend chat UI is disabled
    
    Example:
        GET / HTTP/1.1
        Cookie: salient_session=abc123...
        
        Returns HTML page with embedded configuration and chat history:
        <div data-debounce-ms="250" data-submit-shortcut="ctrl+enter">
            <div id="chatPane" class="chat">
                <!-- Pre-loaded chat history messages -->
            </div>
        </div>
    """
    # Get session information for logging and history loading
    session = get_current_session(request)
    logger.info({
        "event": "serve_base_page",
        "path": "/",
        "client": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "session_id": str(session.id) if session else None,
        "session_key": session.session_key[:8] + "..." if session else None,
    })
    
    cfg = load_config()
    ui_cfg = cfg.get("ui") or {}
    
    # Gate exposure of backend chat UI
    if not ui_cfg.get("expose_backend_chat", True):
        return HTMLResponse("Not Found", status_code=404)
    
    input_cfg = (cfg.get("chat") or {}).get("input") or {}
    logging_cfg = cfg.get("logging") or {}
    
    # Load chat history for session continuity
    chat_history = []
    if session:
        chat_history = await _load_chat_history_for_session(session.id)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            # Inject as data-* attributes for client-side UX tuning
            "debounce_ms": str(input_cfg.get("debounce_ms", 250)),
            "submit_shortcut": str(input_cfg.get("submit_shortcut", "ctrl+enter")),
            "enter_inserts_newline": "true" if input_cfg.get("enter_inserts_newline", True) else "false",
            # Frontend debug console toggle
            "frontend_debug": "true" if logging_cfg.get("frontend_debug", False) else "false",
            # Feature flags
            "sse_enabled": "true" if ui_cfg.get("sse_enabled", True) else "false",
            "allow_basic_html": "true" if ui_cfg.get("allow_basic_html", True) else "false",
            # Chat history for session continuity
            "chat_history": chat_history,
        },
    )


@app.get("/api/config", response_class=JSONResponse)
async def get_frontend_config(request: Request) -> JSONResponse:
    """
    Get frontend configuration settings from app.yaml.
    
    Provides a centralized API endpoint for frontend components to retrieve
    configuration settings, ensuring consistent behavior across all chat
    integration strategies. This eliminates the need for environment variable
    duplication and hardcoded settings in frontend code.
    
    Returns:
        JSONResponse: Frontend configuration object with ui and chat settings
    """
    cfg = load_config()
    
    # Extract only frontend-relevant configuration
    frontend_config = {
        "ui": {
            "sse_enabled": cfg.get("ui", {}).get("sse_enabled", True),
            "allow_basic_html": cfg.get("ui", {}).get("allow_basic_html", True),
        },
        "chat": {
            "input": cfg.get("chat", {}).get("input", {})
        }
    }
    
    return JSONResponse(frontend_config)


@app.get("/health")
async def health() -> dict:
    """
    Comprehensive health check endpoint for monitoring and load balancer integration.
    
    This endpoint provides detailed health status information including database
    connectivity verification, service availability checks, and diagnostic data
    for monitoring systems, load balancers, and operational dashboards.
    
    Health Check Components:
    1. Database connectivity test with connection pool validation
    2. Application service status verification
    3. Timestamp for monitoring freshness and response time tracking
    4. Structured status reporting for automated health monitoring
    
    Database Health Verification:
    Performs active database connectivity test by:
    - Obtaining database service instance from global service registry
    - Executing database health check with connection validation
    - Testing query execution and response validation
    - Reporting connection pool status and database responsiveness
    
    Response Format:
    Returns structured JSON with hierarchical service status:
    - Overall status: "healthy" or "unhealthy" based on critical services
    - Timestamp: ISO format timestamp for monitoring and debugging
    - Services: Detailed status for each application component
    - Error details: Diagnostic information when health checks fail
    
    Monitoring Integration:
    Designed for integration with:
    - Load balancers (HAProxy, NGINX, cloud load balancers)
    - Container orchestration health checks (Docker, Kubernetes)
    - Monitoring systems (Prometheus, Datadog, New Relic)
    - Alerting systems for proactive incident response
    
    Error Handling:
    Comprehensive error handling ensures endpoint availability even when:
    - Database connections fail or timeout
    - Service initialization is incomplete
    - Configuration loading encounters errors
    - Unexpected exceptions occur during health verification
    
    Returns:
        dict: Structured health status with overall status, timestamp, and detailed
            service-specific health information including error details when applicable
    
    Status Codes:
        200: Always returned (health status in response body)
        
    Example Responses:
        Healthy:
        {
            "status": "healthy",
            "timestamp": "2024-01-15T12:00:00Z",
            "services": {
                "database": {"status": "healthy", "connected": true, "message": "..."},
                "application": {"status": "healthy", "message": "Application running normally"}
            }
        }
        
        Unhealthy:
        {
            "status": "unhealthy", 
            "timestamp": "2024-01-15T12:00:00Z",
            "error": "Database connection failed",
            "services": {...}
        }
    """
    try:
        # Get database health status
        db_service = get_database_service()
        db_health = await db_service.health_check()
        
        # Overall health based on database status
        overall_status = "healthy" if db_health.get("connected") else "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_health,
                "application": {
                    "status": "healthy",
                    "message": "Application running normally"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "services": {
                "database": {
                    "status": "unknown",
                    "message": "Database health check failed"
                },
                "application": {
                    "status": "healthy",
                    "message": "Application running normally"
                }
            }
        }


async def sse_stream(request: Request):
    """
    SSE endpoint that streams incremental text chunks with message persistence.

    This endpoint provides Server-Sent Events streaming for LLM responses while
    maintaining complete message persistence and session tracking. It accumulates
    streaming chunks and saves both user and assistant messages to the database.

    Query params (optional):
    - message: seed text to stream back token-by-token (defaults to demo text)
    - llm: "1" to use actual LLM, otherwise demo mode

    Persistence Flow:
    1. Save user message to database before streaming starts
    2. Accumulate assistant message chunks during streaming
    3. Save complete assistant message when streaming ends
    4. Maintain session continuity and chat history

    Returns:
        EventSourceResponse: Streaming SSE response with message persistence
    """
    # Get session information for context and message persistence
    session = get_current_session(request)
    if not session:
        logger.error("No session available for SSE request")
        return HTMLResponse("Session error", status_code=500)
    
    cfg = load_config()
    # Gate by ui.sse_enabled
    if not (cfg.get("ui") or {}).get("sse_enabled", True):
        return HTMLResponse("SSE disabled", status_code=403)

    # Use agent-first configuration cascade for model settings
    from .agents.config_loader import get_agent_model_settings
    model_settings = await get_agent_model_settings("simple_chat")
    model = model_settings["model"]
    temperature = float(model_settings["temperature"])
    max_tokens = int(model_settings["max_tokens"])

    seed = request.query_params.get("message")
    use_llm = request.query_params.get("llm") == "1"

    logger.info({
        "event": "sse_request",
        "path": "/events/stream",
        "client": request.client.host if request.client else None,
        "params": dict(request.query_params),
        "llm": use_llm,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "session_id": str(session.id),
        "session_key": session.session_key[:8] + "..." if session.session_key else None,
        "message_preview": seed[:100] + "..." if seed and len(seed) > 100 else seed,
    })
    
    # DEBUG: Log config loading details (using agent-first cascade)
    logger.info({
        "event": "sse_config_debug", 
        "model_settings": model_settings,
        "final_model": model,
        "cascade_source": "agent-first configuration cascade"
    })

    # Save user message to database before streaming starts (if provided)
    message_service = get_message_service()
    user_message_id = None
    
    if seed and seed.strip():
        try:
            user_message_id = await message_service.save_message(
                session_id=session.id,
                role="human",
                content=seed.strip(),
                metadata={"source": "sse_stream", "model": model}
            )
            logger.info({
                "event": "user_message_saved",
                "session_id": str(session.id),
                "message_id": str(user_message_id),
                "content_length": len(seed.strip())
            })
        except Exception as e:
            # Log error but continue with streaming functionality
            logger.error({
                "event": "user_message_save_failed",
                "session_id": str(session.id),
                "error": str(e),
                "error_type": type(e).__name__
            })

    async def event_generator():
        # Accumulate assistant message chunks for persistence
        assistant_chunks = []
        start = time.perf_counter()  # Track timing for LLM request
        
        try:
            if use_llm and seed:
                # Build optional headers for OpenRouter (recommended)
                headers = {}
                try:
                    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
                    host = request.headers.get("host")
                    if host:
                        headers["HTTP-Referer"] = f"{scheme}://{host}/"
                except Exception:
                    pass
                try:
                    app_name = (load_config().get("app") or {}).get("name", "SalesBot")
                    headers["X-Title"] = app_name
                except Exception:
                    pass
                
                # DEBUG: Log exact parameters passed to stream_chat_chunks
                logger.info({
                    "event": "stream_chat_chunks_call_debug",
                    "message": seed,
                    "model": model,
                    "temperature": temperature, 
                    "max_tokens": max_tokens,
                    "extra_headers": headers or None,
                    "function": "stream_chat_chunks"
                })
                
                # Stream LLM response while accumulating chunks
                async for tok in stream_chat_chunks(
                    message=seed,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    extra_headers=headers or None,
                ):
                    if await request.is_disconnected():
                        logger.info({
                            "event": "sse_disconnected",
                            "path": "/events/stream",
                        })
                        break
                    
                    # Accumulate chunk for persistence
                    assistant_chunks.append(tok)
                    
                    # Stream chunk to client
                    yield {"data": tok}
                    await asyncio.sleep(0.04)
                
                # Save complete assistant message to database
                if assistant_chunks and not await request.is_disconnected():
                    complete_response = "".join(assistant_chunks)
                    try:
                        assistant_message_id = await message_service.save_message(
                            session_id=session.id,
                            role="assistant",
                            content=complete_response,
                            metadata={
                                "source": "sse_stream",
                                "model": model,
                                "temperature": temperature,
                                "max_tokens": max_tokens,
                                "user_message_id": str(user_message_id) if user_message_id else None,
                                "streaming": True
                            }
                        )
                        logger.info({
                            "event": "assistant_message_saved",
                            "session_id": str(session.id),
                            "message_id": str(assistant_message_id),
                            "content_length": len(complete_response),
                            "chunks_count": len(assistant_chunks)
                        })
                        
                        # Track LLM request for billing (estimated token counts for streaming)
                        try:
                            from ..services.llm_request_tracker import LLMRequestTracker
                            from decimal import Decimal
                            from uuid import UUID
                            
                            # Estimate tokens (rough: ~4 chars per token)
                            estimated_prompt_tokens = len(seed) // 4
                            estimated_completion_tokens = len(complete_response) // 4
                            estimated_total = estimated_prompt_tokens + estimated_completion_tokens
                            
                            tracker = LLMRequestTracker()
                            llm_request_id = await tracker.track_llm_request(
                                session_id=UUID(str(session.id)),
                                provider="openrouter",
                                model=model,
                                request_body={
                                    "message_length": len(seed),
                                    "method": "sse_stream",
                                    "streaming": True
                                },
                                response_body={
                                    "response_length": len(complete_response),
                                    "chunks_count": len(assistant_chunks)
                                },
                                tokens={
                                    "prompt": estimated_prompt_tokens,
                                    "completion": estimated_completion_tokens,
                                    "total": estimated_total
                                },
                                cost_data={
                                    "unit_cost_prompt": 0.0,
                                    "unit_cost_completion": 0.0,
                                    "total_cost": Decimal("0.0")  # Streaming doesn't include cost
                                },
                                latency_ms=int((time.perf_counter() - start) * 1000)
                            )
                            logger.info({
                                "event": "llm_request_tracked",
                                "session_id": str(session.id),
                                "llm_request_id": str(llm_request_id),
                                "estimated_tokens": estimated_total,
                                "note": "Token estimates from streaming (no exact counts available)"
                            })
                        except Exception as track_error:
                            # Log tracking error but don't break streaming
                            logger.warning({
                                "event": "llm_request_tracking_failed",
                                "session_id": str(session.id),
                                "error": str(track_error),
                                "error_type": type(track_error).__name__
                            })
                        
                    except Exception as e:
                        # Log error but don't interrupt streaming
                        logger.error({
                            "event": "assistant_message_save_failed",
                            "session_id": str(session.id),
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "content_length": len(complete_response)
                        })
                
                # Graceful end signal
                if not await request.is_disconnected():
                    yield {"event": "end", "data": "end"}
            else:
                # Demo mode: simulate tokenization and latency
                msg = seed or "This is a streaming demo using Server-Sent Events."
                tokens = msg.split()
                # Honor a rough max_tokens cap
                count = 0
                for tok in tokens:
                    if await request.is_disconnected():
                        logger.info({
                            "event": "sse_disconnected",
                            "path": "/events/stream",
                        })
                        break
                    if count >= max_tokens:
                        break
                    
                    # Accumulate chunk for persistence
                    assistant_chunks.append(tok + " ")
                    
                    # Stream chunk to client
                    yield {"data": tok + " "}
                    count += 1
                    await asyncio.sleep(0.12)
                
                # Include a short footer with config context
                footer = f"\n[model={model} temp={temperature} max_tokens={max_tokens}]"
                assistant_chunks.append(footer)
                
                if not await request.is_disconnected():
                    yield {"data": footer}
                    
                    # Save demo response to database
                    complete_response = "".join(assistant_chunks)
                    try:
                        assistant_message_id = await message_service.save_message(
                            session_id=session.id,
                            role="assistant",
                            content=complete_response,
                            metadata={
                                "source": "sse_stream_demo",
                                "model": model,
                                "temperature": temperature,
                                "max_tokens": max_tokens,
                                "user_message_id": str(user_message_id) if user_message_id else None,
                                "streaming": True,
                                "demo_mode": True
                            }
                        )
                        logger.info({
                            "event": "assistant_message_saved",
                            "session_id": str(session.id),
                            "message_id": str(assistant_message_id),
                            "content_length": len(complete_response),
                            "chunks_count": len(assistant_chunks),
                            "demo_mode": True
                        })
                    except Exception as e:
                        # Log error but don't interrupt streaming
                        logger.error({
                            "event": "assistant_message_save_failed",
                            "session_id": str(session.id),
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "content_length": len(complete_response),
                            "demo_mode": True
                        })
                    
                    # Graceful end signal
                    yield {"event": "end", "data": "end"}
        except Exception as exc:
            logger.error({
                "event": "sse_error",
                "path": "/events/stream",
                "error": type(exc).__name__,
            })
            if not await request.is_disconnected():
                yield {"event": "error", "data": f"stream_error: {type(exc).__name__}"}
        finally:
            logger.info({
                "event": "sse_complete",
                "path": "/events/stream",
            })

    return EventSourceResponse(event_generator())


async def chat_fallback(request: Request) -> PlainTextResponse:
    """
    Non-stream fallback chat endpoint with comprehensive message persistence.
    
    This endpoint provides a synchronous alternative to the SSE streaming endpoint,
    returning complete assistant responses in a single HTTP response. It includes
    full message persistence, session tracking, and maintains compatibility with
    existing frontend implementations.
    
    Message Persistence Flow:
    1. Save user message to database before LLM call
    2. Process LLM request with OpenRouter integration
    3. Save assistant response to database after completion
    4. Return response while maintaining existing format
    
    Session Integration:
    - Automatically links messages to current browser session
    - Enables conversation history and continuity
    - Supports session-based analytics and tracking
    
    Error Handling:
    - Database persistence failures don't block LLM responses
    - Graceful degradation ensures chat functionality continues
    - Comprehensive logging for debugging and monitoring
    
    Returns:
        PlainTextResponse: Assistant response text for client rendering
    """
    # Get session information for context and message persistence
    session = get_current_session(request)
    if not session:
        logger.error("No session available for chat request")
        return PlainTextResponse("Session error", status_code=500)
    
    cfg = load_config()
    body = await request.json()
    message = str(body.get("message") or "").strip()
    if not message:
        return PlainTextResponse("", status_code=400)

    # Use agent-first configuration cascade for model settings
    from .agents.config_loader import get_agent_model_settings
    model_settings = await get_agent_model_settings("simple_chat")
    model = model_settings["model"]
    temperature = float(model_settings["temperature"])
    max_tokens = int(model_settings["max_tokens"])

    logger.info({
        "event": "chat_fallback_request",
        "path": "/chat",
        "client": request.client.host if request.client else None,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "session_id": str(session.id),
        "session_key": session.session_key[:8] + "..." if session.session_key else None,
        "message_preview": message[:100] + "..." if len(message) > 100 else message,
    })
    
    # DEBUG: Log chat_fallback config loading details (using agent-first cascade)
    logger.info({
        "event": "chat_fallback_config_debug",
        "model_settings": model_settings,
        "final_model": model,
        "cascade_source": "agent-first configuration cascade"
    })

    # Save user message to database before LLM call
    message_service = get_message_service()
    user_message_id = None
    
    try:
        user_message_id = await message_service.save_message(
            session_id=session.id,
            role="human",
            content=message,
            metadata={"source": "chat_fallback", "model": model}
        )
        logger.info({
            "event": "user_message_saved",
            "session_id": str(session.id),
            "message_id": str(user_message_id),
            "content_length": len(message)
        })
    except Exception as e:
        # Log error but continue with chat functionality
        logger.error({
            "event": "user_message_save_failed",
            "session_id": str(session.id),
            "error": str(e),
            "error_type": type(e).__name__
        })

    # Build optional headers for OpenRouter (recommended)
    headers = {}
    try:
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("host")
        if host:
            headers["HTTP-Referer"] = f"{scheme}://{host}/"
    except Exception:
        pass
    try:
        app_name = (cfg.get("app") or {}).get("name", "SalesBot")
        headers["X-Title"] = app_name
    except Exception:
        pass

    # Get LLM response
    start_time = time.perf_counter()
    try:
        # DEBUG: Log exact parameters passed to chat_completion_content
        logger.info({
            "event": "chat_completion_content_call_debug",
            "message": message,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "extra_headers": headers or None,
            "function": "chat_completion_content"
        })
        
        text = await chat_completion_content(
            message=message,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=headers or None,
        )
        
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Save assistant response to database after LLM completion
        try:
            assistant_message_id = await message_service.save_message(
                session_id=session.id,
                role="assistant",
                content=text,
                metadata={
                    "source": "chat_fallback",
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "user_message_id": str(user_message_id) if user_message_id else None
                }
            )
            logger.info({
                "event": "assistant_message_saved",
                "session_id": str(session.id),
                "message_id": str(assistant_message_id),
                "user_message_id": str(user_message_id) if user_message_id else None,
                "content_length": len(text),
                "model": model
            })
            
            # Track LLM request for billing (estimated token counts for non-streaming)
            try:
                from .services.llm_request_tracker import LLMRequestTracker
                from decimal import Decimal
                from uuid import UUID
                
                # Estimate tokens (rough: ~4 chars per token)
                estimated_prompt_tokens = len(message) // 4
                estimated_completion_tokens = len(text) // 4
                estimated_total = estimated_prompt_tokens + estimated_completion_tokens
                
                tracker = LLMRequestTracker()
                llm_request_id = await tracker.track_llm_request(
                    session_id=UUID(str(session.id)),
                    provider="openrouter",
                    model=model,
                    request_body={
                        "message_length": len(message),
                        "method": "chat_fallback",
                        "streaming": False
                    },
                    response_body={
                        "response_length": len(text)
                    },
                    tokens={
                        "prompt": estimated_prompt_tokens,
                        "completion": estimated_completion_tokens,
                        "total": estimated_total
                    },
                    cost_data={
                        "unit_cost_prompt": 0.0,
                        "unit_cost_completion": 0.0,
                        "total_cost": Decimal("0.0")  # Legacy endpoint doesn't include cost
                    },
                    latency_ms=latency_ms
                )
                logger.info({
                    "event": "llm_request_tracked",
                    "session_id": str(session.id),
                    "llm_request_id": str(llm_request_id),
                    "estimated_tokens": estimated_total,
                    "note": "Token estimates from legacy endpoint (no exact counts available)"
                })
            except Exception as track_error:
                # Log tracking error but don't break response
                logger.warning({
                    "event": "llm_request_tracking_failed",
                    "session_id": str(session.id),
                    "error": str(track_error),
                    "error_type": type(track_error).__name__
                })
            
        except Exception as e:
            # Log error but don't block response
            logger.error({
                "event": "assistant_message_save_failed",
                "session_id": str(session.id),
                "user_message_id": str(user_message_id) if user_message_id else None,
                "error": str(e),
                "error_type": type(e).__name__
            })
        
        # Return plain text; client will render Markdown + sanitize when allowed
        return PlainTextResponse(text)
        
    except Exception as e:
        logger.error({
            "event": "llm_request_failed",
            "session_id": str(session.id),
            "user_message_id": str(user_message_id) if user_message_id else None,
            "error": str(e),
            "error_type": type(e).__name__
        })
        return PlainTextResponse("Sorry, I'm having trouble responding right now.", status_code=500)


@app.get("/api/session", response_class=JSONResponse)
async def get_session_info(request: Request) -> JSONResponse:
    """Get current session information including LLM configuration for debugging/development."""
    session = get_current_session(request)
    if not session:
        return JSONResponse({"error": "No active session"}, status_code=404)
    
    # Use agent-first configuration cascade for model settings
    from .config import get_config_metadata
    from .agents.config_loader import get_agent_model_settings
    
    model_settings = await get_agent_model_settings("simple_chat")
    config_metadata = get_config_metadata()
    
    # Configuration sources are now determined by the cascade system
    # The cascade logs show exact sources via CascadeAuditTrail
    config_sources = {
        "provider": "yaml",  # Always openrouter for now
        "model": "yaml",     # From agent config (highest priority)
        "temperature": "yaml",
        "max_tokens": "yaml"
    }
    
    # Prepare LLM configuration display with cascaded values
    llm_info = {
        "provider": "openrouter",  # Fixed provider
        "model": model_settings["model"],
        "temperature": model_settings["temperature"],
        "max_tokens": model_settings["max_tokens"],
        "config_sources": config_sources
    }
    
    # Add usage statistics placeholder (can be enhanced with actual tracking later)
    llm_info["last_usage"] = {
        "available": False,
        "note": "Usage statistics tracking not yet implemented"
    }
    
    # Add configuration metadata for change detection
    llm_info["configuration_metadata"] = {
        "version": config_metadata.get("version", "unknown"),
        "loaded_at": config_metadata.get("loaded_at"),
        "loaded_at_formatted": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(config_metadata.get("loaded_at", 0))) if config_metadata.get("loaded_at") else "unknown",
        "yaml_file_modified": config_metadata.get("yaml_file_modified"),
        "yaml_file_modified_formatted": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(config_metadata.get("yaml_file_modified", 0))) if config_metadata.get("yaml_file_modified") else "no yaml file",
        "config_hash": config_metadata.get("config_hash", "unknown"),
        "env_vars_hash": config_metadata.get("env_vars_hash", "unknown")
    }
    
    return JSONResponse({
        "session_id": str(session.id),
        "session_key": session.session_key[:8] + "...",  # Partial key for privacy
        "email": session.email,
        "is_anonymous": session.is_anonymous,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
        "metadata": session.meta,
        "llm_configuration": llm_info
    })


@app.get("/api/chat/history", response_class=JSONResponse)
async def get_chat_history(request: Request) -> JSONResponse:
    """
    Get chat history for the current session.
    
    This endpoint retrieves the chat message history for the current user session,
    formatted for frontend consumption. It provides the same history loading logic
    as the main page but through a dedicated API endpoint for dynamic loading.
    
    Returns:
        JSONResponse: Chat history with messages array formatted for UI display
        
    Example Response:
        {
            "session_id": "123e4567-e89b-12d3-a456-426614174000",
            "messages": [
                {
                    "message_id": "msg-uuid",
                    "role": "human", 
                    "content": "Hello",
                    "timestamp": "2023-01-01T12:00:00Z"
                },
                {
                    "message_id": "msg-uuid-2",
                    "role": "assistant",
                    "content": "Hi there!",
                    "timestamp": "2023-01-01T12:00:01Z"
                }
            ]
        }
    """
    session = get_current_session(request)
    if not session:
        logger.warning("Chat history requested but no session found")
        return JSONResponse({"error": "Unauthorized", "messages": []}, status_code=401)
    
    try:
        chat_history = await _load_chat_history_for_session(session.id)
        return JSONResponse({
            "session_id": str(session.id),
            "messages": chat_history
        })
    except Exception as e:
        logger.error(f"Failed to load chat history for session {session.id}: {e}")
        return JSONResponse({"error": "Failed to load chat history", "messages": []}, status_code=500)


@app.get("/dev/logs/tail", response_class=JSONResponse)
async def tail_logs(request: Request, format: str = "json", count: int = 10) -> JSONResponse:
    cfg = load_config()
    ui_cfg = cfg.get("ui") or {}
    # Gate: must be enabled and likely only in dev env
    if not ui_cfg.get("expose_backend_logs", False):
        return JSONResponse({"error": "disabled"}, status_code=403)
    # Determine log directory and latest file
    logging_cfg = cfg.get("logging") or {}
    # Resolve log directory path relative to backend/ directory
    configured_path = logging_cfg.get("path")
    if configured_path:
        # If path is specified in config, resolve it relative to backend/ directory
        log_dir = str(BASE_DIR / configured_path.lstrip('./'))
    else:
        # Default fallback to backend/logs/
        log_dir = str(BASE_DIR / "logs")
    prefix = logging_cfg.get("prefix", "salient-log-")
    pattern = str(Path(log_dir) / f"{prefix}*.jsonl")
    files: List[str] = sorted(glob.glob(pattern))
    if not files:
        return JSONResponse({"entries": []})
    latest = files[-1]
    # Tail last N lines safely - ensure complete JSON entries
    # Use the count parameter, with reasonable limits
    max_count = int(ui_cfg.get("logs_tail_max", 500))  # Prevent excessive load
    n = min(max(count, 1), max_count)  # Between 1 and max_count
    lines = []
    try:
        with open(latest, "r", encoding="utf-8") as f:
            # Read all lines and get the last N complete lines
            all_lines = f.readlines()
            # Filter out empty lines and get last N entries
            complete_lines = [line.strip() for line in all_lines if line.strip()]
            lines = complete_lines[-n:] if len(complete_lines) >= n else complete_lines
    except Exception:
        lines = []
    
    # Process entries based on format parameter
    if format == "pretty":
        # Pretty-print JSONL entries for human readability
        pretty_entries = []
        for line in lines:
            if line.strip():
                try:
                    # Parse JSON and extract key information
                    log_entry = json.loads(line)
                    if isinstance(log_entry, dict) and "record" in log_entry:
                        record = log_entry["record"]
                        # Format: TIMESTAMP | LEVEL | MODULE:FUNCTION:LINE - MESSAGE
                        timestamp = record.get("time", {}).get("repr", "Unknown time")
                        level = record.get("level", {}).get("name", "INFO")
                        module = record.get("module", "unknown")
                        function = record.get("function", "unknown")
                        line_no = record.get("line", "?")
                        message = record.get("message", "")
                        
                        formatted = f"{timestamp} | {level:5} | {module}:{function}:{line_no} - {message}"
                        pretty_entries.append(formatted)
                    else:
                        # Fallback: pretty-print the JSON
                        pretty_entries.append(json.dumps(log_entry, indent=2))
                except json.JSONDecodeError:
                    # Not JSON, show as-is
                    pretty_entries.append(line)
        # Reverse to show newest entries first
        pretty_entries.reverse()
        return JSONResponse({
            "file": Path(latest).name, 
            "entries": pretty_entries, 
            "format": "pretty",
            "count": len(pretty_entries),
            "requested_count": count
        })
    else:
        # Default: return raw JSONL entries (newest first)
        lines.reverse()
        return JSONResponse({
            "file": Path(latest).name, 
            "entries": lines,
            "count": len(lines),
            "requested_count": count
        })


# Agent API Router Registration
# Include agent endpoints for Pydantic AI agent interactions
from .api.agents import router as agents_router
app.include_router(agents_router)

# Multi-Tenant Account-Agent Instance Router Registration
# Include multi-tenant endpoints for account-scoped agent instances
from .api.account_agents import router as account_agents_router
app.include_router(account_agents_router)

# Conditional Legacy Endpoint Registration  
# Register legacy endpoints only if enabled in configuration
# This enables parallel development of new agents without disrupting existing functionality
_register_legacy_endpoints()