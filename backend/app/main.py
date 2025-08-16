from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio
from sse_starlette.sse import EventSourceResponse

from .config import load_config
from .openrouter_client import stream_chat_chunks


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="SalesBot Backend")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def serve_base_page(request: Request) -> HTMLResponse:
    """Render the minimal HTMX-enabled chat page."""
    cfg = load_config()
    input_cfg = (cfg.get("chat") or {}).get("input") or {}
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            # Inject as data-* attributes for client-side UX tuning
            "debounce_ms": str(input_cfg.get("debounce_ms", 250)),
            "submit_shortcut": str(input_cfg.get("submit_shortcut", "ctrl+enter")),
            "enter_inserts_newline": "true" if input_cfg.get("enter_inserts_newline", True) else "false",
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
    llm_cfg = cfg.get("llm") or {}
    model = llm_cfg.get("model", "openai/gpt-oss-20b:free")
    temperature = float(llm_cfg.get("temperature", 0.3))
    max_tokens = int(llm_cfg.get("max_tokens", 256))

    seed = request.query_params.get("message")
    use_llm = request.query_params.get("llm") == "1"

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
                        break
                    yield {"data": tok}
                    await asyncio.sleep(0.04)
            else:
                # Simulate tokenization and latency
                msg = seed or "This is a streaming demo using Server-Sent Events."
                tokens = msg.split()
                # Honor a rough max_tokens cap
                count = 0
                for tok in tokens:
                    if await request.is_disconnected():
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
        except Exception as exc:
            if not await request.is_disconnected():
                yield {"event": "error", "data": f"stream_error: {type(exc).__name__}"}

    return EventSourceResponse(event_generator())


