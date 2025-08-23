"""
Salient Sales Bot FastAPI backend application.

This is the main FastAPI application providing:
- Chat UI with HTMX frontend
- Server-Sent Events for streaming LLM responses  
- Database persistence for chat history and sessions
- Health monitoring and logging
- Configuration management with security best practices

Key Features:
- Async database service with connection pooling
- OpenRouter LLM integration with cost tracking
- Session management for conversation continuity
- Comprehensive logging with rotation and structured output
- Production-ready health checks and graceful shutdown

Security:
- HTTP-only session cookies
- Environment-based configuration for sensitive data
- Input sanitization and error handling
- Configurable CORS and rate limiting (future)
"""

from pathlib import Path
from datetime import datetime
import sys
from typing import List
from fastapi.responses import JSONResponse
import glob

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
import asyncio
from sse_starlette.sse import EventSourceResponse
from contextlib import asynccontextmanager

from .config import load_config
from .openrouter_client import stream_chat_chunks, chat_completion_content
from .database import initialize_database, shutdown_database, get_database_service
from loguru import logger


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI application lifespan management for graceful startup/shutdown.
    
    Handles:
    - Logger configuration and initialization
    - Database service startup with connection pooling
    - Graceful database shutdown on application exit
    - Error handling and logging for service lifecycle
    
    This replaces the deprecated @app.on_event("startup"/"shutdown") pattern
    with the modern FastAPI lifespan approach for better resource management.
    """
    # Startup sequence
    _setup_logger()
    logger.info("Starting Salient Sales Bot application...")
    
    try:
        await initialize_database()
        logger.info("Database service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown sequence
    logger.info("Shutting down application...")
    try:
        await shutdown_database()
        logger.info("Database service shut down cleanly")
    except Exception as e:
        logger.error(f"Error during database shutdown: {e}")


app = FastAPI(title="SalesBot Backend", lifespan=lifespan)
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


@app.get("/", response_class=HTMLResponse)
async def serve_base_page(request: Request) -> HTMLResponse:
    """Render the minimal HTMX-enabled chat page."""
    logger.info({
        "event": "serve_base_page",
        "path": "/",
        "client": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    })
    cfg = load_config()
    ui_cfg = cfg.get("ui") or {}
    # Gate exposure of backend chat UI
    if not ui_cfg.get("expose_backend_chat", True):
        return HTMLResponse("Not Found", status_code=404)
    input_cfg = (cfg.get("chat") or {}).get("input") or {}
    logging_cfg = cfg.get("logging") or {}
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
        },
    )


@app.get("/health")
async def health() -> dict:
    """Enhanced health check including database connectivity."""
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
    """Non-stream fallback: returns full assistant text in one response."""
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

    text = await chat_completion_content(
        message=message,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        extra_headers=headers or None,
    )
    # Return plain text; client will render Markdown + sanitize when allowed
    return PlainTextResponse(text)


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

