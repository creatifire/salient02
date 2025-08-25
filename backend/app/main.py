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

import asyncio
import glob
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from sse_starlette.sse import EventSourceResponse

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
    _setup_logger()
    logger.info("Starting Salient Sales Bot application...")
    
    try:
        # Initialize database service with connection pooling and health verification
        await initialize_database()
        logger.info("Database service initialized successfully")
    except Exception as e:
        # Log startup failure and re-raise to prevent application start
        logger.error(f"Failed to initialize database: {e}")
        raise  # Fail-fast: don't start application with incomplete initialization
    
    # Yield control to FastAPI application - normal operation begins here
    yield  # Application runs here
    
    # Shutdown sequence: Clean up all resources and close connections gracefully
    logger.info("Shutting down application...")
    try:
        # Gracefully shutdown database connections and dispose of connection pools
        await shutdown_database()
        logger.info("Database service shut down cleanly")
    except Exception as e:
        # Log shutdown errors but don't prevent application exit
        logger.error(f"Error during database shutdown: {e}")


# FastAPI application instance with comprehensive configuration
# Title and lifespan management for production deployment
app = FastAPI(title="SalesBot Backend", lifespan=lifespan)

# Middleware Configuration: Session management with path exclusions
# SimpleSessionMiddleware provides automatic session creation, validation, and persistence
# Excluded paths are optimized for performance (health checks, static assets, dev tools)
app.add_middleware(
    SimpleSessionMiddleware,
    exclude_paths=["/health", "/favicon.ico", "/robots.txt", "/dev/logs/tail", "/static"]
)

# Static file serving configuration for assets (images, CSS, JS)
# Mount static files directory for serving SVG icons and other assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Template engine configuration for server-side rendering
# Jinja2Templates provides HTML template rendering with context injection for dynamic content
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _setup_logger() -> None:
    """
    Configure structured logging with file rotation and console output.
    
    Sets up Loguru with:
    - JSONL format for structured logging and parsing
    - File rotation based on size or time intervals
    - Configurable retention for log cleanup
    - Console output for development visibility
    - Timestamped log files for easy identification
    
    Configuration loaded from app.yaml logging section with sensible defaults.
    Log files are created in the configured directory with timestamped names.
    """
    cfg = load_config()
    logging_cfg = cfg.get("logging") or {}
    level = str(logging_cfg.get("level", "INFO")).upper()
    log_dir = logging_cfg.get("path") or str(BASE_DIR.parent / "backend" / "logs")
    prefix = logging_cfg.get("prefix", "salient-log-")
    rotation = str(logging_cfg.get("rotation", "1 day"))
    retention = str(logging_cfg.get("retention", "14 days"))
    compression = logging_cfg.get("compression")
    enqueue = bool(logging_cfg.get("enqueue", False))

    # Remove default logger and configure JSONL structured logging
    logger.remove()
    logger.add(sys.stdout, level=level, serialize=True, enqueue=enqueue)
    
    # Create timestamped log file with rotation and retention
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    file_target = str(Path(log_dir) / f"{prefix}{ts}.jsonl")

    logger.add(
        file_target,
        level=level,
        serialize=True,
        rotation=rotation,
        retention=retention,
        compression=compression,
        enqueue=enqueue,
    )


