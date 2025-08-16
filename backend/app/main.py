from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .config import load_config


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


