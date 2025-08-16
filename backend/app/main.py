from pathlib import Path
import sys

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
import asyncio
from sse_starlette.sse import EventSourceResponse

from .config import load_config
from .openrouter_client import stream_chat_chunks, chat_completion_content
from loguru import logger


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="SalesBot Backend")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _setup_logger() -> None:
    cfg = load_config()
    logging_cfg = cfg.get("logging") or {}
    level = str(logging_cfg.get("level", "INFO")).upper()
    path = str(logging_cfg.get("path", "./backend/logs/app.jsonl"))
    rotation = str(logging_cfg.get("rotation", "50 MB"))
    retention = str(logging_cfg.get("retention", "14 days"))

    # Ensure log directory exists
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure loguru JSONL sinks
    logger.remove()
    logger.add(sys.stdout, level=level, serialize=True)
    logger.add(path, level=level, serialize=True, rotation=rotation, retention=retention)


@app.on_event("startup")
def on_startup() -> None:
    _setup_logger()
    logger.info({
        "event": "startup",
        "message": "application started",
    })


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
            "sse_enabled": "true" if (cfg.get("ui") or {}).get("sse_enabled", True) else "false",
        },
    )


@app.get("/health", response_class=HTMLResponse)
async def health() -> str:
    return "ok"


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
                async for tok in stream_chat_chunks(
                    message=seed,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
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

    text = await chat_completion_content(
        message=message,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    # Render via partial for consistent markup
    allow_basic_html = (cfg.get("ui") or {}).get("allow_basic_html", True)
    html = templates.get_template("partials/message.html").render({
        "role": "bot",
        "text": text,
        "allow_basic_html": allow_basic_html,
    })
    return HTMLResponse(html)