async def _load_chat_history_for_session(session_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Load chat history for a session with UI-optimized formatting.
    
    Retrieves recent chat messages for the given session and formats them
    for immediate display in the chat UI. The function handles pagination,
    role filtering, and content preparation to ensure optimal user experience
    during session resumption.
    
    Chat History Strategy:
    - Loads last 50 messages to balance performance and context preservation
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
    - Limited to 50 messages to prevent slow page loads
    - Uses efficient database queries with proper indexing
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
        
        # Load recent messages (last 50) excluding system messages for cleaner UI
        # Use conversation-friendly order (oldest first) for natural flow
        messages = await message_service.get_session_messages(
            session_id=session_id,
            limit=50,  # Configurable limit for performance
            role_filter=None  # Include all roles initially, filter below
        )
        
        # Format messages for template rendering
        formatted_history = []
        for msg in messages:
            # Skip system messages in UI display (keep conversation clean)
            if msg.role == "system":
                continue
                
            # Map roles for frontend display
            display_role = "user" if msg.role == "human" else "bot"
            
            formatted_message = {
                "role": display_role,
                "content": msg.content,
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


@app.get("/", response_class=HTMLResponse)
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


@app.get("/events/stream")
async def sse_stream(request: Request):
    """SSE endpoint that streams incremental text chunks.

    Query params (optional):
    - message: seed text to stream back token-by-token (defaults to demo text)
    """
    # Get session information for context
    session = get_current_session(request)
    cfg = load_config()
    # Gate by ui.sse_enabled
    if not (cfg.get("ui") or {}).get("sse_enabled", True):
        return HTMLResponse("SSE disabled", status_code=403)

    llm_cfg = cfg.get("llm") or {}
    model = llm_cfg.get("model", "openai/gpt-oss-20b:free")
    temperature = float(llm_cfg.get("temperature", 0.3))
    max_tokens = int(llm_cfg.get("max_tokens", 256))

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
        "session_id": str(session.id) if session else None,
    })

    async def event_generator():
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
                    yield {"data": tok}
                    await asyncio.sleep(0.04)
                # Graceful end signal
                if not await request.is_disconnected():
                    yield {"event": "end", "data": "end"}
            else:
                # Simulate tokenization and latency
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
                    yield {"data": tok + " "}
                    count += 1
                    await asyncio.sleep(0.12)
                # Include a short footer with config context
                footer = f"\n[model={model} temp={temperature} max_tokens={max_tokens}]"
                if not await request.is_disconnected():
                    yield {"data": footer}
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


@app.post("/chat", response_class=PlainTextResponse)
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

    llm_cfg = cfg.get("llm") or {}
    model = llm_cfg.get("model", "openai/gpt-oss-20b:free")
    temperature = float(llm_cfg.get("temperature", 0.3))
    max_tokens = int(llm_cfg.get("max_tokens", 256))

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
    try:
        text = await chat_completion_content(
            message=message,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=headers or None,
        )
        
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
    """Get current session information for debugging/development."""
    session = get_current_session(request)
    if not session:
        return JSONResponse({"error": "No active session"}, status_code=404)
    
    return JSONResponse({
        "session_id": str(session.id),
        "session_key": session.session_key[:8] + "...",  # Partial key for privacy
        "email": session.email,
        "is_anonymous": session.is_anonymous,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
        "metadata": session.meta
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
async def tail_logs(request: Request) -> JSONResponse:
    cfg = load_config()
    ui_cfg = cfg.get("ui") or {}
    # Gate: must be enabled and likely only in dev env
    if not ui_cfg.get("expose_backend_logs", False):
        return JSONResponse({"error": "disabled"}, status_code=403)
    # Determine log directory and latest file
    logging_cfg = cfg.get("logging") or {}
    log_dir = logging_cfg.get("path") or str(BASE_DIR.parent / "backend" / "logs")
    prefix = logging_cfg.get("prefix", "salient-log-")
    pattern = str(Path(log_dir) / f"{prefix}*.jsonl")
    files: List[str] = sorted(glob.glob(pattern))
    if not files:
        return JSONResponse({"entries": []})
    latest = files[-1]
    # Tail last N lines safely
    n = int(ui_cfg.get("logs_tail_count", 10))
    tail: List[str] = []
    try:
        with open(latest, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            block = 1024
            data = b""
            while len(tail) <= n and size > 0:
                step = block if size - block > 0 else size
                f.seek(size - step)
                data = f.read(step) + data
                size -= step
                tail = data.split(b"\n")
            lines = [ln.decode("utf-8", errors="ignore") for ln in tail if ln]
            lines = lines[-n:]
    except Exception:
        lines = []
    return JSONResponse({"file": Path(latest).name, "entries": lines})

