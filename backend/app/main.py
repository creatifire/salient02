from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="SalesBot Backend")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def serve_base_page(request: Request) -> HTMLResponse:
    """Render the minimal HTMX-enabled chat page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", response_class=HTMLResponse)
async def health() -> str:
    return "ok"


